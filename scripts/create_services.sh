#!/bin/bash
###############################################################################
# Create Systemd Services for Audio Detection
# ============================================
# Creates systemd service files for automatic startup
#
# Services created:
# - dog_bark_detector.service (dog bark detection)
# - audio_csv_export.timer (daily CSV export)
#
# Author: Claude Code
# License: MIT
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Creating Systemd Services${NC}"

###############################################################################
# Dog Bark Detector Service
###############################################################################

echo -e "${YELLOW}Creating dog_bark_detector.service...${NC}"

sudo tee /etc/systemd/system/dog_bark_detector.service > /dev/null << 'EOF'
[Unit]
Description=Dog Bark Detector
After=network.target mosquitto.service
Wants=mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/audio_detection
ExecStart=/home/pi/audio_detection/venv/bin/python3 /home/user/Air-quality-sensors/scripts/dog_bark_detector.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ dog_bark_detector.service created${NC}"

###############################################################################
# CSV Export Timer (Daily)
###############################################################################

echo -e "${YELLOW}Creating CSV export timer...${NC}"

# Create the service
sudo tee /etc/systemd/system/audio_csv_export.service > /dev/null << 'EOF'
[Unit]
Description=Export Audio Detection CSV Files

[Service]
Type=oneshot
User=pi
WorkingDirectory=/home/pi/audio_detection
ExecStart=/home/pi/audio_detection/venv/bin/python3 /home/user/Air-quality-sensors/scripts/csv_exporter.py --all
StandardOutput=journal
StandardError=journal
EOF

# Create the timer
sudo tee /etc/systemd/system/audio_csv_export.timer > /dev/null << 'EOF'
[Unit]
Description=Daily CSV Export Timer
Requires=audio_csv_export.service

[Timer]
OnCalendar=daily
OnCalendar=00:01:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo -e "${GREEN}✓ CSV export timer created${NC}"

###############################################################################
# Enable and Start Services
###############################################################################

echo -e "${YELLOW}Reloading systemd daemon...${NC}"
sudo systemctl daemon-reload

echo -e "${YELLOW}Enabling services...${NC}"
sudo systemctl enable dog_bark_detector.service
sudo systemctl enable audio_csv_export.timer

echo -e "${GREEN}✓ Services enabled${NC}"

echo ""
echo -e "${GREEN}Services created successfully!${NC}"
echo ""
echo "To start the services now:"
echo "  sudo systemctl start dog_bark_detector"
echo "  sudo systemctl start audio_csv_export.timer"
echo ""
echo "To check status:"
echo "  sudo systemctl status dog_bark_detector"
echo "  sudo systemctl status audio_csv_export.timer"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u dog_bark_detector -f"
echo ""
