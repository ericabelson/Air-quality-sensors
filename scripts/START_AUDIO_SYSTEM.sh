#!/bin/bash
#
# MASTER AUDIO SYSTEM STARTUP SCRIPT
# ==================================
# This script sets up and starts the complete audio pipeline:
# 1. iPhone Periscope HD stream (RTSP) -> FFmpeg capture
# 2. FFmpeg output -> ALSA loopback device
# 3. PulseAudio reads ALSA loopback
# 4. Dog bark detector reads from PulseAudio
# 5. Bird detector (BirdNET) reads from PulseAudio
#
# Usage: sudo ./START_AUDIO_SYSTEM.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IPHONE_IP="${1:-192.168.68.106}"
RTSP_URL="rtsp://${IPHONE_IP}:8554/live.sdp"
SAMPLE_RATE=16000
CHANNELS=1
LOOPBACK_DEVICE="hw:Loopback,0"

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/var/log/air-quality"
FFMPEG_LOG="${LOG_DIR}/ffmpeg.log"
DETECTOR_LOG="${LOG_DIR}/detector.log"
STATUS_FILE="/tmp/audio_system_status.txt"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}AUDIO SYSTEM STARTUP${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}iPhone IP: ${IPHONE_IP}${NC}"
echo -e "${YELLOW}RTSP URL: ${RTSP_URL}${NC}"
echo ""

# Create log directory
mkdir -p "${LOG_DIR}"
chmod 755 "${LOG_DIR}"

# Step 1: Install required packages
echo -e "${BLUE}[1/6]${NC} Installing dependencies..."
apt-get update -qq
apt-get install -y -qq ffmpeg pulseaudio alsa-base alsa-utils 2>&1 | grep -i "setting up" || true
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 2: Load ALSA loopback module
echo -e "${BLUE}[2/6]${NC} Setting up ALSA loopback device..."
if ! lsmod | grep -q snd_aloop; then
    modprobe snd_aloop
    sleep 1
    echo -e "${GREEN}✓ ALSA loopback module loaded${NC}"
else
    echo -e "${GREEN}✓ ALSA loopback module already loaded${NC}"
fi
echo ""

# Step 3: Verify loopback device exists
echo -e "${BLUE}[3/6]${NC} Verifying loopback device..."
if arecord -l 2>/dev/null | grep -q "Loopback"; then
    echo -e "${GREEN}✓ Loopback device found${NC}"
else
    echo -e "${RED}✗ Loopback device NOT found${NC}"
    exit 1
fi
echo ""

# Step 4: Start PulseAudio (required for PyAudio to work)
echo -e "${BLUE}[4/6]${NC} Starting PulseAudio..."
if ! pgrep -x "pulseaudio" > /dev/null; then
    pulseaudio --daemonize --log-target=syslog
    sleep 2
    echo -e "${GREEN}✓ PulseAudio started${NC}"
else
    echo -e "${GREEN}✓ PulseAudio already running${NC}"
fi
echo ""

# Step 5: Start FFmpeg capturing iPhone audio
echo -e "${BLUE}[5/6]${NC} Starting FFmpeg (capturing iPhone stream)..."
# Kill any existing FFmpeg process
pkill -f "ffmpeg.*${IPHONE_IP}" 2>/dev/null || true
sleep 1

# Start FFmpeg in background
# - Input: RTSP stream from iPhone
# - Output: 16-bit PCM, 16kHz mono, written to ALSA loopback device
nohup ffmpeg \
    -rtsp_transport tcp \
    -i "${RTSP_URL}" \
    -f s16le \
    -acodec pcm_s16le \
    -ar ${SAMPLE_RATE} \
    -ac ${CHANNELS} \
    -v warning \
    "${LOOPBACK_DEVICE}" \
    > "${FFMPEG_LOG}" 2>&1 &

FFMPEG_PID=$!
sleep 3

# Verify FFmpeg started
if kill -0 ${FFMPEG_PID} 2>/dev/null; then
    echo -e "${GREEN}✓ FFmpeg started (PID: ${FFMPEG_PID})${NC}"
else
    echo -e "${RED}✗ FFmpeg failed to start${NC}"
    echo "Check: ${FFMPEG_LOG}"
    exit 1
fi
echo ""

# Step 6: Generate status report
echo -e "${BLUE}[6/6]${NC} Generating status report..."
cat > "${STATUS_FILE}" <<EOF
═══════════════════════════════════════════════════════════
AUDIO SYSTEM STATUS
═══════════════════════════════════════════════════════════
Timestamp: $(date)
iPhone IP: ${IPHONE_IP}
RTSP URL: ${RTSP_URL}

RUNNING PROCESSES:
$(ps aux | grep -E "ffmpeg|pulseaudio" | grep -v grep || echo "None found")

AUDIO DEVICES:
$(arecord -l 2>/dev/null || echo "No recording devices")

ALSA LOOPBACK STATUS:
$(if lsmod | grep -q snd_aloop; then echo "LOADED"; else echo "NOT LOADED"; fi)

LOG FILES:
- FFmpeg:  ${FFMPEG_LOG}
- Detector: ${DETECTOR_LOG}

NEXT STEPS:
1. Verify iPhone is streaming: curl -v rtsp://${IPHONE_IP}:8554/live.sdp
2. Start dog bark detector:   cd ${SCRIPT_DIR} && python3 dog_bark_detector.py
3. Start bird detector:       cd ${SCRIPT_DIR} && python3 -m birdnet_pi

═══════════════════════════════════════════════════════════
EOF

cat "${STATUS_FILE}"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ AUDIO SYSTEM READY${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}To start detectors, run:${NC}"
echo "  cd ${SCRIPT_DIR}"
echo "  python3 dog_bark_detector.py"
echo ""
echo -e "${YELLOW}Status saved to: ${STATUS_FILE}${NC}"
echo -e "${YELLOW}FFmpeg log:      ${FFMPEG_LOG}${NC}"
echo ""
