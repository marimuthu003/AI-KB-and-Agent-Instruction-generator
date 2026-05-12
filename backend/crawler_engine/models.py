from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class CrawlSiteRequest(BaseModel):
    url: str
    max_pages: int = 25
    max_depth: int = 2
    include_blog: bool = True
    include_legal: bool = False
    include_docs: bool = True
    task_type: str = "both"
    business_model: str = "General"
    agent_role: str = "General"

class SiteMapEntry(BaseModel):
    url: str
    page_type: str
    depth: int
    status: str
    title: Optional[str] = None

class CrawledPage(BaseModel):
    url: str
    markdown: str
    title: Optional[str] = None
    page_type: str = "unknown"
    depth: int = 0

class KBSection(BaseModel):
    title: str
    content: str
    source_url: str

class CompanyProfile(BaseModel):
    company_name: str
    website: str
    short_summary: str
    industry: List[str] = []
    business_type: str
    target_customers: List[str] = []
    location: str
    team_size: Optional[str] = None

class PainPoints(BaseModel):
    customer_pain_points: List[str] = []
    operational_pain_points: List[str] = []
    main_manual_workflows: List[str] = []
    communication_heavy_processes: List[str] = []
    support_burden_signals: Optional[str] = None
    lead_response_pain: Optional[str] = None

class AIVoiceAgentFit(BaseModel):
    product_name: str = "Dakini AI Voice Agents"
    fit_score: int
    fit_level: str
    fit_reason: str
    problems_we_can_solve: List[str] = []
    recommended_use_cases: List[str] = []
    expected_benefits: List[str] = []
    risks_or_limitations: List[str] = []

class LeadAnalysis(BaseModel):
    company_profile: CompanyProfile
    pain_points: PainPoints
    ai_voice_agent_fit: AIVoiceAgentFit

class CrawlSiteResponse(BaseModel):
    task_id: str
    status: str
    message: str

# Agent Integration Models
class EvaluateRequest(BaseModel):
    input_kb: str

class EvaluateResponse(BaseModel):
    score: int
    reasoning: str
    improved_kb: Optional[str] = None

class GenerateRequest(BaseModel):
    input_kb: str
    instruction_type: str = "Sales"
    call_direction: str = "Inbound"
    agent_name: str = "Aaliyah"
    company_name: str = "the company"
    extra_instructions: Optional[str] = ""

class GenerateResponse(BaseModel):
    final_instructions: str
    auditor_score: int
    auditor_reasoning: str
    was_refined: bool

class QaRequest(BaseModel):
    input_kb: str

class QaItem(BaseModel):
    question: str
    answer: str
    type_of_question: str

class QaResponse(BaseModel):
    qa_list: List[QaItem]

class UpdateKBRequest(BaseModel):
    task_id: str
    kb_content: str

class UpdateInstructionsRequest(BaseModel):
    task_id: str
    instructions: str

class UpdateQaRequest(BaseModel):
    task_id: str
    qa_list: List[QaItem]

