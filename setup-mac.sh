#!/usr/bin/env bash
# ============================================================================
# Local AI Setup for Legal Work — macOS
# Target: Apple Silicon Macs (M1/M2/M3/M4, 16GB+ RAM)
#
# This script installs and configures:
#   1. Ollama (local AI model server with Metal GPU acceleration)
#   2. Open WebUI (browser-based chat interface)
#   3. Legal models and grammar checker presets
#   4. legal-check CLI tool
#
# Usage:
#   chmod +x setup-mac.sh
#   ./setup-mac.sh
#
# After setup, all AI inference runs locally. No data leaves your machine.
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }
step()  { echo -e "\n${BOLD}── Step $1 ──${NC}"; }

# ── Preflight ──
echo -e "${BOLD}"
echo "============================================"
echo "  Local AI Setup for Legal Work"
echo "  macOS (Apple Silicon)"
echo "============================================"
echo -e "${NC}"

# Check macOS
if [[ "$(uname)" != "Darwin" ]]; then
    error "This script is for macOS. Use setup.sh for Linux."
    exit 1
fi

# Check Apple Silicon
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    ok "Apple Silicon detected ($ARCH)"
else
    warn "Intel Mac detected. Models will run slower. Apple Silicon recommended."
fi

# Check RAM
TOTAL_RAM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
ok "RAM: ${TOTAL_RAM_GB}GB"
if [[ "$TOTAL_RAM_GB" -lt 16 ]]; then
    warn "16GB+ recommended for legal models. Some larger models may not fit."
fi

