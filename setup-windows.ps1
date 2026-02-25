# ============================================================================
# Local AI Setup for Legal Work — Windows Edition
#
# Target: Windows 10/11 with NVIDIA or AMD GPU (12GB+ VRAM)
#
# This script installs and configures:
#   1. Ollama (local AI model server with GPU acceleration)
#   2. Open WebUI (ChatGPT-like browser interface via Docker)
#   3. Recommended models for legal work
#
# Usage:
#   Right-click this file → "Run with PowerShell"
#   OR open PowerShell as Administrator and run: .\setup-windows.ps1
#
# Everything runs locally. No data leaves your machine.
# ============================================================================

$ErrorActionPreference = "Stop"

# ── Helpers ──
function Write-Step { param($num, $msg) Write-Host "`n── Step $num ──" -ForegroundColor White; Write-Host "  $msg" -ForegroundColor Cyan }
function Write-Ok { param($msg) Write-Host "  [OK]    $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [WARN]  $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "  [ERROR] $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "  [INFO]  $msg" -ForegroundColor Blue }

# ── Check Admin ──
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warn "Not running as Administrator. Some steps may require elevation."
    Write-Warn "If installation fails, right-click PowerShell → 'Run as Administrator'"
    Write-Host ""
}

# ── Banner ──
Write-Host ""
Write-Host "============================================" -ForegroundColor White
Write-Host "  Local AI Setup for Legal Work" -ForegroundColor White
Write-Host "  Windows Edition" -ForegroundColor White
Write-Host "============================================" -ForegroundColor White
Write-Host ""
Write-Host "This will install:"
Write-Host "  - Ollama (AI model server with GPU acceleration)"
Write-Host "  - Docker Desktop + Open WebUI (browser-based chat interface)"
Write-Host "  - 3 language models optimized for legal work (~31GB download)"
Write-Host ""
Write-Host "Estimated time: 20-40 minutes (depending on internet speed)"
Write-Host "Disk space needed: ~40GB"
Write-Host ""
$confirm = Read-Host "Continue? [Y/n]"
if ($confirm -and $confirm -notmatch '^[Yy]') { Write-Host "Aborted."; exit 0 }

# ── Step 1: Check GPU ──
Write-Step "1/7" "Checking hardware"

$gpu = Get-CimInstance -ClassName Win32_VideoController | Select-Object -ExpandProperty Name
$hasNvidia = $gpu | Where-Object { $_ -match "NVIDIA" }
$hasAmd = $gpu | Where-Object { $_ -match "AMD|Radeon" }

if ($hasNvidia) {
    Write-Ok "NVIDIA GPU detected: $($hasNvidia -join ', ')"
    Write-Info "Ollama will use CUDA for GPU acceleration"
    $gpuType = "nvidia"
} elseif ($hasAmd) {
    Write-Ok "AMD GPU detected: $($hasAmd -join ', ')"
    Write-Info "Ollama will use Vulkan for GPU acceleration"
    $gpuType = "amd"
} else {
    Write-Warn "No dedicated GPU detected. Models will run on CPU (much slower)."
    $gpuConfirm = Read-Host "Continue anyway? [y/N]"
    if (-not $gpuConfirm -or $gpuConfirm -notmatch '^[Yy]') { Write-Host "Aborted."; exit 0 }
    $gpuType = "cpu"
}

# Check VRAM
try {
    $vram = Get-CimInstance -ClassName Win32_VideoController | Select-Object -First 1 -ExpandProperty AdapterRAM
    $vramGB = [math]::Round($vram / 1GB, 1)
    if ($vramGB -gt 0) {
        Write-Info "VRAM: ${vramGB}GB"
        if ($vramGB -lt 12) {
            Write-Warn "Less than 12GB VRAM. mistral-small:24b may not fit — will pull smaller models only."
        }
    }
} catch {
    Write-Info "Could not detect VRAM size (this is normal on some systems)"
    $vramGB = 0
}

# ── Step 2: Install Ollama ──
Write-Step "2/7" "Installing Ollama"

$ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$ollamaInPath = Get-Command ollama -ErrorAction SilentlyContinue

