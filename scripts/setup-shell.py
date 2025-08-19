"""
Shell Configuration Setup Script

This script sets up zsh configuration by creating symlinks from the repository
to the user's home directory. It includes backup, rollback, and validation features.
Optionally enables vim mode for enhanced command line editing.

Usage:
    uv run setup-shell.py [--dry-run] [--rollback] [--vim-mode] [--help]
"""
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class ShellSetup:
    """Main class for shell configuration setup."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False, vim_mode: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.vim_mode = vim_mode
        self.home_dir = Path.home()
        self.backup_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'backups'
        self.state_file = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'shell_setup_state.json'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Environment file for vim mode setting
        self.zshenv_path = self.home_dir / '.zshenv'
        
        # Files to link
        self.zdotdir = self.home_dir / '.config' / 'shell' / 'zsh'
        self.link_map = {
            # Home directory symlinks
            self.repo_root / 'config' / 'shell' / 'zsh' / 'zshenv': self.home_dir / '.zshenv',
            self.repo_root / 'config' / 'shell' / 'zsh' / 'starship.toml': self.home_dir / '.config' / 'starship.toml',
            # ZDOTDIR symlinks (zsh looks here when ZDOTDIR is set)
            self.repo_root / 'config' / 'shell' / 'zsh' / 'zshrc': self.zdotdir / '.zshrc',
        }
        
        # Ensure required directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def print_status(self, message: str, color: str = Colors.WHITE):
        """Print a colored status message."""
        print(f"{color}{message}{Colors.RESET}")

    def print_error(self, message: str):
        """Print an error message."""
        self.print_status(f"❌ {message}", Colors.RED)

    def print_success(self, message: str):
        """Print a success message."""
        self.print_status(f"✅ {message}", Colors.GREEN)

    def print_info(self, message: str):
        """Print an info message."""
        self.print_status(f"ℹ️  {message}", Colors.BLUE)

    def print_warning(self, message: str):
        """Print a warning message."""
        self.print_status(f"⚠️  {message}", Colors.YELLOW)

    def validate_repository(self) -> bool:
        """Validate that we're in the correct repository with required files."""
        required_files = [
            self.repo_root / 'config' / 'shell' / 'zsh' / 'zshrc',
            self.repo_root / 'config' / 'shell' / 'zsh' / 'zshenv',
            self.repo_root / 'config' / 'shell' / 'zsh' / 'starship.toml',
        ]
        
        # Add vim-mode.zsh if vim mode is enabled
        if self.vim_mode:
            required_files.append(self.repo_root / 'config' / 'shell' / 'zsh' / 'vim-mode.zsh')
        
        for file_path in required_files:
            if not file_path.exists():
                self.print_error(f"Required file not found: {file_path}")
                return False
                
        return True

    def backup_existing_config(self) -> Dict[str, str]:
        """Create timestamped backups of existing configuration files."""
        backups = {}
        
        self.print_info(f"Creating backups in {self.backup_dir}")
        
        for source, target in self.link_map.items():
            if target.exists() or target.is_symlink():
                backup_name = f"{target.name}.backup.{self.timestamp}"
                backup_path = self.backup_dir / backup_name
                
                if not self.dry_run:
                    if target.is_symlink():
                        # For symlinks, save the target path
                        backup_info_path = self.backup_dir / f"{target.name}.backup.{self.timestamp}.info"
                        with open(backup_info_path, 'w') as f:
                            f.write(f"symlink_target: {target.readlink()}")
                        backups[str(target)] = str(backup_info_path)
                        self.print_info(f"Saved symlink info: {target} -> {backup_info_path}")
                    else:
                        shutil.copy2(target, backup_path)
                        backups[str(target)] = str(backup_path)
                        self.print_info(f"Backed up: {target} -> {backup_path}")
                else:
                    backups[str(target)] = str(backup_path)
                    self.print_info(f"Would backup: {target} -> {backup_path}")
        
        return backups

    def create_symlinks(self) -> bool:
        """Create symlinks from repository to home directory."""
        self.print_info("Creating symlinks...")
        
        for source, target in self.link_map.items():
            try:
                if not self.dry_run:
                    # Remove existing file/symlink
                    if target.exists() or target.is_symlink():
                        target.unlink()
                    
                    # Create symlink
                    target.symlink_to(source)
                
                self.print_success(f"Linked: {target} -> {source}")
                
            except Exception as e:
                self.print_error(f"Failed to create symlink {target} -> {source}: {e}")
                return False
        
        return True

    def install_packages(self) -> bool:
        """Install required packages using paru."""
        packages = ['starship-git']
        
        self.print_info("Installing required packages...")
        
        for package in packages:
            # Check if package is already installed
            try:
                result = subprocess.run(['paru', '-Q', package], capture_output=True, text=True)
                if result.returncode == 0:
                    self.print_success(f"Package {package} is already installed")
                    continue
            except FileNotFoundError:
                self.print_error("paru not found. Please install an AUR helper.")
                return False
            
            # Install the package
            if not self.dry_run:
                self.print_info(f"Installing {package} from AUR...")
                try:
                    result = subprocess.run(['paru', '-S', '--noconfirm', package], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        self.print_success(f"Successfully installed {package}")
                    else:
                        self.print_error(f"Failed to install {package}: {result.stderr}")
                        return False
                except Exception as e:
                    self.print_error(f"Failed to install {package}: {e}")
                    return False
            else:
                self.print_info(f"Would install {package}")
        
        return True
    
    def verify_installations(self) -> bool:
        """Verify that required commands are available."""
        commands = ['starship']
        
        for cmd in commands:
            if not self.dry_run:
                cmd_path = shutil.which(cmd)
                if cmd_path:
                    self.print_success(f"Command {cmd} is available at {cmd_path}")
                else:
                    self.print_error(f"Command {cmd} not found after installation")
                    return False
            else:
                self.print_info(f"Would verify {cmd} command is available")
        
        return True

    def ensure_config_directory(self) -> bool:
        """Ensure the .config and ZDOTDIR directories exist."""
        directories = [
            self.home_dir / '.config',
            self.zdotdir
        ]
        
        for config_dir in directories:
            if not self.dry_run:
                try:
                    config_dir.mkdir(parents=True, exist_ok=True)
                    self.print_info(f"Ensured {config_dir} exists")
                except Exception as e:
                    self.print_error(f"Failed to create {config_dir}: {e}")
                    return False
            else:
                self.print_info(f"Would ensure {config_dir} exists")
        
        return True

    def check_vim_mode_status(self) -> bool:
        """Check if vim mode is currently enabled."""
        # Check if ZSH_VIM_MODE is set in environment
        if 'ZSH_VIM_MODE' in os.environ:
            return os.environ['ZSH_VIM_MODE'].lower() == 'true'
            
        # Check .zshenv for ZSH_VIM_MODE setting
        if self.zshenv_path.exists():
            try:
                content = self.zshenv_path.read_text()
                for line in content.split('\n'):
                    if line.strip().startswith('export ZSH_VIM_MODE='):
                        value = line.split('=', 1)[1].strip().strip('"\'')
                        return value.lower() == 'true'
            except Exception as e:
                self.print_warning(f"Could not read .zshenv: {e}")
        
        return False

    def configure_vim_mode(self) -> bool:
        """Configure vim mode setting in .zshenv."""
        try:
            # Backup .zshenv if it exists
            if self.zshenv_path.exists():
                backup_name = f".zshenv.backup.{self.timestamp}"
                backup_path = self.backup_dir / backup_name
                if not self.dry_run:
                    shutil.copy2(self.zshenv_path, backup_path)
                    self.print_info(f"Backed up .zshenv to {backup_path}")
            
            # Read existing .zshenv content
            existing_content = ""
            if self.zshenv_path.exists():
                existing_content = self.zshenv_path.read_text()
            
            # Check if ZSH_VIM_MODE is already set
            lines = existing_content.split('\n') if existing_content else []
            updated_lines = []
            vim_mode_found = False
            
            for line in lines:
                if line.strip().startswith('export ZSH_VIM_MODE='):
                    updated_lines.append(f'export ZSH_VIM_MODE="{str(self.vim_mode).lower()}"')
                    vim_mode_found = True
                else:
                    updated_lines.append(line)
            
            # Add ZSH_VIM_MODE if not found
            if not vim_mode_found:
                if updated_lines and updated_lines[-1].strip():
                    updated_lines.append('')  # Add blank line if file doesn't end with one
                updated_lines.extend([
                    '# Vim mode for zsh (managed by setup-shell.py)',
                    f'export ZSH_VIM_MODE="{str(self.vim_mode).lower()}"'
                ])
            
            new_content = '\n'.join(updated_lines)
            
            if not self.dry_run:
                self.zshenv_path.write_text(new_content)
                status = "enabled" if self.vim_mode else "disabled"
                self.print_success(f"Vim mode {status} in {self.zshenv_path}")
            else:
                status = "enable" if self.vim_mode else "disable"
                self.print_info(f"Would {status} vim mode in {self.zshenv_path}")
            
            return True
            
        except Exception as e:
            self.print_error(f"Failed to configure vim mode: {e}")
            return False

    def save_state(self, backups: Dict[str, str]) -> bool:
        """Save setup state for rollback purposes."""
        state = {
            'timestamp': self.timestamp,
            'backups': backups,
            'links': {str(target): str(source) for source, target in self.link_map.items()},
            'vim_mode': self.vim_mode,
            'vim_mode_status': self.check_vim_mode_status()
        }
        
        if not self.dry_run:
            try:
                with open(self.state_file, 'w') as f:
                    json.dump(state, f, indent=2)
                self.print_info(f"Saved state to {self.state_file}")
                return True
            except Exception as e:
                self.print_error(f"Failed to save state: {e}")
                return False
        else:
            self.print_info(f"Would save state to {self.state_file}")
            return True

    def setup(self) -> bool:
        """Main setup function."""
        self.print_status(f"{Colors.BOLD}🐚 Shell Configuration Setup with Starship{Colors.RESET}")
        
        if self.dry_run:
            self.print_warning("DRY RUN MODE - No changes will be made")
        
        # Validate repository
        if not self.validate_repository():
            return False
        
        # Install required packages
        if not self.install_packages():
            return False
        
        # Verify installations
        if not self.verify_installations():
            return False
        
        # Ensure config directory exists
        if not self.ensure_config_directory():
            return False
        
        # Configure vim mode if requested
        if self.vim_mode or self.check_vim_mode_status():
            if not self.configure_vim_mode():
                return False
        
        # Backup existing configuration
        backups = self.backup_existing_config()
        
        # Create symlinks
        if not self.create_symlinks():
            return False
        
        # Save state for rollback
        if not self.save_state(backups):
            return False
        
        if not self.dry_run:
            self.print_success("Shell configuration setup completed!")
            self.print_info("✨ Starship prompt has been configured!")
            if self.vim_mode:
                self.print_info("🎯 Vim mode enabled with advanced keybindings!")
            self.print_info("Restart your shell or run 'exec zsh' to use the new configuration")
        else:
            self.print_info("Dry run completed. Use without --dry-run to apply changes.")
            if self.vim_mode:
                self.print_info("Vim mode would be enabled")
        
        return True

    def rollback(self) -> bool:
        """Rollback to previous configuration."""
        self.print_status(f"{Colors.BOLD}🔄 Rolling back shell configuration{Colors.RESET}")
        
        if not self.state_file.exists():
            self.print_error(f"No state file found at {self.state_file}")
            return False
        
        try:
            with open(self.state_file) as f:
                state = json.load(f)
        except Exception as e:
            self.print_error(f"Failed to load state file: {e}")
            return False
        
        # Restore backups
        for target_path, backup_path in state['backups'].items():
            target = Path(target_path)
            backup = Path(backup_path)
            
            try:
                # Remove current symlink
                if target.exists() or target.is_symlink():
                    target.unlink()
                
                if backup.name.endswith('.info'):
                    # Restore symlink
                    with open(backup) as f:
                        info = f.read().strip()
                        if info.startswith('symlink_target: '):
                            symlink_target = info[len('symlink_target: '):]
                            target.symlink_to(symlink_target)
                            self.print_success(f"Restored symlink: {target} -> {symlink_target}")
                else:
                    # Restore regular file
                    shutil.copy2(backup, target)
                    self.print_success(f"Restored: {backup} -> {target}")
                    
            except Exception as e:
                self.print_error(f"Failed to restore {target}: {e}")
                return False
        
        # Remove state file
        self.state_file.unlink()
        self.print_success("Rollback completed!")
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Setup shell configuration")
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--rollback', action='store_true',
                       help='Rollback to previous configuration')
    parser.add_argument('--vim-mode', action='store_true',
                       help='Enable vim mode for enhanced command line editing')
    
    args = parser.parse_args()
    
    # Get repository root
    repo_root = Path(__file__).parent.parent.resolve()
    
    # Verify we're in the arch_dotfiles repository
    if not (repo_root / 'CLAUDE.md').exists():
        print(f"{Colors.RED}❌ This script must be run from the arch_dotfiles repository{Colors.RESET}")
        sys.exit(1)
    
    setup = ShellSetup(repo_root, dry_run=args.dry_run, vim_mode=args.vim_mode)
    
    if args.rollback:
        success = setup.rollback()
    else:
        success = setup.setup()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()