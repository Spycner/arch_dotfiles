#!/usr/bin/env python3
"""
Setup script for utility scripts
Symlinks utility scripts to ~/.local/bin/ for easy access

Usage:
    uv run scripts/setup-utils.py [--dry-run] [--rollback]
"""
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import os
import sys
import argparse
from pathlib import Path
import json
from datetime import datetime

# Color output functions
def red(text): return f"\033[31m{text}\033[0m"
def green(text): return f"\033[32m{text}\033[0m"
def yellow(text): return f"\033[33m{text}\033[0m"
def blue(text): return f"\033[34m{text}\033[0m"

class UtilitySetup:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.script_dir = Path(__file__).parent.resolve()
        self.utils_dir = self.script_dir / "utils"
        self.target_dir = Path.home() / ".local" / "bin"
        self.backup_dir = Path.home() / ".local" / "share" / "arch_dotfiles" / "backups"
        self.state_file = Path.home() / ".local" / "share" / "arch_dotfiles" / "utils_setup_state.json"
        
        # List of utility scripts to symlink
        self.utilities = [
            "layout-switcher.sh"
        ]
    
    def ensure_directories(self):
        """Create necessary directories"""
        for directory in [self.target_dir, self.backup_dir, self.state_file.parent]:
            if not self.dry_run:
                directory.mkdir(parents=True, exist_ok=True)
                if directory == self.target_dir:
                    print(f"{green('✓')} Ensured ~/.local/bin exists")
            else:
                if not directory.exists():
                    print(f"{yellow('[DRY RUN]')} Would create directory: {directory}")
    
    def load_state(self):
        """Load previous setup state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                return {"symlinks": []}
        return {"symlinks": []}
    
    def save_state(self, state):
        """Save setup state for rollback"""
        if not self.dry_run:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
    
    def backup_existing(self, path):
        """Backup existing file if it exists"""
        if path.exists() and not path.is_symlink():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{path.name}.backup.{timestamp}"
            
            if not self.dry_run:
                path.rename(backup_path)
                print(f"{yellow('⚠')} Backed up existing file: {path.name} → {backup_path}")
                return backup_path
            else:
                print(f"{yellow('[DRY RUN]')} Would backup: {path} → {backup_path}")
                return None
        return None
    
    def create_symlink(self, source, target):
        """Create symlink from source to target"""
        source_path = Path(source)
        target_path = Path(target)
        
        # Check if source exists
        if not source_path.exists():
            print(f"{red('✗')} Source not found: {source_path}")
            return False
        
        # Handle existing target
        if target_path.exists():
            if target_path.is_symlink():
                if target_path.resolve() == source_path.resolve():
                    print(f"{blue('○')} Symlink already correct: {target_path.name}")
                    return True
                else:
                    if not self.dry_run:
                        target_path.unlink()
                        print(f"{yellow('⟲')} Updating existing symlink: {target_path.name}")
                    else:
                        print(f"{yellow('[DRY RUN]')} Would update symlink: {target_path.name}")
            else:
                # Backup non-symlink file
                self.backup_existing(target_path)
        
        # Create symlink
        if not self.dry_run:
            target_path.symlink_to(source_path)
            print(f"{green('✓')} Created symlink: {target_path.name} → {source_path}")
            return True
        else:
            print(f"{yellow('[DRY RUN]')} Would create symlink: {target_path} → {source_path}")
            return True
    
    def setup_utilities(self):
        """Setup all utility script symlinks"""
        print(f"\n{blue('Setting up utility scripts in ~/.local/bin/ ...')}")
        
        state = self.load_state()
        created_symlinks = []
        
        for util in self.utilities:
            source = self.utils_dir / util
            target = self.target_dir / util
            
            if self.create_symlink(source, target):
                created_symlinks.append(str(target))
        
        # Update state
        state["symlinks"] = list(set(state.get("symlinks", []) + created_symlinks))
        state["last_setup"] = datetime.now().isoformat()
        self.save_state(state)
        
        return len(created_symlinks) > 0
    
    def check_path(self):
        """Check if ~/.local/bin is in PATH"""
        path_dirs = os.environ.get('PATH', '').split(':')
        target_str = str(self.target_dir)
        
        if target_str not in path_dirs:
            print(f"\n{yellow('⚠ Warning:')} {self.target_dir} is not in your PATH")
            print(f"  Add this to your shell config (.zshrc or .bashrc):")
            print(f"  {blue('export PATH=\"$HOME/.local/bin:$PATH\"')}")
        else:
            print(f"\n{green('✓')} ~/.local/bin is in PATH")
    
    def rollback(self):
        """Rollback symlinks created by this setup"""
        print(f"\n{blue('Rolling back utility setup...')}")
        
        state = self.load_state()
        removed_count = 0
        
        for symlink_path in state.get("symlinks", []):
            path = Path(symlink_path)
            if path.exists() and path.is_symlink():
                if not self.dry_run:
                    path.unlink()
                    print(f"{green('✓')} Removed symlink: {path}")
                else:
                    print(f"{yellow('[DRY RUN]')} Would remove symlink: {path}")
                removed_count += 1
        
        # Clear state
        if not self.dry_run:
            state["symlinks"] = []
            self.save_state(state)
        
        print(f"\n{green('✓')} Rollback complete: removed {removed_count} symlinks")
    
    def run(self):
        """Run the setup process"""
        print(f"{green('='*60)}")
        print(f"{green('Utility Scripts Setup')}")
        print(f"{green('='*60)}")
        
        if self.dry_run:
            print(f"{yellow('Running in DRY RUN mode - no changes will be made')}\n")
        
        # Create necessary directories
        self.ensure_directories()
        
        # Setup utilities
        self.setup_utilities()
        
        # Check PATH
        self.check_path()
        
        print(f"\n{green('='*60)}")
        print(f"{green('✓ Setup complete!')}")
        
        if not self.dry_run:
            print(f"\n{blue('Usage:')}")
            print(f"  After adding ~/.local/bin to PATH:")
            print(f"  • Run from anywhere: layout-switcher.sh")
            print(f"  • Check status: layout-switcher.sh --status")
            print(f"  • For status bar: layout-switcher.sh --status-bar")
            print(f"\n{blue('Hyprland keybind:')}")
            print(f"  Add to your keybinds.conf:")
            print(f"  bind = $mainMod SHIFT, L, exec, layout-switcher.sh")
        print(f"{green('='*60)}")

def main():
    parser = argparse.ArgumentParser(description='Setup utility scripts')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview changes without applying them')
    parser.add_argument('--rollback', action='store_true',
                       help='Remove symlinks created by this setup')
    
    args = parser.parse_args()
    
    setup = UtilitySetup(dry_run=args.dry_run)
    
    try:
        if args.rollback:
            setup.rollback()
        else:
            setup.run()
    except KeyboardInterrupt:
        print(f"\n{yellow('Setup interrupted by user')}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{red(f'Error: {e}')}")
        sys.exit(1)

if __name__ == "__main__":
    main()