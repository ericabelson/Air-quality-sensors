#!/usr/bin/env python3
"""
Dog Bark Detector with Decibel Monitoring
==========================================

Detects dog barks using TensorFlow Lite audio classification,
measures decibel levels, and publishes events to MQTT.

Features:
- Real-time dog bark detection
- Decibel level measurement
- 5-minute gap event grouping
- 10-minute gap event grouping
- MQTT publishing for Home Assistant integration
- Audio recording of bark events
- CSV logging

Author: Claude Code
License: MIT
"""

import sys
import os
import subprocess
import time
import json
import logging
from datetime import datetime, timedelta
from collections import deque
import threading
import numpy as np
import paho.mqtt.client as mqtt

# Audio processing imports
try:
    import pyaudio
    import librosa
    import soundfile as sf
    from scipy.io import wavfile
    from pydub import AudioSegment
except ImportError as e:
    print(f"Error importing audio libraries: {e}")
    print("Please install required packages:")
    print("pip install pyaudio librosa soundfile scipy pydub")
    sys.exit(1)

# TensorFlow Lite import
# Uses ai-edge-litert (~12 MB) via tflite_runtime shim instead of
# full tensorflow (~260 MB).  The shim is created by install_birdnet.sh.
try:
    from tflite_runtime.interpreter import Interpreter as TFLiteInterpreter
except ImportError:
    print("Error: tflite_runtime not available")
    print("Run: ./scripts/install_birdnet.sh")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Audio Settings
# Use PulseAudio (default device) so both this detector and BirdNET can share
# the same loopback source. PulseAudio handles resampling from 48kHz to 16kHz.
AUDIO_DEVICE_INDEX = None  # None = PulseAudio default source (shared with BirdNET)
SAMPLE_RATE = 16000  # Hz (YAMNet requires 16kHz; PulseAudio resamples from device rate)
CHANNELS = 1  # Mono
CHUNK_SIZE = 15600  # YAMNet TFLite model expects exactly 15600 samples per inference

# Detection Settings
# Lower threshold improves counting when multiple dogs bark simultaneously —
# YAMNet's per-class confidence drops in complex multi-dog audio, so 0.40
# misses many real barks.  0.30 catches them with acceptable false-positive rate
# given the dB gate below.
DOG_BARK_CONFIDENCE_THRESHOLD = 0.30
BARK_COOLDOWN_SECONDS = 30  # Publish "not barking" after this many seconds of no bark
# Classify anything above the silence floor so we don't miss quieter barks.
MIN_CLASSIFY_DB = 32  # Match SILENCE_THRESHOLD_DB; everything above silence gets classified
DOG_BARK_CLASS_NAMES = [
    "Dog",
    "Bark",
    "Bow-wow",
    "Growling",
    "Whimper",
    "Howl",
    "Domestic animals, pets",
]

# Decibel Settings
# Audio is raw int16 samples (0-32768), not calibrated Pascals.
# We use dBFS (full-scale) + offset to approximate SPL.
# 90 dB offset maps: quiet room ~35 dB, talking ~60 dB, loud bark ~80 dB
DBFS_OFFSET = 90  # dBFS-to-SPL approximation offset
INT16_MAX = 32768.0  # Full-scale reference for 16-bit audio
MIN_DB = 30  # Minimum decibel threshold to consider
MAX_DB = 120  # Maximum decibel (for safety)

# Silence Detection Settings
SILENCE_THRESHOLD_DB = 32  # dB level below which audio is considered silence
SILENCE_ALERT_SECONDS = 60  # Alert after this many seconds of continuous silence
SILENCE_CHECK_INTERVAL = 30  # Check for silence every N seconds

# Event Grouping Settings
GAP_5MIN = 300  # 5 minutes in seconds
GAP_10MIN = 600  # 10 minutes in seconds

# MQTT Settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_BARK = "audio/dog_bark"
MQTT_TOPIC_DECIBELS = "audio/decibels"
MQTT_TOPIC_STATUS = "audio/detector_status"
MQTT_TOPIC_STATS = "audio/bark_stats"
MQTT_TOPIC_LAST_DETECTION = "audio/last_detection"
MQTT_TOPIC_MIC_STATUS = "audio/microphone_status"
MQTT_TOPIC_MONITOR_ACTIVE = "audio/monitor_active"  # Whether detector is actively monitoring
MQTT_TOPIC_STORAGE_STATUS = "audio/storage_status"  # USB drive / recording storage health
MQTT_TOPIC_HEALTH = "audio/health"                  # Full pipeline health (retained JSON)
MQTT_TOPIC_BARK_5MIN = "audio/bark_5min_count"      # Barks-per-5-min bucket for HA chart

# Seconds per bark-count bucket (must match HA statistics period)
BARK_BUCKET_SECONDS = 300  # 5 minutes

# ============================================================================
# HEALTH MONITOR SETTINGS
# ============================================================================

# IP address of the audio source device (iPhone / future mic) to ping.
# Update this if the device IP changes.
AUDIO_SOURCE_IP = "192.168.68.106"

# systemd service that streams audio into the ALSA loopback.
AUDIO_SOURCE_SERVICE = "iphone-audio-stream"

# How often (seconds) the health monitor runs its checks.
HEALTH_CHECK_INTERVAL = 30

# Auto-restart AUDIO_SOURCE_SERVICE when ALSA XRUN is detected.
XRUN_AUTO_RESTART = True

# Minimum seconds between auto-restarts (prevents restart loops).
# 30s is long enough to avoid restart storms but short enough to recover quickly.
RESTART_COOLDOWN_SECONDS = 30

# Seconds without any non-silent audio before health is flagged as degraded.
# 300 s (5 min) avoids false alarms during genuine quiet periods.
REAL_AUDIO_TIMEOUT = 300

# File Paths
BASE_DIR = os.path.expanduser("~/audio_detection")
MODEL_PATH = os.path.join(BASE_DIR, "models", "yamnet.tflite")
LABELS_PATH = os.path.join(BASE_DIR, "models", "yamnet_class_map.csv")

# Recording Storage
# Prefer USB drive for MP3 recordings (saves SD card wear). Fall back to local.
# CSV data always goes to BASE_DIR regardless of USB status.
USB_MOUNT_PATH = "/mnt/usb/bark_audio/recordings"
LOCAL_RECORDING_PATH = os.path.join(BASE_DIR, "recordings")
USB_CHECK_INTERVAL = 300  # Re-check USB availability every 5 minutes

