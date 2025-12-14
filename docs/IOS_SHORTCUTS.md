# iOS Shortcuts Setup Guide
**Personal AI Assistant - Mobile Capture Workflows**

---

## Overview

This guide provides ready-to-use iOS Shortcuts for capturing thoughts and managing tasks from your iPhone. These shortcuts enable the **<10 second capture** goal while you're on the go.

---

## Prerequisites

- **API Deployed:** `https://ai.gruff.icu` accessible
- **API Key:** Your UUID from `.env` file
- **iOS Device:** iPhone with Shortcuts app (built-in iOS 13+)
- **Network Access:** WiFi or cellular data

---

## Quick Start

### 1. Get Your API Key

From your `.env` file on TrueNAS:
```bash
cat /mnt/data2-pool/andy-ai/personal-ai-assistant/docker/.env | grep API_KEY
```

Copy the UUID (e.g., `D2E1B06E-2C3D-4245-B271-CAA054DEDCE4`)

### 2. Create Your First Shortcut

**Open Shortcuts app** → **+** (New Shortcut) → Follow instructions below

---

## Shortcut 1: Quick Thought Capture

**Purpose:** Capture a thought with text input in <10 seconds

### Actions to Add:

1. **Ask for Input**
   - Prompt: `What's on your mind?`
   - Input Type: `Text`
   - Default Answer: (leave empty)

2. **Text** (API URL)
   - Content: `https://ai.gruff.icu/api/v1/thoughts`

3. **Get Contents of URL**
   - URL: `Text` (from previous action)
   - Method: `POST`
   - Headers:
     - `X-API-Key`: `YOUR_API_KEY_HERE`
     - `Content-Type`: `application/json`
   - Request Body: `JSON`
   - JSON:
     ```json
     {
       "content": "Provided Input"
     }
     ```
     (Select "Provided Input" from magic variable for Ask for Input)

4. **Show Notification**
   - Content: `Thought captured! ✓`
   - Sound: `Default`

### Settings:

**Shortcut Name:** `Quick Capture`

**Icon:** 💭 (thought bubble) - Blue color

**Show in Share Sheet:** OFF

**Show in Widgets:** ON

**Add to Home Screen:** ON (for fastest access)

---

## Shortcut 2: Voice Capture

**Purpose:** Capture a thought using voice dictation

### Actions to Add:

1. **Dictate Text**
   - Language: `English (US)` or your preference
   - Stop Listening: `On Pause`

2. **If** (check if dictation worked)
   - Condition: `Dictated Text` `is not` (empty)

3. **Text** (API URL)
   - Content: `https://ai.gruff.icu/api/v1/thoughts`

4. **Get Contents of URL**
   - URL: `Text` (from previous action)
   - Method: `POST`
   - Headers:
     - `X-API-Key`: `YOUR_API_KEY_HERE`
     - `Content-Type`: `application/json`
   - Request Body: `JSON`
   - JSON:
     ```json
     {
       "content": "Dictated Text"
     }
     ```
     (Select "Dictated Text" from magic variable)

5. **Show Notification**
   - Content: `Voice thought captured! 🎤`

6. **Otherwise**

7. **Show Alert**
   - Title: `No Input`
   - Message: `Please try again`
   - Show Cancel Button: OFF

8. **End If**

### Settings:

**Shortcut Name:** `Voice Capture`

**Icon:** 🎤 (microphone) - Red color

**Show in Widgets:** ON

**Hey Siri:** "Capture thought" or "Quick thought"

---

## Shortcut 3: Capture with Tags

**Purpose:** Add tags while capturing a thought

### Actions to Add:

1. **Ask for Input**
   - Prompt: `What's on your mind?`
   - Input Type: `Text`

2. **Ask for Input**
   - Prompt: `Add tags (comma-separated)?`
   - Input Type: `Text`
   - Default Answer: `idea`

3. **Text** (Process tags)
   - Content: `Provided Input` (from tag input)

4. **Split Text**
   - Text: `Text` (from previous)
   - Separator: `Custom` → `,`

5. **Repeat with Each**
   - Input: `Split Text`

6. **Text** (Trim whitespace)
   - Content: `Repeat Item`
   - Change Case: `Lowercase`

7. **Add to Variable**
   - Variable Name: `TagArray`

8. **End Repeat**

9. **Text** (API URL)
   - Content: `https://ai.gruff.icu/api/v1/thoughts`

10. **Get Contents of URL**
    - URL: `Text`
    - Method: `POST`
    - Headers:
      - `X-API-Key`: `YOUR_API_KEY_HERE`
      - `Content-Type`: `application/json`
    - Request Body: `JSON`
    - JSON:
      ```json
      {
        "content": "Provided Input (from first ask)",
        "tags": "TagArray"
      }
      ```

11. **Show Notification**
    - Content: `Thought captured with tags! 🏷️`

### Settings:

**Shortcut Name:** `Capture with Tags`

**Icon:** 🏷️ (tag) - Orange color

---

