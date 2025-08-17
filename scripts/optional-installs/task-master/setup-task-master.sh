#!/bin/bash
# setup-task-master.sh - Complete Task Master AI setup automation
# 
# This script combines both installation and initialization of Task Master AI,
# providing a single command to set up everything. It follows the repository's
# guidelines for idempotency and rollback capabilities.
#
# Usage:
#   ./scripts/optional-installs/task-master/setup-task-master.sh [OPTIONS]
#
# Options:
#   --help, -h        Show this help message
#   --dry-run         Preview changes without applying them
#   --force           Force reinstallation/reinitialization
#   --rollback        Rollback both installation and initialization
#   --status          Show current installation and initialization status
#   --install-only    Only install task-master, skip initialization
#   --init-only       Only initialize task-master, skip installation
#
# Examples:
#   # Complete setup (install + init)
#   ./scripts/optional-installs/task-master/setup-task-master.sh
#
#   # Check status
#   ./scripts/optional-installs/task-master/setup-task-master.sh --status
#
#   # Preview changes
#   ./scripts/optional-installs/task-master/setup-task-master.sh --dry-run
#
#   # Force complete reinstallation
#   ./scripts/optional-installs/task-master/setup-task-master.sh --force
#
#   # Rollback everything
#   ./scripts/optional-installs/task-master/setup-task-master.sh --rollback
#
# Requirements:
#   - Node.js and npm (install via nvm)
#   - Python 3.11+ with uv
#   - Write permissions to current directory

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG_DIR="$HOME/.local/share/arch_dotfiles/logs"
LOG_FILE="$LOG_DIR/setup-task-master_$(date +%Y%m%d_%H%M%S).log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Logging functions
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Task Master AI Complete Setup Script

This script automates the complete setup of Task Master AI, including both
installation and initialization with predefined configuration.

USAGE:
    $(basename "$0") [OPTIONS]

OPTIONS:
    --help, -h        Show this help message
    --dry-run         Preview changes without applying them
    --force           Force reinstallation/reinitialization
    --rollback        Rollback both installation and initialization
    --status          Show current installation and initialization status
    --install-only    Only install task-master, skip initialization
    --init-only       Only initialize task-master, skip installation

CONFIGURATION:
    The script will set up Task Master with:
    - Provider: Claude Code exclusively
    - Models: Sonnet for main, research, and fallback
    - Language: English
    - Interactive responses: y, n, y, y (as documented)

EXAMPLES:
    # Complete setup (recommended for first-time setup)
    $(basename "$0")
    
    # Check current status
    $(basename "$0") --status
    
    # Preview what will be done
    $(basename "$0") --dry-run
    
    # Force complete reinstallation
    $(basename "$0") --force
    
    # Rollback everything
    $(basename "$0") --rollback

LOGS:
    All operations are logged to: $LOG_DIR
    
REQUIREMENTS:
    - Node.js and npm (install via: nvm install node)
    - Python 3.11+ with uv installed
    - Write permissions to current directory

For more information, see the individual scripts:
    - $SCRIPT_DIR/install-task-master.py
    - $SCRIPT_DIR/init-task-master.py

EOF
}

# Parse command line arguments
DRY_RUN=""
FORCE=""
ROLLBACK=false
STATUS=false
INSTALL_ONLY=false
INIT_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --force)
            FORCE="--force"
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --status)
            STATUS=true
            shift
            ;;
        --install-only)
            INSTALL_ONLY=true
            shift
            ;;
        --init-only)
            INIT_ONLY=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check for Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        log_info "Please install Node.js using: nvm install node"
        return 1
    fi
    
    # Check for npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        return 1
    fi
    
    # Check for Python and uv
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        return 1
    fi
    
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed"
        log_info "Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
    
    log_success "All prerequisites are installed"
    return 0
}

# Status command
show_status() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     Task Master AI Setup Status        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo
    
    # Check installation status
    echo -e "${YELLOW}Installation Status:${NC}"
    if command -v uv &> /dev/null; then
        uv run "$SCRIPT_DIR/install-task-master.py" status
    else
        log_error "Cannot check installation status: uv not found"
    fi
    
    echo
    echo -e "${YELLOW}Initialization Status:${NC}"
    if command -v uv &> /dev/null; then
        uv run "$SCRIPT_DIR/init-task-master.py" status
    else
        log_error "Cannot check initialization status: uv not found"
    fi
}

# Rollback command
perform_rollback() {
    log_info "Starting complete rollback..."
    
    # Rollback initialization first
    if [[ "$INIT_ONLY" != true ]]; then
        log_info "Rolling back Task Master initialization..."
        uv run "$SCRIPT_DIR/init-task-master.py" rollback $DRY_RUN
    fi
    
    # Then rollback installation
    if [[ "$INSTALL_ONLY" != true ]]; then
        log_info "Rolling back Task Master installation..."
        uv run "$SCRIPT_DIR/install-task-master.py" rollback $DRY_RUN
    fi
    
    log_success "Rollback completed"
}

# Main setup function
perform_setup() {
    log_info "Starting Task Master AI setup..."
    log_info "Log file: $LOG_FILE"
    
    # Step 1: Install task-master
    if [[ "$INIT_ONLY" != true ]]; then
        log_info "Step 1: Installing task-master-ai package..."
        if uv run "$SCRIPT_DIR/install-task-master.py" install $FORCE $DRY_RUN; then
            log_success "Installation completed successfully"
        else
            log_error "Installation failed"
            return 1
        fi
    else
        log_info "Skipping installation (--init-only specified)"
    fi
    
    # Step 2: Initialize task-master
    if [[ "$INSTALL_ONLY" != true ]]; then
        log_info "Step 2: Initializing Task Master with configuration..."
        if uv run "$SCRIPT_DIR/init-task-master.py" init $FORCE $DRY_RUN; then
            log_success "Initialization completed successfully"
        else
            log_error "Initialization failed"
            return 1
        fi
    else
        log_info "Skipping initialization (--install-only specified)"
    fi
    
    # Summary
    if [[ -z "$DRY_RUN" ]]; then
        echo
        echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║    Task Master AI Setup Complete!      ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
        echo
        echo -e "${GREEN}Task Master has been successfully set up with:${NC}"
        echo -e "  • Provider: Claude Code"
        echo -e "  • Models: Sonnet (all configurations)"
        echo -e "  • Language: English"
        echo -e "  • Location: $PROJECT_ROOT/.taskmaster"
        echo
        echo -e "${BLUE}You can now use task-master commands:${NC}"
        echo -e "  • task-master --help    - Show help"
        echo -e "  • task-master status    - Check status"
        echo -e "  • task-master create    - Create a new task"
        echo
    else
        log_info "Dry-run completed - no changes were made"
    fi
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    # Show header
    echo -e "${BLUE}Task Master AI Setup Script${NC}"
    echo -e "${BLUE}Version: 1.0.0${NC}"
    echo
    
    # Handle different commands
    if [[ "$STATUS" == true ]]; then
        show_status
    elif [[ "$ROLLBACK" == true ]]; then
        if ! check_prerequisites; then
            exit 1
        fi
        perform_rollback
    else
        if ! check_prerequisites; then
            exit 1
        fi
        perform_setup
    fi
}

# Run main function
main "$@"