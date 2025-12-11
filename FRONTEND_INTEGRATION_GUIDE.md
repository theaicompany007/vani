# Frontend Integration Guide - Command Center Updates

## Overview
This guide provides code snippets to integrate authentication, permissions, and pitch presentation into `command_center.html`.

## 1. Authentication Check on Page Load

Add this JavaScript at the beginning of the `<script>` section:

```javascript
// Check authentication on page load
let currentUser = null;
let userPermissions = [];
let currentIndustry = null;

async function checkAuth() {
    try {
        const response = await fetch('/api/auth/session');
        if (!response.ok) {
            window.location.href = '/login';
            return;
        }
        const data = await response.json();
        if (data.success) {
            currentUser = data.user;
            userPermissions = data.user.permissions || [];
            currentIndustry = data.industry;
            
            // Show/hide features based on permissions
            updateUIForPermissions();
            
            // Show industry selector if user has access to multiple industries
            if (currentUser.is_super_user) {
                loadIndustries();
            }
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/login';
    }
}

function hasPermission(useCase) {
    if (!currentUser) return false;
    if (currentUser.is_super_user) return true;
    return userPermissions.includes(useCase);
}

function updateUIForPermissions() {
    // Hide/show tabs based on permissions
    if (!hasPermission('target_management')) {
        document.getElementById('tab-targets')?.classList.add('hidden');
    }
    if (!hasPermission('analytics')) {
        document.getElementById('tab-analytics')?.classList.add('hidden');
    }
    if (!hasPermission('meetings')) {
        document.getElementById('tab-meetings')?.classList.add('hidden');
    }
    if (!hasPermission('pitch_presentation')) {
        document.getElementById('tab-pitch')?.classList.add('hidden');
    }
    
    // Hide buttons based on permissions
    if (!hasPermission('outreach')) {
        document.querySelectorAll('.btn-send-outreach').forEach(btn => btn.classList.add('hidden'));
    }
    if (!hasPermission('ai_message_generation')) {
        document.getElementById('btn-generate')?.classList.add('hidden');
    }
    if (!hasPermission('sheets_import_export')) {
        document.getElementById('btn-import-sheets')?.classList.add('hidden');
        document.getElementById('btn-export-sheets')?.classList.add('hidden');
    }
    
    // Show admin panel link for super users
    if (currentUser && currentUser.is_super_user) {
        const adminLink = document.createElement('a');
        adminLink.href = '/admin';
        adminLink.className = 'text-emerald-600 hover:text-emerald-700';
        adminLink.innerHTML = '<i class="fa-solid fa-shield-halved mr-2"></i>Admin Panel';
        document.getElementById('header-nav')?.appendChild(adminLink);
    }
}

// Call on page load
window.onload = function() {
    checkAuth().then(() => {
        // Existing onload code here
        loadTargetsFromAPI();
        renderGapChart();
        updateRevenue();
        refreshAnalytics();
        loadMeetings();
        loadNotifications();
    });
};
```

## 2. Industry Selector (for Super Users)

Add this HTML in the header section:

```html
<!-- Industry Selector (Super Users Only) -->
<div id="industry-selector" class="hidden">
    <select id="industry-dropdown" onchange="switchIndustry(this.value)" 
            class="px-3 py-2 border border-slate-300 rounded-lg text-sm">
        <option value="">Select Industry...</option>
    </select>
</div>
```

Add this JavaScript:

```javascript
async function loadIndustries() {
    if (!currentUser || !currentUser.is_super_user) return;
    
    try {
        const response = await fetch('/api/industries');
        const data = await response.json();
        if (data.success) {
            const dropdown = document.getElementById('industry-dropdown');
            data.industries.forEach(industry => {
                const option = document.createElement('option');
                option.value = industry.id;
                option.textContent = industry.name;
                if (currentIndustry && industry.id === currentIndustry.id) {
                    option.selected = true;
                }
                dropdown.appendChild(option);
            });
            document.getElementById('industry-selector').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Failed to load industries:', error);
    }
}

async function switchIndustry(industryId) {
    if (!industryId) return;
    
    try {
        const response = await fetch('/api/industries/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ industry_id: industryId })
        });
        const data = await response.json();
        if (data.success) {
            currentIndustry = data.industry;
            showToast('success', 'Industry Switched', `Now viewing ${data.industry.name}`, 3000);
            // Reload data for new industry
            loadTargetsFromAPI();
            refreshAnalytics();
        }
    } catch (error) {
        showToast('error', 'Switch Failed', error.message, 5000);
    }
}
```

