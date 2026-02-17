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
LATITUDE = float(os.environ.get('BIRDNET_LAT', '0'))
LONGITUDE = float(os.environ.get('BIRDNET_LON', '0'))

# MQTT Settings (same broker as dog_bark_detector.py)
MQTT_BROKER = os.environ.get('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', '1883'))
MQTT_TOPIC_DETECTION = "birdnet/detection"
MQTT_TOPIC_STATS = "birdnet/stats"
MQTT_TOPIC_STATUS = "birdnet/status"
MQTT_TOPIC_MONITOR_ACTIVE = "birdnet/monitor_active"

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

# Silence / health thresholds (consistent with dog_bark_detector.py)
SILENCE_THRESHOLD_DB = 32
SILENCE_ALERT_SECONDS = 60

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
    """Tracks daily bird detection statistics."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self.today = date.today()
        self.species_seen = set()
        self.total_detections = 0
        self.detections_by_species = defaultdict(int)

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

    def publish(self, topic, payload):
        if not self.connected:
            return
        try:
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            self.client.publish(topic, payload)
        except Exception as e:
            logger.error(f"MQTT publish error: {e}")

    def publish_status(self, status):
        self.publish(MQTT_TOPIC_STATUS, {
            'status': status,
            'timestamp': datetime.now().isoformat()
        })

    def publish_monitor_active(self, active):
        self.publish(MQTT_TOPIC_MONITOR_ACTIVE, {
            'active': active,
            'timestamp': datetime.now().isoformat()
        })

    def publish_detection(self, common_name, scientific_name, confidence):
        self.publish(MQTT_TOPIC_DETECTION, {
            'timestamp': datetime.now().isoformat(),
            'common_name': common_name,
            'scientific_name': scientific_name,
            'confidence': confidence,
        })

    def publish_stats(self, stats):
        self.publish(MQTT_TOPIC_STATS, stats)

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

        # CSV
        init_csv()

    def _log_audio_devices(self):
        """Log available audio input devices for diagnostics."""
        count = self.audio.get_device_count()
        inputs = []
        for i in range(count):
            info = self.audio.get_device_info_by_index(i)
            if info.get('maxInputChannels', 0) > 0:
                inputs.append((i, info['name']))
        logger.info(f"Found {len(inputs)} input device(s):")
        for idx, name in inputs:
            logger.info(f"  [{idx}] {name}")
        logger.info("Using PulseAudio default source (shared with dog bark detector)")

    def start(self):
        """Open audio and enter detection loop."""
        self._log_audio_devices()

        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=AUDIO_DEVICE_INDEX,
                frames_per_buffer=self.frames_per_chunk
            )
            logger.info(f"Audio stream opened ({SAMPLE_RATE} Hz, {CHUNK_DURATION_SEC}s chunks)")
        except Exception as e:
            logger.error(f"Failed to open audio stream: {e}")
            self.mqtt.publish_status("error")
            raise

        self.mqtt.publish_monitor_active(True)
        self.monitor_active = True

        try:
            self._detection_loop()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt — shutting down")
        finally:
            self.stop()

    def _detection_loop(self):
        """Main loop: record → analyze → publish."""
        logger.info("Detection loop started. Listening for birds...")

        while True:
            try:
                # Record one chunk
                audio_bytes = self.stream.read(self.frames_per_chunk,
                                               exception_on_overflow=False)
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
