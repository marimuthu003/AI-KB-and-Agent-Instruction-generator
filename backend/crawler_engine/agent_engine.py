import os
import json
import asyncio
from typing import Optional, List
from google import genai
from google.genai import types
from .models import EvaluateResponse, GenerateResponse, QaResponse, QaItem

# --- ACCURATE CONFIG TEMPLATES FROM REPO ---
INSTRUCTION_TEMPLATES = {
    "Sales": {
        "Inbound": """
Generate a production ready inbound B2B AI sales voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, professional, consultative, conversational, and non pushy with one question at a time behavior.

Include not asking the same question,assistant identity, silent start, inbound greeting, sales intent detection, requirement discovery, pain point discovery, BANT qualification, product explanation, pricing discussion, objection handling, demo scheduling, callback handling, CRM extraction, conversational memory, escalation, wrap up, and outcome classification.

Detect pricing, demo, integration, enterprise, competitor, callback, and purchase intents.

Collect customer name, company, role, industry, contact details, workflow, pain points, budget indicators, timeline, integrations, team size, decision maker status, and product interest.

Generate structured conversational states from Greeting to Wrap Up. Keep responses short and voice friendly. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive sales behavior, excessive use of special characters and "*".
""",
        "Outbound": """
Generate a production ready outbound B2B AI sales voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, professional, consultative, conversational, and non pushy with one question at a time behavior.

Include not asking the same question, assistant identity, outbound greeting, permission based opening, prospect qualification, business discovery, pain point discovery, BANT qualification, product explanation, pricing discussion, objection handling, follow up handling, demo scheduling, callback handling, CRM extraction, conversational memory, escalation, wrap up, and outcome classification.

Detect pricing, demo, enterprise, integration, competitor, callback, purchase, and follow up intents.

Collect customer name, company, role, industry, workflow, pain points, current tools, budget indicators, timeline, team size, integrations, contact details, and decision maker status.

Generate structured conversational states from Greeting to Wrap Up. Keep responses short and voice friendly. Ask one question at a time. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive sales behavior, excessive use of special characters and "*".
"""
    },
    "B2B": {
        "Inbound": """
Generate a production ready inbound B2B AI voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, professional, consultative, conversational, and non pushy with one question at a time behavior.

Include not asking the same question,assistant identity, inbound greeting, intent detection, business discovery, pain point discovery, BANT qualification, product explanation, pricing discussion, objection handling, demo scheduling, callback handling, CRM extraction, conversational memory, escalation, follow up, wrap up, and outcome classification.

Detect pricing, demo, enterprise, integration, support, competitor, callback, and purchase intents.

Collect customer name, company, role, industry, workflow, pain points, integrations, budget indicators, timeline, team size, contact details, and decision maker status.

Keep responses short and voice friendly. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive behavior, excessive use of special characters and "*"   .
""",
        "Outbound": """
Generate a production ready outbound B2B AI sales voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, professional, consultative, conversational, and non pushy with one question at a time behavior.

Include not asking the same question,assistant identity, outbound greeting, permission based opening, prospect qualification, pain point discovery, BANT qualification, product explanation, pricing discussion, objection handling, demo scheduling, callback handling, CRM extraction, conversational memory, follow up, wrap up, and outcome classification.

Detect pricing, demo, enterprise, integration, competitor, callback, purchase, and follow up intents.

Collect customer name, company, role, industry, workflow, pain points, budget indicators, timeline, integrations, contact details, and decision maker status.

Keep responses short and voice friendly. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive behavior, excessive use of special characters and "*".
"""
    },
    "B2C": {
        "Inbound": """
Generate a production ready inbound B2C AI voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, friendly, professional, conversational, and non pushy with one question at a time behavior.

Include not asking the same question,assistant identity, inbound greeting, customer verification, intent detection, requirement discovery, issue understanding, product or service recommendation, pricing discussion, objection handling, booking support, callback handling, CRM extraction, conversational memory, escalation, follow up, wrap up, and outcome classification.

Detect sales, support, pricing, booking, complaint, refund, cancellation, delivery status, callback, and purchase intents.

Collect customer name, contact details, preferences, issue details, product interest, budget indicators, purchase intent, and booking information.

Keep responses short and voice friendly. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive behavior, excessive use of special characters and "*".
""",
        "Outbound": """
Generate a production ready outbound B2C AI voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, friendly, professional, conversational, and non pushy with one question at a time behavior.

Include not asking the same question,assistant identity, outbound greeting, permission based opening, interest discovery, requirement discovery, product or service recommendation, pricing discussion, objection handling, booking support, callback handling, CRM extraction, conversational memory, follow up, wrap up, and outcome classification.

Detect sales, pricing, callback, booking, support, purchase, cancellation, and follow up intents.

Collect customer name, contact details, preferences, issue details, product interest, budget indicators, purchase intent, and booking information.

Keep responses short and voice friendly. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive behavior, excessive use of special characters and "*".
"""
    },
    "C2B": {
        "Inbound": """
Generate a production ready inbound C2B AI voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, professional, conversational, respectful, and non pushy with one question at a time behavior.

Include not asking the same question,assistant identity, inbound greeting, intent detection, collaboration discovery, requirement gathering, pricing discussion, portfolio collection, document handling, objection handling, callback handling, CRM extraction, conversational memory, escalation, follow up, wrap up, and outcome classification.

Detect partnership, freelancing, sponsorship, affiliate, consulting, recruitment, collaboration, callback, and pricing intents.

Collect name, role, company, audience details, service details, experience, portfolio, pricing expectations, deliverables, timeline, contact details, and collaboration goals.

Keep responses short and voice friendly. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive behavior,excessive use of special characters and "*".
""",
        "Outbound": """
Generate a production ready outbound C2B AI voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, professional, conversational, respectful, and non pushy with one question at a time behavior.

Include not asking the same question,assistant identity, outbound greeting, permission based opening, collaboration discovery, requirement gathering, pricing discussion, portfolio collection, document handling, objection handling, callback handling, CRM extraction, conversational memory, follow up, wrap up, and outcome classification.

Detect partnership, freelancing, sponsorship, affiliate, consulting, recruitment, collaboration, callback, and pricing intents.

Collect name, role, company, audience details, service details, experience, portfolio, pricing expectations, deliverables, timeline, contact details, and collaboration goals.

Keep responses short and voice friendly. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive behavior, and excessive special characters.
"""
    },
    "enquiry": {
        "Inbound": """
Generate a production ready inbound enquiry AI voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, professional, conversational, helpful, and non pushy with one question at a time behavior.

Include not asking the same question,assistant identity, inbound greeting, enquiry intent detection, requirement understanding, clarification flow, product or service explanation, pricing handling, recommendation logic, callback handling, CRM extraction, conversational memory, escalation, follow up, wrap up, and outcome classification.

Detect product, pricing, service, support, booking, technical, enterprise, callback, and general enquiry intents.

Collect customer name, contact details, requirements, product interest, use case, preferences, budget indicators, timeline, and follow up interest.

Keep responses short and voice friendly. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive behavior, excessive use of special characters and "*".
""",
        "Outbound": """
Generate a production ready outbound enquiry AI voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, professional, conversational, helpful, and non pushy with one question at a time behavior.

Include not asking the same question,assistant identity, outbound greeting, permission based opening, enquiry intent detection, requirement discovery, clarification flow, product or service explanation, pricing discussion, recommendation logic, objection handling, callback handling, CRM extraction, conversational memory, follow up, wrap up, and outcome classification.

Detect product, pricing, service, support, booking, enterprise, callback, technical, and follow up enquiry intents.

Collect customer name, contact details, requirements, product interest, use case, preferences, budget indicators, timeline, and follow up interest.

Keep responses short and voice friendly. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive behavior, excessive use of special characters and "*".
"""
    },
    "Lead Generation": {
        "Inbound": """
Generate a production ready inbound lead generation AI voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, professional, conversational, consultative, and non pushy with one question at a time behavior.

Include not asking the same question,assistant identity, inbound greeting, lead qualification, interest discovery, pain point discovery, workflow understanding, product positioning, pricing discussion, objection handling, callback handling, CRM extraction, conversational memory, follow up, wrap up, and outcome classification.

Detect pricing, demo, enterprise, integration, callback, purchase, and qualification intents.

Collect customer name, company, role, industry, workflow, pain points, current tools, budget indicators, timeline, team size, contact details, and decision maker status.

Keep responses short and voice friendly. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive behavior, excessive use of special characters and "*".
""",
        "Outbound": """
Generate a production ready outbound lead generation AI voice agent instruction using only the provided Knowledge Base. The agent must sound human, concise, professional, conversational, consultative, and non pushy with one question at a time behavior.

Include not asking the same question,assistant identity, outbound greeting, permission based opening, lead qualification, interest discovery, pain point discovery, workflow understanding, product positioning, pricing discussion, objection handling, demo scheduling, callback handling, CRM extraction, conversational memory, follow up, wrap up, and outcome classification.

Detect pricing, demo, enterprise, integration, callback, purchase, follow up, and qualification intents.

Collect customer name, company, role, industry, workflow, pain points, current tools, budget indicators, timeline, team size, contact details, and decision maker status.

Keep responses short and voice friendly. Avoid hallucinations, robotic language, repeated questions, unsupported claims, aggressive behavior, excessive use of special characters and "*".
"""
    }
}

