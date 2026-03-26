"""
Semantic Alignment Scorer — sentence-transformer cosine similarity.

Computes semantic similarity between the candidate's resume and a job
description using sentence-transformers (all-MiniLM-L6-v2, ~80MB).

Design:
  - Optional dependency: gracefully returns None when library absent
  - Resume embedding is cached — recomputed only when resume text changes
  - JD embeddings are computed on-demand (not cached — memory concern at scale)
  - Model loaded lazily on first call — ~300ms cold start, negligible warm

Usage:
    scorer = SemanticAlignmentScorer(resume_text="...")
    if scorer.is_available():
        score = scorer.score("Python data engineer role at Stripe...")
        print(score.score_0_100)   # e.g. 72.4

Score interpretation:
  >= 70  Strong semantic alignment
  50–70  Moderate alignment
  < 50   Weak semantic alignment (different domain/role)
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"

# Maximum JD characters to encode — stays within 512-token limit of MiniLM
_JD_CHAR_LIMIT = 2_000


# ── Availability check (module level, checked once) ─────────────────────
_ST_AVAILABLE: Optional[bool] = None


def _check_sentence_transformers() -> bool:
    global _ST_AVAILABLE
    if _ST_AVAILABLE is None:
        try:
            import sentence_transformers  # noqa: F401
            _ST_AVAILABLE = True
            logger.debug("sentence-transformers available — semantic scoring enabled")
        except ImportError:
            _ST_AVAILABLE = False
            logger.debug(
                "sentence-transformers not installed — semantic scoring disabled. "
                "Install: pip install sentence-transformers"
            )
    return _ST_AVAILABLE


# ── Result dataclass ────────────────────────────────────────────────────
@dataclass
class SemanticScore:
    cosine_similarity: float   # raw cosine: 0.0 – 1.0
    score_0_100: float         # cosine * 100, 1 decimal
    model_name: str
    from_cache: bool = False


# ── Main scorer class ───────────────────────────────────────────────────
class SemanticAlignmentScorer:
    """
    Sentence-transformer semantic similarity scorer.

    Attributes:
        resume_text:     Candidate's resume/profile text
        _model:          SentenceTransformer instance (lazy-loaded)
        _resume_emb:     Cached numpy embedding of resume text
    """

    def __init__(self, resume_text: str = ""):
        self._resume_text = resume_text
        self._model = None
        self._resume_emb = None     # numpy array or None
        self._model_loaded = False

    # ── Availability ─────────────────────────────────────────────────
    def is_available(self) -> bool:
        """Check if sentence-transformers is importable."""
        return _check_sentence_transformers()

    # ── Model lazy-load ──────────────────────────────────────────────
    def _load_model(self) -> bool:
        if self._model_loaded:
            return self._model is not None
        self._model_loaded = True

        if not self.is_available():
            return False

        try:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415
            self._model = SentenceTransformer(MODEL_NAME)
            logger.debug("Loaded sentence-transformer: %s", MODEL_NAME)
            return True
        except Exception as e:
            logger.warning("Failed to load sentence-transformer %s: %s", MODEL_NAME, e)
            return False

    # ── Resume management ────────────────────────────────────────────
    def set_resume(self, resume_text: str) -> None:
        """Update resume text and invalidate cached embedding."""
        if resume_text != self._resume_text:
            self._resume_text = resume_text
            self._resume_emb = None

    def _get_resume_embedding(self):
        """Return (possibly cached) resume embedding. None if unable."""
        if not self._resume_text:
            return None
        if self._resume_emb is not None:
            return self._resume_emb
        if not self._load_model():
            return None
        try:
            self._resume_emb = self._model.encode(
                self._resume_text[:4_000],   # cap resume at 4k chars
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return self._resume_emb
        except Exception as e:
            logger.warning("Failed to encode resume: %s", e)
            return None

    # ── Scoring ──────────────────────────────────────────────────────
    def score(self, jd_text: str, jd_title: str = "") -> Optional[SemanticScore]:
        """
        Compute cosine similarity between resume and job description.

        Returns None if:
          - sentence-transformers not available
          - resume_text is empty
          - any encoding error

        The JD is encoded as:  "<title>\\n\\n<description_truncated>"
        Title is prepended to bias the embedding toward role-level matching.
        """
        if not self.is_available():
            return None

        resume_emb = self._get_resume_embedding()
        if resume_emb is None:
            return None

        if not self._load_model():
            return None

        try:
            # Compose JD text with title prefix for role-level signal
            jd_combined = f"{jd_title}\n\n{jd_text[:_JD_CHAR_LIMIT]}" if jd_title else jd_text[:_JD_CHAR_LIMIT]

            jd_emb = self._model.encode(
                jd_combined,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            # Cosine similarity (both embeddings are unit vectors after normalise)
            import numpy as np
            cosine = float(np.dot(resume_emb, jd_emb))
            cosine = max(0.0, min(1.0, cosine))  # clamp to [0, 1]

            return SemanticScore(
                cosine_similarity=cosine,
                score_0_100=round(cosine * 100, 1),
                model_name=MODEL_NAME,
            )
        except Exception as e:
            logger.warning("Semantic scoring failed: %s", e)
            return None

    # ── Batch scoring ────────────────────────────────────────────────
    def score_batch(self, jd_texts: list, jd_titles: list = None) -> list:
        """
        Score multiple JDs in a single encode call (much faster for bulk).
        Returns list of SemanticScore (or None per entry on failure).
        """
        if not self.is_available() or not self._load_model():
            return [None] * len(jd_texts)

        resume_emb = self._get_resume_embedding()
        if resume_emb is None:
            return [None] * len(jd_texts)

        if jd_titles is None:
            jd_titles = [""] * len(jd_texts)

        try:
            combined = [
                f"{t}\n\n{d[:_JD_CHAR_LIMIT]}" if t else d[:_JD_CHAR_LIMIT]
                for t, d in zip(jd_titles, jd_texts)
            ]
            embeddings = self._model.encode(
                combined,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=32,
            )
            import numpy as np
            scores = []
            for emb in embeddings:
                cosine = float(np.dot(resume_emb, emb))
                cosine = max(0.0, min(1.0, cosine))
                scores.append(SemanticScore(
                    cosine_similarity=cosine,
                    score_0_100=round(cosine * 100, 1),
                    model_name=MODEL_NAME,
                ))
            return scores
        except Exception as e:
            logger.warning("Batch semantic scoring failed: %s", e)
            return [None] * len(jd_texts)


# ── Module-level singleton ──────────────────────────────────────────────
_scorer: Optional[SemanticAlignmentScorer] = None


def get_semantic_scorer(resume_text: str = "") -> SemanticAlignmentScorer:
    """
    Return the module-level shared SemanticAlignmentScorer.
    Updates resume if a new value is provided.
    """
    global _scorer
    if _scorer is None:
        _scorer = SemanticAlignmentScorer(resume_text=resume_text)
    elif resume_text and resume_text != _scorer._resume_text:
        _scorer.set_resume(resume_text)
    return _scorer
