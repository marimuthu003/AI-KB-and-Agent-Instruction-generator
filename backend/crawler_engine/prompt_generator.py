import os
from google import genai
from google.genai import types

PROMPT_TEMPLATE = """
ROLE
You are a Senior Knowledge-Base Architect and Data Extraction Specialist. Your objective is a 100% high-fidelity reconstruction of a company’s digital footprint based strictly on the provided scraped text. Prioritize granular data such as pricing, individual names, workflows, policies, trust signals, and platform details over high-level summaries.

{business_model_focus}
{agent_role_focus}

IMPORTANT RULES
- Use only the information present in the provided knowledge base text.
- Do not use external knowledge, assumptions, or prior training data.
- Do not invent, infer, or guess any missing detail.
- If a data point is missing, write exactly: "Not available in scraped data."
- Preserve the exact wording of vague claims when possible.
- Do not expand broad statements into specific names, numbers, or claims unless they are explicitly stated.
- Only create hyperlinks when the URL is explicitly present in the knowledge base text.
- If no URL is provided for an item, mention the item without a hyperlink.
- Do not add commentary before or after the required output.
- Do not add any sections beyond the ones listed below.
- Use plain Markdown only.

EXTRACTION PROTOCOLS
1. Entity Mining
- Identify every human name mentioned in the text, including founders, leaders, mentors, advisors, and team members.
- Extract credentials, alma maters, job titles, roles, company names, and location details exactly as written.
- If a name or credential is not present, write "Not available in scraped data."

2. Financial Reconnaissance
- Extract every currency value and pricing detail.
- Capture base prices, discounts, strike-through prices, per-session rates, monthly plans, free tiers, trials, hidden fees, refunds, and guarantees.
- If multiple pricing formats exist, preserve each one separately.
- Note whether pricing is one-time, per-session, monthly, annual, or free.
- Do not normalize or convert currencies.

3. Operational Logic
- If the service has a workflow or cycle, map it step by step.
- Include daily, weekly, monthly, onboarding, support, booking, rescheduling, refund, cancellation, and escalation logic.
- Preserve the sequence of events exactly as stated.
- If a workflow is described indirectly, reconstruct it only from explicit statements.

4. Trust & Social Proof
- Extract exact counts, ratings, review values, student counts, mentor counts, years of experience, guarantees, and timelines.
- Include any testimonial-based claims only if they are explicitly stated in the scraped text.
- Do not treat marketing language as verified fact unless the text presents it as a claim.

5. Technical Anatomy
- List every software, app, platform, channel, integration, or device mentioned.
- Include web, iOS, Android, WhatsApp, email, Zoom, payment tools, CRM tools, analytics tools, and social platforms if mentioned.
- If a technology is implied but not named, do not guess the product name.

6. Website Structure
- Capture every navigation link, footer link, page name, and page URL available in the text.
- Do not fabricate pages or URLs.
- If a page is mentioned without a URL, write "Not available in scraped data."

OUTPUT STRUCTURE
You must output a single Markdown document using exactly the sections below, in this exact order, separated by:
========================================================

1. COMPANY OVERVIEW
Include the legal or public company name, physical HQ address, location, and the specific problem the company solves.

2. COMPANY MISSION
Include exact taglines, brand promises, and the specific target demographic.

3. FOUNDERS & LEADERSHIP
Include all founders, leaders, mentors, and key team members mentioned. Add titles, alma maters, and professional backgrounds if present.

4. MATERIALS / TECHNOLOGY
Include the tech stack, delivery channels, mobile app links, support channels, and any software or tools mentioned.

5. PRODUCT / SERVICE CATEGORIES
List the full menu of offerings, grouped by category.

6. PRODUCT / SERVICE KNOWLEDGE BASE
Provide a detailed breakdown of every product or service feature, including any "How it works" sections, workflows, and usage steps.

7. COMMON PRODUCT / SERVICE CHARACTERISTICS
Include refund policies, cancellations, confidentiality, mentor-switching rules, guarantees, service limitations, and support expectations.

8. SMART TECHNOLOGY FEATURES
Include analytics, algorithms, personalization logic, weak-area targeting, filtering systems, quizzes, and interactive tools.

9. ENVIRONMENTAL IMPACT
State whether the company is digital-only or has any direct physical footprint. If unavailable, say so.

10. SOCIAL IMPACT
Focus on democratization, access, education, mentorship, affordability, and community impact.

11. WEBSITE STRUCTURE
List all navigational links and their URLs in Markdown link format.

12. BRAND POSITIONING
Include messaging themes such as real talk, student-first, Indian context, anti-corporate, affordability, trust, and transparency.

13. RECOGNITIONS AND ASSOCIATIONS
Include total students served, ratings, mentor counts, partnerships, affiliations, certifications, awards, and any social proof.

14. PRODUCT / SERVICE PRICE SUMMARY
Provide a comprehensive Markdown table or bullet list of all prices, fees, discounts, free tiers, and guarantees.

15. KEYWORDS FOR RAG / VECTOR DATABASE
Provide 50+ highly relevant keywords, phrases, and intent-based search terms for retrieval.

16. SHORT COMPANY SUMMARY
Write a strong three-sentence executive summary of the company.

FORMATTING RULES
- Use exact section headings as written above.
- Separate each section with the line:
  ========================================================
- Use bold for key names and prices.
- Use Markdown links for every item that has an explicit URL in the scraped text.
- If a field is missing, write "Not available in scraped data."
- Keep the tone precise, structured, and culturally aligned with the company’s context.
- Do not mention internal reasoning or analysis.
- Do not include any content outside these sections.

INPUT
Knowledge Base Text to analyze:
```kb
{kb_text}
```
"""

