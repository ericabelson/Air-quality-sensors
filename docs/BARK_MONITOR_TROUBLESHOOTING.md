# Dog Bark Monitor — Troubleshooting & Technical Reference

**System:** Raspberry Pi 4 (hostname: scylla), Raspberry Pi OS
**Purpose:** Legal-quality record of neighbor dog barking for potential court proceedings
**Last major overhaul:** 2026-03-02

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Data Files and Legal Quality](#2-data-files-and-legal-quality)
3. [Bark Audio Recordings](#3-bark-audio-recordings)
4. [Common Failure Modes and TRUE Causes](#4-common-failure-modes-and-true-causes)
5. [Diagnostic Procedure — ALWAYS Follow This Order](#5-diagnostic-procedure--always-follow-this-order)
6. [Interpreting Periscope / RTSP Status](#6-interpreting-periscope--rtsp-status)
7. [ALSA Loopback Architecture (The Complicated Part)](#7-alsa-loopback-architecture-the-complicated-part)
8. [Service Dependency Map](#8-service-dependency-map)
9. [What Was Fixed and When](#9-what-was-fixed-and-when)
10. [Boot Behavior After a Crash](#10-boot-behavior-after-a-crash)
11. [Known Recurring Issues](#11-known-recurring-issues)

---

## 1. Architecture Overview

```
iPhone (Periscope HD app, RTSP server on port 8554)
    │
    │  RTSP over TCP (rtsp://192.168.68.106:8554/live.sdp)
    ▼
ffmpeg (iphone-audio-stream.service)
    │  asplit: duplicates audio to two destinations
    ├──► plughw:CARD,0  (ALSA loopback PCM0/sub0)
    │        │
    │        ▼
    │    PCM1/sub0  ──► PulseAudio (BirdNET-Pi recording via arecord)
    │
    └──► loopback_write_bark  (ALSA loopback PCM0/sub1)
             │
             ▼
         PCM1/sub1 (via dsnoop → loopback_cap in /etc/asound.conf)
             │
             ├──► dog_bark_detector.py  (bark detection + CSV logging)
             └──► birdnet_analyzer.py   (bird species detection)
```

**Key files:**
- `/home/demeter/Air-quality-sensors/scripts/dog_bark_detector.py` — main detector
- `/home/demeter/Air-quality-sensors/scripts/start_iphone_stream.sh` — ffmpeg wrapper
- `/home/demeter/Air-quality-sensors/scripts/audio_startup.sh` — loads snd-aloop at boot
- `/etc/asound.conf` — ALSA virtual device definitions (loopback_write_bark, loopback_cap, dsnoop)
- `/etc/systemd/system/iphone-audio-stream.service`
- `/etc/systemd/system/dog_bark_detector.service`
- `/etc/systemd/system/audio_startup.service`

---

## 2. Data Files and Legal Quality

### bark_events_raw.csv
**Location:** `/home/demeter/audio_detection/data/bark_events_raw.csv`

This is the **primary legal record**. It is a self-contained file designed so that
any period without bark rows can be proven to be genuine silence (not a data gap).

**Columns:**
```
timestamp,date,time,confidence,decibels,class,duration_estimate_sec
```

**Row types:**
| class | meaning |
|-------|---------|
| `Dog` | YAMNet detected a dog bark (high confidence) |
| `Domestic animals, pets` | YAMNet detected animal sounds (lower confidence) |
| `MONITOR_START` | System started — monitoring began at this timestamp |
| `MONITOR_STOP` | System shut down — monitoring ended at this timestamp |
| `MONITOR_SILENCE` | Audio stream went silent (pipeline problem, not dog silence) |
| `MONITOR_RESUME` | Audio stream restored after a silence |
| `MONITOR_OFFLINE` | Health monitor declared pipeline broken |
| `MONITOR_NO_DATA` | No audio data received for >30 seconds |
| `MONITOR_HEALTH_DEGRADED` | One or more health checks failing |

**Legal interpretation:**
- A period of only BARK rows with no MONITOR_SILENCE/MONITOR_OFFLINE rows = monitoring was
  active and only the detected barks occurred.
- A MONITOR_SILENCE or MONITOR_OFFLINE row means monitoring was impaired during that window.
  Bark rows (or lack thereof) in that window do NOT prove dogs were or were not barking.
- MONITOR_START / MONITOR_STOP bracket the periods during which data is reliable.

### monitor_uptime.csv
**Location:** `/home/demeter/audio_detection/data/monitor_uptime.csv`
Secondary uptime log. Every monitoring status change is recorded here with event type
and details. Redundant with the MONITOR_* rows in bark_events_raw.csv.

### daily_stats_cache.json
**Location:** `/home/demeter/audio_detection/data/daily_stats_cache.json`
Rolling cache of today's bark statistics. Not a legal record — may not survive restarts.

---

## 3. Bark Audio Recordings

**Location:** `/mnt/usb/bark_audio/recordings/YYYY/MM/DD/bark_YYYY-MM-DD_HH-MM-SS.mp3`
**Format:** MP3 at 32 kbps (smallest size, sufficient quality for voice/bark evidence)
**Storage limit:** 50 GB (rotating FIFO — oldest deleted when limit hit)
**USB drive:** `/dev/sda1`, 477 GB total, mounted at `/mnt/usb`

Recordings are saved for every bark detection event. They capture audio from a few
seconds before the bark (via recording buffer) through the end of the bark episode.

If the USB drive is not mounted, recordings fall back to
`/home/demeter/audio_detection/recordings/` on the SD card.

**For court use:** MP3 recordings are named by date/time and correspond to rows in
bark_events_raw.csv by timestamp. Cross-reference the CSV timestamp with the
recording filename to find the audio for any specific bark event.

---

## 4. Common Failure Modes and TRUE Causes

### ⚠️ CRITICAL: "Periscope is down" is almost NEVER the actual problem

In dozens of troubleshooting sessions spanning weeks, blaming Periscope for the
pipeline failure was wrong nearly every time. The iPhone shows as reachable on
the network; the RTSP server on port 8554 is accessible; Periscope IS running.
The problem is always somewhere in the Pi-side pipeline.

**Do NOT ask the user to check the iPhone or Periscope until ALL Pi-side checks pass.**

---

### Failure: "Invalid data found when processing input" (ffmpeg RTSP error)
**TRUE cause:** Periscope is open on the phone (port 8554 responds) but is NOT
actively streaming. The RTSP session URL exists but no stream is active.
**This is one of the rare cases where Periscope/iPhone IS the issue** — specifically,
the Periscope app needs to have an active live stream running, not just be open.
**Fix:** Open Periscope on the iPhone and ensure the stream is live.

**How to verify:** `nc -z 192.168.68.106 8554` exits 0 (port open) but ffmpeg fails
with "Invalid data" rather than "Connection refused".

---

### Failure: "Connection refused" on port 8554
**TRUE cause:** Periscope app is completely closed on the iPhone.
**Fix:** Open Periscope on the iPhone.
**How to verify:** `nc -z 192.168.68.106 8554` exits 1.

---

### Failure: ffmpeg crashes with `snd_pcm_close: Assertion 'pcm' failed` (ABORT signal)
**TRUE cause:** `hw:CARD,0` ALSA output failed format negotiation (wrong sample rate
or channel count) because BirdNET/PulseAudio already locked the loopback to a
different format. `hw:` does not handle format mismatches gracefully — it tries to
close a partially-configured device and hits an assertion in the ALSA library.
**Fix (applied 2026-03-02):** Use `plughw:` instead of `hw:` in start_iphone_stream.sh.
`plughw:` handles format conversion and never crashes on mismatch.
**Periscope was fine every time this happened.**

---

### Failure: Bark detector shows "No real audio" / silence for extended periods
**TRUE cause (most common):** PulseAudio auto-detected the ALSA loopback and grabbed
PCM1/subdevice-0 exclusively at 44100 Hz stereo. The bark detector was using the same
subdevice and got locked out, or received format-mismatched audio (which sounds like
silence to the classifier).
**Fix (applied 2026-03-02):** ffmpeg now writes to TWO loopback subdevices simultaneously
via `asplit`. sub0 is dedicated to PulseAudio/BirdNET, sub1 is dedicated to the bark
detector via dsnoop. They no longer compete.
**Periscope was fine every time this happened.**

---

### Failure: Health monitor floods logs with "ALSA closed — auto-restarting" every 30s
**TRUE cause:** The health monitor detected that the loopback playback side was closed
(no ffmpeg writing to it) and restarted iphone-audio-stream. If ffmpeg itself can't
connect (Periscope not streaming), it exits immediately each time, and the health
monitor keeps restarting it in an infinite 30-second loop.
**How to distinguish from a real Periscope problem:** Check ffmpeg logs — "Invalid data"
means Periscope is open but not streaming; "Connection refused" means app is closed.
**If neither error appears** and ffmpeg runs for >10 seconds before being killed by the
health monitor, the problem is ALSA-side.

---

### Failure: Pi becomes completely unresponsive (red LED, intermittent green LED)
**TRUE cause:** Kernel panic, OOM kill, or undervoltage (power supply issue).
**Red LED on Pi:** Typically undervoltage — the power supply or USB-C cable is inadequate.
**Intermittent green LED:** Disk activity during a troubled/hung state.
**Recovery:** Power cycle the Pi.
**After recovery:** Check `vcgencmd get_throttled` — `0x0` means no undervoltage THIS boot.
The previous boot's cause is only recoverable from the system journal if persistent
journaling is enabled. Persistent journaling was enabled 2026-03-02.
**To check previous boot:** `journalctl -b-1` (only works if system was not powered off
uncleanly — a hard power cut does not preserve the current journal buffer).

---

### Failure: "loopback_cap device not found" / bark detector falls back to raw hw:Loopback,1
**TRUE cause:** The dsnoop virtual device in /etc/asound.conf failed to initialize,
usually because it was configured for `channels 1` but the loopback was already locked
to stereo by PulseAudio. When dsnoop fails, loopback_cap (which wraps dsnoop) also
fails to appear in PyAudio's device list.
**Fix (applied 2026-03-02):** Dedicated sub1 for the bark detector — PulseAudio only
ever touches sub0, so dsnoop on sub1 always initializes successfully.

---

## 5. Diagnostic Procedure — ALWAYS Follow This Order

When the bark detector is not detecting / reporting silence:

**Step 1 — Is the Raspberry Pi up?**
```bash
ping -c 2 192.168.68.106   # First ping the iPhone to confirm network works
ping -c 2 <PI_IP>           # Then ping the Pi
```

**Step 2 — Is the iphone-audio-stream service running and healthy?**
```bash
systemctl status iphone-audio-stream
journalctl -u iphone-audio-stream --no-pager -n 30
```

**Step 3 — What is ffmpeg's exact error?**
Look for:
- `Invalid data found when processing input` → Periscope open but not streaming (rare actual Periscope issue)
- `Connection refused` on port 8554 → Periscope app closed
- `snd_pcm_close: Assertion 'pcm' failed` → ALSA format mismatch (Pi-side problem)
- `cannot set channel count` or `sample rate X not available` → ALSA format mismatch (Pi-side)
- ffmpeg running with no error → audio is flowing; check bark detector side

**Step 4 — Is the loopback running at the right format?**
```bash
cat /proc/asound/card0/pcm0p/sub0/hw_params   # ffmpeg's write side (sub0)
cat /proc/asound/card0/pcm0p/sub1/hw_params   # ffmpeg's write side (sub1, bark detector)
cat /proc/asound/card0/pcm1c/sub1/hw_params   # bark detector's read side
```

**Step 5 — Is the bark detector using loopback_cap (not raw hw:)?**
```bash
journalctl -u dog_bark_detector --no-pager -n 5 | grep "Using"
```
Should show: `Using shared loopback capture [20] loopback_cap`
If it shows `(dsnoop not found)` and raw hw:, see ALSA section below.

**Step 6 — Check who has the loopback subdevices:**
```bash
cat /proc/asound/card0/pcm1c/sub0/status   # PulseAudio should own this
cat /proc/asound/card0/pcm1c/sub1/status   # bark detector's dsnoop should own this
```

**Step 7 — Is the iPhone reachable and is port 8554 open?**
```bash
ping -c 2 192.168.68.106
nc -z 192.168.68.106 8554 && echo "PORT OPEN" || echo "PORT CLOSED"
```
Only ask the user to check the iPhone if port 8554 is CLOSED or if ping fails.

---

## 6. Interpreting Periscope / RTSP Status

| Network state | Port 8554 | ffmpeg error | Meaning | Action |
|--------------|-----------|--------------|---------|--------|
| Phone pingable | Open | "Invalid data found" | Periscope app open but stream not active | Ask user to start stream |
| Phone pingable | Closed | "Connection refused" | Periscope app completely closed | Ask user to open Periscope |
| Phone not pingable | N/A | Timeout/connect failed | Phone off WiFi or powered off | Ask user to check phone |
| Phone pingable | Open | No error, ffmpeg runs | Stream is live ✓ | No action needed |
| Phone pingable | Open | ALSA assertion crash | Stream live but Pi-side ALSA problem | Fix Pi-side, NOT Periscope |
| **Port times out, ALL ports on phone time out, mDNS works** | **Times out** | **Timeout** | **Router AP isolation blocking WiFi-to-WiFi TCP** | **Check Eero router settings** |

**Rule:** Port 8554 open = Periscope IS running. "Invalid data" = stream not active.
These are different conditions. Reporting "Periscope not open" when port 8554 IS open
is misleading — the app is open, just not streaming.

### Eero Mesh Backhaul Failure (2026-03-03 confirmed root cause)

**Symptom:** All TCP ports on the iPhone timeout. mDNS still works (Periscope visible via
`avahi-browse -r _peristream._tcp`). Pi can reach SOME devices on the LAN (e.g. one Sonos)
but not others (iPhone, other Sonos). Pattern: reachable devices are on one Eero node;
unreachable devices are on a different Eero node whose mesh backhaul is broken.

**Cause:** The Eero mesh backhaul between nodes breaks — typically after a node reboots
for a firmware update (Eero auto-updates 1–4 AM) and fails to re-establish the inter-node
link. Unicast TCP between devices on different nodes is silently dropped. mDNS (multicast)
still works because it's propagated differently across the mesh. The result looks exactly
like AP isolation but is actually a routing failure within the Eero mesh.

**Key diagnostic: test multiple devices, not just the iPhone**
```bash
# Test TCP to several LAN devices — if SOME work and SOME don't, it's mesh routing
python3 -c "
import socket, select
for ip,port,label in [('192.168.68.106',8554,'iPhone'),('192.168.68.107',1400,'Ickyah'),('192.168.68.108',1400,'Diurnal')]:
    s=socket.socket(); s.setblocking(False); s.connect_ex((ip,port))
    r,w,e=select.select([],[s],[s],2)
    print(label, 'CONNECTED' if w and s.getsockopt(socket.SOL_SOCKET,socket.SO_ERROR)==0 else 'REFUSED' if w else 'TIMEOUT')
    s.close()
"

# Check which Eero node the Pi is on
iw dev wlan0 link | grep Connected
```

**Fix — Pi-side (immediate, no router access needed):**
```bash
wpa_cli -i wlan0 reassociate   # Reconnects Pi to a (hopefully working) Eero node
sudo systemctl restart iphone-audio-stream  # Reconnect ffmpeg
```

**Fix — router-side (permanent):** Power-cycle the Eero node(s) that lost their backhaul,
or reboot all Eero nodes from the Eero app to force a clean mesh re-establishment.

**Why the "reassociate" trick works:** Each Eero node has its own BSSID. `wpa_cli reassociate`
causes the Pi to roam to whichever node has the strongest signal. If that node has a working
backhaul, all devices become reachable again. If Diurnal Sonos becomes unreachable after
reassociation but the iPhone becomes reachable, that confirms mesh routing is the cause.

---

## 7. ALSA Loopback Architecture (The Complicated Part)

### Why this is hard

`snd-aloop` (the Linux ALSA loopback kernel module) creates virtual sound card(s) where
audio written to the playback side can be read from the capture side. The format (sample
rate, channels, bit depth) of each subdevice is locked by the first process to open it.
Multiple processes competing to open the loopback in incompatible formats causes silent
failures or crashes.

**In this system, three things need audio from the loopback:**
1. BirdNET-Pi (via PulseAudio → `arecord`) — opens at 44100 Hz stereo
2. Dog bark detector (PyAudio) — wants 16000 Hz mono
3. BirdNET analyzer service — wants 48000 Hz mono

**PulseAudio's behavior** makes this especially tricky: `module-udev-detect` auto-detects
ALL ALSA sound cards including the loopback and opens PCM1/sub0 at 44100 Hz stereo.
This happens at PulseAudio startup, which races with iphone-audio-stream startup.

### The solution (as of 2026-03-02)

ffmpeg writes to **two separate loopback subdevices** simultaneously:
- **sub0** → PulseAudio reads from PCM1/sub0 (for BirdNET-Pi recording)
- **sub1** → bark detector + birdnet_analyzer read from PCM1/sub1 via dsnoop

`plughw:` on the write side handles whatever format PulseAudio has locked sub0 to.
`dsnoop` on the read side shares sub1 between bark detector and birdnet_analyzer.
`loopback_cap` wraps dsnoop with a `plug:` converter so each reader can request its
preferred rate (16 kHz or 48 kHz) and ALSA resamples transparently.

### asound.conf devices

| Name | Type | Purpose |
|------|------|---------|
| `loopback_write_bark` | `plug` → `hw:Loopback,0,1` | ffmpeg's second output (PCM0/sub1 write) |
| `loopback_share` | `dsnoop` on `hw:Loopback,1,1` | Shared capture from PCM1/sub1 |
| `loopback_cap` | `plug` → `loopback_share` | Format-converting capture for bark detector |

All use **card name** `Loopback` (not a number) so they survive reboots where the
card number changes.

---

## 8. Service Dependency Map

```
sound.target
    └── audio_startup.service  (loads snd-aloop, writes /run/audio_loopback_card)
            └── iphone-audio-stream.service  (ffmpeg: RTSP→ALSA loopback sub0+sub1)
                    └── dog_bark_detector.service  (PyAudio via loopback_cap/sub1)

[parallel, no ordering]
    └── birdnet_recording.service  (PulseAudio/arecord from loopback sub0)
    └── birdnet_analyzer.service   (PyAudio via loopback_cap/sub1)
```

`birdnet_recording` has no ordering constraint relative to `audio_startup` — it races.
This is intentional: even if PulseAudio grabs sub0 first at 44100 stereo, ffmpeg's
`plughw:` output handles the format mismatch and sub1 is always free for the bark detector.

---

## 9. What Was Fixed and When

### 2026-03-03 — Eero mesh backhaul failure + WiFi auto-recovery

**Problem:** Audio stream dropped at ~1:26 AM and could not reconnect despite Periscope
running and the iPhone being on WiFi. All TCP connections to the iPhone timed out, but
mDNS still worked. iOS system ports (AirPlay 7000, lockdown 62078) also timed out —
ruling out any app-level or phone-side cause.

**Root cause:** One of three Eero WiFi nodes (`BSSID 42:84:6A:02:16:0F`) had a broken
mesh backhaul. Traffic between devices on different nodes was silently dropped. The Pi
kept gravitating to this node because it was 3 dBm stronger than the working nodes.
Multicast (mDNS, ARP) still worked because Eero propagates it differently. Unicast TCP
was completely blocked between devices on different nodes. The broken node was most likely
caused by an overnight Eero firmware update that caused one node to reboot and fail to
re-establish its inter-node backhaul link cleanly.

**Diagnosis method:**
```bash
# Test TCP to multiple LAN devices — if SOME work and SOME don't, it's mesh routing
# (not the phone, not Periscope, not the Pi software)
python3 -c "
import socket, select
for ip,port,label in [('192.168.68.106',8554,'iPhone'),('192.168.68.107',1400,'Ickyah'),('192.168.68.108',1400,'Diurnal')]:
    s=socket.socket(); s.setblocking(False); s.connect_ex((ip,port))
    r,w,e=select.select([],[s],[s],2)
    print(label, 'CONNECTED' if w and s.getsockopt(socket.SOL_SOCKET,socket.SO_ERROR)==0 else 'TIMEOUT')
    s.close()
"
# Some working (Diurnal Sonos) and some not (iPhone, Ickyah Sonos) = mesh fault

# Force Pi to roam to a different Eero node
wpa_cli -i wlan0 scan && sleep 3 && wpa_cli -i wlan0 scan_results | grep "42:84:6a"
wpa_cli -i wlan0 roam <good-bssid>  # pick a node that works
sudo systemctl restart iphone-audio-stream
```

**Fixes applied:**
1. WiFi BSSID pinned to working node via NetworkManager (survives reboots):
   ```bash
   sudo nmcli connection modify crotalus 802-11-wireless.bssid 42:84:6A:02:1A:83
   sudo nmcli connection up crotalus
   ```
2. Auto-recovery added to health monitor (`dog_bark_detector.py`): after 4 consecutive
   cycles of "ALSA closed + phone unreachable" (= 2 minutes), the health monitor now
   automatically calls `wpa_cli reassociate` to attempt a node hop, then restarts ffmpeg.
   Constants: `WIFI_REASSOC_COOLDOWN_SECONDS=300`, `WIFI_REASSOC_AFTER_CYCLES=4`.

**Permanent fix needed:** Power-cycle all Eero nodes (or restart via Eero app) to force
the broken node to re-establish its mesh backhaul. After that, remove the BSSID pin:
```bash
sudo nmcli connection modify crotalus 802-11-wireless.bssid ""
sudo nmcli connection up crotalus
```

**Why this was so hard to diagnose:**
- mDNS confirmed Periscope was running → looked like Periscope was at fault
- Ping to iPhone failed (iOS blocks ICMP) → looked like iPhone offline
- But ALL ports on the iPhone timed out (including iOS system ports) → not the phone
- Only after testing TCP to multiple devices revealed the pattern (some work, some don't)
  was the Eero mesh routing identified as the cause

---

### 2026-03-02 — Major pipeline overhaul

**Problem:** After an ~18-hour Pi outage (cause unknown, likely power issue), the
audio pipeline came back broken. ffmpeg was crashing every 30 seconds with:
```
snd_pcm_close: Assertion 'pcm' failed
```
PulseAudio had auto-locked the loopback to 44100 Hz stereo, and ffmpeg's `hw:` ALSA
output can't handle format negotiation failures — it tries to close a partially-open
device and hits an assertion in the ALSA library (pcm.c line 779).

**Fixes applied:**

1. **`hw:` → `plughw:` in start_iphone_stream.sh**
   `plughw:` negotiates format with whatever the loopback is running at and converts
   transparently. No more assertion crashes on format mismatch.

2. **Dual loopback subdevice split in ffmpeg**
   Added `asplit` filter: ffmpeg now writes to both `plughw:CARD,0` (sub0, for PulseAudio)
   and `loopback_write_bark` (sub1, for bark detector). Eliminates the race condition
   where PulseAudio's exclusive hold on sub0 prevented the bark detector from getting audio.

3. **Updated `/etc/asound.conf`**
   `loopback_share` dsnoop now uses `hw:Loopback,1,1` (sub1) instead of sub0.
   Added `loopback_write_bark` device for ffmpeg's sub1 write path.

4. **Enabled persistent systemd journal**
   `/etc/systemd/journald.conf.d/persistent.conf` with `Storage=persistent`,
   300 MB cap, 2-week retention. Future crashes will have their logs available
   in `journalctl -b-1`.

5. **Monitoring status rows in bark_events_raw.csv**
   `MONITOR_START`, `MONITOR_STOP`, `MONITOR_SILENCE`, `MONITOR_RESUME` etc. rows
   are now written to the main bark CSV alongside bark detections. This makes the
   CSV a self-contained legal record.

6. **Recording size limit: 2 GB → 50 GB**
   `MAX_RECORDING_MB` changed from 2000 to 50000. The USB drive has 434 GB free;
   50 GB provides ~3500 hours of bark-event MP3 recordings at 32 kbps.

---

## 10. Boot Behavior After a Crash

After a Pi reboot, the pipeline should come up automatically:

1. `audio_startup.service` runs (oneshot) — loads `snd-aloop`, detects card number,
   writes to `/run/audio_loopback_card`
2. `iphone-audio-stream.service` starts — ffmpeg reads card number, opens RTSP,
   opens both loopback subdevices
3. `dog_bark_detector.service` starts — finds `loopback_cap`, opens audio stream
4. If Periscope is not streaming when ffmpeg starts: ffmpeg exits with "Invalid data",
   systemd restarts it every 5 seconds, bark detector detects silence and logs
   `MONITOR_SILENCE` to CSV. This is correct — it faithfully records that monitoring
   was impaired.
5. When Periscope stream comes back: ffmpeg connects on next retry, audio flows to
   both loopback subdevices, bark detector resumes and logs `MONITOR_RESUME`.

---

## 11. Known Recurring Issues

### Periscope stream drops overnight
The Periscope stream sometimes stops (iOS screen lock, background app refresh killing
the app, etc.). ffmpeg retries every 5 seconds. Monitoring is logged as SILENCE during
the gap. **This is expected behavior, not a bug.**

### Pi undervoltage / spontaneous reboots
The red LED on the Pi indicates undervoltage. The Pi 4 requires a 5V/3A USB-C supply.
Low-quality cables or supplies cause random crashes especially under load.
Check the power supply if reboots happen frequently.

### Health monitor "ALSA closed" restart loop
If the iPhone is not streaming and ffmpeg fails immediately on each retry, the health
monitor also triggers restarts every 30 seconds. This creates log spam but is harmless
— the monitor correctly identifies that audio isn't flowing and tries to recover.

### BirdNET bird detections during no-audio periods
When the loopback has no audio (silence/dead air), BirdNET sometimes detects "Brahminy
Kite" or other false positives from the ambient noise floor. These are not real birds.
Real detections should have confidence > 0.7 and occur alongside real audio events.
