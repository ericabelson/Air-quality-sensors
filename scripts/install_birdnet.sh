#!/bin/bash
###############################################################################
# BirdNET Analyzer Installation Script
# =====================================
# Installs birdnetlib (pip-installable BirdNET-Analyzer wrapper) into the
# audio_detection virtualenv, downloads the model, creates the systemd
# service, and verifies everything works.
#
# Usage:
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

# Paths
VENV_DIR="$HOME/audio_detection/venv"
AUDIO_DIR="$HOME/audio_detection"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIRDNET_SCRIPT="$SCRIPT_DIR/birdnet_analyzer.py"

print_header()  { echo -e "\n${BLUE}======== $1 ========${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_info()    { echo -e "${YELLOW}ℹ $1${NC}"; }

# Track failures so we can bail out with a clear message
ERRORS=0
note_error() {
    print_error "$1"
    ERRORS=$((ERRORS + 1))
}

###############################################################################
# Pre-flight checks
###############################################################################

print_header "Pre-flight checks"

# Python version
PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VER" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VER" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]; }; then
    print_error "Python 3.9+ required (found $PYTHON_VER)"
    exit 1
fi
print_success "Python $PYTHON_VER"

# birdnet_analyzer.py present
if [ ! -f "$BIRDNET_SCRIPT" ]; then
    print_error "birdnet_analyzer.py not found at $BIRDNET_SCRIPT"
    exit 1
fi
print_success "birdnet_analyzer.py found"

# Venv
if [ ! -d "$VENV_DIR" ]; then
    print_info "Creating virtualenv at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi
print_success "Virtualenv at $VENV_DIR"

source "$VENV_DIR/bin/activate"

###############################################################################
# System dependencies
# These are C libraries required by Python packages (soundfile, pyaudio).
# Without them, pip install will succeed but the modules will segfault or
# fail to import.
###############################################################################

print_header "System dependencies"

SYSTEM_PKGS=(
    ffmpeg              # audio format conversion
    libsndfile1         # runtime lib for soundfile/librosa
    libsndfile1-dev     # headers needed to build soundfile
    portaudio19-dev     # headers needed to build pyaudio
    libopenblas-dev     # optimized BLAS for numpy/scipy/tensorflow
)

print_info "Installing: ${SYSTEM_PKGS[*]}"
sudo apt-get update -qq
sudo apt-get install -y -qq "${SYSTEM_PKGS[@]}" 2>/dev/null

# Verify the critical libraries are actually present
for lib in libsndfile.so libportaudio.so; do
    if ldconfig -p 2>/dev/null | grep -q "$lib"; then
        print_success "$lib found"
    else
        note_error "$lib NOT found — a Python package will fail to import"
    fi
done

if [ "$ERRORS" -gt 0 ]; then
    print_error "System dependency issues detected. Fix the above before continuing."
    exit 1
fi

print_success "System dependencies installed and verified"

###############################################################################
# Python packages
# Install in dependency order so we catch failures early.
# birdnetlib 0.18 only declares 4 of its ~12 actual dependencies, so we
# install the undeclared ones explicitly.
###############################################################################

print_header "Python packages (this may take several minutes)"

print_info "Upgrading pip..."
pip install --upgrade pip -q

# 1. TFLite backend — birdnetlib needs tflite_runtime OR tensorflow.
#    tflite-runtime has no wheel for Python 3.13, so go straight to tensorflow.
print_info "Installing tensorflow (BirdNET inference backend)..."
print_info "  This is ~600 MB — be patient..."
pip install tensorflow

# Verify
if python3 -c "from tensorflow import lite as tflite; print('tensorflow OK')" 2>/dev/null; then
    print_success "tensorflow installed and importable"
else
    note_error "tensorflow installed but 'from tensorflow import lite' fails"
fi

# 2. librosa + its full dependency tree (scipy, soundfile, resampy, audioread, numba...)
print_info "Installing librosa (audio analysis library)..."
pip install librosa

if python3 -c "import librosa; print('librosa OK')" 2>/dev/null; then
    print_success "librosa installed and importable"
else
    note_error "librosa installed but import fails"
fi

# 3. birdnetlib itself
print_info "Installing birdnetlib..."
pip install birdnetlib

# 4. Our application dependencies (pyaudio for mic, paho-mqtt for HA)
print_info "Installing pyaudio and paho-mqtt..."
pip install pyaudio paho-mqtt

