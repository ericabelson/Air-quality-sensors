#!/bin/bash
###############################################################################
# Fix iPhone Audio Stream Service IP Address
# ==========================================
# Updates the iphone-audio-stream service with the correct iPhone IP
#
# Usage:
#   ./fix_iphone_audio_ip.sh <correct-iPhone-IP>
#
# Example:
#   ./fix_iphone_audio_ip.sh 192.168.68.106
#
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CORRECT_IP="${1}"

if [ -z "$CORRECT_IP" ]; then
    echo -e "${RED}Error: iPhone IP address required${NC}"
    echo ""
    echo "Usage: $0 <correct-iPhone-IP>"
    echo ""
    echo "Example:"
    echo "  $0 192.168.68.106"
    exit 1
fi

CORRECT_URL="rtsp://${CORRECT_IP}:8554/live.sdp"

echo -e "${GREEN}=== Fixing iPhone Audio Stream IP ===${NC}"
echo "Correct IP:  ${CORRECT_IP}"
echo "Correct URL: ${CORRECT_URL}"
echo ""

# Check if service exists
if ! systemctl is-active --quiet iphone-audio-stream; then
    echo -e "${YELLOW}⚠ Service is not running. Checking if it exists...${NC}"
fi

# Read current service file
CURRENT_SERVICE="/etc/systemd/system/iphone-audio-stream.service"
if [ ! -f "$CURRENT_SERVICE" ]; then
    echo -e "${RED}Error: Service file not found at $CURRENT_SERVICE${NC}"
    exit 1
fi

# Extract current IP from service file
CURRENT_URL=$(grep -oP 'rtsp://[0-9.]+:[0-9]+/[^\s]+' "$CURRENT_SERVICE" | head -1)
CURRENT_IP=$(echo "$CURRENT_URL" | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1)

echo "Current IP in service: ${CURRENT_IP}"
echo ""

if [ "$CURRENT_IP" = "$CORRECT_IP" ]; then
    echo -e "${GREEN}✓ Service already uses correct IP!${NC}"
    exit 0
fi

echo -e "${YELLOW}Updating service from ${CURRENT_IP} to ${CORRECT_IP}...${NC}"

# Update the service file
sudo sed -i "s|rtsp://.*:8554/live.sdp|${CORRECT_URL}|g" "$CURRENT_SERVICE"

# Reload systemd and restart service
echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Restarting service..."
sudo systemctl restart iphone-audio-stream

# Wait for service to start
sleep 3

STATUS=$(systemctl is-active iphone-audio-stream 2>/dev/null || true)
if [ "$STATUS" = "active" ]; then
    echo -e "${GREEN}✓ Service restarted successfully!${NC}"
    echo ""
    echo "Checking service status..."
    sudo systemctl status iphone-audio-stream | head -10
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo "Check logs with: sudo journalctl -u iphone-audio-stream -n 20"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Fix Complete ===${NC}"
echo ""
echo "Audio should now be flowing from your iPhone."
echo "Watch the service logs:"
echo "  sudo journalctl -u iphone-audio-stream -f"
echo ""
