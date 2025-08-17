#!/bin/bash

# Extensible CLI Tools Installation Script
# Installs essential command-line tools for arch_dotfiles setup
# Designed to be easily extended with additional packages

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/.local/share/arch_dotfiles/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging setup
LOG_FILE="$LOG_DIR/cli-tools-install-$(date +%Y%m%d_%H%M%S).log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

echo "=== CLI Tools Installation ==="
echo "Started at: $(date)"
echo "Log file: $LOG_FILE"

# Color output functions
red() { echo -e "\033[31m$*\033[0m"; }
green() { echo -e "\033[32m$*\033[0m"; }
yellow() { echo -e "\033[33m$*\033[0m"; }
blue() { echo -e "\033[34m$*\033[0m"; }

# Package list - easily extensible
# Format: "package_name:description"
PACKAGES=(
    "jq:JSON processor for parsing Hyprland device information"
    # Add more packages here as needed:
    # "ripgrep:Fast text search tool"
    # "fd:Modern find replacement"
    # "bat:Cat with syntax highlighting"
    # "exa:Modern ls replacement"
)

# Help function
show_help() {
    cat << EOF
CLI Tools Installation Script

Usage: $0 [OPTIONS]

OPTIONS:
    --help              Show this help message
    --dry-run          Show what would be installed without installing
    --list             List all available packages
    --install <pkg>    Install specific package only
    --force            Skip confirmation prompts

DESCRIPTION:
    This script installs essential CLI tools for the arch_dotfiles setup.
    Currently includes:
$(printf "    - %s\n" "${PACKAGES[@]}")

EXAMPLES:
    $0                     # Install all packages interactively
    $0 --dry-run          # Preview what would be installed
    $0 --install jq       # Install only jq
    $0 --force            # Install all without confirmation

EXTENDING:
    To add new packages, edit the PACKAGES array in this script:
    PACKAGES+=(
        "new-package:Description of the package"
    )

EOF
}

# Parse command line arguments
DRY_RUN=false
LIST_ONLY=false
INSTALL_SPECIFIC=""
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --list)
            LIST_ONLY=true
            shift
            ;;
        --install)
            if [[ -n "${2:-}" ]]; then
                INSTALL_SPECIFIC="$2"
                shift 2
            else
                red "Error: --install requires a package name"
                exit 1
            fi
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            red "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if paru is available
check_paru() {
    if ! command_exists paru; then
        red "Error: paru (AUR helper) not found"
        echo "Please install paru first:"
        echo "  cd /tmp"
        echo "  git clone https://aur.archlinux.org/paru.git"
        echo "  cd paru && makepkg -si"
        exit 1
    fi
}

# List all available packages
list_packages() {
    echo "$(blue "Available CLI tools:")"
    echo
    for package_info in "${PACKAGES[@]}"; do
        IFS=':' read -r package description <<< "$package_info"
        local status="$(green "✗ not installed")"
        if command_exists "$package"; then
            status="$(green "✓ installed")"
        fi
        printf "  %-15s %s - %s\n" "$package" "$status" "$description"
    done
    echo
}

# Check package installation status
check_package_status() {
    local package="$1"
    
    if command_exists "$package"; then
        return 0  # installed
    else
        return 1  # not installed
    fi
}

# Install a single package
install_package() {
    local package="$1"
    local description="$2"
    
    echo "$(blue "Installing $package...")  $description"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  DRY RUN: Would run 'paru -S --noconfirm $package'"
        return 0
    fi
    
    if paru -S --noconfirm "$package"; then
        echo "  $(green "✓ Successfully installed $package")"
        return 0
    else
        echo "  $(red "✗ Failed to install $package")"
        return 1
    fi
}

