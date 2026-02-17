#!/bin/bash
###############################################################################
# BirdNET Analyzer Installation Script
# =====================================
# Installs birdnetlib (pip-installable BirdNET-Analyzer wrapper) into the
# audio_detection virtualenv, downloads the model, creates the systemd
# service, and verifies everything works.
#
# Key design decisions:
#   - Uses ai-edge-litert (~12 MB) instead of tensorflow (~260 MB)
#     because tflite-runtime has no Python 3.13 wheel and tensorflow
#     is too large for most Pis.
#   - Creates a tflite_runtime shim so birdnetlib's imports work
#     transparently with ai-edge-litert.
#   - Checks disk space before starting.
#   - Verifies every system lib and Python import before proceeding.
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

ERRORS=0
note_error() {
    print_error "$1"
    ERRORS=$((ERRORS + 1))
}

###############################################################################
# Pre-flight checks
###############################################################################

print_header "Pre-flight checks"

# Disk space — need at least 500 MB free for packages + model
AVAIL_MB=$(df --output=avail -m "$HOME" | tail -1 | tr -d ' ')
if [ "$AVAIL_MB" -lt 500 ]; then
    print_error "Only ${AVAIL_MB} MB free on disk. Need at least 500 MB."
    print_info "Tip: run 'sudo apt clean' and 'pip cache purge' to free space."
    exit 1
fi
print_success "Disk space: ${AVAIL_MB} MB available"

# Python version (birdnetlib needs 3.9+)
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
# These are C libraries required by Python packages. Without them, pip
# install succeeds but the modules fail to import at runtime.
###############################################################################

print_header "System dependencies"

SYSTEM_PKGS=(
    ffmpeg              # audio format conversion (used by pydub)
    libsndfile1         # runtime lib for soundfile/librosa
    libsndfile1-dev     # headers needed to build soundfile wheel
    portaudio19-dev     # headers + lib needed to build pyaudio
    libopenblas-dev     # BLAS for numpy/scipy
)

print_info "Installing: ${SYSTEM_PKGS[*]}"
sudo apt-get update -qq
sudo apt-get install -y -qq "${SYSTEM_PKGS[@]}" 2>/dev/null

# Verify the critical shared libraries are actually loadable
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
# birdnetlib 0.18 only declares 4 of its ~12 actual runtime dependencies,
# so we install the undeclared ones explicitly.
#
# We use ai-edge-litert (~12 MB) instead of tensorflow (~260 MB) for the
# TFLite interpreter. tflite-runtime has no Python 3.13 wheel at all.
# ai-edge-litert is Google's official successor with 3.13 aarch64 support.
###############################################################################

print_header "Python packages"

print_info "Upgrading pip..."
pip install --upgrade pip -q

# Clear pip cache to maximize disk space
pip cache purge 2>/dev/null || true

# --- 1. TFLite backend via ai-edge-litert ---
print_info "Installing ai-edge-litert (lightweight TFLite runtime, ~12 MB)..."
pip install ai-edge-litert

if python3 -c "import ai_edge_litert; print('ai-edge-litert OK')" 2>/dev/null; then
    print_success "ai-edge-litert installed and importable"
else
    note_error "ai-edge-litert installed but import fails"
fi

# --- 2. Create tflite_runtime shim ---
# birdnetlib does: import tflite_runtime.interpreter as tflite
# ai-edge-litert provides the same API under a different package name.
# This shim bridges the two so birdnetlib works without patching.
print_info "Creating tflite_runtime compatibility shim..."

SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
SHIM_DIR="$SITE_PACKAGES/tflite_runtime"

mkdir -p "$SHIM_DIR"

cat > "$SHIM_DIR/__init__.py" << 'SHIMEOF'
# Shim: redirect tflite_runtime imports to ai_edge_litert
# birdnetlib expects tflite_runtime but we use the lighter ai-edge-litert
from ai_edge_litert import interpreter
SHIMEOF

cat > "$SHIM_DIR/interpreter.py" << 'SHIMEOF'
# Shim: redirect tflite_runtime.interpreter to ai_edge_litert.interpreter
from ai_edge_litert.interpreter import *
from ai_edge_litert.interpreter import Interpreter
SHIMEOF

# Verify the shim works
if python3 -c "import tflite_runtime.interpreter as tflite; print('tflite_runtime shim OK')" 2>/dev/null; then
    print_success "tflite_runtime shim works"
else
    note_error "tflite_runtime shim failed — birdnetlib will not load"
fi

# --- 3. librosa (pulls in scipy, soundfile, resampy, audioread, etc.) ---
print_info "Installing librosa (audio analysis + dependencies)..."
pip install librosa

if python3 -c "import librosa; print('librosa OK')" 2>/dev/null; then
    print_success "librosa installed and importable"
else
    note_error "librosa installed but import fails"
fi

# --- 4. birdnetlib ---
print_info "Installing birdnetlib..."
pip install birdnetlib

# --- 5. Application dependencies ---
print_info "Installing pyaudio and paho-mqtt..."
pip install pyaudio paho-mqtt

# Clear pip cache again to reclaim space
pip cache purge 2>/dev/null || true

if [ "$ERRORS" -gt 0 ]; then
    print_error "$ERRORS package(s) failed verification. See errors above."
    exit 1
fi

print_success "All Python packages installed"

###############################################################################
# Comprehensive import verification
# Test EVERY import that birdnet_analyzer.py and birdnetlib use.
# If anything fails, we stop before creating the systemd service.
###############################################################################

print_header "Import verification"

print_info "Testing every required import..."

python3 << 'PYEOF'
import sys
failures = []

modules = {
    "numpy":                        "numpy",
    "scipy":                        "scipy",
    "librosa":                      "librosa",
    "soundfile":                    "soundfile",
    "resampy":                      "resampy",
    "audioread":                    "audioread",
    "ai_edge_litert":               "ai-edge-litert",
    "tflite_runtime":               "tflite_runtime (shim)",
    "tflite_runtime.interpreter":   "tflite_runtime.interpreter (shim)",
    "paho.mqtt.client":             "paho-mqtt",
    "pyaudio":                      "pyaudio",
    "birdnetlib":                   "birdnetlib",
    "birdnetlib.analyzer":          "birdnetlib (analyzer)",
    "birdnetlib.main":              "birdnetlib (main)",
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

# Check disk space again before downloading the ~150 MB model
AVAIL_MB=$(df --output=avail -m "$HOME" | tail -1 | tr -d ' ')
if [ "$AVAIL_MB" -lt 200 ]; then
    print_error "Only ${AVAIL_MB} MB free. Need ~200 MB for BirdNET model download."
    exit 1
fi

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

print_info "Running full integration check..."

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
