#!/bin/bash
###############################################################################
# BirdNET-Pi Installation Script
# ===============================
# Automated installation of BirdNET-Pi for bird detection
#
# This script:
# - Installs BirdNET-Pi and dependencies
# - Configures MQTT integration
# - Sets up systemd service
# - Configures audio input
#
# Author: Claude Code
# License: MIT
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BIRDNET_DIR="$HOME/BirdNET-Pi"
INSTALL_DIR="$HOME/audio_detection"
MQTT_BROKER="localhost"
MQTT_PORT="1883"

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

###############################################################################
# Installation Steps
###############################################################################

install_dependencies() {
    print_header "Installing Dependencies"

    print_info "Updating package lists..."
    sudo apt-get update

    print_info "Installing required packages..."
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-dev \
        python3-venv \
        git \
        ffmpeg \
        sox \
        libsox-fmt-all \
        alsa-utils \
        sqlite3 \
        portaudio19-dev \
        libatlas-base-dev \
        libopenblas-dev \
        libhdf5-dev \
        libc-ares-dev \
        libeigen3-dev \
        gcc \
        g++

    print_success "Dependencies installed"
}

clone_birdnet() {
    print_header "Downloading BirdNET-Pi"

    if [ -d "$BIRDNET_DIR" ]; then
        print_info "BirdNET-Pi directory already exists. Updating..."
        cd "$BIRDNET_DIR"
        git pull
    else
        print_info "Cloning BirdNET-Pi repository..."
        git clone https://github.com/mcguirepr89/BirdNET-Pi.git "$BIRDNET_DIR"
        cd "$BIRDNET_DIR"
    fi

    print_success "BirdNET-Pi downloaded"
}

install_birdnet() {
    print_header "Installing BirdNET-Pi"

    cd "$BIRDNET_DIR"

    print_info "Running installation script (this will take 30-60 minutes)..."
    print_info "You may be prompted for configuration choices. Use defaults unless you have specific needs."

    # Run the installer
    chmod +x install.sh
    ./install.sh

    print_success "BirdNET-Pi installed"
}

configure_mqtt() {
    print_header "Configuring MQTT Integration"

    cd "$BIRDNET_DIR"

    print_info "Enabling MQTT in BirdNET configuration..."

    # Update BirdNET config to enable MQTT
    if [ -f "$BIRDNET_DIR/birdnet.conf" ]; then
        sed -i "s/MQTT_ENABLED=.*/MQTT_ENABLED=1/" "$BIRDNET_DIR/birdnet.conf"
        sed -i "s/MQTT_BROKER=.*/MQTT_BROKER=$MQTT_BROKER/" "$BIRDNET_DIR/birdnet.conf"
        sed -i "s/MQTT_PORT=.*/MQTT_PORT=$MQTT_PORT/" "$BIRDNET_DIR/birdnet.conf"
        sed -i "s/MQTT_TOPIC_PREFIX=.*/MQTT_TOPIC_PREFIX=birdnet/" "$BIRDNET_DIR/birdnet.conf"
        print_success "MQTT configuration updated"
    else
        print_info "Configuration file will be created on first run"
    fi
}