## Shortcut 4: Share Sheet Capture

**Purpose:** Capture selected text from any app (Safari, Notes, etc.)

### Actions to Add:

1. **Receive** (from Share Sheet)
   - Input: `Text` or `URLs` or `Safari web pages`

2. **If**
   - Condition: `Shortcut Input` `has any value`

3. **Text** (API URL)
   - Content: `https://ai.gruff.icu/api/v1/thoughts`

4. **Get Contents of URL**
   - URL: `Text`
   - Method: `POST`
   - Headers:
     - `X-API-Key`: `YOUR_API_KEY_HERE`
     - `Content-Type`: `application/json`
   - Request Body: `JSON`
   - JSON:
     ```json
     {
       "content": "Shortcut Input"
     }
     ```

5. **Show Notification**
   - Content: `Shared content captured! 📋`

6. **Otherwise**

7. **Show Alert**
   - Message: `No content to share`

8. **End If**

### Settings:

**Shortcut Name:** `Share to AI Assistant`

**Icon:** 📋 (clipboard) - Green color

**Show in Share Sheet:** ON

**Accepted Types:** `Text`, `URLs`, `Safari web pages`

---

## Shortcut 5: Create Task

**Purpose:** Quickly create a task with optional due date

### Actions to Add:

1. **Ask for Input**
   - Prompt: `Task title?`
   - Input Type: `Text`

2. **Ask for Input**
   - Prompt: `Task description (optional)?`
   - Input Type: `Text`
   - Default Answer: (leave empty)

3. **Ask Each Time**
   - Prompt: `Set a due date?`
   - Type: `Menu`
   - Options:
     - `Today`
     - `Tomorrow`
     - `This Week`
     - `No Due Date`

4. **If** (Today)
   - Get `Current Date`
   - Set Variable: `DueDate`

5. **If** (Tomorrow)
   - Get `Current Date`
   - Adjust Date: Add `1` `Day`
   - Set Variable: `DueDate`

6. **If** (This Week)
   - Get `Current Date`
   - Adjust Date: Add `7` `Days`
   - Set Variable: `DueDate`

7. **Format Date**
   - Date: `DueDate`
   - Format: `Custom` → `yyyy-MM-dd`

8. **Text** (API URL)
   - Content: `https://ai.gruff.icu/api/v1/tasks`

9. **Get Contents of URL**
   - URL: `Text`
   - Method: `POST`
   - Headers:
     - `X-API-Key`: `YOUR_API_KEY_HERE`
     - `Content-Type`: `application/json`
   - Request Body: `JSON`
   - JSON:
     ```json
     {
       "title": "Provided Input (from title)",
       "description": "Provided Input (from description)",
       "due_date": "Formatted Date",
       "priority": "medium"
     }
     ```

10. **Show Notification**
    - Content: `Task created! ✅`

### Settings:

**Shortcut Name:** `Quick Task`

**Icon:** ✅ (checkmark) - Purple color

---

## Shortcut 6: View Recent Thoughts

**Purpose:** See your last 5 thoughts

### Actions to Add:

1. **Text** (API URL)
   - Content: `https://ai.gruff.icu/api/v1/thoughts?limit=5&sort_by=created_at&sort_order=desc`

2. **Get Contents of URL**
   - URL: `Text`
   - Method: `GET`
   - Headers:
     - `X-API-Key`: `YOUR_API_KEY_HERE`

3. **Get Dictionary Value**
   - Key: `data`
   - Dictionary: `Contents of URL`

4. **Repeat with Each**
   - Input: `Dictionary Value`

5. **Get Dictionary Value**
   - Key: `content`
   - Dictionary: `Repeat Item`

6. **Text**
   - Content:
     ```
     • Repeat Item [content]
     ```

7. **Add to Variable**
   - Variable Name: `ThoughtList`

8. **End Repeat**

9. **Show Result**
   - Content: `ThoughtList`
   - (Or use "Show Alert" for cleaner display)

### Settings:

**Shortcut Name:** `Recent Thoughts`

**Icon:** 📝 (memo) - Yellow color

**Show in Widgets:** ON

---

## Widget Setup (Home Screen)

### Add Shortcuts Widget:

1. **Long press** on home screen
2. **Tap** `+` (top left)
3. **Search** for `Shortcuts`
4. **Select** widget size (Small recommended)
5. **Add Widget**
6. **Tap** widget to configure
7. **Select** `Quick Capture` shortcut
8. **Done**

### Suggested Layout:

**Small Widget:** Quick Capture
**Medium Widget:** Voice Capture + Quick Task
**Large Widget:** All shortcuts grid

---

## Siri Integration

### Enable Siri Phrases:

1. **Open Shortcuts app**
2. **Select** a shortcut
3. **Tap** `⋯` (details)
4. **Add to Siri**
5. **Record** phrase:
   - "Capture thought" → Quick Capture
   - "Voice thought" → Voice Capture
   - "New task" → Quick Task
   - "Show thoughts" → Recent Thoughts

