# UI Updates Needed for AI-Powered Multi-Industry Target System

## Summary
This document outlines the UI changes needed in `app/templates/command_center.html` to complete the AI-powered multi-industry target system implementation.

## 1. Industry Selector in Header

**Location:** After line 37 (after "Operational Status")

**Add:**
```html
<!-- Industry Selector -->
<div class="flex items-center gap-2">
    <label class="text-xs text-slate-500 font-medium">Industry:</label>
    <select id="industry-selector" onchange="switchIndustry(this.value)" 
            class="px-3 py-1.5 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500">
        <option value="">All Industries</option>
    </select>
    <span id="industry-badge" class="hidden px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded"></span>
</div>
```

**JavaScript Functions to Add:**
```javascript
let allIndustries = [];
let currentIndustryId = null;

async function loadIndustries() {
    try {
        const response = await fetch('/api/industries', { credentials: 'include' });
        const data = await response.json();
        if (data.success && data.industries) {
            allIndustries = data.industries;
            const selector = document.getElementById('industry-selector');
            if (selector) {
                selector.innerHTML = '<option value="">All Industries</option>' +
                    data.industries.map(ind => 
                        `<option value="${ind.id}">${ind.name}</option>`
                    ).join('');
                
                // Set current industry if available
                if (sessionData && sessionData.user && sessionData.user.active_industry_id) {
                    selector.value = sessionData.user.active_industry_id;
                    currentIndustryId = sessionData.user.active_industry_id;
                    updateIndustryBadge();
                }
            }
        }
    } catch (error) {
        console.error('Error loading industries:', error);
    }
}

async function switchIndustry(industryId) {
    try {
        const response = await fetch('/api/industries/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ industry_id: industryId || null })
        });
        
        const data = await response.json();
        if (data.success) {
            currentIndustryId = industryId;
            updateIndustryBadge();
            showToast('success', 'Industry Switched', `Active industry: ${data.industry?.name || 'All Industries'}`, 3000);
            
            // Reload current view to reflect industry change
            const currentTab = document.querySelector('.nav-active')?.getAttribute('onclick')?.match(/'(\w+)'/)?.[1];
            if (currentTab) {
                switchTab(currentTab);
            }
        } else {
            showToast('error', 'Failed', data.error || 'Failed to switch industry', 5000);
        }
    } catch (error) {
        console.error('Error switching industry:', error);
        showToast('error', 'Failed', `Failed to switch industry: ${error.message}`, 5000);
    }
}

function updateIndustryBadge() {
    const badge = document.getElementById('industry-badge');
    if (currentIndustryId && allIndustries.length > 0) {
        const industry = allIndustries.find(ind => ind.id === currentIndustryId);
        if (industry && badge) {
            badge.textContent = industry.name;
            badge.classList.remove('hidden');
        }
    } else if (badge) {
        badge.classList.add('hidden');
    }
}
```

## 2. Tab Visibility Based on Permissions

**Location:** In `checkSuperUser()` function (around line 1418)

**Add after existing permission checks:**
```javascript
// Check contact_management permission
async function checkContactManagementPermission() {
    try {
        const response = await fetch('/api/contacts?limit=1', { credentials: 'include' });
        if (response.status === 403) {
            // User doesn't have contact_management permission
            const contactsTab = document.getElementById('nav-contacts');
            if (contactsTab) {
                contactsTab.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error checking contact management permission:', error);
    }
}

// Check company_management permission
async function checkCompanyManagementPermission() {
    try {
        const response = await fetch('/api/companies?limit=1', { credentials: 'include' });
        if (response.status === 403) {
            // User doesn't have company_management permission
            const companiesTab = document.getElementById('nav-companies');
            if (companiesTab) {
                companiesTab.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error checking company management permission:', error);
    }
}

// Call these in page load
checkContactManagementPermission();
checkCompanyManagementPermission();
```

## 3. AI Target Finder Panel

**Location:** In the targets view section (around line 600-700)

