# Door Sensors and Smart Speaker Setup Guide

Integrate Zooz Z-Wave door/window sensors and a Dome smart speaker to create a complete security and automation system with voice alarm capabilities.

**Time Required:** 45 minutes (after Z-Wave setup)
**Prerequisites:** Raspberry Pi with Home Assistant running, Z-Wave USB stick and integration configured

---

## Table of Contents

1. [Overview](#overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Part 1: Zooz Door Sensor Setup](#part-1-zooz-door-sensor-setup)
4. [Part 2: Dome Speaker Setup](#part-2-dome-speaker-setup)
5. [Part 3: Dashboard Cards](#part-3-dashboard-cards)
6. [Part 4: Alarm Mode Automations](#part-4-alarm-mode-automations)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers setting up a smart home security system with:

- **Zooz ZSE41 Open/Close Sensors** - Z-Wave door and window sensors
- **Dome by Elexa Smart Speaker** - WiFi-enabled speaker for alarms and notifications
- **Dashboard Cards** - Visual display of sensor states
- **Alarm Modes** - Away (loud), Home (silent), Sleep (beeps)

### Architecture

```
┌──────────────────────────────────────────────┐
│          Home Assistant                      │
│    ┌──────────────────────────────────┐     │
│    │  Z-Wave Integration              │     │
│    │  ┌────────────────────────────┐  │     │
│    │  │ Zooz Door Sensors (x3+)   │  │     │
│    │  │ • Front Door               │  │     │
│    │  │ • Back Door                │  │     │
│    │  │ • Windows                  │  │     │
│    │  └────────────────────────────┘  │     │
│    └──────────────────────────────────┘     │
│                                              │
│    ┌──────────────────────────────────┐     │
│    │  WiFi Integration                │     │
│    │  ┌────────────────────────────┐  │     │
│    │  │ Dome Smart Speaker         │  │     │
│    │  │ • Alarm Sounds             │  │     │
│    │  │ • Notifications            │  │     │
│    │  └────────────────────────────┘  │     │
│    └──────────────────────────────────┘     │
│                                              │
│    ┌──────────────────────────────────┐     │
│    │  Dashboard & Automations         │     │
│    │  • Door Status Cards             │     │
│    │  • Alarm Mode Selector           │     │
│    │  • Mode-based Triggers           │     │
│    └──────────────────────────────────┘     │
└──────────────────────────────────────────────┘
```

---

## Hardware Requirements

| Item | Notes | Cost |
|------|-------|------|
| Zooz ZSE41 Open/Close Sensors | Z-Wave, battery-powered | ~$30-40 each |
| Dome by Elexa Smart Speaker | WiFi, smart home compatible | ~$40-60 |
| Z-Wave USB Stick | Already required for door sensors | ~$25-45 |
| WiFi Network | Standard home WiFi | Already have |

### Why These Products?

**Zooz ZSE41:**
- Reliable Z-Wave protocol (no WiFi needed)
- Good battery life (2-3 years)
- Small form factor
- ~$30-40 each (budget-friendly)
- Easy to pair

**Dome Speaker:**
- WiFi-enabled (integrates with Home Assistant)
- Plays alarm sounds and notifications
- Can be triggered by automations
- Good quality sound
- Compatible with Home Assistant MQTT integration

---

## Part 1: Zooz Door Sensor Setup

### Prerequisites

- Z-Wave USB stick already plugged in
- Z-Wave JS UI container running (from ALTERNATIVE_SENSORS_SETUP.md)
- Home Assistant Z-Wave integration configured

If you haven't set up Z-Wave yet, follow the "Option B: Z-Wave Sensors" section in [ALTERNATIVE_SENSORS_SETUP.md](ALTERNATIVE_SENSORS_SETUP.md).

### Step 1.1: Pair First Zooz Sensor

#### In Home Assistant:

1. Go to **Settings** → **Devices & Services** → **Z-Wave**
2. Click the Z-Wave integration
3. Click **Configure** (or the device)
4. Look for an **"Add Device"** button or option to add a new device
5. If you see it, click it (this puts the Z-Wave controller in inclusion/pairing mode)

**Note:** In some Home Assistant versions, this may be under **"Manage"** → **"Create Group"** or similar. Look for an "Add" or "Include" option.

#### On the Zooz Sensor:

1. Remove the plastic cover from the back
2. Press the button on the sensor **3 times quickly**
3. The LED should start blinking/flashing
4. The sensor will search for Z-Wave networks

#### Pairing Confirmation:

- Wait 10-30 seconds
- Home Assistant should discover and add the sensor
- You'll see a new device appear in the Z-Wave integration
- The LED will stop blinking when paired

### Step 1.2: Name Your Sensor

1. Once paired, Home Assistant shows the device
2. Click on the device name
3. Edit the name to something meaningful:
   - "Front Door"
   - "Back Door"
   - "Living Room Window"
   - etc.

### Step 1.3: Check Sensor Entities

Click on the device to see what sensors it provides:

- **`binary_sensor.XXXX_access_control_door_state`** - Open/Closed status (ON = open, OFF = closed)
- **`sensor.XXXX_battery`** - Battery percentage (0-100)
- Sometimes: temperature (if sensor has built-in temp)

### Step 1.4: Pair Additional Sensors

Repeat Steps 1.1-1.3 for each door/window:
- Front door
- Back door
- Windows (if desired)

### Troubleshooting Pairing Issues

**Sensor won't pair:**
- Make sure Z-Wave add device mode is active (check Z-Wave JS UI)
- Move sensor closer to Z-Wave USB stick
- Factory reset sensor (hold button 10+ seconds) and try again
- Check Z-Wave JS UI is running: `docker ps | grep zwavejs`

**Sensor paired but shows as "Sleeping":**
- Wake it by pressing the button
- Battery-powered devices sleep to save power
- Press the button to wake and get status

---

## Part 2: Dome Speaker Setup

### Step 2.1: Network Setup

1. Download the **Dome by Elexa app** to your phone
2. Create an account if you don't have one
3. Add the speaker to your WiFi network using the app
4. Note the speaker's IP address or hostname

### Step 2.2: Add to Home Assistant

The Dome speaker integrates with Home Assistant via **MQTT** or **HTTP API**.

#### Option A: MQTT Integration (Recommended)

If you already have Mosquitto running (from the Aranet/WS3000 setup):

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **"Dome"** or **"Elexa"**
4. If found, configure it with:
   - Device IP address (from Step 2.1)
   - MQTT broker: `localhost:1883`

#### Option B: Manual MQTT Configuration

Edit your Home Assistant `configuration.yaml`:

```yaml
mqtt:
  switch:
    - name: "Dome Speaker"
      command_topic: "dome/speaker/command"
      state_topic: "dome/speaker/state"
      payload_on: "on"
      payload_off: "off"
      icon: mdi:speaker

  binary_sensor:
    - name: "Dome Speaker Status"
      state_topic: "dome/speaker/status"
      device_class: motion
```

Then restart Home Assistant.

### Step 2.3: Verify Speaker Integration

1. Go to **Developer Tools** → **States**
2. Search for "dome"
3. You should see your speaker listed (may show as `switch.dome_speaker` or similar)
4. Try clicking it to test on/off

---

## Part 3: Dashboard Cards

### Step 3.1: Create Door Sensor Section

Add this to your Home Assistant dashboard (in raw YAML editor):

```yaml
- type: entities
  title: 🚪 Door & Window Status
  show_header_toggle: false
  entities:
    - entity: binary_sensor.front_door_access_control_door_state
      name: Front Door
      icon: mdi:door
    - entity: binary_sensor.back_door_access_control_door_state
      name: Back Door
      icon: mdi:door
    - entity: binary_sensor.kitchen_window_access_control_door_state
      name: Kitchen Window
      icon: mdi:window-closed-variant
    - entity: sensor.front_door_battery
      name: Front Door Battery
      icon: mdi:battery
```

**Entity names will be different for you** - check your actual entity IDs in Developer Tools → States.

### Step 3.2: Battery Status Card

Create a separate card to monitor all battery levels:

```yaml
- type: entities
  title: 🔋 Sensor Batteries
  entities:
    - entity: sensor.front_door_battery
    - entity: sensor.back_door_battery
    - entity: sensor.kitchen_window_battery
```

### Step 3.3: Alarm Mode Selector

Create a helper to store the current alarm mode:

1. Go to **Settings** → **Devices & Services** → **Helpers**
2. Click **+ Create Helper** → **Dropdown**
3. Name: "Alarm Mode"
4. Options (add each one):
   - `away` (Loud alarm, all entry points monitored)
   - `home` (Silent, quiet alerts)
   - `sleep` (Beeps, sleeping residents)
   - `disarmed` (No alarm)
5. Default: `disarmed`

Then add a selector card to your dashboard:

```yaml
- type: entities
  title: 🔔 Alarm Control
  entities:
    - entity: input_select.alarm_mode
      name: Alarm Mode
```

Or use a button stack for quicker access:

```yaml
- type: horizontal-stack
  cards:
    - type: button
      entity: input_select.alarm_mode
      name: Disarmed
      tap_action:
        action: call-service
        service: input_select.select_option
        target:
          entity_id: input_select.alarm_mode
        data:
          option: "disarmed"
      icon: mdi:shield-off

    - type: button
      entity: input_select.alarm_mode
      name: Home
      tap_action:
        action: call-service
        service: input_select.select_option
        target:
          entity_id: input_select.alarm_mode
        data:
          option: "home"
      icon: mdi:home-alert-outline

    - type: button
      entity: input_select.alarm_mode
      name: Away
      tap_action:
        action: call-service
        service: input_select.select_option
        target:
          entity_id: input_select.alarm_mode
        data:
          option: "away"
      icon: mdi:shield-alert

    - type: button
      entity: input_select.alarm_mode
      name: Sleep
      tap_action:
        action: call-service
        service: input_select.select_option
        target:
          entity_id: input_select.alarm_mode
        data:
          option: "sleep"
      icon: mdi:sleep
```

### Step 3.4: Door Status Summary

Create a template sensor to show if any doors are open:

```yaml
template:
  - binary_sensor:
      - name: "Any Door Open"
        unique_id: any_door_open
        state: >
          {{ is_state('binary_sensor.front_door_access_control_door_state', 'on')
             or is_state('binary_sensor.back_door_access_control_door_state', 'on')
             or is_state('binary_sensor.kitchen_window_access_control_door_state', 'on') }}
        icon: >
          {% if this.state == 'on' %}
            mdi:door-open
          {% else %}
            mdi:door-closed
          {% endif %}
```

Then add it to your dashboard:

```yaml
- type: entity
  entity: binary_sensor.any_door_open
  name: Door Status
```

---

## Part 4: Alarm Mode Automations

### Step 4.1: Away Mode - Loud Alarm

This automation triggers the speaker when a door opens in away mode:

```yaml
automation:
  - id: 'alarm_away_mode'
    alias: Alarm - Away Mode
    description: 'Play loud alarm when door opens while away'
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.front_door_access_control_door_state
          - binary_sensor.back_door_access_control_door_state
        to: 'on'
    condition:
      - condition: state
        entity_id: input_select.alarm_mode
        state: 'away'
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.dome_speaker
      - service: mqtt.publish
        data:
          topic: "dome/speaker/sound"
          payload: "alarm_loud"
      - service: persistent_notification.create
        data:
          title: "🚨 ALARM - AWAY MODE"
          message: "Door has been opened! Location: {{ trigger.entity_id }}"
```

### Step 4.2: Home Mode - Silent Alerts

Quiet notification without loud alarm:

```yaml
  - id: 'alarm_home_mode'
    alias: Alarm - Home Mode (Silent)
    description: 'Quiet alert when door opens while home'
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.front_door_access_control_door_state
          - binary_sensor.back_door_access_control_door_state
        to: 'on'
    condition:
      - condition: state
        entity_id: input_select.alarm_mode
        state: 'home'
    action:
      - service: persistent_notification.create
        data:
          title: "🚪 Door Opened"
          message: "{{ trigger.entity_id }} has been opened"
      - service: mqtt.publish
        data:
          topic: "dome/speaker/notification"
          payload: "door_opened"
```

### Step 4.3: Sleep Mode - Beeps

Gentle beeping alert for sleeping residents:

```yaml
  - id: 'alarm_sleep_mode'
    alias: Alarm - Sleep Mode (Beeps)
    description: 'Gentle beeps when door opens while sleeping'
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.front_door_access_control_door_state
          - binary_sensor.back_door_access_control_door_state
        to: 'on'
    condition:
      - condition: state
        entity_id: input_select.alarm_mode
        state: 'sleep'
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.dome_speaker
      - service: mqtt.publish
        data:
          topic: "dome/speaker/sound"
          payload: "beep_gentle"
      - service: persistent_notification.create
        data:
          title: "🔔 Door Alert"
          message: "{{ trigger.entity_id }} opened during sleep"
```

### Step 4.4: Disarmed Mode - No Alarm

No action when disarmed (optional - can skip this one):

```yaml
  - id: 'alarm_disarmed'
    alias: Alarm - Disarmed (No Action)
    description: 'Log door activity when alarm is disarmed'
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.front_door_access_control_door_state
          - binary_sensor.back_door_access_control_door_state
        to: 'on'
    condition:
      - condition: state
        entity_id: input_select.alarm_mode
        state: 'disarmed'
    action:
      - service: persistent_notification.create
        data:
          title: "📝 Door Activity Log"
          message: "{{ trigger.entity_id }} opened (alarm disarmed)"
```

### Where to Add Automations

You can add these automations in two ways:

**Option A: Via Home Assistant UI**
1. Go to **Settings** → **Automations & Scenes** → **Create Automation**
2. Click **Create new automation**
3. Select **"Create from YAML"**
4. Paste the automation YAML

**Option B: Edit automation.yaml**
1. SSH into your Pi
2. Edit the automations file:
   ```bash
   nano ~/homeassistant/automations.yaml
   ```
3. Add the automation blocks from above
4. Restart Home Assistant

---

## Testing

### Test 1: Sensor Status

1. Go to **Developer Tools** → **States**
2. Search for your door sensor
3. Open a door/window
4. The state should change from `off` to `on` within 2 seconds
5. Close it - should change back to `off`

### Test 2: Speaker Control

1. Go to **Developer Tools** → **Services**
2. Search for `switch.turn_on`
3. Target: `switch.dome_speaker`
4. Call the service
5. You should hear the speaker power up

### Test 3: Alarm Mode Selector

1. On your dashboard, click the alarm mode buttons
2. Check that `input_select.alarm_mode` updates
3. Try opening a door - automation should trigger based on mode

### Test 4: Away Mode Alarm

1. Set alarm mode to "Away"
2. Open a door
3. Speaker should activate and play alarm sound
4. Check notification appears

### Test 5: Home Mode Silent

1. Set alarm mode to "Home"
2. Open a door
3. No speaker alarm, but notification appears
4. Much quieter/friendlier

### Test 6: Sleep Mode Beeps

1. Set alarm mode to "Sleep"
2. Open a door
3. Speaker should play gentle beeps
4. Quieter than away mode

---

## Customization

### Add More Doors

To add additional doors/windows:

1. Pair new Zooz sensor (follow Part 1 steps)
2. Update automations - add to `entity_id` list:
   ```yaml
   entity_id:
     - binary_sensor.front_door_access_control_door_state
     - binary_sensor.back_door_access_control_door_state
     - binary_sensor.garage_door_access_control_door_state  # Add new
   ```
3. Add to dashboard cards
4. Update "Any Door Open" template sensor

### Custom Alarm Sounds

If your Dome speaker supports custom sounds, modify the MQTT payloads:

```yaml
# Examples (check Dome documentation for available sounds)
payload: "alarm_loud"      # Full alarm
payload: "beep_gentle"     # Soft beeps
payload: "chime_soft"      # Door chime
payload: "voice_alert"     # Voice message
```

### Time-Based Modes

Make Home Assistant automatically switch modes based on time:

```yaml
automation:
  - id: 'auto_sleep_mode'
    alias: Auto-enable Sleep Mode at Bedtime
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.alarm_mode
        data:
          option: "sleep"

  - id: 'auto_home_mode'
    alias: Auto-enable Home Mode at Wake
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.alarm_mode
        data:
          option: "home"
```

---

## Troubleshooting

### Door Sensor Not Discovered

1. Check Z-Wave JS UI is running:
   ```bash
   docker ps | grep zwavejs
   ```

2. Check Z-Wave controller status:
   - Open Z-Wave JS UI: `http://[PI_IP]:8091`
   - Check if "Driver: Ready"

3. Factory reset the sensor:
   - Hold button 10+ seconds (until LED flashes fast)
   - Try pairing again

### Speaker Not Responding

1. Check speaker is online:
   ```bash
   ping <speaker_ip>
   ```

2. Verify in Dome app that it's connected to WiFi

3. Check Home Assistant MQTT integration is connected:
   - **Settings** → **Devices & Services** → **MQTT**

4. Test MQTT manually:
   ```bash
   mosquitto_pub -h localhost -t "dome/speaker/sound" -m "beep_gentle"
   ```

### Automation Not Triggering

1. Check condition is met:
   - Go to **Developer Tools** → **States**
   - Verify `input_select.alarm_mode` is correct state

2. Check automation is enabled:
   - **Settings** → **Automations & Scenes**
   - Click the automation
   - Toggle should be ON

3. Check logs:
   - **Settings** → **System** → **Logs**
   - Search for your automation name

4. Manually trigger:
   - Open/close door
   - Check Home Assistant notifications appear
   - If notification works, automation logic is OK
   - Issue is likely with speaker integration

### Battery Warnings

Battery level appears as `sensor.XXX_battery` with percentage.

Create an alert when battery is low:

```yaml
automation:
  - id: 'low_battery_alert'
    alias: Low Battery Warning
    trigger:
      - platform: numeric_state
        entity_id:
          - sensor.front_door_battery
          - sensor.back_door_battery
          - sensor.kitchen_window_battery
        below: 20
    action:
      - service: persistent_notification.create
        data:
          title: "🔋 Low Battery Warning"
          message: "{{ trigger.entity_id }} battery is {{ states(trigger.entity_id) }}%"
```

---

## Next Steps

1. **Add motion sensors** - Combine with door sensors for complete security
2. **Create scenes** - Quick "Goodbye!" scene that arms away mode
3. **Add mobile notifications** - Get alerts on your phone
4. **Create automations** - Turn on lights, unlock doors, etc. based on sensor state
5. **Voice integration** - Add voice commands with Alexa/Google Home

---

## Related Documentation

- [Alternative Sensors Setup](ALTERNATIVE_SENSORS_SETUP.md) - Z-Wave and other protocols
- [Home Assistant Setup](HOME_ASSISTANT_SETUP.md) - Full MQTT integration guide
- [Fire Tablet Setup](FIRE_TABLET_SETUP.md) - Display dashboard on tablet

---

## Product Links & Resources

- [Zooz ZSE41 Open/Close Sensor](https://www.zooz.com/)
- [Dome by Elexa](https://www.domebyelexa.com/)
- [Z-Wave Home Automation](https://www.z-wave.com/)
- [Home Assistant Docs](https://www.home-assistant.io/docs/)