echo ""
echo "This will install:"
echo "  - Ollama (AI model server with Metal GPU acceleration)"
echo "  - Open WebUI (browser-based chat interface)"
echo "  - 3 language models + 5 grammar checker models (~40GB download)"
echo "  - legal-check CLI tool"
echo ""
echo "Estimated time: 15-30 minutes (depending on internet speed)"
echo ""
read -p "Continue? [Y/n] " confirm
[[ "${confirm:-Y}" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

# ── Install Homebrew (if needed) ──
step "1/7: Checking Homebrew"

if command -v brew &>/dev/null; then
    ok "Homebrew installed"
else
    info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add to path for this session
    eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null)"
    ok "Homebrew installed"
fi

# ── Install Ollama ──
step "2/7: Installing Ollama"

if command -v ollama &>/dev/null; then
    ok "Ollama already installed: $(ollama --version 2>/dev/null || echo 'version unknown')"
else
    info "Installing Ollama..."
    brew install ollama
    ok "Ollama installed"
fi

# Start Ollama service
info "Starting Ollama..."
if ! pgrep -x "ollama" &>/dev/null; then
    ollama serve &>/dev/null &
    sleep 3
fi

# Wait for Ollama to be ready
for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        ok "Ollama is running"
        break
    fi
    sleep 1
    if [[ $i -eq 30 ]]; then
        error "Ollama didn't start. Try: ollama serve"
        exit 1
    fi
done

# ── Pull Models ──
step "3/7: Downloading AI models"

echo ""
echo "Pulling 3 base models for legal work:"
echo "  1. gemma3:12b       (8GB)   — Fast, great for summarization"
echo "  2. qwen3:14b        (9GB)   — Strong analysis, structured output"
echo "  3. nomic-embed-text (274MB) — Document search embeddings"

# Determine which models to pull based on RAM
if [[ "$TOTAL_RAM_GB" -ge 32 ]]; then
    echo "  4. mistral-small    (14GB)  — Complex reasoning (you have enough RAM)"
    models=("gemma3:12b" "qwen3:14b" "mistral-small:24b" "nomic-embed-text")
else
    echo ""
    warn "Skipping mistral-small (needs 32GB+ RAM for comfortable use)"
    models=("gemma3:12b" "qwen3:14b" "nomic-embed-text")
fi
echo ""

for model in "${models[@]}"; do
    if (ollama list 2>/dev/null || true) | grep -q "$(echo "$model" | cut -d: -f1)"; then
        ok "$model already downloaded"
    else
        info "Pulling $model..."
        ollama pull "$model"
        ok "$model ready"
    fi
done

# ── Build Grammar Checker Models ──
step "4/7: Building grammar checker models"

# Build original legal presets
original_models=("contract-reviewer" "depo-summarizer" "memo-drafter" "clause-identifier")
for name in "${original_models[@]}"; do
    modelfile="$SCRIPT_DIR/Modelfile.${name}"
    if [[ -f "$modelfile" ]]; then
        info "Creating $name..."
        ollama create "$name" -f "$modelfile" 2>&1 | tail -1
        ok "$name ready"
    fi
done

# Build grammar checker models
grammar_models=("legal-reviewer" "email-polisher" "brief-reviewer" "contract-language" "plain-language")
for name in "${grammar_models[@]}"; do
    modelfile="$SCRIPT_DIR/Modelfile.${name}"
    if [[ -f "$modelfile" ]]; then
        info "Creating $name..."
        ollama create "$name" -f "$modelfile" 2>&1 | tail -1
        ok "$name ready"
    fi
done

# ── Install legal-check CLI ──
step "5/7: Installing legal-check CLI"

chmod +x "$SCRIPT_DIR/legal-check"

# Determine install location
if [[ -d "$HOME/.local/bin" ]]; then
    INSTALL_DIR="$HOME/.local/bin"
elif [[ -d "/usr/local/bin" ]]; then
    INSTALL_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
fi

ln -sf "$SCRIPT_DIR/legal-check" "$INSTALL_DIR/legal-check"
ok "legal-check installed to $INSTALL_DIR/legal-check"

# Check if in PATH
if ! command -v legal-check &>/dev/null; then
    warn "$INSTALL_DIR is not in your PATH."
    echo "  Add to your shell config:"
    echo "    echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.zshrc"
    echo "    source ~/.zshrc"
fi

# ── Install Open WebUI ──
step "6/7: Installing Open WebUI"

echo ""
echo "Open WebUI provides a ChatGPT-like browser interface."
echo "You can install it via Docker or pip."
echo ""

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    OPEN_WEBUI_IMAGE="ghcr.io/open-webui/open-webui:v0.6.5"
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "open-webui"; then
        ok "Open WebUI container already exists"
        docker start open-webui 2>/dev/null || true
    else
        info "Starting Open WebUI via Docker..."
        docker run -d \
            -p 127.0.0.1:3000:8080 \
            -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
            -v open-webui:/app/backend/data \
            --name open-webui \
            --restart always \
            "$OPEN_WEBUI_IMAGE"
        ok "Open WebUI running at http://localhost:3000"
    fi
else
    info "Docker not found. You can install Open WebUI via pip:"
    echo "  pip install open-webui"
    echo "  open-webui serve --port 3000"
    echo ""
    echo "Or install Docker Desktop for Mac from https://docker.com"
fi

# ── Quick Test ──
step "7/7: Quick test"

info "Testing grammar checker..."
echo ""

TEST_TEXT="The defendant don't have no evidence to support their claim and we should file the motion immediately."
echo "Test input: $TEST_TEXT"
echo ""

RESULT=$(echo "$TEST_TEXT" | ollama run email-polisher 2>/dev/null | head -20)

if [[ -n "$RESULT" ]]; then
    echo "$RESULT"
    echo ""
    ok "Grammar checker is working!"
else
    warn "No response — model may still be loading. Try: echo 'test' | ollama run email-polisher"
fi

# ── Done ──
echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""
echo "Grammar checker CLI:"
echo "  legal-check file.txt                  # Full grammar review"
echo "  legal-check -m email email.txt        # Quick email polish"
echo "  legal-check -m brief motion.txt       # Brief proofreader"
echo "  legal-check -m contract agreement.txt # Contract precision"
echo "  legal-check -m plain clause.txt       # Plain language rewrite"
echo "  legal-check -c                        # Check clipboard"
echo "  cat doc.txt | legal-check             # Pipe text in"
echo ""
echo "Web interface:"
echo "  http://localhost:3000"
echo "  First time: create a local account (stays on your machine)"
echo ""
echo "Models available:"
echo "  gemma3:12b       — Fast daily tasks"
echo "  qwen3:14b        — Detailed analysis"
if [[ "$TOTAL_RAM_GB" -ge 32 ]]; then
echo "  mistral-small    — Complex reasoning"
fi
echo ""
echo "Grammar presets:"
echo "  legal-reviewer   — Full 7-point legal writing review"
echo "  email-polisher   — Quick email tone and grammar"
echo "  brief-reviewer   — Court filing proofreader"
echo "  contract-language — Contract precision and ambiguity"
echo "  plain-language   — Legalese to plain English"
echo ""
echo -e "${YELLOW}IMPORTANT: Always verify AI outputs, especially citations.${NC}"
echo ""

# Remind about Ollama autostart
echo "To auto-start Ollama on login:"
echo "  brew services start ollama"
echo ""
