# Claude Code Instructions — Air-quality-sensors

This repo is **public** and is the owner's professional calling card.
Keep it clean, professional, and free of any private/personal data.

---

## What This Repo Is

A Raspberry Pi-based home monitoring system featuring:
- **Dog bark detection** — YAMNet TFLite model, iPhone RTSP audio via FFmpeg/ALSA loopback
- **BirdNET bird species detection** — real-time identification via microphone
- **Air quality sensors** — CO₂ (Aranet BLE), weather station (WS3000), and others
- **Home Assistant integration** — MQTT-based sensors, dashboards, automations
- All running as systemd services on Raspberry Pi OS (not HAOS)

---

## NEVER Commit or Push

These things must **never** appear in any commit, branch, or push to this repo:

| What | Why |
|------|-----|
| Anything Anker Solix / solar / battery related | Private, not part of this project |
| `/home/demeter/homeassistant/custom_components/` | Third-party integrations, not ours |
| Full HA config (`/home/demeter/homeassistant/`) | Contains private device data, credentials, and unrelated integrations |
| IP addresses, MAC addresses, passwords, tokens | Security |
| Personal network topology | Security |
| Any credential, secret, or API key | Security |

The `homeassistant/` folder **inside this repo** can contain any HA configs
that are part of this project (audio detection, air quality sensors, weather
station, Z-Wave, BLE sensors, etc.). Just keep out anything Anker Solix
related and anything containing credentials or private device data.

---

## Repo Structure

```
scripts/          Python detectors, shell setup/startup scripts
homeassistant/    HA config for audio detection and sensors ONLY
  packages/       MQTT sensor definitions
  dashboards/     HA dashboard YAML
  automations/    Alert automations
docs/             Setup and reference documentation
firmware/         Microcontroller firmware (air quality sensors)
3DPrints/         Enclosure design files
tasks/            Claude Code task tracking (active + archive)
```

---

## Git Hygiene

- Always work on a feature branch, merge to `main` when complete
- `main` is pushed to the public GitHub — it must always be clean and professional
- Commit messages should be clear and descriptive (they're public)
- The SSH remote is configured: `git@github.com:ericabelson/Air-quality-sensors.git`
- Do not force-push `main`

---

## System Context (Raspberry Pi — hostname: scylla)

- **OS:** Raspberry Pi OS, HA runs as a systemd service (not HAOS)
- **Key services:** `dog_bark_detector`, `iphone-audio-stream`, `audio_startup`,
  `birdnet-analyzer`, `mosquitto`, `caddy`, `zwavejs`, `home-assistant`
- **Audio pipeline:** iPhone Periscope HD app → RTSP → FFmpeg → ALSA loopback
  (`hw:Loopback,0` write, `hw:Loopback,1` read) → PyAudio/YAMNet
- **BLE scanning** requires `bluetoothd --experimental`
  (drop-in: `/etc/systemd/system/bluetooth.service.d/override.conf`)
- **Scripts live at:** `/home/demeter/Air-quality-sensors/scripts/`
- **HA config lives at:** `/home/demeter/homeassistant/` (NOT in this repo)

---

## Known Gotchas

- After reboot, ALSA loopback card number can change — always reference by
  name (`hw:Loopback,X`) not by number (`hw:0,X`)
- PipeWire does not support `module-alsa-source` — do not use PulseAudio
  default source for the bark detector; use direct ALSA loopback instead
- `dog_bark_detector.py` auto-detects the loopback capture device by looking
  for `"Loopback"` + `",1)"` in the PyAudio device name
- iPhone stream requires the Periscope HD app to be actively streaming;
  `iphone-audio-stream.service` pre-checks iPhone reachability with `nc` —
  if unreachable, waits 30s before retry (prevents restart-loop CPU spikes);
  if reachable, ffmpeg launches and systemd retries every 5s on disconnect
