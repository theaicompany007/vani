# Project VANI - Dashboard Features Location Guide

## 📍 Where to Find Each Feature on the Dashboard

### ✅ **Multi-channel Outreach (Email, WhatsApp, LinkedIn)**
**Location:** `Target Hit List` tab → Select any target → "Send Outreach" section

**How to Access:**
1. Click **"Target Hit List"** tab (top navigation)
2. Click any target from the list
3. Scroll to **"Send Outreach"** section
4. You'll see three channel buttons:
   - 📧 **Email** button
   - 💬 **WhatsApp** button  
   - 💼 **LinkedIn** button

**What You See:**
- Channel selection buttons
- Message generation interface
- Preview and edit functionality
- Send button

---

### ✅ **AI Message Generation (OpenAI)**
**Location:** `Target Hit List` tab → Select target → "Generate AI Message" button

**How to Access:**
1. Go to **"Target Hit List"** tab
2. Select a target
3. Choose a channel (Email/WhatsApp/LinkedIn)
4. Click **"Generate AI Message"** button (with magic wand icon ✨)

**What Happens:**
- AI generates personalized message based on:
  - Target's role and company
  - Pain point
  - Pitch angle
  - Selected channel

**What You See:**
- Generated message appears in textarea
- Subject line (for email)
- Edit button to customize
- Send button to approve and send

---

### ✅ **Message Preview and Approval**
**Location:** `Target Hit List` tab → After generating message

**How to Access:**
1. Generate a message (see above)
2. Message appears in preview section
3. Review the message
4. Click **"Edit"** to modify if needed
5. Click **"Send Now"** to approve and send

**What You See:**
- Full message preview
- Subject line (for email)
- Edit button
- Send button

---

### ⚠️ **Real-time Engagement Tracking**
**Status:** Backend implemented, UI needs to be added

**Current Location:** 
- **Backend API:** `/api/dashboard/stats` (returns engagement data)
- **Frontend:** Not yet visible on dashboard

**What's Tracked (Backend):**
- Email opens, clicks, replies
- WhatsApp delivered, read, replied
- LinkedIn engagement
- Meeting scheduled events

**To Add to Dashboard:**
- Need to add an "Analytics" or "Engagement" tab
- Display charts showing opens, clicks, replies over time
- Show channel performance metrics

---

### ⚠️ **Meeting Scheduling (Cal.com)**
**Status:** Backend implemented, UI needs integration

**Current Location:**
- **Backend:** Cal.com webhook handler exists
- **Frontend:** Not yet visible

**What Works:**
- Cal.com webhooks receive booking events
- Meetings are saved to database
- Backend API tracks scheduled meetings

**To Add to Dashboard:**
- Add "Meetings" tab or section
- Show upcoming meetings
- Display meeting calendar
- Show meeting status

---

### ⚠️ **Google Sheets Import/Export**
**Status:** Backend implemented, UI buttons missing

**Current Location:**
- **Backend:** `google_sheets_client.py` exists
- **Frontend:** No import/export buttons visible

**What Works (Backend):**
- Can import targets from Google Sheets
- Can export activities to Google Sheets
- API endpoints exist

**To Add to Dashboard:**
- Add "Import from Google Sheets" button
- Add "Export to Google Sheets" button
- Show sync status

---

### ✅ **Dashboard with Analytics**
**Location:** `Situation Room` tab (default view)

**How to Access:**
- Click **"Situation Room"** tab (first tab, active by default)

**What You See:**
1. **Executive Summary Card**
   - Coverage gap explanation
   - The Brain (AI Company) description
   - The Body (Platform) description

2. **The "Void" in Distribution Chart**
   - Doughnut chart showing:
     - 2-3M stores served directly
     - 9M+ "Dark Stores" unserved
   - Visual representation of 80% unserved market

3. **The Solution: Vani Card**
   - Key features list
   - "Deploy Pilot Strategy" button

**Additional Analytics Available:**
- **The Arbitrage** tab: Unit economics comparison chart
- **Revenue Sim** tab: Revenue simulation

---

### ✅ **Webhook Handling for Events**
**Status:** Backend only (runs automatically)

**Location:** 
- **Backend:** `/api/webhooks/resend`, `/api/webhooks/twilio`, `/api/webhooks/cal-com`
- **Frontend:** Not visible (runs in background)

**What Happens:**
- Resend sends email events (sent, delivered, opened, clicked)
- Twilio sends WhatsApp events (delivered, read, replied)
- Cal.com sends meeting events (created, cancelled, rescheduled)
- All events are logged to database automatically

**How to Verify:**
- Check database `webhook_events` table
- Check `outreach_activities` table for status updates

---

