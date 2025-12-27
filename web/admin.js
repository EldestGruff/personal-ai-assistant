/**
 * Personal AI Assistant - Admin Settings
 * 
 * Handles settings, profile, and scheduler management.
 */

// API Configuration
const API_BASE = window.CONFIG?.API_BASE_URL || window.CONFIG?.API_BASE || 'http://localhost:8000/api/v1';
const API_KEY = window.CONFIG?.API_KEY || localStorage.getItem('api_key') || '';

// State
let currentSettings = null;
let currentProfile = null;
let scheduleRunning = false;

// =============================================================================
// Tab Navigation
// =============================================================================

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Update button states
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Show corresponding tab
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
        const tabId = btn.dataset.tab + '-tab';
        document.getElementById(tabId).classList.add('active');
    });
});

// =============================================================================
// Toast Notifications
// =============================================================================

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// =============================================================================
// API Helpers
// =============================================================================

async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
        ...options.headers
    };
    
    try {
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error?.message || `HTTP ${response.status}`);
        }
        
        if (response.status === 204) {
            return null;
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

// =============================================================================
// Settings Management
// =============================================================================

async function loadSettings() {
    try {
        const response = await apiRequest('/settings');
        currentSettings = response.data;
        
        // Populate form
        document.getElementById('primary-backend').value = currentSettings.primary_backend || 'claude';
        document.getElementById('fallback-backend').value = currentSettings.fallback_backend || 'ollama';
        document.getElementById('model-preference').value = currentSettings.model_preference || '';
        
        document.getElementById('auto-tagging-enabled').checked = currentSettings.auto_tagging_enabled !== false;
        document.getElementById('max-tags').value = currentSettings.max_suggested_tags || 3;
        
        document.getElementById('auto-task-enabled').checked = currentSettings.auto_task_creation_enabled !== false;
        document.getElementById('task-confidence').value = currentSettings.task_confidence_threshold || 0.7;
        document.getElementById('require-confirmation').checked = currentSettings.require_task_confirmation !== false;
        
        document.getElementById('consciousness-depth').value = currentSettings.consciousness_check_depth || 'standard';
        document.getElementById('include-archived').checked = currentSettings.include_archived_in_analysis || false;
        
        showToast('Settings loaded');
    } catch (error) {
        showToast('Failed to load settings: ' + error.message, 'error');
    }
}

async function saveSettings() {
    try {
        const settings = {
            primary_backend: document.getElementById('primary-backend').value,
            fallback_backend: document.getElementById('fallback-backend').value,
            model_preference: document.getElementById('model-preference').value || null,
            
            auto_tagging_enabled: document.getElementById('auto-tagging-enabled').checked,
            max_suggested_tags: parseInt(document.getElementById('max-tags').value) || 3,
            
            auto_task_creation_enabled: document.getElementById('auto-task-enabled').checked,
            task_confidence_threshold: parseFloat(document.getElementById('task-confidence').value) || 0.7,
            require_task_confirmation: document.getElementById('require-confirmation').checked,
            
            consciousness_check_depth: document.getElementById('consciousness-depth').value,
            include_archived_in_analysis: document.getElementById('include-archived').checked
        };
        
        await apiRequest('/settings', {
            method: 'PUT',
            body: JSON.stringify(settings)
        });
        
        currentSettings = settings;
        showToast('Settings saved successfully!');
    } catch (error) {
        showToast('Failed to save settings: ' + error.message, 'error');
    }
}

// =============================================================================
// Profile Management
// =============================================================================

async function loadProfile() {
    try {
        const response = await apiRequest('/profile');
        currentProfile = response.data;
        
        // Populate projects
        renderProjects(currentProfile.ongoing_projects || []);
        
        // Populate interests
        renderInterests(currentProfile.interests || []);
        
        // Work style
        document.getElementById('work-style').value = currentProfile.work_style || '';
        document.getElementById('adhd-considerations').value = currentProfile.adhd_considerations || '';
        
        // AI preferences
        document.getElementById('preferred-tone').value = currentProfile.preferred_tone || 'warm_encouraging';
        document.getElementById('detail-level').value = currentProfile.detail_level || 'moderate';
        document.getElementById('reference-past-work').checked = currentProfile.reference_past_work !== false;
        
        showToast('Profile loaded');
    } catch (error) {
        showToast('Failed to load profile: ' + error.message, 'error');
    }
}

function renderProjects(projects) {
    const list = document.getElementById('project-list');
    
    if (!projects || projects.length === 0) {
        list.innerHTML = '<li class="project-item"><div class="project-info"><em>No projects yet. Add one below!</em></div></li>';
        return;
    }
    
    list.innerHTML = projects.map(project => `
        <li class="project-item">
            <div class="project-info">
                <div class="project-name">${escapeHtml(project.name)}</div>
                <div class="project-status">
                    <span class="status-badge status-${project.status}">${project.status}</span>
                    ${project.description ? ' - ' + escapeHtml(project.description) : ''}
                </div>
            </div>
            <div class="project-actions">
                <select onchange="updateProjectStatus('${escapeHtml(project.name)}', this.value)">
                    <option value="active" ${project.status === 'active' ? 'selected' : ''}>Active</option>
                    <option value="paused" ${project.status === 'paused' ? 'selected' : ''}>Paused</option>
                    <option value="completed" ${project.status === 'completed' ? 'selected' : ''}>Completed</option>
                </select>
                <button class="btn btn-sm btn-danger" onclick="removeProject('${escapeHtml(project.name)}')">×</button>
            </div>
        </li>
    `).join('');
}

function renderInterests(interests) {
    const container = document.getElementById('interest-tags');
    
    if (!interests || interests.length === 0) {
        container.innerHTML = '<span style="color: var(--text-muted);">No interests yet. Add some below!</span>';
        return;
    }
    
    container.innerHTML = interests.map(interest => `
        <span class="interest-tag">
            ${escapeHtml(interest)}
            <span class="remove-tag" onclick="removeInterest('${escapeHtml(interest)}')">&times;</span>
        </span>
    `).join('');
}

async function addProject() {
    const nameInput = document.getElementById('new-project-name');
    const descInput = document.getElementById('new-project-description');
    
    const name = nameInput.value.trim();
    const description = descInput.value.trim();
    
    if (!name) {
        showToast('Please enter a project name', 'error');
        return;
    }
    
    try {
        await apiRequest('/profile/projects', {
            method: 'POST',
            body: JSON.stringify({ name, description, status: 'active' })
        });
        
        // Clear inputs
        nameInput.value = '';
        descInput.value = '';
        
        // Reload profile
        await loadProfile();
        showToast(`Project "${name}" added!`);
    } catch (error) {
        showToast('Failed to add project: ' + error.message, 'error');
    }
}

async function updateProjectStatus(name, status) {
    try {
        await apiRequest(`/profile/projects/${encodeURIComponent(name)}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
        
        showToast(`Project "${name}" updated to ${status}`);
        await loadProfile();
    } catch (error) {
        showToast('Failed to update project: ' + error.message, 'error');
    }
}

async function removeProject(name) {
    if (!confirm(`Remove project "${name}"?`)) {
        return;
    }
    
    try {
        await apiRequest(`/profile/projects/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });
        
        showToast(`Project "${name}" removed`);
        await loadProfile();
    } catch (error) {
        showToast('Failed to remove project: ' + error.message, 'error');
    }
}

