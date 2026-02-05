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
try:
    import tensorflow as tf
    from tensorflow import lite
except ImportError:
    print("Error: TensorFlow not installed")
    print("pip install tensorflow==2.13.0")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Audio Settings
AUDIO_DEVICE_INDEX = None  # None = default device, or specify device number
SAMPLE_RATE = 16000  # Hz (YAMNet requires 16kHz)
CHANNELS = 1  # Mono
CHUNK_DURATION = 1.0  # seconds per analysis chunk
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

# Detection Settings
DOG_BARK_CONFIDENCE_THRESHOLD = 0.70  # 70% confidence minimum
DOG_BARK_CLASS_NAMES = [
    "Animal",
    "Domestic animals, pets",
    "Dog",
    "Bark",
    "Bow-wow",
    "Growling",
    "Whimper",
    "Howl"
]

# Decibel Settings
REFERENCE_PRESSURE = 20e-6  # 20 micropascals (standard reference for dB SPL)
MIN_DB = 30  # Minimum decibel threshold to consider
MAX_DB = 120  # Maximum decibel (for safety)

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

# File Paths
BASE_DIR = os.path.expanduser("~/audio_detection")
MODEL_PATH = os.path.join(BASE_DIR, "models", "yamnet.tflite")
LABELS_PATH = os.path.join(BASE_DIR, "models", "yamnet_class_map.csv")

# Determine recording directory: prefer USB mount if available, fall back to local
USB_MOUNT_PATH = "/mnt/usb/bark_audio/recordings"
LOCAL_RECORDING_PATH = os.path.join(BASE_DIR, "recordings")

def get_recording_dir():
    """Determine the best recording directory to use"""
    # Try USB mount first (for larger storage)
    if os.path.exists("/mnt/usb") and os.access("/mnt/usb", os.W_OK):
        print(f"Using USB mount for recordings: {USB_MOUNT_PATH}")
        return USB_MOUNT_PATH
    # Fall back to local directory
    print(f"USB mount not available, using local directory for recordings: {LOCAL_RECORDING_PATH}")
    return LOCAL_RECORDING_PATH

