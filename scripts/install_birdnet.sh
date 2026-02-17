#!/bin/bash
###############################################################################
# BirdNET Analyzer Installation Script
# =====================================
# Installs birdnetlib (pip-installable BirdNET-Analyzer wrapper) into the
# existing audio_detection virtualenv, downloads the model, creates the
# systemd service, and verifies everything works.
#
# Prerequisites (already installed for dog bark detector):
#   - Python 3.9+
#   - pyaudio, paho-mqtt, numpy
#   - PulseAudio with snd-aloop loopback
#   - Mosquitto MQTT broker
#
# Usage:
#   # Set your location first (required for regional species filtering):
#   export BIRDNET_LAT=37.7749
#   export BIRDNET_LON=-122.4194
#
#   ./install_birdnet.sh
#
# Author: Claude Code
# License: MIT
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths — match the dog bark detector's conventions
VENV_DIR="$HOME/audio_detection/venv"
AUDIO_DIR="$HOME/audio_detection"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIRDNET_SCRIPT="$SCRIPT_DIR/birdnet_analyzer.py"

print_header()  { echo -e "\n${BLUE}======== $1 ========${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_info()    { echo -e "${YELLOW}ℹ $1${NC}"; }

###############################################################################
# Pre-flight checks
###############################################################################

print_header "Pre-flight checks"

# Check Python version (birdnetlib needs 3.9+)
PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VER" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VER" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]; }; then
    print_error "Python 3.9+ required (found $PYTHON_VER)"
    exit 1
fi
print_success "Python $PYTHON_VER"

# Check that birdnet_analyzer.py exists
if [ ! -f "$BIRDNET_SCRIPT" ]; then
    print_error "birdnet_analyzer.py not found at $BIRDNET_SCRIPT"
    exit 1
fi
print_success "birdnet_analyzer.py found"

# Check/create venv
if [ ! -d "$VENV_DIR" ]; then
    print_info "Creating virtualenv at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi
print_success "Virtualenv at $VENV_DIR"

# Activate venv for the rest of the script
source "$VENV_DIR/bin/activate"

###############################################################################
# Install system dependencies
###############################################################################

print_header "System dependencies"

print_info "Installing system packages (if not present)..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    2>/dev/null

print_success "System dependencies installed"

###############################################################################
# Install Python packages
###############################################################################

print_header "Python packages"

print_info "Upgrading pip..."
pip install --upgrade pip -q

print_info "Installing TFLite runtime (needed by BirdNET model)..."
# Try lightweight tflite-runtime first; fall back to full tensorflow
if ! pip install tflite-runtime -q 2>/dev/null; then
    print_info "tflite-runtime not available for this Python version, installing tensorflow..."
    pip install tensorflow -q
fi

print_info "Installing birdnetlib (includes BirdNET-Analyzer)..."
pip install birdnetlib -q

print_info "Ensuring other audio dependencies are present..."
pip install pyaudio paho-mqtt numpy librosa -q

print_success "Python packages installed"

###############################################################################
# Download & verify BirdNET model
###############################################################################

print_header "BirdNET model"

print_info "Loading BirdNET model (downloads ~150 MB on first run)..."
python3 -c "
from birdnetlib.analyzer import Analyzer
a = Analyzer()
print('Model loaded successfully')
print(f'  Labels: {len(a.custom_species_list) if hasattr(a, \"custom_species_list\") else \"default\"} species')
"
print_success "BirdNET model ready"

###############################################################################
# Set up location
###############################################################################

print_header "Location configuration"

if [ -z "$BIRDNET_LAT" ] || [ -z "$BIRDNET_LON" ]; then
    print_info "BIRDNET_LAT and BIRDNET_LON are not set."
    print_info "BirdNET works without location but species filtering improves accuracy."
    echo ""
    read -p "Enter latitude  (e.g. 37.7749, or press Enter to skip): " USER_LAT
    read -p "Enter longitude (e.g. -122.4194, or press Enter to skip): " USER_LON

    if [ -n "$USER_LAT" ] && [ -n "$USER_LON" ]; then
        BIRDNET_LAT="$USER_LAT"
        BIRDNET_LON="$USER_LON"
    else
        BIRDNET_LAT="30.2672"
        BIRDNET_LON="-97.7431"
        print_info "Defaulting to Austin, TX (30.2672, -97.7431)"
    fi
else
    print_success "Location: $BIRDNET_LAT, $BIRDNET_LON"
fi

###############################################################################
# Create directories
###############################################################################

print_header "Directories"

mkdir -p "$AUDIO_DIR/logs"
mkdir -p "$AUDIO_DIR/data"
mkdir -p "$AUDIO_DIR/bird_recordings"

print_success "Directories created"

###############################################################################
# Create systemd service
###############################################################################

print_header "Systemd service"

CURRENT_USER="$(whoami)"

sudo tee /etc/systemd/system/birdnet_analyzer.service > /dev/null << EOF
[Unit]
Description=BirdNET Real-Time Bird Analyzer
After=network.target mosquitto.service iphone-audio-stream.service
Wants=mosquitto.service iphone-audio-stream.service

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${AUDIO_DIR}
ExecStart=${VENV_DIR}/bin/python3 ${BIRDNET_SCRIPT}
Restart=always
RestartSec=15

# Environment
Environment="PYTHONUNBUFFERED=1"
Environment="BIRDNET_LAT=${BIRDNET_LAT}"
Environment="BIRDNET_LON=${BIRDNET_LON}"
Environment="BIRDNET_MIN_CONF=0.25"
Environment="BIRDNET_GAP=0"

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable birdnet_analyzer.service

print_success "birdnet_analyzer.service created and enabled"

###############################################################################
# Quick test
###############################################################################

print_header "Quick test"

print_info "Running a quick import test..."
python3 -c "
from birdnetlib.analyzer import Analyzer
from birdnetlib import Recording
import pyaudio
import paho.mqtt.client as mqtt
print('All imports successful')
"
print_success "All imports work"

###############################################################################
# Summary
###############################################################################

print_header "Installation Complete!"

echo ""
echo -e "${GREEN}BirdNET Analyzer has been installed!${NC}"
echo ""
echo "Location: ${BIRDNET_LAT}, ${BIRDNET_LON}"
echo ""
echo "To start the service:"
echo "  sudo systemctl start birdnet_analyzer"
echo ""
echo "To check status:"
echo "  sudo systemctl status birdnet_analyzer"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u birdnet_analyzer -f"
echo ""
echo "To test MQTT output:"
echo "  mosquitto_sub -h localhost -t 'birdnet/#' -v"
echo ""
echo "To change location later, edit the service file:"
echo "  sudo systemctl edit birdnet_analyzer"
echo "  (add Environment=\"BIRDNET_LAT=xx.xx\" etc.)"
echo ""

if [ "$BIRDNET_LAT" = "0" ] && [ "$BIRDNET_LON" = "0" ]; then
    echo -e "${YELLOW}REMINDER: Set your location for better accuracy!${NC}"
    echo "  Edit /etc/systemd/system/birdnet_analyzer.service"
    echo "  Change BIRDNET_LAT and BIRDNET_LON, then:"
    echo "  sudo systemctl daemon-reload && sudo systemctl restart birdnet_analyzer"
    echo ""
fi

print_success "Done!"
