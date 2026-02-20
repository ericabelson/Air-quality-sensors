#!/bin/bash
#
# DETECTOR STARTUP SCRIPT
# =======================
# Starts the dog bark detector and bird detector
# (Audio system must be running first!)
#
# Usage: ./START_DETECTORS.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/var/log/air-quality"

# Fix log directory permissions if running as non-root
if [ ! -w "${LOG_DIR}" ]; then
    sudo chmod 777 "${LOG_DIR}" 2>/dev/null || mkdir -p "${LOG_DIR}"
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STARTING DETECTORS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if audio system is running
echo -e "${YELLOW}Checking audio system...${NC}"
if ! pgrep -f "ffmpeg.*192.168" > /dev/null; then
    echo -e "${RED}✗ FFmpeg is not running!${NC}"
    echo "Please start the audio system first:"
    echo "  sudo ./START_AUDIO_SYSTEM.sh"
    exit 1
fi
echo -e "${GREEN}✓ Audio system is running${NC}"
echo ""

# Check MQTT broker
echo -e "${YELLOW}Checking MQTT broker...${NC}"
if ! netstat -tuln 2>/dev/null | grep -q ":1883 "; then
    echo -e "${YELLOW}⚠ MQTT broker not running on localhost:1883${NC}"
    echo "  (Make sure Home Assistant is running)"
fi
echo ""

# Start dog bark detector
echo -e "${BLUE}Starting dog bark detector...${NC}"
cd "${SCRIPT_DIR}"
python3 dog_bark_detector.py > "${LOG_DIR}/dog_bark_detector.log" 2>&1 &
DOG_PID=$!
sleep 2

if kill -0 ${DOG_PID} 2>/dev/null; then
    echo -e "${GREEN}✓ Dog bark detector started (PID: ${DOG_PID})${NC}"
else
    echo -e "${RED}✗ Dog bark detector failed${NC}"
    cat "${LOG_DIR}/dog_bark_detector.log"
    exit 1
fi
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ DETECTORS RUNNING${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Process IDs:${NC}"
echo "  Dog bark detector: ${DOG_PID}"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo "  ${LOG_DIR}/dog_bark_detector.log"
echo ""
echo -e "${YELLOW}To stop detectors:${NC}"
echo "  kill ${DOG_PID}"
echo ""
