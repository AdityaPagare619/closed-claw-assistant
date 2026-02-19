#!/bin/bash
# =============================================================================
# CLOSED CLAW v3.0 - ONE-COMMAND INSTALLER (FIXED VERSION)
# =============================================================================
# RUN THIS IN TERMUX:
# curl -fsSL https://raw.githubusercontent.com/AdityaPagare619/closed-claw-assistant/main/install.sh | bash
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

INSTALL_DIR="$HOME/closed-claw-assistant"
REPO_URL="https://github.com/AdityaPagare619/closed-claw-assistant.git"
MODEL_URL="https://huggingface.co/sarvam/sarvam-1-2b/resolve/main/sarvam-1-2b-q4.gguf"

log() { echo -e "${GREEN}>>>${NC} $1"; }
warn() { echo -e "${YELLOW}>>>${NC} $1"; }
error() { echo -e "${RED}>>>${NC} $1"; }

main() {
    clear
    echo ""
    echo -e "${CYAN}${BOLD}  _____  _       _____  ____   _____ ______${NC}"
    echo -e "${CYAN}${BOLD} / ____|| |     / ____|/ __ \\ / ____|  ____|${NC}"
    echo -e "${CYAN}${BOLD}| |     | |    | |    | |  | | |  __| |__${NC}"
    echo -e "${CYAN}${BOLD}| |     | |    | |    | |  | | | |_ |  __|${NC}"
    echo -e "${CYAN}${BOLD}| |____ | |____| |____| |__| | |__| | |____|${NC}"
    echo -e "${CYAN}${BOLD} \\_____||______|\\_____|\\____/ \\_____|______|${NC}"
    echo -e "${CYAN}${BOLD}          v3.0 - Mobile AI Assistant${NC}"
    echo ""
    
    # Check Termux
    if [ ! -d "/data/data/com.termux/files" ]; then
        error "This requires Termux on Android!"
        error "Install from: https://f-droid.org/packages/com.termux/"
        exit 1
    fi
    
    log "Termux detected"
    echo ""
    echo -n "Install Closed Claw v3.0? [Y/n]: "
    read -n 1 -r reply
    echo
    [[ $reply =~ ^[Nn]$ ]] && exit 0
    
    # Step 1: Update
    echo ""
    log "Step 1/7: Updating package list..."
    pkg update -y 2>&1 || warn "Update had issues, continuing..."
    
    # Step 2: Install deps
    log "Step 2/7: Installing dependencies..."
    pkg install -y git python python-pip curl wget termux-api 2>&1 || true
    
    # Step 3: Clone
    echo ""
    log "Step 3/7: Downloading Closed Claw..."
    cd "$HOME"
    [ -d "$INSTALL_DIR" ] && rm -rf "$INSTALL_DIR"
    
    if git clone --depth 1 "$REPO_URL" "$INSTALL_DIR" 2>&1; then
        log "Downloaded successfully"
    else
        error "Git clone failed!"
        exit 1
    fi
    
    cd "$INSTALL_DIR"
    mkdir -p data/{memory,audit,cache,learning} models logs
    
    # Step 4: Python packages
    echo ""
    log "Step 4/7: Installing Python packages (this takes time)..."
    
    pip install --upgrade pip --quiet 2>/dev/null || true
    
    pip install --no-cache-dir aiofiles pydantic numpy cryptography 2>&1 | tail -1 || true
    pip install --no-cache-dir python-dotenv pyTelegramBotAPI requests psutil 2>&1 | tail -1 || true
    
    # Install llama-cpp (most important)
    log "Installing llama-cpp-python (5-10 min)..."
    CMAKE_ARGS="-DLLAMA_BUILD_METAL=OFF" pip install --no-cache-dir llama-cpp-python 2>&1 | tail -3 || warn "llama-cpp may need manual install"
    
    # Step 5: Config
    echo ""
    log "Step 5/7: Configuration"
    echo ""
    echo -n "Your name [Boss]: "
    read boss_name
    boss_name=${boss_name:-Boss}
    
    echo -n "Telegram Bot Token (skip Enter): "
    read bot_token
    
    echo -n "Performance: 1)Low 2)Medium 3)High [2]: "
    read perf
    perf=${perf:-2}
    
    case $perf in
        1) max_ram=1000; context=1024; tokens=256 ;;
        3) max_ram=2000; context=4096; tokens=512 ;;
        *) max_ram=1400; context=2048; tokens=512 ;;
    esac
    
    cat > "$INSTALL_DIR/config/config.local.json" << EOF
{
  "assistant": {"name": "Closed Claw", "version": "3.0", "boss_name": "$boss_name"},
  "sarvam": {"brain_model_path": "models/sarvam-1-2b-q4.gguf", "context_length": $context, "max_tokens": $tokens},
  "memory": {"working_memory_size": 20, "episodic_memory_limit_mb": 500},
  "security": {"permission_level": "L2"},
  "telegram": {"enabled": $([ -n "$bot_token" ] && echo "true" || echo "false"), "bot_token": "$bot_token"},
  "performance": {"lazy_load_models": true, "model_idle_timeout_seconds": 300, "max_ram_usage_mb": $max_ram, "keep_model_loaded": true}
}
EOF
    log "Configuration saved"
    
    # Step 6: Model
    echo ""
    log "Step 6/7: AI Model"
    cd "$INSTALL_DIR/models"
    
    if [ -f "sarvam-1-2b-q4.gguf" ]; then
        size=$(stat -c%s "sarvam-1-2b-q4.gguf" 2>/dev/null || echo 0)
        if [ "$size" -gt 1500000000 ]; then
            log "Model already present ($((size/1024/1024))MB)"
        else
            rm -f sarvam-1-2b-q4.gguf
        fi
    fi
    
    if [ ! -f "sarvam-1-2b-q4.gguf" ]; then
        echo ""
        warn "Model not found (~1.6GB)"
        echo "Download manually later with:"
        echo "  cd ~/closed-claw-assistant/models"
        echo "  wget $MODEL_URL"
        echo ""
        echo -n "Download now? (y/N): "
        read -n 1 -r download
        echo
        if [[ $download =~ ^[Yy]$ ]]; then
            log "Downloading (15-30 min)..."
            wget -c -O sarvam-1-2b-q4.gguf "$MODEL_URL" || warn "Download failed"
        fi
    fi
    
    # Step 7: Launchers
    echo ""
    log "Step 7/7: Creating launch commands..."
    
    cat > "$INSTALL_DIR/claw" << 'LCH'
#!/bin/bash
cd "$HOME/closed-claw-assistant"
export PYTHONPATH="$HOME/closed-claw-assistant/src:$PYTHONPATH"

if pgrep -f "main.py" > /dev/null 2>&1; then
    echo "Already running! Use ./claw-stop"
    exit 1
fi

echo "Starting Closed Claw v3.0..."
echo "Logs: tail -f logs/assistant.log"
python3 main.py "$@"
LCH
    chmod +x "$INSTALL_DIR/claw"
    
    cat > "$INSTALL_DIR/claw-stop" << 'STP'
#!/bin/bash
pkill -f "main.py" 2>/dev/null || true
pkill -f "llama" 2>/dev/null || true
echo "Stopped."
STP
    chmod +x "$INSTALL_DIR/claw-stop"
    
    # Done
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  CLOSED CLAW v3.0 READY!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Location: $INSTALL_DIR"
    echo "Start: cd $INSTALL_DIR && ./claw"
    echo "Stop: ./claw-stop"
    echo ""
    echo "First message takes 1-2 min to load model."
    echo "After that - instant responses!"
    echo ""
}

main "$@"
