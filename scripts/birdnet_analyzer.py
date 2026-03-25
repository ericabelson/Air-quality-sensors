#!/usr/bin/env python3
"""
BirdNET Real-Time Analyzer
===========================

Detects bird species using BirdNET-Analyzer via birdnetlib.
Records audio from PulseAudio, analyzes each 3-second segment,
and publishes detections to MQTT for Home Assistant.

Shares the same PulseAudio default source as dog_bark_detector.py.
PulseAudio handles fan-out so both scripts read simultaneously
without conflict — each gets its own resampled copy.

Architecture:
  iPhone → RTSP → ffmpeg → snd-aloop → PulseAudio default source
                                          ├→ dog_bark_detector.py (16 kHz)
                                          └→ birdnet_analyzer.py  (48 kHz)

Features:
- Real-time bird species identification via BirdNET TFLite model
- Location-based species filtering (narrows to regionally likely birds)
- MQTT publishing matching existing HA audio_detection package
- Daily species and detection tracking with CSV logging
- Health/uptime monitoring (publishes online/offline status)
- Optional audio recording of bird detections
- FIFO storage cleanup (configurable cap)

Requirements:
  pip install birdnetlib pyaudio paho-mqtt numpy

Author: Claude Code
License: MIT
"""

import sys
import os
import time
import json
import wave
import tempfile
import logging
import threading
from datetime import datetime, date, timedelta
from collections import defaultdict
import numpy as np

# Audio
try:
    import pyaudio
except ImportError:
    print("Error: pyaudio not installed. Run: pip install pyaudio")
    sys.exit(1)

# MQTT
try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: paho-mqtt not installed. Run: pip install paho-mqtt")
    sys.exit(1)

# BirdNET
try:
    from birdnetlib import Recording
    from birdnetlib.analyzer import Analyzer
except ImportError:
    print("Error: birdnetlib not installed. Run: pip install birdnetlib")
    print("  (This will also install BirdNET-Analyzer and download the model.)")
    sys.exit(1)

# HTTP (for Wikipedia photo lookup — optional, gracefully degraded if missing)
try:
    import requests as _requests
except ImportError:
    _requests = None


# ============================================================================
# CONFIGURATION
# ============================================================================

# Audio Settings
# BirdNET's native sample rate is 48 kHz.  PulseAudio resamples from
# the loopback device rate automatically.
SAMPLE_RATE = 48000
CHANNELS = 1
AUDIO_DEVICE_INDEX = None   # None = PulseAudio default source (shared)
CHUNK_DURATION_SEC = 3.0    # BirdNET default analysis window

# How long to wait between analysis cycles.
# 0 = back-to-back (best detection, higher CPU).
# 12 = analyze 3 s every 15 s (light CPU, still good coverage).
ANALYSIS_GAP_SEC = float(os.environ.get('BIRDNET_GAP', '0'))

# Detection Settings
MIN_CONFIDENCE = float(os.environ.get('BIRDNET_MIN_CONF', '0.25'))

# Location — BirdNET uses lat/lon + date to filter species likely present
# in your region at this time of year.  Set via env vars or edit here.
# If left at 0/0 BirdNET still works but won't filter by region.
LATITUDE = float(os.environ.get('BIRDNET_LAT', '30.2672'))
LONGITUDE = float(os.environ.get('BIRDNET_LON', '-97.7431'))

# MQTT Settings (same broker as dog_bark_detector.py)
MQTT_BROKER = os.environ.get('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', '1883'))
MQTT_TOPIC_DETECTION = "birdnet/detection"
MQTT_TOPIC_STATS = "birdnet/stats"
MQTT_TOPIC_STATUS = "birdnet/status"
MQTT_TOPIC_MONITOR_ACTIVE = "birdnet/monitor_active"
MQTT_TOPIC_RECENT_BIRDS = "birdnet/recent_birds"  # Retained JSON for photo gallery

# File Paths
BASE_DIR = os.path.expanduser("~/audio_detection")
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Optional bird audio recordings
SAVE_BIRD_AUDIO = True
BIRD_RECORDING_DIR = os.path.join(BASE_DIR, "bird_recordings")
MAX_BIRD_RECORDING_MB = 500  # FIFO cap for bird recordings

