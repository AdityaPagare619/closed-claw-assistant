#!/bin/bash
#
# Closed Claw Assistant - Start Script
# Starts all services with health checks
# Usage: bash start.sh [--daemon]
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INSTALL_DIR="${CLOSED_CLAW_HOME:-$HOME/closed-claw}"
CONFIG_DIR="$INSTALL_DIR/config"
LOG_DIR="$INSTALL_DIR/logs"
PID_DIR="$INSTALL_DIR/.pids"
PYTHON_ENV="$INSTALL_DIR/venv"

DAEMON_MODE=false

# Process IDs
LLAMA_PID=""
AGENT_PID=""

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
}

cleanup() {
    log_warn "Shutting down services..."
    
    if [ -n "$AGENT_PID" ]; then
        kill "$AGENT_PID" 2>/dev/null || true
    fi
    
    if [ -n "$LLAMA_PID" ]; then
        kill "$LLAMA_PID" 2>/dev/null || true
    fi
    
    rm -rf "$PID_DIR"
    log_info "Cleanup complete"
}

trap cleanup EXIT INT TERM

#######################################
# Check Functions
#######################################

check_environment() {
    log_info "Checking environment..."
    
    # Check installation directory
    if [ ! -d "$INSTALL_DIR" ]; then
        log_error "Installation not found at $INSTALL_DIR"
        log_info "Run setup-termux.sh first"
        exit 1
    fi
    
    # Check virtual environment
    if [ ! -d "$PYTHON_ENV" ]; then
        log_error "Python environment not found"
        exit 1
    fi
    
    # Activate virtual environment
    source "$PYTHON_ENV/bin/activate"
    
    # Check configuration
    if [ ! -f "$CONFIG_DIR/telegram.env" ]; then
        log_warn "Telegram configuration not found"
        log_info "Copy template: cp $CONFIG_DIR/telegram.env.template $CONFIG_DIR/telegram.env"
    fi
    
    log_success "Environment check passed"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing=()
    
    # Check Python packages
    python -c "import telegram" 2>/dev/null || missing+=("python-telegram-bot")
    python -c "import requests" 2>/dev/null || missing+=("requests")
    python -c "import cryptography" 2>/dev/null || missing+=("cryptography")
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_warn "Missing Python packages: ${missing[*]}"
        log_info "Installing missing packages..."
        pip install "${missing[@]}"
    fi
    
    # Check for model
    local model_file="$INSTALL_DIR/models/llama-2-7b-chat.Q4_K_M.gguf"
    if [ ! -f "$model_file" ]; then
        log_warn "AI model not found at $model_file"
        log_info "Run: bash scripts/setup-termux.sh to download models"
    fi
    
    log_success "Dependencies check passed"
}

check_ports() {
    log_info "Checking port availability..."
    
    # Default llama.cpp port
    local llama_port="${LLAMA_PORT:-8080}"
    
    # Check if port is in use
    if command -v netstat &> /dev/null; then
        if netstat -tuln 2>/dev/null | grep -q ":$llama_port "; then
            log_warn "Port $llama_port is already in use"
            log_info "Another instance may be running"
        fi
    fi
    
    log_success "Port check passed"
}

#######################################
# Service Functions
#######################################

start_llama_server() {
    log_info "Starting llama.cpp server..."
    
    local model_file="$INSTALL_DIR/models/llama-2-7b-chat.Q4_K_M.gguf"
    local llama_bin="$INSTALL_DIR/llama.cpp/server"
    local port="${LLAMA_PORT:-8080}"
    
    # Check if model exists
    if [ ! -f "$model_file" ]; then
        log_error "Model file not found: $model_file"
        return 1
    fi
    
    # Check if llama.cpp binary exists
    if [ ! -f "$llama_bin" ]; then
        log_error "llama.cpp server not found: $llama_bin"
        log_info "Run setup-termux.sh to download llama.cpp"
        return 1
    fi
    
    # Start server
    mkdir -p "$PID_DIR"
    
    if $DAEMON_MODE; then
        nohup "$llama_bin" \
            -m "$model_file" \
            --port "$port" \
            -c 2048 \
            --host 127.0.0.1 \
            > "$LOG_DIR/llama-server.log" 2>&1 &
    else
        "$llama_bin" \
            -m "$model_file" \
            --port "$port" \
            -c 2048 \
            --host 127.0.0.1 \
            > "$LOG_DIR/llama-server.log" 2>&1 &
    fi
    
    LLAMA_PID=$!
    echo $LLAMA_PID > "$PID_DIR/llama.pid"
    
    log_info "Waiting for llama.cpp to initialize..."
    sleep 3
    
    # Health check
    local attempts=0
    local max_attempts=30
    
    while [ $attempts -lt $max_attempts ]; do
        if curl -s "http://127.0.0.1:$port/health" > /dev/null 2>&1; then
            log_success "llama.cpp server ready on port $port"
            return 0
        fi
        
        # Check if process is still running
        if ! kill -0 $LLAMA_PID 2>/dev/null; then
            log_error "llama.cpp server failed to start"
            log_info "Check logs: $LOG_DIR/llama-server.log"
            return 1
        fi
        
        attempts=$((attempts + 1))
        sleep 1
    done
    
    log_error "llama.cpp server health check timeout"
    return 1
}

