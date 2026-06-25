# Chief of Staff — AI Email Triage Assistant

An intelligent email assistant that reads your Gmail inbox, classifies each thread by priority using Google's Gemini AI, and presents a clean daily digest.

![Demo](https://img.shields.io/badge/status-working-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

---

## How It Works

```
Gmail API  ──►  engine.py  ──►  triage.py  ──►  Daily Digest
   │              (MCP)          (Gemini AI)
   │                              │
   │                   ┌──────────┴──────────┐
   │                   │  urgent             │
   │                   │  needs-reply        │
   │                   │  fyi                │
   │                   │  ignore             │
   └───────────────────┴─────────────────────┘
```

1. **`engine.py`** connects to Gmail via an MCP server and fetches your latest inbox threads
2. **`triage.py`** sends each thread to **Gemini 2.5 Flash** which classifies it:
   - **Priority**: `urgent` / `needs-reply` / `fyi` / `ignore`
   - **Category**: `meeting-request`, `follow-up`, `newsletter`, `billing`, etc.
   - **Reason**: one-sentence explanation
3. Results are printed in a sorted digest — urgent first

## Features

- **AI-powered triage** — no rule-writing, just natural language understanding
- **Gmail MCP server** — full read/search capability via Google's API
- **IST timezone** — built-in Indian Standard Time support
- **Rate-limit handling** — auto-retries on API quota exhaustion
- **Extensible** — plug in any MCP-capable Gmail server

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the Gmail MCP server)
- A Google Cloud project with Gmail API enabled (see [gmail-mcp-server setup](gmail-mcp-server/README.md))
- A [Gemini API key](https://aistudio.google.com/apikey)

### Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/chief_of_staff.git
cd chief_of_staff

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # macOS/Linux

# Install Python dependencies
pip install -r requirements.txt

# Build the Gmail MCP server (dist/ is gitignored)
cd gmail-mcp-server
npm install
npm run build
cd ..

# Set up your environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Authenticate Gmail

```bash
cd gmail-mcp-server
npx @gongrzhe/server-gmail-autoauth-mcp auth
cd ..
```

### Run

```bash
python engine.py
```

### Sample output

```
============================================================
  INBOX DIGEST  —  25 Jun 2026  |  3 threads
============================================================
  [URGENT] boss@company.com | Budget approval needed EOD — requires immediate sign-off
  [NEEDS-REPLY] client@acme.com | Project timeline question — waiting for your input
------------------------------------------------------------
  [FYI] team@company.com | Weekly standup notes — informational, no action needed
  [IGNORE] newsletter@medium.com | Top stories this week — promotional content
============================================================
```

## Project Structure

```
chief_of_staff/
├── engine.py                 # Fetches inbox threads via MCP protocol
├── triage.py                 # Classifies emails using Gemini AI
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .gitignore                # Files to exclude from version control
├── LICENSE                   # MIT license
├── README.md                 # This file
└── gmail-mcp-server/         # Gmail MCP server (Node.js)
    ├── src/
    ├── dist/
    ├── mcp-config.json
    └── README.md
```

## Built With

- **[Gemini 2.5 Flash](https://ai.google.dev)** — email classification
- **[MCP Protocol](https://modelcontextprotocol.io)** — standardized AI-to-tool communication
- **[server-gmail-autoauth-mcp](https://github.com/gongrzhe/server-gmail-autoauth-mcp)** — Gmail MCP server
- **Python** — glue logic and orchestration

## Roadmap

- [ ] Auto-label emails in Gmail based on priority
- [ ] Generate AI-powered reply drafts
- [ ] SQLite history to skip re-triaging
- [ ] Web dashboard (Streamlit)
- [ ] Multi-account support
- [ ] Calendar integration

## License

MIT
