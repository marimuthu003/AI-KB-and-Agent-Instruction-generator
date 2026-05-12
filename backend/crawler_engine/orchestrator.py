from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from crawler_engine.kb_builder import build_kb
from crawler_engine.prompt_generator import generate_voice_agent_prompt
from crawler_engine.lead_analyzer import analyze_leads
from crawler_engine.agent_engine import AgentEngine

# Reducer to handle concurrent status updates in parallel tracks
def reduce_status(old: str, new: str) -> str:
    return new

# Define the shared state across all agents
class AgentState(TypedDict):
    task_id: str
    url: str
    max_pages: int
    max_depth: int
    business_model: str
    agent_role: str
    crawled_pages: List[Any]
    raw_kb: str
    final_kb: str
    lead_analysis: Optional[Dict[str, Any]]
    kb_evaluation: Optional[Dict[str, Any]]
    agent_instructions: Optional[Dict[str, Any]]
    qa_list: List[Dict[str, Any]]
    status: Annotated[str, reduce_status]
    error: Optional[str]

# Define the Nodes (Agents)
async def scraping_node(state: AgentState):
    # This node is a placeholder because the actual crawling loop 
    # happens in crawler.py to update real-time progress.
    # We will pass the crawled_pages into the state.
    return {"status": "crawling_completed"}

async def text_preprocessor_node(state: AgentState):
    pages = state.get("crawled_pages", [])
    raw_kb = build_kb(pages)
    return {
        "raw_kb": raw_kb,
        "status": "text_preprocessed"
    }

async def kb_generator_node(state: AgentState):
    raw_kb = state.get("raw_kb", "")
    # ...
    business_model = state.get("business_model", "General")
    agent_role = state.get("agent_role", "General")
    
    print(f"[ORCHESTRATOR] Generating structured KB with Gemini ({business_model}/{agent_role})...")
    final_kb = await generate_voice_agent_prompt(raw_kb, business_model=business_model, agent_role=agent_role)
    print(f"[ORCHESTRATOR] Final KB Generated! Length: {len(final_kb)} characters.")
    
    return {
        "raw_kb": raw_kb,
        "final_kb": final_kb,
        "status": "kb_generated"
    }

async def lead_analyzer_node(state: AgentState):
    kb_text = state.get("raw_kb", "")
    analysis = await analyze_leads(kb_text)
    return {
        "lead_analysis": analysis,
        "status": "leads_analyzed"
    }

async def auditor_node(state: AgentState):
    engine = AgentEngine()
    final_kb = state.get("final_kb", "")
    
    eval_resp = await engine.evaluate_kb(final_kb)
    
    update = {
        "kb_evaluation": eval_resp.dict(),
        "final_kb": eval_resp.improved_kb if eval_resp.improved_kb else final_kb,
        "status": "kb_audited"
    }
    
    return update

async def instruction_refiner_node(state: AgentState):
    engine = AgentEngine()
    final_kb = state.get("final_kb", "")
    instr_type = state.get("agent_role", "Sales")
    if instr_type == "General Assistant": instr_type = "Sales"
    
    gen_resp = await engine.generate_instructions(
        input_kb=final_kb,
        instruction_type=instr_type,
        call_direction="Inbound"
    )
    
    return {
        "agent_instructions": gen_resp.dict(),
        "status": "instructions_refined"
    }

async def qa_generator_node(state: AgentState):
    engine = AgentEngine()
    final_kb = state.get("final_kb", "")
    
    qa_resp = await engine.generate_qa(final_kb)
    
    return {
        "qa_list": [qa.dict() for qa in qa_resp.qa_list],
        "status": "completed"
    }

# Build the Graph
def create_orchestrator():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("scraping", scraping_node)
    workflow.add_node("pre-processing", text_preprocessor_node)
    workflow.add_node("kb_generation", kb_generator_node)
    workflow.add_node("lead_analysis", lead_analyzer_node)
    workflow.add_node("auditing", auditor_node)
    workflow.add_node("refining", instruction_refiner_node)
    workflow.add_node("qa_generation", qa_generator_node)

    # Build Edges
    workflow.set_entry_point("scraping")
    workflow.add_edge("scraping", "pre-processing")
    
    # Split after pre-processing
    workflow.add_edge("pre-processing", "kb_generation")
    workflow.add_edge("pre-processing", "lead_analysis")
    
    workflow.add_edge("kb_generation", "auditing")
    workflow.add_edge("auditing", "refining")
    workflow.add_edge("auditing", "qa_generation")
    
    # Join all tracks at the end
    workflow.add_edge("refining", END)
    workflow.add_edge("qa_generation", END)
    workflow.add_edge("lead_analysis", END)

    return workflow.compile()
