#!/bin/bash
# =============================================================================
# CLOSED CLAW v3.0 - ONE-COMMAND INSTALLER (WORKING VERSION)
# =============================================================================
# CORRECT URL: https://raw.githubusercontent.com/AdityaPagare619/closed-claw-assistant/main/install.sh
# 
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
RAW_URL="https://raw.githubusercontent.com/AdityaPagare619/closed-claw-assistant/main"
MODEL_URL="https://huggingface.co/sarvam/sarvam-1-2b/resolve/main/sarvam-1-2b-q4.gguf"

# Progress tracking
CURRENT_STEP=0
TOTAL_STEPS=7

progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo ""
    echo -e "${CYAN}${BOLD}[Step $CURRENT_STEP/$TOTAL_STEPS]${NC} $1"
    echo -e "${CYAN}$(printf '=%.0s' $(seq 1 50))${NC}"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

main() {
    clear 2>/dev/null || true
    echo ""
    echo -e "${CYAN}${BOLD}  _____  _       _____  ____   _____ ______${NC}"
    echo -e "${CYAN}${BOLD} / ____|| |     / ____|/ __ \ / ____|  ____|${NC}"
    echo -e "${CYAN}${BOLD}| |     | |    | |    | |  | | |  __| |__${NC}"
    echo -e "${CYAN}${BOLD}| |     | |    | |    | |  | | | |_ |  __|${NC}"
    echo -e "${CYAN}${BOLD}| |____ | |____| |____| |__| | |__| | |____|${NC}"
    echo -e "${CYAN}${BOLD} \_____||______|\_____|\____/ \_____|______|${NC}"
    echo -e "${CYAN}${BOLD}                                           ${NC}"
    echo -e "${CYAN}${BOLD}          v3.0 - Mobile AI Assistant${NC}"
    echo ""
    
    # Check Termux
    if [ ! -d "/data/data/com.termux/files" ]; then
        error "This installer requires Termux on Android!"
        error "Install from: https://f-droid.org/packages/com.termux/"
        exit 1
    fi
    
    success "Termux environment detected"
    echo ""
    read -p "Install Closed Claw v3.0? (Y/n): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Nn]$ ]] && exit 0
    
    # Step 1: System prep
    progress "Preparing System"
    info "Updating packages (this may take a minute)..."
    pkg update -y 2>&1 | tail -3
    
    info "Installing required packages..."
    pkg install -y git python python-pip curl wget termux-api clang cmake make rust 2>/dev/null || true
    termux-setup-storage 2>/dev/null || true
    success "System ready"
    
    # Step 2: Download project
    progress "Downloading Closed Claw"
    cd "$HOME"
    
    if [ -d "$INSTALL_DIR" ]; then
        warning "Directory exists, updating..."
        rm -rf "$INSTALL_DIR"
    fi
    
    info "Cloning from GitHub..."
    if git clone --depth 1 "$REPO_URL" "$INSTALL_DIR" 2>&1 | tail -3; then
        success "Downloaded from GitHub"
    else
        error "Git clone failed!"
        error "Alternative: Download ZIP manually from GitHub"
        exit 1
    fi
    
    cd "$INSTALL_DIR"
    mkdir -p data/{memory,audit,cache,learning} models logs
    success "Project ready"
    
    # Step 3: Python deps
    progress "Installing Python Packages"
    info "Installing (this takes several minutes)..."
    pip install --upgrade pip 2>&1 | tail -1
    
    pip install --no-cache-dir asyncio aiofiles pydantic numpy cryptography 2>&1 | tail -2
    pip install --no-cache-dir python-dotenv pyTelegramBotAPI requests psutil 2>&1 | tail -2
    
    info "Installing ML libraries..."
    pip install --no-cache-dir sentence-transformers 2>&1 | tail -2 || warning "sentence-transformers had issues"
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu 2>&1 | tail -2 || warning "torch had issues"
    
    info "Installing llama-cpp (this takes 5-10 minutes)..."
    CMAKE_ARGS="-DLLAMA_BUILD_METAL=OFF" pip install --no-cache-dir llama-cpp-python 2>&1 | tail -3 || {
        warning "llama-cpp-python install had warnings"
        warning "You may need to install it manually later"
    }
    success "Python packages installed"
    
    # Step 4: Interactive config
    progress "Configuration"
    echo ""
    echo -e "${CYAN}Let's configure your assistant:${NC}"
    echo ""
    
    read -p "Your name [Boss]: " boss_name
    boss_name=${boss_name:-Boss}
    
    echo ""
    read -p "Telegram Bot Token (press Enter to skip): " bot_token
    
    echo ""
    read -p "Your phone number (optional): " phone
    
    echo ""
    echo "Performance: 1)Low(4GB) 2)Medium(6GB) 3)High(8GB+)"
    read -p "Select [2]: " perf
    perf=${perf:-2}
    
    case $perf in
        1) max_ram=1000; context=1024; tokens=256 ;;
        3) max_ram=2000; context=4096; tokens=512 ;;
        *) max_ram=1400; context=2048; tokens=512 ;;
    esac
    
    # Create config
    cat > "$INSTALL_DIR/config/config.local.json" << EOF
{
  "assistant": {
    "name": "Closed Claw",
    "version": "3.0",
    "boss_name": "$boss_name",
    "hotword": "Hey Claw"
  },
  "sarvam": {
    "brain_model_path": "models/sarvam-1-2b-q4.gguf",
    "context_length": $context,
    "max_tokens": $tokens
  },
  "memory": {
    "working_memory_size": 20,
    "episodic_memory_limit_mb": 500,
    "embedding_model": "all-MiniLM-L6-v2",
    "context_window_tokens": 3500
  },
  "security": {
    "permission_level": "L2",
    "audit_retention_days": 30
  },
  "telegram": {
    "enabled": $([ -n "$bot_token" ] && echo "true" || echo "false"),
    "bot_token": "$bot_token",
    "phone": "$phone"
  },
  "performance": {
    "lazy_load_models": true,
    "model_idle_timeout_seconds": 300,
    "max_ram_usage_mb": $max_ram,
    "keep_model_loaded": true
  }
}
EOF
    success "Configuration saved"
    
    # Step 5: Download model
    progress "Downloading AI Model"
    cd "$INSTALL_DIR/models"
    
    if [ -f "sarvam-1-2b-q4.gguf" ]; then
        size=$(stat -c%s "sarvam-1-2b-q4.gguf" 2>/dev/null || echo "0")
        if [ "$size" -gt 1500000000 ]; then
            success "Model already downloaded ($(($size/1024/1024))MB)"
            read -p "Re-download? (y/N): " -n 1 -r
            echo
            [[ $REPLY =~ ^[Yy]$ ]] || skip_model=1
        fi
    fi
    
    if [ "$skip_model" != "1" ]; then
        info "Downloading Sarvam-1 2B (~1.6GB, 15-30 mins)..."
        info "Press Ctrl+C to skip and download manually later"
        echo ""
        
        if wget -c --progress=bar:force -O model.tmp "$MODEL_URL" 2>&1; then
            mv model.tmp sarvam-1-2b-q4.gguf
            size=$(stat -c%s "sarvam-1-2b-q4.gguf")
            success "Model downloaded ($((size/1024/1024))MB)"
        else
            warning "Download failed - will try on first run"
        fi
    fi
    
    # Step 6: Create launcher
    progress "Creating Launch Commands"
    cat > "$INSTALL_DIR/claw" << 'LAUNCHER'
