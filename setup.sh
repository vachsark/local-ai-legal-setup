#!/usr/bin/env bash
# ============================================================================
# Local AI Setup for Legal Work
# Target: Arch Linux + AMD RX 9070 XT (16GB VRAM)
#
# This script installs and configures:
#   1. Ollama (local AI model server with GPU acceleration)
#   2. Open WebUI (ChatGPT-like browser interface)
#   3. Recommended models for legal work
#   4. Legal preset models with specialized system prompts
#   5. RAG (document upload) with legal-optimized settings
#   6. GPU tuning for optimal performance
#   7. Voice-to-text (Whisper) for dictation
#   8. Optional: LanguageTool for grammar checking
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
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

# ── Preflight Checks ──
echo -e "${BOLD}"
echo "============================================"
echo "  Local AI Setup for Legal Work"
echo "  Arch Linux + AMD GPU"
echo "============================================"
echo -e "${NC}"
echo "This will install:"
echo "  - Ollama (AI model server with GPU acceleration)"
echo "  - Open WebUI (browser-based chat interface)"
echo "  - 3 language models, 5 legal presets, and an embedding model (~32GB download)"
echo ""
echo "Estimated time: 15-30 minutes (depending on internet speed)"
echo "Disk space needed: ~35GB"
echo ""
read -p "Continue? [Y/n] " confirm
[[ "${confirm:-Y}" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

# ── Check for AMD GPU ──
step "1/9: Checking hardware"

if lspci 2>/dev/null | grep -qi "VGA.*AMD\|Display.*AMD"; then
    gpu_name=$(lspci | grep -iE "VGA|Display" | grep -i AMD | head -1 | sed 's/.*: //')
    ok "AMD GPU detected: $gpu_name"
else
    warn "No AMD GPU detected. Models will run on CPU (much slower)."
    read -p "Continue anyway? [y/N] " gpu_confirm
    [[ "${gpu_confirm:-N}" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
fi

# Check Vulkan support
if command -v vulkaninfo &>/dev/null && vulkaninfo --summary 2>/dev/null | grep -qi "radv\|amd"; then
    ok "Vulkan (RADV) driver detected"
elif command -v vulkaninfo &>/dev/null; then
    warn "Vulkan found but RADV driver not detected. Installing vulkan-radeon..."
    sudo pacman -S --needed --noconfirm vulkan-radeon
else
    warn "vulkaninfo not found. Installing Vulkan packages..."
    sudo pacman -S --needed --noconfirm vulkan-radeon vulkan-tools
fi

# ── Install Ollama ──
step "2/9: Installing Ollama"

if command -v ollama &>/dev/null; then
    ok "Ollama already installed: $(ollama --version 2>/dev/null || echo 'version unknown')"
else
    info "Installing ollama-rocm (includes Vulkan GPU support)..."

    # Prefer pacman packages (verified by distro maintainers)
    if pacman -Si ollama-rocm &>/dev/null 2>&1; then
        sudo pacman -S --needed --noconfirm ollama-rocm
    elif pacman -Si ollama &>/dev/null 2>&1; then
        sudo pacman -S --needed --noconfirm ollama
        warn "Installed base 'ollama' package. For best GPU performance, consider 'ollama-rocm' from AUR."
    else
        # Fallback: download installer to a temp file for inspection
        info "Not in pacman repos. Downloading Ollama installer for review..."
        INSTALLER_PATH=$(mktemp /tmp/ollama-install-XXXXXX.sh)
        curl -fsSL https://ollama.com/install.sh -o "$INSTALLER_PATH"
        warn "Downloaded installer to: $INSTALLER_PATH"
        warn "You can inspect it before running: less $INSTALLER_PATH"
        read -p "Execute the Ollama installer? [y/N] " run_confirm
        if [[ "${run_confirm:-N}" =~ ^[Yy]$ ]]; then
            sh "$INSTALLER_PATH"
        else
            error "Ollama not installed. Install manually from https://ollama.com"
            rm -f "$INSTALLER_PATH"
            exit 1
        fi
        rm -f "$INSTALLER_PATH"
    fi
    ok "Ollama installed"
fi

# ── Configure Vulkan Backend & Tuning ──
step "3/9: Configuring GPU acceleration"

info "Setting up Vulkan (RADV) backend and performance tuning..."

OVERRIDE_DIR="/etc/systemd/system/ollama.service.d"
OVERRIDE_FILE="$OVERRIDE_DIR/override.conf"

# Check for existing override
if [[ -f "$OVERRIDE_FILE" ]]; then
    warn "Existing Ollama override found at $OVERRIDE_FILE"
    read -p "Overwrite with recommended GPU tuning? [Y/n] " ow_confirm
    if [[ "${ow_confirm:-Y}" =~ ^[Nn]$ ]]; then
        info "Skipping GPU tuning override."
    fi
fi

if [[ ! -f "$OVERRIDE_FILE" ]] || [[ ! "${ow_confirm:-Y}" =~ ^[Nn]$ ]]; then
    sudo mkdir -p "$OVERRIDE_DIR"
    sudo tee "$OVERRIDE_FILE" > /dev/null << 'OVERRIDE'
[Service]
# Force Vulkan (RADV) backend — faster than ROCm on RDNA 4 (Wave32 hardware)
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_MULTIUSER_CACHE=1"
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_KEEP_ALIVE=10m"
# Bind to localhost only — not accessible from other machines
Environment="OLLAMA_HOST=127.0.0.1:11434"
# Force RADV Vulkan driver (not AMDVLK)
Environment="AMD_VULKAN_ICD=RADV"
OVERRIDE
    ok "GPU tuning applied (flash attention, q8 KV cache, Vulkan RADV, localhost-only)"
fi

# Start and enable Ollama
sudo systemctl daemon-reload
sudo systemctl enable --now ollama.service

# Wait for Ollama to be ready
info "Waiting for Ollama to start..."
for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        ok "Ollama is running"
        break
    fi
    sleep 1
    if [[ $i -eq 30 ]]; then
        error "Ollama didn't start in 30 seconds. Check: journalctl -u ollama"
        exit 1
    fi
done

# ── Pull Models ──
step "4/9: Downloading AI models (this takes a while)"

echo ""
echo "Pulling 3 models for legal work + embedding model for document search:"
echo "  1. gemma3:12b       (8GB)   — Fast, great for summarization and drafting"
echo "  2. qwen3:14b        (9GB)   — Strong instruction following, structured analysis"
echo "  3. mistral-small    (14GB)  — Most capable, best for complex reasoning"
echo "  4. nomic-embed-text (274MB) — Embedding model for document upload (RAG)"
echo ""

models=("gemma3:12b" "qwen3:14b" "mistral-small:24b" "nomic-embed-text")

for model in "${models[@]}"; do
    if ollama list 2>/dev/null | grep -q "$(echo "$model" | cut -d: -f1)"; then
        ok "$model already downloaded"
    else
        info "Pulling $model..."
        ollama pull "$model"
        ok "$model ready"
    fi
done

# ── Create Legal Presets ──
step "5/9: Creating legal presets (specialized models)"

info "Building legal-tuned model presets from Modelfiles..."

modelfiles=("contract-reviewer" "depo-summarizer" "memo-drafter" "clause-identifier" "legal-reviewer")

for name in "${modelfiles[@]}"; do
    modelfile="$SCRIPT_DIR/Modelfile.$name"
    if [[ -f "$modelfile" ]]; then
        if ollama list 2>/dev/null | grep -q "$name"; then
            ok "$name already exists"
        else
            info "Creating $name..."
            ollama create "$name" -f "$modelfile"
            ok "$name ready"
        fi
    else
        warn "Modelfile.$name not found in $SCRIPT_DIR — skipping"
    fi
done

# ── Install Docker (if needed for Open WebUI) ──
step "6/9: Setting up Docker"

if command -v docker &>/dev/null; then
    ok "Docker already installed"
else
    info "Installing Docker..."
    sudo pacman -S --needed --noconfirm docker docker-compose
    sudo systemctl enable --now docker.service

    warn "Docker requires your user to be in the 'docker' group."
    warn "Note: The docker group grants root-equivalent access on this machine."
    read -p "Add $USER to the docker group? [Y/n] " docker_confirm
    if [[ "${docker_confirm:-Y}" =~ ^[Nn]$ ]]; then
        info "Skipping. You'll need to use 'sudo docker' for commands."
    else
        sudo usermod -aG docker "$USER"
        warn "Added $USER to docker group. Log out and back in for it to take effect."
    fi
    warn "For now, using sudo for Docker commands..."
fi

# Ensure Docker is running
DOCKER_CMD=(docker)
if ! docker info &>/dev/null 2>&1; then
    if sudo docker info &>/dev/null 2>&1; then
        DOCKER_CMD=(sudo docker)
        warn "Using 'sudo docker' (log out and back in to use without sudo)"
    else
        sudo systemctl start docker.service
        sleep 2
        if sudo docker info &>/dev/null 2>&1; then
            DOCKER_CMD=(sudo docker)
        else
            error "Docker won't start. Try: sudo systemctl start docker"
            error "You can install Open WebUI manually later (see README)."
            DOCKER_CMD=()
        fi
    fi
fi

# ── Install Open WebUI ──
step "7/9: Installing Open WebUI (chat interface)"

# Pin to a specific release tag for supply chain safety
OPEN_WEBUI_IMAGE="ghcr.io/open-webui/open-webui:v0.6.5"

if [[ ${#DOCKER_CMD[@]} -gt 0 ]]; then
    if "${DOCKER_CMD[@]}" ps -a --format '{{.Names}}' 2>/dev/null | grep -q "open-webui"; then
        ok "Open WebUI container already exists"
        "${DOCKER_CMD[@]}" start open-webui 2>/dev/null || true
    else
        info "Starting Open WebUI container (with RAG document support)..."
        # Bind to 127.0.0.1 only — not accessible from other machines on the network
        "${DOCKER_CMD[@]}" run -d \
            -p 127.0.0.1:3000:8080 \
            --add-host=host.docker.internal:host-gateway \
            -v open-webui:/app/backend/data \
            -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
            -e RAG_EMBEDDING_ENGINE=ollama \
            -e RAG_EMBEDDING_MODEL=nomic-embed-text \
            -e CHUNK_SIZE=512 \
            -e CHUNK_OVERLAP=75 \
            -e ENABLE_RAG_HYBRID_SEARCH=true \
            -e RAG_SYSTEM_CONTEXT=true \
            -e AUDIO_STT_ENGINE=whisper \
            -e WHISPER_MODEL=base \
            --name open-webui \
            --restart always \
            "$OPEN_WEBUI_IMAGE"
        ok "Open WebUI is running (localhost only, RAG enabled)"
    fi
else
    warn "Docker not available. Install Open WebUI manually:"
    echo "  pip install open-webui && open-webui serve --port 3000"
fi

# ── Optional: LanguageTool ──
step "8/9: Optional — LanguageTool (grammar checker backend)"

echo ""
echo "LanguageTool is a grammar/style checker that powers the legal-grammar-checker tool."
echo "It runs as a Docker container (~500MB download). This is optional."
echo ""
read -p "Install LanguageTool? [y/N] " lt_confirm
if [[ "${lt_confirm:-N}" =~ ^[Yy]$ ]] && [[ ${#DOCKER_CMD[@]} -gt 0 ]]; then
    if "${DOCKER_CMD[@]}" ps -a --format '{{.Names}}' 2>/dev/null | grep -q "languagetool"; then
        ok "LanguageTool container already exists"
        "${DOCKER_CMD[@]}" start languagetool 2>/dev/null || true
    else
        info "Starting LanguageTool container..."
        "${DOCKER_CMD[@]}" run -d \
            -p 127.0.0.1:8081:8010 \
            --name languagetool \
            --restart unless-stopped \
            silviof/docker-languagetool
        ok "LanguageTool is running (localhost:8081)"
    fi
else
    info "Skipping LanguageTool. You can install it later — see README.md."
fi

# ── Quick Test ──
step "9/9: Running quick test"

info "Testing gemma3:12b with a simple legal prompt..."
echo ""

test_response=$(curl -s --max-time 60 http://localhost:11434/api/generate \
    -d '{
        "model": "gemma3:12b",
        "prompt": "In one paragraph, explain what attorney-client privilege protects.",
        "stream": false,
        "options": {"num_ctx": 8192}
    }' 2>&1)

if echo "$test_response" | python3 -c "import sys,json; print(json.load(sys.stdin)['response'][:500])" 2>/dev/null; then
    echo ""
    ok "Model is responding correctly!"

    # Show speed metrics
    total_ms=$(echo "$test_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_duration',0)//1000000)" 2>/dev/null || echo "?")
    eval_count=$(echo "$test_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('eval_count',0))" 2>/dev/null || echo "?")
    info "Generated $eval_count tokens in ${total_ms}ms"
else
    warn "Test didn't return expected output. Ollama may still be loading the model."
    warn "Try manually: ollama run gemma3:12b"
fi

# ── Verify Security ──
echo ""
info "Verifying network security..."
if ss -tlnp 2>/dev/null | grep ":11434" | grep -q "127.0.0.1"; then
    ok "Ollama bound to localhost only (127.0.0.1:11434)"
else
    warn "Could not verify Ollama bind address. Check: ss -tlnp | grep 11434"
fi
if ss -tlnp 2>/dev/null | grep ":3000" | grep -q "127.0.0.1"; then
    ok "Open WebUI bound to localhost only (127.0.0.1:3000)"
else
    warn "Could not verify Open WebUI bind address. Check: ss -tlnp | grep 3000"
fi
if ss -tlnp 2>/dev/null | grep ":8081" &>/dev/null; then
    if ss -tlnp 2>/dev/null | grep ":8081" | grep -q "127.0.0.1"; then
        ok "LanguageTool bound to localhost only (127.0.0.1:8081)"
    else
        warn "Could not verify LanguageTool bind address. Check: ss -tlnp | grep 8081"
    fi
fi

# ── Done ──
echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""
echo "Open your browser to:"
echo ""
echo -e "  ${BOLD}http://localhost:3000${NC}"
echo ""
echo "First time: Create a local account (this is just for the UI,"
echo "it stays on your machine — no email verification needed)."
echo ""
echo "Available models (select from dropdown in chat):"
echo "  - gemma3:12b      Fast daily work, summaries, drafting"
echo "  - qwen3:14b       Structured analysis, detailed responses"
echo "  - mistral-small   Complex reasoning, best quality (slower)"
echo ""
echo "Legal presets (specialized system prompts):"
echo "  - contract-reviewer  Contract analysis (qwen3:14b)"
echo "  - depo-summarizer    Deposition summaries (gemma3:12b)"
echo "  - memo-drafter       Legal memo drafting (mistral-small)"
echo "  - clause-identifier  Structured clause extraction (qwen3:14b)"
echo "  - legal-reviewer     Writing review and proofreading (qwen3:14b)"
echo ""
echo "Tools (import manually in Open WebUI > Workspace > Tools > +):"
echo "  - legal-grammar-checker    Grammar/style checking (needs LanguageTool)"
echo "  - legal-readability-scorer Readability metrics for legal text"
echo "  - contract-comparator      Side-by-side document comparison"
echo "  See tools/ folder and README.md for import instructions."
echo ""
echo "Voice-to-text: Click the mic icon in the chat input to dictate."
echo "  Whisper (base model) downloads automatically on first use (~74MB)."
echo ""
echo "Document upload: Create a Knowledge collection in Open WebUI,"
echo "upload PDFs, then reference them with # in chat. See README.md."
echo ""
echo "See README.md for:"
echo "  - How to use document upload (RAG)"
echo "  - Legal preset details and when to use each"
echo "  - Tools setup and usage instructions"
echo "  - Example prompts for legal work"
echo "  - Important limitations to understand"
echo "  - Troubleshooting tips"
echo ""
echo -e "${YELLOW}IMPORTANT: These models are not as accurate as GPT-4 or Claude.${NC}"
echo -e "${YELLOW}Always verify outputs, especially case citations and legal claims.${NC}"
echo ""