RECORDING_DIR = get_recording_dir()
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Storage Management
MAX_STORAGE_PERCENT = 95  # Use up to 95% of 1TB before cleanup
AUDIO_QUALITY = "32k"  # Very low quality MP3 for minimal size

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
            self.interpreter = tf.lite.Interpreter(model_path=model_path)
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
        """Load YAMNet class labels from CSV"""
        class_names = []
        try:
            with open(labels_path, 'r') as f:
                # Skip header
                next(f)
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        class_names.append(parts[1].strip('"'))
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

            # Normalize audio to [-1, 1]
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))

            # Get expected input shape from model
            expected_shape = self.input_details[0]['shape']

            # Reshape audio to match model's expected input
            # YAMNet TFLite expects shape (1, num_samples)
            if len(expected_shape) == 2:
                # Model expects (batch, samples)
                if expected_shape[1] != len(audio_data):
                    # Pad or truncate to match expected length
                    if len(audio_data) < expected_shape[1]:
                        # Pad with zeros
                        audio_data = np.pad(audio_data, (0, expected_shape[1] - len(audio_data)))
                    else:
                        # Truncate
                        audio_data = audio_data[:expected_shape[1]]
                audio_data = np.expand_dims(audio_data, axis=0)
            else:
                # Fallback to simple reshape
                audio_data = np.expand_dims(audio_data, axis=0)

            # Ensure dtype matches model expectation
            input_dtype = self.input_details[0]['dtype']
            if input_dtype != np.float32:
                audio_data = audio_data.astype(input_dtype)

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
    Calculate decibel level (dB SPL) from audio data

    Args:
        audio_data: numpy array of audio samples

    Returns:
        float: decibel level
    """
    # Calculate RMS (Root Mean Square) amplitude
    rms = np.sqrt(np.mean(audio_data**2))

    # Avoid log(0)
    if rms < 1e-10:
        return MIN_DB

    # Convert to decibels SPL (Sound Pressure Level)
    # dB = 20 * log10(rms / reference)
    db = 20 * np.log10(rms / REFERENCE_PRESSURE)

    # Clamp to reasonable range
    db = max(MIN_DB, min(MAX_DB, db))

    return db

# ============================================================================
# AUDIO RECORDER
# ============================================================================

class AudioRecorder:
    """Records audio clips of bark events"""

    def __init__(self, recording_dir):
        self.recording_dir = recording_dir
        self.is_recording = False
        self.recording_buffer = []
        self.recording_start_time = None
        self.last_cleanup_check = datetime.now()

    def check_storage_and_cleanup(self):
        """Check storage usage and delete oldest files if over threshold"""
        # Only check every 10 minutes to reduce disk I/O
        if (datetime.now() - self.last_cleanup_check).total_seconds() < 600:
            return

        self.last_cleanup_check = datetime.now()

        try:
            import shutil

            # Get storage stats for the mount point
            stats = shutil.disk_usage(self.recording_dir)
            usage_percent = (stats.used / stats.total) * 100

            if usage_percent > MAX_STORAGE_PERCENT:
                logger.warning(f"Storage at {usage_percent:.1f}% - cleaning up old recordings")

                # Get all MP3 files with their modification times
                files = []
                for root, dirs, filenames in os.walk(self.recording_dir):
                    for filename in filenames:
                        if filename.endswith('.mp3'):
                            filepath = os.path.join(root, filename)
                            mtime = os.path.getmtime(filepath)
                            size = os.path.getsize(filepath)
                            files.append((filepath, mtime, size))

                # Sort by modification time (oldest first)
                files.sort(key=lambda x: x[1])

                # Delete oldest files until we're under 90% usage
                bytes_to_free = stats.total * 0.05  # Free up 5% of space
                bytes_freed = 0
                files_deleted = 0

                for filepath, mtime, size in files:
                    if bytes_freed >= bytes_to_free:
                        break
                    try:
                        os.remove(filepath)
                        bytes_freed += size
                        files_deleted += 1
                    except Exception as e:
                        logger.error(f"Error deleting {filepath}: {e}")

                logger.info(f"Cleanup complete: deleted {files_deleted} files, freed {bytes_freed / 1024 / 1024:.1f} MB")

        except Exception as e:
            logger.error(f"Error during storage cleanup: {e}")

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

    def publish(self, topic, payload):
        """Publish message to MQTT topic"""
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return

        try:
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            self.client.publish(topic, payload)
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
        self.recorder = AudioRecorder(RECORDING_DIR)

        # Event tracking
        self.all_events = []
        self.events_5min = []
        self.events_10min = []
        self.current_group_5min = None
        self.current_group_10min = None
        self.last_bark_time = None
        self.last_bark_confidence = 0
        self.last_bark_decibels = 0

        # Microphone health monitoring
        self.last_audio_received = datetime.now()
        self.last_mqtt_update = datetime.now()
        self.consecutive_read_errors = 0
        self.mic_status = 'starting'

        # Statistics
        self.daily_stats = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_barks': 0,
            'total_duration_min': 0,
            'max_decibels': 0,
            'start_time': None,
            'end_time': None
        }

        # Audio stream
        self.audio = pyaudio.PyAudio()
        self.stream = None

        logger.info("Initialization complete!")

    def start(self):
        """Start the detection system"""
        logger.info("Starting dog bark detection...")

        # Open audio stream
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=AUDIO_DEVICE_INDEX,
                frames_per_buffer=CHUNK_SIZE
            )
            logger.info(f"Audio stream opened (sample rate: {SAMPLE_RATE} Hz)")
        except Exception as e:
            logger.error(f"Error opening audio stream: {e}")
            logger.error("Available audio devices:")
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                logger.error(f"  {i}: {info['name']}")
            raise

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
                # Read audio chunk
                audio_bytes = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)

                # Mark that we received audio successfully
                self.last_audio_received = datetime.now()
                self.consecutive_read_errors = 0

                # Update mic status if it was offline
                if self.mic_status != 'online':
                    self.mic_status = 'online'
                    self.mqtt.publish_mic_status('online', 'Audio stream restored')
                    logger.info("Microphone back online")

                # Calculate decibels
                decibels = calculate_decibels(audio_data)

                # Publish decibels (throttled to every second)
                if int(time.time()) % 1 == 0:
                    self.mqtt.publish_decibels(decibels)

                # Check microphone health (every 30 seconds)
                time_since_audio = (datetime.now() - self.last_audio_received).total_seconds()
                if time_since_audio > 30:
                    if self.mic_status != 'no_data':
                        self.mic_status = 'no_data'
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

                # Classify audio
                predictions = self.classifier.classify_audio(audio_data)

                # Check for dog bark
                is_bark, confidence, class_name = self.classifier.is_dog_bark(predictions)

                if is_bark:
                    # Create bark event
                    event = BarkEvent(datetime.now(), confidence, decibels)
                    self.all_events.append(event)

                    logger.info(f"🐕 DOG BARK DETECTED - Confidence: {confidence:.2f} - Decibels: {decibels:.1f}dB - Class: {class_name}")

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
                'total_duration_min': 0,
                'max_decibels': 0,
                'start_time': None,
                'end_time': None
            }

        # Update stats
        self.daily_stats['total_barks'] += 1
        self.daily_stats['max_decibels'] = max(self.daily_stats['max_decibels'], event.decibels)
        self.daily_stats['end_time'] = event.timestamp.isoformat()

        if not self.daily_stats['start_time']:
            self.daily_stats['start_time'] = event.timestamp.isoformat()

        # Publish updated stats
        self.mqtt.publish_stats(self.daily_stats)

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