if ($ollamaInPath -or (Test-Path $ollamaPath)) {
    Write-Ok "Ollama already installed"
} else {
    Write-Info "Downloading Ollama installer..."

    $installerUrl = "https://ollama.com/download/OllamaSetup.exe"
    $installerPath = "$env:TEMP\OllamaSetup.exe"

    try {
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
        Write-Info "Running Ollama installer (follow the prompts if any appear)..."
        Start-Process -FilePath $installerPath -Wait
        Write-Ok "Ollama installed"
    } catch {
        Write-Err "Failed to download Ollama. Please install manually from https://ollama.com/download"
        Write-Host "After installing Ollama, run this script again."
        Read-Host "Press Enter to exit"
        exit 1
    }

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# ── Step 3: Configure GPU tuning ──
Write-Step "3/7" "Configuring GPU acceleration"

# Set environment variables for Ollama performance tuning
$envVars = @{
    "OLLAMA_FLASH_ATTENTION" = "1"
    "OLLAMA_KV_CACHE_TYPE"   = "q8_0"
    "OLLAMA_KEEP_ALIVE"      = "10m"
    "OLLAMA_NUM_PARALLEL"    = "2"
}

foreach ($key in $envVars.Keys) {
    $current = [System.Environment]::GetEnvironmentVariable($key, "User")
    if ($current -ne $envVars[$key]) {
        [System.Environment]::SetEnvironmentVariable($key, $envVars[$key], "User")
        $env:$key = $envVars[$key]
    }
}

Write-Ok "GPU tuning applied (flash attention, q8 KV cache)"

if ($gpuType -eq "amd") {
    Write-Info "AMD GPU: Ollama will auto-detect Vulkan on Windows"
}

# ── Step 4: Start Ollama and wait ──
Write-Step "4/7" "Starting Ollama"

# Check if Ollama is already running
$ollamaRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) { $ollamaRunning = $true }
} catch {}

if (-not $ollamaRunning) {
    Write-Info "Starting Ollama service..."

    # Try starting Ollama
    $ollamaExe = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollamaExe) {
        $ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    } else {
        $ollamaExe = $ollamaExe.Source
    }

    Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
    Write-Info "Waiting for Ollama to start..."

    $attempts = 0
    while ($attempts -lt 30) {
        Start-Sleep -Seconds 1
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) { break }
        } catch {}
        $attempts++
    }

    if ($attempts -ge 30) {
        Write-Err "Ollama didn't start in 30 seconds."
        Write-Err "Try starting it manually: open Ollama from the Start menu."
        Read-Host "Press Enter after Ollama is running"
    }
}

Write-Ok "Ollama is running"

# ── Step 5: Pull Models ──
Write-Step "5/7" "Downloading AI models (this takes a while)"

Write-Host ""
Write-Host "  Pulling 3 models optimized for legal work:"
Write-Host "    1. gemma3:12b    (8GB)  - Fast, great for summarization and drafting"
Write-Host "    2. qwen3:14b     (9GB)  - Strong instruction following, structured analysis"
Write-Host "    3. mistral-small (14GB)  - Most capable, best for complex reasoning"
Write-Host ""

$models = @("gemma3:12b", "qwen3:14b")

# Only pull mistral-small if we have enough VRAM
if ($vramGB -ge 12 -or $vramGB -eq 0) {
    $models += "mistral-small:24b"
} else {
    Write-Warn "Skipping mistral-small:24b (needs 14GB VRAM, you have ${vramGB}GB)"
}

foreach ($model in $models) {
    Write-Info "Pulling $model..."
    & ollama pull $model
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "$model ready"
    } else {
        Write-Warn "Failed to pull $model — you can try later with: ollama pull $model"
    }
}

# ── Step 6: Install Docker Desktop + Open WebUI ──
Write-Step "6/7" "Installing Open WebUI (chat interface)"

$dockerAvailable = Get-Command docker -ErrorAction SilentlyContinue

