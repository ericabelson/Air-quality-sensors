# Home Assistant UTSensing Integration - Deployment Notes

**Last Updated**: December 29, 2025
**Status**: In Progress (Sensors configured, verification pending)

## What Worked ✅

### 1. MQTT Data Publishing
- All 7 sensors actively publishing data to MQTT broker
- Verified with: `mosquitto_sub -h YOUR_HA_IP -t "utsensing/#" -v`
- Data format is correct (JSON with sensor-specific fields)

### 2. Repository Code Deployment
```bash
git pull origin main  # Successfully pulls HA configuration files
```

### 3. File Structure Setup
```bash
mkdir -p ~/homeassistant/packages
cp homeassistant/packages/utsensing_sensors.yaml ~/homeassistant/packages/
```
- Package directory creation works fine
- File permissions are correct (755)

### 4. Configuration File Update
```bash
sed -i '/^homeassistant:$/a\  packages: !include_dir_named packages' ~/homeassistant/configuration.yaml
```
- Using sed to inject the packages line works reliably
- Verified with: `grep -A 2 "^homeassistant:" ~/homeassistant/configuration.yaml`

### 5. Home Assistant Process Management
```bash
sudo kill <PID>  # Successfully restarts via s6-supervise
```
- Process restarts within 30-60 seconds
- s6 supervisor automatically restarts killed process

---

## What Didn't Work ❌

### 1. Systemd Services
```bash
sudo systemctl restart homeassistant       # FAILED - service not found
sudo systemctl restart home-assistant@root # FAILED - service not found
```
**Reason**: HA on this system uses s6-supervise, not systemd
**Solution**: Use `sudo kill <PID>` instead

### 2. Home Assistant UI Restart Options
- Settings > System > Restart (button doesn't exist)
- Developer Tools > Services > homeassistant.restart (service not available)
- Settings > Developer Tools > YAML (restart option not present)

**Reason**: HA version or configuration doesn't expose these options
**Solution**: Use command-line kill method

### 3. Hardcoded /config Path
```bash
sudo cp file.yaml /config/packages/  # FAILED - /config doesn't exist
```
**Reason**: HA process uses `--config /config` flag but actual directory is `~/homeassistant/`
**Solution**: Always use `~/homeassistant/` for this installation

### 4. File Location Discovery Issues
- Assumed ~/.homeassistant (standard HA location)
- Actually ~/homeassistant (non-standard)
- **Solution**: Use `find ~ -name "configuration.yaml" 2>/dev/null` first

---

## How HA is Actually Running

```bash
$ ps aux | grep homeassistant
root 2121817 10.6 13.3 1079696 520376 ? Ssl 17:13 python3 -m homeassistant --config /config
root 187899 0.0 0.0 212 80 ? S s6-supervise home-assistant
```

- **Process Manager**: s6-supervise (not systemd)
- **Config Flag**: `--config /config` (but real location: `~/homeassistant/`)
- **Restart Method**: `sudo kill <PID>` (auto-restarts via s6)
- **User**: root (not demeter)

---

## Steps That Should Be Done Next (Verified Working)

### Step 1: Check Sensor Loading
SSH to RPi and run:
```bash
ps aux | grep "python3 -m homeassistant"
# Should show process is running
```

Then in Home Assistant UI:
- Go to **Settings > Devices & Services**
- Look for entities starting with "Air Quality"
- Should see at least: CO2, Temperature, PM2.5, Humidity, etc.

### Step 2: If Sensors Don't Appear
Check HA logs:
```bash
# On RPi, check if there are any config errors
tail -50 ~/homeassistant/home-assistant.log
```

### Step 3: Add Dashboard
Once sensors are confirmed:
- **Settings > Dashboards > Create**
- Name: "Air Quality Monitor"
- Raw config editor > Paste `homeassistant/dashboards/air_quality_dashboard.yaml`

---

## Configuration File Notes

### Repository Configuration vs Actual Installation

The repo's `homeassistant/configuration.yaml` was **already updated** with packages support, but the user's actual HA installation had a different configuration.yaml.

**Why the mismatch?**
- Repository maintains a "template" configuration
- User's installation has custom modifications (WS3000 sensors, etc.)
- These don't automatically sync

**Solution Going Forward**:
1. Don't assume repo config matches actual installation
2. Always check user's actual configuration first: `grep "packages:" ~/homeassistant/configuration.yaml`
3. Apply only the necessary changes (packages line)
4. Preserve all existing configuration

---

## Troubleshooting Reference

| Problem | Test Command | Solution |
|---------|--------------|----------|
| MQTT not connected | `mosquitto_sub -h YOUR_HA_IP -t "utsensing/#" -C 1` | Check MQTT broker, firewall port 1883 |
| HA won't restart | `ps aux \| grep homeassistant` | Use `sudo kill <PID>`, not systemctl |
| Config file not loading | `grep "packages:" ~/homeassistant/configuration.yaml` | Add line with sed command above |
| Can't find HA config | `find ~ -name configuration.yaml 2>/dev/null` | Then use actual path |
| Sensors show "unavailable" | Check MQTT publisher on Odroid | `ps aux \| grep nanoReader` |

---

## Key Paths (This Installation)

| Item | Path |
|------|------|
| HA Config Directory | `~/homeassistant/` (not `/config` or `~/.homeassistant`) |
| Packages Directory | `~/homeassistant/packages/` |
| Configuration File | `~/homeassistant/configuration.yaml` |
| HA Process | `python3 -m homeassistant --config /config` |
| Supervisor | `s6-supervise home-assistant` |
| Restart Method | `sudo kill <PID>` (auto-restart via s6) |

---

## Deployment Checklist For Next Time

- [ ] Verify MQTT data flowing: `mosquitto_sub -h YOUR_HA_IP -t "utsensing/#" -v -C 5`
- [ ] Find actual HA config: `find ~ -name configuration.yaml 2>/dev/null`
- [ ] Check if packages line exists: `grep "packages:" <config_path>`
- [ ] Create packages directory: `mkdir -p <config_dir>/packages`
- [ ] Copy sensor file: `cp homeassistant/packages/utsensing_sensors.yaml <config_dir>/packages/`
- [ ] Add packages to config: `sed -i '/^homeassistant:$/a\  packages: !include_dir_named packages' <config_path>`
- [ ] Check process manager: `ps aux | grep -E "supervisor|homeassistant"`
- [ ] Restart HA appropriately (systemd vs s6 vs other)
- [ ] Verify sensors in UI: Settings > Devices & Services > MQTT
- [ ] Add dashboard from YAML

---

## Important: What NOT To Do

❌ Don't assume `/config` directory exists
❌ Don't try systemctl restart (use kill <PID> instead)
❌ Don't look for UI options that may not exist (restart, services, etc)
❌ Don't copy repo config directly (it may not match actual installation)
❌ Don't give commands without first verifying actual system state

---

**Status**: Sensors configured, awaiting verification that Home Assistant loaded them successfully.
