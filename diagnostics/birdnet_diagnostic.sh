#!/bin/bash
###############################################################################
# BirdNET-Pi Diagnostic Script
# Copy-paste this entire script into your SSH session on the Pi
###############################################################################

echo "==============================================================================="
echo "BIRDNET-PI DIAGNOSTIC SCRIPT"
echo "==============================================================================="
echo ""

echo "=== 1. CHECKING BIRDNET SERVICES ==="
echo ""
echo "Checking birdnet_recording service:"
systemctl is-active birdnet_recording 2>&1 || echo "Service not found or inactive"
echo ""

echo "Checking birdnet_analysis service:"
systemctl is-active birdnet_analysis 2>&1 || echo "Service not found or inactive"
echo ""

echo "Checking birdnet service:"
systemctl is-active birdnet 2>&1 || echo "Service not found or inactive"
echo ""

echo "All services with 'bird' in name:"
systemctl list-units --all | grep -i bird || echo "No BirdNET services found"
echo ""

echo "=== 2. CHECKING BIRDNET PROCESSES ==="
echo ""
ps aux | grep -i birdnet | grep -v grep || echo "No BirdNET processes running"
echo ""

echo "=== 3. CHECKING BIRDNET DIRECTORIES ==="
echo ""
echo "Looking for BirdNET-Pi directory:"
ls -la ~/BirdNET-Pi/ 2>/dev/null || echo "~/BirdNET-Pi/ does not exist"
echo ""

echo "Looking for BirdSongs directory:"
ls -la ~/BirdSongs/ 2>/dev/null || echo "~/BirdSongs/ does not exist"
echo ""

echo "Searching for any BirdNET directories:"
find ~ -maxdepth 3 -type d -iname "*birdnet*" 2>/dev/null || echo "No BirdNET directories found"
echo ""

echo "=== 4. CHECKING BIRDNET PYTHON MODULE ==="
echo ""
python3 -c "import birdnet" 2>&1 && echo "BirdNET Python module found" || echo "BirdNET Python module NOT found"
echo ""

echo "=== 5. CHECKING WEB INTERFACE PORTS ==="
echo ""
echo "Checking for web services on common ports:"
sudo netstat -tulpn 2>/dev/null | grep -E ":(80|8080|8000|3000)" || echo "netstat not available, trying ss:"
sudo ss -tulpn 2>/dev/null | grep -E ":(80|8080|8000|3000)" || echo "No common web ports in use"
echo ""

echo "=== 6. CHECKING MQTT BROKER ==="
echo ""
echo "Testing MQTT broker connectivity:"
timeout 5 mosquitto_sub -h localhost -t "birdnet/#" -C 1 2>&1 || echo "MQTT broker connection failed or no messages"
echo ""

echo "=== 7. CHECKING AUDIO SETUP ==="
echo ""
echo "ALSA audio devices:"
arecord -l 2>&1
echo ""

echo "Current audio capture test (3 seconds):"
LOOPBACK_CARD=$(arecord -l 2>/dev/null | grep -i loopback | head -1 | sed -n 's/card \([0-9]*\):.*/\1/p')
if [ -n "$LOOPBACK_CARD" ]; then
    echo "Found loopback device on card $LOOPBACK_CARD"
    timeout 3 arecord -D "hw:$LOOPBACK_CARD,1" -f S16_LE -r 16000 -c 1 -d 2 /tmp/audio_test.wav 2>&1
    if [ -f /tmp/audio_test.wav ]; then
        FILESIZE=$(stat -f%z /tmp/audio_test.wav 2>/dev/null || stat -c%s /tmp/audio_test.wav 2>/dev/null)
        echo "Audio captured: $FILESIZE bytes"
        rm -f /tmp/audio_test.wav
    else
        echo "Failed to capture audio"
    fi
else
    echo "No loopback device found"
fi
echo ""

echo "=== 8. CHECKING DOG BARK DETECTOR (PROOF AUDIO WORKS) ==="
echo ""
echo "Dog bark detector service status:"
systemctl is-active dog_bark_detector 2>&1 || echo "Service not found or inactive"
echo ""

echo "Dog bark detector process:"
ps aux | grep dog_bark_detector | grep -v grep || echo "Dog bark detector not running"
echo ""

echo "Recent dog bark MQTT messages:"
timeout 3 mosquitto_sub -h localhost -t "audio/#" -C 3 -v 2>&1 || echo "No audio MQTT messages received"
echo ""

echo "=== 9. CHECKING SYSTEM INFO ==="
echo ""
echo "Current user:"
whoami
echo ""

echo "Home directory:"
echo $HOME
echo ""

echo "Current directory:"
pwd
echo ""

echo "Python version:"
python3 --version
echo ""

echo "Free disk space:"
df -h | grep -E "Filesystem|/$|/mnt/usb"
echo ""

echo "=== 10. CHECKING BIRDNET CONFIG FILES ==="
echo ""
echo "Looking for birdnet.conf:"
find ~ -name "birdnet.conf" 2>/dev/null || echo "No birdnet.conf found"
echo ""

echo "Looking for BirdNET config in common locations:"
ls -la /etc/birdnet/ 2>/dev/null || echo "/etc/birdnet/ does not exist"
ls -la ~/.config/birdnet/ 2>/dev/null || echo "~/.config/birdnet/ does not exist"
echo ""

echo "==============================================================================="
echo "DIAGNOSTIC COMPLETE"
echo "==============================================================================="
echo ""
echo "Please copy ALL of the above output and paste it back to Claude."
echo ""
