# Recipe Display Feature - Implementation Plan

## Executive Summary

Add recipe viewing capability to the existing Home Assistant air quality dashboard on the Fire Tablet, allowing users to send recipes from their phone to the kitchen display while cooking.

## Current System Overview

- **Display**: Amazon Fire Tablet (8"/10") running Fully Kiosk Browser
- **Platform**: Home Assistant dashboard on port 8123
- **Data Flow**: MQTT-based sensor data → Home Assistant → Web UI
- **Current Tabs**: Overview, History, Details, Settings, Tablet View

## Design Goals

1. **Seamless Integration**: Recipe display fits naturally into existing HA dashboard
2. **Easy Phone-to-Display**: Quick way to "send" recipes from phone while cooking
3. **Persistent State**: Resume where you left off (scrolling position, current step)
4. **Kitchen-Friendly UI**: Large text, easy navigation, splash-resistant operation
5. **Minimal Complexity**: Leverage existing HA infrastructure, avoid new services

---

## Architecture Options

### **Option 1: Home Assistant Dashboard Tab with iFrame (RECOMMENDED)**

**How it works:**
- Add new "Recipes" tab to Home Assistant dashboard
- Use iFrame card to display recipe websites directly
- Control displayed URL via MQTT/HA input_text helper
- Send recipe URL from phone using HA Companion App

**Pros:**
- ✅ Simplest implementation (no new servers/services)
- ✅ Uses existing MQTT infrastructure
- ✅ Works with any recipe website (AllRecipes, NYT Cooking, etc.)
- ✅ HA Companion App already installed on most phones
- ✅ Can bookmark favorite recipe sites
- ✅ Automatic state persistence via HA

**Cons:**
- ⚠️ Some recipe sites may block iFrame embedding (X-Frame-Options)
- ⚠️ Requires internet connection
- ⚠️ Ads and popups from recipe sites

**Implementation Complexity**: ⭐ Low (2-3 hours)

---

### **Option 2: Home Assistant Dashboard with Recipe Scraper Service**

**How it works:**
- Python service scrapes recipe from URL and extracts clean data
- Stores recipe in HA entities (ingredients, steps, images)
- Custom Lovelace card displays recipe with kitchen-optimized UI
- Send recipe via MQTT topic or HA REST API

**Pros:**
- ✅ Clean, ad-free recipe display
- ✅ Offline support (cache recipes)
- ✅ Custom UI optimized for cooking (step-by-step mode, timers)
- ✅ Integration with HA timers and automations
- ✅ Can add voice control ("Alexa, next step")

**Cons:**
- ⚠️ Requires recipe parsing library (recipe-scrapers Python package)
- ⚠️ Maintenance as recipe sites change formats
- ⚠️ Custom Lovelace card development (JavaScript)

**Implementation Complexity**: ⭐⭐⭐ Medium-High (10-15 hours)

---

### **Option 3: Standalone Web App with MQTT Control**

**How it works:**
- Flask/FastAPI web server on Raspberry Pi (port 5000)
- Recipe viewer web app with mobile-optimized UI
- MQTT messages control displayed recipe
- HA dashboard embeds web app in iFrame

**Pros:**
- ✅ Full control over UI/UX
- ✅ Can add features like grocery lists, meal planning
- ✅ Works independently of Home Assistant
- ✅ Easy to add recipe management features

**Cons:**
- ⚠️ New service to maintain (web server)
- ⚠️ More complex architecture
- ⚠️ Need to handle authentication/security

**Implementation Complexity**: ⭐⭐⭐⭐ High (20-25 hours)

---

### **Option 4: Fully Kiosk Browser URL Switching**

**How it works:**
- Use Fully Kiosk Browser's URL switching feature
- MQTT automation switches browser between HA dashboard and recipe URL
- Send recipe URL via MQTT from phone

**Pros:**
- ✅ Very simple - no HA changes needed
- ✅ Full-screen recipe view (no iFrame restrictions)
- ✅ Works with any website

**Cons:**
- ⚠️ Loses sensor dashboard while viewing recipe
- ⚠️ Manual switching back to sensors
- ⚠️ No split-screen capability

**Implementation Complexity**: ⭐ Very Low (1 hour)

---

## Recommended Approach: Hybrid Solution

**Best of both worlds combining Options 1 and 4:**

### Phase 1: Quick Win (Option 4 + MQTT)
1. Set up MQTT topic: `kitchen/recipe/url`
2. Configure Fully Kiosk automation to switch URLs on MQTT message
3. Create simple web form or MQTT app on phone to send URLs
4. **Time to implement**: 1-2 hours