async function addInterest() {
    const input = document.getElementById('new-interest');
    const interest = input.value.trim().toLowerCase();
    
    if (!interest) {
        showToast('Please enter an interest', 'error');
        return;
    }
    
    try {
        // Get current interests and add new one
        const currentInterests = currentProfile?.interests || [];
        if (currentInterests.includes(interest)) {
            showToast('Interest already exists', 'error');
            return;
        }
        
        const updatedInterests = [...currentInterests, interest];
        
        await apiRequest('/profile', {
            method: 'PUT',
            body: JSON.stringify({ interests: updatedInterests })
        });
        
        input.value = '';
        await loadProfile();
        showToast(`Interest "${interest}" added!`);
    } catch (error) {
        showToast('Failed to add interest: ' + error.message, 'error');
    }
}

async function removeInterest(interest) {
    try {
        const currentInterests = currentProfile?.interests || [];
        const updatedInterests = currentInterests.filter(i => i !== interest);
        
        await apiRequest('/profile', {
            method: 'PUT',
            body: JSON.stringify({ interests: updatedInterests })
        });
        
        await loadProfile();
        showToast(`Interest "${interest}" removed`);
    } catch (error) {
        showToast('Failed to remove interest: ' + error.message, 'error');
    }
}

async function saveProfile() {
    try {
        const profile = {
            work_style: document.getElementById('work-style').value || null,
            adhd_considerations: document.getElementById('adhd-considerations').value || null,
            preferred_tone: document.getElementById('preferred-tone').value,
            detail_level: document.getElementById('detail-level').value,
            reference_past_work: document.getElementById('reference-past-work').checked
        };
        
        await apiRequest('/profile', {
            method: 'PUT',
            body: JSON.stringify(profile)
        });
        
        showToast('Profile saved successfully!');
    } catch (error) {
        showToast('Failed to save profile: ' + error.message, 'error');
    }
}