### ⚠️ **HIT Notifications (Email & WhatsApp)**
**Status:** Backend implemented, UI notification display missing

**Current Location:**
- **Backend:** Notification system exists
- **Frontend:** No notification center visible

**What's a HIT?**
- Email opened
- Email clicked
- Email replied
- WhatsApp delivered
- WhatsApp read
- WhatsApp replied
- Meeting scheduled

**What Happens:**
- Backend sends email notification to `NOTIFICATION_EMAIL`
- Backend sends WhatsApp notification to `NOTIFICATION_WHATSAPP`

**To Add to Dashboard:**
- Add notification center/bell icon
- Show recent HITs
- Display notification history

---

### ⚠️ **Scheduled Polling (4x Daily)**
**Status:** Backend implemented, UI status missing

**Current Location:**
- **Backend:** Runs automatically at 10 AM, 12 PM, 2 PM, 5 PM
- **Frontend:** No polling status indicator

**What Happens:**
- System polls for updates 4 times daily
- Updates dashboard statistics
- Checks for new engagement events

**To Add to Dashboard:**
- Show "Last Polled" timestamp
- Display next polling time
- Show polling status indicator

---

## 📊 Current Dashboard Tabs

### 1. **Situation Room** (Dashboard)
- ✅ Executive summary
- ✅ Coverage gap chart
- ✅ Solution overview

### 2. **The Arbitrage**
- ✅ Unit economics comparison chart
- ✅ Human vs AI cost analysis

### 3. **Revenue Sim**
- ✅ Revenue simulation charts

### 4. **Target Hit List**
- ✅ List of all targets
- ✅ Target details view
- ✅ **Multi-channel outreach** (Email, WhatsApp, LinkedIn)
- ✅ **AI message generation**
- ✅ **Message preview and approval**

---

## 🚧 Missing UI Features (Backend Ready)

These features work in the backend but need UI buttons/sections:

1. **Google Sheets Import/Export**
   - Need: Import/Export buttons in Target Hit List
   - Backend: ✅ Ready

2. **Real-time Engagement Tracking**
   - Need: Analytics tab with charts
   - Backend: ✅ API ready at `/api/dashboard/stats`

3. **Meeting Scheduling Display**
   - Need: Meetings tab or section
   - Backend: ✅ Webhooks working

4. **HIT Notifications Display**
   - Need: Notification center/bell icon
   - Backend: ✅ Sending notifications

5. **Polling Status**
   - Need: Status indicator showing last poll time
   - Backend: ✅ Running automatically

---

## 🎯 Quick Access Guide

| Feature | Tab | Section | Status |
|---------|-----|---------|--------|
| Multi-channel Outreach | Target Hit List | Send Outreach | ✅ Visible |
| AI Message Generation | Target Hit List | Generate Message | ✅ Visible |
| Message Preview | Target Hit List | Preview Section | ✅ Visible |
| Analytics Charts | Situation Room | Charts | ✅ Visible |
| Google Sheets | - | - | ⚠️ Backend only |
| Engagement Tracking | - | - | ⚠️ Backend only |
| Meetings | - | - | ⚠️ Backend only |
| Notifications | - | - | ⚠️ Backend only |
| Polling Status | - | - | ⚠️ Backend only |

---

## 💡 How to Use What's Available

### To Send Outreach:
1. Go to **Target Hit List**
2. Click a target
3. Choose channel (Email/WhatsApp/LinkedIn)
4. Click **"Generate AI Message"**
5. Review and edit message
6. Click **"Send Now"**

### To View Analytics:
1. Go to **Situation Room** tab
2. See coverage gap chart
3. Go to **The Arbitrage** tab for cost analysis
4. Go to **Revenue Sim** tab for revenue projections

### To Check Backend Stats (API):
- Visit: `http://localhost:5000/api/dashboard/stats`
- Returns JSON with all engagement metrics

---

## 📝 Summary

**Fully Visible on Dashboard:**
- ✅ Multi-channel outreach (Email, WhatsApp, LinkedIn)
- ✅ AI message generation
- ✅ Message preview and approval
- ✅ Analytics charts (coverage gap, arbitrage, revenue)

**Backend Ready, UI Missing:**
- ⚠️ Google Sheets import/export (need buttons)
- ⚠️ Real-time engagement tracking (need analytics tab)
- ⚠️ Meeting scheduling display (need meetings section)
- ⚠️ HIT notifications display (need notification center)
- ⚠️ Polling status (need status indicator)

**Automatic (No UI Needed):**
- ✅ Webhook handling (runs in background)
- ✅ HIT notifications (sends email/WhatsApp automatically)
- ✅ Scheduled polling (runs automatically)

---

**Note:** All backend features are working. The missing UI elements can be added to make these features more accessible from the dashboard.