### Usage:

- **Hey Siri, capture thought** → Opens text input
- **Hey Siri, voice thought** → Starts dictation
- **Hey Siri, new task** → Creates task

---

## Advanced: Context-Aware Capture

**Purpose:** Automatically add location/time context

### Additional Actions:

1. **Get Current Location**
   - (Requires location permission)

2. **Text** (Format location)
   - Content: `Current Location [Name]`

3. **Text** (Current time of day)
   - Content:
     ```
     If [Current Time] is before 12:00 PM → "morning"
     If [Current Time] is before 6:00 PM → "afternoon"
     If [Current Time] is before 9:00 PM → "evening"
     Otherwise → "night"
     ```

4. **Add to JSON:**
   ```json
   {
     "content": "...",
     "context": {
       "location": "Current Location [Name]",
       "time_of_day": "calculated time"
     }
   }
   ```

---

## Troubleshooting

### "Cannot Connect to Server"

**Causes:**
- No internet connection
- VPN not connected (if required)
- API server down

**Solutions:**
1. Test in browser: `https://ai.gruff.icu/api/v1/health`
2. Check WiFi/cellular connection
3. Verify API key is correct
4. Check TrueNAS container status

### "Unauthorized" / 403 Error

**Cause:** Invalid API key

**Solutions:**
1. Verify API key in `.env` file
2. Copy-paste carefully (no extra spaces)
3. Regenerate API key if needed
4. Update all shortcuts with new key

### Shortcut Runs But No Data Appears

**Debug:**
1. Add "Show Alert" action after API call
2. Display `Contents of URL` to see response
3. Check response for error messages
4. Verify JSON structure matches API expectations

### Voice Dictation Not Working

**Causes:**
- Microphone permission denied
- Background noise
- Network issue (requires internet for Siri)

**Solutions:**
1. Settings > Shortcuts > Allow Microphone
2. Find quiet location
3. Speak clearly, pause when done
4. Check Siri & Search settings

---

## Performance Tips

### Fastest Capture Method:

**Option 1: Home Screen Widget**
- One tap → Direct to input
- ~5 seconds total

**Option 2: Back Tap**
- Settings > Accessibility > Touch > Back Tap
- Double Tap or Triple Tap → Quick Capture
- Works with screen off (after unlock)
- ~3 seconds total

**Option 3: Control Center**
- Settings > Control Center > Add Shortcut
- Swipe down → Tap shortcut
- ~4 seconds total

### Recommendation:

**Primary:** Back tap (fastest)
**Secondary:** Home screen widget (most visible)
**Tertiary:** Siri voice command (hands-free)

---

## Security Considerations

### API Key Storage

Shortcuts store API keys locally, encrypted with device keychain. However:

**Best Practices:**
1. Don't share shortcuts with API key embedded
2. Use separate API keys for different devices (if multi-user)
3. Rotate keys if device is lost/stolen
4. Consider VPN-only access for extra security

### Privacy

- Thoughts are transmitted over HTTPS (encrypted)
- Stored in your private database on moria
- Not shared with third parties
- Location data (if used) stays local to context field

---

## Next Steps

Once shortcuts are working:

1. **Use for one week** - Capture 30+ thoughts
2. **Identify friction** - What slows you down?
3. **Customize** - Adjust prompts, tags, workflows
4. **Build habits** - Set reminders to capture daily thoughts
5. **Add automation** - Time-based prompts (e.g., evening reflection)

---

## Shortcut Templates Summary

| Shortcut | Purpose | Speed | Complexity |
|----------|---------|-------|------------|
| Quick Capture | Text input | ⚡⚡⚡ Fast | ⭐ Simple |
| Voice Capture | Dictation | ⚡⚡ Medium | ⭐ Simple |
| Capture with Tags | Categorize | ⚡ Slower | ⭐⭐ Medium |
| Share Sheet | Capture from apps | ⚡⚡ Medium | ⭐ Simple |
| Quick Task | Create tasks | ⚡⚡ Medium | ⭐⭐ Medium |
| Recent Thoughts | View history | ⚡⚡⚡ Fast | ⭐ Simple |

---

## Example Workflows

### Morning Routine:
1. **Hey Siri, capture thought** → "Goals for today"
2. **Quick Task** → "Review project notes"
3. **Voice Capture** → "Remember to call mom"

### During Meeting:
1. **Share Sheet** → Capture key points from notes
2. **Quick Capture** → "Follow up with John about proposal"

### Evening Reflection:
1. **Recent Thoughts** → Review day's captures
2. **Capture with Tags** → "reflection" tag → Daily summary

---

**Setup Date:** _____________
**Primary Shortcut:** ⬜ Quick Capture | ⬜ Voice Capture | ⬜ Other: _______
**Fastest Method:** ⬜ Widget | ⬜ Back Tap | ⬜ Siri | ⬜ Control Center
**Status:** ⬜ Not Started | ⬜ Configured | ⬜ Testing | ⬜ Daily Use
