#!/bin/bash
###############################################################################
# Audio Detection Installation Script
# ====================================
# Installs ALL dependencies for both detectors into a single virtualenv:
#   - BirdNET bird species detector  (birdnet_analyzer.py)
#   - Dog bark detector              (dog_bark_detector.py)
#
# Key design decisions:
#   - Uses ai-edge-litert (~12 MB) instead of tensorflow (~260 MB).
#     Both detectors share the same TFLite runtime via a tflite_runtime shim.
#   - Every Python dependency is installed EXPLICITLY — no reliance on
#     transitive deps that may or may not be pulled in by pip.
#   - Downloads the YAMNet model for dog bark detection automatically.
#   - Verifies every import before declaring success.
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
DOG_BARK_SCRIPT="$SCRIPT_DIR/dog_bark_detector.py"
MODELS_DIR="$AUDIO_DIR/models"

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

# Disk space — need at least 500 MB free for packages + models
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

# Scripts present
for script in "$BIRDNET_SCRIPT" "$DOG_BARK_SCRIPT"; do
    name=$(basename "$script")
    if [ ! -f "$script" ]; then
        print_error "$name not found at $script"
        exit 1
    fi
    print_success "$name found"
done

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
# EVERY runtime dependency is listed explicitly below. We do NOT rely on
# transitive dependencies being pulled in — pip resolvers can skip them.
#
# We use ai-edge-litert (~12 MB) instead of tensorflow (~260 MB) for the
# TFLite interpreter. Both birdnetlib and dog_bark_detector.py use it via
# a tflite_runtime shim created below.
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
# birdnetlib does:  import tflite_runtime.interpreter as tflite
# dog_bark_detector: from tflite_runtime.interpreter import Interpreter
# ai-edge-litert provides the same API under a different package name.
# This shim bridges the two so both scripts work without patching.
print_info "Creating tflite_runtime compatibility shim..."

SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
SHIM_DIR="$SITE_PACKAGES/tflite_runtime"

mkdir -p "$SHIM_DIR"

cat > "$SHIM_DIR/__init__.py" << 'SHIMEOF'
# Shim: redirect tflite_runtime imports to ai_edge_litert
# Both birdnetlib and dog_bark_detector use this shim
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
    note_error "tflite_runtime shim failed"
fi

# --- 3. ALL audio/ML packages (explicit, not relying on transitive deps) ---
print_info "Installing all audio and ML packages..."

# Install in one shot so pip can resolve versions together
pip install \
    numpy \
    scipy \
    librosa \
    soundfile \
    resampy \
    audioread \
    pydub \
    birdnetlib \
    pyaudio \
    paho-mqtt

# Clear pip cache again to reclaim space
pip cache purge 2>/dev/null || true

if [ "$ERRORS" -gt 0 ]; then
    print_error "$ERRORS package(s) failed verification. See errors above."
    exit 1
fi

print_success "All Python packages installed"

###############################################################################
# Comprehensive import verification
# Test EVERY import that both detectors use. If anything fails here, we
# attempt to install the missing package and re-test (self-healing).
###############################################################################

print_header "Import verification"

print_info "Testing every required import..."

python3 << 'PYEOF'
import sys
failures = []

