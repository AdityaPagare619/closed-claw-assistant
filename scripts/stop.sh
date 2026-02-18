#!/bin/bash
#
# Closed Claw Assistant - Stop Script
# Gracefully shuts down all services
# Usage: bash stop.sh
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
PID_DIR="$INSTALL_DIR/.pids"
LOG_DIR="$INSTALL_DIR/logs"

# Graceful shutdown timeout (seconds)
GRACEFUL_TIMEOUT=10

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

#######################################
# Process Management
#######################################

stop_process() {
    local name="$1"
    local pid_file="$2"
    local pid=""
    
    # Get PID from file or find it
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file" 2>/dev/null) || true
    fi
    
    # Fallback: find by name
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
        case "$name" in
            "llama")
                pid=$(pgrep -f "llama.*server" | head -1) || true
                ;;
            "agent")
                pid=$(pgrep -f "python.*main.py" | head -1) || true
                ;;
        esac
    fi
    
    if [ -z "$pid" ]; then
        log_warn "$name: Not running"
        return 0
    fi
    
    log_info "Stopping $name (PID: $pid)..."
    
    # Try graceful shutdown first
    if kill -0 "$pid" 2>/dev/null; then
        kill -TERM "$pid" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local waited=0
        while kill -0 "$pid" 2>/dev/null && [ $waited -lt $GRACEFUL_TIMEOUT ]; do
            sleep 1
            waited=$((waited + 1))
            echo -n "."
        done
        echo ""
        
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            log_warn "$name: Force killing..."
            kill -KILL "$pid" 2>/dev/null || true
            sleep 1
        fi
    fi
    
    # Verify stopped
    if kill -0 "$pid" 2>/dev/null; then
        log_error "$name: Failed to stop"
        return 1
    else
        log_success "$name: Stopped"
        rm -f "$pid_file"
        return 0
    fi
}

#######################################
# Cleanup Functions
#######################################

cleanup_files() {
    log_info "Cleaning up temporary files..."
    
    # Remove PID files
    if [ -d "$PID_DIR" ]; then
        rm -rf "$PID_DIR"
        log_success "PID files cleaned"
    fi
    
    # Clean old logs (keep last 7 days of temp logs)
    find "$LOG_DIR" -name "*.tmp" -mtime +7 -delete 2>/dev/null || true
    
    # Remove lock files
    find "$INSTALL_DIR" -name "*.lock" -delete 2>/dev/null || true
    
    log_success "Cleanup complete"
}

cleanup_network() {
    log_info "Checking network resources..."
    
    # Close any lingering connections on our ports
    local llama_port="${LLAMA_PORT:-8080}"
    
    # This is mostly for Linux systems
    if command -v fuser &> /dev/null; then
        fuser -k "${llama_port}/tcp" 2>/dev/null || true
    fi
    
    log_success "Network resources released"
}

#######################################
# Status Functions
#######################################

show_status() {
    log_info "Checking for remaining processes..."
    
    local found=0
    
    # Check for llama.cpp
    if pgrep -f "llama.*server" > /dev/null 2>&1; then
        log_warn "llama.cpp processes still running:"
        pgrep -a -f "llama.*server" || true
        found=$((found + 1))
    fi
    
    # Check for agent
    if pgrep -f "python.*main.py" > /dev/null 2>&1; then
        log_warn "Agent processes still running:"
        pgrep -a -f "python.*main.py" || true
        found=$((found + 1))
    fi
    
    if [ $found -eq 0 ]; then
        log_success "All processes stopped"
    else
        log_warn "$found process(es) may need manual cleanup"
        log_info "Run: pkill -f 'llama|main.py'"
    fi
}

#######################################
# Main
#######################################

main() {
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  Closed Claw Assistant - Stop"
    echo "=========================================="
    echo -e "${NC}"
    
    # Stop services
    stop_process "llama" "$PID_DIR/llama.pid"
    stop_process "agent" "$PID_DIR/agent.pid"
    
    # Cleanup
    cleanup_files
    cleanup_network
    
    # Final status
    echo ""
    show_status
    
    echo ""
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  Shutdown Complete"
    echo "=========================================="
    echo -e "${NC}"
}

# Handle arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: bash stop.sh [OPTIONS]"
        echo ""
        echo "Stops all Closed Claw Assistant services gracefully"
        echo ""
        echo "Options:"
        echo "  --help, -h    Show this help"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown option: $1"
        exit 1
        ;;
esac
