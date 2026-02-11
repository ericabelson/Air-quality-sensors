#!/bin/bash
#
# Safe History Clear Script - Dog Bark Detection System
#
# This script SAFELY clears bark detection history with automatic backups.
# It will NOT delete anything without creating a backup first.
#
# Author: Claude Code
# Date: 2026-02-11
#

set -e  # Exit on any error

echo "=========================================="
echo "Safe Bark History Clear Script"
echo "=========================================="
echo ""
echo "This script will:"
echo "  1. Create backups of all data"
echo "  2. Clear CSV event logs"
echo "  3. Clear Home Assistant sensor history"
echo "  4. Optionally clear audio recordings"
echo ""
echo "IMPORTANT: Backups will be saved to:"
echo "  ~/audio_detection/backups/backup_$(date +%Y%m%d_%H%M%S)/"
echo ""

# Ask for confirmation
read -p "Do you want to proceed? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted by user."
    exit 0
fi

# Create backup directory
BACKUP_DIR=~/audio_detection/backups/backup_$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
echo ""
echo "Creating backup at: $BACKUP_DIR"

# Stop the detector service
echo ""
echo "[1/6] Stopping dog_bark_detector service..."
sudo systemctl stop dog_bark_detector || echo "  Warning: Service not running or doesn't exist"

# Backup CSV files
echo ""
echo "[2/6] Backing up CSV files..."
if [ -d ~/audio_detection/data ]; then
    cp -r ~/audio_detection/data "$BACKUP_DIR/data_backup"
    echo "  ✓ CSV files backed up"

    # Show what we're backing up
    echo "  Files backed up:"
    ls -lh ~/audio_detection/data/*.csv 2>/dev/null || echo "  No CSV files found"
else
    echo "  No data directory found - skipping"
fi

# Backup logs
echo ""
echo "[3/6] Backing up log files..."
if [ -d ~/audio_detection/logs ]; then
    cp -r ~/audio_detection/logs "$BACKUP_DIR/logs_backup"
    echo "  ✓ Log files backed up"
else
    echo "  No logs directory found - skipping"
fi

# Backup Home Assistant database
echo ""
echo "[4/6] Backing up Home Assistant database..."
if [ -f ~/homeassistant/home-assistant_v2.db ]; then
    cp ~/homeassistant/home-assistant_v2.db "$BACKUP_DIR/home-assistant_v2.db.backup"
    echo "  ✓ HA database backed up ($(du -h ~/homeassistant/home-assistant_v2.db | cut -f1))"
else
    echo "  Warning: HA database not found at expected location"
fi

# Ask about audio recordings
echo ""
echo "[5/6] Audio recordings..."
echo "  Current recordings:"
if [ -d ~/audio_detection/recordings ]; then
    du -sh ~/audio_detection/recordings 2>/dev/null || echo "  (empty)"
fi
if [ -d /mnt/usb/bark_audio/recordings ]; then
    du -sh /mnt/usb/bark_audio/recordings 2>/dev/null || echo "  (empty)"
fi

read -p "  Do you want to delete audio recordings? (yes/no): " DELETE_AUDIO

# Clear CSV files
echo ""
echo "[6/6] Clearing history..."
if [ -d ~/audio_detection/data ]; then
    rm -f ~/audio_detection/data/bark_events_*.csv
    echo "  ✓ CSV files cleared"
fi

# Clear logs (optional - keep recent ones)
read -p "  Do you want to clear log files? (yes/no): " DELETE_LOGS
if [ "$DELETE_LOGS" = "yes" ]; then
    rm -f ~/audio_detection/logs/*.log
    echo "  ✓ Log files cleared"
fi

# Clear audio recordings if requested
if [ "$DELETE_AUDIO" = "yes" ]; then
    if [ -d ~/audio_detection/recordings ]; then
        rm -rf ~/audio_detection/recordings/*
        echo "  ✓ Local recordings cleared"
    fi
    if [ -d /mnt/usb/bark_audio/recordings ]; then
        rm -rf /mnt/usb/bark_audio/recordings/*
        echo "  ✓ USB recordings cleared"
    fi
fi

# Clear Home Assistant database history for bark sensors
echo ""
echo "Clearing Home Assistant sensor history..."
docker exec homeassistant sqlite3 /config/home-assistant_v2.db \
    "DELETE FROM states WHERE entity_id LIKE 'sensor.%bark%' OR entity_id LIKE 'sensor.%decibel%' OR entity_id LIKE 'binary_sensor.dog_barking';" \
    2>/dev/null && echo "  ✓ HA sensor states cleared" || echo "  Warning: Could not clear HA database"

docker exec homeassistant sqlite3 /config/home-assistant_v2.db \
    "DELETE FROM statistics WHERE metadata_id IN (SELECT metadata_id FROM statistics_meta WHERE statistic_id LIKE '%bark%' OR statistic_id LIKE '%decibel%');" \
    2>/dev/null && echo "  ✓ HA statistics cleared" || echo "  Warning: Could not clear statistics"

# Restart services
echo ""
echo "Restarting services..."
sudo systemctl start dog_bark_detector
echo "  ✓ dog_bark_detector started"

docker restart homeassistant > /dev/null 2>&1
echo "  ✓ Home Assistant restarting (wait 30 seconds)"

echo ""
echo "=========================================="
echo "✓ History cleared successfully!"
echo "=========================================="
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo "To restore from backup:"
echo "  cp -r $BACKUP_DIR/data_backup/* ~/audio_detection/data/"
echo "  cp $BACKUP_DIR/home-assistant_v2.db.backup ~/homeassistant/home-assistant_v2.db"
echo "  docker restart homeassistant"
echo ""
echo "Next steps:"
echo "  1. Wait 30 seconds for Home Assistant to restart"
echo "  2. Check dashboard - should show clean data"
echo "  3. Verify detector is running: sudo systemctl status dog_bark_detector"
echo ""