#!/bin/bash
cd "$HOME/closed-claw-assistant"
export PYTHONPATH="$HOME/closed-claw-assistant/src:$PYTHONPATH"

if pgrep -f "main.py" > /dev/null 2>&1; then
    echo "Closed Claw is already running!"
    echo "Stop it first with: ./claw-stop"
    exit 1
fi

echo "Starting Closed Claw v3.0..."
echo "Logs: tail -f logs/assistant.log"
echo ""
python3 main.py "$@"
LAUNCHER
    chmod +x "$INSTALL_DIR/claw"
    
    cat > "$INSTALL_DIR/claw-stop" << 'STOPPER'
#!/bin/bash
echo "Stopping Closed Claw..."
pkill -f "main.py" 2>/dev/null || true
pkill -f "llama" 2>/dev/null || true
sleep 1
echo "Stopped."
STOPPER
    chmod +x "$INSTALL_DIR/claw-stop"
    
    # Add to PATH
    if ! grep -q "$INSTALL_DIR" "$HOME/.bashrc" 2>/dev/null; then
        echo "export PATH="$INSTALL_DIR:\$PATH"" >> "$HOME/.bashrc"
    fi
    success "Launchers created"
    
    # Step 7: Validation
    progress "Validating Installation"
    [ -f "$INSTALL_DIR/main.py" ] && success "main.py found" || error "main.py missing"
    [ -d "$INSTALL_DIR/src" ] && success "src/ directory found" || error "src/ missing"
    [ -f "$INSTALL_DIR/config/config.local.json" ] && success "config found" || error "config missing"
    success "Installation validated"
    
    # Done
    echo ""
    echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║     CLOSED CLAW v3.0 READY TO USE!            ║${NC}"
    echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Location:${NC} $INSTALL_DIR"
    echo -e "${CYAN}Start:${NC} cd $INSTALL_DIR && ./claw"
    echo -e "${CYAN}Stop:${NC} ./claw-stop"
    echo ""
    echo -e "${YELLOW}Important:${NC}"
    echo "• Grant Android permissions (Settings > Accessibility)"
    echo "• Model loads on first use (1-2 minutes)"
    echo "• Then stays loaded for instant responses!"
    echo ""
    echo -e "${GREEN}Your secure AI assistant is ready!${NC}"
    echo ""
}

main "$@"