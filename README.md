# Reddit Q&A to Notion MCP Server

A simple MCP server that searches Reddit for answers to questions and saves Q&A sessions to Notion.

## Features

- 🔍 Search across all Reddit or specific subreddits
- 📊 Get top posts with comments for context
- 🤖 Perfect for LLM-powered Q&A workflows
- 💾 Save complete Q&A sessions to Notion
- 🔐 Secure HTTP transport with authentication
- 📱 Built with PRAW for reliable Reddit access

## Quick Start

### 1. Environment Setup

**Create a `.env` file:**
```env
# MCP Authentication
MCP_API_KEY=your-secret-api-key-here

# Reddit API (get from https://www.reddit.com/prefs/apps)
CLIENT_ID=your-reddit-client-id
CLIENT_SECRET=your-reddit-client-secret
USER_AGENT=your-app-name/1.0

# Notion Integration
NOTION_API_TOKEN=your-notion-integration-token
NOTION_QA_DATABASE_ID=your-notion-database-id

# Optional: Proxy for cloud deployments (required for Render, AWS, etc.)
PROXY_URL=http://username:password@proxy-server:port
```

**⚠️ Cloud Platform Note:** Reddit blocks most cloud provider IPs (AWS, Google Cloud, Render, etc.). You need a proxy service for reliable operation.

### 2. Reddit API Setup

1. **Go to:** https://www.reddit.com/prefs/apps
2. **Create a new app** (script type)
3. **Copy Client ID and Secret** to your `.env`
4. **Set User Agent** to something descriptive like `MyBot/1.0`

### 🆓 Free Proxy Setup (Webshare)

**For cloud deployments (Render, Railway, AWS, etc.):**

1. **Sign up at Webshare:** https://www.webshare.io/
2. **Get 10 free proxies** (no credit card required)
3. **Find your proxy details** in their dashboard
4. **Your webshare proxyurl:** `http://username:password@proxy-endpoint:port`
5. **Add to your `.env`:** `HTTP_PROXY=your-webshare-proxy-url` and `HTTPS_PROXY=your-webshare-proxy-url`

### 3. Notion Database Setup

Create a Notion database with these properties:
- **Question** (Title)
- **Answer** (Text)
- **Search Query** (Text)
- **Reddit Sources** (Text)
- **Created** (Date)

### 4. Run the Server

**Option A: With Docker (Recommended)**

```bash
# Build the image
docker build -t reddit-qa-notion-mcp .

# Run the server
docker run -p 8000:8000 -v $(pwd)/.env:/app/.env reddit-qa-notion-mcp
```

The server will be available at `http://localhost:8000`

**Option B: Local Development**

```bash
# Install dependencies
uv sync

# Run with HTTP transport (recommended)
uv run reddit_qa_to_notion_mcp.py --transport http --port 8000

# Or run with stdio transport
uv run reddit_qa_to_notion_mcp.py --transport stdio
```

### 5. Configure MCP Client

Add to your MCP client configuration (e.g., `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "reddit-qa-to-notion-server": {
      "type": "streamable-http", 
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer your-secret-api-key-here"
      }
    }
  }
}
```

## Available Tools

- `search_reddit(query, limit, sort)` - Search across all Reddit subreddits
- `search_posts(subreddits, query, limit, sort)` - Search specific subreddits  
- `get_top_subreddit_posts(subreddits, limit, time_filter)` - Get top posts from subreddits
- `save_reddit_qa_to_notion(question, answer, search_query, reddit_sources)` - Save Q&A session to Notion

## Example Workflow

1. **Ask a question:** "How do I optimize Python performance?"
2. **Search Reddit:** Use `search_reddit()` to find relevant discussions  
3. **Generate answer:** Use Reddit context to inform your LLM response
4. **Save to Notion:** Use `save_reddit_qa_to_notion()` to create a knowledge base entry

## Development

```bash
# Install dependencies
uv sync

# Run locally
uv run reddit_qa_to_notion_mcp.py --transport http
```

The server will be available at `http://localhost:8000`
