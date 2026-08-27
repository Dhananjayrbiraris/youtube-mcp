# YouTube Studio & Channel Analytics MCP Server

A Model Context Protocol (MCP) server that empowers AI assistants to analyze your YouTube channel, monitor video metrics, deep-dive into YouTube Studio analytics, discover audience traffic sources, and analyze community engagement — **configured entirely through `.env`**.

---

## 🚀 Features & MCP Tools

| Tool | Description |
| :--- | :--- |
| **`get_channel_overview`** | Fetches channel title, handle, subscriber count, total lifetime views, video count, topic categories, and channel description. |
| **`get_channel_analytics`** | Fetches core Studio metrics (`views`, `watch time hours`, `average view duration`, `subscribers gained/lost`, `likes`, `shares`, `comments`, `impressions`, `CTR`) over any timeframe (`7d`, `28d`, `90d`, `365d`, `last_month`, or custom dates). |
| **`get_analytics_by_dimension`** | Detailed breakdowns by dimension: `trafficSource` (YouTube search, suggested videos, browse features), `deviceType`, `country` (geographics), `ageGroup`, `gender`, `operatingSystem`, or `day`. |
| **`get_top_performing_videos`** | Ranks your top videos by views, watch time minutes, or subscribers gained in any date range. |
| **`get_video_analytics`** | Deep-dive analytics on a single specific video (daily trajectory, traffic sources, audience retention). |
| **`list_channel_videos`** | Lists recent uploaded videos with views, likes, comments, duration, and privacy status. |
| **`get_video_details`** | Returns full metadata, tags, description, category, and statistics for specified video IDs. |
| **`get_video_comments`** | Retrieves top comment threads and replies across your channel or on a specific video for sentiment analysis and feedback. |

---

## ⚙️ Configuration via `.env`

All credentials and settings are read directly from `.env`:

```ini
# Google OAuth 2.0 Credentials (from Google Cloud Console)
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret

# OAuth Refresh Token (written automatically by run_auth.py)
YOUTUBE_REFRESH_TOKEN=
```

---

## 🛠️ Step-by-Step Setup

### Step 1: Install Dependencies with `uv`

```powershell
uv venv
uv pip install -e .
```

---

### Step 2: Get Google Cloud Client ID & Secret

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project (e.g. `YouTube-MCP-Studio`).
3. In **APIs & Services > Library**, enable:
   - **YouTube Data API v3**
   - **YouTube Analytics API**
4. In **OAuth consent screen**:
   - Choose **External** -> fill app name & email.
   - Under **Test users**, add your Google email address.
5. In **Credentials**:
   - Click **Create Credentials** -> **OAuth client ID**.
   - Application Type: **Desktop App**.
   - Copy the **Client ID** and **Client Secret**.
6. Paste them directly into your `.env` file:
   ```ini
   YOUTUBE_CLIENT_ID=123456789-xxxx.apps.googleusercontent.com
   YOUTUBE_CLIENT_SECRET=GOCSPX-xxxx
   ```

---

### Step 3: Run 1-Click Authenticator

Run:

```powershell
uv run run_auth.py
```

This launches your browser for a 1-click Google login. It automatically writes the **`YOUTUBE_REFRESH_TOKEN`** directly into your **`.env`** file.

---

### Step 4: Add to Antigravity / Claude Desktop MCP Configuration

Add this entry to your MCP configuration:

```json
{
  "mcpServers": {
    "youtube-studio": {
      "command": "uv",
      "args": [
        "--directory",
        "c:/Users/dhananjay.biraris/Desktop/Dhananjay_PC_Backup/Desktop/Youtube MCP",
        "run",
        "youtube-studio-mcp"
      ]
    }
  }
}
```

---

## 💡 Example Queries with AI

- *"Give me a complete summary of my channel stats for the last 28 days."*
- *"Where is most of my traffic coming from (search, suggested, browse)?"*
- *"Which videos gave me the most subscribers this month?"*
- *"Summarize the feedback and common questions in the comments of my latest video."*
- *"What is the demographic breakdown of my viewers by age and country?"*
