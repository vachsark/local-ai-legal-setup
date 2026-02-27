# ============================================================================
# Local AI Setup for Legal Work --Windows Edition
#
# Target: Windows 10/11 with NVIDIA or AMD GPU (12GB+ VRAM)
#
# This script installs and configures:
#   1. Ollama (local AI model server with GPU acceleration)
#   2. Open WebUI (ChatGPT-like browser interface via Docker)
#   3. Recommended models for legal work
#   4. Legal preset models with specialized system prompts
#   5. RAG (document upload) with legal-optimized settings
#
# Usage:
#   1. Open PowerShell as Administrator
#   2. Run: powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1
#
# If you get "running scripts is disabled on this system":
#   - Right-click this file -> Properties -> check "Unblock" -> OK
#   - Or run: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#
# After setup, all AI inference runs locally. No data leaves your machine.
# ============================================================================

$ErrorActionPreference = "Stop"

$scriptDir = $PSScriptRoot

# -- Helpers --
function Write-Step { param($num, $msg) Write-Host "`n-- Step $num --" -ForegroundColor White; Write-Host "  $msg" -ForegroundColor Cyan }
function Write-Ok { param($msg) Write-Host "  [OK]    $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [WARN]  $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "  [ERROR] $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "  [INFO]  $msg" -ForegroundColor Blue }

# -- Check Admin --
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warn "Not running as Administrator. Some steps may require elevation."
    Write-Warn "If installation fails, right-click PowerShell -> 'Run as Administrator'"
    Write-Host ""
}

# -- Banner --
Write-Host ""
Write-Host "============================================" -ForegroundColor White
Write-Host "  Local AI Setup for Legal Work" -ForegroundColor White
Write-Host "  Windows Edition" -ForegroundColor White
Write-Host "============================================" -ForegroundColor White
Write-Host ""
Write-Host "This will install:"
Write-Host "  - Ollama (AI model server with GPU acceleration)"
Write-Host "  - Docker Desktop + Open WebUI (browser-based chat interface)"
Write-Host "  - 3 language models, 3 legal presets, and an embedding model (~32GB download)"
Write-Host ""
Write-Host "Estimated time: 20-40 minutes (depending on internet speed)"
Write-Host "Disk space needed: ~40GB"
Write-Host ""
$confirm = Read-Host "Continue? [Y/n]"
if ($confirm -and $confirm -notmatch '^[Yy]') { Write-Host "Aborted."; exit 0 }

# -- Step 1: Check GPU --
Write-Step "1/8" "Checking hardware"

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
# Win32_VideoController.AdapterRAM is a 32-bit uint -- overflows above 4GB.
# The registry stores the real value as a 64-bit qword.
try {
    $vramGB = 0
    $regPath = "HKLM:\SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    $subkeys = Get-ChildItem $regPath -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -match '^\d+$' }
    foreach ($key in $subkeys) {
        $qwMem = (Get-ItemProperty $key.PSPath -ErrorAction SilentlyContinue).'HardwareInformation.qwMemorySize'
        if ($qwMem -and $qwMem -gt 0) {
            $candidate = [math]::Round($qwMem / 1GB, 1)
            if ($candidate -gt $vramGB) { $vramGB = $candidate }
        }
    }

    # Fallback to WMI if registry didn't work (still wrong for >4GB, but better than nothing)
    if ($vramGB -eq 0) {
        $vram = Get-CimInstance -ClassName Win32_VideoController | Select-Object -First 1 -ExpandProperty AdapterRAM
        $vramGB = [math]::Round($vram / 1GB, 1)
    }

    if ($vramGB -gt 0) {
        Write-Info "VRAM: ${vramGB}GB"
        if ($vramGB -lt 12) {
            Write-Warn "Less than 12GB VRAM. mistral-small:24b may not fit --will pull smaller models only."
        }
    }
} catch {
    Write-Info "Could not detect VRAM size (this is normal on some systems)"
    $vramGB = 0
}

# -- Step 2: Install Ollama --
Write-Step "2/8" "Installing Ollama"

$ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$ollamaInPath = Get-Command ollama -ErrorAction SilentlyContinue

