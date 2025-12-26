# Sonos Speaker Setup Guide

This guide walks you through setting up Sonos speaker control in Home Assistant, integrated with the Air Quality dashboard.

## Prerequisites

- Home Assistant instance running
- Three Sonos speakers (Diurnal, Ickyah, Nocturnal)
- All speakers on the same WiFi network as your Home Assistant instance

## Step 1: Install Sonos Integration

1. Go to **Settings** → **Devices & Services** → **Create Automation**
2. Click **Create Automation** (or use quick integration setup)
3. Look for **Sonos** in the integrations list
4. Click **Sonos** → **Create Integration**

Home Assistant will auto-discover your Sonos speakers on the network.

**Expected Result:**
- Three media_player entities created:
  - `media_player.diurnal`
  - `media_player.ickyah`
  - `media_player.nocturnal`

*(The entity names are based on your Sonos speaker names)*

### Verify Integration

Go to **Settings** → **Devices & Services** → **Sonos**

You should see all three speakers listed with their current playback state.

---

## Step 2: Dashboard Access

The Sonos controls are now available in your dashboard:

1. Open your **Air Quality Dashboard**
2. Click the **Audio** tab (speaker icon)

---

## Step 3: Audio View Features

### Speaker Status Overview
Shows the current playback state of all three speakers at a glance.

### Individual Speaker Control (Mushroom Cards)
Each speaker has full playback control:
- **Now Playing**: Shows current track and artist
- **Volume Control**: Slider + ± buttons
- **Playback Controls**: Play/Pause, Next, Previous
- **Status Indicator**: Shows current state (playing, paused, idle)

### Speaker Grouping
Group speakers for synchronized playback:

- **Group Diurnal** - Syncs all speakers to play the same music
- **Ungroup All** - Separates speakers for independent control

When grouped:
- Music plays on all speakers simultaneously
- Volume can still be controlled individually (after ungrouping)
- One speaker acts as the "coordinator"

### Volume Control
Two ways to adjust volume:

1. **Slider on Individual Cards** - Drag the volume slider on each speaker card
2. **Volume Buttons** - Use + / - buttons for fine-tuning

### Quick Controls
Buttons to control all speakers at once:
- **Play All** - Resume playback on all speakers
- **Pause All** - Pause all speakers
- **Next Track** - Skip to next track on all speakers

---

## Available Controls Summary

### Per-Speaker Controls
| Control | Function |
|---------|----------|
| Play/Pause Button | Toggle playback |
| Next Button | Skip to next track |
| Previous Button | Go back to previous track |
| Volume Slider | Set volume 0-100% |
| Volume Buttons | Adjust volume ±1% |
| Album Art | Shows current track cover (when available) |
| Track Info | Displays song name and artist |

### Multi-Speaker Controls
| Control | Function |
|---------|----------|
| Group Diurnal | Synchronize all speakers |
| Ungroup All | Separate speakers |
| Play All | Resume playback (all speakers) |
| Pause All | Pause playback (all speakers) |
| Next Track | Skip track (all speakers) |

---

## Music Source Support

Your Sonos speakers can play from:

### Direct Integration
- **Spotify** (if linked to your Sonos account)
- **Apple Music**
- **Amazon Music**
- **YouTube Music**
- **Tidal**
- **Local Music Library** (via Sonos app)

### Home Assistant Integration
You can automate music playback:

```yaml
# Example: Play a specific playlist on Diurnal
service: media_player.play_media
data:
  entity_id: media_player.diurnal
  media_content_id: "spotify:playlist:YOUR_PLAYLIST_ID"
  media_content_type: "music"
```

---

## Speaker Groups Explained

### What is Grouping?

Grouping allows multiple Sonos speakers to play the same music in sync. This creates a "zone group."

**Example Scenarios:**
- Group all three for whole-house music
- Group just Diurnal + Ickyah for living room stereo
- Keep Nocturnal independent for bedroom

### How to Group

1. Go to **Audio** tab
2. Click **Group Diurnal** button
3. All speakers will synchronize

One speaker becomes the "coordinator" and controls playback for the group.

### How to Ungroup

1. Click **Ungroup All** button
2. Speakers return to independent control

---

## Troubleshooting

### Speakers Not Showing in Dashboard

**Problem:** Entities don't appear or show as "unavailable"

**Solutions:**
1. Check if Sonos integration is loaded:
   - Settings → Devices & Services → Look for Sonos
2. Restart Home Assistant
3. Check speaker network connectivity
4. Verify speakers are powered on

### Volume Control Not Working

1. Ensure integration is properly loaded
2. Try controlling volume directly in the Sonos app first
3. Check for Home Assistant logs at Settings → System → Logs

### Playback Not Syncing When Grouped

**Known Issue:** If speakers are far apart or have poor WiFi signal, sync may be delayed

**Solution:**
- Check WiFi signal strength on each speaker
- Ungroup and regroup speakers
- Check Sonos app for any error messages

---

## Advanced: Custom Automations

You can create automations to trigger music playback:

### Example: Play Music at Sunrise

```yaml
automation:
  - alias: Morning Music
    trigger:
      platform: time
      at: "06:00:00"
    action:
      - service: media_player.play_media
        target:
          entity_id: media_player.diurnal
        data:
          media_content_id: "spotify:playlist:PLAYLIST_ID"
          media_content_type: "music"
```

### Example: Play Announcement

```yaml
automation:
  - alias: Air Quality Alert
    trigger:
      platform: state
      entity_id: sensor.air_quality_aqi
      to: "150"
    action:
      - service: media_player.play_media
        target:
          entity_id: media_player.nocturnal
        data:
          media_content_id: "announcement_url"
          media_content_type: "music"
```

---

## Integration with Air Quality Monitoring

You can create automations to alert via Sonos speakers:

```yaml
automation:
  - alias: Poor Air Quality Alert - Play on Speakers
    trigger:
      platform: numeric_state
      entity_id: sensor.air_quality_aqi
      above: 200
    action:
      - service: persistent_notification.create
        data:
          title: "Air Quality Alert"
          message: "AQI is {{ states('sensor.air_quality_aqi') }} - Poor air quality!"
      # Optionally play alert sound on speaker
      - service: media_player.play_media
        target:
          entity_id: media_player.diurnal
        data:
          media_content_id: "ding"
          media_content_type: "music"
```

---

## Quick Reference: Entity Names

```yaml
# Media Player Entities
media_player.diurnal      # First speaker
media_player.ickyah       # Second speaker
media_player.nocturnal    # Third speaker

# Available Services
media_player.media_play
media_player.media_pause
media_player.media_play_pause
media_player.media_next_track
media_player.media_previous_track
media_player.volume_set
media_player.volume_mute
media_player.volume_up
media_player.volume_down
media_player.join         # Group speakers
media_player.unjoin       # Ungroup speakers
```

---

## Next Steps

1. **Install HACS** (if not already done) for optional custom cards
2. **Customize** the Audio view dashboard as needed
3. **Create automations** to integrate with air quality alerts
4. **Experiment** with speaker grouping for your use case

Enjoy your Sonos setup!
