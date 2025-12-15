// Personal AI Assistant - Dashboard Application
// Vanilla JavaScript implementation

// State Management
const state = {
    thoughts: [],
    tasks: [],
    currentView: 'dashboard',
    filters: {
        thoughtSearch: '',
        thoughtTimeframe: 'all',
        thoughtTag: '',
        taskStatus: 'all',
        taskPriority: 'all'
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
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Error:', error);
            showError(`Failed to ${options.method || 'GET'} ${endpoint}: ${error.message}`);
            throw error;
        }
    },

    async getThoughts() {
        return await this.request('/thoughts?limit=1000&sort_by=created_at&sort_order=desc');
    },

    async getTasks() {
        return await this.request('/tasks?limit=1000');
    },

    async searchThoughts(query) {
        return await this.request(`/thoughts/search?q=${encodeURIComponent(query)}&limit=100`);
    }
};

// Utility Functions
const utils = {
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
    }
};

// UI Rendering Functions
const ui = {
    // Dashboard View
    renderDashboard() {
        this.renderQuickStats();
        this.renderRecentThoughts();
        this.renderTopTags();
        this.renderActiveTasks();
    },

    renderQuickStats() {
        const todayCount = state.thoughts.filter(t => utils.isToday(t.created_at)).length;
        const weekCount = state.thoughts.filter(t => utils.isThisWeek(t.created_at)).length;

        document.getElementById('dash-total-thoughts').textContent = state.thoughts.length;
        document.getElementById('dash-total-tasks').textContent = state.tasks.length;
        document.getElementById('dash-today-thoughts').textContent = todayCount;
        document.getElementById('dash-week-thoughts').textContent = weekCount;
    },

    renderRecentThoughts() {
        const container = document.getElementById('dash-recent-thoughts');
        const recent = state.thoughts.slice(0, 5);

        if (recent.length === 0) {
            container.innerHTML = this.emptyState('💭', 'No thoughts yet', 'Start capturing with your iOS Shortcuts');
            return;
        }

        container.innerHTML = recent.map(thought => `
            <div class="thought-item">
                <div class="thought-content">${this.escapeHtml(thought.content)}</div>
                <div class="thought-meta">
                    <span class="thought-time">${utils.timeAgo(thought.created_at)}</span>
                    ${thought.tags && thought.tags.length > 0 ? `
                        <div class="thought-tags">
                            ${thought.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
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
    },

    // Thoughts View
    renderThoughtsView() {
        const container = document.getElementById('thoughts-list');
        let filtered = this.filterThoughts();

        if (filtered.length === 0) {
            container.innerHTML = this.emptyState('🔍', 'No thoughts found', 'Try adjusting your filters');
            return;
        }

        container.innerHTML = filtered.map(thought => `
            <div class="thought-item">
                <div class="thought-content">${this.escapeHtml(thought.content)}</div>
                <div class="thought-meta">
                    <span class="thought-time">${utils.formatDateTime(thought.created_at)}</span>
                    ${thought.tags && thought.tags.length > 0 ? `
                        <div class="thought-tags">
                            ${thought.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
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
    },

    renderTaskItem(task) {
        return `
            <div class="task-item priority-${task.priority} status-${task.status}">
                <div class="task-content">
                    <div class="task-title">${this.escapeHtml(task.title)}</div>
                    <div class="task-meta">
                        <span class="task-badge priority">${task.priority}</span>
                        <span class="task-badge status">${task.status.replace('_', ' ')}</span>
                        ${task.due_date ? `<span>Due: ${utils.formatDate(task.due_date)}</span>` : ''}
                        <span>${utils.timeAgo(task.created_at)}</span>
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
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 5000);
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
}

// Start app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
