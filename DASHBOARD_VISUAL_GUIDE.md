# Project VANI - Dashboard Visual Guide

## 🎯 Where to Find Features on the Dashboard

When you open `http://localhost:5000/command-center`, here's exactly where to find each feature:

---

## 📍 **Top Navigation Tabs**

At the top of the dashboard, you'll see these tabs:

1. **Situation Room** (default, active on load)
2. **Analytics** 
3. **Meetings**
4. **The Arbitrage**
5. **Revenue Sim**
6. **Target Hit List**

---

## ✅ **VISIBLE FEATURES ON DASHBOARD**

### 1. **Multi-Channel Outreach (Email, WhatsApp, LinkedIn)**

**Location:** 
- Click **"Target Hit List"** tab (6th tab)
- Select any target from the list
- Scroll down to **"Send Outreach"** section

**What You'll See:**
```
┌─────────────────────────────────────┐
│  Send Outreach                      │
├─────────────────────────────────────┤
│  [📧 Email] [💬 WhatsApp] [💼 LinkedIn] │
│                                     │
│  [✨ Generate AI Message]           │
│                                     │
│  [Message Preview Area]             │
│  [✏️ Edit] [📤 Send Now]            │
└─────────────────────────────────────┘
```

**Steps:**
1. Go to **Target Hit List** tab
2. Click on any target (e.g., "HUL", "Britannia")
3. Scroll to **"Send Outreach"** section
4. Click **Email**, **WhatsApp**, or **LinkedIn** button
5. Click **"Generate AI Message"** button
6. Review the generated message
7. Click **"Send Now"** to send

---

### 2. **AI Message Generation**

**Location:** 
- **Target Hit List** tab → Select target → **"Generate AI Message"** button

**What You'll See:**
- A button with magic wand icon: **✨ Generate AI Message**
- After clicking, message appears in textarea
- You can edit before sending

---

### 3. **Analytics Dashboard**

**Location:** 
- Click **"Analytics"** tab (2nd tab in navigation)

**What You'll See:**
```
┌─────────────────────────────────────┐
│  Real-time Engagement Analytics     │
│  [🔄 Refresh]                       │
├─────────────────────────────────────┤
│  • Total Outreach Activities        │
│  • Email Statistics                 │
│  • WhatsApp Statistics              │
│  • Engagement Metrics               │
└─────────────────────────────────────┘
```

**Steps:**
1. Click **"Analytics"** tab at the top
2. Click **"🔄 Refresh"** button to load data
3. View engagement statistics

---

### 4. **Meetings (Cal.com)**

**Location:** 
- Click **"Meetings"** tab (3rd tab in navigation)

**What You'll See:**
```
┌─────────────────────────────────────┐
│  Scheduled Meetings                 │
├─────────────────────────────────────┤
│  [List of meetings from Cal.com]   │
│  • Meeting date/time                │
│  • Attendee information             │
│  • Meeting status                   │
└─────────────────────────────────────┘
```

**Steps:**
1. Click **"Meetings"** tab at the top
2. View scheduled meetings
3. Meetings are loaded automatically

---

### 5. **Google Sheets Import/Export**

**Location:** 
- **Target Hit List** tab → Top right area

**What You'll See:**
```
┌─────────────────────────────────────┐
│  [📥 Import from Sheets]            │
│  [📤 Export to Sheets]              │
└─────────────────────────────────────┘
```

**Steps:**
1. Go to **Target Hit List** tab
2. Look for buttons at the top:
   - **"Import from Sheets"** (green button with download icon)
   - **"Export to Sheets"** (blue button with upload icon)
3. Click to import/export data

---

### 6. **HIT Notifications**

**Location:** 
- Top right corner of dashboard (bell icon 🔔)

**What You'll See:**
```
┌─────────────────────────────────────┐
│  [🔔] (Bell icon in top right)      │
└─────────────────────────────────────┘
```

**Steps:**
1. Look for bell icon in top right corner
2. Click to view notifications
3. Shows email opens, clicks, replies, WhatsApp engagement

---

### 7. **Situation Room (Dashboard Overview)**

**Location:** 
- **"Situation Room"** tab (default, 1st tab)

**What You'll See:**
- Executive summary cards
- Coverage gap chart (doughnut chart)
- Solution overview
- "Deploy Pilot Strategy" button

---

### 8. **The Arbitrage**

**Location:** 
- **"The Arbitrage"** tab (4th tab)

**What You'll See:**
- Unit economics comparison chart
- Human vs AI cost analysis

---

### 9. **Revenue Sim**

**Location:** 
- **"Revenue Sim"** tab (5th tab)

**What You'll See:**
- Revenue simulation charts
- Projection data

---

## 🗺️ **Complete Navigation Map**

