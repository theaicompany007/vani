# AI Target Finder Enhancement Plan

## Overview
Enhance the AI Target Finder with search configurations, industry search bar, improved loading animations, results storage, and history view similar to Pitch Presentation.

## Requirements

### 1. Search Configurations
- Provide multiple preset configurations:
  - **High Priority** (default): min_seniority=0.7, limit=10, focus on C-level executives
  - **Broad Search**: min_seniority=0.3, limit=10, includes mid-level managers
  - **C-Level Only**: min_seniority=0.9, limit=10, strict C-level filtering
  - **Custom**: User can override all settings
- Default to "High Priority" configuration
- Allow quick switching between presets

### 2. Industry Selection
- Replace dropdown with **searchable multi-select** component
- Support 100+ industries
- Allow selecting multiple industries at once
- Show selected industries as badges/tags
- Search functionality: type to filter industries

### 3. Loading Animation
- Enhanced animation during AI processing
- Show progress indicators
- Display estimated time remaining
- Animated spinner with contextual messages

### 4. Results Limit
- Set default limit to **10 results** per search
- Allow user to override if needed

### 5. Results Storage
- Create `ai_target_search_results` table to store:
  - Search configuration (industries, min_seniority, limit)
  - Search timestamp
  - User who ran the search
  - Results (JSONB column)
  - Search metadata (search_id, status)
- Save results automatically after each search

### 6. History View
- Create "AI Target Finder History" section
- Grid layout similar to Pitch History
- Each history item shows:
  - Search date/time
  - Industries searched
  - Number of results
  - Configuration used
- Collapse/expand functionality for each history item
- Click to view full results from that search
- Ability to re-run a previous search

## Implementation Steps

### Step 1: Database Migration
**File**: `app/migrations/016_ai_target_search_results.sql`

Create table:
```sql
CREATE TABLE IF NOT EXISTS ai_target_search_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    industry_id UUID REFERENCES industries(id) ON DELETE SET NULL,
    search_config JSONB NOT NULL, -- {industries: [], min_seniority: 0.7, limit: 10, preset: "high_priority"}
    results JSONB NOT NULL, -- Array of recommendations
    result_count INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'completed', -- completed, failed, partial
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ai_search_results_user ON ai_target_search_results(user_id);
CREATE INDEX idx_ai_search_results_created ON ai_target_search_results(created_at DESC);
```

### Step 2: Update API Endpoint
**File**: `app/api/targets.py`

Modify `ai_identify_targets()` to:
- Accept multiple industries (array)
- Accept search_config preset name
- Save results to `ai_target_search_results` table
- Return `search_id` along with results

### Step 3: Create History API Endpoint
**File**: `app/api/targets.py`

Add new endpoint:
```python
@targets_bp.route('/api/targets/ai-search-history', methods=['GET'])
@require_auth
@require_use_case('ai_target_finder')
def get_ai_search_history():
    """Get AI target search history for current user"""
    # Fetch from ai_target_search_results table
    # Return paginated list of searches
```

### Step 4: Update UI - Search Configurations
**File**: `app/templates/command_center.html`

Replace configuration section with:
- Radio buttons or dropdown for preset selection
- "Custom" option that shows all fields
- Default to "High Priority"

### Step 5: Update UI - Industry Multi-Select
**File**: `app/templates/command_center.html`

Replace industry dropdown with:
- Searchable input field
- Dropdown list that filters as user types
- Multi-select checkboxes
- Selected industries shown as removable badges
- Support for 100+ industries

### Step 6: Enhanced Loading Animation
**File**: `app/templates/command_center.html`

Update loading state:
- Animated progress bar
- Step indicators (Analyzing contacts, Running AI, Generating recommendations)
- Estimated time display
- Cancel button (optional)

### Step 7: History View UI
**File**: `app/templates/command_center.html`

Add new section:
- "AI Target Finder History" tab or section
- Grid layout with cards
- Each card shows:
  - Date/time
  - Industries (badges)
  - Result count
  - Configuration preset
  - Expand/collapse button
- Expanded view shows full results list
- "Re-run Search" button

### Step 8: JavaScript Functions
**File**: `app/templates/command_center.html`

New functions needed:
- `loadAISearchHistory()` - Fetch and display history
- `renderAISearchHistory()` - Render history grid
- `toggleSearchHistoryItem(id)` - Expand/collapse
- `rerunAISearch(searchId)` - Re-run previous search
- `loadIndustriesForSearch()` - Load industries for multi-select
- `filterIndustries(searchTerm)` - Filter industries as user types

## Files to Modify

1. **Database**:
   - `app/migrations/016_ai_target_search_results.sql` (new)

2. **Backend**:
   - `app/api/targets.py` - Update `ai_identify_targets()` and add history endpoint

3. **Frontend**:
   - `app/templates/command_center.html` - Update AI Target Finder section

## UI/UX Details

### Search Configuration Presets
```
[○] High Priority (Default)    min_seniority: 0.7, limit: 10
[ ] Broad Search               min_seniority: 0.3, limit: 10
[ ] C-Level Only               min_seniority: 0.9, limit: 10
[ ] Custom                     [Show all fields]
```

### Industry Multi-Select
```
[Search industries...] ▼
Selected: [Technology ×] [Healthcare ×] [Finance ×]

[✓] Technology
[✓] Healthcare
[✓] Finance
[ ] Education
[ ] Manufacturing
...
```

### History Grid
```
┌─────────────────────────────────────┐
│ Dec 11, 2025 4:30 PM                │
│ Industries: [Tech] [Healthcare]     │
│ Results: 10                          │
│ Config: High Priority               │
│ [▶ Expand] [Re-run]                 │
└─────────────────────────────────────┘
```

## Testing Checklist

- [ ] Search configurations work correctly
- [ ] Industry multi-select handles 100+ industries
- [ ] Loading animation displays properly
- [ ] Results are saved to database
- [ ] History view loads and displays correctly
- [ ] Collapse/expand works for history items
- [ ] Re-run search functionality works
- [ ] Default limit is 10 results
- [ ] Multiple industries can be selected
- [ ] Search history is user-specific