create_mqtt_publisher() {
    print_header "Creating MQTT Publisher Script"

    cat > "$BIRDNET_DIR/scripts/publish_mqtt.py" << 'EOF'
#!/usr/bin/env python3
"""
BirdNET MQTT Publisher
Publishes bird detections to MQTT for Home Assistant integration
"""

import sqlite3
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "birdnet"
DB_PATH = "/home/pi/BirdNET-Pi/scripts/birds.db"

def publish_detection(client, detection):
    """Publish detection to MQTT"""
    payload = {
        'timestamp': detection['Date'] + ' ' + detection['Time'],
        'scientific_name': detection['Sci_Name'],
        'common_name': detection['Com_Name'],
        'confidence': detection['Confidence'],
        'latitude': detection['Lat'],
        'longitude': detection['Lon']
    }

    topic = f"{MQTT_TOPIC_PREFIX}/detection"
    client.publish(topic, json.dumps(payload))
    print(f"Published: {detection['Com_Name']} ({detection['Confidence']})")

def publish_stats(client):
    """Publish daily statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')

    # Count unique species today
    cursor.execute("""
        SELECT COUNT(DISTINCT Com_Name)
        FROM detections
        WHERE Date = ?
    """, (today,))
    species_count = cursor.fetchone()[0]

    # Count total detections today
    cursor.execute("""
        SELECT COUNT(*)
        FROM detections
        WHERE Date = ?
    """, (today,))
    total_detections = cursor.fetchone()[0]

    conn.close()

    payload = {
        'date': today,
        'species_count': species_count,
        'total_detections': total_detections
    }

    topic = f"{MQTT_TOPIC_PREFIX}/stats"
    client.publish(topic, json.dumps(payload))

def main():
    """Main loop"""
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    print("BirdNET MQTT Publisher started")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get last detection time
    last_check = datetime.now() - timedelta(seconds=10)

    while True:
        try:
            # Query new detections
            cursor.execute("""
                SELECT Date, Time, Sci_Name, Com_Name, Confidence, Lat, Lon
                FROM detections
                WHERE datetime(Date || ' ' || Time) > datetime(?)
                ORDER BY Date DESC, Time DESC
            """, (last_check.strftime('%Y-%m-%d %H:%M:%S'),))

            detections = cursor.fetchall()

            for detection in detections:
                publish_detection(client, dict(detection))

            if detections:
                last_check = datetime.now()

            # Publish stats every minute
            publish_stats(client)

            time.sleep(10)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

    conn.close()
    client.loop_stop()

if __name__ == "__main__":
    main()
EOF

    chmod +x "$BIRDNET_DIR/scripts/publish_mqtt.py"
    print_success "MQTT publisher script created"
}

create_systemd_service() {
    print_header "Creating Systemd Service"

    print_info "Creating birdnet-mqtt.service..."

    sudo tee /etc/systemd/system/birdnet-mqtt.service > /dev/null << EOF
[Unit]
Description=BirdNET MQTT Publisher
After=network.target mosquitto.service birdnet.service
Wants=mosquitto.service birdnet.service

[Service]
Type=simple
User=pi
WorkingDirectory=$BIRDNET_DIR/scripts
ExecStart=/usr/bin/python3 $BIRDNET_DIR/scripts/publish_mqtt.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable birdnet-mqtt.service

    print_success "Systemd service created"
}

test_installation() {
    print_header "Testing Installation"

    print_info "Checking if BirdNET service is running..."
    if systemctl is-active --quiet birdnet; then
        print_success "BirdNET service is running"
    else
        print_info "Starting BirdNET service..."
        sudo systemctl start birdnet
        sleep 5
        if systemctl is-active --quiet birdnet; then
            print_success "BirdNET service started"
        else
            print_error "BirdNET service failed to start. Check logs: sudo journalctl -u birdnet"
        fi
    fi

    print_info "Checking if MQTT publisher is running..."
    if systemctl is-active --quiet birdnet-mqtt; then
        print_success "MQTT publisher is running"
    else
        print_info "Starting MQTT publisher..."
        sudo systemctl start birdnet-mqtt
        sleep 5
        if systemctl is-active --quiet birdnet-mqtt; then
            print_success "MQTT publisher started"
        else
            print_error "MQTT publisher failed to start. Check logs: sudo journalctl -u birdnet-mqtt"
        fi
    fi

    print_info "Checking BirdNET database..."
    if [ -f "$HOME/BirdNET-Pi/scripts/birds.db" ]; then
        print_success "BirdNET database exists"
    else
        print_info "Database will be created when first bird is detected"
    fi
}

print_summary() {
    print_header "Installation Complete!"

    echo ""
    echo -e "${GREEN}BirdNET-Pi has been installed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Access the web interface:"
    echo "   http://$(hostname -I | awk '{print $1}')"
    echo ""
    echo "2. Configure settings in the web interface:"
    echo "   - Audio source (select your iPhone/microphone)"
    echo "   - Location (for species filtering)"
    echo "   - Minimum confidence threshold (0.7 recommended)"
    echo ""
    echo "3. Check service status:"
    echo "   sudo systemctl status birdnet"
    echo "   sudo systemctl status birdnet-mqtt"
    echo ""
    echo "4. View logs:"
    echo "   sudo journalctl -u birdnet -f"
    echo "   sudo journalctl -u birdnet-mqtt -f"
    echo ""
    echo "5. Test MQTT messages:"
    echo "   mosquitto_sub -h localhost -t 'birdnet/#' -v"
    echo ""
    echo -e "${YELLOW}Important:${NC} Make sure your iPhone audio is streaming to the Pi!"
    echo ""
}

###############################################################################
# Main Installation Flow
###############################################################################

main() {
    print_header "BirdNET-Pi Installation Script"
    echo ""
    echo "This script will install BirdNET-Pi for bird detection."
    echo "Installation will take approximately 30-60 minutes."
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."

    install_dependencies
    clone_birdnet
    install_birdnet
    configure_mqtt
    create_mqtt_publisher
    create_systemd_service
    test_installation
    print_summary

    print_success "All done! 🎉"
}

# Run main function
main
