import os
import json
from google import genai
from google.genai import types
from typing import Dict, Any

async def analyze_leads(kb_text: str) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment.")
        
    client = genai.Client(api_key=api_key)
    # Using gemini-2.5-flash as requested
    model_id = 'gemini-2.5-flash'
    
    prompt = f"""
    You are a Senior Strategic Analyst. Your job is to analyze the following website text top-to-bottom and extract structured company data.
    
    You MUST return ONLY valid JSON matching this exact structure. 
    DO NOT wrap the response in any other keys like "core", "data", or "response".
    If a field is missing, use "N/A" for strings or an empty list [] for arrays.
    
    Structure:
    {{
      "company_profile": {{
        "company_name": "string",
        "website": "string",
        "short_summary": "string",
        "industry": ["string"],
        "business_type": "string",
        "target_customers": ["string"],
        "location": "string",
        "team_size": "string or null"
      }},
      "pain_points": {{
        "customer_pain_points": ["string"],
        "operational_pain_points": ["string"],
        "main_manual_workflows": ["string"],
        "communication_heavy_processes": ["string"],
        "support_burden_signals": "string or null",
        "lead_response_pain": "string or null"
      }},
      "ai_voice_agent_fit": {{
        "product_name": "Dakini AI Voice Agents",
        "fit_score": number (0-100),
        "fit_level": "Low | Medium | High",
        "fit_reason": "string",
        "problems_we_can_solve": ["string"],
        "recommended_use_cases": ["string"],
        "expected_benefits": ["string"],
        "risks_or_limitations": ["string"]
      }}
    }}
    
    Knowledge Base Text (first 60,000 characters):
    {kb_text[:60000]}
    """
    
    try:
        response = await client.aio.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        text = response.text.strip()
        
        # Clean potential markdown wrappers
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        return json.loads(text)
    except Exception as e:
        print(f"Error in analyze_leads: {str(e)}")
        return {
            "company_profile": {
                "company_name": "Error",
                "website": "Error",
                "short_summary": f"Analysis failed: {str(e)}",
                "industry": [],
                "business_type": "Unknown",
                "target_customers": [],
                "location": "Unknown",
                "team_size": None
            },
            "pain_points": {
                "customer_pain_points": [],
                "operational_pain_points": [],
                "main_manual_workflows": [],
                "communication_heavy_processes": [],
                "support_burden_signals": None,
                "lead_response_pain": None
            },
            "ai_voice_agent_fit": {
                "product_name": "Dakini AI Voice Agents",
                "fit_score": 0,
                "fit_level": "Low",
                "fit_reason": "Analysis error",
                "problems_we_can_solve": [],
                "recommended_use_cases": [],
                "expected_benefits": [],
                "risks_or_limitations": []
            }
        }
