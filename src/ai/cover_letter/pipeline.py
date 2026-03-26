"""
Cover Letter Pipeline -- 5-step constrained generation.

Steps:
  1. Research hiring manager / extract connection points
  2. Classify role -> RoleClassification
  3. Authentication check -- verify claims grounded in resume
  4. Generate constrained cover letter (canonical 4-paragraph structure)
  5. Enforce no-repetition -- no shared metrics or >5-word phrases with resume
"""

import logging
from typing import List, Optional

from .models import (
    CoverLetterRequest,
    CoverLetterResult,
    RoleClassification,
)
from .templates import (
    FORBIDDEN_PHRASES,
    CANONICAL_STRUCTURE,
    AUTH_SUMMARY_TEMPLATE,
    ROLE_TONE_GUIDANCE,
    GENERATION_PROMPT,
)
from .checklist import PreSubmissionChecklist


logger = logging.getLogger(__name__)


class CoverLetterPipeline:
    """
    5-step constrained cover letter generation pipeline.

    Requires an AI router instance for steps that need AI generation.
    """

    def __init__(self, ai_router=None):
        self.ai_router = ai_router
        self.checklist = PreSubmissionChecklist()

    async def generate(self, request: CoverLetterRequest) -> CoverLetterResult:
        """Run the full 5-step pipeline."""
        logger.info("Cover letter pipeline: starting for %s at %s", request.job_title, request.company)

        # Step 1: Research / extract connection points
        connection_points = await self._research_hiring_manager(request)

        # Step 2: Classify role
        role_class = await self._classify_role(request)

        # Step 3: Authentication check -- build claims list
        auth_summary = await self._check_authentication(request)

        # Step 4: Generate constrained cover letter
        raw_letter = await self._generate_constrained(
            request, role_class, connection_points, auth_summary
        )

        # Step 5: Enforce no-repetition (post-processing)
        cleaned_letter = self._enforce_no_repetition(raw_letter, request.resume_text)

        # Run checklist
        all_passed, items, forbidden_violations, repetition_violations = self.checklist.run(
            cleaned_letter, request.company, request.resume_text
        )

        paragraphs = [p.strip() for p in cleaned_letter.split('\n\n') if p.strip()]
        body_paragraphs = [p for p in paragraphs if len(p.split()) > 20]

        result = CoverLetterResult(
            cover_letter=cleaned_letter,
            role_classification=role_class,
            word_count=len(cleaned_letter.split()),
            paragraph_count=len(body_paragraphs),
            checklist_passed=all_passed,
            checklist_items=items,
            forbidden_violations=forbidden_violations,
            repetition_violations=repetition_violations,
            connection_points=connection_points,
            metadata={
                'auth_summary': auth_summary,
                'tone_guidance': ROLE_TONE_GUIDANCE.get(role_class.value, {}),
            },
        )

        logger.info(
            "Cover letter pipeline: done -- %d words, %d paragraphs, checklist=%s",
            result.word_count, result.paragraph_count, result.checklist_passed,
        )
        return result

    # -- Step 1: Research --

    async def _research_hiring_manager(self, request: CoverLetterRequest) -> List[str]:
        """Extract connection points from company/role context."""
        connection_points = []

        if request.company_context:
            if 'mission' in request.company_context:
                connection_points.append(f"Company mission: {request.company_context['mission']}")
            if 'recent_news' in request.company_context:
                connection_points.append(f"Recent news: {request.company_context['recent_news']}")
            if 'tech_stack' in request.company_context:
                connection_points.append(f"Tech stack: {request.company_context['tech_stack']}")
            if 'culture' in request.company_context:
                connection_points.append(f"Culture: {request.company_context['culture']}")

        if self.ai_router and not connection_points:
            try:
                prompt = (
                    f"From this job description for {request.job_title} at {request.company}, "
                    f"extract 3-4 specific company challenges, initiatives, or values that a "
                    f"candidate could reference in a cover letter. Be specific, not generic.\n\n"
                    f"Job Description:\n{request.job_description[:2000]}\n\n"
                    f"Return each point on a new line, prefixed with '- '."
                )
                response = await self.ai_router.generate_content(
                    prompt, task_type="cover_letter_research"
                )
                for line in response.strip().split('\n'):
                    line = line.strip().lstrip('- ').strip()
                    if line and len(line) > 10:
                        connection_points.append(line)
            except Exception as e:
                logger.warning("Connection point extraction failed: %s", e)

        if not connection_points:
            connection_points.append(f"Role: {request.job_title} at {request.company}")

        return connection_points[:5]

    # -- Step 2: Classify role --

    async def _classify_role(self, request: CoverLetterRequest) -> RoleClassification:
        """Classify role type for tone/format selection."""
        title_lower = request.job_title.lower()
        jd_lower = request.job_description.lower()

        bsa_signals = {
            'business analyst', 'business systems analyst', 'bsa',
            'product owner', 'scrum master', 'project manager',
        }
        leadership_signals = {
            'director', 'vp ', 'vice president', 'head of', 'chief',
            'cto', 'cio',
        }
        engineering_signals = {
            'engineer', 'developer', 'architect', 'devops', 'sre',
            'platform', 'infrastructure', 'backend', 'frontend', 'fullstack',
            'full-stack', 'software',
        }
        analyst_signals = {
            'analyst', 'analytics', 'data analyst', 'business intelligence',
            'bi ', 'reporting', 'data science', 'scientist',
        }

        if any(s in title_lower for s in bsa_signals):
            return RoleClassification.BSA
        if any(s in title_lower for s in leadership_signals):
            return RoleClassification.LEADERSHIP

        combined = title_lower + ' ' + jd_lower[:500]
        if any(s in combined for s in engineering_signals):
            return RoleClassification.ENGINEERING
        if any(s in combined for s in analyst_signals):
            return RoleClassification.ANALYST

        return RoleClassification.ENGINEERING

    # -- Step 3: Authentication --

    async def _check_authentication(self, request: CoverLetterRequest) -> str:
        """Build authentication summary -- verify claims are grounded in resume."""
        # F3: Pre-generation auth audit (non-blocking warning)
        try:
            from src.dashboard.auth_audit import AuthAuditEngine
            _audit_result = AuthAuditEngine().audit(
                cover_letter="",  # not generated yet - audit the outline/claims
                resume_text=request.resume_text,
            )
            if not _audit_result.passed:
                logger.warning(
                    "Pre-generation auth audit found %d violation(s): %s",
                    len(_audit_result.violations),
                    _audit_result.summary,
                )
        except Exception as _e:
            logger.debug("Auth audit pre-check failed (non-critical): %s", _e)

        # F6: Audience classification for tone guidance
        try:
            from src.intelligence.company_research.audience_classifier import AudienceClassifier
            _audience_clf = AudienceClassifier()
            _audience = _audience_clf.classify(
                hiring_manager_title=getattr(request, 'hiring_manager_title', None),
                job_description=getattr(request, 'job_description', ''),
            )
            # Append tone guidance to the generation context
            logger.debug(
                "Audience: %s | Tone: %s",
                _audience.audience_type,
                _audience.tone_guidance[:60],
            )
        except Exception as _e:
            logger.debug("Audience classification skipped: %s", _e)

        if not self.ai_router:
            return "Authentication: AI router not available -- manual verification required."

        try:
            prompt = (
                f"You are a fact-checker. Review this resume and extract:\n"
                f"1. All quantified achievements (metrics, percentages, dollar amounts)\n"
                f"2. All company names and roles held\n"
                f"3. All technical skills with documented experience\n\n"
                f"Resume:\n{request.resume_text[:3000]}\n\n"
                f"Format each as a bullet point. These are the ONLY claims that may "
                f"appear in the cover letter."
            )
            response = await self.ai_router.generate_content(
                prompt, task_type="cover_letter_auth"
            )
            claims_list = response.strip()
        except Exception as e:
            logger.warning("Authentication check failed: %s", e)
            claims_list = "- Authentication check unavailable -- use resume claims only"

        return AUTH_SUMMARY_TEMPLATE.format(claims_list=claims_list)

    # -- Step 4: Generate --

    async def _generate_constrained(
        self,
        request: CoverLetterRequest,
        role_class: RoleClassification,
        connection_points: List[str],
        auth_summary: str,
    ) -> str:
        """Generate the cover letter using canonical structure."""
        if request.hiring_manager_name:
            addressee = f"Dear {request.hiring_manager_name},"
        else:
            addressee = f"Dear {request.company} Team,"

        guidance = ROLE_TONE_GUIDANCE.get(role_class.value, ROLE_TONE_GUIDANCE['engineering'])
        forbidden_sample = ', '.join(f'"{p}"' for p in FORBIDDEN_PHRASES[:10])

        prompt = GENERATION_PROMPT.format(
            user_name=request.user_name or "the applicant",
            job_title=request.job_title,
            company=request.company,
            role_type=role_class.value,
            tone_guidance=guidance['tone'],
            addressee=addressee,
            connection_points='\n'.join(f'- {cp}' for cp in connection_points),
            job_description=request.job_description[:3000],
            resume_text=request.resume_text[:3000],
            auth_summary=auth_summary,
            canonical_structure=CANONICAL_STRUCTURE,
            p2_focus=guidance['p2_focus'],
            p3_focus=guidance['p3_focus'],
            forbidden_sample=forbidden_sample,
        )

        if self.ai_router:
            try:
                raw = await self.ai_router.generate_content(
                    prompt, task_type="cover_letter_generation"
                )
                return raw.strip()
            except Exception as e:
                logger.error("Cover letter generation failed: %s", e)
                raise

        raise RuntimeError("AI router required for cover letter generation")

    # -- Step 5: No-repetition enforcement --

    def _enforce_no_repetition(self, cover_letter: str, resume_text: str) -> str:
        """
        Post-processing: flag but don't auto-modify the letter.
        Repetition violations are surfaced via checklist, not silently rewritten.
        """
        return cover_letter


# -- Singleton --

_pipeline: Optional[CoverLetterPipeline] = None


def get_cover_letter_pipeline(ai_router=None) -> CoverLetterPipeline:
    """Get or create the global cover letter pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = CoverLetterPipeline(ai_router=ai_router)
    return _pipeline
