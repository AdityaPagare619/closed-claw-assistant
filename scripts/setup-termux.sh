#!/bin/bash
#
# Closed Claw Assistant - Termux Setup Script
# One-command setup for Termux environment
# Usage: bash setup-termux.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/closed-claw"
LOG_DIR="$INSTALL_DIR/logs"
CONFIG_DIR="$INSTALL_DIR/config"
MODELS_DIR="$INSTALL_DIR/models"
TELEGRAM_CLI_DIR="$INSTALL_DIR/telegram-cli"
PYTHON_ENV="$INSTALL_DIR/venv"

# Progress tracking
TOTAL_STEPS=10
CURRENT_STEP=0

# Error tracking
ERRORS=()

#######################################
# Helper Functions
#######################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ERRORS+=("$1")
}

progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo -e "\n${YELLOW}[${CURRENT_STEP}/${TOTAL_STEPS}]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

rollback() {
    log_warn "Setup failed! Rolling back changes..."
    
    # Deactivate virtual environment if active
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        deactivate 2>/dev/null || true
    fi
    
    # Remove installation directory if partially created
    if [ -d "$INSTALL_DIR" ] && [ ${#ERRORS[@]} -gt 0 ]; then
        log_warn "Removing $INSTALL_DIR due to errors..."
        rm -rf "$INSTALL_DIR"
    fi
    
    log_error "Setup failed. Check errors above."
    exit 1
}

#######################################
# Installation Steps
#######################################

step_check_termux() {
    progress "Checking Termux environment"
    
    if [ -z "${TERMUX_VERSION:-}" ] && [ ! -d "/data/data/com.termux" ]; then
        log_warn "Not running in Termux. Some features may not work."
    else
        log_success "Termux environment detected"
    fi
    
    # Check for required binaries
    for cmd in pkg python git; do
        if ! check_command "$cmd"; then
            log_error "Required command '$cmd' not found"
            return 1
        fi
    done
    
    log_success "All required commands available"
}

step_update_packages() {
    progress "Updating package lists"
    
    pkg update -y || {
        log_error "Failed to update package lists"
        return 1
    }
    
    log_success "Package lists updated"
}

step_install_dependencies() {
    progress "Installing dependencies"
    
    local packages=(
        python
        python-pip
        git
        cmake
        clang
        pkg-config
        openssl
        libffi
        zlib
        curl
        wget
        proot-distro
    )
    
    for package in "${packages[@]}"; do
        log_info "Installing $package..."
        pkg install -y "$package" || {
            log_warn "Failed to install $package (may already be installed)"
        }
    done
    
    log_success "Dependencies installed"
}

step_create_directories() {
    progress "Creating directory structure"
    
    mkdir -p "$INSTALL_DIR"/{src,scripts,config,logs,models,data}
    mkdir -p "$LOG_DIR"/{audit,security,app}
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$MODELS_DIR"
    
    log_success "Directory structure created at $INSTALL_DIR"
}

step_setup_python_env() {
    progress "Setting up Python virtual environment"
    
    # Create virtual environment
    python -m venv "$PYTHON_ENV" || {
        log_error "Failed to create virtual environment"
        return 1
    }
    
    # Activate
    source "$PYTHON_ENV/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip wheel
    
    log_success "Python virtual environment ready"
}

step_install_python_packages() {
    progress "Installing Python packages"
    
    # Ensure virtual environment is active
    if [ -z "${VIRTUAL_ENV:-}" ]; then
        source "$PYTHON_ENV/bin/activate"
    fi
    
    # Core dependencies
    local packages=(
        "python-telegram-bot>=20.0"
        "requests>=2.28.0"
        "cryptography>=3.4.8"
        "aiohttp>=3.8.0"
        "python-dotenv>=0.19.0"
        "schedule>=1.1.0"
        "psutil>=5.9.0"
        "pydantic>=2.0.0"
        "typing-extensions>=4.0.0"
    )
    
    for package in "${packages[@]}"; do
        log_info "Installing $package..."
        pip install "$package" || {
            log_warn "Failed to install $package"
        }
    done
    
    log_success "Python packages installed"
}

step_download_models() {
    progress "Downloading AI models"
    
    log_info "This step downloads the base language model (~4GB)"
    log_info "This may take 10-30 minutes depending on connection speed"
    
    # Create models directory
    mkdir -p "$MODELS_DIR"
    
    # Download llama.cpp compatible model
    local model_url="https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
    local model_file="$MODELS_DIR/llama-2-7b-chat.Q4_K_M.gguf"
    
    if [ -f "$model_file" ]; then
        log_warn "Model already exists, skipping download"
    else
        log_info "Downloading model..."
        wget --progress=bar:force "$model_url" -O "$model_file" || {
            log_warn "Failed to download model (will retry on first start)"
        }
    fi
    
    # Download llama.cpp server
    log_info "Downloading llama.cpp server..."
    
    local llama_version="b2000"
    local llama_url="https://github.com/ggerganov/llama.cpp/releases/download/${llama_version}/llama-${llama_version}-bin-android-arm64.zip"
    
    cd "$INSTALL_DIR"
    wget "$llama_url" -O llama.zip 2>/dev/null || {
        log_warn "Failed to download llama.cpp (will build from source on first start)"
    }
    
    if [ -f "llama.zip" ]; then
        unzip -o llama.zip -d llama.cpp/
        rm llama.zip
        chmod +x llama.cpp/*.exe 2>/dev/null || true
        log_success "llama.cpp downloaded"
    fi
    
    log_success "Model setup complete"
}

step_configure_telegram() {
    progress "Configuring Telegram CLI"
    
    mkdir -p "$TELEGRAM_CLI_DIR"
    
    # Create Telegram config template
    cat > "$CONFIG_DIR/telegram.env" << 'EOF'
# Telegram Bot Configuration
# Get your bot token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_USER_ID=your_user_id_here

# Optional: Webhook configuration
# TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
# TELEGRAM_WEBHOOK_PORT=8443
EOF
    
    log_warn "⚠️  IMPORTANT: Edit $CONFIG_DIR/telegram.env with your bot token!"
    log_info "Get your bot token from @BotFather on Telegram"
    
    log_success "Telegram configuration template created"
}

step_setup_permissions() {
    progress "Setting up permissions and security"
    
    # Create restrictive permissions
    chmod 700 "$INSTALL_DIR"
    chmod 700 "$CONFIG_DIR"
    chmod 750 "$LOG_DIR"
    
    # Create security configuration
    cat > "$CONFIG_DIR/security.json" << 'EOF'
{
    "sandbox_enabled": true,
    "audit_logging": true,
    "banking_blocker": true,
    "allowed_paths": ["~/closed-claw"],
    "blocked_apps": [
        "phonepe", "gpay", "paytm", "bhim", "cred",
        "hdfc", "sbi", "icici", "axis", "kotak"
    ],
    "log_retention_days": 30
}
EOF
    
    log_success "Security configuration applied"
}

step_create_scripts() {
    progress "Creating utility scripts"
    
    # Create activation script
    cat > "$INSTALL_DIR/activate.sh" << EOF
#!/bin/bash
# Quick activation script
source "$PYTHON_ENV/bin/activate"
export CLOSED_CLAW_HOME="$INSTALL_DIR"
export PATH="$INSTALL_DIR/llama.cpp:\$PATH"
echo "Closed Claw environment activated!"
echo "Run 'python src/main.py' to start"
EOF
    chmod +x "$INSTALL_DIR/activate.sh"
    
    # Create systemd service file (for proot-distro Linux)
    mkdir -p "$INSTALL_DIR/service"
    cat > "$INSTALL_DIR/service/closed-claw.service" << EOF
[Unit]
Description=Closed Claw Assistant
After=network.target

[Service]
Type=simple
User=%I
WorkingDirectory=$INSTALL_DIR
ExecStart=$PYTHON_ENV/bin/python $INSTALL_DIR/src/main.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF
    
    log_success "Utility scripts created"
}

#######################################
# Main Installation
#######################################

main() {
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  Closed Claw Assistant - Setup"
    echo "=========================================="
    echo -e "${NC}"
    
    log_info "Starting installation..."
    log_info "This will take approximately 5-10 minutes"
    log_info "Install directory: $INSTALL_DIR"
    
    # Set trap for rollback on error
    trap rollback ERR
    
    # Run all steps
    step_check_termux
    step_update_packages
    step_install_dependencies
    step_create_directories
    step_setup_python_env
    step_install_python_packages
    step_download_models
    step_configure_telegram
    step_setup_permissions
    step_create_scripts
    
    # Success!
    echo -e "\n${GREEN}"
    echo "=========================================="
    echo "  Setup Complete!"
    echo "=========================================="
    echo -e "${NC}"
    
    log_success "Closed Claw Assistant installed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Edit config: nano $CONFIG_DIR/telegram.env"
    echo "  2. Start assistant: bash scripts/start.sh"
    echo "  3. Or activate manually: source $INSTALL_DIR/activate.sh"
    echo ""
    echo "Directory structure:"
    echo "  $INSTALL_DIR/src/        - Source code"
    echo "  $INSTALL_DIR/config/     - Configuration files"
    echo "  $INSTALL_DIR/logs/       - Log files"
    echo "  $INSTALL_DIR/models/     - AI models"
    echo ""
    
    # Deactivate virtual environment
    deactivate 2>/dev/null || true
}

# Run main
main "$@"