**Add before the target list:**
```html
<!-- AI Target Finder Panel -->
<div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6">
    <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-bold text-slate-900">
            <i class="fa-solid fa-brain text-indigo-500 mr-2"></i>AI Target Finder
        </h3>
        <button onclick="showAITargetFinder()" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium">
            <i class="fa-solid fa-search mr-2"></i>Find Targets
        </button>
    </div>
    
    <!-- AI Finder Modal (hidden by default) -->
    <div id="ai-finder-modal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
        <div class="bg-white rounded-xl shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div class="p-6 border-b border-slate-200">
                <div class="flex justify-between items-center">
                    <h3 class="text-xl font-bold text-slate-900">AI Target Identification</h3>
                    <button onclick="closeAITargetFinder()" class="text-slate-400 hover:text-slate-600">
                        <i class="fa-solid fa-times text-xl"></i>
                    </button>
                </div>
            </div>
            <div class="p-6">
                <div class="mb-4">
                    <label class="block text-sm font-medium text-slate-700 mb-2">Industry</label>
                    <select id="ai-finder-industry" class="w-full px-3 py-2 border border-slate-300 rounded-lg">
                        <option value="">Select Industry</option>
                    </select>
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium text-slate-700 mb-2">Minimum Seniority Score</label>
                    <input type="range" id="ai-finder-seniority" min="0" max="1" step="0.1" value="0.5" 
                           class="w-full" oninput="document.getElementById('seniority-value').textContent = this.value">
                    <div class="flex justify-between text-xs text-slate-500 mt-1">
                        <span>0.0</span>
                        <span id="seniority-value">0.5</span>
                        <span>1.0</span>
                    </div>
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium text-slate-700 mb-2">Max Results</label>
                    <input type="number" id="ai-finder-limit" value="50" min="10" max="200" 
                           class="w-full px-3 py-2 border border-slate-300 rounded-lg">
                </div>
                <button onclick="runAITargetFinder()" class="w-full px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium">
                    <i class="fa-solid fa-magic mr-2"></i>Identify Targets
                </button>
                
                <!-- Results -->
                <div id="ai-finder-results" class="mt-6 hidden">
                    <h4 class="font-bold text-slate-900 mb-3">Recommended Targets</h4>
                    <div id="ai-finder-results-list" class="space-y-3"></div>
                    <div class="mt-4 flex gap-2">
                        <button onclick="selectAllAIRecommendations()" class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-sm">
                            Select All
                        </button>
                        <button onclick="createSelectedTargets()" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium">
                            <i class="fa-solid fa-plus mr-2"></i>Create Selected Targets
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

**JavaScript Functions:**
```javascript
let aiRecommendations = [];

function showAITargetFinder() {
    const modal = document.getElementById('ai-finder-modal');
    if (modal) {
        modal.classList.remove('hidden');
        // Populate industry dropdown
        const industrySelect = document.getElementById('ai-finder-industry');
        if (industrySelect && allIndustries.length > 0) {
            industrySelect.innerHTML = '<option value="">Select Industry</option>' +
                allIndustries.map(ind => 
                    `<option value="${ind.name}">${ind.name}</option>`
                ).join('');
            if (currentIndustryId) {
                const currentIndustry = allIndustries.find(ind => ind.id === currentIndustryId);
                if (currentIndustry) {
                    industrySelect.value = currentIndustry.name;
                }
            }
        }
    }
}