def is_usb_available():
    """Check if USB drive is mounted and writable"""
    return os.path.ismount("/mnt/usb") and os.access("/mnt/usb", os.W_OK)

def get_recording_dir():
    """Determine the best recording directory to use"""
    if is_usb_available():
        return USB_MOUNT_PATH
    return LOCAL_RECORDING_PATH

RECORDING_DIR = get_recording_dir()
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Storage Management
MAX_RECORDING_MB = 50000  # Maximum MB for audio recordings (FIFO: oldest deleted first)
                          # 50 GB on a 477 GB USB drive; at 32 kbps MP3 this holds
                          # ~3500 hours of bark-event audio for long-term legal evidence.
AUDIO_QUALITY = "32k"  # Very low quality MP3 for minimal size

# Raw Event Log - every individual bark detection with timestamp
RAW_EVENTS_CSV = os.path.join(DATA_DIR, "bark_events_raw.csv")
# Uptime/Downtime Log - tracks when the monitor starts, stops, and gaps
UPTIME_LOG_CSV = os.path.join(DATA_DIR, "monitor_uptime.csv")

# Create directories if they don't exist
for directory in [LOG_DIR, DATA_DIR, RECORDING_DIR]:
    os.makedirs(directory, exist_ok=True)

# Logging Setup
log_file = os.path.join(LOG_DIR, f"dog_bark_detector_{datetime.now().strftime('%Y%m%d')}.log")
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
# BARK EVENT TRACKING
# ============================================================================

class BarkEvent:
    """Represents a single bark detection event"""
    def __init__(self, timestamp, confidence, decibels):
        self.timestamp = timestamp
        self.confidence = confidence
        self.decibels = decibels

    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'confidence': float(self.confidence),
            'decibels': float(self.decibels)
        }

class BarkEventGroup:
    """Groups bark events based on gap time"""
    def __init__(self, gap_seconds):
        self.gap_seconds = gap_seconds
        self.events = []
        self.start_time = None
        self.end_time = None
        self.max_decibels = 0
        self.avg_confidence = 0

    def add_event(self, event):
        """Add a bark event to this group"""
        if not self.start_time:
            self.start_time = event.timestamp

        self.end_time = event.timestamp
        self.events.append(event)
        self.max_decibels = max(self.max_decibels, event.decibels)
        self.avg_confidence = np.mean([e.confidence for e in self.events])

    def get_duration_minutes(self):
        """Calculate duration in minutes"""
        if not self.start_time or not self.end_time:
            return 0
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 60.0

    def to_csv_row(self):
        """Format as CSV row: date,start_time,end_time,duration_min,max_db,num_barks"""
        if not self.start_time:
            return None

        date_str = self.start_time.strftime('%Y-%m-%d')
        start_str = self.start_time.strftime('%H:%M:%S')
        end_str = self.end_time.strftime('%H:%M:%S')
        duration = self.get_duration_minutes()

        return f"{date_str},{start_str},{end_str},{duration:.2f},{self.max_decibels:.1f},{len(self.events)}"

# ============================================================================
# AUDIO CLASSIFIER
# ============================================================================