// =============================================================================
// Scheduler Management
// =============================================================================

async function loadSchedule() {
    try {
        const response = await apiRequest('/scheduled-analyses');
        const data = response.data;
        
        // Update schedule display
        scheduleRunning = data.is_running;
        updateScheduleDisplay(data);
        
        // Populate form
        document.getElementById('schedule-interval').value = data.interval_minutes || 30;
        
        if (data.active_hours) {
            document.getElementById('active-hours-start').value = data.active_hours.start || '09:00';
            document.getElementById('active-hours-end').value = data.active_hours.end || '18:00';
        }
        
        document.getElementById('weekend-enabled').checked = data.weekend_enabled || false;
        
        // Load recent analyses
        renderRecentAnalyses(data.recent_analyses || []);
        
        showToast('Schedule loaded');
    } catch (error) {
        showToast('Failed to load schedule: ' + error.message, 'error');
    }
}

function updateScheduleDisplay(data) {
    const indicator = document.getElementById('schedule-indicator');
    const statusText = document.getElementById('schedule-status-text');
    const detail = document.getElementById('schedule-detail');
    const toggleBtn = document.getElementById('toggle-schedule-btn');
    
    if (data.is_running) {
        indicator.className = 'status-indicator running';
        statusText.textContent = 'Schedule Active';
        detail.textContent = `Running every ${data.interval_minutes || 30} minutes`;
        toggleBtn.textContent = 'Stop';
        toggleBtn.className = 'btn btn-sm btn-danger';
    } else {
        indicator.className = 'status-indicator stopped';
        statusText.textContent = 'Schedule Stopped';
        detail.textContent = 'Click Start to enable automatic checks';
        toggleBtn.textContent = 'Start';
        toggleBtn.className = 'btn btn-sm btn-primary';
    }
}

function renderRecentAnalyses(analyses) {
    const container = document.getElementById('recent-analyses');
    
    if (!analyses || analyses.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted);">No recent analyses. Schedule will populate results here.</p>';
        return;
    }
    
    container.innerHTML = analyses.slice(0, 5).map(analysis => {
        const date = new Date(analysis.timestamp);
        return `
            <div class="project-item">
                <div class="project-info">
                    <div class="project-name">${date.toLocaleDateString()} ${date.toLocaleTimeString()}</div>
                    <div class="project-status">
                        ${analysis.thoughts_analyzed} thoughts analyzed • 
                        ${analysis.themes?.length || 0} themes discovered
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function toggleSchedule() {
    try {
        if (scheduleRunning) {
            await apiRequest('/scheduled-analyses/stop', { method: 'POST' });
            showToast('Schedule stopped');
        } else {
            await apiRequest('/scheduled-analyses/start', { method: 'POST' });
            showToast('Schedule started');
        }
        
        await loadSchedule();
    } catch (error) {
        showToast('Failed to toggle schedule: ' + error.message, 'error');
    }
}

async function saveSchedule() {
    try {
        const schedule = {
            interval_minutes: parseInt(document.getElementById('schedule-interval').value) || 30,
            active_hours: {
                start: document.getElementById('active-hours-start').value,
                end: document.getElementById('active-hours-end').value
            },
            weekend_enabled: document.getElementById('weekend-enabled').checked
        };
        
        await apiRequest('/scheduled-analyses', {
            method: 'PUT',
            body: JSON.stringify(schedule)
        });
        
        showToast('Schedule saved successfully!');
    } catch (error) {
        showToast('Failed to save schedule: ' + error.message, 'error');
    }
}

async function runNow() {
    try {
        showToast('Running consciousness check...');
        
        const response = await apiRequest('/consciousness-check-v3', {
            method: 'POST',
            body: JSON.stringify({ depth: 'standard' })
        });
        
        if (response.success) {
            showToast('Consciousness check completed!');
            await loadSchedule();
        } else {
            showToast('Check completed but with issues', 'error');
        }
    } catch (error) {
        showToast('Failed to run check: ' + error.message, 'error');
    }
}

// =============================================================================
// Utilities
// =============================================================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// =============================================================================
// Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Load all data
    loadSettings();
    loadProfile();
    loadSchedule();
    
    // Enter key handlers for add fields
    document.getElementById('new-project-name').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addProject();
    });
    
    document.getElementById('new-interest').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addInterest();
    });
});