function closeAITargetFinder() {
    const modal = document.getElementById('ai-finder-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

async function runAITargetFinder() {
    const industry = document.getElementById('ai-finder-industry')?.value;
    const minSeniority = parseFloat(document.getElementById('ai-finder-seniority')?.value || 0.5);
    const limit = parseInt(document.getElementById('ai-finder-limit')?.value || 50);
    
    if (!industry) {
        showToast('error', 'Required', 'Please select an industry', 3000);
        return;
    }
    
    try {
        showToast('info', 'Analyzing', 'AI is identifying high-value targets...', 5000);
        
        const response = await fetch('/api/targets/ai-identify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ industry, limit, min_seniority: minSeniority })
        });
        
        const data = await response.json();
        if (data.success && data.recommendations) {
            aiRecommendations = data.recommendations;
            renderAIRecommendations();
            document.getElementById('ai-finder-results')?.classList.remove('hidden');
            showToast('success', 'Complete', `Found ${data.count} recommended targets`, 3000);
        } else {
            showToast('error', 'Failed', data.error || 'Failed to identify targets', 5000);
        }
    } catch (error) {
        console.error('Error running AI target finder:', error);
        showToast('error', 'Failed', `Error: ${error.message}`, 5000);
    }
}

function renderAIRecommendations() {
    const container = document.getElementById('ai-finder-results-list');
    if (!container) return;
    
    container.innerHTML = aiRecommendations.map((rec, index) => `
        <div class="border border-slate-200 rounded-lg p-4">
            <div class="flex items-start gap-3">
                <input type="checkbox" class="ai-recommendation-checkbox mt-1" 
                       data-index="${index}" onchange="updateSelectedCount()">
                <div class="flex-1">
                    <div class="flex justify-between items-start mb-2">
                        <div>
                            <h4 class="font-bold text-slate-900">${rec.contact_name || 'Unknown'}</h4>
                            <p class="text-sm text-slate-600">${rec.company_name || ''} • ${rec.role || ''}</p>
                        </div>
                        <div class="text-right">
                            <div class="text-xs text-slate-500">Seniority</div>
                            <div class="font-bold text-indigo-600">${(rec.seniority_score * 100).toFixed(0)}%</div>
                        </div>
                    </div>
                    <div class="flex gap-2 mb-2">
                        <span class="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs rounded">${rec.solution_fit}</span>
                        <span class="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">Confidence: ${(rec.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                    <p class="text-sm text-slate-600 mb-2">${rec.reasoning || ''}</p>
                    <div class="text-xs text-slate-500">
                        <div><strong>Pain Points:</strong> ${rec.pain_points?.join(', ') || 'N/A'}</div>
                        <div><strong>Gaps:</strong> ${rec.identified_gaps?.join(', ') || 'N/A'}</div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function selectAllAIRecommendations() {
    const checkboxes = document.querySelectorAll('.ai-recommendation-checkbox');
    checkboxes.forEach(cb => cb.checked = true);
    updateSelectedCount();
}

async function createSelectedTargets() {
    const checkboxes = document.querySelectorAll('.ai-recommendation-checkbox:checked');
    const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index));
    const selectedRecommendations = selectedIndices.map(idx => aiRecommendations[idx]);
    
    if (selectedRecommendations.length === 0) {
        showToast('error', 'Required', 'Please select at least one recommendation', 3000);
        return;
    }
    
    try {
        showToast('info', 'Creating', `Creating ${selectedRecommendations.length} targets...`, 5000);
        
        const recommendationIds = selectedRecommendations.map(rec => rec.contact_id);
        const response = await fetch('/api/targets/ai-create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ 
                recommendation_ids: recommendationIds,
                auto_link: true 
            })
        });
        
        const data = await response.json();
        if (data.success) {
            showToast('success', 'Created', `Created ${data.count} targets successfully`, 3000);
            closeAITargetFinder();
            loadTargetsFromAPI(); // Reload targets list
        } else {
            showToast('error', 'Failed', data.error || 'Failed to create targets', 5000);
        }
    } catch (error) {
        console.error('Error creating targets:', error);
        showToast('error', 'Failed', `Error: ${error.message}`, 5000);
    }
}
```

## 4. Industry Badges in Lists

**Add industry badges to target/contact/company cards:**
```javascript
function getIndustryBadge(industry) {
    if (!industry) return '';
    return `<span class="px-2 py-1 bg-slate-100 text-slate-700 text-xs rounded">${industry}</span>`;
}
```

## Implementation Order

1. ✅ Industry Selector (Header) - Add dropdown and JavaScript functions
2. ✅ Tab Visibility - Add permission checks for Contacts and Companies tabs
3. ✅ AI Target Finder - Add modal and JavaScript functions
4. ✅ Industry Badges - Add to existing render functions
5. ✅ Call `loadIndustries()` on page load

## Testing Checklist

- [ ] Industry selector appears in header
- [ ] Industry switching works and updates active_industry_id
- [ ] Contacts tab hidden if user lacks contact_management permission
- [ ] Companies tab hidden if user lacks company_management permission
- [ ] AI Target Finder modal opens and closes
- [ ] AI target identification returns recommendations
- [ ] Creating targets from recommendations works
- [ ] Industry badges appear on target/contact/company cards