### Phase 2: Enhanced Integration (Option 1)
1. Add "Recipes" tab to HA dashboard with iFrame card
2. Create HA input_text helper: `input_text.current_recipe_url`
3. Add automation to update iFrame when input_text changes
4. Use HA Companion App to update input_text from phone
5. **Time to implement**: 2-3 hours

### Phase 3: Advanced Features (Option 2 - Optional)
1. Add recipe-scrapers Python service
2. Create custom recipe display card
3. Add step-by-step mode, timers, voice control
4. **Time to implement**: 10-15 hours (as desired features grow)

---

## Detailed Implementation: Phase 1 & 2

### **A. MQTT-Based URL Sending (Phone → Display)**

#### 1. Create MQTT Topic Structure
```yaml
# Topic: kitchen/recipe/url
# Payload: {"url": "https://example.com/recipe/chocolate-chip-cookies"}
```

#### 2. Phone-Side Options

**Option A: Home Assistant Companion App (Easiest)**
- Use HA Companion App notification with action
- Tap "Share to Kitchen Display" button
- Sends URL to HA input_text entity

**Option B: MQTT Dash App (Android)**
- Install MQTT Dash app
- Create "Send Recipe" button
- Enter MQTT broker credentials
- Publishes to `kitchen/recipe/url` topic

**Option C: iOS Shortcuts (iOS)**
- Create shortcut to publish MQTT message
- Add to Share Sheet
- Share recipe from Safari/Chrome → "Send to Kitchen"

**Option D: Custom Web Form**
- Simple HTML page hosted on Raspberry Pi
- Input field + "Send" button
- Posts to MQTT via JavaScript/WebSockets

#### 3. Display-Side Handling

**Fully Kiosk Browser Automation:**
```yaml
# File: homeassistant/automations/recipe_display.yaml
- alias: "Display Recipe URL on Tablet"
  trigger:
    - platform: mqtt
      topic: "kitchen/recipe/url"
  action:
    - service: input_text.set_value
      target:
        entity_id: input_text.current_recipe_url
      data:
        value: "{{ trigger.payload_json.url }}"
    - service: notify.fully_kiosk
      data:
        message: "loadUrl"
        data:
          url: "{{ trigger.payload_json.url }}"
```

### **B. Home Assistant Dashboard Integration**

#### 1. Add Input Text Helper
```yaml
# File: homeassistant/configuration.yaml
input_text:
  current_recipe_url:
    name: Current Recipe URL
    initial: "https://www.allrecipes.com"
    max: 500
```

#### 2. Create Recipe Tab in Dashboard
```yaml
# File: homeassistant/dashboards/air_quality_dashboard.yaml

# Add new view:
- title: Recipe
  path: recipe
  icon: mdi:chef-hat
  badges: []
  cards:
    # Quick return to sensors button
    - type: button
      name: Back to Air Quality
      icon: mdi:air-filter
      tap_action:
        action: navigate
        navigation_path: /lovelace/tablet

    # Recipe URL input (for manual entry)
    - type: entities
      title: Recipe Controls
      entities:
        - entity: input_text.current_recipe_url
          name: Recipe URL
        - type: button
          name: Load Recipe
          icon: mdi:refresh
          action_row: true
          tap_action:
            action: call-service
            service: browser_mod.navigate
            service_data:
              path: "{{ states('input_text.current_recipe_url') }}"

    # iFrame card for recipe display
    - type: iframe
      url_path: input_text.current_recipe_url
      aspect_ratio: 100%
      title: Recipe Viewer
```

#### 3. Send Recipe from Phone (HA Companion App)

**Using HA Mobile App Notification:**
```yaml
# Create script in HA
script:
  send_recipe_to_kitchen:
    alias: "Send Recipe to Kitchen Display"
    fields:
      recipe_url:
        description: "URL of the recipe"
        example: "https://example.com/recipe"
    sequence:
      - service: input_text.set_value
        target:
          entity_id: input_text.current_recipe_url
        data:
          value: "{{ recipe_url }}"
      - service: notify.mobile_app_your_phone
        data:
          message: "Recipe sent to kitchen display!"
```

**iOS Shortcut Example:**
```
1. Get URL from Safari Web Page
2. Call Service: script.send_recipe_to_kitchen
   - recipe_url: [Safari URL]
3. Show notification: "Sent to kitchen!"
```

