#!/usr/bin/env bash
# tune-grammar-models.sh — End-to-end pipeline to fine-tune a grammar checker model
#
# Uses the existing ClaudeLab infrastructure:
#   1. Generate training data via Claude Sonnet (free via Max subscription)
#   2. Prepare SFT dataset
#   3. Fine-tune with LoRA on local GPU (RX 9070 XT / 16GB)
#   4. Convert to GGUF, quantize, deploy to Ollama
#   5. Evaluate against test samples
#
# Usage:
#   ./tune-grammar-models.sh generate    # Step 1: Generate training data
#   ./tune-grammar-models.sh prepare     # Step 2: Prepare SFT dataset
#   ./tune-grammar-models.sh train       # Step 3-4: Train + convert + deploy
#   ./tune-grammar-models.sh eval        # Step 5: Evaluate
#   ./tune-grammar-models.sh all         # Run everything

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CLAUDELAB_DIR="/home/veech/Documents/TestVault/Projects/ClaudeLab"
LLAMACPP_DIR="/home/veech/Documents/llama.cpp"
TRAINING_DATA_DIR="$CLAUDELAB_DIR/training-data/legal-grammar"
VENV="$CLAUDELAB_DIR/.venv"

# Task name used in ClaudeLab pipeline
TASK="legal-grammar"
# Base model for fine-tuning (3B fits in 16GB VRAM with LoRA)
BASE_MODEL="Qwen/Qwen2.5-3B-Instruct"
MAX_LENGTH=3072
EPOCHS=5
LORA_RANK=32

mkdir -p "$TRAINING_DATA_DIR"

step_generate() {
    echo "=== Step 1: Generate Training Data ==="
    echo ""
    echo "This generates grammar-check training examples using Claude Sonnet."
    echo "Each example: bad legal text → model-formatted grammar review."
    echo ""

    # Check if batch files exist
    if [[ ! -f "$TRAINING_DATA_DIR/batch-0.jsonl" ]]; then
        echo "Creating batch files from research samples..."
        python3 "$SCRIPT_DIR/generate-grammar-batches.py" \
            --output-dir "$TRAINING_DATA_DIR" \
            --samples-per-batch 20
        echo ""
    fi

    BATCH_COUNT=$(ls "$TRAINING_DATA_DIR"/batch-*.jsonl 2>/dev/null | wc -l)
    echo "Found $BATCH_COUNT batch files"
    echo ""

    # Process each batch through Claude
    for batch_file in "$TRAINING_DATA_DIR"/batch-*.jsonl; do
        batch_name=$(basename "$batch_file" .jsonl)
        output_file="$TRAINING_DATA_DIR/output-${batch_name}.jsonl"

        if [[ -f "$output_file" ]]; then
            existing=$(wc -l < "$output_file")
            total=$(wc -l < "$batch_file")
            echo "  $batch_name: $existing/$total done (resuming)"
        else
            echo "  $batch_name: starting"
        fi

        cd "$CLAUDELAB_DIR"
        python3 gen-one.py \
            --task "$TASK" \
            --batch-file "$batch_file" \
            --output-file "$output_file" \
            --system-prompt-file "$SCRIPT_DIR/grammar-training-system-prompt.txt" \
            2>&1 | tail -5
    done

    # Combine outputs
    cat "$TRAINING_DATA_DIR"/output-batch-*.jsonl > "$TRAINING_DATA_DIR/combined-raw.jsonl" 2>/dev/null || true
    TOTAL=$(wc -l < "$TRAINING_DATA_DIR/combined-raw.jsonl" 2>/dev/null || echo 0)
    echo ""
    echo "Total training examples: $TOTAL"
    echo ""
    echo "Run './tune-grammar-models.sh prepare' next."
}

step_prepare() {
    echo "=== Step 2: Prepare SFT Dataset ==="

    # Copy latest data from project to ClaudeLab training dir
    if [[ -f "$PROJECT_DIR/training-data/combined-raw.jsonl" ]]; then
        cp "$PROJECT_DIR/training-data/combined-raw.jsonl" "$TRAINING_DATA_DIR/combined-raw.jsonl"
    fi

    if [[ ! -f "$TRAINING_DATA_DIR/combined-raw.jsonl" ]]; then
        echo "Error: No combined-raw.jsonl found. Run 'generate' first." >&2
        exit 1
    fi

    python3 "$SCRIPT_DIR/prepare-legal-sft.py"

    echo ""
    TRAIN_COUNT=$(wc -l < "$TRAINING_DATA_DIR/sft-train.jsonl" 2>/dev/null || echo 0)
    VAL_COUNT=$(wc -l < "$TRAINING_DATA_DIR/sft-val.jsonl" 2>/dev/null || echo 0)
    echo "Train: $TRAIN_COUNT examples"
    echo "Val:   $VAL_COUNT examples"
    echo ""
    echo "Run './tune-grammar-models.sh train' next."
}

