# Comprehensive Arch Linux Installation Guide

This guide provides step-by-step instructions for installing Arch Linux from scratch, designed to be used alongside this dotfiles repository for a complete system setup.

## Table of Contents

1. [Pre-Installation Setup](#pre-installation-setup)
2. [Disk Preparation](#disk-preparation)
3. [Base System Installation](#base-system-installation)
4. [System Configuration](#system-configuration)
5. [Bootloader Installation](#bootloader-installation)
6. [User Setup](#user-setup)
7. [Network Configuration](#network-configuration)
8. [Essential Packages](#essential-packages)
9. [Post-Installation](#post-installation)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Installation Setup

### 1. Boot from Arch ISO
- Download the latest Arch Linux ISO from [archlinux.org](https://archlinux.org/download/)
- Create a bootable USB drive using `dd`, Rufus, or similar tools
- Boot from the USB drive (ensure UEFI mode if using modern hardware)

### 2. Verify Boot Mode
```bash
ls /sys/firmware/efi/efivars
```
**Expected Result**: Directory should exist (confirms UEFI mode)
**If missing**: You're in BIOS mode - adjust commands accordingly

### 3. Connect to Internet

#### For Ethernet (automatic):
```bash
ping archlinux.org
```

#### For WiFi:
```bash
iwctl
# Inside iwctl prompt:
station wlan0 scan
station wlan0 get-networks
station wlan0 connect "YourNetworkName"
exit
```

### 4. Update System Clock
```bash
timedatectl set-ntp true
timedatectl status
```

### 5. Enable SSH (Optional - for remote installation)
```bash
passwd  # Set root password
systemctl start sshd
ip addr show  # Note the IP address
```

---

## Disk Preparation

### 1. Identify Disks
```bash
lsblk
fdisk -l
```
**Note**: Identify your target disk (e.g., `/dev/sda`, `/dev/nvme0n1`)

### 2. Partition the Disk

#### Using `cfdisk` (recommended for beginners):
```bash
cfdisk /dev/sda  # Replace with your disk
```

#### Recommended UEFI Partition Scheme:
1. **EFI System Partition**: 512MB, Type: EFI System
2. **Root Partition**: Remaining space, Type: Linux filesystem
3. **Swap Partition** (optional): 2-8GB, Type: Linux swap

#### Using `fdisk` (advanced):
```bash
fdisk /dev/sda

# Commands in fdisk:
g          # Create GPT partition table
n          # New partition (EFI)
1          # Partition number
           # First sector (default)
+512M      # Last sector
t          # Change type
1          # EFI System

n          # New partition (root)
2          # Partition number
           # First sector (default)
           # Last sector (default - use remaining space)

w          # Write changes
```

### 3. Format Partitions

#### Format EFI partition:
```bash
mkfs.fat -F32 /dev/sda1
```

#### Format root partition:
```bash
mkfs.ext4 /dev/sda2
```

#### Format swap (if created):
```bash
mkswap /dev/sda3
swapon /dev/sda3
```

### 4. Mount Filesystems
```bash
mount /dev/sda2 /mnt
mkdir /mnt/boot
mount /dev/sda1 /mnt/boot
```

---

## Base System Installation

### 1. Update Package Database
```bash
pacman -Sy
```

### 2. Install Base System

```bash
  pacstrap /mnt base linux linux-firmware \
    base-devel \
    networkmanager \
    wireless_tools \
    wpa_supplicant \
    sudo \
    git \
    reflector \
    grub \
    efibootmgr \
    neovim \
    zsh
```

### 3. Generate Filesystem Table
```bash
genfstab -U /mnt >> /mnt/etc/fstab
```

**Verify the fstab**:
```bash
cat /mnt/etc/fstab
```

### 4. Change Root into New System
```bash
arch-chroot /mnt
```

---

## System Configuration

### 1. Set Time Zone
```bash
ln -sf /usr/share/zoneinfo/Europe/Berlin /etc/localtime  # Adjust for your timezone
hwclock --systohc
```

### 2. Configure Localization

#### Edit locale.gen:
```bash
nano /etc/locale.gen
```
**Uncomment**:
```
en_US.UTF-8 UTF-8
de_DE.UTF-8 UTF-8
```

#### Generate locales:
```bash
locale-gen
```

#### Set system locale: /etc/locale.conf
```bash
  LANG=en_US.UTF-8
  LC_NUMERIC=de_DE.UTF-8
  LC_TIME=de_DE.UTF-8
  LC_MONETARY=de_DE.UTF-8
  LC_MEASUREMENT=de_DE.UTF-8  # Metric system

```

### 3. Set Hostname
```bash
echo "yourhostname" > /etc/hostname
```

### 4. Configure Hosts File
```bash
nano /etc/hosts
```

**Add the following**:
```
127.0.0.1    localhost
::1          localhost
127.0.1.1    yourhostname.localdomain    yourhostname
```

### 5. Set Root Password
```bash
passwd
```

### 6. Configure Network
```bash
systemctl enable NetworkManager
```

---

## Bootloader Installation

### For UEFI Systems (GRUB):

#### 1. Install GRUB and EFI tools:
```bash
pacman -S grub efibootmgr
```

#### 2. Install GRUB to EFI:
```bash
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
```

#### 3. Generate GRUB config:
```bash
grub-mkconfig -o /boot/grub/grub.cfg
```

### For BIOS Systems:
```bash
pacman -S grub
grub-install --target=i386-pc /dev/sda  # Install to disk, not partition
grub-mkconfig -o /boot/grub/grub.cfg
```

---

## User Setup

### 1. Create User Account
```bash
useradd -m -g users -G wheel,storage,power -s /bin/bash yourusername
```

### 2. Set User Password
```bash
passwd yourusername
```

### 3. Configure Sudo
```bash
EDITOR=nano visudo
```
**Uncomment**: `%wheel ALL=(ALL) ALL`

---

## Essential Package Installation

### 1. Install AUR Helper (yay)
```bash
# Switch to user account first
su - yourusername
cd /tmp
git clone https://aur.archlinux.org/paru.git
cd paru && makepkg -si
```

### 2. Install Essential Applications
```bash
paru -S hyprland-meta-git \
  kitty \
  ghostty-git \
  firefox \
  github-cli \
  cpio \ # for creating cpio archives
  uwsm # wayland session manager
```

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
```

---

## Post-Installation

### 1. Exit chroot and reboot
```bash
exit          # Exit chroot
umount -R /mnt
reboot
```

### 2. First Boot Setup
```bash
# Enable and start NetworkManager
sudo systemctl enable --now NetworkManager

# Connect to WiFi (if needed)
nmcli device wifi list
nmcli device wifi connect "SSID" password "password"

# Update system
sudo pacman -Syu
```

### 3. Configure Zsh (if installed)
```bash
chsh -s /bin/zsh  # Change default shell
# Install oh-my-zsh (optional)
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

### 4. Enable Services
```bash
# Enable common services
sudo systemctl enable NetworkManager
sudo systemctl enable bluetooth  # If you have Bluetooth hardware

# Start user services
systemctl --user enable pulseaudio
```

---

## Troubleshooting

### Boot Issues

#### GRUB not found:
```bash
# Boot from live USB, mount system, and chroot
mount /dev/sda2 /mnt
mount /dev/sda1 /mnt/boot
arch-chroot /mnt
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg
```

#### Network not working:
```bash
# Check network interfaces
ip link show

# Start NetworkManager
sudo systemctl start NetworkManager
sudo systemctl enable NetworkManager
```

### Package Issues

#### Keys and signatures:
```bash
sudo pacman-key --init
sudo pacman-key --populate archlinux
sudo pacman -Sy archlinux-keyring
```

#### Mirror issues:
```bash
sudo reflector --verbose --latest 10 --country 'United States' --age 12 --protocol https --sort rate --save /etc/pacman.d/mirrorlist
```

### Common Commands Reference

```bash
# System information
uname -a                    # Kernel info
lscpu                      # CPU info
lsblk                      # Block devices
df -h                      # Disk usage
free -h                    # Memory usage

# Package management
pacman -S package_name     # Install package
pacman -R package_name     # Remove package
pacman -Rs package_name    # Remove package and dependencies
pacman -Syu               # Update system
pacman -Ss search_term    # Search packages
pacman -Q                 # List installed packages

# Service management
systemctl status service   # Check service status
systemctl start service   # Start service
systemctl enable service  # Enable service at boot
systemctl disable service # Disable service
journalctl -u service     # View service logs
```

---

## Next Steps

After completing this installation:

1. **Apply dotfiles**: Use the scripts in this repository to configure your desktop environment
2. **Install development tools**: Set up your programming environment
3. **Configure backups**: Set up automated backups of your configuration
4. **Security hardening**: Configure firewall, fail2ban, etc.
5. **Performance tuning**: Optimize for your specific hardware

## Additional Resources

- [Arch Linux Wiki](https://wiki.archlinux.org/)
- [Arch Linux Installation Guide](https://wiki.archlinux.org/title/Installation_guide)
- [Post-installation recommendations](https://wiki.archlinux.org/title/General_recommendations)
- [List of applications](https://wiki.archlinux.org/title/List_of_applications)

---

**Note**: This guide assumes UEFI systems with GPT partitioning. For BIOS/MBR systems, adjust partitioning and bootloader commands accordingly.