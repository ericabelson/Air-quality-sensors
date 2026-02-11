# How to Backup Your Raspberry Pi Configuration

This guide helps you create a complete backup of your Pi's important configuration files **without pushing sensitive data to GitHub**.

---

## What Gets Backed Up

✅ **Included:**
- Home Assistant configuration (dashboards, automations, packages, secrets)
- Audio detection scripts and configurations
- BirdNET-Pi configuration files
- Systemd service files (all audio/bird/dog related services)
- ALSA audio configuration
- Network configuration
- Cron jobs
- System information

❌ **Excluded (to keep backup small):**
- Audio recordings (.wav, .mp3 files)
- Large databases (.db files)
- Git repositories (.git folders)
- Python virtual environments (venv folders)
- Home Assistant internal storage

**Typical backup size:** 5-50 MB (depending on your config)

---

## Quick Start (Copy-Paste Method)

### Step 1: Create Backup on Pi (via SSH)

Copy-paste this **entire command** into your PowerShell window where you're SSHed into the Pi:

```bash
BACKUP_DATE=$(date +%Y%m%d_%H%M%S) && BACKUP_NAME="pi_config_backup_${BACKUP_DATE}" && BACKUP_DIR="/tmp/${BACKUP_NAME}" && BACKUP_FILE="/tmp/${BACKUP_NAME}.tar.gz" && mkdir -p "$BACKUP_DIR" && echo "[1/10] Home Assistant..." && rsync -av --exclude='*.db*' --exclude='*.log' --exclude='deps/' --exclude='tts/' --exclude='.storage/' --exclude='backups/' ~/homeassistant/ "$BACKUP_DIR/homeassistant/" 2>/dev/null && echo "[2/10] Audio detection..." && rsync -av --exclude='recordings/' --exclude='models/' --exclude='*.wav' --exclude='*.mp3' --exclude='venv/' ~/audio_detection/ "$BACKUP_DIR/audio_detection/" 2>/dev/null && echo "[3/10] Air-quality-sensors..." && rsync -av --exclude='.git/' --exclude='__pycache__/' ~/Air-quality-sensors/ "$BACKUP_DIR/Air-quality-sensors/" 2>/dev/null && echo "[4/10] BirdNET-Pi..." && rsync -av --exclude='.git/' --exclude='BirdSongs/' --exclude='*.wav' --exclude='*.db' ~/BirdNET-Pi/ "$BACKUP_DIR/BirdNET-Pi/" 2>/dev/null && echo "[5/10] Systemd services..." && mkdir -p "$BACKUP_DIR/systemd" && sudo cp /etc/systemd/system/*{audio,bird,dog,bark,iphone}*.service "$BACKUP_DIR/systemd/" 2>/dev/null && sudo chown -R $(whoami):$(whoami) "$BACKUP_DIR/systemd/" && echo "[6/10] ALSA config..." && mkdir -p "$BACKUP_DIR/alsa" && cp ~/.asoundrc "$BACKUP_DIR/alsa/" 2>/dev/null && sudo cp /etc/asound.conf "$BACKUP_DIR/alsa/" 2>/dev/null && echo "[7/10] Cron jobs..." && mkdir -p "$BACKUP_DIR/cron" && crontab -l > "$BACKUP_DIR/cron/user_crontab.txt" 2>/dev/null && echo "[8/10] Network config..." && mkdir -p "$BACKUP_DIR/network" && sudo cp /etc/dhcpcd.conf "$BACKUP_DIR/network/" 2>/dev/null && echo "[9/10] System info..." && echo "Backup Date: $(date)" > "$BACKUP_DIR/SYSTEM_INFO.txt" && echo "Hostname: $(hostname)" >> "$BACKUP_DIR/SYSTEM_INFO.txt" && df -h >> "$BACKUP_DIR/SYSTEM_INFO.txt" && arecord -l >> "$BACKUP_DIR/SYSTEM_INFO.txt" 2>&1 && echo "[10/10] Creating archive..." && cd /tmp && tar -czf "$BACKUP_FILE" "$BACKUP_NAME/" && rm -rf "$BACKUP_DIR" && echo "" && echo "✓ BACKUP COMPLETE: $BACKUP_FILE ($(du -h $BACKUP_FILE | cut -f1))" && echo "" && echo "Next: Run PowerShell command on your LOCAL machine to download it"
```

This will take about 10-30 seconds and create a file like: `/tmp/pi_config_backup_20260211_143025.tar.gz`

---

### Step 2: Download Backup to Your PC (from PowerShell)

**Exit your SSH session first** (type `exit`), then run this on your **local PowerShell**:

```powershell
$PI_USER = "demeter"; $PI_IP = "192.168.68.109"; $DOWNLOAD_PATH = "$env:USERPROFILE\Downloads"; Write-Host "Finding backup..." -ForegroundColor Yellow; $backupFile = ssh ${PI_USER}@${PI_IP} "ls -t /tmp/pi_config_backup_*.tar.gz 2>/dev/null | head -1"; $backupFileName = Split-Path $backupFile -Leaf; Write-Host "Downloading: $backupFileName" -ForegroundColor Green; scp "${PI_USER}@${PI_IP}:${backupFile}" "$DOWNLOAD_PATH\$backupFileName"; Write-Host "✓ Download complete!" -ForegroundColor Green; Write-Host "Location: $DOWNLOAD_PATH\$backupFileName" -ForegroundColor Cyan
```

The backup will be downloaded to your **Downloads folder**.

---

### Step 3: Extract the Backup (on Windows)

1. **Install 7-Zip** (if not already installed):
   - Download: https://www.7-zip.org/
   - Install it

2. **Extract the backup:**
   - Go to your Downloads folder
   - Right-click the `pi_config_backup_XXXXXXXX.tar.gz` file
   - 7-Zip → Extract Here (may need to extract twice: .tar.gz → .tar → folder)

3. **Browse the files:**
   - You'll see folders like `homeassistant/`, `audio_detection/`, etc.
   - All your sensitive config files are there!

---

## Alternative: Using the Scripts

If you prefer running the full scripts instead of one-liners:

### Method A: Run Script on Pi

```bash
# On Pi (via SSH)
cd ~/Air-quality-sensors/diagnostics
chmod +x create_backup.sh
./create_backup.sh
```

### Method B: Download via PowerShell Script

```powershell
# On Local PC (in PowerShell)
cd C:\Users\YourUsername\Downloads
# (Copy download_backup.ps1 to this location first)
.\download_backup.ps1
```

---

## What You Can Do With This Backup

### 1. Store It Privately
- Put it in Google Drive, OneDrive, Dropbox (private folder)
- Keep it on an external hard drive
- Store it in a password-protected archive

### 2. Share Config with Claude (Safely)
- Extract the backup
- Copy specific YAML files you want help with
- Paste them into Claude Code **without** sensitive device names
- Or manually redact sensitive information before sharing

### 3. Restore Configuration
If you ever need to rebuild your Pi:
- Extract the backup
- Copy files back to their original locations
- Reinstall services using the backed-up service files

### 4. Version Control
- Keep multiple backups with dates
- Compare old vs new configurations
- Track changes over time

---

## Cleaning Up

### Delete Backup from Pi (after downloading)

```bash
# On Pi
rm /tmp/pi_config_backup_*.tar.gz
```

### Automate Weekly Backups

Add to crontab on Pi:

```bash
crontab -e

# Add this line (runs every Sunday at 2am)
0 2 * * 0 /home/demeter/Air-quality-sensors/diagnostics/create_backup.sh
```

---

## Troubleshooting

### "Permission denied" errors
- Run the backup script with your normal user (not root)
- The script uses `sudo` only when needed

### "rsync: command not found"
```bash
sudo apt-get install rsync
```

### "scp: command not found" (on Windows)
- Install OpenSSH on Windows: Settings → Apps → Optional Features → OpenSSH Client
- Or use WinSCP (GUI tool): https://winscp.net/

### Backup is too large
- Check if audio recordings are being included
- Use `du -sh /tmp/pi_config_backup_*` to see size before compression

---

## Security Notes

✅ **This backup stays local** - nothing gets pushed to GitHub

✅ **Your secrets.yaml file is included** - store the backup securely

✅ **Network passwords are included** - keep it encrypted/private

⚠️ **Backup is in /tmp/** - it will be auto-deleted after 24-48 hours (by system cleanup)

⚠️ **Download it soon** - don't wait days to download from /tmp/

---

## Summary

**On Pi (via SSH):**
```bash
# Long one-liner that creates backup (see Step 1 above)
```

**On Local PC (PowerShell):**
```powershell
# One-liner that downloads backup (see Step 2 above)
```

**Result:**
- Backup file in your Downloads folder
- All important configs safely stored locally
- No sensitive data pushed to GitHub
- Ready to extract and browse

---

## Questions?

- The backup only includes configuration files, not recordings or databases
- Typical backup is 5-50 MB
- Takes 10-30 seconds to create
- Takes 5-10 seconds to download (depending on network speed)
- Safe to run multiple times (each backup is timestamped)