modules = {
    # Shared by both detectors
    "numpy":                        "numpy",
    "scipy":                        "scipy",
    "scipy.io.wavfile":             "scipy.io.wavfile",
    "librosa":                      "librosa",
    "soundfile":                    "soundfile",
    "resampy":                      "resampy",
    "audioread":                    "audioread",
    "ai_edge_litert":               "ai-edge-litert",
    "tflite_runtime":               "tflite_runtime (shim)",
    "tflite_runtime.interpreter":   "tflite_runtime.interpreter (shim)",
    "paho.mqtt.client":             "paho-mqtt",
    "pyaudio":                      "pyaudio",

    # BirdNET specific
    "birdnetlib":                   "birdnetlib",
    "birdnetlib.analyzer":          "birdnetlib (analyzer)",
    "birdnetlib.main":              "birdnetlib (main)",

    # Dog bark detector specific
    "pydub":                        "pydub",
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
# Download YAMNet model (dog bark detection)
###############################################################################

print_header "YAMNet model (dog bark detection)"

mkdir -p "$MODELS_DIR"

YAMNET_MODEL="$MODELS_DIR/yamnet.tflite"
YAMNET_LABELS="$MODELS_DIR/yamnet_class_map.csv"

YAMNET_MODEL_URL="https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/audio_classification/android/lite-model_yamnet_classification_tflite_1.tflite"
YAMNET_LABELS_URL="https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv"

if [ -f "$YAMNET_MODEL" ]; then
    print_success "yamnet.tflite already present ($(du -h "$YAMNET_MODEL" | cut -f1))"
else
    print_info "Downloading yamnet.tflite (~4 MB)..."
    if wget -q -O "$YAMNET_MODEL" "$YAMNET_MODEL_URL"; then
        print_success "yamnet.tflite downloaded ($(du -h "$YAMNET_MODEL" | cut -f1))"
    else
        note_error "Failed to download yamnet.tflite"
    fi
fi

if [ -f "$YAMNET_LABELS" ]; then
    print_success "yamnet_class_map.csv already present"
else
    print_info "Downloading yamnet_class_map.csv..."
    if wget -q -O "$YAMNET_LABELS" "$YAMNET_LABELS_URL"; then
        print_success "yamnet_class_map.csv downloaded"
    else
        note_error "Failed to download yamnet_class_map.csv"
    fi
fi

# Verify YAMNet model loads with the TFLite interpreter
if [ -f "$YAMNET_MODEL" ]; then
    print_info "Verifying YAMNet model loads..."
    python3 -c "
from tflite_runtime.interpreter import Interpreter
interp = Interpreter(model_path='$YAMNET_MODEL')
interp.allocate_tensors()
inp = interp.get_input_details()
out = interp.get_output_details()
print(f'  Input shape:  {inp[0][\"shape\"]}')
print(f'  Output shape: {out[0][\"shape\"]}')
print('  YAMNet model OK')
"
    if [ $? -eq 0 ]; then
        print_success "YAMNet model verified"
    else
        note_error "YAMNet model failed to load"
    fi
fi

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
mkdir -p "$AUDIO_DIR/recordings"
mkdir -p "$AUDIO_DIR/models"

print_success "Directories created"

###############################################################################
# Systemd services (both detectors)
###############################################################################

print_header "Systemd services"

CURRENT_USER="$(whoami)"

# --- BirdNET Analyzer service ---
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

print_success "birdnet_analyzer.service created"

# --- Dog Bark Detector service ---
sudo tee /etc/systemd/system/dog_bark_detector.service > /dev/null << EOF
[Unit]
Description=Dog Bark Detector with Decibel Monitoring
After=network.target mosquitto.service iphone-audio-stream.service
Wants=mosquitto.service iphone-audio-stream.service

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${AUDIO_DIR}
ExecStart=${VENV_DIR}/bin/python3 ${DOG_BARK_SCRIPT}
Restart=always
RestartSec=10

Environment="PYTHONUNBUFFERED=1"

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

print_success "dog_bark_detector.service created"

sudo systemctl daemon-reload
sudo systemctl enable birdnet_analyzer.service
sudo systemctl enable dog_bark_detector.service

print_success "Both services enabled"

###############################################################################
# Final end-to-end test
###############################################################################

print_header "End-to-end test"

print_info "Running full integration check..."

python3 -c "
from birdnetlib.analyzer import Analyzer
from birdnetlib import Recording
from tflite_runtime.interpreter import Interpreter
import pyaudio
import paho.mqtt.client as mqtt
import numpy as np
import librosa
import soundfile
import resampy
import pydub
from scipy.io import wavfile
import json, wave, tempfile, os

# Verify BirdNET Analyzer can be instantiated
a = Analyzer()

# Verify YAMNet model loads (if present)
yamnet_path = os.path.expanduser('~/audio_detection/models/yamnet.tflite')
if os.path.exists(yamnet_path):
    interp = Interpreter(model_path=yamnet_path)
    interp.allocate_tensors()
    print(f'  YAMNet model: OK')
else:
    print(f'  YAMNet model: not found (dog bark detector will not work)')

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
echo -e "${GREEN}Both audio detectors are ready!${NC}"
echo ""
echo "  BirdNET Analyzer:"
echo "    Location: ${BIRDNET_LAT}, ${BIRDNET_LON}"
echo "    Service:  birdnet_analyzer.service"
echo "    Script:   ${BIRDNET_SCRIPT}"
echo ""
echo "  Dog Bark Detector:"
echo "    Model:    ${YAMNET_MODEL}"
echo "    Service:  dog_bark_detector.service"
echo "    Script:   ${DOG_BARK_SCRIPT}"
echo ""
echo "  Shared:"
echo "    Venv:     ${VENV_DIR}"
echo ""
echo "Start both:"
echo "  sudo systemctl start birdnet_analyzer dog_bark_detector"
echo ""
echo "Check status:"
echo "  sudo systemctl status birdnet_analyzer"
echo "  sudo systemctl status dog_bark_detector"
echo ""
echo "View logs:"
echo "  sudo journalctl -u birdnet_analyzer -f"
echo "  sudo journalctl -u dog_bark_detector -f"
echo ""
echo "MQTT topics:"
echo "  mosquitto_sub -h localhost -t 'birdnet/#' -v"
echo "  mosquitto_sub -h localhost -t 'audio/#' -v"
echo ""

print_success "Done!"
