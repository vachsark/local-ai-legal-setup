#!/usr/bin/env bash
# Build all legal grammar/style checker models for Ollama
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GRAMMAR_MODELS=(
    "legal-reviewer"
    "email-polisher"
    "brief-reviewer"
    "contract-language"
    "plain-language"
)

echo "Building legal grammar checker models..."
echo ""

for model in "${GRAMMAR_MODELS[@]}"; do
    modelfile="Modelfile.${model}"
    if [[ ! -f "$modelfile" ]]; then
        echo "  SKIP  $model — $modelfile not found"
        continue
    fi

    # Extract base model
    base=$(grep "^FROM " "$modelfile" | head -1 | awk '{print $2}')

    # Check if base model is pulled
    if ! (ollama list 2>/dev/null || true) | grep -q "${base}"; then
        echo "  PULL  $base (needed for $model)"
        ollama pull "$base"
    fi

    echo "  BUILD $model (from $base)"
    ollama create "$model" -f "$modelfile" 2>&1 | tail -1
done

echo ""
echo "Done. Available grammar models:"
ollama list 2>/dev/null | grep -E "(legal-reviewer|email-polisher|brief-reviewer|contract-language|plain-language)" || echo "  (none found — check for errors above)"
echo ""
echo "Usage: legal-check -m email your-email.txt"
echo "       cat brief.txt | legal-check -m brief"
echo "       legal-check -c  # clipboard"