if (-not $dockerAvailable) {
    Write-Info "Docker Desktop is needed for the chat interface."
    Write-Info ""
    Write-Host "  Two options:" -ForegroundColor White
    Write-Host ""
    Write-Host "  Option A: Install Docker Desktop (recommended)" -ForegroundColor Cyan
    Write-Host "    1. Download from: https://www.docker.com/products/docker-desktop/"
    Write-Host "    2. Install and restart your computer"
    Write-Host "    3. Run this script again"
    Write-Host ""
    Write-Host "  Option B: Use pip instead (no Docker needed)" -ForegroundColor Cyan
    Write-Host "    1. Open a new PowerShell window"
    Write-Host "    2. Run: pip install open-webui"
    Write-Host "    3. Run: open-webui serve --port 3000"
    Write-Host "    4. Open http://localhost:3000 in your browser"
    Write-Host ""

    $pipAvailable = Get-Command pip -ErrorAction SilentlyContinue
    if ($pipAvailable) {
        $usePip = Read-Host "Python/pip detected. Install Open WebUI via pip now? [Y/n]"
        if (-not $usePip -or $usePip -match '^[Yy]') {
            Write-Info "Installing Open WebUI via pip..."
            & pip install open-webui
            if ($LASTEXITCODE -eq 0) {
                Write-Ok "Open WebUI installed via pip"
                Write-Info "Starting Open WebUI..."
                Start-Process -FilePath "open-webui" -ArgumentList "serve", "--port", "3000" -WindowStyle Hidden
                Start-Sleep -Seconds 5
                Write-Ok "Open WebUI is running"
                $webUIInstalled = $true
            } else {
                Write-Warn "pip install failed. Try manually: pip install open-webui"
                $webUIInstalled = $false
            }
        } else {
            $webUIInstalled = $false
        }
    } else {
        Write-Warn "Neither Docker nor pip found."
        Write-Warn "Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
        Write-Warn "Or install Python from https://www.python.org/ then run: pip install open-webui"
        $webUIInstalled = $false
    }
} else {
    # Docker is available — use it
    $existing = docker ps -a --format "{{.Names}}" 2>$null | Where-Object { $_ -eq "open-webui" }
    if ($existing) {
        Write-Ok "Open WebUI container already exists"
        docker start open-webui 2>$null
    } else {
        Write-Info "Starting Open WebUI container..."
        docker run -d `
            -p 3000:8080 `
            --add-host=host.docker.internal:host-gateway `
            -v open-webui:/app/backend/data `
            --name open-webui `
            --restart always `
            ghcr.io/open-webui/open-webui:main
        Write-Ok "Open WebUI is running"
    }
    $webUIInstalled = $true
}

# ── Step 7: Quick Test ──
Write-Step "7/7" "Running quick test"

Write-Info "Testing gemma3:12b with a simple legal prompt..."
Write-Host ""

try {
    $body = @{
        model   = "gemma3:12b"
        prompt  = "In one paragraph, explain what attorney-client privilege protects."
        stream  = $false
        options = @{ num_ctx = 8192 }
    } | ConvertTo-Json -Depth 3

    $testResponse = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 120

    if ($testResponse.response) {
        Write-Host "  $($testResponse.response.Substring(0, [Math]::Min(500, $testResponse.response.Length)))" -ForegroundColor Gray
        Write-Host ""
        Write-Ok "Model is responding correctly!"

        $totalMs = [math]::Round($testResponse.total_duration / 1000000)
        $evalCount = $testResponse.eval_count
        Write-Info "Generated $evalCount tokens in ${totalMs}ms"
    }
} catch {
    Write-Warn "Test didn't complete. Ollama may still be loading the model."
    Write-Warn "Try manually in a terminal: ollama run gemma3:12b"
}

# ── Done ──
Write-Host ""
Write-Host "============================================" -ForegroundColor White
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor White
Write-Host ""

if ($webUIInstalled) {
    Write-Host "  Open your browser to:" -ForegroundColor White
    Write-Host ""
    Write-Host "    http://localhost:3000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  First time: Create a local account (stays on your machine)." -ForegroundColor Gray
} else {
    Write-Host "  Ollama is running! You can chat in the terminal:" -ForegroundColor White
    Write-Host ""
    Write-Host "    ollama run gemma3:12b" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  For the browser UI, install Docker Desktop or run:" -ForegroundColor Gray
    Write-Host "    pip install open-webui && open-webui serve --port 3000" -ForegroundColor Gray
}

Write-Host ""
Write-Host "  Available models (select from dropdown in chat):" -ForegroundColor White
Write-Host "    - gemma3:12b      Fast daily work, summaries, drafting"
Write-Host "    - qwen3:14b       Structured analysis, detailed responses"
if ($vramGB -ge 12 -or $vramGB -eq 0) {
    Write-Host "    - mistral-small   Complex reasoning, best quality (slower)"
}
Write-Host ""
Write-Host "  See README.md for example prompts and limitations." -ForegroundColor Gray
Write-Host ""
Write-Host "  IMPORTANT: These models are not as accurate as GPT-4 or Claude." -ForegroundColor Yellow
Write-Host "  Always verify outputs, especially case citations and legal claims." -ForegroundColor Yellow
Write-Host ""

# Open browser if WebUI is running
if ($webUIInstalled) {
    $openBrowser = Read-Host "Open browser to http://localhost:3000 now? [Y/n]"
    if (-not $openBrowser -or $openBrowser -match '^[Yy]') {
        Start-Process "http://localhost:3000"
    }
}