if ($ollamaInPath -or (Test-Path $ollamaPath)) {
    Write-Ok "Ollama already installed"
} else {
    Write-Info "Downloading Ollama installer (this may take a minute)..."

    $installerUrl = "https://ollama.com/download/OllamaSetup.exe"
    $randomSuffix = [System.IO.Path]::GetRandomFileName().Replace(".", "")
    $installerPath = "$env:TEMP\OllamaSetup-$randomSuffix.exe"

    try {
        # Disable progress bar -- PowerShell 5.1's progress stream makes downloads 10-100x slower
        $oldProgress = $ProgressPreference
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
        $ProgressPreference = $oldProgress

        # Verify the downloaded file has a valid Authenticode signature
        $sig = Get-AuthenticodeSignature -FilePath $installerPath
        if ($sig.Status -eq "Valid") {
            Write-Ok "Installer signature verified: $($sig.SignerCertificate.Subject)"
        } else {
            Write-Warn "Installer signature status: $($sig.Status)"
            Write-Warn "Downloaded file: $installerPath"
            $sigConfirm = Read-Host "Run anyway? [y/N]"
            if (-not $sigConfirm -or $sigConfirm -notmatch '^[Yy]') {
                Write-Err "Aborted. Install manually from https://ollama.com/download"
                Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue
                exit 1
            }
        }

        Write-Info "Running Ollama installer..."
        Start-Process -FilePath $installerPath

        # Don't use -Wait -- Ollama auto-launches as a tray app after install,
        # which keeps the installer process alive and hangs the script forever.
        # Instead, poll for ollama.exe to appear in PATH.
        Write-Info "Waiting for installation to complete..."
        $attempts = 0
        while ($attempts -lt 60) {
            Start-Sleep -Seconds 3
            # Refresh PATH so we can find newly installed ollama
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            if (Get-Command ollama -ErrorAction SilentlyContinue) {
                break
            }
            $attempts++
        }

        if (Get-Command ollama -ErrorAction SilentlyContinue) {
            Write-Ok "Ollama installed"
        } else {
            Write-Err "Ollama not found after 3 minutes. Complete the installer manually, then re-run this script."
            exit 1
        }
    } catch {
        Write-Err "Failed to download Ollama. Please install manually from https://ollama.com/download"
        Write-Host "After installing Ollama, run this script again."
        Read-Host "Press Enter to exit"
        exit 1
    } finally {
        # Clean up installer
        Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue
    }

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# -- Step 3: Configure GPU tuning --
Write-Step "3/8" "Configuring GPU acceleration"

# Set environment variables for Ollama performance tuning
$envVars = @{
    "OLLAMA_FLASH_ATTENTION" = "1"
    "OLLAMA_KV_CACHE_TYPE"   = "q8_0"
    "OLLAMA_KEEP_ALIVE"      = "10m"
    "OLLAMA_NUM_PARALLEL"    = "2"
    "OLLAMA_HOST"            = "127.0.0.1:11434"
}

Write-Info "The following environment variables will be set for your user account:"
foreach ($key in $envVars.Keys) {
    Write-Host "    $key = $($envVars[$key])"
}
$envConfirm = Read-Host "Apply these settings? [Y/n]"
if (-not $envConfirm -or $envConfirm -match '^[Yy]') {
    foreach ($key in $envVars.Keys) {
        $current = [System.Environment]::GetEnvironmentVariable($key, "User")
        if ($current -ne $envVars[$key]) {
            [System.Environment]::SetEnvironmentVariable($key, $envVars[$key], "User")
            Set-Item -Path "Env:\$key" -Value $envVars[$key]
        }
    }
    Write-Ok "GPU tuning applied (flash attention, q8 KV cache, localhost-only)"
} else {
    Write-Warn "Skipping GPU tuning. You can set these manually later."
}

if ($gpuType -eq "amd") {
    Write-Info "AMD GPU: Ollama will auto-detect Vulkan on Windows"
}

# -- Step 4: Start Ollama and wait --
Write-Step "4/8" "Starting Ollama"

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

# -- Step 5: Pull Models --
Write-Step "5/8" "Downloading AI models (this takes a while)"

Write-Host ""
Write-Host "  Pulling 3 models for legal work + embedding model for document search:"
Write-Host "    1. gemma3:12b       (8GB)   - Fast, great for summarization and drafting"
Write-Host "    2. qwen3:14b        (9GB)   - Strong instruction following, structured analysis"
Write-Host "    3. mistral-small    (14GB)  - Most capable, best for complex reasoning"
Write-Host "    4. nomic-embed-text (274MB) - Embedding model for document upload (RAG)"
Write-Host ""

$models = @("gemma3:12b", "qwen3:14b")

# Only pull mistral-small if we have enough VRAM
if ($vramGB -ge 12 -or $vramGB -eq 0) {
    $models += "mistral-small:24b"
} else {
    Write-Warn "Skipping mistral-small:24b (needs 14GB VRAM, you have ${vramGB}GB)"
}

# Always pull embedding model (small, needed for RAG)
$models += "nomic-embed-text"

foreach ($model in $models) {
    Write-Info "Pulling $model..."
    & ollama pull $model
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "$model ready"
    } else {
        Write-Warn "Failed to pull $model --you can try later with: ollama pull $model"
    }
}