class DogBarkClassifier:
    """TensorFlow Lite audio classifier for dog bark detection"""

    def __init__(self, model_path, labels_path):
        """Initialize the classifier with TFLite model"""
        logger.info(f"Loading TFLite model from: {model_path}")

        # Load TFLite model
        try:
            self.interpreter = TFLiteInterpreter(model_path=model_path)
            self.interpreter.allocate_tensors()

            # Get input and output details
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()

            logger.info(f"Model loaded successfully")
            logger.info(f"Input shape: {self.input_details[0]['shape']}")
            logger.info(f"Output shape: {self.output_details[0]['shape']}")

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

        # Load class labels
        self.class_names = self._load_labels(labels_path)
        logger.info(f"Loaded {len(self.class_names)} class labels")

    def _load_labels(self, labels_path):
        """Load YAMNet class labels from CSV.

        The yamnet_class_map.csv has columns: index, mid, display_name
        We need the display_name (column 2), not the mid (column 1).
        """
        import csv
        class_names = []
        try:
            with open(labels_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 3:
                        class_names.append(row[2].strip())
                    elif len(row) >= 2:
                        class_names.append(row[1].strip())
            logger.info(f"Sample labels: {class_names[:5]}")
            return class_names
        except Exception as e:
            logger.error(f"Error loading labels: {e}")
            return []

    def classify_audio(self, audio_data):
        """
        Classify audio chunk and return predictions

        Args:
            audio_data: numpy array of audio samples (16kHz, mono)

        Returns:
            dict with top predictions and confidence scores
        """
        try:
            # Ensure correct type
            audio_data = audio_data.astype(np.float32)

            # Normalize to [-1, 1] using fixed int16 reference (not signal max).
            # Using np.max(np.abs(audio_data)) would amplify silence to full scale,
            # causing YAMNet to classify noise artifacts as real sounds.
            audio_data = audio_data / INT16_MAX

            # Flatten to 1D if needed (YAMNet expects 1D input)
            audio_data = audio_data.flatten()

            # Ensure we have exactly 15600 samples (YAMNet model requirement)
            if len(audio_data) < 15600:
                # Pad with zeros if too short
                audio_data = np.pad(audio_data, (0, 15600 - len(audio_data)))
            elif len(audio_data) > 15600:
                # Truncate if too long
                audio_data = audio_data[:15600]

            # Set input tensor
            self.interpreter.set_tensor(self.input_details[0]['index'], audio_data)

            # Run inference
            self.interpreter.invoke()

            # Get output predictions
            predictions = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

            # Get top predictions
            top_indices = np.argsort(predictions)[-5:][::-1]

            results = []
            for idx in top_indices:
                if idx < len(self.class_names):
                    results.append({
                        'class': self.class_names[idx],
                        'confidence': float(predictions[idx])
                    })

            return results

        except Exception as e:
            logger.error(f"Error during classification: {e}")
            return []

    def is_dog_bark(self, predictions):
        """
        Check if predictions contain dog bark with sufficient confidence

        Args:
            predictions: list of prediction dicts from classify_audio()

        Returns:
            tuple (is_bark: bool, confidence: float, class_name: str)
        """
        for pred in predictions:
            class_name = pred['class']
            confidence = pred['confidence']

            # Check if any dog-related class exceeds threshold
            if any(bark_class in class_name for bark_class in DOG_BARK_CLASS_NAMES):
                if confidence >= DOG_BARK_CONFIDENCE_THRESHOLD:
                    return True, confidence, class_name

        return False, 0.0, ""

# ============================================================================
# DECIBEL METER
# ============================================================================

def calculate_decibels(audio_data):
    """
    Calculate approximate dB SPL from raw int16 audio samples.

    Uses dBFS (decibels relative to full-scale) plus an offset to
    approximate real-world SPL. Without a calibrated microphone,
    absolute values are estimates, but relative changes are accurate.

    Args:
        audio_data: numpy array of int16 audio samples (as float32)

    Returns:
        float: approximate decibel level (SPL)
    """
    # Calculate RMS (Root Mean Square) amplitude
    rms = np.sqrt(np.mean(audio_data**2))

    # Avoid log(0)
    if rms < 1e-10:
        return MIN_DB

    # Normalize to 0-1 range (int16 full scale = 32768)
    # Then convert to dBFS and add offset to approximate SPL
    # dBFS = 20 * log10(rms / 32768)  → range: -90 to 0
    # dB SPL ≈ dBFS + 90              → range: ~0 to 90
    db = 20 * np.log10(rms / INT16_MAX) + DBFS_OFFSET

    # Clamp to reasonable range
    db = max(MIN_DB, min(MAX_DB, db))

    return db

# ============================================================================
# AUDIO RECORDER
# ============================================================================

class AudioRecorder:
    """Records audio clips of bark events"""

    def __init__(self, recording_dir, mqtt_publisher=None):
        self.recording_dir = recording_dir
        self.is_recording = False
        self.recording_buffer = []
        self.recording_start_time = None
        self.last_cleanup_check = datetime.now()
        self.last_usb_check = datetime.now()
        self.usb_connected = is_usb_available()
        self.mqtt = mqtt_publisher

    def check_storage_and_cleanup(self):
        """Delete oldest recordings when total exceeds MAX_RECORDING_MB"""
        # Only check every 10 minutes to reduce disk I/O
        if (datetime.now() - self.last_cleanup_check).total_seconds() < 600:
            return

        self.last_cleanup_check = datetime.now()

        try:
            # Get all MP3 files with their modification times and sizes
            files = []
            total_bytes = 0
            for root, dirs, filenames in os.walk(self.recording_dir):
                for filename in filenames:
                    if filename.endswith('.mp3'):
                        filepath = os.path.join(root, filename)
                        mtime = os.path.getmtime(filepath)
                        size = os.path.getsize(filepath)
                        files.append((filepath, mtime, size))
                        total_bytes += size

            total_mb = total_bytes / (1024 * 1024)
            max_bytes = MAX_RECORDING_MB * 1024 * 1024

            if total_bytes > max_bytes:
                logger.warning(f"Recordings at {total_mb:.0f} MB (limit: {MAX_RECORDING_MB} MB) - cleaning up oldest")

                # Sort by modification time (oldest first)
                files.sort(key=lambda x: x[1])

                # Delete oldest files until under limit
                bytes_freed = 0
                files_deleted = 0
                target_free = total_bytes - max_bytes + (max_bytes * 0.1)  # Free to 90% of limit

                for filepath, mtime, size in files:
                    if bytes_freed >= target_free:
                        break
                    try:
                        os.remove(filepath)
                        bytes_freed += size
                        files_deleted += 1
                    except Exception as e:
                        logger.error(f"Error deleting {filepath}: {e}")

                logger.info(f"Cleanup complete: deleted {files_deleted} files, freed {bytes_freed / 1024 / 1024:.1f} MB")
            else:
                logger.info(f"Recording storage: {total_mb:.0f} MB / {MAX_RECORDING_MB} MB ({len(files)} files)")

        except Exception as e:
            logger.error(f"Error during storage cleanup: {e}")

    def check_usb_status(self, force=False):
        """Periodically re-check USB drive and switch recording directory if needed"""
        if not force and (datetime.now() - self.last_usb_check).total_seconds() < USB_CHECK_INTERVAL:
            return
        self.last_usb_check = datetime.now()

        usb_now = is_usb_available()
        new_dir = get_recording_dir()

        if usb_now != self.usb_connected:
            # USB status changed
            self.usb_connected = usb_now
            self.recording_dir = new_dir
            os.makedirs(self.recording_dir, exist_ok=True)

            if usb_now:
                logger.info(f"USB drive reconnected - recordings now going to {new_dir}")
            else:
                logger.warning(f"USB drive disconnected - recordings falling back to {new_dir}")

        if self.mqtt:
            details = ""
            if not usb_now:
                details = ("USB drive not mounted at /mnt/usb. "
                           "Recordings are saving to SD card. "
                           "Plug in USB drive and mount it to preserve SD card life.")
            self.mqtt.publish_storage_status(usb_now, new_dir, details)

    def start_recording(self):
        """Start recording audio"""
        self.is_recording = True
        self.recording_buffer = []
        self.recording_start_time = datetime.now()
        logger.info("Started recording bark audio")

    def add_audio_chunk(self, audio_data):
        """Add audio chunk to recording buffer"""
        if self.is_recording:
            self.recording_buffer.append(audio_data)

    def stop_recording(self):
        """Stop recording and save to file"""
        if not self.is_recording or not self.recording_buffer:
            return None

        self.is_recording = False

        try:
            # Concatenate all audio chunks
            full_audio = np.concatenate(self.recording_buffer)

            # Create filename with timestamp
            timestamp_str = self.recording_start_time.strftime('%Y-%m-%d_%H-%M-%S')
            date_path = os.path.join(
                self.recording_dir,
                self.recording_start_time.strftime('%Y'),
                self.recording_start_time.strftime('%m'),
                self.recording_start_time.strftime('%d')
            )
            os.makedirs(date_path, exist_ok=True)

            # Save as WAV first
            wav_file = os.path.join(date_path, f"bark_{timestamp_str}.wav")
            wavfile.write(wav_file, SAMPLE_RATE, full_audio.astype(np.int16))

            # Convert to MP3 with lowest quality for minimal size
            mp3_file = wav_file.replace('.wav', '.mp3')
            audio_segment = AudioSegment.from_wav(wav_file)
            audio_segment.export(mp3_file, format='mp3', bitrate='32k')  # Lowest quality, smallest size

            # Remove WAV file to save space
            os.remove(wav_file)

            logger.info(f"Saved bark recording: {mp3_file}")

            # Check storage and cleanup if needed
            self.check_storage_and_cleanup()

            return mp3_file

        except Exception as e:
            logger.error(f"Error saving recording: {e}")
            return None

# ============================================================================
# MQTT CLIENT
# ============================================================================

class MQTTPublisher:
    """Publishes detection events to MQTT broker"""

    def __init__(self, broker, port):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()
        self.connected = False

        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        # Connect
        try:
            self.client.connect(broker, port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self.connected = True
            self.publish_status("online")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        logger.warning("Disconnected from MQTT broker")
        self.connected = False

    @staticmethod
    def _convert_numpy(obj):
        """Convert numpy types to native Python for JSON serialization"""
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    # Topics whose last value should be retained by the MQTT broker so that
    # Home Assistant sensors recover immediately after an HA restart without
    # waiting for the next publish from the detector.
    RETAINED_TOPICS = {
        MQTT_TOPIC_BARK,
        MQTT_TOPIC_STATUS,
        MQTT_TOPIC_STATS,
        MQTT_TOPIC_LAST_DETECTION,
        MQTT_TOPIC_MIC_STATUS,
        MQTT_TOPIC_MONITOR_ACTIVE,
        MQTT_TOPIC_STORAGE_STATUS,
        MQTT_TOPIC_HEALTH,
        MQTT_TOPIC_BARK_5MIN,
    }

    def publish(self, topic, payload):
        """Publish message to MQTT topic"""
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return

        try:
            if isinstance(payload, dict):
                payload = json.dumps(payload, default=self._convert_numpy)
            retain = topic in self.RETAINED_TOPICS
            self.client.publish(topic, payload, retain=retain)
        except Exception as e:
            logger.error(f"Error publishing to MQTT: {e}")

    def publish_bark_event(self, event, is_bark, class_name):
        """Publish bark detection event"""
        payload = {
            'timestamp': event.timestamp.isoformat(),
            'detected': is_bark,
            'confidence': float(event.confidence),
            'decibels': float(event.decibels),
            'class': class_name
        }
        self.publish(MQTT_TOPIC_BARK, payload)

    def publish_decibels(self, decibels):
        """Publish current decibel level"""
        self.publish(MQTT_TOPIC_DECIBELS, {'decibels': float(decibels)})

    def publish_status(self, status):
        """Publish detector status"""
        self.publish(MQTT_TOPIC_STATUS, {'status': status})

    def publish_stats(self, stats):
        """Publish daily statistics"""
        self.publish(MQTT_TOPIC_STATS, stats)

    def publish_last_detection(self, last_bark_time, confidence, decibels):
        """Publish last detection info (updated every minute for dashboard)"""
        if last_bark_time:
            time_ago_seconds = (datetime.now() - last_bark_time).total_seconds()
            payload = {
                'last_bark': last_bark_time.isoformat(),
                'seconds_ago': int(time_ago_seconds),
                'confidence': float(confidence),
                'decibels': float(decibels),
                'status': 'recent' if time_ago_seconds < 300 else 'quiet'  # Recent if within 5 min
            }
        else:
            payload = {
                'last_bark': None,
                'seconds_ago': None,
                'confidence': 0,
                'decibels': 0,
                'status': 'no_data'
            }
        self.publish(MQTT_TOPIC_LAST_DETECTION, payload)

    def publish_mic_status(self, status, details=None):
        """Publish microphone/audio input status"""
        payload = {
            'status': status,  # 'online', 'offline', 'no_data', 'error'
            'timestamp': datetime.now().isoformat(),
            'details': details or ''
        }
        self.publish(MQTT_TOPIC_MIC_STATUS, payload)

    def publish_health(self, health_payload):
        """Publish full pipeline health status (retained)."""
        self.publish(MQTT_TOPIC_HEALTH, health_payload)

    def publish_storage_status(self, usb_connected, recording_dir, details=None):
        """Publish recording storage status"""
        payload = {
            'usb_connected': usb_connected,
            'recording_path': recording_dir,
            'status': 'usb' if usb_connected else 'local_fallback',
            'timestamp': datetime.now().isoformat(),
            'details': details or ''
        }
        self.publish(MQTT_TOPIC_STORAGE_STATUS, payload)

# ============================================================================
# PIPELINE HEALTH MONITOR
# ============================================================================

class HealthMonitor:
    """
    Independent pipeline health checker running in a daemon thread.

    Every HEALTH_CHECK_INTERVAL seconds it verifies:
      1. Phone / mic source reachable (ICMP ping to AUDIO_SOURCE_IP)
      2. Audio source systemd service is 'active'
      3. ALSA loopback playback side is RUNNING (not XRUN / closed)
      4. Real non-silent audio has been received recently

    Findings are published as a single retained JSON to MQTT_TOPIC_HEALTH so
    the HA dashboard can show exactly which component broke.

    Auto-recovery: on XRUN the service is restarted (with cooldown).
    monitor_active is forced False whenever any component is unhealthy.
    """

    def __init__(self, detector, mqtt_publisher):
        self.detector = detector
        self.mqtt = mqtt_publisher
        self.last_restart_time = None
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="HealthMonitor"
        )

    def start(self):
        self._thread.start()
        logger.info("HealthMonitor thread started")

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_phone_reachable(self):
        """Ping AUDIO_SOURCE_IP once; return True if host replies."""
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", AUDIO_SOURCE_IP],
                capture_output=True,
                timeout=6,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"[health] ping check error: {e}")
            return False

    def _check_service_active(self):
        """Return True if AUDIO_SOURCE_SERVICE is 'active' per systemctl."""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", AUDIO_SOURCE_SERVICE],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip() == "active"
        except Exception as e:
            logger.debug(f"[health] service check error: {e}")
            return False

    def _check_alsa_loopback(self):
        """
        Inspect /proc/asound/Loopback/pcm0p/subN/status for all subdevices.
        Returns (state_str, detail_str) where state_str is one of:
          'running' | 'xrun' | 'closed' | 'error'
        """
        xrun_found = False
        running_found = False
        for sub in range(8):
            path = f"/proc/asound/Loopback/pcm0p/sub{sub}/status"
            try:
                with open(path) as f:
                    content = f.read()
                if "state: XRUN" in content:
                    xrun_found = True
                elif "state: RUNNING" in content:
                    running_found = True
            except FileNotFoundError:
                break
            except Exception:
                pass
        if xrun_found:
            return "xrun", "Loopback playback in XRUN — audio frozen (will auto-restart)"
        if running_found:
            return "running", "Loopback healthy"
        return "closed", "Loopback playback not open — ffmpeg may not be writing"

    def _try_restart_service(self):
        """Restart AUDIO_SOURCE_SERVICE with cooldown protection."""
        now = datetime.now()
        if self.last_restart_time:
            age = (now - self.last_restart_time).total_seconds()
            if age < RESTART_COOLDOWN_SECONDS:
                logger.warning(
                    f"[health] auto-restart skipped: cooldown active "
                    f"({age:.0f}s < {RESTART_COOLDOWN_SECONDS}s)"
                )
                return False
        try:
            result = subprocess.run(
                ["sudo", "systemctl", "restart", AUDIO_SOURCE_SERVICE],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                self.last_restart_time = now
                logger.info(
                    f"[health] auto-restarted {AUDIO_SOURCE_SERVICE} (XRUN recovery)"
                )
                return True
            else:
                logger.error(
                    f"[health] auto-restart failed: {result.stderr.strip()}"
                )
                return False
        except Exception as e:
            logger.error(f"[health] auto-restart exception: {e}")
            return False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _run(self):
        # Let startup settle before the first check
        time.sleep(HEALTH_CHECK_INTERVAL)
        while True:
            try:
                self._do_check()
            except Exception as e:
                logger.error(f"[health] check error: {e}")
            time.sleep(HEALTH_CHECK_INTERVAL)

    def _do_check(self):
        phone_ok = self._check_phone_reachable()
        service_ok = self._check_service_active()
        alsa_state, alsa_detail = self._check_alsa_loopback()
        alsa_ok = alsa_state == "running"

        real_audio_age = (
            datetime.now() - self.detector.last_real_audio_time
        ).total_seconds()
        audio_ok = real_audio_age < REAL_AUDIO_TIMEOUT

        issues = []
        if not phone_ok:
            issues.append(
                f"{AUDIO_SOURCE_IP} unreachable (phone/mic offline or wrong IP?)"
            )
        if not service_ok:
            issues.append(f"{AUDIO_SOURCE_SERVICE} service not running")
        if not alsa_ok:
            issues.append(alsa_detail)
        if not audio_ok:
            mins = int(real_audio_age // 60)
            issues.append(f"No real audio for {mins}m — silent or source muted")

        pipeline_ok = phone_ok and service_ok and alsa_ok and audio_ok
        overall = "ok" if pipeline_ok else "degraded"

        payload = {
            "overall": overall,
            "phone_reachable": phone_ok,
            "service_running": service_ok,
            "alsa_state": alsa_state,
            "alsa_healthy": alsa_ok,
            "audio_flowing": audio_ok,
            "real_audio_age_seconds": int(real_audio_age),
            "issues": issues,
            "source_ip": AUDIO_SOURCE_IP,
            "source_service": AUDIO_SOURCE_SERVICE,
            "timestamp": datetime.now().isoformat(),
        }
        self.mqtt.publish_health(payload)

        if overall == "ok":
            logger.info(
                f"[health] OK — phone:{phone_ok} svc:{service_ok} "
                f"alsa:{alsa_state} audio:{audio_ok} "
                f"(real audio {int(real_audio_age)}s ago)"
            )
        else:
            logger.warning(f"[health] DEGRADED: {'; '.join(issues)}")

        # Force monitor_active=False if the pipeline is unhealthy
        if not pipeline_ok and self.detector.monitor_active:
            self.detector._publish_monitor_active(False)
            self.detector._log_uptime_event(
                "health_degraded", "; ".join(issues)
            )

        # Auto-recovery: restart the service on XRUN or closed loopback
        if alsa_state in ("xrun", "closed") and XRUN_AUTO_RESTART:
            logger.warning(
                f"[health] ALSA {alsa_state} detected — auto-restarting audio service"
            )
            self._try_restart_service()


# ============================================================================
# MAIN DETECTOR
# ============================================================================

class DogBarkDetector:
    """Main dog bark detection system"""

    def __init__(self):
        # Initialize components
        logger.info("Initializing Dog Bark Detector...")

        self.classifier = DogBarkClassifier(MODEL_PATH, LABELS_PATH)
        self.mqtt = MQTTPublisher(MQTT_BROKER, MQTT_PORT)
        self.recorder = AudioRecorder(RECORDING_DIR, self.mqtt)

        # Event tracking
        self.all_events = []
        self.events_5min = []
        self.events_10min = []
        self.current_group_5min = None
        self.current_group_10min = None
        self.last_bark_time = None
        self.last_bark_confidence = 0
        self.last_bark_decibels = 0
        self.bark_active = False  # True when actively barking, False after cooldown

        # Microphone health monitoring
        self.last_audio_received = datetime.now()
        self.last_real_audio_time = datetime.now()  # Updated only on non-silent audio
        self.last_mqtt_update = datetime.now()
        self.consecutive_read_errors = 0
        self.mic_status = 'starting'
        self.monitor_active = False  # Published to MQTT so HA knows we're running
        self.health_monitor = None   # Set in start() after audio stream opens

        # Initialize raw event CSV (individual bark log)
        self._init_raw_event_csv()
        # Log startup in uptime log
        self._log_uptime_event('start')

        # Silence detection - detect when mic is connected but getting no real audio
        self.silence_start_time = None
        self.last_silence_check = datetime.now()
        self.silence_alerted = False

        # Statistics — loaded from disk so totals survive detector restarts
        self.daily_stats = self._load_daily_stats()

        # 5-minute bark-count bucket for the HA histogram chart
        self.bark_bucket_count = 0
        self.bark_bucket_start = datetime.now()

        # Audio stream
        self.audio = pyaudio.PyAudio()
        self.stream = None

        # Publish initial USB storage status
        usb_ok = is_usb_available()
        if usb_ok:
            logger.info(f"Recording to USB drive: {RECORDING_DIR}")
        else:
            logger.warning(f"USB drive not mounted - recording to SD card: {RECORDING_DIR}")
        self.recorder.check_usb_status(force=True)

        logger.info("Initialization complete!")

    # ------------------------------------------------------------------
    # Daily stats persistence — survives detector restarts mid-day
    # ------------------------------------------------------------------

    _STATS_CACHE = os.path.join(
        os.path.expanduser("~/audio_detection"), "data", "daily_stats_cache.json"
    )

    def _load_daily_stats(self):
        """Load today's stats from disk, or start fresh if date has changed."""
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            with open(self._STATS_CACHE) as f:
                cached = json.load(f)
            if cached.get('date') == today:
                logger.info(
                    f"Resumed daily stats from cache: "
                    f"{cached.get('total_barks', 0)} barks so far today"
                )
                return cached
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
        # Fresh day or no cache
        return {
            'date': today,
            'total_barks': 0,
            'max_decibels': 0,
            'start_time': None,
            'end_time': None,
        }

    def _save_daily_stats(self):
        """Persist today's stats to disk (called after every bark detection)."""
        try:
            # Convert numpy types to native Python for JSON serialization
            serializable = {
                k: (float(v) if hasattr(v, 'item') else v)
                for k, v in self.daily_stats.items()
            }
            with open(self._STATS_CACHE, 'w') as f:
                json.dump(serializable, f)
        except Exception as e:
            logger.error(f"Error saving daily stats cache: {e}")

    # ------------------------------------------------------------------

    def _init_raw_event_csv(self):
        """Initialize raw bark event CSV with header if it doesn't exist"""
        if not os.path.exists(RAW_EVENTS_CSV):
            with open(RAW_EVENTS_CSV, 'w') as f:
                f.write("timestamp,date,time,confidence,decibels,class,duration_estimate_sec\n")
            logger.info(f"Created raw event log: {RAW_EVENTS_CSV}")

    def _log_raw_bark_event(self, event, class_name):
        """Log individual bark detection to raw CSV"""
        try:
            with open(RAW_EVENTS_CSV, 'a') as f:
                ts = event.timestamp
                # Duration estimate: each chunk is ~1 second of audio
                f.write(f"{ts.isoformat()},{ts.strftime('%Y-%m-%d')},{ts.strftime('%H:%M:%S')},"
                        f"{event.confidence:.3f},{event.decibels:.1f},{class_name},1\n")
        except Exception as e:
            logger.error(f"Error writing raw event CSV: {e}")

    def _log_uptime_event(self, event_type, details=''):
        """Log monitor start/stop/gap events to uptime CSV AND to the main bark CSV.

        Writing monitoring status rows into bark_events_raw.csv is critical for
        legal data quality: a gap in bark records can only mean "no barking" if
        the monitor was confirmed active during that period.  Status rows here
        provide that proof — absence of BARK rows between two MONITOR_ONLINE rows
        is affirmative evidence of silence, not a data gap.
        """
        now = datetime.now()
        try:
            if not os.path.exists(UPTIME_LOG_CSV):
                with open(UPTIME_LOG_CSV, 'w') as f:
                    f.write("timestamp,event,details\n")
            with open(UPTIME_LOG_CSV, 'a') as f:
                f.write(f"{now.isoformat()},{event_type},{details}\n")
            logger.info(f"Uptime event logged: {event_type} {details}")
        except Exception as e:
            logger.error(f"Error writing uptime log: {e}")

        # Mirror every monitoring-status change into bark_events_raw.csv so that
        # file is a self-contained legal record.  Rows use class = MONITOR_<TYPE>
        # and confidence/decibels = 0 to distinguish them from actual detections.
        try:
            class_name = f"MONITOR_{event_type.upper()}"
            detail_safe = (details or '').replace(',', ';')  # avoid breaking CSV
            with open(RAW_EVENTS_CSV, 'a') as f:
                f.write(
                    f"{now.isoformat()},{now.strftime('%Y-%m-%d')},{now.strftime('%H:%M:%S')},"
                    f"1.000,0.0,{class_name},{detail_safe}\n"
                )
        except Exception as e:
            logger.error(f"Error mirroring uptime event to raw CSV: {e}")

    def _publish_monitor_active(self, active):
        """Publish whether the monitor is actively recording"""
        self.monitor_active = active
        self.mqtt.publish(MQTT_TOPIC_MONITOR_ACTIVE, {
            'active': active,
            'timestamp': datetime.now().isoformat()
        })

    def _find_audio_device(self):
        """Find the shared loopback capture device.

        Prefers the 'loopback_cap' dsnoop device defined in /etc/asound.conf,
        which lets multiple readers (bark detector + BirdNET) share the same
        ALSA loopback subdevice. Falls back to raw hw:Loopback,1 if dsnoop
        is unavailable.

        Returns the PyAudio device index to use, or None to fall back to default.
        """
        device_count = self.audio.get_device_count()
        input_devices = []
        dsnoop_idx = None
        loopback_capture_idx = None

        for i in range(device_count):
            info = self.audio.get_device_info_by_index(i)
            if info.get('maxInputChannels', 0) > 0:
                input_devices.append((i, info['name']))
                name = info['name']
                # Prefer the shared dsnoop device (defined in /etc/asound.conf)
                if 'loopback_cap' in name.lower():
                    dsnoop_idx = i
                # Fallback: raw loopback capture (hw:X,1)
                elif 'Loopback' in name and name.endswith(',1)'):
                    loopback_capture_idx = i

        selected = dsnoop_idx if dsnoop_idx is not None else loopback_capture_idx

        logger.info(f"Found {len(input_devices)} input device(s):")
        for idx, name in input_devices:
            marker = " <-- selected" if idx == selected else ""
            logger.info(f"  [{idx}] {name}{marker}")

        if dsnoop_idx is not None:
            name = self.audio.get_device_info_by_index(dsnoop_idx)['name']
            logger.info(f"Using shared loopback capture [{dsnoop_idx}] {name}")
        elif loopback_capture_idx is not None:
            name = self.audio.get_device_info_by_index(loopback_capture_idx)['name']
            logger.info(f"Using raw ALSA loopback capture [{loopback_capture_idx}] {name} (dsnoop not found)")
        else:
            logger.warning("Loopback capture device not found — falling back to system default")
            logger.warning("  - Load ALSA loopback: sudo modprobe snd-aloop")
            logger.warning("  - Start iPhone stream: sudo systemctl start iphone-audio-stream")

        if not input_devices:
            logger.warning("NO INPUT AUDIO DEVICES FOUND!")
            self.mqtt.publish_mic_status('no_device',
                'No audio input devices found - check snd-aloop and iphone-audio-stream')

        return selected

    def start(self):
        """Start the detection system"""
        logger.info("Starting dog bark detection...")

        # Find loopback device
        device_index = self._find_audio_device()

        # Open audio stream
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK_SIZE
            )
            logger.info(f"Audio stream opened (sample rate: {SAMPLE_RATE} Hz)")
        except Exception as e:
            logger.error(f"Error opening audio stream: {e}")
            logger.error("Available audio devices:")
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                logger.error(f"  {i}: {info['name']}")
            self.mqtt.publish_mic_status('error', f'Failed to open audio stream: {e}')
            raise

        # Mark monitor as actively recording
        self._publish_monitor_active(True)

        # Start the independent pipeline health monitor thread
        self.health_monitor = HealthMonitor(self, self.mqtt)
        self.health_monitor.start()

        # Start detection loop
        try:
            self._detection_loop()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        finally:
            self.stop()

    def _detection_loop(self):
        """Main detection loop"""
        logger.info("Detection loop started. Listening for barks...")

        while True:
            try:
                # Read audio chunk (PulseAudio resamples to 16kHz for us)
                audio_bytes = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)

                # Mark that we received audio successfully
                self.last_audio_received = datetime.now()
                self.consecutive_read_errors = 0

                # Update mic status if it was offline due to a stream error.
                # Exclude 'silence' here — silence means the stream is open but
                # audio content is silent (ALSA XRUN, RTSP source quiet, etc.).
                # Recovering from silence is handled below in the else branch.
                if self.mic_status not in ('online', 'silence'):
                    self.mic_status = 'online'
                    self.mqtt.publish_mic_status('online', 'Audio stream restored')
                    if not self.monitor_active:
                        self._publish_monitor_active(True)
                        self._log_uptime_event('resume', 'Audio stream restored')
                    logger.info("Microphone back online")

                # Calculate decibels
                decibels = calculate_decibels(audio_data)

                # Publish decibels (throttled to every second)
                if int(time.time()) % 1 == 0:
                    self.mqtt.publish_decibels(decibels)

                # Silence detection - catch the case where stream is open but reading dead air
                if decibels <= SILENCE_THRESHOLD_DB:
                    if self.silence_start_time is None:
                        self.silence_start_time = datetime.now()
                    silence_duration = (datetime.now() - self.silence_start_time).total_seconds()

                    # Periodic silence check to avoid log spam
                    time_since_silence_check = (datetime.now() - self.last_silence_check).total_seconds()
                    if silence_duration >= SILENCE_ALERT_SECONDS and time_since_silence_check >= SILENCE_CHECK_INTERVAL:
                        self.last_silence_check = datetime.now()
                        if not self.silence_alerted:
                            self.silence_alerted = True
                            self.mic_status = 'silence'
                            self._publish_monitor_active(False)
                            self._log_uptime_event('silence', f'No real audio for {int(silence_duration)}s')
                            logger.warning(
                                f"SILENCE DETECTED: Audio stuck at {decibels:.0f} dB for "
                                f"{int(silence_duration)}s. No real audio is being captured!"
                            )
                            logger.warning("Possible causes:")
                            logger.warning("  - ALSA loopback not loaded (sudo modprobe snd-aloop)")
                            logger.warning("  - iphone-audio-stream service not running")
                            logger.warning("  - iPhone Periscope HD app not streaming")
                            logger.warning("  - Wrong audio device selected")
                            self.mqtt.publish_mic_status(
                                'silence',
                                f'No real audio - constant {decibels:.0f} dB for {int(silence_duration)}s. '
                                f'Check: snd-aloop module, iphone-audio-stream service, Periscope HD app'
                            )
                        elif int(silence_duration) % 300 == 0:
                            # Re-alert every 5 minutes of continuous silence
                            logger.warning(
                                f"Still silent: {int(silence_duration)}s of silence "
                                f"({int(silence_duration / 60)} min)"
                            )
                            self.mqtt.publish_mic_status(
                                'silence',
                                f'Continuous silence for {int(silence_duration / 60)} min. '
                                f'No audio input device providing real audio.'
                            )
                else:
                    # Real audio detected - reset silence tracking
                    self.last_real_audio_time = datetime.now()
                    if self.silence_alerted:
                        logger.info(f"Audio restored - silence ended after "
                                    f"{int((datetime.now() - self.silence_start_time).total_seconds())}s")
                        self.mqtt.publish_mic_status('online', 'Real audio detected - silence ended')
                    # Recover monitor_active if we were in silence state
                    if self.mic_status == 'silence':
                        self.mic_status = 'online'
                        if not self.monitor_active:
                            self._publish_monitor_active(True)
                            self._log_uptime_event('resume', 'Real audio detected after silence')
                    self.silence_start_time = None
                    self.silence_alerted = False

                # Check microphone health (every 30 seconds)
                time_since_audio = (datetime.now() - self.last_audio_received).total_seconds()
                if time_since_audio > 30:
                    if self.mic_status != 'no_data':
                        self.mic_status = 'no_data'
                        self._publish_monitor_active(False)
                        self._log_uptime_event('no_data', f'No audio for {int(time_since_audio)}s')
                        self.mqtt.publish_mic_status('no_data', f'No audio for {int(time_since_audio)}s')
                        logger.error(f"Microphone offline - no audio data for {int(time_since_audio)} seconds")

                # Publish last_detection update every minute
                time_since_update = (datetime.now() - self.last_mqtt_update).total_seconds()
                if time_since_update >= 60:
                    self.mqtt.publish_last_detection(
                        self.last_bark_time,
                        self.last_bark_confidence,
                        self.last_bark_decibels
                    )
                    self.last_mqtt_update = datetime.now()

                # Publish 5-minute bark-count bucket and reset
                bucket_age = (datetime.now() - self.bark_bucket_start).total_seconds()
                if bucket_age >= BARK_BUCKET_SECONDS:
                    self.mqtt.publish(
                        MQTT_TOPIC_BARK_5MIN,
                        {'count': self.bark_bucket_count,
                         'window_start': self.bark_bucket_start.isoformat()}
                    )
                    logger.info(
                        f"5-min bucket: {self.bark_bucket_count} barks "
                        f"(window started {self.bark_bucket_start.strftime('%H:%M')})"
                    )
                    self.bark_bucket_count = 0
                    self.bark_bucket_start = datetime.now()

                # Periodically check USB drive status and switch recording dir if needed
                self.recorder.check_usb_status()

                # Skip classification if audio is too quiet (silence/no input)
                if decibels <= MIN_CLASSIFY_DB:
                    predictions = []
                else:
                    # Classify audio
                    predictions = self.classifier.classify_audio(audio_data)

                # Log top predictions periodically for debugging
                if predictions and int(time.time()) % 5 == 0:
                    top3 = predictions[:3]
                    top_str = ", ".join(f"{p['class']}:{p['confidence']:.3f}" for p in top3)
                    logger.info(f"[DEBUG] dB={decibels:.1f} top3=[{top_str}]")

                # Check for dog bark
                is_bark, confidence, class_name = self.classifier.is_dog_bark(predictions)

                if is_bark:
                    self.bark_active = True
                    # Create bark event
                    event = BarkEvent(datetime.now(), confidence, decibels)
                    self.all_events.append(event)

                    logger.info(f"🐕 DOG BARK DETECTED - Confidence: {confidence:.2f} - Decibels: {decibels:.1f}dB - Class: {class_name}")

                    # Log to raw event CSV (permanent record)
                    self._log_raw_bark_event(event, class_name)

                    # Publish to MQTT (real-time)
                    self.mqtt.publish_bark_event(event, True, class_name)

                    # Update last detection info for minute-based sensor
                    self.last_bark_time = datetime.now()
                    self.last_bark_confidence = confidence
                    self.last_bark_decibels = decibels

                    # Update statistics
                    self._update_statistics(event)

                    # Handle event grouping
                    self._handle_event_grouping(event)

                    # Record audio
                    if not self.recorder.is_recording:
                        self.recorder.start_recording()

                # Bark cooldown - publish "not barking" when barking stops
                elif self.bark_active and self.last_bark_time:
                    time_since_bark = (datetime.now() - self.last_bark_time).total_seconds()
                    if time_since_bark > BARK_COOLDOWN_SECONDS:
                        self.bark_active = False
                        self.mqtt.publish(MQTT_TOPIC_BARK, {
                            'timestamp': datetime.now().isoformat(),
                            'detected': False,
                            'confidence': 0.0,
                            'decibels': float(decibels),
                            'class': ''
                        })
                        logger.info("Bark cooldown: published 'not barking' state")

                # Add to recording buffer if recording
                if self.recorder.is_recording:
                    self.recorder.add_audio_chunk(audio_data)

                    # Stop recording if gap exceeded
                    if self.last_bark_time:
                        gap = (datetime.now() - self.last_bark_time).total_seconds()
                        if gap > 10:  # 10 seconds silence to end recording
                            self.recorder.stop_recording()

                # Small delay to reduce CPU usage
                time.sleep(0.01)

            except IOError as e:
                # Audio read error (common with ALSA loopback if stream disconnects)
                self.consecutive_read_errors += 1
                logger.warning(f"Audio read error #{self.consecutive_read_errors}: {e}")

                if self.consecutive_read_errors > 10:
                    if self.mic_status != 'error':
                        self.mic_status = 'error'
                        self._publish_monitor_active(False)
                        self._log_uptime_event('error', f'Consecutive read errors: {self.consecutive_read_errors}')
                        self.mqtt.publish_mic_status('error', f'Consecutive read errors: {self.consecutive_read_errors}')
                        logger.error("Too many audio read errors - microphone may be offline")

                time.sleep(1)

            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                time.sleep(1)

    def _update_statistics(self, event):
        """Update daily statistics"""
        today = datetime.now().strftime('%Y-%m-%d')

        # Reset if new day
        if self.daily_stats['date'] != today:
            self.daily_stats = {
                'date': today,
                'total_barks': 0,
                'max_decibels': 0,
                'start_time': None,
                'end_time': None,
            }
            # Also reset bucket at midnight
            self.bark_bucket_count = 0
            self.bark_bucket_start = datetime.now()

        # Update stats
        self.daily_stats['total_barks'] += 1
        self.daily_stats['max_decibels'] = max(self.daily_stats['max_decibels'], event.decibels)
        self.daily_stats['end_time'] = event.timestamp.isoformat()
        if not self.daily_stats['start_time']:
            self.daily_stats['start_time'] = event.timestamp.isoformat()

        # Count into the current 5-min bucket
        self.bark_bucket_count += 1

        # Publish updated stats and persist to disk
        self.mqtt.publish_stats(self.daily_stats)
        self._save_daily_stats()

    def _handle_event_grouping(self, event):
        """Handle event grouping for 5-min and 10-min gaps"""
        now = event.timestamp

        # 5-minute gap grouping
        if self.last_bark_time:
            gap = (now - self.last_bark_time).total_seconds()

            if gap > GAP_5MIN:
                # Close current 5-min group
                if self.current_group_5min:
                    self.events_5min.append(self.current_group_5min)
                    self._save_csv_row(self.current_group_5min, '5min')

                # Start new 5-min group
                self.current_group_5min = BarkEventGroup(GAP_5MIN)

            if gap > GAP_10MIN:
                # Close current 10-min group
                if self.current_group_10min:
                    self.events_10min.append(self.current_group_10min)
                    self._save_csv_row(self.current_group_10min, '10min')

                # Start new 10-min group
                self.current_group_10min = BarkEventGroup(GAP_10MIN)

        # Add event to current groups
        if not self.current_group_5min:
            self.current_group_5min = BarkEventGroup(GAP_5MIN)
        self.current_group_5min.add_event(event)

        if not self.current_group_10min:
            self.current_group_10min = BarkEventGroup(GAP_10MIN)
        self.current_group_10min.add_event(event)

    def _save_csv_row(self, group, gap_type):
        """Save event group to CSV file"""
        csv_file = os.path.join(DATA_DIR, f"bark_events_{gap_type}.csv")

        # Create file with header if it doesn't exist
        if not os.path.exists(csv_file):
            with open(csv_file, 'w') as f:
                f.write("date,start_time,end_time,duration_minutes,max_decibels,num_barks\n")

        # Append row
        with open(csv_file, 'a') as f:
            f.write(group.to_csv_row() + "\n")

        logger.info(f"Saved event to {gap_type} CSV: {group.get_duration_minutes():.1f} min, {len(group.events)} barks")

    def stop(self):
        """Stop the detection system"""
        logger.info("Stopping detection system...")

        # Mark monitor as inactive and log shutdown
        self._publish_monitor_active(False)
        self._log_uptime_event('stop')

        # Save final groups
        if self.current_group_5min:
            self.events_5min.append(self.current_group_5min)
            self._save_csv_row(self.current_group_5min, '5min')

        if self.current_group_10min:
            self.events_10min.append(self.current_group_10min)
            self._save_csv_row(self.current_group_10min, '10min')

        # Stop recording
        if self.recorder.is_recording:
            self.recorder.stop_recording()

        # Close audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        self.audio.terminate()

        # Disconnect MQTT
        self.mqtt.publish_status("offline")
        self.mqtt.client.loop_stop()
        self.mqtt.client.disconnect()

        logger.info("Shutdown complete")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Dog Bark Detector Starting")
    logger.info("=" * 60)

    # Check if model exists
    if not os.path.exists(MODEL_PATH):
        logger.error(f"Model not found: {MODEL_PATH}")
        logger.error("Please download the model using the setup script")
        sys.exit(1)

    # Create and start detector
    detector = DogBarkDetector()
    detector.start()

if __name__ == "__main__":
    main()