start_agent() {
    log_info "Starting Closed Claw agent..."
    
    local main_script="$INSTALL_DIR/src/main.py"
    
    if [ ! -f "$main_script" ]; then
        log_error "Main script not found: $main_script"
        return 1
    fi
    
    # Load environment
    if [ -f "$CONFIG_DIR/telegram.env" ]; then
        set -a
        source "$CONFIG_DIR/telegram.env"
        set +a
    fi
    
    # Start agent
    if $DAEMON_MODE; then
        nohup python "$main_script" > "$LOG_DIR/agent.log" 2>&1 &
    else
        python "$main_script" &
    fi
    
    AGENT_PID=$!
    echo $AGENT_PID > "$PID_DIR/agent.pid"
    
    log_info "Waiting for agent to initialize..."
    sleep 2
    
    # Check if process is running
    if kill -0 $AGENT_PID 2>/dev/null; then
        log_success "Agent started (PID: $AGENT_PID)"
    else
        log_error "Agent failed to start"
        return 1
    fi
}

#######################################
# Health Check Functions
#######################################

run_health_checks() {
    log_info "Running health checks..."
    
    local checks_passed=0
    local total_checks=3
    
    # Check 1: llama.cpp responding
    local llama_port="${LLAMA_PORT:-8080}"
    if curl -s "http://127.0.0.1:$llama_port/health" > /dev/null 2>&1; then
        log_success "✓ llama.cpp server responding"
        checks_passed=$((checks_passed + 1))
    else
        log_error "✗ llama.cpp server not responding"
    fi
    
    # Check 2: Agent process running
    if [ -n "$AGENT_PID" ] && kill -0 $AGENT_PID 2>/dev/null; then
        log_success "✓ Agent process running"
        checks_passed=$((checks_passed + 1))
    else
        log_error "✗ Agent process not running"
    fi
    
    # Check 3: Log files writable
    if touch "$LOG_DIR/health-check.tmp" 2>/dev/null; then
        rm "$LOG_DIR/health-check.tmp"
        log_success "✓ Log directory writable"
        checks_passed=$((checks_passed + 1))
    else
        log_error "✗ Log directory not writable"
    fi
    
    echo ""
    log_info "Health check results: $checks_passed/$total_checks passed"
    
    if [ $checks_passed -eq $total_checks ]; then
        log_success "All health checks passed!"
        return 0
    else
        log_warn "Some health checks failed"
        return 1
    fi
}

#######################################
# Main
#######################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --daemon|-d)
                DAEMON_MODE=true
                shift
                ;;
            --help|-h)
                echo "Usage: bash start.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --daemon, -d    Run in daemon mode"
                echo "  --help, -h      Show this help"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  Closed Claw Assistant - Start"
    echo "=========================================="
    echo -e "${NC}"
    
    # Run checks
    check_environment
    check_dependencies
    check_ports
    
    # Start services
    start_llama_server
    start_agent
    
    # Health checks
    run_health_checks
    
    # Final status
    echo ""
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  Services Started Successfully!"
    echo "=========================================="
    echo -e "${NC}"
    
    log_info "llama.cpp server: PID $LLAMA_PID"
    log_info "Agent: PID $AGENT_PID"
    log_info "Logs: $LOG_DIR/"
    
    if $DAEMON_MODE; then
        log_info "Running in daemon mode"
        log_info "Use 'bash scripts/stop.sh' to stop"
    else
        log_info "Press Ctrl+C to stop"
        # Wait for interrupt
        wait $AGENT_PID
    fi
}

main "$@"
