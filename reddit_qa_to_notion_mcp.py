from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import TokenVerifier, AccessToken
from mcp.server.auth.settings import AuthSettings
from dotenv import load_dotenv
import praw
import os
from typing import List, Dict, Any, Union
import logging
import requests
from pydantic import BaseModel
from datetime import datetime
import argparse

logger = logging.getLogger(__name__)

load_dotenv()

class SimpleTokenVerifier(TokenVerifier):
    """Simple token verifier for single-user scenarios"""
    
    def __init__(self):
        self.valid_token = os.getenv("MCP_API_KEY")
        if not self.valid_token:
            logger.warning("⚠️  MCP_API_KEY not set - authentication will fail")
    
    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify a bearer token against the single configured key."""
        if not self.valid_token or token != self.valid_token:
            return None
        
        return AccessToken(
            token=token,
            client_id="single_user",
            scopes=["reddit:read", "notion:write"],
            expires_at=None
        )

mcp = FastMCP(
    "Reddit Scraping",
    host="0.0.0.0",
    port=8000,
    stateless_http=True,
    token_verifier=SimpleTokenVerifier(),
    auth=AuthSettings(
        issuer_url="http://localhost:8000",
        resource_server_url="http://localhost:8000",
        required_scopes=["reddit:read", "notion:write"],
    ),
)

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT")
)

class RedditPost(BaseModel):
    title: str
    body: str
    url: str
    created_utc: int
    num_comments: int
    permalink: str
    comments: List[str]

@mcp.tool()
def get_top_subreddit_posts(subreddits: str, limit: int = 5, comment_limit: int = 5, time_filter: str = "week") -> List[Dict[str, Any]]:
    """
    Get top posts from specified subreddits.
    
    Args:
        subreddits (str): Subreddit name(s) separated by '+' (e.g., "redditdev+learnpython")
        limit (int): Number of posts to retrieve (default: 10)
        comment_limit (int): Number of comments to retrieve for each post (default: 5)
        time_filter (str): One of: "all", "day", "hour", "month", "week", "year" (default: "week")
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing post information
    """
    try:
        posts = []
        subreddit = reddit.subreddit(subreddits)
        
        logger.info(f"🔥 Getting top posts from r/{subreddits} (limit={limit}, time_filter={time_filter})")
        
        for post in subreddit.top(time_filter=time_filter, limit=limit):
            post_data = RedditPost(
                title=post.title,
                body=post.selftext,
                url=post.url,
                created_utc=post.created_utc,
                num_comments=post.num_comments,
                permalink=f"https://reddit.com{post.permalink}",
                comments=[]
            )
            
            post.comments.replace_more(limit=0)  # Remove MoreComments objects
            for comment in post.comments.list()[:comment_limit]:  # Get top 5 comments
                post_data.comments.append(comment.body)
                
            posts.append(post_data.model_dump())
        
        logger.info(f"✅ Successfully retrieved {len(posts)} top posts from r/{subreddits}")
        return posts
        
    except Exception as e:
        logger.error(f"❌ Reddit Top Posts Error: {str(e)}")
        
        # Build detailed error info for the response
        error_details = {
            "error": str(e),
            "error_type": type(e).__name__,
            "subreddits": subreddits,
            "time_filter": time_filter,
            "reddit_read_only": reddit.read_only,
            "client_id_exists": bool(reddit.config.client_id),
        }
        
        # Try to get HTTP response details
        if hasattr(e, 'response'):
            error_details.update({
                "http_status": e.response.status_code,
                "response_headers": dict(e.response.headers),
                "response_body": e.response.text[:500]
            })
        
        # Return detailed error info instead of raising
        return [{
            "error_details": error_details,
            "message": f"Top posts retrieval failed for r/{subreddits}: {str(e)}",
            "debug_info": "Check error_details for Reddit API response information"
        }]

@mcp.tool()
def search_posts(subreddits: str, query: str, limit: int = 5, comment_limit: int = 5, sort: str = "relevance") -> List[Dict[str, Any]]:
    """
    Search for posts in specified subreddits.
    
    Args:
        subreddits (str): Subreddit name(s) separated by '+' (e.g., "redditdev+learnpython")
        query (str): Search query
        limit (int): Number of posts to retrieve (default: 5)
        comment_limit (int): Number of comments to retrieve for each post (default: 5)
        sort (str): One of: "relevance", "hot", "top", "new", "comments" (default: "relevance")
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing post information
    """
    try:
        posts = []
        subreddit = reddit.subreddit(subreddits)
        
        logger.info(f"🔍 Searching r/{subreddits} for: '{query}' (limit={limit}, sort={sort})")
        
        for post in subreddit.search(query, sort=sort, limit=limit):
            post_data = RedditPost(
                title=post.title,
                body=post.selftext,
                url=post.url,
                created_utc=post.created_utc,
                num_comments=post.num_comments,
                permalink=f"https://reddit.com{post.permalink}",
                comments=[]
            )
            
            post.comments.replace_more(limit=0)
            for comment in post.comments.list()[:comment_limit]:
                post_data.comments.append(comment.body)
                
            posts.append(post_data.model_dump())
        
        logger.info(f"✅ Successfully found {len(posts)} posts in r/{subreddits}")
        return posts
        
    except Exception as e:
        logger.error(f"❌ Reddit Subreddit Search Error: {str(e)}")
        
        # Build detailed error info for the response
        error_details = {
            "error": str(e),
            "error_type": type(e).__name__,
            "subreddits": subreddits,
            "reddit_read_only": reddit.read_only,
            "client_id_exists": bool(reddit.config.client_id),
        }
        
        # Try to get HTTP response details
        if hasattr(e, 'response'):
            error_details.update({
                "http_status": e.response.status_code,
                "response_headers": dict(e.response.headers),
                "response_body": e.response.text[:500]
            })
        
        # Return detailed error info instead of raising
        return [{
            "error_details": error_details,
            "message": f"Subreddit search failed for r/{subreddits}: {str(e)}",
            "debug_info": "Check error_details for Reddit API response information"
        }]

@mcp.tool()
def search_reddit(query: str, limit: int = 5, comment_limit: int = 5, sort: str = "relevance") -> List[Dict[str, Any]]:
    """
    Search for posts across all subreddits (site-wide search).
    
    Args:
        query (str): Search query
        limit (int): Number of posts to retrieve (default: 5)
        comment_limit (int): Number of comments to retrieve for each post (default: 5)
        sort (str): One of: "relevance", "hot", "top", "new", "comments" (default: "relevance")
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing post information
    """
    try:
        posts = []
        # Use "all" to search across all subreddits
        all_subreddits = reddit.subreddit("all")
        
        logger.info(f"🔍 Searching Reddit for: '{query}' (limit={limit}, sort={sort})")
        
        for post in all_subreddits.search(query, sort=sort, limit=limit):
            post_data = RedditPost(
                title=post.title,
                body=post.selftext,
                url=post.url,
                created_utc=post.created_utc,
                num_comments=post.num_comments,
                permalink=f"https://reddit.com{post.permalink}",
                comments=[]
            )
            
            post.comments.replace_more(limit=0)
            for comment in post.comments.list()[:comment_limit]:
                post_data.comments.append(comment.body)
                
            posts.append(post_data.model_dump())
        
        logger.info(f"✅ Successfully found {len(posts)} Reddit posts")
        return posts
        
    except Exception as e:
        logger.error(f"❌ Reddit API Error: {str(e)}")
        
        # Build detailed error info for the response
        error_details = {
            "error": str(e),
            "error_type": type(e).__name__,
            "reddit_read_only": reddit.read_only,
            "client_id_exists": bool(reddit.config.client_id),
        }
        
        # Try to get HTTP response details
        if hasattr(e, 'response'):
            error_details.update({
                "http_status": e.response.status_code,
                "response_headers": dict(e.response.headers),
                "response_body": e.response.text[:500]  # Limit response body length
            })
        
        # Return detailed error info instead of raising
        return [{
            "error_details": error_details,
            "message": f"Reddit search failed: {str(e)}",
            "debug_info": "Check error_details for Reddit API response information"
        }]

@mcp.tool()
def save_reddit_qa_to_notion(
    question: str, 
    answer: str, 
    search_query: str, 
    reddit_sources: List[Dict[str, str]], 
) -> dict:
    """
    Save a Q&A session with Reddit context to Notion database.
    
    Args:
        question (str): The original question asked
        answer (str): The LLM-generated answer
        search_query (str): The Reddit search query used
        reddit_sources (List[Dict[str, str]]): List of Reddit posts with 'title' and 'url' keys
    
    Returns:
        dict: Success/error response
    """
    try:
        database_id = os.getenv("NOTION_QA_DATABASE_ID") or os.getenv("NOTION_DATABASE_ID")
        api_token = os.getenv("NOTION_API_TOKEN")
        
        if not database_id:
            return {"error": "NOTION_QA_DATABASE_ID or NOTION_DATABASE_ID environment variable not set"}
        if not api_token:
            return {"error": "NOTION_API_TOKEN environment variable not set"}
        
        # Format Reddit sources as text with links
        sources_text = ""
        for i, source in enumerate(reddit_sources, 1):
            sources_text += f"{i}. [{source.get('title', 'Untitled')}]({source.get('url', '#')})\n"
        
        url_endpoint = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        page_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Question": {
                    "title": [
                        {
                            "text": {"content": question}
                        }
                    ]
                },
                "Answer": {
                    "rich_text": [
                        {
                            "text": {"content": answer}
                        }
                    ]
                },
                "Search Query": {
                    "rich_text": [
                        {
                            "text": {"content": search_query}
                        }
                    ]
                },
                "Reddit Sources": {
                    "rich_text": [
                        {
                            "text": {"content": sources_text}
                        }
                    ]
                },
                "Created": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                }
            }
        }
        
        response = requests.post(url_endpoint, json=page_data, headers=headers)
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": f"Successfully saved Q&A session to Notion",
                "question": question[:50] + "..." if len(question) > 50 else question
            }
        else:
            logger.error(f"Notion API error: {response.status_code} - {response.text}")
            return {"error": f"Failed to save to Notion: {response.status_code} - {response.text}"}
            
    except Exception as e:
        logger.error(f"Error saving Q&A to Notion: {str(e)}")
        return {"error": f"Error saving Q&A to Notion: {str(e)}"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reddit Q&A to Notion MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio", help="Transport type")
    
    args = parser.parse_args()

    if args.transport == "http":
        logger.info(f"🚀 Starting HTTP server on localhost:8000")
        logger.info("🔐 Authentication: Bearer token required")
        logger.info("📋 Required scopes: reddit:read, notion:write")
        logger.info("🛠️  Available tools: get_top_subreddit_posts, search_posts, search_reddit, save_reddit_qa_to_notion")
        mcp.run(transport="streamable-http")
    else:
        logger.info("📟 Starting stdio server (no auth required)")
        logger.info("🛠️  Available tools: get_top_subreddit_posts, search_posts, search_reddit, save_reddit_qa_to_notion")
        mcp.run(transport="stdio")