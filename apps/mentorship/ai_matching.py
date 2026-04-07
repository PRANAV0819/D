"""
AI Mentor Matching — Gemini Embeddings
======================================
Converts user skills into dense vector embeddings via the Google Gemini API,
stores them on the user's Profile, and ranks alumni mentors by cosine similarity.

Environment variable required:
    GEMINI_API_KEY  — Your Google AI Studio API key
    (get one free at https://aistudio.google.com/app/apikey)
"""

import os
import math
import logging
import threading
from django.utils import timezone

logger = logging.getLogger(__name__)

# ── Gemini embedding settings ──────────────────────────────────────────────
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-embedding-exp-03-07:embedContent"
)


# ─────────────────────────────────────────────
# Low-level: call Gemini Embedding API
# ─────────────────────────────────────────────

def get_embedding(text: str) -> list[float] | None:
    """
    Send `text` to the Gemini embedding endpoint and return a float-list.
    Returns None on failure (network error, bad key, etc.).
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — skipping embedding computation.")
        return None

    try:
        import urllib.request, json as _json

        payload = _json.dumps({
            "model": "models/gemini-embedding-exp-03-07",
            "content": {
                "parts": [{"text": text}]
            },
            "taskType": "SEMANTIC_SIMILARITY",
        }).encode("utf-8")

        url = f"{GEMINI_API_URL}?key={api_key}"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read())
            return data["embedding"]["values"]

    except Exception as exc:
        logger.error("Gemini embedding API error: %s", exc)
        return None


# ─────────────────────────────────────────────
# Math: cosine similarity
# ─────────────────────────────────────────────

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    Returns a value in [0, 1] (1 = identical direction).
    """
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    dot   = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))

    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


# ─────────────────────────────────────────────
# Build skill text from a profile
# ─────────────────────────────────────────────

def _build_skill_text(profile) -> str:
    """
    Convert a Profile's skills into a natural-language text for embedding.
    Example: "Python (advanced), Django (expert), Machine Learning (beginner)"
    """
    skills = list(
        profile.profile_skills
        .select_related("skill")
        .values_list("skill__name", "level")
    )
    if not skills:
        return ""
    return ", ".join(f"{name} ({level})" for name, level in skills)


# ─────────────────────────────────────────────
# Compute & cache embedding for a profile
# ─────────────────────────────────────────────

def compute_and_store_embedding(profile) -> bool:
    """
    Build the skill text, call Gemini, and persist the embedding on `profile`.
    Returns True on success, False if the API call failed or no skills.
    """
    text = _build_skill_text(profile)
    if not text:
        # No skills — clear old embedding so stale data isn't used
        profile.skill_embedding = None
        profile.embedding_updated_at = None
        profile.save(update_fields=["skill_embedding", "embedding_updated_at"])
        return False

    embedding = get_embedding(text)
    if embedding is None:
        return False

    profile.skill_embedding = embedding
    profile.embedding_updated_at = timezone.now()
    profile.save(update_fields=["skill_embedding", "embedding_updated_at"])
    logger.info("Embedding updated for profile %s", profile.pk)
    return True


def async_compute_embedding(profile):
    """Fire-and-forget: compute embedding in a background thread."""
    t = threading.Thread(
        target=compute_and_store_embedding,
        args=(profile,),
        daemon=True,
    )
    t.start()


# ─────────────────────────────────────────────
# Core matching logic
# ─────────────────────────────────────────────

def get_top_mentors(student_profile, limit: int = 5) -> list[dict]:
    """
    Given a student's Profile, return a list of the `limit` best-matching
    alumni/teacher mentor profiles, sorted by descending cosine similarity.

    Each result dict contains:
        {
            'user':         User instance,
            'mentor_profile': MentorProfile instance,
            'score':        int (0–100),
            'expertise_list': list[str],
        }

    Falls back to returning the most-recently-active mentors if the student
    has no embedding yet.
    """
    from apps.mentorship.models import MentorProfile

    # If student has no embedding yet, try to compute one now
    if student_profile.skill_embedding is None:
        compute_and_store_embedding(student_profile)

    student_vec = student_profile.skill_embedding  # may still be None

    # Fetch all active mentor profiles with prefetched data
    mentor_profiles = (
        MentorProfile.objects
        .filter(is_active=True)
        .exclude(user=student_profile.user)   # don't match self
        .select_related("user", "user__profile")
    )

    results = []
    for mp in mentor_profiles:
        mentor_vec = mp.user.profile.skill_embedding

        if student_vec and mentor_vec:
            sim   = cosine_similarity(student_vec, mentor_vec)
            score = round(sim * 100)
        else:
            # No vectors available — use a neutral score
            score = 0

        results.append({
            "user":           mp.user,
            "mentor_profile": mp,
            "score":          score,
            "expertise_list": mp.expertise_list(),
        })

    # Sort by score descending, then by name for determinism
    results.sort(key=lambda x: (-x["score"], x["user"].first_name))
    return results[:limit]
