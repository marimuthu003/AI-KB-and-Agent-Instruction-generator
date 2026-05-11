# AI Knowledge Base Extraction Templates

This document summarizes the specialized extraction protocols and focus areas used to synthesize high-fidelity Knowledge Bases (KBs) for various business contexts and AI agent roles.

---

## 🏢 Business Model Focus
The Business Model focus determines the **Strategic Entities** and **Operational Logic** the AI prioritizes during extraction.

### 1. B2B (Business to Business)
*   **Protocol**: Focus on enterprise-grade data and complex decision-making cycles.
*   **Key Data Points**:
    *   Decision-maker roles and target departments.
    *   SLA (Service Level Agreement) details and security certifications.
    *   Integration capabilities and technical requirements.
    *   Case studies, whitepapers, and corporate partnership mentions.
    *   Procurement workflows and multi-seat licensing models.

### 2. B2C (Business to Consumer)
*   **Protocol**: Focus on consumer pain points, emotional triggers, and rapid conversion.
*   **Key Data Points**:
    *   Customer pain points and immediate benefits.
    *   Shipping timelines, delivery methods, and tracking.
    *   Return/Refund windows and warranty policies.
    *   Loyalty programs, referral bonuses, and community engagement.
    *   Social proof: User reviews, ratings, and celebrity endorsements.

### 3. Mixed (B2B & B2C)
*   **Protocol**: Identify distinct pathways for different customer segments.
*   **Key Data Points**:
    *   Differentiated pricing for individual vs. corporate clients.
    *   Support channels tailored by account type.
    *   Balance between enterprise-scale features and consumer-facing simplicity.

### 4. General (Default)
*   **Protocol**: Comprehensive extraction of all factual data without specific industry bias.

---

## 🤖 AI Agent Role Focus
The AI Agent Role determines the **Actionable Knowledge** the agent requires to handle user interactions effectively.

### 1. Sales & Conversion
*   **Protocol**: Identify triggers that drive high-intent actions and purchase decisions.
*   **Key Data Points**:
    *   Unique Selling Propositions (USPs) and "Why Choose Us" arguments.
    *   Scarcity/Urgency triggers: Limited-time offers, stock alerts, or countdowns.
    *   Objection handling: Detailed answers to common purchase hesitations.
    *   The exact step-by-step path to purchase or checkout.

### 2. Support & FAQ
*   **Protocol**: Prioritize troubleshooting, technical resolution, and product limitations.
*   **Key Data Points**:
    *   Step-by-step troubleshooting guides for common issues.
    *   Contact channels, support hours, and escalation procedures.
    *   Product limitations, compatibility, and versioning info.
    *   "How-to" documentation and feature walkthroughs.

### 3. Hiring & Recruitment
*   **Protocol**: Focus on employer branding and the candidate experience.
*   **Key Data Points**:
    *   Detailed job roles, departments, and office locations.
    *   Candidate requirements: Skills, years of experience, and cultural fit.
    *   Employee value proposition: Benefits, insurance, perks, and growth paths.
    *   Recruitment workflow: Application -> Screening -> Interviews -> Onboarding.

### 4. Enquiry & Lead Generation
*   **Protocol**: Capture all methods of engagement and response expectations.
*   **Key Data Points**:
    *   Mapping all contact methods (forms, WhatsApp, chatbots, phone).
    *   Typical response times and lead qualification criteria.
    *   Consultation or demo booking steps.
    *   Pricing tiers or "Request a Quote" workflows.

### 5. General Assistant
*   **Protocol**: A holistic extraction of product, service, and organizational knowledge for general-purpose interaction.

---

## 🛠️ How it Works (Workflow)

1.  **Selection**: The user selects a **Business Model** and an **Agent Role** in the UI.
2.  **API Call**: The frontend sends these selections as parameters in the JSON payload to the `/api/crawl-site` endpoint.
3.  **Prompt Synthesis**: The `prompt_generator.py` module replaces the `{business_model_focus}` and `{agent_role_focus}` placeholders in the master `PROMPT_TEMPLATE` with the specific instructions listed above.
4.  **AI Extraction**: The `gemini-2.5-flash` model receives the crawled text along with these focused protocols, ensuring it prioritizes "Actionable Knowledge" over "Marketing Fluff."
5.  **Output**: The result is a structured Markdown document that serves as a high-fidelity Knowledge Base for the specific agent type.
