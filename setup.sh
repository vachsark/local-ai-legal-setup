#!/usr/bin/env bash
# ============================================================================
# Local AI Setup for Legal Work
# Target: Arch Linux + AMD RX 9070 XT (16GB VRAM)
#
# This script installs and configures:
#   1. Ollama (local AI model server with GPU acceleration)
#   2. Open WebUI (ChatGPT-like browser interface)
#   3. Recommended models for legal work
#   4. GPU tuning for optimal performance
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
#
# Everything runs locally. No data leaves your machine.
# ============================================================================

set -euo pipefail

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
echo "  Arch Linux + AMD RX 9070 XT"
echo "============================================"
echo -e "${NC}"
echo "This will install:"
echo "  - Ollama (AI model server with GPU acceleration)"
echo "  - Open WebUI (browser-based chat interface)"
echo "  - 3 language models optimized for legal work (~31GB download)"
echo ""
echo "Estimated time: 15-30 minutes (depending on internet speed)"
echo "Disk space needed: ~35GB"
echo ""
read -p "Continue? [Y/n] " confirm
[[ "${confirm:-Y}" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

# ── Check for AMD GPU ──
step "1/7: Checking hardware"

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
step "2/7: Installing Ollama"

if command -v ollama &>/dev/null; then
    ok "Ollama already installed: $(ollama --version 2>/dev/null || echo 'version unknown')"
else
    info "Installing ollama-rocm (includes Vulkan GPU support)..."

    # Prefer ollama-rocm from official repos, fall back to AUR
    if pacman -Si ollama-rocm &>/dev/null 2>&1; then
        sudo pacman -S --needed --noconfirm ollama-rocm
    elif pacman -Si ollama &>/dev/null 2>&1; then
        # Base ollama package (may not have full GPU support)
        sudo pacman -S --needed --noconfirm ollama
        warn "Installed base 'ollama' package. For best GPU performance, consider 'ollama-rocm' from AUR."
    else
        # Fallback: official install script
        info "Not in pacman repos. Using Ollama's official installer..."
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    ok "Ollama installed"
fi

# ── Configure Vulkan Backend & Tuning ──
step "3/7: Configuring GPU acceleration"

info "Setting up Vulkan (RADV) backend and performance tuning..."

# Create systemd override directory
sudo mkdir -p /etc/systemd/system/ollama.service.d/

# Write tuning override
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null << 'OVERRIDE'
[Service]
# Force Vulkan (RADV) backend — faster than ROCm on RDNA 4 (Wave32 hardware)
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_MULTIUSER_CACHE=1"
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_KEEP_ALIVE=10m"
# Force RADV Vulkan driver (not AMDVLK)
Environment="AMD_VULKAN_ICD=RADV"
OVERRIDE

ok "GPU tuning applied (flash attention, q8 KV cache, Vulkan RADV)"

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
step "4/7: Downloading AI models (this takes a while)"

echo ""
echo "Pulling 3 models optimized for legal work:"
echo "  1. gemma3:12b   (8GB)  — Fast, great for summarization and drafting"
echo "  2. qwen3:14b    (9GB)  — Strong instruction following, structured analysis"
echo "  3. mistral-small (14GB) — Most capable, best for complex reasoning"
echo ""

models=("gemma3:12b" "qwen3:14b" "mistral-small:24b")

for model in "${models[@]}"; do
    if ollama list 2>/dev/null | grep -q "$(echo "$model" | cut -d: -f1)"; then
        ok "$model already downloaded"
    else
        info "Pulling $model..."
        ollama pull "$model"
        ok "$model ready"
    fi
done

# ── Install Docker (if needed for Open WebUI) ──
step "5/7: Setting up Docker"

if command -v docker &>/dev/null; then
    ok "Docker already installed"
else
    info "Installing Docker..."
    sudo pacman -S --needed --noconfirm docker docker-compose
    sudo systemctl enable --now docker.service
    sudo usermod -aG docker "$USER"
    warn "Added your user to the 'docker' group. You may need to log out and back in."
    warn "For now, using sudo for the Docker commands..."
fi

# Ensure Docker is running
if ! docker info &>/dev/null 2>&1; then
    if sudo docker info &>/dev/null 2>&1; then
        DOCKER_CMD="sudo docker"
        warn "Using 'sudo docker' (log out and back in to use without sudo)"
    else
        sudo systemctl start docker.service
        sleep 2
        if sudo docker info &>/dev/null 2>&1; then
            DOCKER_CMD="sudo docker"
        else
            error "Docker won't start. Try: sudo systemctl start docker"
            error "You can install Open WebUI manually later (see README)."
            DOCKER_CMD=""
        fi
    fi
else
    DOCKER_CMD="docker"
fi

# ── Install Open WebUI ──
step "6/7: Installing Open WebUI (chat interface)"

if [[ -n "${DOCKER_CMD:-}" ]]; then
    if $DOCKER_CMD ps -a --format '{{.Names}}' 2>/dev/null | grep -q "open-webui"; then
        ok "Open WebUI container already exists"
        # Make sure it's running
        $DOCKER_CMD start open-webui 2>/dev/null || true
    else
        info "Starting Open WebUI container..."
        $DOCKER_CMD run -d \
            -p 3000:8080 \
            --add-host=host.docker.internal:host-gateway \
            -v open-webui:/app/backend/data \
            --name open-webui \
            --restart always \
            ghcr.io/open-webui/open-webui:main
        ok "Open WebUI is running"
    fi
else
    warn "Docker not available. Install Open WebUI manually:"
    echo "  pip install open-webui && open-webui serve --port 3000"
fi

# ── Quick Test ──
step "7/7: Running quick test"

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
echo "See README.md for:"
echo "  - How to use each model effectively"
echo "  - Example prompts for legal work"
echo "  - Important limitations to understand"
echo "  - Troubleshooting tips"
echo ""
echo -e "${YELLOW}IMPORTANT: These models are not as accurate as GPT-4 or Claude.${NC}"
echo -e "${YELLOW}Always verify outputs, especially case citations and legal claims.${NC}"
echo ""
