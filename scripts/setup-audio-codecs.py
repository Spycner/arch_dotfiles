"""
Audio Codec Setup Script for Arch Linux

This script automates the installation and configuration of audio codecs,
including PipeWire components, GStreamer plugins, and various codec libraries
for comprehensive multimedia support. Uses paru for all package operations.

Requirements:
    - paru (AUR helper) must be installed

Usage:
    uv run setup-audio-codecs.py [--dry-run] [--rollback] [--minimal] [--skip-aur] [--help]

Options:
    --dry-run    Preview changes without installing
    --rollback   Remove packages installed by this script
    --minimal    Install only essential codecs (skip optional)
    --skip-aur   Skip AUR packages, only use official repos
    --help       Show this help message

Examples:
    # Install all audio codecs
    uv run scripts/setup-audio-codecs.py

    # Preview what would be installed
    uv run scripts/setup-audio-codecs.py --dry-run

    # Install minimal codec set
    uv run scripts/setup-audio-codecs.py --minimal

    # Rollback installation
    uv run scripts/setup-audio-codecs.py --rollback
"""
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


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


class AudioCodecSetup:
    """Main class for audio codec installation and management."""
    
    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.backup_dir = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'backups'
        self.state_file = Path.home() / '.local' / 'share' / 'arch_dotfiles' / 'audio_codec_state.json'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Define package categories
        self.packages = {
            'pipewire_core': {
                'official': [
                    'pipewire-audio',  # Meta package that pulls in pipewire
                    'pipewire-alsa',
                    'pipewire-pulse',
                    'pipewire-jack',
                    'wireplumber',
                    'qpwgraph'  # Visual patchbay
                ],
                'aur': [],
                'description': 'Core PipeWire audio stack'
            },
            'gstreamer_essential': {
                'official': [
                    'gstreamer',
                    'gst-plugins-base',
                    'gst-plugins-good',
                    'gst-plugin-pipewire'
                ],
                'aur': [],
                'description': 'Essential GStreamer plugins'
            },
            'gstreamer_extended': {
                'official': [
                    'gst-plugins-bad',
                    'gst-plugins-ugly',
                    'gst-libav'  # FFmpeg integration
                ],
                'aur': [],
                'description': 'Extended GStreamer plugins (proprietary formats)'
            },
            'codec_libraries': {
                'official': [
                    'libmad',      # MP3 decoding
                    'lame',        # MP3 encoding
                    'flac',        # FLAC support
                    'opus',        # Opus codec
                    'libvorbis',   # Ogg Vorbis
                    'faac',        # AAC encoding
                    'faad2',       # AAC decoding
                    'wavpack',     # WavPack format
                    'a52dec',      # AC3/DTS decoding
                    'libdca',      # DTS decoding
                    'libdv',       # DV video codec
                    'libmpeg2',    # MPEG-2 decoding
                    'x264',        # H.264 encoding
                    'x265',        # H.265/HEVC encoding
                    'opencore-amr' # AMR audio codec
                ],
                'aur': [],
                'description': 'Codec libraries for various formats'
            },
            'multimedia_tools': {
                'official': [
                    'ffmpeg',       # Already installed but ensure latest
                    'sox',          # Sound processing
                    'mediainfo',    # Media file information
                    'pavucontrol',  # PulseAudio/PipeWire volume control
                    'easyeffects'   # Audio effects for PipeWire
                ],
                'aur': [],
                'description': 'Multimedia tools and utilities'
            },
            'professional': {
                'official': [],
                'aur': [
                    'ffmpeg-full',     # Enhanced FFmpeg with all codecs
                ],
                'description': 'Professional/enhanced codec support (AUR)'
            }
        }
        
        # Categories for minimal installation
        self.minimal_categories = [
            'pipewire_core',
            'gstreamer_essential',
            'codec_libraries'
        ]
        
        # All categories for full installation
        self.full_categories = list(self.packages.keys())
    
    def print_info(self, message: str) -> None:
        """Print an info message."""
        print(f"{Colors.BLUE}ℹ{Colors.RESET}  {message}")
    
    def print_success(self, message: str) -> None:
        """Print a success message."""
        print(f"{Colors.GREEN}✓{Colors.RESET}  {message}")
    
    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        print(f"{Colors.YELLOW}⚠{Colors.RESET}  {message}")
    
    def print_error(self, message: str) -> None:
        """Print an error message."""
        print(f"{Colors.RED}✗{Colors.RESET}  {message}")
    
    def print_header(self, message: str) -> None:
        """Print a section header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}═══ {message} ═══{Colors.RESET}\n")
    
    def check_installed_packages(self) -> Dict[str, bool]:
        """Check which packages are already installed using paru."""
        installed = {}
        
        try:
            result = subprocess.run(
                ['paru', '-Q'],
                capture_output=True,
                text=True,
                check=True
            )
            installed_list = {line.split()[0] for line in result.stdout.strip().split('\n')}
            
            for category, info in self.packages.items():
                for pkg in info['official'] + info['aur']:
                    installed[pkg] = pkg in installed_list
            
        except subprocess.CalledProcessError:
            self.print_error("Failed to check installed packages")
            return {}
        
        return installed
    
    def check_conflicts(self, packages: List[str]) -> Dict[str, List[str]]:
        """Check for package conflicts before installation."""
        conflicts = {}
        
        # Known conflicting packages
        conflict_map = {
            'pipewire-jack': ['jack', 'jack2', 'pipewire-jack-client'],
            'pipewire-pulse': ['pulseaudio', 'pulseaudio-bluetooth'],
            'pipewire-alsa': ['pulseaudio-alsa']
        }
        
        try:
            result = subprocess.run(
                ['paru', '-Q'],
                capture_output=True,
                text=True,
                check=True
            )
            installed_list = {line.split()[0] for line in result.stdout.strip().split('\n')}
            
            for pkg in packages:
                if pkg in conflict_map:
                    conflicting = [c for c in conflict_map[pkg] if c in installed_list]
                    if conflicting:
                        conflicts[pkg] = conflicting
            
        except subprocess.CalledProcessError:
            pass
        
        return conflicts
    
    def check_package_dependencies(self, package: str) -> List[str]:
        """Check what packages depend on a given package."""
        try:
            result = subprocess.run(
                ['paru', '-Qi', package],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.split('\n'):
                if line.strip().startswith('Required By'):
                    deps = line.split(':', 1)[1].strip()
                    if deps == 'None':
                        return []
                    return [dep.strip() for dep in deps.split()]
            
        except subprocess.CalledProcessError:
            pass
        
        return []
    
    def resolve_conflicts(self, conflicts: Dict[str, List[str]]) -> bool:
        """Handle package conflicts by asking user permission to replace."""
        if not conflicts:
            return True
        
        self.print_warning("Package conflicts detected:")
        
        # Check dependencies for conflicting packages
        blocking_deps = {}
        for new_pkg, conflicting_pkgs in conflicts.items():
            self.print_info(f"  • {new_pkg} conflicts with: {', '.join(conflicting_pkgs)}")
            
            for conflicting_pkg in conflicting_pkgs:
                deps = self.check_package_dependencies(conflicting_pkg)
                if deps:
                    blocking_deps[conflicting_pkg] = deps
                    self.print_warning(f"    - {conflicting_pkg} is required by: {', '.join(deps[:3])}{'...' if len(deps) > 3 else ''}")
        
        if blocking_deps:
            self.print_info(f"\n{Colors.YELLOW}Some conflicting packages have dependencies that prevent removal.{Colors.RESET}")
            self.print_info(f"We'll skip the conflicting PipeWire components for now.")
            self.print_info(f"Your existing audio system will continue to work.")
            
            # Remove conflicting packages from installation list
            for pkg in conflicts.keys():
                if pkg in self.current_packages:
                    self.current_packages.remove(pkg)
                    self.print_info(f"  - Skipped: {pkg}")
            
            if self.dry_run:
                self.print_info("[DRY-RUN] Would skip conflicting packages")
            
            return True
        else:
            self.print_info(f"\nPipeWire provides modern replacements for these legacy audio systems.")
            self.print_info(f"It's recommended to replace conflicting packages for better performance.")
            
            if self.dry_run:
                self.print_info("[DRY-RUN] Would ask user to resolve conflicts")
                return True
            
            response = input(f"\n{Colors.YELLOW}Replace conflicting packages? (y/N): {Colors.RESET}")
            if response.lower() != 'y':
                self.print_info("Installation cancelled due to conflicts")
                return False
            
            # Remove conflicting packages
            all_conflicting = []
            for conflicting_list in conflicts.values():
                all_conflicting.extend(conflicting_list)
            
            if all_conflicting:
                self.print_info(f"Removing conflicting packages: {', '.join(all_conflicting)}")
                cmd = ['paru', '-R', '--noconfirm'] + all_conflicting
                success, output = self.run_command(cmd, check=False)
                
                if not success:
                    self.print_warning("Failed to remove some conflicting packages")
                    self.print_info("You may need to resolve conflicts manually")
                    return False
                else:
                    self.print_success(f"Removed {len(all_conflicting)} conflicting packages")
            
            return True
    
    def run_command(self, cmd: List[str], check: bool = True) -> Tuple[bool, str]:
        """Run a shell command and return success status and output."""
        if self.dry_run:
            self.print_info(f"[DRY-RUN] Would run: {' '.join(cmd)}")
            return True, ""
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
    
    def install_packages(self, packages: List[str], aur: bool = False) -> bool:
        """Install a list of packages using paru."""
        if not packages:
            return True
        
        # Filter out already installed packages
        installed_check = self.check_installed_packages()
        to_install = [pkg for pkg in packages if not installed_check.get(pkg, False)]
        
        if not to_install:
            self.print_info(f"All packages already installed")
            return True
        
        # Store current packages for conflict resolution
        self.current_packages = to_install.copy()
        
        # Check for conflicts
        conflicts = self.check_conflicts(to_install)
        if conflicts:
            if not self.resolve_conflicts(conflicts):
                return False
            # Update to_install list after conflict resolution
            to_install = self.current_packages
        
        if not to_install:
            self.print_info("No packages to install after conflict resolution")
            return True
        
        # Use paru for all installations (it handles both official repos and AUR)
        cmd = ['paru', '-S', '--noconfirm', '--needed'] + to_install
        
        repo_type = "AUR" if aur else "official repositories"
        self.print_info(f"Installing {len(to_install)} packages from {repo_type}: {', '.join(to_install[:3])}{'...' if len(to_install) > 3 else ''}")
        
        success, output = self.run_command(cmd)
        
        if success:
            self.print_success(f"Successfully installed {len(to_install)} packages")
        else:
            # Check if it's a mirror sync issue
            if "404" in output and "failed retrieving file" in output:
                self.print_warning(f"Mirror sync issue detected. Trying to refresh package databases...")
                if not self.dry_run:
                    refresh_success, _ = self.run_command(['paru', '-Sy'], check=False)
                    if refresh_success:
                        self.print_info("Retrying installation after database refresh...")
                        success, output = self.run_command(cmd)
                        if success:
                            self.print_success(f"Successfully installed {len(to_install)} packages after retry")
                            return True
            
            self.print_error(f"Failed to install packages")
            if "404" in output and "failed retrieving file" in output:
                self.print_warning("This appears to be a temporary mirror synchronization issue.")
                self.print_info("You can try running the script again later, or manually run:")
                self.print_info(f"  paru -Sy && paru -S {' '.join(to_install)}")
            elif output:
                print(f"{Colors.RED}Error output:{Colors.RESET}")
                print(output[:1000] + '...' if len(output) > 1000 else output)
        
        return success
    
    def load_state(self) -> Dict:
        """Load the installation state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.print_warning(f"Could not load state file: {e}")
        return {}
    
    def save_state(self, installed_packages: List[str]) -> None:
        """Save the installation state to file."""
        if self.dry_run:
            self.print_info("[DRY-RUN] Would save state file")
            return
        
        state = {
            'timestamp': self.timestamp,
            'installed_packages': installed_packages,
            'version': '1.0'
        }
        
        # Create directory if it doesn't exist
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            self.print_success(f"State saved to {self.state_file}")
        except Exception as e:
            self.print_error(f"Failed to save state: {e}")
    
    def verify_audio_system(self) -> bool:
        """Verify that the audio system is working correctly."""
        self.print_header("Verifying Audio System")
        
        checks_passed = True
        
        # Check PipeWire service
        self.print_info("Checking PipeWire service...")
        success, output = self.run_command(
            ['systemctl', '--user', 'is-active', 'pipewire'],
            check=False
        )
        if output.strip() == 'active':
            self.print_success("PipeWire service is active")
        else:
            self.print_warning("PipeWire service is not active")
            checks_passed = False
        
        # Check WirePlumber service
        success, output = self.run_command(
            ['systemctl', '--user', 'is-active', 'wireplumber'],
            check=False
        )
        if output.strip() == 'active':
            self.print_success("WirePlumber service is active")
        else:
            self.print_warning("WirePlumber service is not active - starting it...")
            if not self.dry_run:
                start_success, _ = self.run_command(
                    ['systemctl', '--user', 'start', 'wireplumber'],
                    check=False
                )
                if start_success:
                    self.print_success("WirePlumber service started successfully")
                else:
                    self.print_warning("Failed to start WirePlumber service")
                    checks_passed = False
        
        # Check for GStreamer plugins
        self.print_info("Checking GStreamer plugins...")
        success, output = self.run_command(
            ['gst-inspect-1.0', '--version'],
            check=False
        )
        if success:
            self.print_success("GStreamer tools are available")
            
            # Check for specific important plugins
            important_plugins = ['mp3', 'aac', 'flac', 'opus', 'vorbis']
            for plugin in important_plugins:
                success, output = self.run_command(
                    ['sh', '-c', f'gst-inspect-1.0 | grep -i {plugin}'],
                    check=False
                )
                if output:
                    self.print_success(f"  • {plugin.upper()} support detected")
                else:
                    self.print_warning(f"  • {plugin.upper()} support not found")
        else:
            self.print_warning("GStreamer tools not available")
            checks_passed = False
        
        # List audio devices using PipeWire
        self.print_info("Checking audio devices...")
        success, output = self.run_command(
            ['pw-cli', 'ls', 'Node'],
            check=False
        )
        if success and output:
            # Parse PipeWire nodes for audio devices
            lines = output.split('\n')
            audio_sinks = []
            audio_sources = []
            
            for i, line in enumerate(lines):
                if 'media.class = "Audio/Sink"' in line:
                    # Look for node.name in previous lines
                    for j in range(max(0, i-10), i):
                        if 'node.name = ' in lines[j]:
                            name = lines[j].split('node.name = ')[1].strip('"')
                            if not name.startswith('Dummy') and not name.startswith('Freewheel'):
                                audio_sinks.append(name)
                            break
                elif 'media.class = "Audio/Source"' in line:
                    # Look for node.name in previous lines
                    for j in range(max(0, i-10), i):
                        if 'node.name = ' in lines[j]:
                            name = lines[j].split('node.name = ')[1].strip('"')
                            if not name.startswith('Dummy') and not name.startswith('Freewheel'):
                                audio_sources.append(name)
                            break
            
            if audio_sinks or audio_sources:
                self.print_success("Audio devices found:")
                for sink in audio_sinks[:2]:
                    self.print_info(f"  • Output: {sink.replace('alsa_output.', '').replace('alsa_input.', '')}")
                for source in audio_sources[:2]:
                    self.print_info(f"  • Input: {source.replace('alsa_input.', '').replace('alsa_output.', '')}")
            else:
                self.print_warning("No audio devices found")
        else:
            # Fallback to pactl
            success, output = self.run_command(
                ['pactl', 'list', 'short', 'sinks'],
                check=False
            )
            if success and output:
                self.print_success(f"Audio output devices found:")
                for line in output.strip().split('\n')[:3]:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        self.print_info(f"  • {parts[1]}")
            else:
                self.print_info("Audio device detection requires PipeWire to be fully started")
                self.print_info("Try logging out and back in, or restart your session")
        
        return checks_passed
    
    def setup(self, minimal: bool = False, skip_aur: bool = False) -> bool:
        """Main setup method to install audio codecs."""
        self.print_header("Audio Codec Setup for Arch Linux")
        
        # Determine which categories to install
        categories = self.minimal_categories if minimal else self.full_categories
        
        if skip_aur:
            categories = [cat for cat in categories if cat != 'professional']
        
        # Check current state
        self.print_info("Checking currently installed packages...")
        installed_before = self.check_installed_packages()
        already_installed = [pkg for pkg, is_installed in installed_before.items() if is_installed]
        
        if already_installed:
            self.print_info(f"Found {len(already_installed)} packages already installed")
        
        # Track newly installed packages
        newly_installed = []
        
        # Install packages by category
        for category in categories:
            if category not in self.packages:
                continue
            
            info = self.packages[category]
            self.print_header(info['description'])
            
            # Install official packages
            if info['official']:
                if self.install_packages(info['official'], aur=False):
                    newly_installed.extend([p for p in info['official'] 
                                          if not installed_before.get(p, False)])
                else:
                    self.print_error(f"Failed to install {category} official packages")
                    return False
            
            # Install AUR packages
            if info['aur'] and not skip_aur:
                if self.install_packages(info['aur'], aur=True):
                    newly_installed.extend([p for p in info['aur'] 
                                          if not installed_before.get(p, False)])
                else:
                    self.print_warning(f"Failed to install {category} AUR packages (continuing)")
        
        # Save state
        if newly_installed:
            self.save_state(newly_installed)
            self.print_success(f"Installed {len(newly_installed)} new packages")
        else:
            self.print_info("No new packages were installed")
        
        # Verify installation
        if not self.dry_run:
            self.verify_audio_system()
        
        # Print summary
        self.print_header("Installation Summary")
        self.print_success("Audio codec setup completed successfully!")
        
        if not self.dry_run:
            self.print_info("\nSupported audio formats now include:")
            formats = [
                "MP3, AAC, FLAC, OGG Vorbis, Opus",
                "WAV, WavPack, APE, DTS, AC3",
                "AMR, MP2, and many more..."
            ]
            for fmt in formats:
                print(f"  • {fmt}")
            
            self.print_info("\nNext steps:")
            self.print_info("• Restart your audio applications for codec changes to take effect")
            self.print_info("• Run 'paru -Syu' to ensure your system is fully updated")
            self.print_info("• Test audio playback with different formats")
            
            if any("jack" in str(conflicts) for conflicts in []):  # Will be updated if conflicts were skipped
                self.print_info("• Consider migrating from JACK2 to PipeWire-JACK in the future")
        
        return True
    
    def rollback(self) -> bool:
        """Rollback by removing packages installed by this script."""
        self.print_header("Audio Codec Rollback")
        
        # Load state
        state = self.load_state()
        if not state or 'installed_packages' not in state:
            self.print_warning("No installation state found. Nothing to rollback.")
            return False
        
        packages_to_remove = state['installed_packages']
        if not packages_to_remove:
            self.print_info("No packages to remove")
            return True
        
        self.print_warning(f"This will remove {len(packages_to_remove)} packages:")
        for pkg in packages_to_remove[:10]:
            print(f"  • {pkg}")
        if len(packages_to_remove) > 10:
            print(f"  ... and {len(packages_to_remove) - 10} more")
        
        if not self.dry_run:
            response = input(f"\n{Colors.YELLOW}Proceed with rollback? (y/N): {Colors.RESET}")
            if response.lower() != 'y':
                self.print_info("Rollback cancelled")
                return False
        
        # Remove packages using paru
        cmd = ['paru', '-R', '--noconfirm'] + packages_to_remove
        self.print_info(f"Removing {len(packages_to_remove)} packages...")
        
        success, output = self.run_command(cmd, check=False)
        
        if success:
            self.print_success("Packages removed successfully")
            # Clear state file
            if not self.dry_run and self.state_file.exists():
                self.state_file.unlink()
                self.print_success("State file cleared")
        else:
            self.print_error("Failed to remove some packages")
            self.print_info("You may need to remove them manually")
        
        return success


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Setup audio codecs for Arch Linux',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                   # Install all audio codecs
  %(prog)s --dry-run         # Preview what would be installed
  %(prog)s --minimal         # Install only essential codecs
  %(prog)s --skip-aur        # Skip AUR packages
  %(prog)s --rollback        # Remove installed packages
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without installing'
    )
    
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Remove packages installed by this script'
    )
    
    parser.add_argument(
        '--minimal',
        action='store_true',
        help='Install only essential codecs'
    )
    
    parser.add_argument(
        '--skip-aur',
        action='store_true',
        help='Skip AUR packages, only use official repos'
    )
    
    args = parser.parse_args()
    
    # Get repository root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    
    # Create setup instance
    setup = AudioCodecSetup(repo_root, dry_run=args.dry_run)
    
    try:
        if args.rollback:
            success = setup.rollback()
        else:
            success = setup.setup(
                minimal=args.minimal,
                skip_aur=args.skip_aur
            )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup interrupted by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == '__main__':
    main()