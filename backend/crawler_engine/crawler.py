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
        "kb_evaluation": None,
        "agent_instructions": None,
        "qa_list": [],
        "error": None
    }
    
    queue = [base_url]
    visited = {base_url}
    
    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
        
        # High-speed STEALTH config
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            wait_for_images=False,
            excluded_tags=['img', 'video', 'style', 'script', 'iframe'],
            # Stealth settings
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        async with AsyncWebCrawler() as crawler:
            # 1. First pass: Get the home page to find links
            result = await crawler.arun(url=base_url, config=run_config)
            active_crawls[task_id]["pages_crawled"] = 1
            
            if result.success:
                # Content validation
                if not result.markdown or len(result.markdown) < 100:
                    print(f"[SYSTEM] WARNING: Homepage returned very little content ({len(result.markdown) if result.markdown else 0} chars). Site might be blocking us.")
                # Extract internal links for batching
                internal_links = []
                if hasattr(result, "links") and isinstance(result.links, dict):
                    internal_links = result.links.get("internal", [])
                
                for link_obj in internal_links:
                    href = link_obj.get("href")
                    if not href: continue
                    norm_url = normalize_url(href, base_url)
                    if norm_url not in visited and is_valid_link(norm_url, base_domain, request_data):
                        queue.append(norm_url)
                        visited.add(norm_url)
                        if len(queue) >= max_pages: break

                # 2. Batch crawl the discovered links in parallel with high concurrency
                batch_urls = queue[1:] # Skip home page
                if batch_urls:
                    results = await crawler.arun_many(urls=batch_urls, config=run_config)
                    
                    for i, res in enumerate(results):
                        current_url = batch_urls[i]
                        active_crawls[task_id]["pages_crawled"] += 1
                        ptype = classify_page(current_url, base_url)
                        
                        title = "Untitled"
                        if hasattr(res, "metadata") and isinstance(res.metadata, dict):
                            title = res.metadata.get("title", "Untitled")
                        
                        markdown_text = res.markdown or ""
                        
                        if res.success and len(markdown_text.strip()) > 50:
                            page = CrawledPage(
                                url=current_url,
                                markdown=markdown_text,
                                title=title,
                                page_type=ptype,
                                depth=1
                            )
                            active_crawls[task_id]["crawled_pages"].append(page)
                            active_crawls[task_id]["useful_pages"] += 1
                        
                        active_crawls[task_id]["site_map"].append({
                            "url": current_url, "page_type": ptype, "depth": 1, 
                            "status": "success" if res.success else "failed", "title": title
                        })
            
            # Handle home page result
            ptype = classify_page(base_url, base_url)
            title = result.metadata.get("title", "Home") if hasattr(result, "metadata") else "Home"
            active_crawls[task_id]["site_map"].insert(0, {
                "url": base_url, "page_type": ptype, "depth": 0, "status": "success", "title": title
            })
            if result.success:
                active_crawls[task_id]["crawled_pages"].append(CrawledPage(
                    url=base_url, markdown=result.markdown, title=title, page_type=ptype, depth=0
                ))
                active_crawls[task_id]["useful_pages"] += 1
    
    except Exception as e:
        active_crawls[task_id]["status"] = "failed"
        active_crawls[task_id]["error"] = str(e)
        return
        
    # --- DATA VALIDATION ---
    if not active_crawls[task_id]["crawled_pages"] or active_crawls[task_id]["useful_pages"] == 0:
        active_crawls[task_id]["status"] = "failed"
        active_crawls[task_id]["error"] = "No content was extracted from the website. The site might be blocking our scraper or is empty."
        print("[SYSTEM] ABORTING: No pages were successfully crawled.")
        return

    # --- LANGGRAPH ORCHESTRATION ---
    print(f"\n[SYSTEM] Crawler finished. Starting AI Orchestration for {len(active_crawls[task_id]['crawled_pages'])} pages...")
    active_crawls[task_id]["status"] = "AI: Initializing Agents..."
    
    try:
        from crawler_engine.orchestrator import create_orchestrator
        
        # Initialize State
        initial_state = {
            "task_id": task_id,
            "url": base_url,
            "max_pages": max_pages,
            "max_depth": max_depth,
            "business_model": request_data.get("business_model", "General"),
            "agent_role": request_data.get("agent_role", "Sales"),
            "crawled_pages": active_crawls[task_id]["crawled_pages"],
            "raw_kb": "",
            "final_kb": "",
            "lead_analysis": None,
            "kb_evaluation": None,
            "agent_instructions": None,
            "qa_list": [],
            "status": "starting_graph",
            "error": None
        }

        # Compile and Run Graph
        app_graph = create_orchestrator()
        
        # Stream updates from the graph
        accumulated_state = initial_state.copy()
        async for output in app_graph.astream(initial_state):
            for node_name, node_output in output.items():
                print(f"[ORCHESTRATOR] Node '{node_name}' completed.")
                # Merge node output into our local tracker
                accumulated_state.update(node_output)
                
                # Update status
                if "status" in node_output:
                    status_map = {
                        "kb_generated": "AI: Building Knowledge Base...",
                        "leads_analyzed": "AI: Extracting Strategic Leads...",
                        "kb_audited": "AI: Auditing Content Quality...",
                        "instructions_refined": "AI: Refining Voice Instructions...",
                        "completed": "completed"
                    }
                    active_crawls[task_id]["status"] = status_map.get(node_output["status"], f"AI: {node_output['status'].replace('_', ' ').title()}...")
                
                # Immediate Sync for live UI feedback
                if "final_kb" in node_output and node_output["final_kb"]:
                    active_crawls[task_id]["kb_content"] = node_output["final_kb"]
                if "lead_analysis" in node_output:
                    active_crawls[task_id]["lead_analysis"] = node_output["lead_analysis"]
                if "kb_evaluation" in node_output:
                    active_crawls[task_id]["kb_evaluation"] = node_output["kb_evaluation"]
                if "agent_instructions" in node_output:
                    active_crawls[task_id]["agent_instructions"] = node_output["agent_instructions"]
                if "qa_list" in node_output:
                    active_crawls[task_id]["qa_list"] = node_output["qa_list"]

        # --- FINAL SAFETY SYNC (Only update if data is present) ---
        print(f"[SYSTEM] Orchestration complete. Syncing final state. KB length: {len(accumulated_state.get('final_kb', ''))}")
        
        if accumulated_state.get("final_kb"):
            active_crawls[task_id]["kb_content"] = accumulated_state["final_kb"]
        if accumulated_state.get("lead_analysis"):
            active_crawls[task_id]["lead_analysis"] = accumulated_state["lead_analysis"]
        if accumulated_state.get("kb_evaluation"):
            active_crawls[task_id]["kb_evaluation"] = accumulated_state["kb_evaluation"]
        if accumulated_state.get("agent_instructions"):
            active_crawls[task_id]["agent_instructions"] = accumulated_state["agent_instructions"]
        if accumulated_state.get("qa_list"):
            active_crawls[task_id]["qa_list"] = accumulated_state["qa_list"]
            
        active_crawls[task_id]["status"] = "completed"
        domain_safe = base_domain.replace(".", "-")
        active_crawls[task_id]["kb_file_name"] = f"{domain_safe}-voice-prompt.txt"

    except Exception as e:
        import traceback
        traceback.print_exc()
        active_crawls[task_id]["status"] = "failed"
        active_crawls[task_id]["error"] = str(e)
