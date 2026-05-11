import asyncio
from typing import Dict, Any
from urllib.parse import urlparse, urljoin
from crawl4ai import AsyncWebCrawler
from crawler_engine.models import CrawledPage

# Global store for crawl progress
active_crawls: Dict[str, Any] = {}

def normalize_url(url: str, base_url: str) -> str:
    parsed = urlparse(urljoin(base_url, url))
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def is_valid_link(link: str, base_domain: str, settings: dict) -> bool:
    parsed = urlparse(link)
    if parsed.netloc and parsed.netloc != base_domain and not parsed.netloc.endswith('.' + base_domain):
        return False
    lower_link = link.lower()
    if lower_link.endswith(('.jpg', '.png', '.pdf', '.css', '.js', '.zip', '.mp4', '.gif', '.svg')):
        return False
    if "mailto:" in lower_link or "tel:" in lower_link or "javascript:" in lower_link:
        return False
    if not settings.get("include_blog") and "/blog" in lower_link:
        return False
    if not settings.get("include_legal") and any(x in lower_link for x in ["/privacy", "/terms", "/cookie", "/legal"]):
        return False
    return True

def classify_page(url: str, base_url: str) -> str:
    lower_url = url.lower()
    if url == base_url or url == base_url + "/": return "home"
    if "/about" in lower_url: return "about"
    if "/contact" in lower_url: return "contact"
    if "/pricing" in lower_url: return "pricing"
    if "/blog" in lower_url: return "blog"
    if "/docs" in lower_url: return "docs"
    if "/faq" in lower_url: return "faq"
    return "unknown"

async def run_crawl(task_id: str, request_data: dict):
    base_url = request_data["url"]
    base_domain = urlparse(base_url).netloc
    max_pages = request_data["max_pages"]
    max_depth = request_data["max_depth"]
    
    active_crawls[task_id] = {
        "status": "crawling",
        "input_url": base_url,
        "domain": base_domain,
        "pages_discovered": 1,
        "pages_crawled": 0,
        "useful_pages": 0,
        "site_map": [],
        "crawled_pages": [], 
        "lead_analysis": None,
        "kb_preview": None,
        "kb_file_name": None,
        "error": None
    }
    
    queue = [(base_url, 0)]
    visited = set()
    
    try:
        async with AsyncWebCrawler() as crawler:
            while queue and active_crawls[task_id]["pages_crawled"] < max_pages:
                current_url, depth = queue.pop(0)
                if current_url in visited:
                    continue
                visited.add(current_url)
                
                result = await crawler.arun(url=current_url)
                active_crawls[task_id]["pages_crawled"] += 1
                
                ptype = classify_page(current_url, base_url)
                
                if not result.success:
                    active_crawls[task_id]["site_map"].append({
                        "url": current_url, "page_type": ptype, "depth": depth, "status": "failed", "title": ""
                    })
                    continue
                    
                # Extract internal links
                # In newer versions of crawl4ai, result.links might be a dict or object
                internal_links = []
                if hasattr(result, "links") and isinstance(result.links, dict):
                    internal_links = result.links.get("internal", [])
                
                for link_obj in internal_links:
                    href = link_obj.get("href")
                    if not href: continue
                    norm_url = normalize_url(href, base_url)
                    if norm_url not in visited and is_valid_link(norm_url, base_domain, request_data):
                        if depth + 1 <= max_depth:
                            queue.append((norm_url, depth + 1))
                            active_crawls[task_id]["pages_discovered"] += 1
                
                # Try to get title
                title = "Untitled"
                # metadata access varies depending on crawl4ai version, play it safe
                if hasattr(result, "metadata") and isinstance(result.metadata, dict):
                    title = result.metadata.get("title", "Untitled")
                elif hasattr(result, "title"):
                    title = result.title
                    
                markdown_text = result.markdown or ""
                
                page = CrawledPage(
                    url=current_url,
                    markdown=markdown_text,
                    title=title,
                    page_type=ptype,
                    depth=depth
                )
                
                # Only save pages with some content
                if len(markdown_text.strip()) > 50:
                    active_crawls[task_id]["crawled_pages"].append(page)
                    active_crawls[task_id]["useful_pages"] += 1
                
                active_crawls[task_id]["site_map"].append({
                    "url": current_url, "page_type": ptype, "depth": depth, "status": "success", "title": title
                })
                
                # Yield context to allow other async operations to run and status to be checked
                await asyncio.sleep(0.1)
        
        active_crawls[task_id]["status"] = "building_kb"
        
        # 1. Build KB (Voice Agent Prompt)
        from crawler_engine.kb_builder import build_kb
        kb_text = build_kb(active_crawls[task_id]["crawled_pages"])
        domain_safe = base_domain.replace(".", "-")
        
        # If the task includes KB generation, we synthesize it into the Voice Prompt template
        if request_data.get("task_type") in ("both", "kb_generation"):
            active_crawls[task_id]["status"] = "generating_voice_prompt"
            from crawler_engine.prompt_generator import generate_voice_agent_prompt
            business_model = request_data.get("business_model", "General")
            agent_role = request_data.get("agent_role", "General")
            final_kb_content = generate_voice_agent_prompt(kb_text, business_model=business_model, agent_role=agent_role)
        else:
            final_kb_content = kb_text
            
        active_crawls[task_id]["kb_preview"] = final_kb_content
        active_crawls[task_id]["kb_file_name"] = f"{domain_safe}-voice-prompt.txt"
        
        # 2. Analyze Leads
        if request_data.get("task_type") in ("both", "lead_analysis"):
            active_crawls[task_id]["status"] = "analyzing_leads"
            from crawler_engine.lead_analyzer import analyze_leads
            analysis = analyze_leads(kb_text)
            active_crawls[task_id]["lead_analysis"] = analysis
        
        active_crawls[task_id]["status"] = "completed"

    except Exception as e:
        active_crawls[task_id]["status"] = "failed"
        active_crawls[task_id]["error"] = str(e)