# -- Step 6: Create Legal Presets --
Write-Step "6/8" "Creating legal presets (specialized models)"

Write-Info "Building legal-tuned model presets from Modelfiles..."

$modelfiles = @("contract-reviewer", "depo-summarizer", "memo-drafter")

foreach ($name in $modelfiles) {
    $modelfile = Join-Path $scriptDir "Modelfile.$name"
    if (Test-Path $modelfile) {
        $existing = ollama list 2>$null | Select-String $name
        if ($existing) {
            Write-Ok "$name already exists"
        } else {
            Write-Info "Creating $name..."
            & ollama create $name -f $modelfile
            if ($LASTEXITCODE -eq 0) {
                Write-Ok "$name ready"
            } else {
                Write-Warn "Failed to create $name --you can try later with: ollama create $name -f $modelfile"
            }
        }
    } else {
        Write-Warn "Modelfile.$name not found in $scriptDir --skipping"
    }
}

# -- Step 7: Install Docker Desktop + Open WebUI --
Write-Step "7/8" "Installing Open WebUI (chat interface)"

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
            Write-Info "Installing Open WebUI via pip (in a virtual environment)..."
            $venvPath = "$env:USERPROFILE\.open-webui-venv"
            & python -m venv $venvPath
            & "$venvPath\Scripts\pip.exe" install open-webui
            if ($LASTEXITCODE -eq 0) {
                Write-Ok "Open WebUI installed via pip (venv: $venvPath)"
                Write-Info "Starting Open WebUI (bound to localhost)..."
                Start-Process -FilePath "$venvPath\Scripts\open-webui.exe" -ArgumentList "serve", "--host", "127.0.0.1", "--port", "3000" -WindowStyle Hidden
                Start-Sleep -Seconds 5
                Write-Ok "Open WebUI is running (localhost only)"
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
    # Docker command exists -- but is the daemon running?
    $dockerRunning = $false
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) { $dockerRunning = $true }
    } catch {}

    if (-not $dockerRunning) {
        Write-Warn "Docker is installed but the Docker daemon is not running."
        Write-Warn "Please start Docker Desktop from the Start menu, wait for it to finish loading,"
        Write-Warn "then press Enter to continue."
        Write-Host ""
        Read-Host "Press Enter after Docker Desktop is running (or type 'skip' to use pip instead)"

        # Check again
        try {
            $dockerInfo = docker info 2>&1
            if ($LASTEXITCODE -eq 0) { $dockerRunning = $true }
        } catch {}
    }

    if ($dockerRunning) {
        $existing = docker ps -a --format "{{.Names}}" 2>$null | Where-Object { $_ -eq "open-webui" }
        if ($existing) {
            Write-Ok "Open WebUI container already exists"
            docker start open-webui 2>$null
        } else {
            Write-Info "Starting Open WebUI container (with RAG document support)..."
            # Pin to a specific release tag for supply chain safety
            # Bind to 127.0.0.1 only --not accessible from other machines on the network
            docker run -d `
                -p 127.0.0.1:3000:8080 `
                --add-host=host.docker.internal:host-gateway `
                -v open-webui:/app/backend/data `
                -e OLLAMA_BASE_URL=http://host.docker.internal:11434 `
                -e RAG_EMBEDDING_ENGINE=ollama `
                -e RAG_EMBEDDING_MODEL=nomic-embed-text `
                -e CHUNK_SIZE=512 `
                -e CHUNK_OVERLAP=75 `
                -e ENABLE_RAG_HYBRID_SEARCH=true `
                -e RAG_SYSTEM_CONTEXT=true `
                --name open-webui `
                --restart always `
                ghcr.io/open-webui/open-webui:v0.6.5
            Write-Ok "Open WebUI is running (localhost only, RAG enabled)"
        }
        $webUIInstalled = $true
    } else {
        Write-Warn "Docker daemon still not running. Falling back to pip install..."
        $pipAvailable = Get-Command pip -ErrorAction SilentlyContinue
        if ($pipAvailable) {
            Write-Info "Installing Open WebUI via pip (in a virtual environment)..."
            $venvPath = "$env:USERPROFILE\.open-webui-venv"
            & python -m venv $venvPath
            & "$venvPath\Scripts\pip.exe" install open-webui
            if ($LASTEXITCODE -eq 0) {
                Write-Ok "Open WebUI installed via pip (venv: $venvPath)"
                Write-Info "Starting Open WebUI (bound to localhost)..."
                Start-Process -FilePath "$venvPath\Scripts\open-webui.exe" -ArgumentList "serve", "--host", "127.0.0.1", "--port", "3000" -WindowStyle Hidden
                Start-Sleep -Seconds 5
                Write-Ok "Open WebUI is running (localhost only)"
                $webUIInstalled = $true
            } else {
                Write-Warn "pip install failed. Try manually: pip install open-webui"
                $webUIInstalled = $false
            }
        } else {
            Write-Warn "Start Docker Desktop and re-run this script, or install manually:"
            Write-Warn "  pip install open-webui && open-webui serve --port 3000"
            $webUIInstalled = $false
        }
    }
}