class AgentEngine:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

    async def evaluate_kb(self, input_kb: str) -> EvaluateResponse:
        # Step 1: Evaluate KB (Match EXACT logic from app.py)
        eval_prompt = f"""
You are an expert Data Cleaner and Content Auditor. Your task is to evaluate the following Input Knowledge Base.
Check for the following issues:
1. Formatting: Does it have excessive blank spaces, blank lines, or unwanted junk characters?
2. Relevancy & Coherence: Is the content coherent, logically structured, and highly relevant to its own stated topic? Does it contain off-topic garbage or noise?

Return your response strictly as a JSON object with two keys: 
"score" (a number from 0-100), 
"reasoning" (a brief string).

Input Knowledge Base:
{input_kb}

Do not use markdown blocks.
"""
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=eval_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        result_text = response.text.strip()
        eval_result = json.loads(result_text)
        score = eval_result.get("score", 0)
        reasoning = eval_result.get("reasoning", "")
        
        improved_kb = None
        if score < 75:
            reconstruct_prompt = f"""
You are an expert Knowledge Base Editor. The following Input Knowledge Base scored poorly on formatting, cleanliness, or coherence.
Your task is to clean up and restructure the text.
Fix the following issues without changing the core factual intent:
- Remove excessive blank spaces, blank lines, and junk characters.
- Remove unwanted, irrelevant, or noisy off-topic data.
- Ensure consistent, readable, and clean structuring.

Reasoning for poor score:
{reasoning}

Original Input Knowledge Base:
{input_kb}

Return ONLY the fully cleaned and formatted Knowledge Base without any markdown wrapping or additional conversational text.
"""
            reconstruct_resp = self.client.models.generate_content(
                model=self.model,
                contents=reconstruct_prompt
            )
            improved_kb = reconstruct_resp.text.strip()
            score = 100
            reasoning += " -> Reconstructed by AI to meet standards."

        return EvaluateResponse(score=score, reasoning=reasoning, improved_kb=improved_kb)

    async def generate_instructions(self, 
                                   input_kb: str, 
                                   instruction_type: str = "Sales", 
                                   call_direction: str = "Inbound",
                                   agent_name: str = "Aaliyah",
                                   company_name: str = "the company",
                                   extra_instructions: str = "") -> GenerateResponse:
        
        # Select template (Match EXACT logic from app.py)
        category_templates = INSTRUCTION_TEMPLATES.get(instruction_type, INSTRUCTION_TEMPLATES.get("Sales", {}))
        if isinstance(category_templates, dict):
            instruction_template = category_templates.get(call_direction, list(category_templates.values())[0] if category_templates else "")
        else:
            instruction_template = category_templates

        if extra_instructions:
            instruction_template += f"\n\n--- ADDITIONAL INSTRUCTIONS ---\n{extra_instructions}\n"

        # Step 2: Generate Instructions
        instr_prompt = f"""
You are an expert AI agent configuration generator. Based on the provided Input Knowledge Base, generate the final AI agent instructions using the provided Instruction Template.

The AI Agent's name MUST be: {agent_name}
The AI Agent represents the company: {company_name}

Instruction Template:
{instruction_template}

Input Knowledge Base:
{input_kb}

Return only the final generated instructions.
"""
        response = await self.client.aio.models.generate_content(model=self.model, contents=instr_prompt)
        initial_instructions = response.text.strip()

        # Step 3: Agent Instruction Auditor (Match EXACT logic from app.py)
        eval_instr_prompt = f"""
You are an AI auditor. Evaluate the following generated agent instructions against the Instruction Template.
Determine if the generated instructions perfectly follow the structure, tone, and requirements of the Instruction Template.
Return a relevance score from 0 to 100, where 100 means perfect match.
Provide a brief reasoning.

Instruction Template:
{instruction_template}

Generated Instructions:
{initial_instructions}

Output your response strictly as a JSON object with two keys: "score" (a number) and "reasoning" (a string).
"""
        audit_resp = await self.client.aio.models.generate_content(
            model=self.model, 
            contents=eval_instr_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        eval_result = json.loads(audit_resp.text)
        instr_score = eval_result.get("score", 0)
        instr_reasoning = eval_result.get("reasoning", "")
        
        final_instructions = initial_instructions
        was_refined = False
        
        if instr_score < 75:
            was_refined = True
            refine_prompt = f"""
You are an expert AI configuration refiner. The previously generated instructions were evaluated as not up to standard.
Rewrite them perfectly to match the Instruction Template.

Auditor Reasoning:
{instr_reasoning}

Instruction Template:
{instruction_template}

Original Flawed Instructions:
{initial_instructions}

Return ONLY the fully refined agent instructions.
"""
            refine_resp = await self.client.aio.models.generate_content(model=self.model, contents=refine_prompt)
            final_instructions = refine_resp.text.strip()

        return GenerateResponse(
            final_instructions=final_instructions,
            auditor_score=instr_score,
            auditor_reasoning=instr_reasoning,
            was_refined=was_refined
        )

    async def generate_qa(self, input_kb: str) -> QaResponse:
        # Step 4: Q&A Generator (Match EXACT logic from app.py)
        qa_prompt = f"""
You are an expert customer support analyst and "Red Team" tester for AI voice agents. 
Based on the following Knowledge Base, generate a list of at least 25 questions. 

Your goal is to create a rigorous test suite that includes:
1. **Trivial Questions**: Basic facts about the company, services, and contact info.
2. **Advanced/Complex Questions**: Questions requiring multi-step logic or combining multiple pieces of info from the KB.
3. **Edge Cases**: Specific, rare scenarios that a customer might ask about.
4. **Stumpers (Negative Testing)**: Questions about products, services, or policies that are NOT mentioned in the KB. 
   - For these, the "answer" should be how a good agent should respond (e.g., "I'm sorry, I don't have information on that, but I can check with my team").
   - Categorize these as "Negative Testing".
5. **Ambiguous Questions**: Questions that are slightly unclear, to see if the agent can clarify.
6. **Comparative Questions**: Comparing different offerings mentioned in the KB.

Input Knowledge Base:
{input_kb}

Output your response strictly as a JSON array of objects, where each object has the keys: "question", "answer", and "type_of_question". Do not use markdown blocks.
"""
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=qa_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        qa_list = json.loads(response.text)
        return QaResponse(qa_list=[QaItem(**item) for item in qa_list])