# CSV log of every detection
BIRD_DETECTIONS_CSV = os.path.join(DATA_DIR, "bird_detections.csv")

# Bird photo cache — persists Wikipedia thumbnail URLs across restarts
BIRD_PHOTO_CACHE_FILE = os.path.join(DATA_DIR, "bird_photo_cache.json")

# Recent birds list — how many unique species to track for the dashboard gallery
RECENT_BIRDS_MAX = 10

# Wikipedia REST API for species photo lookup (no API key required)
_WIKIPEDIA_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
_PHOTO_FETCH_TIMEOUT = 6  # seconds per request

# Silence / health thresholds (consistent with dog_bark_detector.py)
SILENCE_THRESHOLD_DB = 32
SILENCE_ALERT_SECONDS = 60

# Watchdog — how long (seconds) stream.read() is allowed to block before we
# consider the audio device frozen and force-reopen it.
WATCHDOG_TIMEOUT_SEC = 45
# How often the watchdog thread wakes to check (should be < WATCHDOG_TIMEOUT_SEC)
WATCHDOG_POLL_SEC = 10

# Create directories
for _d in [LOG_DIR, DATA_DIR]:
    os.makedirs(_d, exist_ok=True)
if SAVE_BIRD_AUDIO:
    os.makedirs(BIRD_RECORDING_DIR, exist_ok=True)

