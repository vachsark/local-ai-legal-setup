#!/usr/bin/env bash
# gen-grammar-data.sh — Generate gold-standard grammar corrections via Claude Sonnet
# Processes items in PARALLEL for speed (4 concurrent by default)
#
# Usage:
#   ./gen-grammar-data.sh                    # Process all (4 parallel workers)
#   ./gen-grammar-data.sh --parallel 6       # 6 concurrent Claude calls
#   ./gen-grammar-data.sh --batch 0          # Process specific batch only
#   ./gen-grammar-data.sh --max 5            # Max N items per batch
#   ./gen-grammar-data.sh --dry-run          # Show what would be processed
#   ./gen-grammar-data.sh --regenerate       # Regenerate batch files from templates

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/training-data"
SYSTEM_PROMPT_FILE="$SCRIPT_DIR/grammar-training-system-prompt.txt"

BATCH_FILTER=""
MAX_ITEMS=0
DRY_RUN=false
PARALLEL=4
REGENERATE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --batch) BATCH_FILTER="$2"; shift 2 ;;
        --max) MAX_ITEMS="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        --parallel|-j) PARALLEL="$2"; shift 2 ;;
        --regenerate) REGENERATE=true; shift ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

mkdir -p "$DATA_DIR"

# Generate batches if needed
if [[ "$REGENERATE" == true ]] || ! ls "$DATA_DIR"/batch-*.jsonl &>/dev/null; then
    echo "Generating batch files..."
    [[ "$REGENERATE" == true ]] && rm -f "$DATA_DIR"/batch-*.jsonl "$DATA_DIR"/output-batch-*.jsonl
    python3 "$SCRIPT_DIR/generate-grammar-batches.py" --output-dir "$DATA_DIR"
    echo ""
fi

if [[ ! -f "$SYSTEM_PROMPT_FILE" ]]; then
    echo "Error: System prompt not found at $SYSTEM_PROMPT_FILE" >&2
    exit 1
fi

# Create work directory — each item gets its own file for clean parallel processing
WORK_DIR=$(mktemp -d)
RESULTS_DIR=$(mktemp -d)
trap "rm -rf $WORK_DIR $RESULTS_DIR" EXIT

# Build work items
item_idx=0
for batch_file in "$DATA_DIR"/batch-*.jsonl; do
    batch_name=$(basename "$batch_file" .jsonl)
    batch_num="${batch_name#batch-}"
    [[ -n "$BATCH_FILTER" && "$batch_num" != "$BATCH_FILTER" ]] && continue

    output_file="$DATA_DIR/output-${batch_name}.jsonl"
    touch "$output_file"

    line_count=0
    while IFS= read -r line; do
        if [[ "$MAX_ITEMS" -gt 0 && "$line_count" -ge "$MAX_ITEMS" ]]; then
            break
        fi

        batch_id=$(echo "$line" | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['batch_id'])")

        # Skip already processed
        if grep -q "\"batch_id\": \"$batch_id\"" "$output_file" 2>/dev/null; then
            continue
        fi

        # Write work item
        echo "$line" > "$WORK_DIR/item-${item_idx}.json"
        echo "$output_file" > "$WORK_DIR/item-${item_idx}.out"
        item_idx=$((item_idx + 1))
        line_count=$((line_count + 1))
    done < "$batch_file"
done

echo "=== Legal Grammar Data Generation ==="
echo "Items to process: $item_idx | Parallel workers: $PARALLEL"
echo ""

if [[ "$item_idx" -eq 0 ]]; then
    echo "Nothing to process — all items already done."
else
    if [[ "$DRY_RUN" == true ]]; then
        for f in "$WORK_DIR"/item-*.json; do
            batch_id=$(python3 -c "import json; print(json.load(open('$f'))['batch_id'])")
            chars=$(python3 -c "import json; print(len(json.load(open('$f'))['user_input']))")
            echo "  WOULD process $batch_id ($chars chars)"
        done
    else
        SYSTEM_PROMPT=$(cat "$SYSTEM_PROMPT_FILE")

        # Worker function
        process_item() {
            local item_file="$1"
            local idx=$(basename "$item_file" .json | sed 's/item-//')
            local out_target=$(cat "$WORK_DIR/item-${idx}.out")

            local batch_id user_input
            batch_id=$(python3 -c "import json; print(json.load(open('$item_file'))['batch_id'])")
            user_input=$(python3 -c "import json; print(json.load(open('$item_file'))['user_input'])")

            local start_time=$(date +%s)

            local result
            result=$(echo "$user_input" | env -u CLAUDECODE claude \
                --model claude-sonnet-4-6 \
                --print \
                --max-turns 1 \
                --system-prompt "$SYSTEM_PROMPT" \
                2>/dev/null) || true

            local elapsed=$(( $(date +%s) - start_time ))

            if [[ -z "$result" || ${#result} -lt 50 ]]; then
                echo "FAIL $batch_id (${elapsed}s)"
                return 1
            fi

            # Build JSON output
            python3 -c "
import json, sys
batch_id = '$batch_id'
user_input = open('$item_file').read()
user_input = json.loads(user_input)['user_input']
result = sys.stdin.read()
print(json.dumps({'batch_id': batch_id, 'user_input': user_input, 'output': result}))
" <<< "$result" > "$RESULTS_DIR/result-${idx}.jsonl"

            # Store target file path
            echo "$out_target" > "$RESULTS_DIR/target-${idx}.txt"

            echo "DONE $batch_id (${#result} chars, ${elapsed}s)"
        }
        export -f process_item
        export WORK_DIR RESULTS_DIR SYSTEM_PROMPT

        # Run in parallel
        ls "$WORK_DIR"/item-*.json | xargs -P "$PARALLEL" -I {} bash -c 'process_item "{}"'

        # Collect results (sequential — safe file append)
        for result_file in "$RESULTS_DIR"/result-*.jsonl; do
            [[ -f "$result_file" ]] || continue
            idx=$(basename "$result_file" .jsonl | sed 's/result-//')
            target=$(cat "$RESULTS_DIR/target-${idx}.txt")
            cat "$result_file" >> "$target"
        done
    fi
fi

echo ""
echo "=== Summary ==="

# Combine outputs
if ls "$DATA_DIR"/output-batch-*.jsonl &>/dev/null; then
    cat "$DATA_DIR"/output-batch-*.jsonl > "$DATA_DIR/combined-raw.jsonl"
    combined_count=$(wc -l < "$DATA_DIR/combined-raw.jsonl")
    echo "Combined: $combined_count items in $DATA_DIR/combined-raw.jsonl"
fi

echo ""
echo "Next: ./tests/tune-grammar-models.sh prepare"
