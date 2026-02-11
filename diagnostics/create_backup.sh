#!/bin/bash
###############################################################################
# Backup Script - Run this ON THE PI via SSH
# Creates a compressed backup of all important configuration files
# EXCLUDES: audio recordings, large databases, git repos
###############################################################################

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="pi_config_backup_${BACKUP_DATE}"
BACKUP_DIR="/tmp/${BACKUP_NAME}"
BACKUP_FILE="/tmp/${BACKUP_NAME}.tar.gz"

echo "==============================================================================="
echo "CREATING BACKUP: ${BACKUP_NAME}"
echo "==============================================================================="
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "[1/10] Backing up Home Assistant configuration..."
if [ -d ~/homeassistant ]; then
    mkdir -p "$BACKUP_DIR/homeassistant"
    # Copy HA config, exclude large files and databases
    rsync -av --exclude='*.db' --exclude='*.db-shm' --exclude='*.db-wal' \
        --exclude='*.log' --exclude='deps/' --exclude='tts/' \
        --exclude='.storage/' --exclude='backups/' \
        ~/homeassistant/ "$BACKUP_DIR/homeassistant/" 2>/dev/null
    echo "   ✓ Home Assistant config backed up"
else
    echo "   ⚠ Home Assistant directory not found"
fi

echo "[2/10] Backing up audio detection scripts..."
if [ -d ~/audio_detection ]; then
    mkdir -p "$BACKUP_DIR/audio_detection"
    # Exclude recordings, models, and large files
    rsync -av --exclude='recordings/' --exclude='models/' --exclude='*.wav' \
        --exclude='*.mp3' --exclude='venv/' --exclude='__pycache__/' \
        ~/audio_detection/ "$BACKUP_DIR/audio_detection/" 2>/dev/null
    echo "   ✓ Audio detection scripts backed up"
else
    echo "   ⚠ Audio detection directory not found"
fi

echo "[3/10] Backing up Air-quality-sensors repo (config only)..."
if [ -d ~/Air-quality-sensors ]; then
    mkdir -p "$BACKUP_DIR/Air-quality-sensors"
    # Copy repo but exclude .git directory
    rsync -av --exclude='.git/' --exclude='*.pyc' --exclude='__pycache__/' \
        ~/Air-quality-sensors/ "$BACKUP_DIR/Air-quality-sensors/" 2>/dev/null
    echo "   ✓ Air-quality-sensors backed up"
else
    echo "   ⚠ Air-quality-sensors directory not found"
fi

echo "[4/10] Backing up BirdNET-Pi configuration..."
if [ -d ~/BirdNET-Pi ]; then
    mkdir -p "$BACKUP_DIR/BirdNET-Pi"
    # Copy BirdNET config, exclude git and large files
    rsync -av --exclude='.git/' --exclude='BirdSongs/' --exclude='*.wav' \
        --exclude='*.db' --exclude='Extracted/' \
        ~/BirdNET-Pi/ "$BACKUP_DIR/BirdNET-Pi/" 2>/dev/null
    echo "   ✓ BirdNET-Pi config backed up"
else
    echo "   ⚠ BirdNET-Pi directory not found"
fi

echo "[5/10] Backing up systemd service files..."
mkdir -p "$BACKUP_DIR/systemd"
sudo cp /etc/systemd/system/*audio*.service "$BACKUP_DIR/systemd/" 2>/dev/null
sudo cp /etc/systemd/system/*bird*.service "$BACKUP_DIR/systemd/" 2>/dev/null
sudo cp /etc/systemd/system/*dog*.service "$BACKUP_DIR/systemd/" 2>/dev/null
sudo cp /etc/systemd/system/*bark*.service "$BACKUP_DIR/systemd/" 2>/dev/null
sudo cp /etc/systemd/system/*iphone*.service "$BACKUP_DIR/systemd/" 2>/dev/null
sudo chown -R $(whoami):$(whoami) "$BACKUP_DIR/systemd/" 2>/dev/null
echo "   ✓ Systemd services backed up"

echo "[6/10] Backing up ALSA configuration..."
mkdir -p "$BACKUP_DIR/alsa"
cp ~/.asoundrc "$BACKUP_DIR/alsa/" 2>/dev/null
sudo cp /etc/asound.conf "$BACKUP_DIR/alsa/" 2>/dev/null
sudo cp -r /etc/alsa/ "$BACKUP_DIR/alsa/etc_alsa/" 2>/dev/null
sudo chown -R $(whoami):$(whoami) "$BACKUP_DIR/alsa/" 2>/dev/null
echo "   ✓ ALSA config backed up"

echo "[7/10] Backing up cron jobs..."
mkdir -p "$BACKUP_DIR/cron"
crontab -l > "$BACKUP_DIR/cron/user_crontab.txt" 2>/dev/null
sudo crontab -l > "$BACKUP_DIR/cron/root_crontab.txt" 2>/dev/null
sudo chown -R $(whoami):$(whoami) "$BACKUP_DIR/cron/" 2>/dev/null
echo "   ✓ Cron jobs backed up"

echo "[8/10] Backing up network configuration..."
mkdir -p "$BACKUP_DIR/network"
sudo cp /etc/network/interfaces "$BACKUP_DIR/network/" 2>/dev/null
sudo cp /etc/wpa_supplicant/wpa_supplicant.conf "$BACKUP_DIR/network/" 2>/dev/null
sudo cp /etc/dhcpcd.conf "$BACKUP_DIR/network/" 2>/dev/null
sudo chown -R $(whoami):$(whoami) "$BACKUP_DIR/network/" 2>/dev/null
echo "   ✓ Network config backed up"

echo "[9/10] Creating system info file..."
cat > "$BACKUP_DIR/SYSTEM_INFO.txt" << EOF
Backup Date: $(date)
Hostname: $(hostname)
User: $(whoami)
OS: $(cat /etc/os-release | grep PRETTY_NAME)
Kernel: $(uname -r)
Python: $(python3 --version)
Disk Space:
$(df -h | grep -E "Filesystem|/$|/mnt")

Installed Services:
$(systemctl list-unit-files | grep -E "audio|bird|dog|bark|iphone")

Network Interfaces:
$(ip addr show)

Audio Devices:
$(arecord -l)
EOF
echo "   ✓ System info saved"

echo "[10/10] Creating compressed archive..."
cd /tmp
tar -czf "$BACKUP_FILE" "$BACKUP_NAME/" 2>/dev/null
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "   ✓ Archive created: $BACKUP_FILE ($BACKUP_SIZE)"

# Cleanup
rm -rf "$BACKUP_DIR"

echo ""
echo "==============================================================================="
echo "BACKUP COMPLETE!"
echo "==============================================================================="
echo ""
echo "Backup file location: $BACKUP_FILE"
echo "Backup file size: $BACKUP_SIZE"
echo ""
echo "NEXT STEP:"
echo "Run the PowerShell commands on your LOCAL machine to copy this file."
echo ""
echo "The backup file will be available at: $BACKUP_FILE"
echo "It will be deleted automatically after 24 hours (in /tmp)"
echo ""
echo "To copy it now, use this on your LOCAL PowerShell:"
echo "scp demeter@192.168.68.109:$BACKUP_FILE C:\\Users\\YourUsername\\Downloads\\"
echo ""