## 3. Pitch Presentation Tab

Add this HTML tab in the navigation:

```html
<button id="tab-pitch" onclick="showTab('pitch')" 
        class="px-6 py-3 text-slate-600 hover:text-emerald-600 font-medium transition">
    <i class="fa-solid fa-presentation-screen mr-2"></i>Pitch Presentation
</button>
```

Add this content section:

```html
<!-- Pitch Presentation Tab -->
<div id="content-pitch" class="hidden">
    <div class="bg-white rounded-xl shadow-lg border border-slate-200 p-8">
        <h2 class="text-2xl font-bold text-slate-900 mb-6">AI Pitch Generator</h2>
        
        <!-- Target Selector -->
        <div class="mb-6">
            <label class="block text-sm font-medium text-slate-700 mb-2">Select Target</label>
            <select id="pitch-target-select" 
                    class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500">
                <option value="">Choose a target...</option>
            </select>
        </div>
        
        <!-- Generate Button -->
        <div class="mb-6">
            <button id="btn-generate-pitch" onclick="generatePitch()" 
                    class="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold">
                <i class="fa-solid fa-wand-magic-sparkles mr-2"></i>Generate AI Pitch
            </button>
        </div>
        
        <!-- Pitch Preview -->
        <div id="pitch-preview-container" class="hidden">
            <div class="mb-4 flex gap-2">
                <button onclick="sendPitch('email')" 
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
                    <i class="fa-solid fa-envelope mr-2"></i>Send via Email
                </button>
                <button onclick="sendPitch('whatsapp')" 
                        class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg">
                    <i class="fa-brands fa-whatsapp mr-2"></i>Send via WhatsApp
                </button>
                <button onclick="sendPitch('linkedin')" 
                        class="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white rounded-lg">
                    <i class="fa-brands fa-linkedin mr-2"></i>Send via LinkedIn
                </button>
            </div>
            <iframe id="pitch-preview" 
                    class="w-full border border-slate-300 rounded-lg" 
                    style="height: 600px; background: white;">
            </iframe>
        </div>
    </div>
</div>
```

Add this JavaScript:

```javascript
let currentPitchId = null;
let currentPitchTargetId = null;

async function generatePitch() {
    const targetId = document.getElementById('pitch-target-select').value;
    if (!targetId) {
        showToast('warning', 'No Target Selected', 'Please select a target first', 3000);
        return;
    }
    
    const btn = document.getElementById('btn-generate-pitch');
    const originalHTML = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>Generating...';
        
        const response = await fetch(`/api/pitch/generate/${targetId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentPitchId = data.pitch.id;
            currentPitchTargetId = targetId;
            
            // Show preview
            const preview = document.getElementById('pitch-preview');
            const blob = new Blob([data.pitch.html_content], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            preview.src = url;
            
            document.getElementById('pitch-preview-container').classList.remove('hidden');
            showToast('success', 'OK - Pitch Generated', 'AI pitch generated successfully!', 3000);
        } else {
            showToast('error', 'Not OK - Generation Failed', data.error || 'Failed to generate pitch', 5000);
        }
    } catch (error) {
        showToast('error', 'Not OK - Network Error', error.message, 5000);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
    }
}