---

## Alternative: Simple Bookmark Dashboard

**Ultra-Simple Approach (No phone integration):**

1. Create "Recipe Bookmarks" tab in HA dashboard
2. Add button cards for favorite recipe sites:
   - AllRecipes
   - NYT Cooking
   - Budget Bytes
   - Personal recipe notebook (Google Docs)
3. Each button opens recipe site in iFrame or new tab
4. Manually search/browse on the tablet itself

**Pros:**
- ✅ Zero phone integration needed
- ✅ Works offline with saved recipes
- ✅ 30-minute implementation

**Cons:**
- ⚠️ No "send from phone" feature
- ⚠️ Must browse on tablet (less convenient)

---

## Handling iFrame Restrictions

Many recipe sites block iFrame embedding. Solutions:

### **1. Proxy Server (Advanced)**
```python
# Flask app on Raspberry Pi
@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    response = requests.get(url)
    # Remove X-Frame-Options header
    return response.content
```

### **2. Browser Extension on Fully Kiosk**
- Install "Ignore X-Frame-Options" extension
- Enable in Fully Kiosk settings

### **3. Use Recipe-Friendly Sites**
Sites that work well in iFrames:
- Budget Bytes (budgetbytes.com)
- Serious Eats (seriouseats.com)
- King Arthur Baking (kingarthurbaking.com)

### **4. Local Recipe Storage**
- Export recipes to PDF/HTML
- Host locally on Raspberry Pi
- Always accessible, no restrictions

---

## State Persistence (Resume Where You Left Off)

### **Option A: Browser Session Storage**
- Modern browsers remember scroll position
- Works automatically for same URL

### **Option B: HA Sensor for Scroll Position**
```javascript
// Custom JavaScript in Lovelace card
window.addEventListener('scroll', () => {
  hass.callService('input_number', 'set_value', {
    entity_id: 'input_number.recipe_scroll_position',
    value: window.scrollY
  });
});

// Restore on load
window.scrollTo(0, states['input_number.recipe_scroll_position'].state);
```

### **Option C: Step-by-Step Mode (Future Enhancement)**
- Custom recipe parser extracts steps
- HA tracks current step number
- "Next Step" / "Previous Step" buttons
- Voice control: "Alexa, next step"

---

## Recommended Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Recipe Display | Home Assistant iFrame card | Embed recipe websites |
| URL Control | HA input_text helper | Store current recipe URL |
| Phone Integration | HA Companion App + Script | Send URL from phone |
| MQTT Alternative | MQTT topic `kitchen/recipe/url` | Direct URL publishing |
| Future Parsing | recipe-scrapers (Python) | Extract clean recipe data |
| Future UI | Custom Lovelace card (JS) | Step-by-step cooking mode |

---

## Implementation Roadmap

### **Week 1: MVP (Minimum Viable Product)**
- [ ] Add input_text.current_recipe_url to HA configuration
- [ ] Create "Recipe" tab in dashboard with iFrame card
- [ ] Test with recipe bookmark buttons
- [ ] Create HA script for sending recipe from phone
- [ ] Test with HA Companion App

### **Week 2: Phone Integration**
- [ ] Set up iOS Shortcut or Android MQTT Dash
- [ ] Create "Share to Kitchen" functionality
- [ ] Test from various recipe websites
- [ ] Document sites that work/don't work in iFrame

### **Future Enhancements (As Needed)**
- [ ] Add recipe scraper service (recipe-scrapers library)
- [ ] Create custom recipe display card with step mode
- [ ] Add cooking timers integration
- [ ] Voice control ("Alexa, show next step")
- [ ] Grocery list integration
- [ ] Meal planning calendar

---

## Security Considerations

1. **Network Security**
   - HA should be on local network only (no external exposure)
   - If exposing HA externally, use Nabu Casa or reverse proxy with SSL
   - MQTT broker should require authentication

2. **Recipe Site Safety**
   - Only load recipes from trusted sites
   - Be cautious of malicious URLs
   - Consider URL whitelist validation

3. **Fully Kiosk Browser**
   - Enable kiosk mode to prevent tampering
   - Set password for settings access
   - Disable browser navigation (address bar)

---

## Cost Analysis

| Component | Cost | Notes |
|-----------|------|-------|
| Home Assistant | $0 | Already installed |
| MQTT Broker | $0 | Already running (Mosquitto) |
| Recipe iFrame Display | $0 | Built-in HA card |
| HA Companion App | $0 | Free download |
| iOS Shortcuts | $0 | Built-in iOS app |
| MQTT Dash (Android) | $0 | Free app |
| recipe-scrapers library | $0 | Open source Python package |
| **Total** | **$0** | Uses existing infrastructure! |

