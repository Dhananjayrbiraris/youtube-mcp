<div align="center">

# YouTube Studio & Channel Analytics MCP Server

**A Production-Grade Model Context Protocol (MCP) Server for YouTube Studio & Channel Intelligence**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python)](https://www.python.org/)
[![Managed by: uv](https://img.shields.io/badge/managed%20by-uv-DE5FE9.svg?logo=astral)](https://github.com/astral-sh/uv)
[![MCP Compatible](https://img.shields.io/badge/MCP-Official%20SDK-black.svg)](https://modelcontextprotocol.io/)

*Empower AI assistants (Claude, Cursor, Antigravity, etc.) to analyze your YouTube channel, track video metrics, deep-dive into YouTube Studio analytics, discover audience traffic sources, and analyze community sentiment — configured entirely through `.env`.*

</div>

---

## 🚀 Features & MCP Tool Suite

YouTube Studio MCP provides **8 specialized tools**:

| Tool | Category | Description |
| :--- | :--- | :--- |
| **`get_channel_overview`** | Channel Stats | Returns channel title, handle, subscriber count, total lifetime views, video count, topic categories, and description. |
| **`get_channel_analytics`** | Studio Analytics | Queries core Studio metrics (`views`, `watch time hours`, `average view duration`, `subscribers gained/lost`, `likes`, `shares`, `comments`, `impressions`, `CTR`) over any timeframe (`7d`, `28d`, `90d`, `365d`, `last_month`, or custom dates). |
| **`get_analytics_by_dimension`** | Demographics & Traffic | Detailed breakdowns by dimension: `trafficSource` (YouTube search, suggested, browse), `deviceType`, `country`, `ageGroup`, `gender`, `operatingSystem`, or `day`. |
| **`get_top_performing_videos`** | Video Intelligence | Ranks your top videos by views, watch time minutes, or subscribers gained in any date range. |
| **`get_video_analytics`** | Video Deep-Dive | Deep-dive analytics on a single specific video (daily trajectory, watch time, audience retention, traffic sources). |
| **`list_channel_videos`** | Content Inventory | Lists uploaded videos with current views, likes, comments, duration, and privacy status. |
| **`get_video_details`** | Video Metadata | Returns full metadata, tags, description, category, and statistics for specified video IDs. |
| **`get_video_comments`** | Community & Sentiment | Retrieves top comment threads and replies across your channel or on a specific video for sentiment analysis and feedback. |

---

## ⚙️ Environment Configuration (`.env`)

All credentials and settings are read directly from `.env`:

```ini
# Google OAuth 2.0 Credentials (from Google Cloud Console)
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret

# OAuth Refresh Token (written automatically by run_auth.py)
YOUTUBE_REFRESH_TOKEN=
```

---

## 🛠️ Step-by-Step Setup Guide

### 1. Clone & Install Dependencies with `uv`

```bash
git clone https://github.com/Dhananjayrbiraris/youtube-mcp.git
cd youtube-mcp

uv venv
uv pip install -e .
```

---

### 2. Set Up Google Cloud Project (One-Time)

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g. `YouTube-Studio-MCP`).
3. In **APIs & Services > Library**, enable:
   - **YouTube Data API v3**
   - **YouTube Analytics API**
4. In **OAuth consent screen**:
   - User Type: **External** -> fill app name & your email.
   - Under **Test users**, add your Google email address.
5. In **Credentials**:
   - Click **Create Credentials > OAuth client ID**.
   - Application Type: **Desktop App**.
   - Copy the **Client ID** and **Client Secret**.
6. Paste them into `.env`:
   ```ini
   YOUTUBE_CLIENT_ID=123456789-xxxx.apps.googleusercontent.com
   YOUTUBE_CLIENT_SECRET=GOCSPX-xxxx
   ```

---

### 3. Run 1-Click Authenticator

```bash
uv run run_auth.py
```

This launches your browser for a 1-click Google OAuth login. It automatically writes the **`YOUTUBE_REFRESH_TOKEN`** directly into your **`.env`** file.

---

### 4. Connect to your AI Client

#### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "youtube-studio": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/youtube-mcp",
        "run",
        "youtube-studio-mcp"
      ]
    }
  }
}
```

---

## 💡 Example AI Prompts

- *"Give me an overview of my YouTube channel's performance over the last 28 days."*
- *"Where is most of my traffic coming from (search, suggested videos, or browse features)?"*
- *"Which of my videos generated the most subscribers this month?"*
- *"Summarize common themes and questions from the comments on my latest video."*
- *"Show me my audience breakdown by age group and country."*

---

## 🧪 Testing

Run the test suite:

```bash
pytest
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