async function sendPitch(channel) {
    if (!currentPitchId || !currentPitchTargetId) {
        showToast('warning', 'No Pitch', 'Please generate a pitch first', 3000);
        return;
    }
    
    if (!confirm(`Send pitch via ${channel}?`)) return;
    
    try {
        showToast('info', 'Sending...', `Sending pitch via ${channel}...`, 2000);
        
        const response = await fetch('/api/pitch/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pitch_id: currentPitchId,
                target_id: currentPitchTargetId,
                channel: channel
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('success', 'OK - Pitch Sent', `Pitch sent successfully via ${channel}`, 4000);
        } else {
            showToast('error', 'Not OK - Send Failed', data.error || 'Failed to send pitch', 5000);
        }
    } catch (error) {
        showToast('error', 'Not OK - Network Error', error.message, 5000);
    }
}

// Populate target selector for pitch
function populatePitchTargets() {
    const select = document.getElementById('pitch-target-select');
    select.innerHTML = '<option value="">Choose a target...</option>';
    
    if (targets && targets.length > 0) {
        targets.forEach(target => {
            const option = document.createElement('option');
            option.value = target.id;
            option.textContent = `${target.company_name} - ${target.contact_name || 'N/A'}`;
            select.appendChild(option);
        });
    }
}

// Call after targets are loaded
// In loadTargetsFromAPI(), add: populatePitchTargets();
```

## 4. Update Existing Functions

### Update `loadTargetsFromAPI()` to filter by industry:

```javascript
async function loadTargetsFromAPI() {
    try {
        let url = '/api/targets';
        if (currentIndustry) {
            url += `?industry_id=${currentIndustry.id}`;
        }
        
        const response = await fetch(url);
        // ... rest of function
    } catch (error) {
        // ... error handling
    }
}
```

### Add permission checks to existing functions:

```javascript
// In sendOutreach()
if (!hasPermission('outreach')) {
    showToast('error', 'Access Denied', 'You do not have permission to send outreach', 5000);
    return;
}

// In importFromSheets()
if (!hasPermission('sheets_import_export')) {
    showToast('error', 'Access Denied', 'You do not have permission to import from Sheets', 5000);
    return;
}

// In generateMessage()
if (!hasPermission('ai_message_generation')) {
    showToast('error', 'Access Denied', 'You do not have permission to generate messages', 5000);
    return;
}
```

## 5. Logout Functionality

Add logout button in header:

```html
<button onclick="logout()" class="text-slate-600 hover:text-red-600">
    <i class="fa-solid fa-sign-out-alt mr-2"></i>Logout
</button>
```

Add JavaScript:

```javascript
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        window.location.href = '/login';
    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = '/login';
    }
}
```

## 6. Update Tab Navigation

Update the `showTab()` function to check permissions:

```javascript
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('[id^="content-"]').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('[id^="tab-"]').forEach(el => el.classList.remove('nav-active'));
    
    // Check permissions
    const permissionMap = {
        'targets': 'target_management',
        'analytics': 'analytics',
        'meetings': 'meetings',
        'pitch': 'pitch_presentation'
    };
    
    if (permissionMap[tabName] && !hasPermission(permissionMap[tabName])) {
        showToast('error', 'Access Denied', `You do not have permission to access ${tabName}`, 5000);
        return;
    }
    
    // Show selected tab
    document.getElementById(`content-${tabName}`)?.classList.remove('hidden');
    document.getElementById(`tab-${tabName}`)?.classList.add('nav-active');
}
```

## 7. Industry Context Display

Add industry indicator in header:

```html
<div id="industry-indicator" class="text-sm text-slate-600">
    <i class="fa-solid fa-building mr-1"></i>
    <span id="industry-name">Loading...</span>
</div>
```

Update on auth success:

```javascript
if (currentIndustry) {
    document.getElementById('industry-name').textContent = currentIndustry.name;
} else {
    document.getElementById('industry-indicator').classList.add('hidden');
}
```

## Summary

Key changes needed:
1. ✅ Authentication check on page load
2. ✅ Permission-based UI hiding
3. ✅ Industry selector for super users
4. ✅ Pitch presentation tab and functionality
5. ✅ Logout functionality
6. ✅ Permission checks in existing functions
7. ✅ Industry filtering for targets

All code snippets are ready to integrate into `command_center.html`.