step_train() {
    echo "=== Step 3: Fine-Tune + Convert + Deploy ==="

    # Unload Ollama models to free VRAM
    echo "Unloading Ollama models to free GPU memory..."
    for model in $(ollama list 2>/dev/null | awk 'NR>1 {print $1}'); do
        curl -s http://localhost:11434/api/generate -d "{\"model\":\"$model\",\"keep_alive\":0}" > /dev/null 2>&1 || true
    done
    sleep 2

    cd "$CLAUDELAB_DIR"

    echo "Training $TASK (base: $BASE_MODEL)..."
    echo "  max_length=$MAX_LENGTH, epochs=$EPOCHS, lora_rank=$LORA_RANK"
    echo ""

    # Add legal-grammar config to finetune-model.py if not already there
    # (The script reads TASK_CONFIGS dict)
    source "$VENV/bin/activate"

    python3 finetune-model.py "$TASK"

    MERGED_DIR="$CLAUDELAB_DIR/vault-${TASK}-merged"

    if [[ ! -d "$MERGED_DIR" ]]; then
        echo "Error: Merged model directory not found at $MERGED_DIR" >&2
        exit 1
    fi

    echo ""
    echo "Converting to GGUF..."
    python3 "$LLAMACPP_DIR/convert_hf_to_gguf.py" \
        "$MERGED_DIR" \
        --outfile "$CLAUDELAB_DIR/legal-grammar.f16.gguf" \
        --outtype f16

    echo "Quantizing to Q8_0..."
    "$LLAMACPP_DIR/build/bin/llama-quantize" \
        "$CLAUDELAB_DIR/legal-grammar.f16.gguf" \
        "$CLAUDELAB_DIR/legal-grammar.Q8_0.gguf" \
        Q8_0

    deactivate 2>/dev/null || true

    # Create Ollama Modelfile for the fine-tuned model
    GGUF_PATH="$CLAUDELAB_DIR/legal-grammar.Q8_0.gguf"
    SFT_PROMPT=$(cat "$SCRIPT_DIR/grammar-sft-system-prompt.txt")

    cat > "$PROJECT_DIR/Modelfile.legal-grammar-ft" <<MODELFILE
FROM $GGUF_PATH

SYSTEM """$SFT_PROMPT"""

PARAMETER temperature 0.1
PARAMETER num_ctx 3072
PARAMETER num_predict 2048
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
MODELFILE

    echo "Loading into Ollama..."
    ollama create legalgrammar -f "$PROJECT_DIR/Modelfile.legal-grammar-ft"

    echo ""
    echo "Model deployed as 'legalgrammar'"
    echo "Run './tune-grammar-models.sh eval' to benchmark."
}

step_eval() {
    echo "=== Step 4: Evaluate ==="
    cd "$SCRIPT_DIR"

    python3 eval-grammar.py \
        --models "legal-reviewer,legalgrammar,email-polisher,brief-reviewer,contract-language,plain-language" \
        --test-samples "$SCRIPT_DIR/grammar-test-samples.md" \
        --output "$SCRIPT_DIR/results/eval-$(date +%Y%m%d).json"
}

case "${1:-}" in
    generate) step_generate ;;
    prepare)  step_prepare ;;
    train)    step_train ;;
    eval)     step_eval ;;
    all)
        step_generate
        step_prepare
        step_train
        step_eval
        ;;
    *)
        echo "Usage: $0 {generate|prepare|train|eval|all}"
        echo ""
        echo "  generate  — Create training data via Claude Sonnet"
        echo "  prepare   — Convert to SFT format"
        echo "  train     — LoRA fine-tune, GGUF convert, deploy to Ollama"
        echo "  eval      — Benchmark against test samples"
        echo "  all       — Run everything end-to-end"
        exit 1
        ;;
esac
