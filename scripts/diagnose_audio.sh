#!/bin/bash
###############################################################################
# Audio Pipeline Diagnostic Script
# =================================
# Run this on the Raspberry Pi via SSH to diagnose why the dog bark detector
# is only hearing silence. Copy the ENTIRE output and paste it back.
#
# Usage:  bash diagnose_audio.sh
###############################################################################

echo "========================================================================"
echo "  AUDIO PIPELINE DIAGNOSTIC - $(date)"
echo "========================================================================"
echo ""

# --- 1. KERNEL MODULE ---
echo "=== 1. ALSA LOOPBACK MODULE ==="
if lsmod | grep -q snd_aloop; then
    echo "snd-aloop: LOADED"
    lsmod | grep snd_aloop
else
    echo "snd-aloop: *** NOT LOADED ***"
    echo "  Fix: sudo modprobe snd-aloop"
fi
echo ""

# --- 2. ALSA DEVICES ---
echo "=== 2. ALSA DEVICES ==="
echo "--- Capture (input) devices ---"
arecord -l 2>&1
echo ""
echo "--- Playback (output) devices ---"
aplay -l 2>&1
echo ""

# --- 3. PulseAudio ---
echo "=== 3. PULSEAUDIO SOURCES ==="
if command -v pactl &>/dev/null; then
    pactl list sources short 2>&1
    echo ""
    echo "Default source:"
    pactl get-default-source 2>&1 || echo "(could not get default source)"
else
    echo "pactl not found (PulseAudio may not be installed)"
fi
echo ""

# --- 4. ASOUND CONFIG ---
echo "=== 4. /etc/asound.conf ==="
if [ -f /etc/asound.conf ]; then
    cat /etc/asound.conf
else
    echo "(no /etc/asound.conf file)"
fi
echo ""

# --- 5. SERVICE STATUS ---
echo "=== 5. SERVICE STATUS ==="
for svc in iphone-audio-stream dog_bark_detector mosquitto; do
    STATUS=$(systemctl is-active "$svc" 2>/dev/null || echo "not-found")
    ENABLED=$(systemctl is-enabled "$svc" 2>/dev/null || echo "not-found")
    printf "  %-30s active=%-12s enabled=%s\n" "$svc" "$STATUS" "$ENABLED"
done
echo ""

# --- 6. IPHONE STREAM SERVICE ---
echo "=== 6. IPHONE-AUDIO-STREAM SERVICE ==="
echo "--- Service file ---"
systemctl cat iphone-audio-stream 2>&1 || echo "(service not found)"
echo ""
echo "--- Last 25 log lines ---"
sudo journalctl -u iphone-audio-stream -n 25 --no-pager 2>&1
echo ""

# --- 7. DOG BARK DETECTOR SERVICE ---
echo "=== 7. DOG_BARK_DETECTOR SERVICE ==="
echo "--- Service file ---"
systemctl cat dog_bark_detector 2>&1 || echo "(service not found)"
echo ""
echo "--- Last 40 log lines ---"
sudo journalctl -u dog_bark_detector -n 40 --no-pager 2>&1
echo ""

# --- 8. FFMPEG PROCESSES ---
echo "=== 8. FFMPEG PROCESSES ==="
ps aux | grep '[f]fmpeg' || echo "(no ffmpeg processes running)"
echo ""

# --- 9. NETWORK: CAN WE REACH THE IPHONE? ---
echo "=== 9. NETWORK TO IPHONE ==="
# Try to find the iPhone IP from the service file
IPHONE_IP=$(systemctl cat iphone-audio-stream 2>/dev/null | grep -oP 'rtsp://\K[0-9.]+' | head -1)
if [ -n "$IPHONE_IP" ]; then
    echo "iPhone IP from service: $IPHONE_IP"
    if ping -c 2 -W 2 "$IPHONE_IP" 2>&1; then
        echo "PING: SUCCESS"
    else
        echo "PING: *** FAILED *** - iPhone may be off or IP changed"
    fi
    echo ""
    echo "--- RTSP stream probe (5s timeout) ---"
    if command -v ffprobe &>/dev/null; then
        timeout 5 ffprobe -v error -show_entries stream=codec_name,sample_rate,channels \
            -rtsp_transport udp "rtsp://${IPHONE_IP}:8554/live.sdp" 2>&1 || \
            echo "*** RTSP PROBE FAILED *** - Periscope HD may not be streaming"
    else
        echo "(ffprobe not found, skipping stream probe)"
    fi
else
    echo "Could not determine iPhone IP from service file"
    echo "Check manually: systemctl cat iphone-audio-stream"
fi
echo ""

# --- 10. LOOPBACK AUDIO TEST ---
echo "=== 10. LOOPBACK AUDIO TEST (3 seconds) ==="
CARD=$(arecord -l 2>/dev/null | grep -i loopback | head -1 | sed -n 's/card \([0-9]*\):.*/\1/p')
if [ -n "$CARD" ]; then
    echo "Loopback card number: $CARD"
    echo "Capture device: hw:$CARD,1"
    echo "Recording 3 seconds from hw:$CARD,1 ..."
    timeout 6 arecord -D "hw:$CARD,1" -f S16_LE -r 16000 -c 1 -d 3 /tmp/diag_audio_test.wav 2>&1
    if [ -f /tmp/diag_audio_test.wav ] && [ -s /tmp/diag_audio_test.wav ]; then
        python3 -c "
