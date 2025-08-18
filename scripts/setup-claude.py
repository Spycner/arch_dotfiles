#!/usr/bin/env python3
"""
Claude Code Configuration Setup

Sets up project-specific Claude Code agents and commands directories
with symlinks to the user's global Claude configuration.

Usage:
    uv run scripts/setup-claude.py [options]
"""

# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ClaudeSetup:
    """Manages Claude Code configuration setup with backup and rollback support."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        """Initialize the Claude setup manager."""
        self.repo_root = repo_root
        self.dry_run = dry_run
        
        # Setup directories
        self.data_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles'
        self.backup_dir = self.data_dir / 'backups' / 'claude'
        self.state_file = self.data_dir / 'claude_state.json'
        self.log_dir = self.data_dir / 'logs'
        
        # Claude directories
        self.user_claude_dir = Path.home() / '.claude'
        self.project_claude_dir = self.repo_root / '.claude'
        
        # Target directories for symlinks
        self.symlink_targets = {
            'agents': {
                'source': self.project_claude_dir / 'agents',
                'target': self.user_claude_dir / 'agents'
            },
            'commands': {
                'source': self.project_claude_dir / 'commands',
                'target': self.user_claude_dir / 'commands'
            }
        }
        
        # Create necessary directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # ANSI color codes
        self.colors = {
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'reset': '\033[0m'
        }
    
    def _setup_logging(self):
        """Setup logging configuration."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f'claude-setup-{timestamp}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Log file: {log_file}")
    
    def _color(self, text: str, color: str) -> str:
        """Apply color to text."""
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"
    
    def _load_state(self) -> Dict:
        """Load setup state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load state file: {e}")
        return {
            'version': '1.0',
            'setup_timestamp': None,
            'backups': {},
            'symlinks_created': []
        }
    
    def _save_state(self, state: Dict):
        """Save setup state to file."""
        if not self.dry_run:
            try:
                with open(self.state_file, 'w') as f:
                    json.dump(state, f, indent=2)
                self.logger.info(f"State saved to {self.state_file}")
            except Exception as e:
                self.logger.error(f"Failed to save state: {e}")
    
    def _create_backup(self, path: Path) -> Optional[Path]:
        """Create a backup of an existing directory or file."""
        if not path.exists():
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{path.name}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would backup {path} to {backup_path}")
            return backup_path
        
        try:
            if path.is_dir():
                shutil.copytree(path, backup_path, symlinks=True)
            else:
                shutil.copy2(path, backup_path)
            
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup of {path}: {e}")
            return None
    
    def _create_symlink(self, source: Path, target: Path) -> bool:
        """Create a symlink from target to source."""
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would create symlink {target} -> {source}")
            return True
        
        try:
            # Ensure source directory exists
            source.mkdir(parents=True, exist_ok=True)
            
            # Remove target if it exists and is not a symlink to our source
            if target.exists() or target.is_symlink():
                if target.is_symlink() and target.readlink() == source:
                    self.logger.info(f"Symlink already exists: {target} -> {source}")
                    return True
                
                # Remove existing target
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            
            # Create the symlink
            target.symlink_to(source)
            self.logger.info(f"Created symlink: {target} -> {source}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create symlink {target} -> {source}: {e}")
            return False
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        issues = []
        
        # Check if repo_root exists
        if not self.repo_root.exists():
            issues.append(f"Repository root not found: {self.repo_root}")
        
        # Check if .claude directories exist in project
        if not self.project_claude_dir.exists():
            issues.append(f"Project .claude directory not found: {self.project_claude_dir}")
        
        # Check if user .claude directory exists
        if not self.user_claude_dir.exists():
            issues.append(f"User .claude directory not found: {self.user_claude_dir}")
            issues.append("This usually means Claude Code hasn't been run yet.")
        
        if issues:
            print(self._color("Prerequisites check failed:", 'red'))
            for issue in issues:
                print(f"  - {issue}")
            return False
        
        return True
    
    def status(self) -> None:
        """Show current status of Claude configuration."""
        print(self._color("Claude Code Configuration Status", 'blue'))
        print()
        
        state = self._load_state()
        
        # Check if setup has been run
        if state.get('setup_timestamp'):
            setup_time = datetime.fromisoformat(state['setup_timestamp'])
            print(f"  {self._color('✓', 'green')} Setup completed: {setup_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"  {self._color('○', 'yellow')} Setup not completed")
        
        print()
        print("Symlink Status:")
        
        for name, config in self.symlink_targets.items():
            source = config['source']
            target = config['target']
            
            if target.is_symlink():
                actual_target = target.readlink()
                if actual_target == source:
                    status = self._color('✓ Linked correctly', 'green')
                else:
                    status = self._color(f'⚠ Links to {actual_target}', 'yellow')
            elif target.exists():
                status = self._color('⚠ Exists but not a symlink', 'yellow')
            else:
                status = self._color('✗ Not linked', 'red')
            
            print(f"  {name:10} {status}")
            print(f"             {target} -> {source}")
        
        print()
        
        # Show backup information
        if state.get('backups'):
            print("Available Backups:")
            for name, backup_path in state['backups'].items():
                if Path(backup_path).exists():
                    print(f"  {name}: {backup_path}")
                else:
                    print(f"  {name}: {backup_path} (missing)")
        else:
            print("No backups available")
    
    def setup(self) -> bool:
        """Perform the Claude configuration setup."""
        print(self._color("Setting up Claude Code configuration...", 'blue'))
        print()
        
        if not self.check_prerequisites():
            return False
        
        state = self._load_state()
        timestamp = datetime.now().isoformat()
        
        # Create backups of existing directories
        print("Creating backups of existing configurations...")
        backups_created = {}
        
        for name, config in self.symlink_targets.items():
            target = config['target']
            
            if target.exists() and not target.is_symlink():
                backup_path = self._create_backup(target)
                if backup_path:
                    backups_created[name] = str(backup_path)
                    print(f"  {self._color('✓', 'green')} Backed up {name}: {backup_path}")
                else:
                    print(f"  {self._color('✗', 'red')} Failed to backup {name}")
                    return False
            else:
                print(f"  {self._color('○', 'yellow')} No backup needed for {name}")
        
        print()
        
        # Create symlinks
        print("Creating symlinks...")
        symlinks_created = []
        
        for name, config in self.symlink_targets.items():
            source = config['source']
            target = config['target']
            
            if self._create_symlink(source, target):
                symlinks_created.append(name)
                print(f"  {self._color('✓', 'green')} Created {name} symlink")
            else:
                print(f"  {self._color('✗', 'red')} Failed to create {name} symlink")
                return False
        
        # Update state
        if backups_created:
            state['backups'].update(backups_created)
        state['symlinks_created'] = symlinks_created
        state['setup_timestamp'] = timestamp
        
        self._save_state(state)
        
        print()
        print(self._color("✅ Claude Code configuration setup completed!", 'green'))
        print()
        print("Next steps:")
        print("  - Add custom agents to .claude/agents/")
        print("  - Add custom commands to .claude/commands/")
        print("  - Run 'claude --help' to see available agents and commands")
        
        return True
    
    def rollback(self) -> bool:
        """Rollback the Claude configuration setup."""
        print(self._color("Rolling back Claude Code configuration...", 'blue'))
        print()
        
        state = self._load_state()
        
        if not state.get('setup_timestamp'):
            print(self._color("No setup found to rollback", 'yellow'))
            return True
        
        # Remove symlinks
        print("Removing symlinks...")
        for name in state.get('symlinks_created', []):
            if name in self.symlink_targets:
                target = self.symlink_targets[name]['target']
                
                if target.is_symlink():
                    if self.dry_run:
                        print(f"  DRY RUN: Would remove symlink {target}")
                    else:
                        target.unlink()
                        print(f"  {self._color('✓', 'green')} Removed {name} symlink")
                else:
                    print(f"  {self._color('○', 'yellow')} {name} symlink not found")
        
        print()
        
        # Restore backups
        print("Restoring backups...")
        for name, backup_path in state.get('backups', {}).items():
            backup = Path(backup_path)
            
            if not backup.exists():
                print(f"  {self._color('⚠', 'yellow')} Backup not found: {backup_path}")
                continue
            
            if name in self.symlink_targets:
                target = self.symlink_targets[name]['target']
                
                if self.dry_run:
                    print(f"  DRY RUN: Would restore {name} from {backup_path}")
                else:
                    try:
                        # Remove current target if it exists
                        if target.exists():
                            if target.is_dir():
                                shutil.rmtree(target)
                            else:
                                target.unlink()
                        
                        # Restore from backup
                        if backup.is_dir():
                            shutil.copytree(backup, target)
                        else:
                            shutil.copy2(backup, target)
                        
                        print(f"  {self._color('✓', 'green')} Restored {name}")
                        
                    except Exception as e:
                        print(f"  {self._color('✗', 'red')} Failed to restore {name}: {e}")
                        return False
        
        # Clear state
        if not self.dry_run:
            state = {
                'version': '1.0',
                'setup_timestamp': None,
                'backups': {},
                'symlinks_created': []
            }
            self._save_state(state)
        
        print()
        print(self._color("✅ Rollback completed successfully!", 'green'))
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Claude Code Configuration Setup',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    uv run scripts/setup-claude.py              # Setup Claude configuration
    uv run scripts/setup-claude.py --dry-run    # Preview what would be done
    uv run scripts/setup-claude.py --status     # Show current status
    uv run scripts/setup-claude.py --rollback   # Undo setup

DESCRIPTION:
    This script sets up project-specific Claude Code agents and commands
    directories by creating symlinks from ~/.claude/agents and ~/.claude/commands
    to the project's .claude/ directories.
    
    This allows you to version control and share Claude configurations
    with your team while maintaining compatibility with Claude Code.
        """
    )
    
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--status', action='store_true',
                        help='Show current status of Claude configuration')
    parser.add_argument('--rollback', action='store_true',
                        help='Rollback the Claude configuration setup')
    
    args = parser.parse_args()
    
    # Determine repository root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    
    # Create setup instance
    setup = ClaudeSetup(repo_root, dry_run=args.dry_run)
    
    # Handle different modes
    if args.status:
        setup.status()
        return 0
    elif args.rollback:
        success = setup.rollback()
        return 0 if success else 1
    else:
        success = setup.setup()
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())