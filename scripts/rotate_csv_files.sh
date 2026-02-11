#!/bin/bash
#
# CSV Rotation Script - Keep Only Last N Days of Data
#
# This script rotates CSV files to prevent them from growing forever.
# Default: Keep last 90 days (configurable)
#
# Usage:
#   ./rotate_csv_files.sh [days_to_keep]
#
# Example:
#   ./rotate_csv_files.sh 30    # Keep last 30 days
#   ./rotate_csv_files.sh 180   # Keep last 180 days
#
# Can be run via cron daily:
#   0 2 * * * /home/demeter/Air-quality-sensors/scripts/rotate_csv_files.sh
#

# Configuration
DAYS_TO_KEEP=${1:-90}  # Default 90 days if not specified
DATA_DIR=~/audio_detection/data
ARCHIVE_DIR=~/audio_detection/data/archive

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "CSV Rotation Script"
echo "Keeping last $DAYS_TO_KEEP days of data"
echo ""

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Process each CSV file
for CSV_FILE in "$DATA_DIR"/bark_events_*.csv; do
    if [ ! -f "$CSV_FILE" ]; then
        echo "No CSV files found"
        exit 0
    fi

    FILENAME=$(basename "$CSV_FILE")
    echo "Processing: $FILENAME"

    # Create temporary files
    TEMP_FILE=$(mktemp)
    ARCHIVE_FILE="$ARCHIVE_DIR/${FILENAME%.csv}_$(date +%Y%m%d).csv"

    # Get cutoff date (N days ago)
    CUTOFF_DATE=$(date -d "$DAYS_TO_KEEP days ago" +%Y-%m-%d)

    # Read header
    head -1 "$CSV_FILE" > "$TEMP_FILE"

    # Count total rows (excluding header)
    TOTAL_ROWS=$(tail -n +2 "$CSV_FILE" | wc -l)

    # Filter rows newer than cutoff date
    # CSV format: date,start_time,end_time,duration_minutes,max_decibels,num_barks
    tail -n +2 "$CSV_FILE" | awk -F',' -v cutoff="$CUTOFF_DATE" '$1 >= cutoff' >> "$TEMP_FILE"

    # Count kept rows
    KEPT_ROWS=$(tail -n +2 "$TEMP_FILE" | wc -l)
    REMOVED_ROWS=$((TOTAL_ROWS - KEPT_ROWS))

    if [ $REMOVED_ROWS -gt 0 ]; then
        # Archive old data before removing
        tail -n +2 "$CSV_FILE" | awk -F',' -v cutoff="$CUTOFF_DATE" '$1 < cutoff' > "$ARCHIVE_FILE.tmp"
        if [ -s "$ARCHIVE_FILE.tmp" ]; then
            # Add header to archive
            head -1 "$CSV_FILE" > "$ARCHIVE_FILE"
            cat "$ARCHIVE_FILE.tmp" >> "$ARCHIVE_FILE"
            rm "$ARCHIVE_FILE.tmp"
            echo -e "  ${YELLOW}Archived:${NC} $REMOVED_ROWS rows → $(basename $ARCHIVE_FILE)"
        else
            rm "$ARCHIVE_FILE.tmp"
        fi

        # Replace original with filtered data
        mv "$TEMP_FILE" "$CSV_FILE"
        echo -e "  ${GREEN}Kept:${NC} $KEPT_ROWS rows (last $DAYS_TO_KEEP days)"
    else
        rm "$TEMP_FILE"
        echo -e "  ${GREEN}No rotation needed${NC} (all $TOTAL_ROWS rows within $DAYS_TO_KEEP days)"
    fi

    echo ""
done

# Compress old archives (older than 1 year)
echo "Compressing old archives..."
find "$ARCHIVE_DIR" -name "*.csv" -type f -mtime +365 -exec gzip {} \; 2>/dev/null
COMPRESSED=$(find "$ARCHIVE_DIR" -name "*.csv.gz" -type f | wc -l)
if [ $COMPRESSED -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Compressed $COMPRESSED old archive(s)"
fi

# Show archive directory size
ARCHIVE_SIZE=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1)
echo ""
echo "Archive directory: $ARCHIVE_DIR"
echo "Total size: $ARCHIVE_SIZE"
echo ""
echo "✓ CSV rotation complete"
