// Personal AI Assistant - Dashboard Application
// Vanilla JavaScript implementation
// Phase 3B Spec 2: Enhanced with AI Intelligence UI

// State Management
const state = {
    thoughts: [],
    tasks: [],
    taskSuggestions: [],
    currentView: 'dashboard',
    filters: {
        thoughtSearch: '',
        thoughtTimeframe: 'all',
        thoughtTag: '',
        taskStatus: 'all',
        taskPriority: 'all'
    },
    consciousnessCheck: {
        lastCheck: null,
        autoRefreshInterval: null,
        isLoading: false
    }
};

// API Client
const api = {
    async request(endpoint, options = {}) {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        const headers = {
            'Authorization': `Bearer ${CONFIG.API_KEY}`,
            'Content-Type': 'application/json',
            ...options.headers
        };

        try {
            const response = await fetch(url, { ...options, headers });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
            }

            // Handle 204 No Content (empty response)
            if (response.status === 204) {
                return null;
            }

            const result = await response.json();

            // FastAPI returns { success: true, data: {...} }
            if (result.success && result.data) {
                return result.data;
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            showError(`Failed to ${options.method || 'GET'} ${endpoint}: ${error.message}`);
            throw error;
        }
    },

    async getThoughts() {
        // API has pagination, fetch all thoughts in batches
        let allThoughts = [];
        let offset = 0;
        const limit = 100; // Max allowed by API

        while (true) {
            const response = await this.request(`/thoughts?limit=${limit}&offset=${offset}&sort_by=created_at&sort_order=desc`);

            // Response format: { thoughts: [...], pagination: {...} }
            const thoughts = response.thoughts || [];
            allThoughts = allThoughts.concat(thoughts);

            // Check if there are more results
            if (!response.pagination || !response.pagination.has_more) {
                break;
            }

            offset += limit;
        }

        return allThoughts;
    },

    async getTasks() {
        // API has pagination, fetch all tasks in batches
        let allTasks = [];
        let offset = 0;
        const limit = 100;

        while (true) {
            const response = await this.request(`/tasks?limit=${limit}&offset=${offset}`);

            // Response format: { tasks: [...], pagination: {...} }
            const tasks = response.tasks || [];
            allTasks = allTasks.concat(tasks);

            // Check if there are more results
            if (!response.pagination || !response.pagination.has_more) {
                break;
            }

            offset += limit;
        }

        return allTasks;
    },

    async searchThoughts(query) {
        const response = await this.request(`/thoughts/search?q=${encodeURIComponent(query)}&limit=100`);
        return response.results || [];
    },

    async getConsciousnessCheck(limitRecent = 20) {
        // Manual trigger - runs a new check (used by "Run Now" button)
        const recentThoughts = state.thoughts.slice(0, limitRecent).map(t => ({
            id: t.id,
            content: t.content
        }));

        const response = await this.request(`/consciousness-check-v2`, {
            method: 'POST',
            body: JSON.stringify({
                recent_thoughts: recentThoughts,
                limit_recent: limitRecent,
                include_archived: false
            })
        });
        return response;
    },

    async getLatestConsciousnessCheck() {
        // Load latest cached result from database (no new analysis)
        const response = await this.request('/consciousness-check/latest');
        return response;
    },

    async createThought(content, tags = [], context = {}) {
        const response = await this.request('/thoughts', {
            method: 'POST',
            body: JSON.stringify({ content, tags, context })
        });
        return response;
    },

    async updateThought(thoughtId, updates) {
        const response = await this.request(`/thoughts/${thoughtId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
        return response;
    },

    async deleteThought(thoughtId) {
        await this.request(`/thoughts/${thoughtId}`, {
            method: 'DELETE'
        });
    },

    async updateTask(taskId, updates) {
        const response = await this.request(`/tasks/${taskId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
        return response;
    },

    async deleteTask(taskId) {
        await this.request(`/tasks/${taskId}`, {
            method: 'DELETE'
        });
    },

    // =========================================================================
    // Task Suggestion API Methods (Phase 3B Spec 2)
    // =========================================================================

    async getPendingTaskSuggestions(minConfidence = 0.0) {
        const response = await this.request(`/task-suggestions/pending?min_confidence=${minConfidence}`);
        return response.suggestions || [];
    },

    async acceptTaskSuggestion(suggestionId, modifications = null) {
        const body = modifications ? JSON.stringify(modifications) : null;
        const response = await this.request(`/task-suggestions/${suggestionId}/accept`, {
            method: 'POST',
            body: body
        });
        return response;
    },

    async rejectTaskSuggestion(suggestionId, reason = null) {
        const response = await this.request(`/task-suggestions/${suggestionId}/reject`, {
            method: 'POST',
            body: reason ? JSON.stringify({ reason }) : null
        });
        return response;
    },

    async deleteTaskSuggestion(suggestionId, reason = 'user_deleted') {
        const response = await this.request(`/task-suggestions/${suggestionId}?reason=${encodeURIComponent(reason)}`, {
            method: 'DELETE'
        });
        return response;
    },

    async restoreTaskSuggestion(suggestionId) {
        const response = await this.request(`/task-suggestions/${suggestionId}/restore`, {
            method: 'POST'
        });
        return response;
    },

    async getTaskSuggestionHistory(includeDeleted = false, limit = 50) {
        const response = await this.request(`/task-suggestions/history?include_deleted=${includeDeleted}&limit=${limit}`);
        return response.suggestions || [];
    },

    // =========================================================================
    // Tag Application API Methods (Phase 3B Spec 2)
    // =========================================================================

    async applyTagsToThought(thoughtId, tags) {
        // Use the existing update endpoint to apply tags
        const response = await this.request(`/thoughts/${thoughtId}`, {
            method: 'PUT',
            body: JSON.stringify({ tags })
        });
        return response;
    }
};

// Utility Functions
const utils = {
    getCurrentTimeOfDay() {
        const hour = new Date().getHours();
        if (hour < 6) return 'night';
        if (hour < 12) return 'morning';
        if (hour < 18) return 'afternoon';
        if (hour < 22) return 'evening';
        return 'night';
    },

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    },

    formatTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit'
        });
    },

    formatDateTime(dateString) {
        return `${this.formatDate(dateString)} at ${this.formatTime(dateString)}`;
    },

    timeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        return this.formatDate(dateString);
    },

    isToday(dateString) {
        const date = new Date(dateString);
        const today = new Date();
        return date.toDateString() === today.toDateString();
    },

    isThisWeek(dateString) {
        const date = new Date(dateString);
        const today = new Date();
        const weekAgo = new Date(today);
        weekAgo.setDate(weekAgo.getDate() - 7);
        return date >= weekAgo;
    },

    isThisMonth(dateString) {
        const date = new Date(dateString);
        const today = new Date();
        return date.getMonth() === today.getMonth() &&
               date.getFullYear() === today.getFullYear();
    },

    getHour(dateString) {
        const date = new Date(dateString);
        return date.getHours();
    },

    getDayOfWeek(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { weekday: 'short' });
    },

    formatConfidence(confidence) {
        return Math.round((confidence || 0) * 100) + '%';
    }
};

