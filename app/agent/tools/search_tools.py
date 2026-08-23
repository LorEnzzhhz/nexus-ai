import httpx
import json
from bs4 import BeautifulSoup


async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo and return results."""
    results = []
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (compatible; NexusAI/1.0)"},
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            for result in soup.select(".result")[:max_results]:
                title_el = result.select_one(".result__title a")
                snippet_el = result.select_one(".result__snippet")
                if title_el:
                    url = title_el.get("href", "")
                    if "uddg=" in url:
                        from urllib.parse import urlparse, parse_qs
                        parsed = parse_qs(urlparse(url).query)
                        url = parsed.get("uddg", [url])[0]
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": url,
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })
    except Exception as e:
        return json.dumps({"error": f"Search failed: {e}"})

    if not results:
        return json.dumps({"message": "No results found", "query": query})
    return json.dumps({"query": query, "results": results})


async def fetch_url(url: str) -> str:
    """Fetch a URL and extract readable text content."""
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; NexusAI/1.0)"},
            )
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        if len(text) > 50_000:
            text = text[:50_000] + "\n... (truncated)"
        return json.dumps({"url": url, "content": text})
    except Exception as e:
        return json.dumps({"error": f"Fetch failed: {e}"})


SEARCH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information. Returns titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 5)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Fetch a URL and extract its readable text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                },
                "required": ["url"],
            },
        },
    },
]