```
┌─────────────────────────────────────────────────────────┐
│  [🔔] Notifications                                    │
├─────────────────────────────────────────────────────────┤
│  [Situation Room] [Analytics] [Meetings] [Arbitrage]   │
│  [Revenue Sim] [Target Hit List]                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Content changes based on selected tab]                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 **Quick Feature Finder**

| Feature | Tab | Location | Status |
|---------|-----|----------|--------|
| **Multi-Channel Outreach** | Target Hit List | Select target → Send Outreach section | ✅ Visible |
| **AI Message Generation** | Target Hit List | Select target → Generate AI Message button | ✅ Visible |
| **Message Preview** | Target Hit List | After generating message | ✅ Visible |
| **Analytics** | Analytics | Click Analytics tab | ✅ Visible |
| **Meetings** | Meetings | Click Meetings tab | ✅ Visible |
| **Google Sheets Import** | Target Hit List | Top right buttons | ✅ Visible |
| **Google Sheets Export** | Target Hit List | Top right buttons | ✅ Visible |
| **HIT Notifications** | All tabs | Top right bell icon | ✅ Visible |
| **Dashboard Overview** | Situation Room | Default tab | ✅ Visible |
| **Cost Analysis** | The Arbitrage | Click Arbitrage tab | ✅ Visible |
| **Revenue Projections** | Revenue Sim | Click Revenue Sim tab | ✅ Visible |

---

## 🚀 **Step-by-Step: How to Use Each Feature**

### **To Send an Outreach Message:**

1. **Open Dashboard**: `http://localhost:5000/command-center`
2. **Click "Target Hit List"** tab (6th tab)
3. **Click on a target** (e.g., "HUL")
4. **Choose channel**: Click **Email**, **WhatsApp**, or **LinkedIn** button
5. **Generate message**: Click **"✨ Generate AI Message"** button
6. **Review message**: Message appears in textarea
7. **Edit if needed**: Click **"✏️ Edit"** button
8. **Send**: Click **"📤 Send Now"** button

### **To View Analytics:**

1. **Click "Analytics"** tab (2nd tab)
2. **Click "🔄 Refresh"** button
3. **View statistics**: See engagement metrics

### **To View Meetings:**

1. **Click "Meetings"** tab (3rd tab)
2. **View list**: See scheduled meetings from Cal.com

### **To Import/Export from Google Sheets:**

1. **Go to "Target Hit List"** tab
2. **Click "📥 Import from Sheets"** or **"📤 Export to Sheets"**
3. **Wait for toast notification**: Shows "OK" or "Not OK" status

### **To View Notifications:**

1. **Click bell icon 🔔** in top right corner
2. **View HIT notifications**: See email opens, clicks, replies

---

## 🔍 **If You Can't See Features:**

### **Check 1: Are you logged in?**
- Go to: `http://localhost:5000/login`
- Login with your credentials
- Then go to: `http://localhost:5000/command-center`

### **Check 2: Is the app running?**
```bash
# Check if Flask is running
# Should see: "Running on http://127.0.0.1:5000"
```

### **Check 3: Check browser console**
- Press `F12` to open developer tools
- Check for JavaScript errors
- Check Network tab for API errors

### **Check 4: Verify targets exist**
- Go to **Target Hit List** tab
- If no targets shown, run: `python scripts/seed_targets.py`

---

## 📱 **Visual Layout**

```
┌─────────────────────────────────────────────────────────────┐
│  PROJECT VANI | Strategic Command    [🔔 Notifications]     │
├─────────────────────────────────────────────────────────────┤
│  [Situation Room] [Analytics] [Meetings] [Arbitrage]        │
│  [Revenue Sim] [Target Hit List]                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  [Tab Content - Changes based on selected tab]       │  │
│  │                                                      │  │
│  │  For "Target Hit List":                             │  │
│  │  • List of targets                                  │  │
│  │  • [Import] [Export] buttons                        │  │
│  │  • Target details                                   │  │
│  │  • Send Outreach section                            │  │
│  │    - [Email] [WhatsApp] [LinkedIn]                 │  │
│  │    - [Generate AI Message]                          │  │
│  │    - Message preview                                │  │
│  │    - [Send Now]                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ **Summary: What's Visible**

**Fully Visible and Working:**
- ✅ Multi-channel outreach buttons (Email, WhatsApp, LinkedIn)
- ✅ AI message generation button
- ✅ Message preview and editing
- ✅ Send button
- ✅ Analytics tab with refresh button
- ✅ Meetings tab
- ✅ Google Sheets import/export buttons
- ✅ HIT notifications bell icon
- ✅ Dashboard overview (Situation Room)
- ✅ Cost analysis (Arbitrage)
- ✅ Revenue projections (Revenue Sim)

**All features listed in the feature overview ARE visible on the dashboard!**

---

**Last Updated**: December 2025  
**Dashboard URL**: `http://localhost:5000/command-center`

