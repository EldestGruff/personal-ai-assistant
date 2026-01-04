# Opus Execution Prompt: Phase 3B Spec 2 - AI Intelligence UI

## Context

I'm building a Personal AI Assistant that auto-analyzes thoughts for:
- **Intent classification** (task/note/reminder/question/idea)
- **Auto-suggested tags** (with confidence scores)
- **Task detection** (actionable items → task suggestions)

**CRITICAL:** The backend analysis is **ALREADY WORKING**. Thoughts are being analyzed, data is being stored, but the web UI doesn't display any of it yet.

---

## Current State

**Backend (Working):**
- ✅ Thoughts analyzed on capture via `ThoughtIntelligenceService`
- ✅ Data stored in `thoughts.suggested_tags` (JSON array with tag/confidence/reason)
- ✅ Task suggestions created in `task_suggestions` table
- ✅ API endpoints exist: `/task-suggestions/pending`, `/task-suggestions/{id}/accept`, etc.
- ✅ Settings control auto-analysis: `user_settings.auto_tagging_enabled = true`

**Frontend (Missing):**
- ❌ No display of `suggested_tags` when viewing thoughts
- ❌ No "accept tags" button to apply suggestions
- ❌ No task suggestion cards/workflow
- ❌ No admin settings page
- ❌ No user profile page

**Example Data in Database:**
```json
// thoughts.suggested_tags
[
  {"tag": "home-improvement", "confidence": 0.8, "reason": "Mentions building things"},
  {"tag": "creativity", "confidence": 0.7, "reason": "Exploring possibilities"}
]

// task_suggestions row
{
  "id": "uuid",
  "title": "List Marvel statues for sale",
  "description": "Search Facebook marketplace...",
  "confidence": 0.85,
  "status": "pending"
}
```

---

## What You Need to Build

### 1. Enhanced Thought Display

**Modify `ui.renderThoughtItem()` in `web/app.js`:**

Show suggested tags with confidence badges:
```html
<div class="suggested-tags-section">
  <span class="label">💡 Suggested tags:</span>
  <span class="suggested-tag" data-tag="home-improvement">
    home-improvement <small>(80%)</small>
    <button class="accept-tag">✓</button>
  </span>
  <button class="accept-all-tags">Accept All</button>
</div>
```

**Visual Design:**
- Suggested tags: outlined style (dashed border)
- Applied tags: solid style (filled background)
- Confidence shown as percentage
- Click ✓ to accept individual tag
- "Accept All" applies all suggestions at once

---

### 2. Task Suggestion Cards

**Add new API client methods in `web/app.js`:**
```javascript
async getPendingTaskSuggestions() {
  return await this.request('/task-suggestions/pending');
}

async acceptTaskSuggestion(suggestionId) {
  return await this.request(`/task-suggestions/${suggestionId}/accept`, {
    method: 'POST'
  });
}

async rejectTaskSuggestion(suggestionId, reason) {
  return await this.request(`/task-suggestions/${suggestionId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason })
  });
}
```

**New Dashboard Section:**
```html
<div class="card task-suggestions-card">
  <h3>🎯 Task Suggestions</h3>
  <div class="task-suggestion">
    <div class="suggestion-header">
      <span class="suggestion-title">List Marvel statues for sale</span>
      <span class="confidence-badge">85%</span>
    </div>
    <p class="suggestion-description">Search Facebook marketplace...</p>
    <div class="suggestion-actions">
      <button class="btn-accept">✓ Create Task</button>
      <button class="btn-reject">✗ Dismiss</button>
      <button class="btn-modify">✏️ Modify</button>
    </div>
  </div>
</div>
```

---

### 3. Admin Settings Page

**New HTML file: `web/admin.html`**

Create tabbed interface:
- **Tab 1: Auto-Analysis Settings**
  - Enable/disable auto-tagging
  - Enable/disable task detection
  - Task suggestion mode (suggest/auto_create/disabled)
  
- **Tab 2: User Profile**
  - Ongoing projects (text area)
  - Interests (text area)
  - Work style notes
  - ADHD considerations
  
- **Tab 3: Backend Configuration**
  - Primary AI backend selector
  - Secondary backend selector
  - Test connection buttons

**Navigation:**
Add "⚙️ Settings" button to main dashboard header that links to `/dashboard/admin.html`

---

### 4. CSS Styling

**Add to `web/styles.css`:**

```css
/* Suggested Tags */
.suggested-tags-section {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(100, 150, 255, 0.1);
  border-radius: 4px;
  border: 1px dashed rgba(100, 150, 255, 0.3);
}

.suggested-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  margin: 0.25rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px dashed rgba(100, 150, 255, 0.5);
  border-radius: 3px;
  font-size: 0.85rem;
}

.suggested-tag small {
  color: rgba(255, 255, 255, 0.6);
}

.accept-tag {
  background: transparent;
  border: none;
  color: #4ade80;
  cursor: pointer;
  font-size: 1rem;
  padding: 0 0.25rem;
}

/* Task Suggestions */
.task-suggestions-card {
  margin-top: 1rem;
}

.task-suggestion {
  background: rgba(100, 150, 255, 0.1);
  border: 1px solid rgba(100, 150, 255, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.suggestion-title {
  font-weight: 600;
  font-size: 1.1rem;
}

.confidence-badge {
  background: rgba(74, 222, 128, 0.2);
  color: #4ade80;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.suggestion-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-accept {
  background: #4ade80;
  color: #1a1a1a;
}

.btn-reject {
  background: #ef4444;
}

.btn-modify {
  background: #3b82f6;
}
```

---

## Implementation Requirements

**Standards to Follow:**
- All code must follow existing patterns in `app.js`
- Use existing `api.request()` method for API calls
- Add error handling with `showError()` helper
- Update `loadData()` to also fetch task suggestions
- Keep mobile-responsive (works on iPhone)
- Dark mode compatible

**File Modifications:**
1. `web/app.js` - Add task suggestion logic, enhance thought display
2. `web/index.html` - Add task suggestions section to dashboard
3. `web/admin.html` - NEW file for settings/profile management
4. `web/styles.css` - Add styling for new components

**Testing Checklist:**
- [ ] Suggested tags appear when viewing thoughts
- [ ] Accept tag button adds tag to thought.tags
- [ ] Accept all applies all suggestions
- [ ] Task suggestion cards load on dashboard
- [ ] Accept creates real task
- [ ] Reject dismisses suggestion
- [ ] Admin page loads and saves settings
- [ ] Mobile responsive on iPhone

---

## Output Format

Provide complete files ready for deployment:

```javascript
// web/app.js (modified sections)
[code]

// web/admin.html (complete new file)
[code]

// web/styles.css (additions)
[code]
```

---

## Attached Specification

The full Phase 3B Spec 2 is attached: `Phase3B_Spec2_AIIntelligence.md`

**Focus areas from spec:**
- Section: "Enhanced Prompt Engineering" (understand the personal context)
- Section: "Task Suggestion Workflow" (UI patterns)
- Section: "Admin Page UI" (settings interface)

Generate production-ready code. The backend works - just build the UI to surface it! 🚀
