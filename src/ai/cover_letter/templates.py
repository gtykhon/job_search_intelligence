"""
Cover Letter Templates -- Canonical structure, forbidden phrases, and auth template.

Canonical 4-paragraph structure:
  P1: Company challenge + mission alignment
  P2: Solution + methodology (specific achievement)
  P3: Human dynamics / narrative (collaboration, leadership)
  P4: Mission-aligned closing + call to action
"""

# ---------- Forbidden phrases ----------
# These must never appear in any cover letter output.
FORBIDDEN_PHRASES = [
    "i am writing to express my interest",
    "i am excited to apply",
    "i believe i would be a great fit",
    "i am confident that",
    "please find attached",
    "to whom it may concern",
    "i am a team player",
    "i think outside the box",
    "i am a self-starter",
    "i have a proven track record",
    "i am reaching out regarding",
    "i was thrilled to see",
    "as you can see from my resume",
    "i look forward to hearing from you",
    "thank you for your time and consideration",
    "please do not hesitate to contact me",
    "i am a hard worker",
    "i am passionate about",
    "dear sir or madam",
    "dear hiring manager",
    "synergy",
    "leverage my skills",
    "utilize my expertise",
    "hit the ground running",
    "go-getter",
    "results-driven professional",
    "dynamic individual",
]

# ---------- Addressee rules ----------
ADDRESSEE_RULES = """
- If hiring manager name is known: "Dear [First] [Last],"
- If hiring manager name is unknown: "Dear [Company] [Department] Team,"
- Never use "Dear Sir or Madam" or "To Whom It May Concern"
- Never use "Dear Hiring Manager" -- it signals zero research effort
"""

# ---------- Canonical structure ----------
CANONICAL_STRUCTURE = """
## Paragraph 1 -- Company Challenge + Mission
Open with a specific company challenge, recent initiative, or mission element that
resonates with you. Demonstrate you researched the company. Connect to why this
role matters to you personally. Do NOT open with "I am writing to apply."

## Paragraph 2 -- Solution + Methodology
Present your most relevant achievement with a specific metric. Explain the
methodology or approach, not just the result. Show how this directly maps to
what the role requires. Use ONE concrete example, not a laundry list.

## Paragraph 3 -- Human Dynamics / Narrative
Share a collaboration story, leadership moment, or stakeholder management win.
Show how you work with people, not just technology. This differentiates you from
other technically qualified candidates. Keep it concise and specific.

## Paragraph 4 -- Mission-Aligned Closing
Connect your career trajectory to the company's direction. Include a specific
next step or conversation starter (not "I look forward to hearing from you").
End with confidence, not desperation.
"""

# ---------- Auth summary template ----------
AUTH_SUMMARY_TEMPLATE = """
AUTHENTICATION SUMMARY -- Claims Check
Before generating the cover letter, verify each claim against the resume:
{claims_list}

Rules:
- Every metric cited in the cover letter MUST appear in the resume
- Every company/role referenced MUST appear in the resume
- Skill claims must be grounded in documented experience
- Do NOT fabricate achievements, timelines, or responsibilities
"""

# ---------- Role-specific tone guidance ----------
ROLE_TONE_GUIDANCE = {
    "engineering": {
        "tone": "Technical but human. Lead with systems thinking and measurable impact.",
        "p2_focus": "Technical achievement with architecture/methodology detail",
        "p3_focus": "Cross-functional collaboration, mentorship, or incident response",
    },
    "analyst": {
        "tone": "Analytical and insight-driven. Lead with data storytelling.",
        "p2_focus": "Data-driven decision with business impact metric",
        "p3_focus": "Stakeholder communication, translating data for non-technical audiences",
    },
    "bsa": {
        "tone": "Bridge-builder. Lead with requirements translation and process improvement.",
        "p2_focus": "Requirements gathering win with stakeholder alignment",
        "p3_focus": "Mediating between technical and business teams",
    },
    "leadership": {
        "tone": "Strategic and people-focused. Lead with organizational impact.",
        "p2_focus": "Team or organizational transformation with measurable outcome",
        "p3_focus": "Culture building, talent development, or strategic decision",
    },
}

# ---------- Generation prompt ----------
GENERATION_PROMPT = """
You are writing a cover letter for {user_name} applying to {job_title} at {company}.

ROLE CLASSIFICATION: {role_type}
TONE GUIDANCE: {tone_guidance}

ADDRESSEE: {addressee}

COMPANY CONTEXT / CONNECTION POINTS:
{connection_points}

JOB DESCRIPTION:
{job_description}

RESUME (for authentication -- every claim must trace back here):
{resume_text}

{auth_summary}

STRUCTURE -- Follow this exactly (4 paragraphs):
{canonical_structure}

PARAGRAPH 2 FOCUS: {p2_focus}
PARAGRAPH 3 FOCUS: {p3_focus}

CONSTRAINTS:
- Word count: 280-420 words
- Exactly 4 paragraphs
- Company name must appear in the body (not just the addressee)
- No phrases from this forbidden list: {forbidden_sample}
- Do NOT repeat any metric or >5-word phrase that appears in the resume verbatim
- Include at least one specific achievement with a number/metric
- Do NOT use generic filler -- every sentence must carry information

Write the cover letter now. Output ONLY the letter text, no commentary.
"""
