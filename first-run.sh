#!/usr/bin/env bash
# first-run.sh — Onboarding experience: welcome message, live demo, next steps
# Run this after setup.sh completes to see legal-check in action immediately.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEGAL_CHECK="$SCRIPT_DIR/legal-check"

# ── Colors ──────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

print_box() {
    local width=62
    local msg="$1"
    local pad=$(( (width - ${#msg}) / 2 ))
    printf "${BOLD}%s${NC}\n" "$(printf '═%.0s' $(seq 1 $width))"
    printf "${BOLD}%*s%s%*s${NC}\n" "$pad" "" "$msg" "$pad" ""
    printf "${BOLD}%s${NC}\n" "$(printf '═%.0s' $(seq 1 $width))"
}

pause() {
    local secs="${1:-2}"
    sleep "$secs"
}

# ── Welcome ──────────────────────────────────────────────────────────────────────

clear
echo ""
print_box "Welcome to Local AI for Legal Work"
echo ""
echo -e "${GREEN}Your private AI legal assistant is ready.${NC}"
echo ""
echo "  Everything you do here stays on this machine."
echo "  No subscription. No cloud. No data leaving your office."
echo ""
pause 3

# ── Check prerequisites ──────────────────────────────────────────────────────────

# Guard: Ollama must be installed before first-run can work
if ! command -v ollama &>/dev/null; then
    echo -e "${YELLOW}[!] Ollama is not installed yet.${NC}"
    echo ""
    echo "  first-run.sh is meant to be run after the setup script."
    echo "  Run setup first:"
    echo ""

    case "$(uname)" in
        Darwin)
            echo "    chmod +x setup-mac.sh && ./setup-mac.sh"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "    Double-click setup-windows.bat"
            ;;
        *)
            echo "    chmod +x setup.sh && ./setup.sh"
            ;;
    esac

    echo ""
    exit 1
fi

# Verify Ollama is running
if ! curl -s --max-time 5 http://localhost:11434/api/tags &>/dev/null; then
    echo -e "${YELLOW}[!] Ollama isn't running. Starting it...${NC}"

    # Try systemd first (Linux), then direct serve (macOS / no systemd)
    started=0
    if command -v systemctl &>/dev/null && systemctl list-units --type=service 2>/dev/null | grep -q ollama; then
        sudo systemctl start ollama.service 2>/dev/null && started=1
    fi
    if [[ $started -eq 0 ]] && command -v ollama &>/dev/null; then
        ollama serve &>/dev/null &
    fi

    echo "    Waiting for Ollama..."
    for i in $(seq 1 20); do
        sleep 1
        if curl -s --max-time 3 http://localhost:11434/api/tags &>/dev/null; then
            echo -e "${GREEN}[+] Ollama is running${NC}"
            break
        fi
        if [[ $i -eq 20 ]]; then
            echo -e "${YELLOW}[!] Couldn't start Ollama automatically.${NC}"
            echo ""
            echo "  Try starting it manually:"
            echo "    Linux:   sudo systemctl start ollama.service"
            echo "    macOS:   ollama serve"
            echo ""
            echo "  Then re-run: $0"
            exit 1
        fi
    done
fi

# Find a working model for the demo
DEMO_MODEL=""
for candidate in email-polisher legal-reviewer gemma3:12b qwen3.5:9b; do
    if (ollama list 2>/dev/null || true) | grep -q "${candidate%%:*}"; then
        DEMO_MODEL="$candidate"
        break
    fi
done

if [[ -z "$DEMO_MODEL" ]]; then
    echo -e "${YELLOW}[!] No models found.${NC}"
    echo ""
    echo "  Models haven't been downloaded yet. Run the setup script first:"
    echo ""

    case "$(uname)" in
        Darwin)
            echo "    chmod +x setup-mac.sh && ./setup-mac.sh"
            ;;
        *)
            echo "    chmod +x setup.sh && ./setup.sh"
            ;;
    esac

    echo ""
    echo "  The setup script downloads models (~32GB) and sets everything up."
    exit 1
fi

# ── Demo ─────────────────────────────────────────────────────────────────────────

echo -e "${BOLD}── Live Demo ──────────────────────────────────────────────────${NC}"
echo ""
echo "Let's run a real example. Here's an email draft that needs polish:"
echo ""
echo -e "${DIM}  Subject: Following up"
echo ""
echo "  Hey John,"
echo ""
echo "  I wanted to followup on our conversation from last week's meeting"
echo "  about the contract. Myself and the team has reviewed it and we think"
echo "  there's some issues that needs to be addressed before we can move forward."
echo "  Please advise at your earliest convenience."
echo ""
echo -e "  Thanks, Sarah${NC}"
echo ""

pause 2

echo -e "${BLUE}Running: legal-check -m email ...${NC}"
echo ""

# Write sample email to temp file
TMPFILE=$(mktemp /tmp/legal-demo-XXXXXX.txt)
trap 'rm -f "$TMPFILE"' EXIT

cat > "$TMPFILE" <<'EMAIL'
Hey John,

I wanted to followup on our conversation from last week's meeting about the contract. Myself and the team has reviewed it and we think there's some issues that needs to be addressed before we can move forward. Please advise at your earliest convenience.

Thanks, Sarah
EMAIL

# Run with the email-polisher if available, fallback to first available
if (ollama list 2>/dev/null || true) | grep -q "email-polisher"; then
    "$LEGAL_CHECK" -m email "$TMPFILE"
elif [[ -n "$DEMO_MODEL" ]]; then
    "$LEGAL_CHECK" "$TMPFILE"
fi

# ── Next steps ───────────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}── You're ready. Here's what to try next: ─────────────────────${NC}"
echo ""
echo -e "  ${GREEN}1. Check a document${NC}"
echo "     legal-check -d your-contract.pdf \"What are the payment terms?\""
echo ""
echo -e "  ${GREEN}2. Summarize a filing${NC}"
echo "     legal-check -s motion.pdf"
echo ""
echo -e "  ${GREEN}3. Open an interactive session${NC}"
echo "     legal-check -i contract.pdf"
echo "     (Ask multiple questions without reloading the document)"
echo ""
echo -e "  ${GREEN}4. Use the chat interface${NC}"
echo "     Open your browser to: http://localhost:3000"
echo "     Use specialized models like contract-reviewer or depo-summarizer"
echo ""
echo -e "  ${GREEN}5. See all commands${NC}"
echo "     legal-check -h"
echo "     cat QUICKSTART.md"
echo ""

# ── Open browser ─────────────────────────────────────────────────────────────────

echo -e "${BOLD}── Opening the chat interface ─────────────────────────────────${NC}"
echo ""
echo "  Opening http://localhost:3000 in your browser..."
echo "  (Create a local account on first visit — username/password only,"
echo "   no email needed, stays on your machine)"
echo ""

pause 1

# Try to open browser — Linux and macOS
if command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:3000" &>/dev/null &
elif command -v open &>/dev/null; then
    open "http://localhost:3000" &>/dev/null &
else
    echo -e "${YELLOW}  Couldn't auto-open browser. Navigate to:${NC}"
    echo "  http://localhost:3000"
fi

echo -e "${GREEN}All done. Read QUICKSTART.md for a 2-minute reference guide.${NC}"
echo ""