# Install all packages
install_all_packages() {
    local packages_to_install=()
    local already_installed=()
    local failed_packages=()
    
    echo "$(blue "Checking package installation status...")"
    echo
    
    # Check which packages need installation
    for package_info in "${PACKAGES[@]}"; do
        IFS=':' read -r package description <<< "$package_info"
        
        if check_package_status "$package"; then
            already_installed+=("$package")
            echo "  $(green "✓") $package - already installed"
        else
            packages_to_install+=("$package_info")
            echo "  $(yellow "○") $package - needs installation"
        fi
    done
    
    echo
    
    # Show summary
    if [[ ${#already_installed[@]} -gt 0 ]]; then
        echo "$(green "Already installed:") ${already_installed[*]}"
    fi
    
    if [[ ${#packages_to_install[@]} -eq 0 ]]; then
        echo "$(green "All packages are already installed!")"
        return 0
    fi
    
    echo "$(yellow "Packages to install:") ${#packages_to_install[@]}"
    for package_info in "${packages_to_install[@]}"; do
        IFS=':' read -r package description <<< "$package_info"
        echo "  - $package: $description"
    done
    echo
    
    # Confirmation prompt
    if [[ "$FORCE" == "false" && "$DRY_RUN" == "false" ]]; then
        read -p "Proceed with installation? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            yellow "Installation cancelled"
            exit 0
        fi
    fi
    
    # Install packages
    echo "$(blue "Installing packages...")"
    echo
    
    for package_info in "${packages_to_install[@]}"; do
        IFS=':' read -r package description <<< "$package_info"
        
        if install_package "$package" "$description"; then
            # Verify installation
            if [[ "$DRY_RUN" == "false" ]] && ! check_package_status "$package"; then
                echo "  $(yellow "⚠ Warning: $package installation reported success but command not found")"
                failed_packages+=("$package")
            fi
        else
            failed_packages+=("$package")
        fi
        echo
    done
    
    # Final summary
    echo "$(blue "Installation Summary:")"
    echo "  Total packages: ${#PACKAGES[@]}"
    echo "  Already installed: ${#already_installed[@]}"
    echo "  Newly installed: $((${#packages_to_install[@]} - ${#failed_packages[@]}))"
    
    if [[ ${#failed_packages[@]} -gt 0 ]]; then
        echo "  $(red "Failed installations: ${#failed_packages[@]}")"
        echo "    Failed packages: ${failed_packages[*]}"
        return 1
    else
        echo "  $(green "✓ All installations successful!")"
        return 0
    fi
}

# Install specific package
install_specific_package() {
    local target_package="$1"
    local found=false
    
    for package_info in "${PACKAGES[@]}"; do
        IFS=':' read -r package description <<< "$package_info"
        
        if [[ "$package" == "$target_package" ]]; then
            found=true
            echo "$(blue "Installing specific package: $package")"
            echo
            
            if check_package_status "$package"; then
                echo "$(green "✓ $package is already installed")"
                return 0
            fi
            
            install_package "$package" "$description"
            return $?
        fi
    done
    
    if [[ "$found" == "false" ]]; then
        red "Error: Package '$target_package' not found in package list"
        echo "Available packages:"
        for package_info in "${PACKAGES[@]}"; do
            IFS=':' read -r package description <<< "$package_info"
            echo "  - $package"
        done
        return 1
    fi
}

# Main execution
main() {
    if [[ "$LIST_ONLY" == "true" ]]; then
        list_packages
        exit 0
    fi
    
    # Check prerequisites
    check_paru
    
    echo "$(green "CLI Tools Installation Script")"
    echo "Log file: $LOG_FILE"
    echo
    
    if [[ -n "$INSTALL_SPECIFIC" ]]; then
        install_specific_package "$INSTALL_SPECIFIC"
        exit_code=$?
    else
        install_all_packages
        exit_code=$?
    fi
    
    echo
    echo "Installation completed at: $(date)"
    
    if [[ $exit_code -eq 0 ]]; then
        echo "$(green "✅ CLI tools installation successful!")"
    else
        echo "$(red "❌ Some installations failed. Check the log for details.")"
    fi
    
    exit $exit_code
}

# Run main function
main "$@"