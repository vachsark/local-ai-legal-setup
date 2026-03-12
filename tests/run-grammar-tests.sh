#!/usr/bin/env bash
# run-grammar-tests.sh — Benchmark grammar checker models against test samples
# Runs each test sample through each model and saves results for comparison
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$SCRIPT_DIR/results"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RUN_DIR="$RESULTS_DIR/$TIMESTAMP"

mkdir -p "$RUN_DIR"

# Extract test samples from the markdown file
extract_samples() {
    local file="$SCRIPT_DIR/grammar-test-samples.md"
    local sample_num=0
    local in_code_block=false
    local in_sample=false
    local sample_text=""
    local expected=""

    while IFS= read -r line; do
        if [[ "$line" =~ ^##\ Sample\ ([0-9]+): ]]; then
            # Save previous sample
            if [[ $sample_num -gt 0 && -n "$sample_text" ]]; then
                echo "$sample_text" > "$RUN_DIR/sample-${sample_num}.txt"
                echo "$expected" > "$RUN_DIR/expected-${sample_num}.txt"
            fi
            sample_num="${BASH_REMATCH[1]}"
            sample_text=""
            expected=""
            in_sample=true
            in_code_block=false
            continue
        fi

        if [[ "$in_sample" == true ]]; then
            if [[ "$line" =~ ^EXPECTED: ]]; then
                expected="$line"
                continue
            fi
            if [[ "$line" == '```' ]]; then
                in_code_block=$([ "$in_code_block" == true ] && echo false || echo true)
                continue
            fi
            if [[ "$in_code_block" == false && "$in_sample" == true && -n "$line" && ! "$line" =~ ^# && ! "$line" =~ ^--- && ! "$line" =~ ^\`\`\` ]]; then
                sample_text+="$line"$'\n'
            fi
        fi
    done < "$file"

    # Save last sample
    if [[ $sample_num -gt 0 && -n "$sample_text" ]]; then
        echo "$sample_text" > "$RUN_DIR/sample-${sample_num}.txt"
        echo "$expected" > "$RUN_DIR/expected-${sample_num}.txt"
    fi
}

# Models to test and their corresponding legal-check modes
declare -A TEST_MODELS=(
    [grammar]="legal-reviewer"
    [email]="email-polisher"
    [brief]="brief-reviewer"
    [contract]="contract-language"
)

run_test() {
    local mode="$1"
    local model="${TEST_MODELS[$mode]}"
    local sample_file="$2"
    local sample_num="$3"
    local output_file="$RUN_DIR/${mode}-sample${sample_num}.md"

    # Check if model exists
    if ! ollama list 2>/dev/null | grep -q "^${model}"; then
        echo "  SKIP $model (not built)" | tee -a "$RUN_DIR/run.log"
        return
    fi

    local start_time=$(date +%s%N)
    local result
    result=$(ollama run "$model" < "$sample_file" 2>/dev/null) || true
    local end_time=$(date +%s%N)
    local elapsed_ms=$(( (end_time - start_time) / 1000000 ))
    local elapsed_sec=$(awk "BEGIN {printf \"%.1f\", $elapsed_ms / 1000}")

    # Write result
    {
        echo "# $mode — Sample $sample_num"
        echo "Model: $model | Time: ${elapsed_sec}s"
        echo "---"
        echo ""
        echo "$result"
    } > "$output_file"

    echo "  $mode sample-$sample_num: ${elapsed_sec}s" | tee -a "$RUN_DIR/run.log"
}

echo "=== Legal Grammar Test Run: $TIMESTAMP ==="
echo "Results: $RUN_DIR"
echo ""

# Extract samples
echo "Extracting test samples..."
extract_samples
SAMPLE_COUNT=$(ls "$RUN_DIR"/sample-*.txt 2>/dev/null | wc -l)
echo "Found $SAMPLE_COUNT samples"
echo ""

# Run each model against relevant samples
echo "Running tests..."
for sample_file in "$RUN_DIR"/sample-*.txt; do
    sample_num=$(basename "$sample_file" | sed 's/sample-\([0-9]*\)\.txt/\1/')

    # Run grammar model on all samples
    run_test "grammar" "$sample_file" "$sample_num"

    # Run email model on sample 1 (email)
    [[ "$sample_num" == "1" ]] && run_test "email" "$sample_file" "$sample_num"

    # Run brief model on samples 2 and 5
    [[ "$sample_num" == "2" || "$sample_num" == "5" ]] && run_test "brief" "$sample_file" "$sample_num"

    # Run contract model on sample 3
    [[ "$sample_num" == "3" ]] && run_test "contract" "$sample_file" "$sample_num"
done

echo ""
echo "=== Test run complete ==="
echo "Results in: $RUN_DIR"
echo ""
echo "To compare results:"
echo "  ls $RUN_DIR/*.md"
echo "  # or diff two model outputs:"
echo "  diff $RUN_DIR/grammar-sample1.md $RUN_DIR/email-sample1.md"