// UI Rendering Functions
const ui = {
    // Dashboard View
    renderDashboard() {
        this.renderQuickCapture();
        this.renderQuickStats();
        this.renderClaudeInsights();
        this.renderTaskSuggestions();
        this.renderRecentThoughts();
        this.renderTopTags();
        this.renderActiveTasks();
    },

    renderQuickCapture() {
        const container = document.getElementById('quick-capture-container');
        if (!container) return;

        // Get all existing tags for suggestions
        const allTags = new Set();
        state.thoughts.forEach(t => {
            if (t.tags) t.tags.forEach(tag => allTags.add(tag));
        });
        const sortedTags = Array.from(allTags).sort();

        container.innerHTML = `
            <div class="card quick-capture-card">
                <h2>✍️ Quick Capture</h2>
                <form id="capture-form" class="capture-form">
                    <textarea 
                        id="capture-input" 
                        class="capture-input" 
                        placeholder="What's on your mind? (Press Ctrl/Cmd+Enter to submit)"
                        rows="3"
                    ></textarea>
                    
                    <div class="capture-tags">
                        <div class="tag-suggestions">
                            ${sortedTags.slice(0, 8).map(tag => `
                                <button type="button" class="tag-suggestion" data-tag="${tag}">${tag}</button>
                            `).join('')}
                        </div>
                        <input 
                            type="text" 
                            id="new-tag-input" 
                            class="new-tag-input" 
                            placeholder="Add custom tag (comma-separated)"
                        />
                        <div id="selected-tags" class="selected-tags"></div>
                    </div>
                    
                    <div class="capture-actions">
                        <button type="submit" class="btn-capture">💾 Capture Thought</button>
                        <button type="button" id="clear-capture" class="btn-clear">✕ Clear</button>
                    </div>
                </form>
            </div>
        `;

        this.setupCaptureListeners();
    },

    setupCaptureListeners() {
        const form = document.getElementById('capture-form');
        const input = document.getElementById('capture-input');
        const newTagInput = document.getElementById('new-tag-input');
        const clearBtn = document.getElementById('clear-capture');
        const selectedTagsContainer = document.getElementById('selected-tags');
        
        // Track selected tags
        let selectedTags = [];

        // Tag suggestion buttons
        document.querySelectorAll('.tag-suggestion').forEach(btn => {
            btn.addEventListener('click', () => {
                const tag = btn.dataset.tag;
                if (!selectedTags.includes(tag)) {
                    selectedTags.push(tag);
                    this.updateSelectedTags(selectedTags, selectedTagsContainer);
                }
            });
        });

        // Add tags from text input (comma-separated)
        newTagInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                const tags = newTagInput.value.split(',').map(t => t.trim().toLowerCase()).filter(Boolean);
                tags.forEach(tag => {
                    if (!selectedTags.includes(tag)) {
                        selectedTags.push(tag);
                    }
                });
                newTagInput.value = '';
                this.updateSelectedTags(selectedTags, selectedTagsContainer);
            }
        });

        // Keyboard shortcut (Ctrl/Cmd+Enter to submit)
        input.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                form.dispatchEvent(new Event('submit'));
            }
        });

        // Clear button
        clearBtn.addEventListener('click', () => {
            input.value = '';
            newTagInput.value = '';
            selectedTags = [];
            this.updateSelectedTags(selectedTags, selectedTagsContainer);
            input.focus();
        });

        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const content = input.value.trim();
            if (!content) {
                showError('Please enter some content');
                return;
            }

            // Auto-capture context
            const context = {
                time_of_day: utils.getCurrentTimeOfDay(),
                active_app: 'Web UI',
                captured_via: 'dashboard'
            };

            try {
                showLoading();
                const newThought = await api.createThought(content, selectedTags, context);
                
                // Add to local state
                state.thoughts.unshift(newThought);
                
                // Clear form
                input.value = '';
                newTagInput.value = '';
                selectedTags = [];
                this.updateSelectedTags(selectedTags, selectedTagsContainer);
                
                // Refresh dashboard (also loads new task suggestions if any)
                await loadTaskSuggestions();
                this.renderDashboard();
                ui.updateHeaderStats();
                ui.populateTagFilter();
                
                // Show success feedback
                input.placeholder = '✅ Thought captured! Add another?';
                setTimeout(() => {
                    input.placeholder = "What's on your mind? (Press Ctrl/Cmd+Enter to submit)";
                }, 2000);
                
                input.focus();
            } catch (error) {
                console.error('Failed to create thought:', error);
            } finally {
                hideLoading();
            }
        });
    },

    updateSelectedTags(tags, container) {
        container.innerHTML = tags.map(tag => `
            <span class="tag selected-tag">
                ${tag}
                <button class="remove-tag" data-tag="${tag}">×</button>
            </span>
        `).join('');

        // Add remove handlers
        container.querySelectorAll('.remove-tag').forEach(btn => {
            btn.addEventListener('click', () => {
                const tag = btn.dataset.tag;
                const index = tags.indexOf(tag);
                if (index > -1) {
                    tags.splice(index, 1);
                    this.updateSelectedTags(tags, container);
                }
            });
        });
    },

    renderQuickStats() {
        const todayCount = state.thoughts.filter(t => utils.isToday(t.created_at)).length;
        const weekCount = state.thoughts.filter(t => utils.isThisWeek(t.created_at)).length;
        const pendingSuggestions = state.taskSuggestions.length;

        document.getElementById('dash-total-thoughts').textContent = state.thoughts.length;
        document.getElementById('dash-total-tasks').textContent = state.tasks.length;
        document.getElementById('dash-today-thoughts').textContent = todayCount;
        document.getElementById('dash-week-thoughts').textContent = weekCount;
        
        // Update pending suggestions count if element exists
        const pendingEl = document.getElementById('dash-pending-suggestions');
        if (pendingEl) {
            pendingEl.textContent = pendingSuggestions;
        }
    },

    // =========================================================================
    // Task Suggestions UI (Phase 3B Spec 2)
    // =========================================================================

    renderTaskSuggestions() {
        const container = document.getElementById('task-suggestions-container');
        if (!container) return;

        if (state.taskSuggestions.length === 0) {
            container.innerHTML = `
                <div class="card task-suggestions-card">
                    <div class="card-header">
                        <h2>🎯 Task Suggestions</h2>
                        <button class="btn-icon" onclick="loadTaskSuggestions()" title="Refresh suggestions">↻</button>
                    </div>
                    <div class="empty-state">
                        <div class="empty-state-icon">✨</div>
                        <div class="empty-state-text">No pending suggestions</div>
                        <div class="empty-state-hint">AI will suggest tasks when it detects actionable items</div>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="card task-suggestions-card">
                <div class="card-header">
                    <h2>🎯 Task Suggestions <span class="suggestion-count">${state.taskSuggestions.length}</span></h2>
                    <button class="btn-icon" onclick="loadTaskSuggestions()" title="Refresh suggestions">↻</button>
                </div>
                <div class="task-suggestions-list">
                    ${state.taskSuggestions.map(suggestion => this.renderTaskSuggestionCard(suggestion)).join('')}
                </div>
            </div>
        `;

        this.attachTaskSuggestionHandlers();
    },

    renderTaskSuggestionCard(suggestion) {
        const confidenceClass = suggestion.confidence >= 0.8 ? 'high' : 
                               suggestion.confidence >= 0.6 ? 'medium' : 'low';
        
        return `
            <div class="task-suggestion" data-suggestion-id="${suggestion.id}">
                <div class="suggestion-header">
                    <span class="suggestion-title">${this.escapeHtml(suggestion.title)}</span>
                    <span class="confidence-badge ${confidenceClass}">${utils.formatConfidence(suggestion.confidence)}</span>
                </div>
                ${suggestion.description ? `
                    <p class="suggestion-description">${this.escapeHtml(suggestion.description)}</p>
                ` : ''}
                <div class="suggestion-meta">
                    <span class="priority-badge ${suggestion.priority}">${suggestion.priority}</span>
                    ${suggestion.estimated_effort_minutes ? `
                        <span class="effort-badge">⏱️ ${suggestion.estimated_effort_minutes}min</span>
                    ` : ''}
                    <span class="suggestion-time">${utils.timeAgo(suggestion.created_at)}</span>
                </div>
                ${suggestion.reasoning ? `
                    <div class="suggestion-reasoning">
                        <small>💡 ${this.escapeHtml(suggestion.reasoning)}</small>
                    </div>
                ` : ''}
                <div class="suggestion-actions">
                    <button class="btn-accept" data-action="accept">✓ Create Task</button>
                    <button class="btn-modify" data-action="modify">✏️ Modify</button>
                    <button class="btn-reject" data-action="reject">✗ Dismiss</button>
                </div>
            </div>
        `;
    },

    attachTaskSuggestionHandlers() {
        document.querySelectorAll('.task-suggestion').forEach(card => {
            const suggestionId = card.dataset.suggestionId;
            
            card.querySelector('[data-action="accept"]')?.addEventListener('click', async () => {
                await this.handleAcceptSuggestion(suggestionId);
            });
            
            card.querySelector('[data-action="reject"]')?.addEventListener('click', async () => {
                await this.handleRejectSuggestion(suggestionId);
            });
            
            card.querySelector('[data-action="modify"]')?.addEventListener('click', () => {
                this.handleModifySuggestion(suggestionId);
            });
        });
    },

    async handleAcceptSuggestion(suggestionId) {
        try {
            showLoading();
            const result = await api.acceptTaskSuggestion(suggestionId);
            
            // Update local state
            state.taskSuggestions = state.taskSuggestions.filter(s => s.id !== suggestionId);
            if (result.task) {
                state.tasks.unshift(result.task);
            }
            
            // Re-render
            this.renderTaskSuggestions();
            this.renderActiveTasks();
            ui.updateHeaderStats();
            
            showSuccess('Task created from suggestion!');
        } catch (error) {
            console.error('Failed to accept suggestion:', error);
        } finally {
            hideLoading();
        }
    },

    async handleRejectSuggestion(suggestionId) {
        try {
            showLoading();
            await api.rejectTaskSuggestion(suggestionId);
            
            // Update local state
            state.taskSuggestions = state.taskSuggestions.filter(s => s.id !== suggestionId);
            
            // Re-render
            this.renderTaskSuggestions();
            
            showSuccess('Suggestion dismissed');
        } catch (error) {
            console.error('Failed to reject suggestion:', error);
            showError('Failed to dismiss suggestion');
        } finally {
            hideLoading();
        }
    },

    handleModifySuggestion(suggestionId) {
        const suggestion = state.taskSuggestions.find(s => s.id === suggestionId);
        if (!suggestion) return;

        // Show modification modal
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal modify-suggestion-modal">
                <div class="modal-header">
                    <h3>✏️ Modify Task Suggestion</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                </div>
                <form id="modify-suggestion-form">
                    <div class="form-group">
                        <label for="mod-title">Title</label>
                        <input type="text" id="mod-title" value="${this.escapeHtml(suggestion.title)}" required>
                    </div>
                    <div class="form-group">
                        <label for="mod-description">Description</label>
                        <textarea id="mod-description" rows="3">${this.escapeHtml(suggestion.description || '')}</textarea>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="mod-priority">Priority</label>
                            <select id="mod-priority">
                                <option value="low" ${suggestion.priority === 'low' ? 'selected' : ''}>Low</option>
                                <option value="medium" ${suggestion.priority === 'medium' ? 'selected' : ''}>Medium</option>
                                <option value="high" ${suggestion.priority === 'high' ? 'selected' : ''}>High</option>
                                <option value="critical" ${suggestion.priority === 'critical' ? 'selected' : ''}>Critical</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="mod-effort">Estimated Minutes</label>
                            <input type="number" id="mod-effort" value="${suggestion.estimated_effort_minutes || ''}" min="1">
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button type="submit" class="btn-primary">✓ Create Modified Task</button>
                        <button type="button" class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);

        // Handle form submission
        modal.querySelector('#modify-suggestion-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const modifications = {
                title: modal.querySelector('#mod-title').value.trim(),
                description: modal.querySelector('#mod-description').value.trim() || null,
                priority: modal.querySelector('#mod-priority').value,
                estimated_effort_minutes: parseInt(modal.querySelector('#mod-effort').value) || null
            };

            try {
                showLoading();
                const result = await api.acceptTaskSuggestion(suggestionId, modifications);
                
                // Update local state
                state.taskSuggestions = state.taskSuggestions.filter(s => s.id !== suggestionId);
                if (result.task) {
                    state.tasks.unshift(result.task);
                }
                
                modal.remove();
                this.renderTaskSuggestions();
                this.renderActiveTasks();
                ui.updateHeaderStats();
                
                showSuccess('Task created with modifications!');
            } catch (error) {
                console.error('Failed to create modified task:', error);
            } finally {
                hideLoading();
            }
        });
    },

    async renderClaudeInsights(forceRefresh = false) {
        const container = document.getElementById('claude-insights');

        // Prevent multiple simultaneous requests
        if (state.consciousnessCheck.isLoading) {
            return;
        }

        // Show loading state
        state.consciousnessCheck.isLoading = true;
        container.innerHTML = `
            <div class="insights-loading">
                <div class="spinner-small"></div>
                <span>${forceRefresh ? 'Running new analysis...' : 'Loading latest insights...'}</span>
            </div>
        `;

        try {
            let response;
            
            if (forceRefresh) {
                // Manual refresh - run a new consciousness check
                response = await api.getConsciousnessCheck(20);
            } else {
                // Page load - just get the latest cached result
                response = await api.getLatestConsciousnessCheck();
            }

            if (!response || !response.summary) {
                container.innerHTML = this.emptyState('🤖', 'No insights yet', 'Scheduler will run checks automatically every 30 minutes');
                state.consciousnessCheck.isLoading = false;
                return;
            }

            // Store in state
            state.consciousnessCheck.lastCheck = response;
            state.consciousnessCheck.isLoading = false;

            // Display the insights
            this.displayClaudeInsightsV2(response);

        } catch (error) {
            console.error('Failed to load Claude insights:', error);
            state.consciousnessCheck.isLoading = false;
            container.innerHTML = `
                <div class="insights-error">
                    <p>⚠️ Failed to load AI insights</p>
                    <button onclick="ui.renderClaudeInsights(true)" class="btn-retry">Run New Check</button>
                </div>
            `;
        }
    },

    displayClaudeInsights(insights) {
        const container = document.getElementById('claude-insights');

        container.innerHTML = `
            <div class="insights-content">
                <div class="insights-summary">
                    <p>${this.escapeHtml(insights.summary)}</p>
                    <div class="insights-meta">
                        <span>📊 ${insights.thoughts_analyzed} thoughts analyzed</span>
                        <span>⚡ ${insights.tokens_used} tokens</span>
                        <span>🕒 ${utils.timeAgo(insights.timestamp)}</span>
                        <span class="next-refresh">Auto-checks every 30 minutes</span>
                    </div>
                </div>

                ${insights.themes && insights.themes.length > 0 ? `
                    <div class="insights-section">
                        <h4>🎯 Key Themes</h4>
                        <div class="insights-tags">
                            ${insights.themes.map(theme => `<span class="insight-tag theme-tag">${this.escapeHtml(theme)}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}

                ${insights.suggested_actions && insights.suggested_actions.length > 0 ? `
                    <div class="insights-section">
                        <h4>💡 Suggested Actions</h4>
                        <ul class="insights-list">
                            ${insights.suggested_actions.map(action => `<li>${this.escapeHtml(action)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${insights.positives && insights.positives.length > 0 ? `
                    <div class="insights-section positive">
                        <h4>✨ Positives</h4>
                        <ul class="insights-list">
                            ${insights.positives.map(positive => `<li>${this.escapeHtml(positive)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${insights.concerns && insights.concerns.length > 0 ? `
                    <div class="insights-section concern">
                        <h4>⚠️ Concerns</h4>
                        <ul class="insights-list">
                            ${insights.concerns.map(concern => `<li>${this.escapeHtml(concern)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    },

    displayClaudeInsightsV2(response) {
        const container = document.getElementById('claude-insights');
        
        // Extract backend name from backend_stats (first key)
        const backendUsed = Object.keys(response.backend_stats || {})[0] || 'unknown';
        const backendInfo = response.backend_stats?.[backendUsed];

        container.innerHTML = `
            <div class="insights-content">
                <div class="insights-summary">
                    <p>${this.escapeHtml(response.summary)}</p>
                    <div class="insights-meta">
                        <span>🤖 ${backendUsed}</span>
                        ${backendInfo?.tokens_used ? `<span>⚡ ${backendInfo.tokens_used} tokens</span>` : ''}
                        ${backendInfo?.processing_time_ms ? `<span>⏱️ ${backendInfo.processing_time_ms}ms</span>` : ''}
                        <span>📊 ${response.source_analyses} thoughts analyzed</span>
                        <span>🕒 ${utils.timeAgo(response.timestamp)}</span>
                    </div>
                </div>

                ${response.themes && response.themes.length > 0 ? `
                    <div class="insights-section">
                        <h4>🎯 Key Themes</h4>
                        <div class="insights-tags">
                            ${response.themes.map(theme => {
                                const themeText = typeof theme === 'string' ? theme : theme.theme;
                                return `<span class="insight-tag theme-tag">${this.escapeHtml(themeText)}</span>`;
                            }).join('')}
                        </div>
                    </div>
                ` : ''}

                ${response.suggested_actions && response.suggested_actions.length > 0 ? `
                    <div class="insights-section">
                        <h4>💡 Suggested Actions</h4>
                        <ul class="insights-list">
                            ${response.suggested_actions.map(action => {
                                const actionText = typeof action === 'string' ? action : action.action;
                                const priority = typeof action === 'object' && action.priority ? `<span class="priority-badge ${action.priority}">${action.priority}</span>` : '';
                                return `<li>${this.escapeHtml(actionText)} ${priority}</li>`;
                            }).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${response.related_thought_ids && response.related_thought_ids.length > 0 ? `
                    <div class="insights-section">
                        <h4>🔗 Related Thoughts</h4>
                        <p>${response.related_thought_ids.length} related thoughts found</p>
                    </div>
                ` : ''}
            </div>
        `;
    },

    renderRecentThoughts() {
        const container = document.getElementById('dash-recent-thoughts');
        const recent = state.thoughts.slice(0, 5);

        if (recent.length === 0) {
            container.innerHTML = this.emptyState('💭', 'No thoughts yet', 'Use Quick Capture above to get started!');
            return;
        }

        container.innerHTML = recent.map(thought => this.renderThoughtItem(thought)).join('');
        this.attachThoughtHandlers();
    },

    // =========================================================================
    // Enhanced Thought Item with Suggested Tags (Phase 3B Spec 2)
    // =========================================================================

    renderThoughtItem(thought, showActions = true) {
        const hasSuggestedTags = thought.suggested_tags && thought.suggested_tags.length > 0;
        const appliedTags = thought.tags || [];
        
        // Filter out suggested tags that are already applied
        const pendingSuggestedTags = hasSuggestedTags 
            ? thought.suggested_tags.filter(st => !appliedTags.includes(st.tag))
            : [];

        return `
            <div class="thought-item" data-thought-id="${thought.id}">
                <div class="thought-view">
                    <div class="thought-content">${this.escapeHtml(thought.content)}</div>
                    <div class="thought-meta">
                        <span class="thought-time">${utils.timeAgo(thought.created_at)}</span>
                        ${appliedTags.length > 0 ? `
                            <div class="thought-tags">
                                ${appliedTags.map(tag => `<span class="tag applied-tag">${tag}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                    
                    ${pendingSuggestedTags.length > 0 ? `
                        <div class="suggested-tags-section">
                            <span class="suggested-tags-label">💡 Suggested tags:</span>
                            <div class="suggested-tags-list">
                                ${pendingSuggestedTags.map(st => `
                                    <span class="suggested-tag" data-tag="${this.escapeHtml(st.tag)}" data-thought-id="${thought.id}">
                                        ${this.escapeHtml(st.tag)} <small>(${utils.formatConfidence(st.confidence)})</small>
                                        <button class="accept-tag" title="Accept this tag">✓</button>
                                        <button class="decline-tag" title="Dismiss this tag">✕</button>
                                    </span>
                                `).join('')}
                            </div>
                            <div class="suggested-tags-actions">
                                <button class="accept-all-tags btn-small" data-thought-id="${thought.id}">Accept All</button>
                                <button class="dismiss-all-tags btn-small" data-thought-id="${thought.id}">Dismiss All</button>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${showActions ? `
                        <div class="thought-actions">
                            <button class="btn-icon edit-thought" title="Edit thought">✏️</button>
                            <button class="btn-icon delete-thought" title="Delete thought">🗑️</button>
                        </div>
                    ` : ''}
                </div>
                <div class="thought-edit" style="display: none;">
                    <textarea class="edit-content">${this.escapeHtml(thought.content)}</textarea>
                    <input type="text" class="edit-tags" placeholder="Tags (comma-separated)" value="${appliedTags.join(', ')}">
                    <div class="edit-actions">
                        <button class="btn-save">💾 Save</button>
                        <button class="btn-cancel">✕ Cancel</button>
                    </div>
                </div>
            </div>
        `;
    },

    attachThoughtHandlers() {
        // Edit buttons
        document.querySelectorAll('.edit-thought').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const thoughtItem = e.target.closest('.thought-item');
                thoughtItem.querySelector('.thought-view').style.display = 'none';
                thoughtItem.querySelector('.thought-edit').style.display = 'block';
                thoughtItem.querySelector('.edit-content').focus();
            });
        });

        // Cancel edit buttons
        document.querySelectorAll('.btn-cancel').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const thoughtItem = e.target.closest('.thought-item');
                thoughtItem.querySelector('.thought-view').style.display = 'block';
                thoughtItem.querySelector('.thought-edit').style.display = 'none';
            });
        });

        // Save edit buttons
        document.querySelectorAll('.btn-save').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const thoughtItem = e.target.closest('.thought-item');
                const thoughtId = thoughtItem.dataset.thoughtId;
                const content = thoughtItem.querySelector('.edit-content').value.trim();
                const tagsInput = thoughtItem.querySelector('.edit-tags').value;
                const tags = tagsInput.split(',').map(t => t.trim().toLowerCase()).filter(Boolean);

                if (!content) {
                    showError('Content cannot be empty');
                    return;
                }

                try {
                    showLoading();
                    const updated = await api.updateThought(thoughtId, { content, tags });
                    
                    // Update local state
                    const index = state.thoughts.findIndex(t => t.id === thoughtId);
                    if (index !== -1) {
                        state.thoughts[index] = { ...state.thoughts[index], ...updated };
                    }
                    
                    // Re-render current view
                    switchView(state.currentView);
                } catch (error) {
                    console.error('Failed to update thought:', error);
                } finally {
                    hideLoading();
                }
            });
        });

        // Delete buttons
        document.querySelectorAll('.delete-thought').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const thoughtItem = e.target.closest('.thought-item');
                const thoughtId = thoughtItem.dataset.thoughtId;
                
                if (!confirm('Delete this thought? This cannot be undone.')) {
                    return;
                }

                try {
                    showLoading();
                    await api.deleteThought(thoughtId);
                    
                    // Remove from local state
                    state.thoughts = state.thoughts.filter(t => t.id !== thoughtId);
                    
                    // Re-render
                    ui.updateHeaderStats();
                    switchView(state.currentView);
                } catch (error) {
                    console.error('Failed to delete thought:', error);
                } finally {
                    hideLoading();
                }
            });
        });

        // =====================================================================
        // Suggested Tag Handlers (Phase 3B Spec 2)
        // =====================================================================

        // Accept individual tag
        document.querySelectorAll('.suggested-tag .accept-tag').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const tagSpan = e.target.closest('.suggested-tag');
                const tag = tagSpan.dataset.tag;
                const thoughtId = tagSpan.dataset.thoughtId;
                
                await this.acceptSuggestedTag(thoughtId, tag);
            });
        });

        // Decline individual tag
        document.querySelectorAll('.suggested-tag .decline-tag').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const tagSpan = e.target.closest('.suggested-tag');
                const tag = tagSpan.dataset.tag;
                const thoughtId = tagSpan.dataset.thoughtId;
                
                await this.declineSuggestedTag(thoughtId, tag);
            });
        });

        // Accept all tags
        document.querySelectorAll('.accept-all-tags').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const thoughtId = btn.dataset.thoughtId;
                await this.acceptAllSuggestedTags(thoughtId);
            });
        });

        // Dismiss all tags
        document.querySelectorAll('.dismiss-all-tags').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const thoughtId = btn.dataset.thoughtId;
                await this.dismissAllSuggestedTags(thoughtId);
            });
        });
    },

    async acceptSuggestedTag(thoughtId, tagToAdd) {
        const thought = state.thoughts.find(t => t.id === thoughtId);
        if (!thought) return;

        const currentTags = thought.tags || [];
        if (currentTags.includes(tagToAdd)) return;

        const newTags = [...currentTags, tagToAdd];

        try {
            showLoading();
            const updated = await api.applyTagsToThought(thoughtId, newTags);
            
            // Update local state
            const index = state.thoughts.findIndex(t => t.id === thoughtId);
            if (index !== -1) {
                state.thoughts[index] = { ...state.thoughts[index], ...updated };
            }
            
            // Re-render current view
            switchView(state.currentView);
            showSuccess(`Tag "${tagToAdd}" added!`);
        } catch (error) {
            console.error('Failed to add tag:', error);
        } finally {
            hideLoading();
        }
    },

    async acceptAllSuggestedTags(thoughtId) {
        const thought = state.thoughts.find(t => t.id === thoughtId);
        if (!thought || !thought.suggested_tags) return;

        const currentTags = thought.tags || [];
        const suggestedTagNames = thought.suggested_tags.map(st => st.tag);
        
        // Merge current and suggested (no duplicates)
        const newTags = [...new Set([...currentTags, ...suggestedTagNames])];

        try {
            showLoading();
            const updated = await api.applyTagsToThought(thoughtId, newTags);
            
            // Update local state
            const index = state.thoughts.findIndex(t => t.id === thoughtId);
            if (index !== -1) {
                state.thoughts[index] = { ...state.thoughts[index], ...updated };
            }
            
            // Re-render current view
            switchView(state.currentView);
            showSuccess('All suggested tags applied!');
        } catch (error) {
            console.error('Failed to apply tags:', error);
        } finally {
            hideLoading();
        }
    },

    async declineSuggestedTag(thoughtId, tagToRemove) {
        const thought = state.thoughts.find(t => t.id === thoughtId);
        if (!thought || !thought.suggested_tags) return;

        // Update local state - remove this suggested tag
        const index = state.thoughts.findIndex(t => t.id === thoughtId);
        if (index !== -1) {
            state.thoughts[index].suggested_tags = state.thoughts[index].suggested_tags.filter(
                st => st.tag !== tagToRemove
            );
        }

        // Re-render current view
        switchView(state.currentView);
    },

    async dismissAllSuggestedTags(thoughtId) {
        const thought = state.thoughts.find(t => t.id === thoughtId);
        if (!thought || !thought.suggested_tags) return;

        // Update local state - clear all suggested tags
        const index = state.thoughts.findIndex(t => t.id === thoughtId);
        if (index !== -1) {
            state.thoughts[index].suggested_tags = [];
        }

        // Re-render current view
        switchView(state.currentView);
        showSuccess('All tag suggestions dismissed');
    },

    renderTopTags() {
        const container = document.getElementById('dash-top-tags');
        const tagCounts = {};

        state.thoughts.forEach(thought => {
            if (thought.tags) {
                thought.tags.forEach(tag => {
                    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
                });
            }
        });

        const topTags = Object.entries(tagCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);

        if (topTags.length === 0) {
            container.innerHTML = this.emptyState('🏷️', 'No tags yet', 'Add tags to organize your thoughts');
            return;
        }

        container.innerHTML = topTags.map(([tag, count]) => `
            <div class="tag-cloud-item">
                <span>${tag}</span>
                <span class="tag-count">${count}</span>
            </div>
        `).join('');
    },

    renderActiveTasks() {
        const container = document.getElementById('dash-active-tasks');
        const active = state.tasks.filter(t => t.status !== 'done' && t.status !== 'cancelled').slice(0, 5);

        if (active.length === 0) {
            container.innerHTML = this.emptyState('✅', 'No active tasks', 'All caught up!');
            return;
        }

        container.innerHTML = active.map(task => this.renderTaskItem(task)).join('');
        this.attachTaskHandlers();
    },

    attachTaskHandlers() {
        // Complete task button
        document.querySelectorAll('.complete-task').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const taskItem = e.target.closest('.task-item');
                const taskId = taskItem.dataset.taskId;
                await this.completeTask(taskId);
            });
        });

        // Uncomplete task button
        document.querySelectorAll('.uncomplete-task').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const taskItem = e.target.closest('.task-item');
                const taskId = taskItem.dataset.taskId;
                await this.uncompleteTask(taskId);
            });
        });

        // Edit task button
        document.querySelectorAll('.edit-task').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const taskItem = e.target.closest('.task-item');
                taskItem.querySelector('.task-view').style.display = 'none';
                taskItem.querySelector('.task-edit').style.display = 'block';
                taskItem.querySelector('.edit-task-title').focus();
            });
        });

        // Cancel edit button
        document.querySelectorAll('.btn-cancel-task').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const taskItem = e.target.closest('.task-item');
                taskItem.querySelector('.task-view').style.display = 'block';
                taskItem.querySelector('.task-edit').style.display = 'none';
            });
        });

        // Save task button
        document.querySelectorAll('.btn-save-task').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const taskItem = e.target.closest('.task-item');
                const taskId = taskItem.dataset.taskId;
                
                const title = taskItem.querySelector('.edit-task-title').value.trim();
                const description = taskItem.querySelector('.edit-task-description').value.trim();
                const priority = taskItem.querySelector('.edit-task-priority').value;
                const effortStr = taskItem.querySelector('.edit-task-effort').value;
                const dueDate = taskItem.querySelector('.edit-task-due').value;

                if (!title) {
                    showError('Task title cannot be empty');
                    return;
                }

                const updates = {
                    title,
                    description: description || null,
                    priority,
                    estimated_effort_minutes: effortStr ? parseInt(effortStr) : null,
                    due_date: dueDate || null
                };

                await this.updateTask(taskId, updates);
            });
        });

        // Delete task button
        document.querySelectorAll('.delete-task').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const taskItem = e.target.closest('.task-item');
                const taskId = taskItem.dataset.taskId;
                const task = state.tasks.find(t => t.id === taskId);
                
                if (!confirm(`Delete task "${task?.title}"? This cannot be undone.`)) {
                    return;
                }

                await this.deleteTask(taskId);
            });
        });
    },

    async completeTask(taskId) {
        try {
            showLoading();
            const updated = await api.updateTask(taskId, { status: 'done' });
            
            // Update local state
            const index = state.tasks.findIndex(t => t.id === taskId);
            if (index !== -1) {
                state.tasks[index] = { ...state.tasks[index], ...updated };
            }
            
            // Re-render current view
            switchView(state.currentView);
            ui.updateHeaderStats();
            showSuccess('Task completed! 🎉');
        } catch (error) {
            console.error('Failed to complete task:', error);
        } finally {
            hideLoading();
        }
    },

    async uncompleteTask(taskId) {
        try {
            showLoading();
            const updated = await api.updateTask(taskId, { status: 'pending' });
            
            // Update local state
            const index = state.tasks.findIndex(t => t.id === taskId);
            if (index !== -1) {
                state.tasks[index] = { ...state.tasks[index], ...updated };
            }
            
            // Re-render current view
            switchView(state.currentView);
            ui.updateHeaderStats();
            showSuccess('Task reopened');
        } catch (error) {
            console.error('Failed to uncomplete task:', error);
        } finally {
            hideLoading();
        }
    },

    async updateTask(taskId, updates) {
        try {
            showLoading();
            const updated = await api.updateTask(taskId, updates);
            
            // Update local state
            const index = state.tasks.findIndex(t => t.id === taskId);
            if (index !== -1) {
                state.tasks[index] = { ...state.tasks[index], ...updated };
            }
            
            // Re-render current view
            switchView(state.currentView);
            showSuccess('Task updated!');
        } catch (error) {
            console.error('Failed to update task:', error);
        } finally {
            hideLoading();
        }
    },

    async deleteTask(taskId) {
        try {
            showLoading();
            await api.deleteTask(taskId);
            
            // Remove from local state
            state.tasks = state.tasks.filter(t => t.id !== taskId);
            
            // Re-render
            ui.updateHeaderStats();
            switchView(state.currentView);
            showSuccess('Task deleted');
        } catch (error) {
            console.error('Failed to delete task:', error);
        } finally {
            hideLoading();
        }
    },

    // Thoughts View
    renderThoughtsView() {
        const container = document.getElementById('thoughts-list');
        let filtered = this.filterThoughts();

        if (filtered.length === 0) {
            container.innerHTML = this.emptyState('🔍', 'No thoughts found', 'Try adjusting your filters');
            return;
        }

        container.innerHTML = filtered.map(thought => this.renderThoughtItem(thought, true)).join('');
        this.attachThoughtHandlers();
    },

    filterThoughts() {
        let filtered = [...state.thoughts];

        // Search filter
        if (state.filters.thoughtSearch) {
            const query = state.filters.thoughtSearch.toLowerCase();
            filtered = filtered.filter(t =>
                t.content.toLowerCase().includes(query) ||
                (t.tags && t.tags.some(tag => tag.toLowerCase().includes(query)))
            );
        }

        // Time filter
        if (state.filters.thoughtTimeframe !== 'all') {
            filtered = filtered.filter(t => {
                switch (state.filters.thoughtTimeframe) {
                    case 'today': return utils.isToday(t.created_at);
                    case 'week': return utils.isThisWeek(t.created_at);
                    case 'month': return utils.isThisMonth(t.created_at);
                    default: return true;
                }
            });
        }

        // Tag filter
        if (state.filters.thoughtTag) {
            filtered = filtered.filter(t =>
                t.tags && t.tags.includes(state.filters.thoughtTag)
            );
        }

        return filtered;
    },

    // Tasks View
    renderTasksView() {
        const container = document.getElementById('tasks-list');
        let filtered = this.filterTasks();

        if (filtered.length === 0) {
            container.innerHTML = this.emptyState('✅', 'No tasks found', 'Try adjusting your filters');
            return;
        }

        container.innerHTML = filtered.map(task => this.renderTaskItem(task)).join('');
        this.attachTaskHandlers();
    },

    renderTaskItem(task) {
        const isDone = task.status === 'done';
        const canComplete = task.status === 'pending' || task.status === 'in_progress';
        
        return `
            <div class="task-item priority-${task.priority} status-${task.status}" data-task-id="${task.id}">
                <div class="task-view">
                    <div class="task-content">
                        <div class="task-title ${isDone ? 'completed' : ''}">${this.escapeHtml(task.title)}</div>
                        ${task.description ? `<div class="task-description">${this.escapeHtml(task.description)}</div>` : ''}
                        <div class="task-meta">
                            <span class="task-badge priority">${task.priority}</span>
                            <span class="task-badge status">${task.status.replace('_', ' ')}</span>
                            ${task.due_date ? `<span>Due: ${utils.formatDate(task.due_date)}</span>` : ''}
                            ${task.estimated_effort_minutes ? `<span>⏱️ ${task.estimated_effort_minutes}min</span>` : ''}
                            <span>${utils.timeAgo(task.created_at)}</span>
                        </div>
                    </div>
                    <div class="task-actions">
                        ${canComplete ? `
                            <button class="btn-icon complete-task" title="Mark as complete">✓</button>
                        ` : ''}
                        ${isDone ? `
                            <button class="btn-icon uncomplete-task" title="Mark as incomplete">↶</button>
                        ` : ''}
                        <button class="btn-icon edit-task" title="Edit task">✏️</button>
                        <button class="btn-icon delete-task" title="Delete task">🗑️</button>
                    </div>
                </div>
                <div class="task-edit" style="display: none;">
                    <input type="text" class="edit-task-title" value="${this.escapeHtml(task.title)}" placeholder="Task title">
                    <textarea class="edit-task-description" placeholder="Description">${this.escapeHtml(task.description || '')}</textarea>
                    <div class="edit-task-meta">
                        <select class="edit-task-priority">
                            <option value="low" ${task.priority === 'low' ? 'selected' : ''}>Low</option>
                            <option value="medium" ${task.priority === 'medium' ? 'selected' : ''}>Medium</option>
                            <option value="high" ${task.priority === 'high' ? 'selected' : ''}>High</option>
                            <option value="critical" ${task.priority === 'critical' ? 'selected' : ''}>Critical</option>
                        </select>
                        <input type="number" class="edit-task-effort" value="${task.estimated_effort_minutes || ''}" placeholder="Minutes" min="1">
                        <input type="date" class="edit-task-due" value="${task.due_date || ''}">
                    </div>
                    <div class="edit-actions">
                        <button class="btn-save-task">💾 Save</button>
                        <button class="btn-cancel-task">✕ Cancel</button>
                    </div>
                </div>
            </div>
        `;
    },

    filterTasks() {
        let filtered = [...state.tasks];

        if (state.filters.taskStatus !== 'all') {
            filtered = filtered.filter(t => t.status === state.filters.taskStatus);
        }

        if (state.filters.taskPriority !== 'all') {
            filtered = filtered.filter(t => t.priority === state.filters.taskPriority);
        }

        return filtered;
    },

    // Statistics View
    renderStatsView() {
        this.renderTimelineChart();
        this.renderTagDistribution();
        this.renderHourlyChart();
        this.renderTaskStats();
    },

    renderTimelineChart() {
        const container = document.getElementById('timeline-chart');
        const days = [];
        const counts = {};

        // Get last 7 days
        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            const key = date.toDateString();
            days.push(key);
            counts[key] = 0;
        }

        // Count thoughts per day
        state.thoughts.forEach(thought => {
            const date = new Date(thought.created_at);
            const key = date.toDateString();
            if (counts.hasOwnProperty(key)) {
                counts[key]++;
            }
        });

        const maxCount = Math.max(...Object.values(counts), 1);

        container.innerHTML = `
            <div class="bar-chart">
                ${days.map(day => {
                    const count = counts[day];
                    const height = (count / maxCount) * 100;
                    const label = new Date(day).toLocaleDateString('en-US', { weekday: 'short' });
                    return `
                        <div class="bar" style="height: ${height}%">
                            <div class="bar-value">${count}</div>
                            <div class="bar-label">${label}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    },

    renderTagDistribution() {
        const container = document.getElementById('tag-distribution');
        const tagCounts = {};

        state.thoughts.forEach(thought => {
            if (thought.tags) {
                thought.tags.forEach(tag => {
                    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
                });
            }
        });

        const sorted = Object.entries(tagCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);

        if (sorted.length === 0) {
            container.innerHTML = this.emptyState('🏷️', 'No tags yet');
            return;
        }

        const total = sorted.reduce((sum, [_, count]) => sum + count, 0);

        container.innerHTML = sorted.map(([tag, count]) => {
            const percentage = ((count / total) * 100).toFixed(1);
            return `
                <div class="stat-row">
                    <span class="stat-row-label">${tag}</span>
                    <span class="stat-row-value">${count} (${percentage}%)</span>
                </div>
            `;
        }).join('');
    },

    renderHourlyChart() {
        const container = document.getElementById('hourly-chart');
        const hourCounts = Array(24).fill(0);

        state.thoughts.forEach(thought => {
            const hour = utils.getHour(thought.created_at);
            hourCounts[hour]++;
        });

        const maxCount = Math.max(...hourCounts, 1);
        const hours = ['12a', '3a', '6a', '9a', '12p', '3p', '6p', '9p'];
        const hourIndices = [0, 3, 6, 9, 12, 15, 18, 21];

        container.innerHTML = `
            <div class="bar-chart">
                ${hourIndices.map((hourIndex, i) => {
                    const count = hourCounts[hourIndex];
                    const height = (count / maxCount) * 100;
                    return `
                        <div class="bar" style="height: ${height}%">
                            <div class="bar-value">${count}</div>
                            <div class="bar-label">${hours[i]}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    },

    renderTaskStats() {
        const container = document.getElementById('task-stats');

        const statusCounts = {
            pending: 0,
            in_progress: 0,
            done: 0,
            cancelled: 0
        };

        const priorityCounts = {
            critical: 0,
            high: 0,
            medium: 0,
            low: 0
        };

        state.tasks.forEach(task => {
            statusCounts[task.status] = (statusCounts[task.status] || 0) + 1;
            priorityCounts[task.priority] = (priorityCounts[task.priority] || 0) + 1;
        });

        const completionRate = state.tasks.length > 0
            ? ((statusCounts.done / state.tasks.length) * 100).toFixed(1)
            : 0;

        container.innerHTML = `
            <div class="stat-row">
                <span class="stat-row-label">Total Tasks</span>
                <span class="stat-row-value">${state.tasks.length}</span>
            </div>
            <div class="stat-row">
                <span class="stat-row-label">Completion Rate</span>
                <span class="stat-row-value">${completionRate}%</span>
            </div>
            <div class="stat-row">
                <span class="stat-row-label">Active Tasks</span>
                <span class="stat-row-value">${statusCounts.pending + statusCounts.in_progress}</span>
            </div>
            <div class="stat-row">
                <span class="stat-row-label">Completed</span>
                <span class="stat-row-value">${statusCounts.done}</span>
            </div>
            <div class="stat-row">
                <span class="stat-row-label">High Priority</span>
                <span class="stat-row-value">${priorityCounts.critical + priorityCounts.high}</span>
            </div>
        `;
    },

    // Helper Functions
    emptyState(icon, title, subtitle = '') {
        return `
            <div class="empty-state">
                <div class="empty-state-icon">${icon}</div>
                <div class="empty-state-text">${title}</div>
                ${subtitle ? `<div class="empty-state-hint">${subtitle}</div>` : ''}
            </div>
        `;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    updateHeaderStats() {
        document.getElementById('total-thoughts').textContent = `${state.thoughts.length} thoughts`;
        document.getElementById('total-tasks').textContent = `${state.tasks.length} tasks`;
    },

    populateTagFilter() {
        const select = document.getElementById('tag-filter');
        const tags = new Set();

        state.thoughts.forEach(thought => {
            if (thought.tags) {
                thought.tags.forEach(tag => tags.add(tag));
            }
        });

        const sortedTags = Array.from(tags).sort();

        select.innerHTML = '<option value="">All Tags</option>' +
            sortedTags.map(tag => `<option value="${tag}">${tag}</option>`).join('');
    }
};

// Event Handlers
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const view = e.target.dataset.view;
            switchView(view);
        });
    });

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', loadData);

    // Claude insights refresh button - force refresh
    document.getElementById('refresh-insights-btn').addEventListener('click', () => {
        ui.renderClaudeInsights(true);
    });

    // Thought filters
    document.getElementById('thought-search').addEventListener('input', (e) => {
        state.filters.thoughtSearch = e.target.value;
        ui.renderThoughtsView();
    });

    document.getElementById('thought-filter').addEventListener('change', (e) => {
        state.filters.thoughtTimeframe = e.target.value;
        ui.renderThoughtsView();
    });

    document.getElementById('tag-filter').addEventListener('change', (e) => {
        state.filters.thoughtTag = e.target.value;
        ui.renderThoughtsView();
    });

    // Task filters
    document.getElementById('task-status-filter').addEventListener('change', (e) => {
        state.filters.taskStatus = e.target.value;
        ui.renderTasksView();
    });

    document.getElementById('task-priority-filter').addEventListener('change', (e) => {
        state.filters.taskPriority = e.target.value;
        ui.renderTasksView();
    });
}

function switchView(view) {
    state.currentView = view;

    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    // Update views
    document.querySelectorAll('.view').forEach(v => {
        v.classList.remove('active');
    });
    document.getElementById(`${view}-view`).classList.add('active');

    // Render view content
    switch (view) {
        case 'dashboard':
            ui.renderDashboard();
            break;
        case 'thoughts':
            ui.renderThoughtsView();
            break;
        case 'tasks':
            ui.renderTasksView();
            break;
        case 'stats':
            ui.renderStatsView();
            break;
    }
}

// Loading & Error Management
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showError(message) {
    const toast = document.getElementById('error-toast');
    toast.textContent = message;
    toast.className = 'toast error';
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 5000);
}

function showSuccess(message) {
    const toast = document.getElementById('error-toast');
    toast.textContent = message;
    toast.className = 'toast success';
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// Task Suggestions Loading
async function loadTaskSuggestions() {
    try {
        state.taskSuggestions = await api.getPendingTaskSuggestions();
    } catch (error) {
        console.error('Failed to load task suggestions:', error);
        state.taskSuggestions = [];
    }
}

// Data Loading
async function loadData() {
    showLoading();

    try {
        const [thoughts, tasks] = await Promise.all([
            api.getThoughts(),
            api.getTasks()
        ]);

        state.thoughts = thoughts;
        state.tasks = tasks;

        // Also load task suggestions
        await loadTaskSuggestions();

        ui.updateHeaderStats();
        ui.populateTagFilter();
        switchView(state.currentView);

    } catch (error) {
        console.error('Failed to load data:', error);
    } finally {
        hideLoading();
    }
}

// Initialize Application
async function init() {
    console.log('🧠 Personal AI Assistant Dashboard starting...');
    console.log('API:', CONFIG.API_BASE_URL);

    setupEventListeners();
    await loadData();

    console.log('✅ Dashboard ready');
    console.log('ℹ️  Consciousness checks run automatically every 30 minutes on the server');
}

// Start app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
