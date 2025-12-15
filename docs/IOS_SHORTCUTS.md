# iOS Shortcuts Setup Guide
**Personal AI Assistant - Mobile Capture Workflows**

---

## Quick Reference

**API Endpoint:** `https://ai.gruff.icu/api/v1`
**API Key:** `ad8c1f1e-bad4-4f6b-a4ac-a7674bf1ce03`
**Authentication:** `Authorization: Bearer ad8c1f1e-bad4-4f6b-a4ac-a7674bf1ce03`

---

## Shortcut 1: Quick Thought Capture

**Purpose:** Capture a thought with text input in <10 seconds

### Step-by-Step Setup:

1. **Open Shortcuts app** on your iPhone
2. Tap **+** (top right) to create new shortcut
3. Tap **Add Action**

### Actions to Add:

**Action 1: Ask for Input**
- Search for: `Ask for Input`
- Tap it to add
- Configure:
  - **Prompt:** `What's on your mind?`
  - **Input Type:** Text
  - **Default Answer:** (leave blank)

**Action 2: Get Contents of URL**
- Search for: `Get Contents of URL`
- Tap it to add
- Configure:
  - **URL:** `https://ai.gruff.icu/api/v1/thoughts`
  - **Method:** POST
  - Tap **Show More** ▼
  - **Headers:** Tap "Add new field"
    - Key: `Authorization`
    - Value: `Bearer ad8c1f1e-bad4-4f6b-a4ac-a7674bf1ce03`
  - **Request Body:** JSON
  - Tap the JSON field and configure:
    ```json
    {
      "content": "Provided Input"
    }
    ```
    - When typing "Provided Input", tap on it and select the magic variable from "Ask for Input"

**Action 3: Show Notification**
- Search for: `Show Notification`
- Configure:
  - **Text:** `Thought captured! ✓`

### Final Settings:

1. Tap the shortcut name at top (says "New Shortcut")
2. Rename to: `Quick Capture`
3. Tap the icon to change it:
   - Choose 💭 (thought bubble)
   - Color: Blue
4. Enable these options:
   - **Show in Share Sheet:** OFF
   - **Add to Home Screen:** ON
5. Tap **Done**

### Testing:

1. Tap the shortcut to run it
2. Type "test thought"
3. You should see "Thought captured! ✓"

---

## Shortcut 2: Voice Capture

**Purpose:** Capture a thought using voice dictation

### Actions to Add:

**Action 1: Dictate Text**
- Search for: `Dictate Text`
- Configure:
  - **Language:** English (US)
  - **Stop Listening:** On Pause

**Action 2: Get Contents of URL**
- **URL:** `https://ai.gruff.icu/api/v1/thoughts`
- **Method:** POST
- **Headers:**
  - `Authorization`: `Bearer ad8c1f1e-bad4-4f6b-a4ac-a7674bf1ce03`
- **Request Body:** JSON
  ```json
  {
    "content": "Dictated Text"
  }
  ```
  (Select "Dictated Text" from magic variables)

**Action 3: Show Notification**
- **Text:** `Voice thought captured! 🎤`

### Settings:
- **Name:** `Voice Capture`
- **Icon:** 🎤 (microphone) - Red
- **Add to Siri:** "Capture thought"

---

## Shortcut 3: Share Sheet Capture

**Purpose:** Capture selected text from Safari, Notes, or any app

### Actions to Add:

**Action 1: Get Contents of URL**
- **URL:** `https://ai.gruff.icu/api/v1/thoughts`
- **Method:** POST
- **Headers:**
  - `Authorization`: `Bearer ad8c1f1e-bad4-4f6b-a4ac-a7674bf1ce03`
- **Request Body:** JSON
  ```json
  {
    "content": "Shortcut Input"
  }
  ```
  (Select "Shortcut Input" from magic variables)

**Action 2: Show Notification**
- **Text:** `Shared content captured! 📋`

### Settings:
- **Name:** `Share to AI`
- **Icon:** 📋 (clipboard) - Green
- **Show in Share Sheet:** ON
- **Accepted Types:** Text, URLs, Safari web pages

**Usage:** In Safari or Notes, select text → Share → Share to AI

---

## Shortcut 4: Quick Task

**Purpose:** Create a task quickly

### Actions to Add:

**Action 1: Ask for Input**
- **Prompt:** `Task title?`
- **Input Type:** Text

**Action 2: Ask for Input**
- **Prompt:** `Description (optional)?`
- **Input Type:** Text
- **Default Answer:** (leave blank)

**Action 3: Get Contents of URL**
- **URL:** `https://ai.gruff.icu/api/v1/tasks`
- **Method:** POST
- **Headers:**
  - `Authorization`: `Bearer ad8c1f1e-bad4-4f6b-a4ac-a7674bf1ce03`
- **Request Body:** JSON
  ```json
  {
    "title": "Provided Input",
    "description": "Provided Input",
    "priority": "medium"
  }
  ```
  (Map the first "Provided Input" to task title, second to description)

**Action 4: Show Notification**
- **Text:** `Task created! ✅`

### Settings:
- **Name:** `Quick Task`
- **Icon:** ✅ - Purple

---

## Widget Setup (Fastest Access)

### Add to Home Screen:

1. **Long press** empty space on home screen
2. Tap **+** (top left)
3. Search for **Shortcuts**
4. Choose **Small** widget
5. **Add Widget**
6. **Long press** the widget
7. **Edit Widget**
8. Select: `Quick Capture`
9. Tap outside widget to save

**Result:** One-tap access to thought capture from your home screen!

---

## Back Tap Setup (Even Faster!)

This is the fastest way to capture - works even with screen off (after unlock):

1. **Settings** → **Accessibility**
2. **Touch** → **Back Tap**
3. **Double Tap** → Select `Quick Capture`
4. Done!

**Usage:** Double tap the back of your iPhone → instant thought capture

---

## Siri Commands

For each shortcut:

1. Open **Shortcuts app**
2. Long press the shortcut
3. **Rename** → Add to Siri
4. Record your phrase:
   - "Capture thought" → Quick Capture
   - "Voice thought" → Voice Capture
   - "New task" → Quick Task

**Usage:** "Hey Siri, capture thought"

---

## Troubleshooting

### "Cannot Connect to Server"
- Check internet connection
- Test in browser: `https://ai.gruff.icu/api/v1/health`
- Verify you're on WiFi or cellular data

### "Unauthorized" Error
- Double-check the Authorization header
- Make sure it says: `Bearer ad8c1f1e-bad4-4f6b-a4ac-a7674bf1ce03`
- No extra spaces before or after

### Shortcut Runs But Nothing Happens
- Add a "Show Alert" action after "Get Contents of URL"
- Display: `Contents of URL`
- This shows the API response for debugging

### Voice Dictation Doesn't Work
- **Settings** → **Shortcuts** → Allow Microphone
- Speak clearly and pause when done
- Requires internet connection

---

## Summary

| Shortcut | Speed | Access Method |
|----------|-------|---------------|
| Quick Capture | ⚡⚡⚡ | Widget, Back Tap, Siri |
| Voice Capture | ⚡⚡ | Siri, Widget |
| Share to AI | ⚡⚡ | Share Sheet |
| Quick Task | ⚡⚡ | Widget, Siri |

**Recommended Setup:**
1. **Primary:** Quick Capture with Back Tap (fastest)
2. **Secondary:** Voice Capture with Siri (hands-free)
3. **Tertiary:** Share to AI for web content

---

**Status:** Ready to configure ✓
