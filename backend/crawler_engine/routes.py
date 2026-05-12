import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from crawler_engine.models import (
    CrawlSiteRequest, 
    CrawlSiteResponse, 
    EvaluateRequest, 
    EvaluateResponse,
    GenerateRequest,
    GenerateResponse,
    QaRequest,
    QaResponse,
    UpdateKBRequest,
    UpdateInstructionsRequest,
    UpdateQaRequest
)
from crawler_engine.crawler import run_crawl, active_crawls
from crawler_engine.agent_engine import AgentEngine

agent_engine = AgentEngine()

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
        "kb_content": status_data.get("kb_content", ""),
        "kb_file_name": status_data["kb_file_name"],
        "kb_evaluation": status_data.get("kb_evaluation"),
        "agent_instructions": status_data.get("agent_instructions"),
        "qa_list": status_data.get("qa_list", []),
        "error": status_data.get("error")
    }
    
    return response_data

@router.get("/api/download-kb/{task_id}")
async def download_kb(task_id: str):
    if task_id not in active_crawls:
        raise HTTPException(status_code=404, detail="Task ID not found")
        
    status_data = active_crawls[task_id]
    if status_data["status"] != "completed" or not status_data.get("kb_content"):
        raise HTTPException(status_code=400, detail="KB not ready yet")
        
    headers = {
        'Content-Disposition': f'attachment; filename="{status_data["kb_file_name"]}"'
    }
    return PlainTextResponse(content=status_data["kb_content"], headers=headers)

@router.post("/api/evaluate", response_model=EvaluateResponse)
async def evaluate_kb(request: EvaluateRequest):
    return await agent_engine.evaluate_kb(request.input_kb)

@router.post("/api/generate", response_model=GenerateResponse)
async def generate_instructions(request: GenerateRequest):
    return await agent_engine.generate_instructions(
        input_kb=request.input_kb,
        instruction_type=request.instruction_type,
        call_direction=request.call_direction,
        agent_name=request.agent_name,
        company_name=request.company_name,
        extra_instructions=request.extra_instructions
    )

@router.post("/api/generate_qa", response_model=QaResponse)
async def generate_qa(request: QaRequest):
    return await agent_engine.generate_qa(request.input_kb)

@router.post("/api/update-kb")
async def update_kb(request: UpdateKBRequest):
    if request.task_id not in active_crawls:
        raise HTTPException(status_code=404, detail="Task ID not found")
    active_crawls[request.task_id]["kb_preview"] = request.kb_content
    return {"status": "success"}

@router.post("/api/update-instructions")
async def update_instructions(request: UpdateInstructionsRequest):
    if request.task_id not in active_crawls:
        raise HTTPException(status_code=404, detail="Task ID not found")
    if active_crawls[request.task_id]["agent_instructions"]:
        active_crawls[request.task_id]["agent_instructions"].final_instructions = request.instructions
    else:
        # Create a basic structure if it doesn't exist
        from crawler_engine.models import GenerateResponse
        active_crawls[request.task_id]["agent_instructions"] = GenerateResponse(
            final_instructions=request.instructions,
            auditor_score=100,
            auditor_reasoning="Manually updated",
            was_refined=True
        )
    return {"status": "success"}

@router.post("/api/update-qa")
async def update_qa(request: UpdateQaRequest):
    if request.task_id not in active_crawls:
        raise HTTPException(status_code=404, detail="Task ID not found")
    active_crawls[request.task_id]["qa_list"] = request.qa_list
    return {"status": "success"}