# -- Step 8: Quick Test --
Write-Step "8/8" "Running quick test"

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

# -- Verify Security --
Write-Host ""
Write-Info "Verifying network security..."

# Check Ollama bind address
try {
    $ollamaListeners = netstat -an 2>$null | Select-String ":11434" | Select-String "LISTENING"
    if ($ollamaListeners -and $ollamaListeners -match "127\.0\.0\.1") {
        Write-Ok "Ollama bound to localhost only (127.0.0.1:11434)"
    } elseif ($ollamaListeners -and $ollamaListeners -match "0\.0\.0\.0") {
        Write-Warn "Ollama is listening on all interfaces (0.0.0.0:11434)"
        Write-Warn "Set OLLAMA_HOST=127.0.0.1:11434 in user environment variables to restrict."
    } else {
        Write-Info "Could not verify Ollama bind address. Check: netstat -an | findstr 11434"
    }
} catch {
    Write-Info "Could not verify bind addresses."
}

# Check Open WebUI bind address
try {
    $webuiListeners = netstat -an 2>$null | Select-String ":3000" | Select-String "LISTENING"
    if ($webuiListeners -and $webuiListeners -match "127\.0\.0\.1") {
        Write-Ok "Open WebUI bound to localhost only (127.0.0.1:3000)"
    } elseif ($webuiListeners) {
        Write-Warn "Could not verify Open WebUI bind address. Check: netstat -an | findstr 3000"
    }
} catch {}

# -- Done --
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
Write-Host "  Legal presets (specialized system prompts):" -ForegroundColor White
Write-Host "    - contract-reviewer  Contract analysis (qwen3:14b)"
Write-Host "    - depo-summarizer    Deposition summaries (gemma3:12b)"
Write-Host "    - memo-drafter       Legal memo drafting (mistral-small)"
Write-Host ""
Write-Host "  Document upload: Create a Knowledge collection in Open WebUI," -ForegroundColor Gray
Write-Host "  upload PDFs, then reference them with # in chat. See README.md." -ForegroundColor Gray
Write-Host ""
Write-Host "  See README.md for example prompts, limitations, and RAG tips." -ForegroundColor Gray
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