import wave, struct, math
try:
    w = wave.open('/tmp/diag_audio_test.wav', 'r')
    n = w.getnframes()
    frames = w.readframes(n)
    w.close()
    if len(frames) < 4:
        print('RESULT: FILE EMPTY - no audio captured')
    else:
        samples = [abs(struct.unpack('<h', frames[i:i+2])[0]) for i in range(0, min(len(frames), 96000), 2)]
        peak = max(samples)
        rms = (sum(s*s for s in samples) / len(samples)) ** 0.5
        db = 20 * math.log10(rms / 32768 + 1e-10) + 90
        print(f'  Samples: {len(samples)}, Peak: {peak}, RMS: {rms:.0f}, ~dB: {db:.1f}')
        if peak < 10:
            print('  RESULT: *** SILENCE *** No audio flowing through loopback')
            print('  This means FFmpeg is NOT writing audio to the loopback device.')
            print('  Check: iphone-audio-stream service, iPhone Periscope HD app, network')
        elif peak < 100:
            print('  RESULT: VERY QUIET - might be noise floor only')
        else:
            print('  RESULT: AUDIO IS FLOWING - loopback pipeline is working')
except Exception as e:
    print(f'  Error analyzing: {e}')
" 2>&1
        rm -f /tmp/diag_audio_test.wav
    else
        echo "*** COULD NOT RECORD *** - loopback device may be busy or misconfigured"
    fi
else
    echo "*** NO LOOPBACK DEVICE FOUND ***"
    echo "  snd-aloop module may not be loaded, or no loopback card exists"
    echo "  Fix: sudo modprobe snd-aloop"
fi
echo ""

# --- 11. MQTT TEST ---
echo "=== 11. MQTT STATUS ==="
if command -v mosquitto_sub &>/dev/null; then
    echo "Listening on audio/decibels for 4 seconds..."
    MSG=$(timeout 4 mosquitto_sub -t "audio/decibels" -C 1 2>&1)
    if [ -n "$MSG" ]; then
        echo "  Received: $MSG"
    else
        echo "  *** NO MESSAGE *** in 4 seconds"
        echo "  Either mosquitto is down or dog_bark_detector is not publishing"
    fi
    echo ""
    echo "Listening on audio/microphone_status for 4 seconds..."
    MSG2=$(timeout 4 mosquitto_sub -t "audio/microphone_status" -C 1 2>&1)
    if [ -n "$MSG2" ]; then
        echo "  Received: $MSG2"
    else
        echo "  (no message on microphone_status in 4s)"
    fi
else
    echo "mosquitto_sub not found - cannot test MQTT"
fi
echo ""

# --- 12. DETECTOR LOG FILE ---
echo "=== 12. DETECTOR LOG FILE (last 30 lines) ==="
LOGDIR="$HOME/audio_detection/logs"
if [ -d "$LOGDIR" ]; then
    LATEST_LOG=$(ls -t "$LOGDIR"/dog_bark_detector_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "Log file: $LATEST_LOG"
        tail -30 "$LATEST_LOG"
    else
        echo "(no log files found in $LOGDIR)"
    fi
else
    echo "(log directory $LOGDIR does not exist)"
fi
echo ""

# --- 13. PYTHON / PYAUDIO DEVICE CHECK ---
echo "=== 13. PYAUDIO DEVICE LIST ==="
python3 -c "
try:
    import pyaudio
    p = pyaudio.PyAudio()
    print(f'PyAudio version: {pyaudio.get_portaudio_version_text()}')
    print(f'Device count: {p.get_device_count()}')
    print()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f'  [{i}] {info[\"name\"]}')
            print(f'       input_ch={info[\"maxInputChannels\"]} rate={info[\"defaultSampleRate\"]}')
    p.terminate()
except Exception as e:
    print(f'Error: {e}')
" 2>&1
echo ""

# --- 14. DISK / RECORDING STORAGE ---
echo "=== 14. STORAGE ==="
df -h /mnt/usb 2>/dev/null || echo "/mnt/usb not mounted"
df -h "$HOME/audio_detection" 2>/dev/null || echo "$HOME/audio_detection not found"
echo ""
echo "Recording files:"
find /mnt/usb/bark_audio/recordings -name "*.mp3" 2>/dev/null | wc -l | xargs -I{} echo "  MP3 files on USB: {}"
find "$HOME/audio_detection/recordings" -name "*.mp3" 2>/dev/null | wc -l | xargs -I{} echo "  MP3 files local: {}"
echo ""

# --- 15. SERVICE FILE CARD NUMBER VS ACTUAL ---
echo "=== 15. CARD NUMBER MISMATCH CHECK ==="
SVC_CARD=$(systemctl cat iphone-audio-stream 2>/dev/null | grep -oP 'hw:\K[0-9]+' | head -1)
ACTUAL_CARD=$(arecord -l 2>/dev/null | grep -i loopback | head -1 | sed -n 's/card \([0-9]*\):.*/\1/p')
if [ -n "$SVC_CARD" ] && [ -n "$ACTUAL_CARD" ]; then
    if [ "$SVC_CARD" = "$ACTUAL_CARD" ]; then
        echo "  Service uses hw:$SVC_CARD, actual loopback is card $ACTUAL_CARD - MATCH OK"
    else
        echo "  *** MISMATCH *** Service uses hw:$SVC_CARD but loopback is actually card $ACTUAL_CARD"
        echo "  This is likely the cause of silence!"
        echo "  Fix: Update the service file to use hw:$ACTUAL_CARD,0"
        echo "  Run: sudo systemctl edit iphone-audio-stream --full"
        echo "  Change hw:$SVC_CARD,0 to hw:$ACTUAL_CARD,0, then:"
        echo "  sudo systemctl daemon-reload && sudo systemctl restart iphone-audio-stream"
    fi
else
    echo "  Service card: ${SVC_CARD:-unknown}, Actual loopback card: ${ACTUAL_CARD:-unknown}"
fi
echo ""

echo "========================================================================"
echo "  DIAGNOSTIC COMPLETE - Copy everything above and paste it back"
echo "========================================================================"
