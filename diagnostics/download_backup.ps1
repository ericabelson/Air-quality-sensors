# ============================================================================
# PowerShell Script - Run this ON YOUR LOCAL WINDOWS MACHINE
# Downloads the backup from your Raspberry Pi to your local machine
# ============================================================================

# Configuration - UPDATE THESE VALUES
$PI_USER = "demeter"
$PI_IP = "192.168.68.109"
$DOWNLOAD_PATH = "$env:USERPROFILE\Downloads"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "RASPBERRY PI BACKUP DOWNLOAD" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if SSH is available
Write-Host "[1/4] Checking SSH availability..." -ForegroundColor Yellow
try {
    $sshTest = ssh -V 2>&1
    Write-Host "   ✓ SSH is available" -ForegroundColor Green
} catch {
    Write-Host "   ✗ SSH not found. Install OpenSSH or use PuTTY's pscp.exe" -ForegroundColor Red
    exit 1
}

# Find the most recent backup file on the Pi
Write-Host "[2/4] Finding backup file on Pi..." -ForegroundColor Yellow
$backupFile = ssh ${PI_USER}@${PI_IP} "ls -t /tmp/pi_config_backup_*.tar.gz 2>/dev/null | head -1"

if ([string]::IsNullOrEmpty($backupFile)) {
    Write-Host "   ✗ No backup file found on Pi!" -ForegroundColor Red
    Write-Host "   Please run the backup script on the Pi first." -ForegroundColor Red
    exit 1
}

$backupFileName = Split-Path $backupFile -Leaf
Write-Host "   ✓ Found backup: $backupFileName" -ForegroundColor Green

# Get backup file size
$backupSize = ssh ${PI_USER}@${PI_IP} "du -h $backupFile | cut -f1"
Write-Host "   ✓ Backup size: $backupSize" -ForegroundColor Green

# Download the backup
Write-Host "[3/4] Downloading backup to: $DOWNLOAD_PATH" -ForegroundColor Yellow
$localPath = Join-Path $DOWNLOAD_PATH $backupFileName

try {
    scp "${PI_USER}@${PI_IP}:${backupFile}" "$localPath"
    Write-Host "   ✓ Download complete!" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Download failed: $_" -ForegroundColor Red
    exit 1
}

# Verify download
Write-Host "[4/4] Verifying download..." -ForegroundColor Yellow
if (Test-Path $localPath) {
    $localSize = (Get-Item $localPath).Length
    $localSizeMB = [math]::Round($localSize / 1MB, 2)
    Write-Host "   ✓ File downloaded successfully: $localSizeMB MB" -ForegroundColor Green
} else {
    Write-Host "   ✗ File not found after download!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "DOWNLOAD COMPLETE!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backup location: $localPath" -ForegroundColor White
Write-Host ""
Write-Host "What's included in this backup:" -ForegroundColor Yellow
Write-Host "  • Home Assistant configuration (dashboards, automations, packages)" -ForegroundColor White
Write-Host "  • Audio detection scripts" -ForegroundColor White
Write-Host "  • BirdNET-Pi configuration" -ForegroundColor White
Write-Host "  • Systemd service files" -ForegroundColor White
Write-Host "  • ALSA audio configuration" -ForegroundColor White
Write-Host "  • Network configuration" -ForegroundColor White
Write-Host "  • Cron jobs" -ForegroundColor White
Write-Host "  • System information" -ForegroundColor White
Write-Host ""
Write-Host "EXCLUDED (to save space):" -ForegroundColor Yellow
Write-Host "  • Audio recordings (.wav, .mp3)" -ForegroundColor White
Write-Host "  • Large databases (.db files)" -ForegroundColor White
Write-Host "  • Git repositories" -ForegroundColor White
Write-Host "  • Python virtual environments" -ForegroundColor White
Write-Host ""
Write-Host "To extract the backup:" -ForegroundColor Yellow
Write-Host "  1. Install 7-Zip (https://www.7-zip.org/)" -ForegroundColor White
Write-Host "  2. Right-click the .tar.gz file" -ForegroundColor White
Write-Host "  3. Extract to a folder" -ForegroundColor White
Write-Host ""
Write-Host "Optional - Delete backup from Pi:" -ForegroundColor Yellow
Write-Host "  ssh ${PI_USER}@${PI_IP} 'rm $backupFile'" -ForegroundColor Gray
Write-Host ""