---

## Sample User Flow

### **Scenario: Sending Recipe While Meal Planning**

1. **On Phone (in bed Sunday morning):**
   - Browse NYT Cooking for recipes
   - Find "One-Pot Chicken and Rice"
   - Tap Share button → "Send to Kitchen Display"
   - iOS Shortcut sends URL to Home Assistant

2. **On Kitchen Tablet:**
   - Recipe appears in "Recipe" tab
   - Tap notification or manually switch to Recipe tab
   - Recipe is displayed full-screen

3. **While Cooking:**
   - Tablet shows recipe with ingredients and steps
   - Can scroll through steps as you cook
   - Tap "Back to Air Quality" to check CO2 levels
   - Return to recipe, scroll position is preserved

4. **After Cooking:**
   - Recipe remains on display until new one is sent
   - Can manually enter different recipe URL if needed

---

## Testing Plan

### **Phase 1: Basic Display**
- [ ] Test iFrame with 5 popular recipe sites
- [ ] Verify tablet display in portrait and landscape
- [ ] Check text readability from 3 feet away
- [ ] Test browser back/forward navigation

### **Phase 2: Phone Integration**
- [ ] Test sending URL from iPhone using Shortcuts
- [ ] Test sending URL from Android using MQTT Dash
- [ ] Verify URL arrives within 2 seconds
- [ ] Test with invalid/malformed URLs

### **Phase 3: Kitchen Use**
- [ ] Cook actual recipe using display
- [ ] Test with wet/floury hands (touch accuracy)
- [ ] Verify scroll position persistence
- [ ] Check display timeout/screen saver behavior

---

## Support Resources

- **Home Assistant iFrame Card**: https://www.home-assistant.io/dashboards/iframe/
- **HA Companion App**: https://companion.home-assistant.io/
- **recipe-scrapers Library**: https://github.com/hhursev/recipe-scrapers
- **MQTT Dash (Android)**: https://play.google.com/store/apps/details?id=net.routix.mqttdash
- **iOS Shortcuts Guide**: https://support.apple.com/guide/shortcuts/welcome/ios

---

## Questions to Consider

Before implementation, decide on:

1. **Primary Use Case**:
   - Send recipes from phone while browsing? → Option 1/2
   - Browse recipes directly on tablet? → Bookmark dashboard
   - Both? → Hybrid approach

2. **Recipe Sources**:
   - Specific websites (AllRecipes, NYT)? → Test iFrame compatibility
   - Personal recipes? → Local storage or Google Docs
   - Recipe apps? → May need screen mirroring instead

3. **Display Mode**:
   - Full-screen recipe (hide sensors)? → Option 4
   - Split view (recipe + sensors)? → Option 1
   - Toggle between modes? → Automation

4. **Future Features**:
   - Voice control needed? → Plan for HA Voice integration
   - Meal planning wanted? → Consider Option 3 (standalone app)
   - Keep it simple? → Stick with Option 1

---

## Next Steps

**Ready to implement? Choose your path:**

### **Path A: Quick & Simple (Recommended to start)**
1. Add Recipe tab with bookmarked recipe sites
2. Test which sites work in iFrame
3. Use tablet to browse recipes (no phone integration yet)
4. **Time**: 30 minutes

### **Path B: Full Phone Integration**
1. Set up input_text helper and automation
2. Create HA script for URL sending
3. Configure iOS Shortcut or Android MQTT app
4. **Time**: 2-3 hours

### **Path C: Advanced Recipe System**
1. Install recipe-scrapers Python library
2. Build recipe parsing service
3. Create custom Lovelace card
4. **Time**: 15-20 hours (multi-week project)

**My recommendation**: Start with Path A to validate the concept, then move to Path B once you confirm it's useful. Path C can wait until you've used the basic version for a few weeks and identified specific pain points.

---

## Conclusion

Adding recipe display to your air quality sensor dashboard is highly feasible and can be done with zero additional cost using your existing Home Assistant infrastructure. The hybrid approach (iFrame + MQTT URL control) provides the best balance of simplicity and functionality.

**Bottom line**: You can have a working recipe display in your kitchen in 1-2 hours of work, with the option to enhance it over time based on your actual usage patterns.

Let me know which approach you'd like to pursue, and I can start implementing!