BUSINESS_MODEL_INSTRUCTIONS = {
    "B2B": """
BUSINESS MODEL FOCUS: B2B (Business to Business)
- Prioritize decision-maker roles, target departments, and procurement cycles.
- Identify enterprise data: SLAs, security certifications, and integration capabilities.
- Capture case studies and multi-seat licensing details.
""",
    "B2C": """
BUSINESS MODEL FOCUS: B2C (Business to Consumer)
- Prioritize consumer pain points, emotional triggers, and user-centric benefits.
- Extract shipping timelines, return windows, and warranty details.
- Capture loyalty programs and community engagement signals.
""",
    "Mixed": """
BUSINESS MODEL FOCUS: Mixed (B2B & B2C)
- Balance extraction between enterprise requirements and consumer-facing features.
- Identify distinct pathways for corporate clients vs. individual customers.
""",
    "General": ""
}

AGENT_ROLE_INSTRUCTIONS = {
    "Sales": """
AI AGENT ROLE: Sales & Conversion
- Prioritize the Unique Selling Proposition (USP) and "Why Choose Us" arguments.
- Identify scarcity/urgency triggers and objection-handling content.
- Detail the exact step-by-step path to purchase/checkout.
""",
    "Support": """
AI AGENT ROLE: Support & FAQ
- Prioritize troubleshooting steps, common technical issues, and documentation.
- Extract all contact channels, support hours, and escalation paths.
- Detail "How-to" guides and feature limitations.
""",
    "Hiring": """
AI AGENT ROLE: Hiring & Recruitment
- Prioritize job roles, departments, locations, and candidate requirements.
- Detail the employee value proposition (culture, perks, benefits).
- Map the recruitment process from application to onboarding.
""",
    "Enquiry": """
AI AGENT ROLE: Enquiry & Lead Generation
- Prioritize all lead capture methods: forms, chatbots, phone, and WhatsApp.
- Extract typical response times and consultation booking steps.
- Capture qualification questions and criteria.
""",
    "General": """
AI AGENT ROLE: General Assistant
- Provide a balanced extraction of all product, service, and company data.
"""
}

async def generate_voice_agent_prompt(kb_text: str, business_model: str = "General", agent_role: str = "General") -> str:
    """
    Takes the raw markdown extracted from crawling and passes it to Gemini
    to synthesize into a structured knowledge base document, tailored to the business model and agent role.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables."
        
    client = genai.Client(api_key=api_key)
    model_id = 'gemini-2.5-flash'
    
    # Get specific instructions
    model_instructions = BUSINESS_MODEL_INSTRUCTIONS.get(business_model, "")
    role_instructions = AGENT_ROLE_INSTRUCTIONS.get(agent_role, AGENT_ROLE_INSTRUCTIONS["General"])
    
    # Truncate text if needed
    safe_kb_text = kb_text[:60000]
    
    prompt = (PROMPT_TEMPLATE.replace("{kb_text}", safe_kb_text)
                             .replace("{business_model_focus}", model_instructions)
                             .replace("{agent_role_focus}", role_instructions))
    
    try:
        response = await client.aio.models.generate_content(
            model=model_id,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error generating knowledge base structure: {str(e)}"