# Logging
log_file = os.path.join(LOG_DIR, f"birdnet_analyzer_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# DAILY STATS TRACKER
# ============================================================================

class BirdDetectionTracker:
    """Tracks daily bird detection statistics.

    Recovers today's counts from the CSV on startup so that reboots
    don't zero out the dashboard mid-day.
    """

    def __init__(self):
        self._reset()
        self._recover_from_csv()

    def _reset(self):
        self.today = date.today()
        self.species_seen = set()
        self.total_detections = 0
        self.detections_by_species = defaultdict(int)

    def _recover_from_csv(self):
        """Re-read today's detections from the CSV so restarts keep counts."""
        today_str = self.today.isoformat()
        try:
            with open(BIRD_DETECTIONS_CSV, 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 4 and parts[1] == today_str:
                        common_name = parts[3]
                        self.species_seen.add(common_name)
                        self.total_detections += 1
                        self.detections_by_species[common_name] += 1
            if self.total_detections > 0:
                logger.info(
                    f"Recovered {self.total_detections} detections, "
                    f"{len(self.species_seen)} species from CSV for {today_str}"
                )
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"CSV recovery error: {e}")

    def _check_new_day(self):
        if date.today() != self.today:
            logger.info(f"New day — resetting stats.  Yesterday: "
                        f"{self.total_detections} detections, "
                        f"{len(self.species_seen)} species")
            self._reset()

    def add_detection(self, common_name):
        self._check_new_day()
        self.species_seen.add(common_name)
        self.total_detections += 1
        self.detections_by_species[common_name] += 1

    def get_stats(self):
        self._check_new_day()
        return {
            'date': self.today.isoformat(),
            'species_count': len(self.species_seen),
            'total_detections': self.total_detections,
        }


# ============================================================================
# MQTT CLIENT
# ============================================================================

class MQTTPublisher:
    """Thin MQTT wrapper — same pattern as dog_bark_detector.py."""

    def __init__(self, broker, port):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()
        self.connected = False
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        # Last-will so HA immediately knows if we crash
        self.client.will_set(
            MQTT_TOPIC_STATUS,
            json.dumps({'status': 'offline', 'timestamp': datetime.now().isoformat()}),
            qos=1, retain=True
        )

        try:
            self.client.connect(broker, port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"MQTT connect error: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self.connected = True
            self.publish_status("online")
        else:
            logger.error(f"MQTT connection failed (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        logger.warning("Disconnected from MQTT broker")
        self.connected = False

    def publish(self, topic, payload, retain=False):
        if not self.connected:
            return
        try:
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            self.client.publish(topic, payload, retain=retain)
        except Exception as e:
            logger.error(f"MQTT publish error: {e}")

    def publish_status(self, status):
        # Retain=True so HA gets the correct state after restart, not just the LWT "offline"
        self.publish(MQTT_TOPIC_STATUS, {
            'status': status,
            'timestamp': datetime.now().isoformat()
        }, retain=True)

    def publish_monitor_active(self, active):
        # Retain=True so HA knows monitor state even if it restarts between publishes
        self.publish(MQTT_TOPIC_MONITOR_ACTIVE, {
            'active': active,
            'timestamp': datetime.now().isoformat()
        }, retain=True)

    def publish_detection(self, common_name, scientific_name, confidence):
        self.publish(MQTT_TOPIC_DETECTION, {
            'timestamp': datetime.now().isoformat(),
            'common_name': common_name,
            'scientific_name': scientific_name,
            'confidence': confidence,
        })

    def publish_stats(self, stats):
        self.publish(MQTT_TOPIC_STATS, stats, retain=True)

    def disconnect(self):
        self.publish_status("offline")
        self.publish_monitor_active(False)
        self.client.loop_stop()
        self.client.disconnect()


# ============================================================================
# AUDIO HELPERS
# ============================================================================

def calculate_rms_db(audio_data):
    """Calculate approximate dB from int16 samples (same formula as dog bark detector)."""
    rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
    if rms < 1e-10:
        return 0
    db = 20 * np.log10(rms / 32768.0) + 90
    return max(0, min(120, db))


def save_wav(audio_data, path, sample_rate=SAMPLE_RATE):
    """Write int16 audio to a WAV file."""
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())


# ============================================================================
# CSV LOGGER
# ============================================================================

def init_csv():
    if not os.path.exists(BIRD_DETECTIONS_CSV):
        with open(BIRD_DETECTIONS_CSV, 'w') as f:
            f.write("timestamp,date,time,common_name,scientific_name,confidence\n")
        logger.info(f"Created bird detection CSV: {BIRD_DETECTIONS_CSV}")


def log_detection_csv(common_name, scientific_name, confidence):
    try:
        now = datetime.now()
        with open(BIRD_DETECTIONS_CSV, 'a') as f:
            f.write(f"{now.isoformat()},{now.strftime('%Y-%m-%d')},"
                    f"{now.strftime('%H:%M:%S')},{common_name},"
                    f"{scientific_name},{confidence:.3f}\n")
    except Exception as e:
        logger.error(f"CSV write error: {e}")


# ============================================================================
# STORAGE CLEANUP
# ============================================================================

def cleanup_bird_recordings():
    """Delete oldest bird recordings when over the storage cap (FIFO)."""
    if not SAVE_BIRD_AUDIO:
        return
    try:
        files = []
        total_bytes = 0
        for root, _, filenames in os.walk(BIRD_RECORDING_DIR):
            for fn in filenames:
                if fn.endswith('.wav'):
                    fp = os.path.join(root, fn)
                    sz = os.path.getsize(fp)
                    files.append((fp, os.path.getmtime(fp), sz))
                    total_bytes += sz

        max_bytes = MAX_BIRD_RECORDING_MB * 1024 * 1024
        if total_bytes > max_bytes:
            files.sort(key=lambda x: x[1])  # oldest first
            freed = 0
            target = total_bytes - max_bytes + (max_bytes * 0.1)
            for fp, _, sz in files:
                if freed >= target:
                    break
                os.remove(fp)
                freed += sz
            logger.info(f"Bird recording cleanup: freed {freed / 1024 / 1024:.1f} MB")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


# ============================================================================
# BIRD PHOTO CACHE
# ============================================================================

class BirdPhotoCache:
    """Fetches and caches Wikipedia thumbnail URLs for bird species.

    Lookups happen in background threads so the detection loop is never
    blocked by a network request.  Results are persisted to disk so the
    cache survives service restarts.
    """

    def __init__(self):
        self._cache = {}          # {scientific_name_lower: url_or_empty_string}
        self._pending = set()     # species currently being fetched
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        try:
            if os.path.exists(BIRD_PHOTO_CACHE_FILE):
                with open(BIRD_PHOTO_CACHE_FILE) as f:
                    self._cache = json.load(f)
                logger.info(f"Bird photo cache loaded ({len(self._cache)} species)")
        except Exception as e:
            logger.warning(f"Could not load bird photo cache: {e}")

    def _save(self):
        try:
            with open(BIRD_PHOTO_CACHE_FILE, 'w') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save bird photo cache: {e}")

    def get_photo_url(self, common_name, scientific_name):
        """Return a cached photo URL, or '' while a background fetch is in progress.

        On the first detection of a new species the URL is '', but subsequent
        detections (and the next MQTT publish) will include the real photo.
        """
        if _requests is None:
            return ''
        key = scientific_name.lower()
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            if key not in self._pending:
                self._pending.add(key)
                threading.Thread(
                    target=self._fetch_and_cache,
                    args=(common_name, scientific_name, key),
                    daemon=True,
                    name=f"PhotoFetch-{common_name[:20]}"
                ).start()
        return ''

    def _fetch_and_cache(self, common_name, scientific_name, key):
        """Background thread: try scientific name first, then common name."""
        url = (self._fetch_wikipedia(scientific_name) or
               self._fetch_wikipedia(common_name) or '')
        with self._lock:
            self._cache[key] = url
            self._pending.discard(key)
        self._save()
        if url:
            logger.info(f"Photo cached for {common_name}: {url[:70]}")
        else:
            logger.debug(f"No Wikipedia photo found for {common_name}")

    def _fetch_wikipedia(self, name):
        """Fetch Wikipedia thumbnail URL for a species name."""
        page = name.replace(' ', '_')
        url = _WIKIPEDIA_URL.format(page)
        try:
            resp = _requests.get(
                url, timeout=_PHOTO_FETCH_TIMEOUT,
                headers={'User-Agent': 'BirdNET-HA-Dashboard/1.0 (home automation)'}
            )
            if resp.status_code == 200:
                data = resp.json()
                thumb = data.get('thumbnail', {}).get('source', '')
                if thumb:
                    return thumb
        except Exception as e:
            logger.debug(f"Wikipedia fetch error for '{name}': {e}")
        return None


class RecentBirds:
    """Ordered list of the most recently detected unique bird species.

    When a species is detected again it moves to the top of the list (most
    recent).  The list is capped at RECENT_BIRDS_MAX entries.  Each entry
    carries the photo URL from BirdPhotoCache (may be '' on first detection,
    then filled in on subsequent detections of the same species).
    """

    def __init__(self, photo_cache):
        self._photo_cache = photo_cache
        self._birds = []   # list of dicts, index 0 = most recently detected

    def add(self, common_name, scientific_name, confidence, timestamp):
        """Add or update a detection entry."""
        url = self._photo_cache.get_photo_url(common_name, scientific_name)
        entry = {
            'common_name': common_name,
            'scientific_name': scientific_name,
            'confidence': round(float(confidence), 3),
            'timestamp': timestamp.isoformat(),
            'photo_url': url,
        }
        # Remove any existing entry for this species so it moves to top
        self._birds = [b for b in self._birds if b['common_name'] != common_name]
        self._birds.insert(0, entry)
        self._birds = self._birds[:RECENT_BIRDS_MAX]

    def refresh_photo(self, common_name, scientific_name):
        """Re-fetch photo URL for a cached entry (called after background fetch)."""
        url = self._photo_cache.get_photo_url(common_name, scientific_name)
        if not url:
            return
        for b in self._birds:
            if b['common_name'] == common_name and not b['photo_url']:
                b['photo_url'] = url

    def as_mqtt_payload(self):
        return {
            'count': len(self._birds),
            'birds': self._birds,
            'updated': datetime.now().isoformat(),
        }


# ============================================================================
# MAIN ANALYZER
# ============================================================================

class BirdNETAnalyzer:
    """Main BirdNET real-time analysis loop."""

    def __init__(self):
        logger.info("=" * 60)
        logger.info("BirdNET Real-Time Analyzer Starting")
        logger.info("=" * 60)

        # Location info
        if LATITUDE == 0 and LONGITUDE == 0:
            logger.warning("Location not set!  BirdNET will not filter by region.")
            logger.warning("Set BIRDNET_LAT and BIRDNET_LON environment variables.")
            logger.warning("Example: export BIRDNET_LAT=37.7749 BIRDNET_LON=-122.4194")
        else:
            logger.info(f"Location: {LATITUDE}, {LONGITUDE}")

        logger.info(f"Min confidence: {MIN_CONFIDENCE}")
        logger.info(f"Analysis gap: {ANALYSIS_GAP_SEC}s")
        logger.info(f"Sample rate: {SAMPLE_RATE} Hz")

        # Initialize BirdNET model (downloads ~150 MB on first run)
        logger.info("Loading BirdNET model (first run downloads ~150 MB)...")
        self.analyzer = Analyzer()
        logger.info("BirdNET model loaded")

        # MQTT
        self.mqtt = MQTTPublisher(MQTT_BROKER, MQTT_PORT)

        # Stats
        self.tracker = BirdDetectionTracker()

        # Audio
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames_per_chunk = int(SAMPLE_RATE * CHUNK_DURATION_SEC)

        # Health monitoring
        self.last_audio_time = datetime.now()
        self.silence_start = None
        self.silence_alerted = False
        self.mic_status = 'starting'
        self.monitor_active = False
        self.last_cleanup = datetime.now()
        self.consecutive_errors = 0

        # Watchdog — signals when the main loop is trying to read audio
        self._reading_audio = False
        self._watchdog_abort = threading.Event()

        # Bird photo cache + recent birds list (for dashboard gallery)
        self.photo_cache = BirdPhotoCache()
        self.recent_birds = RecentBirds(self.photo_cache)

        # CSV
        init_csv()

    def _find_loopback_device(self):
        """Find the shared loopback capture device.

        Prefers the 'loopback_cap' dsnoop device defined in /etc/asound.conf,
        which lets multiple readers (bark detector + BirdNET) share the same
        ALSA loopback subdevice. Falls back to raw hw:Loopback,1 if dsnoop
        is unavailable.
        """
        count = self.audio.get_device_count()
        inputs = []
        dsnoop_idx = None
        loopback_idx = None
        for i in range(count):
            info = self.audio.get_device_info_by_index(i)
            if info.get('maxInputChannels', 0) > 0:
                name = info['name']
                inputs.append((i, name))
                # Prefer the shared dsnoop device (defined in /etc/asound.conf)
                if 'loopback_cap' in name.lower():
                    dsnoop_idx = i
                # Fallback: raw loopback capture (hw:X,1)
                elif 'Loopback' in name and name.endswith(',1)'):
                    loopback_idx = i

        selected = dsnoop_idx if dsnoop_idx is not None else loopback_idx

        logger.info(f"Found {len(inputs)} input device(s):")
        for idx, name in inputs:
            marker = " <-- selected" if idx == selected else ""
            logger.info(f"  [{idx}] {name}{marker}")
        if dsnoop_idx is not None:
            name = self.audio.get_device_info_by_index(dsnoop_idx)['name']
            logger.info(f"Using shared loopback capture [{dsnoop_idx}] {name}")
        elif loopback_idx is not None:
            name = self.audio.get_device_info_by_index(loopback_idx)['name']
            logger.info(f"Using raw ALSA loopback capture [{loopback_idx}] {name} (dsnoop not found)")
        else:
            logger.warning("Loopback capture device not found — falling back to system default")
            logger.warning("  Check: sudo modprobe snd-aloop && systemctl status iphone-audio-stream")
        return selected

    def start(self):
        """Open audio and enter detection loop."""
        device_index = self._find_loopback_device()

        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.frames_per_chunk
            )
            logger.info(f"Audio stream opened ({SAMPLE_RATE} Hz, {CHUNK_DURATION_SEC}s chunks)")
        except Exception as e:
            logger.error(f"Failed to open audio stream: {e}")
            self.mqtt.publish_status("error")
            raise

        self.mqtt.publish_monitor_active(True)
        self.monitor_active = True

        # Start watchdog thread
        watchdog = threading.Thread(
            target=self._watchdog_loop, daemon=True, name="BirdNETWatchdog"
        )
        watchdog.start()

        try:
            self._detection_loop()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt — shutting down")
        finally:
            self._watchdog_abort.set()
            self.stop()

    def _watchdog_loop(self):
        """Daemon thread: kick the audio stream if it freezes silently.

        stream.read() can block forever when the ALSA dsnoop device becomes
        unresponsive (e.g. iPhone stream drops and reconnects).  This watchdog
        monitors last_audio_time and forcefully closes+reopens the stream if
        WATCHDOG_TIMEOUT_SEC elapses without a successful read.
        """
        logger.info(f"Watchdog started (timeout={WATCHDOG_TIMEOUT_SEC}s, "
                    f"poll={WATCHDOG_POLL_SEC}s)")
        while not self._watchdog_abort.is_set():
            self._watchdog_abort.wait(timeout=WATCHDOG_POLL_SEC)
            if self._watchdog_abort.is_set():
                break
            if not self._reading_audio:
                # Not currently blocked in stream.read() — nothing to do
                continue
            elapsed = (datetime.now() - self.last_audio_time).total_seconds()
            if elapsed >= WATCHDOG_TIMEOUT_SEC:
                logger.error(
                    f"[watchdog] stream.read() blocked for {elapsed:.0f}s — "
                    f"forcing stream reopen"
                )
                self._reopen_stream()

    def _reopen_stream(self):
        """Close and reopen the PyAudio stream to recover from a frozen device.

        Called from the watchdog thread while the main thread is blocked in
        stream.read().  Closing the stream unblocks the read with an IOError,
        which the _detection_loop except clause will catch and recover from.
        """
        try:
            if self.stream:
                try:
                    self.stream.stop_stream()
                except Exception:
                    pass
                try:
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None
            logger.info("[watchdog] old stream closed — main loop will reopen")
        except Exception as e:
            logger.error(f"[watchdog] reopen error: {e}")

    def _detection_loop(self):
        """Main loop: record → analyze → publish."""
        logger.info("Detection loop started. Listening for birds...")

        while True:
            try:
                # If watchdog closed a frozen stream, reopen it before reading
                if self.stream is None:
                    logger.info("Reopening audio stream after watchdog reset...")
                    device_index = self._find_loopback_device()
                    self.stream = self.audio.open(
                        format=pyaudio.paInt16,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=self.frames_per_chunk
                    )
                    logger.info("Audio stream reopened successfully")
                    self.consecutive_errors = 0

                # Record one chunk (set flag so watchdog knows we're in here)
                self._reading_audio = True
                audio_bytes = self.stream.read(self.frames_per_chunk,
                                               exception_on_overflow=False)
                self._reading_audio = False
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16)

                self.last_audio_time = datetime.now()
                self.consecutive_errors = 0

                # Update mic status if it was offline
                if self.mic_status != 'online':
                    self.mic_status = 'online'
                    if not self.monitor_active:
                        self.mqtt.publish_monitor_active(True)
                        self.monitor_active = True
                    logger.info("Audio stream active")

                # Check for silence (dead mic / no iPhone stream)
                db = calculate_rms_db(audio_data)
                self._check_silence(db)

                # Skip analysis if audio is dead silence
                if db <= SILENCE_THRESHOLD_DB:
                    self._publish_stats()
                    if ANALYSIS_GAP_SEC > 0:
                        time.sleep(ANALYSIS_GAP_SEC)
                    continue

                # Write to temp WAV for birdnetlib
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    tmp_path = tmp.name
                save_wav(audio_data, tmp_path)

                # Run BirdNET analysis
                try:
                    recording = Recording(
                        self.analyzer,
                        path=tmp_path,
                        lat=LATITUDE,
                        lon=LONGITUDE,
                        date=datetime.now(),
                        min_conf=MIN_CONFIDENCE
                    )
                    recording.analyze()
                    detections = recording.detections
                except Exception as e:
                    logger.error(f"BirdNET analysis error: {e}")
                    detections = []
                finally:
                    # Always clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass

                # Process detections
                for det in detections:
                    common = det['common_name']
                    scientific = det['scientific_name']
                    confidence = det['confidence']

                    logger.info(f"BIRD: {common} ({scientific}) "
                                f"conf={confidence:.2f}")

                    # Publish to MQTT
                    self.mqtt.publish_detection(common, scientific, confidence)

                    # Track stats
                    self.tracker.add_detection(common)

                    # Update recent birds gallery and publish (retained)
                    now_ts = datetime.now()
                    self.recent_birds.add(common, scientific, confidence, now_ts)
                    self.mqtt.publish(
                        MQTT_TOPIC_RECENT_BIRDS,
                        self.recent_birds.as_mqtt_payload(),
                        retain=True
                    )

                    # Log to CSV
                    log_detection_csv(common, scientific, confidence)

                    # Save audio clip
                    if SAVE_BIRD_AUDIO:
                        self._save_bird_clip(audio_data, common, confidence)

                # Publish updated stats
                self._publish_stats()

                # Periodic storage cleanup (every 30 min)
                if (datetime.now() - self.last_cleanup).total_seconds() > 1800:
                    cleanup_bird_recordings()
                    self.last_cleanup = datetime.now()

                # Gap between analyses
                if ANALYSIS_GAP_SEC > 0:
                    time.sleep(ANALYSIS_GAP_SEC)

            except IOError as e:
                self._reading_audio = False
                self.consecutive_errors += 1
                logger.warning(f"Audio read error #{self.consecutive_errors}: {e}")
                if self.consecutive_errors > 10:
                    if self.mic_status != 'error':
                        self.mic_status = 'error'
                        self.mqtt.publish_monitor_active(False)
                        self.monitor_active = False
                        logger.error("Too many audio errors — mic may be offline")
                time.sleep(1)

            except Exception as e:
                self._reading_audio = False
                logger.error(f"Detection loop error: {e}")
                time.sleep(2)

    def _check_silence(self, db):
        """Detect prolonged silence (equipment failure, not 'no birds')."""
        if db <= SILENCE_THRESHOLD_DB:
            if self.silence_start is None:
                self.silence_start = datetime.now()
            silence_sec = (datetime.now() - self.silence_start).total_seconds()
            if silence_sec >= SILENCE_ALERT_SECONDS and not self.silence_alerted:
                self.silence_alerted = True
                self.mic_status = 'silence'
                self.mqtt.publish_monitor_active(False)
                self.monitor_active = False
                logger.warning(f"SILENCE: No real audio for {int(silence_sec)}s")
        else:
            if self.silence_alerted:
                logger.info("Audio restored after silence period")
            self.silence_start = None
            self.silence_alerted = False

    def _publish_stats(self):
        """Publish current daily stats to MQTT."""
        self.mqtt.publish_stats(self.tracker.get_stats())

    def _save_bird_clip(self, audio_data, species_name, confidence):
        """Save a WAV clip of the detected bird."""
        try:
            now = datetime.now()
            date_dir = os.path.join(
                BIRD_RECORDING_DIR,
                now.strftime('%Y'),
                now.strftime('%m'),
                now.strftime('%d')
            )
            os.makedirs(date_dir, exist_ok=True)

            safe_name = species_name.replace(' ', '_').replace('/', '_')[:40]
            filename = f"bird_{safe_name}_{now.strftime('%H-%M-%S')}_{confidence:.0%}.wav"
            filepath = os.path.join(date_dir, filename)

            save_wav(audio_data, filepath)
            logger.info(f"Saved bird clip: {filepath}")
        except Exception as e:
            logger.error(f"Error saving bird clip: {e}")

    def stop(self):
        """Clean shutdown."""
        logger.info("Shutting down BirdNET analyzer...")

        self.mqtt.publish_monitor_active(False)
        self.mqtt.publish_status("offline")

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

        self.mqtt.disconnect()
        logger.info("Shutdown complete")


# ============================================================================
# MAIN
# ============================================================================

def main():
    analyzer = BirdNETAnalyzer()
    analyzer.start()


if __name__ == "__main__":
    main()
