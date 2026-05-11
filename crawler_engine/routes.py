import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from crawler_engine.models import CrawlSiteRequest, CrawlSiteResponse
from crawler_engine.crawler import run_crawl, active_crawls

router = APIRouter()

@router.post("/api/crawl-site", response_model=CrawlSiteResponse)
async def crawl_site(request: CrawlSiteRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    
    # Run the crawl task in the background
    background_tasks.add_task(run_crawl, task_id, request.dict())
    
    return CrawlSiteResponse(
        task_id=task_id,
        status="started",
        message="Crawl started successfully. Poll /api/crawl-status/{task_id} for progress."
    )

@router.get("/api/crawl-status/{task_id}")
async def get_crawl_status(task_id: str):
    if task_id not in active_crawls:
        raise HTTPException(status_code=404, detail="Task ID not found")
        
    status_data = active_crawls[task_id]
    
    response_data = {
        "status": status_data["status"],
        "input_url": status_data["input_url"],
        "pages_discovered": status_data["pages_discovered"],
        "pages_crawled": status_data["pages_crawled"],
        "useful_pages": status_data["useful_pages"],
        # only send full site map if done to save bandwidth
        "site_map": status_data["site_map"] if status_data["status"] in ("completed", "failed") else [],
        "lead_analysis": status_data["lead_analysis"],
        "kb_preview": status_data["kb_preview"][:2000] + "\n...[Full KB is available for download]" if status_data["kb_preview"] else None,
        "kb_file_name": status_data["kb_file_name"],
        "error": status_data.get("error")
    }
    
    return response_data

@router.get("/api/download-kb/{task_id}")
async def download_kb(task_id: str):
    if task_id not in active_crawls:
        raise HTTPException(status_code=404, detail="Task ID not found")
        
    status_data = active_crawls[task_id]
    if status_data["status"] != "completed" or not status_data["kb_preview"]:
        raise HTTPException(status_code=400, detail="KB not ready yet")
        
    headers = {
        'Content-Disposition': f'attachment; filename="{status_data["kb_file_name"]}"'
    }
    return PlainTextResponse(content=status_data["kb_preview"], headers=headers)
