# Task 04: Fix Wrong Usernames and Paths in HA Config and Service Scripts

**Priority:** MEDIUM
**Estimated effort:** Small (search and replace)
**Type:** Bug fix - correct hardcoded paths

---

## System Context

You are working on a Raspberry Pi-based audio detection system. The user accesses
the Pi via SSH and you are running in a separate Claude Code environment connected
to the git repo. You CANNOT run commands on the Pi directly - you must give the
user commands to copy/paste.

### Architecture
- Raspberry Pi hostname: "scylla", username: "demeter"
- Home Assistant is also running (possibly as Docker container or native)
- Systemd services run the detector and audio stream
- The git repo is cloned at `~/Air-quality-sensors` on the Pi

### User Preferences
- **Combine as many commands as possible** into single copy-paste blocks
- Make it as easy as possible on the user
- After making changes, commit, push, and give the user a single command to pull and restart

---

## The Bug

Multiple files reference the wrong username and home directory:
- Scripts use `User=pi` and `/home/pi/` but the actual Pi user is `demeter`
- HA automation shell commands reference `/home/pi/audio_detection/venv/bin/python3`
- The file logger path references `/home/pi/`

**IMPORTANT:** This is a public repo intended for a wide audience, not just this one Pi.
The fix should make paths configurable or use variables/relative paths where possible,
rather than hardcoding "demeter" everywhere.

---

## Files to Fix

### 1. `scripts/create_services.sh`

**Lines 38-41 (dog_bark_detector.service):**
```
User=pi
WorkingDirectory=/home/pi/audio_detection
ExecStart=/home/pi/audio_detection/venv/bin/python3 /home/user/Air-quality-sensors/scripts/dog_bark_detector.py
```

**Fix:** Add a configurable user variable at the top of the script and use it:

At the top of the script (after `set -e`), add:
```bash
# Configurable: Set these for your Pi
PI_USER="${PI_USER:-$(whoami)}"
PI_HOME="${PI_HOME:-/home/$PI_USER}"
```

Then replace all `User=pi` with `User=$PI_USER` and `/home/pi/` with `$PI_HOME/`
throughout the file. Same for the CSV export service and iphone-audio-stream service.

**Also fix line 159:** The `User=pi` in the iphone-audio-stream service section.

### 2. `scripts/setup_iphone_audio.sh`

**Line 159:** `User=pi` in the systemd service template.

**Fix:** Same approach - add `PI_USER` variable and use it.

### 3. `homeassistant/automations/audio_alerts.yaml`

**Lines 302-309 (shell_command section):**
```yaml
shell_command:
  export_csv_daily: >
    /home/pi/audio_detection/venv/bin/python3
    /home/user/Air-quality-sensors/scripts/csv_exporter.py --all
  generate_weekly_report: >
    /home/pi/audio_detection/venv/bin/python3
    /home/user/Air-quality-sensors/scripts/csv_exporter.py --weekly
```

**Fix:** Change `/home/pi/audio_detection/venv/bin/python3` to just `python3`
(the system Python should work, or the venv can be activated in the command).
If the venv is needed, use a more generic path or add a comment explaining
the user should update the path:

```yaml
shell_command:
  # Update paths below to match your Pi's username and venv location
  export_csv_daily: >
    python3 /home/user/Air-quality-sensors/scripts/csv_exporter.py --all
  generate_weekly_report: >
    python3 /home/user/Air-quality-sensors/scripts/csv_exporter.py --weekly
```

**Lines 326-328 (notify file_logger):**
```yaml
notify:
  - name: file_logger
    platform: file
    filename: /home/pi/audio_detection/logs/events.log
```

**Fix:** This is HA-specific config that runs on the HA host. If HA runs on the Pi:
```yaml
notify:
  - name: file_logger
    platform: file
    filename: /var/log/audio_detection_events.log
```

Or use a path relative to HA's config directory. Add a comment noting the user
should adjust the path.

### 4. `homeassistant/dashboards/audio_detection_dashboard.yaml`

**Lines 481 and 496:** References to `pi@<your-pi-ip>` and `ssh pi@...`

**Fix:** Change to generic placeholders:
```
ssh <your-username>@<your-pi-ip>
scp <your-username>@<your-pi-ip>:...
```

---

## Important Note

Do NOT hardcode "demeter" as a replacement for "pi". The repo is public and should
work for any user. Use variables in scripts and generic placeholders in documentation.

The user can set the variable when running scripts:
```bash
PI_USER=demeter ./create_services.sh
```

---

## Verification

After making changes, search the entire repo for remaining `/home/pi` references:

```bash
grep -r "/home/pi" --include="*.sh" --include="*.yaml" --include="*.py" .
```

This should return zero results (or only results in `tasks/` docs and `docs/` guides
that explain what to configure).

---

## When This Task Is Complete

```bash
git mv tasks/active/04-fix-ha-config-wrong-paths.md tasks/archive/
git add -A tasks/
git commit -m "Archive task 04: fixed hardcoded paths and usernames"
git push
```

Give the user a combined command to pull and recreate services:
```bash
cd ~/Air-quality-sensors && git pull && echo "To recreate services with your username:" && echo "PI_USER=demeter bash scripts/create_services.sh"
```