# Bail out if anything failed
if [ "$ERRORS" -gt 0 ]; then
    print_error "$ERRORS package(s) failed verification. See errors above."
    exit 1
fi

print_success "All Python packages installed"

###############################################################################
# Comprehensive import verification
# Test EVERY import that birdnet_analyzer.py and birdnetlib need.
# If anything fails here, we stop before creating the service.
###############################################################################

print_header "Import verification"

print_info "Testing every required import..."

python3 << 'PYEOF'
import sys
failures = []

modules = {
    "numpy":                    "numpy",
    "scipy":                    "scipy",
    "librosa":                  "librosa",
    "soundfile":                "soundfile",
    "resampy":                  "resampy",
    "audioread":                "audioread",
    "tensorflow":               "tensorflow",
    "tensorflow.lite":          "from tensorflow import lite as tflite",
    "paho.mqtt.client":         "paho-mqtt",
    "pyaudio":                  "pyaudio",
    "birdnetlib":               "birdnetlib",
    "birdnetlib.analyzer":      "birdnetlib (analyzer)",
    "birdnetlib.main":          "birdnetlib (main)",
}

for mod, label in modules.items():
    try:
        __import__(mod)
        print(f"  OK: {label}")
    except Exception as e:
        print(f"  FAIL: {label} -- {e}")
        failures.append(label)

if failures:
    print(f"\n{len(failures)} import(s) failed: {', '.join(failures)}")
    sys.exit(1)
else:
    print("\nAll imports successful!")
    sys.exit(0)
PYEOF

if [ $? -ne 0 ]; then
    print_error "Import verification failed. See above for details."
    exit 1
fi

print_success "All imports verified"

###############################################################################
# Download & verify BirdNET model
###############################################################################

print_header "BirdNET model"

print_info "Loading BirdNET model (downloads ~150 MB on first run)..."
python3 -c "
from birdnetlib.analyzer import Analyzer
a = Analyzer()
print('  Model loaded successfully')
"

if [ $? -ne 0 ]; then
    print_error "BirdNET model failed to load"
    exit 1
fi

print_success "BirdNET model ready"

###############################################################################
# Location
###############################################################################

print_header "Location configuration"

if [ -z "$BIRDNET_LAT" ] || [ -z "$BIRDNET_LON" ]; then
    print_info "BIRDNET_LAT and BIRDNET_LON are not set."
    print_info "BirdNET uses your location to filter species likely in your area."
    echo ""
    read -p "Enter latitude  (e.g. 30.2672, or press Enter for Austin TX): " USER_LAT
    read -p "Enter longitude (e.g. -97.7431, or press Enter for Austin TX): " USER_LON

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
# Directories
###############################################################################

print_header "Directories"

mkdir -p "$AUDIO_DIR/logs"
mkdir -p "$AUDIO_DIR/data"
mkdir -p "$AUDIO_DIR/bird_recordings"

print_success "Directories created"

###############################################################################
# Systemd service
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
# Final end-to-end test
###############################################################################

print_header "End-to-end test"

print_info "Running birdnet_analyzer.py import check..."

python3 -c "
from birdnetlib.analyzer import Analyzer
from birdnetlib import Recording
import pyaudio
import paho.mqtt.client as mqtt
import numpy as np
import json, wave, tempfile, os

# Verify Analyzer can be instantiated
a = Analyzer()

# Verify pyaudio can see audio devices
pa = pyaudio.PyAudio()
count = pa.get_device_count()
pa.terminate()

print(f'  BirdNET model: OK')
print(f'  Audio devices: {count} found')
print(f'  All systems go!')
"

if [ $? -ne 0 ]; then
    print_error "End-to-end test failed"
    exit 1
fi

print_success "End-to-end test passed"

###############################################################################
# Summary
###############################################################################

print_header "Installation Complete!"

echo ""
echo -e "${GREEN}BirdNET Analyzer is ready!${NC}"
echo ""
echo "  Location:  ${BIRDNET_LAT}, ${BIRDNET_LON}"
echo "  Service:   birdnet_analyzer.service"
echo "  Script:    ${BIRDNET_SCRIPT}"
echo "  Venv:      ${VENV_DIR}"
echo ""
echo "Start it:"
echo "  sudo systemctl start birdnet_analyzer"
echo ""
echo "Check it:"
echo "  sudo systemctl status birdnet_analyzer"
echo "  sudo journalctl -u birdnet_analyzer -f"
echo "  mosquitto_sub -h localhost -t 'birdnet/#' -v"
echo ""

print_success "Done!"
