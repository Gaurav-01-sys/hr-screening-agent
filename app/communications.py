"""Human-reviewable communication drafts.

The drafts are deliberately warm and plain-spoken. They are never sent
automatically and never expose protected attributes or unverified reasoning to
a candidate. If Groq is configured, it may smooth the language using only the
bounded, source-backed screening context; deterministic templates remain the
safe fallback for local/offline runs.
"""

from __future__ import annotations

import re
from typing import Optional

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None

from .config import GROQ_API_KEY, GROQ_MODEL
from .memory import build_screening_memory, render_memory_context
from .schemas import CandidateProfile, JobRequirement, Recommendation, ScreeningResponse


def _first_name(candidate: CandidateProfile) -> str:
    name = " ".join((candidate.full_name or "Candidate").split())
    return name.split()[0] if name else "Candidate"


def _natural_strength(candidate: CandidateProfile, response: ScreeningResponse) -> str:
    """Turn rubric shorthand into a specific, conversational positive detail."""

    for skill in candidate.skills:
        if skill.months > 0 and skill.skill.strip():
            return f"Your hands-on experience with {skill.skill}"
    if candidate.total_experience_months:
        return f"Your {candidate.total_experience_months} months of experience"
    if response.strengths:
        strength = response.strengths[0].rstrip(".")
        if re.match(r"Meets \d+/\d+ mandatory skill criteria", strength, flags=re.IGNORECASE):
            return "Your background is a strong match for the role's core requirements"
        if re.match(r"Matches \d+/\d+ preferred skills", strength, flags=re.IGNORECASE):
            return "Your background is a strong match for the preferred skills"
        return strength[0].upper() + strength[1:]
    return "Your background"


def _natural_reason(reason: str) -> str:
    """Translate deterministic rule messages into recruiter-readable language."""

    text = " ".join(reason.split()).strip().rstrip(".")
    match = re.search(
        r"(?P<skill>.+?) experience is (?P<actual>\d+) months, below required (?P<required>\d+) months",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return (
            f"the role asks for at least {match.group('required')} months of "
            f"{match.group('skill').strip()} experience, while the reviewed profile shows "
            f"{match.group('actual')} months"
        )

    match = re.search(
        r"Required skill (?P<skill>.+?) not found", text, flags=re.IGNORECASE
    )
    if match:
        return f"the resume does not show the required {match.group('skill').strip()} experience"

    match = re.search(
        r"Total experience is (?P<actual>\d+) months, below required (?P<required>\d+) months",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return (
            f"the role asks for at least {match.group('required')} months of experience, "
            f"while the reviewed profile shows {match.group('actual')} months"
        )

    match = re.search(
        r"Required education (?P<qualification>.+?) not found", text, flags=re.IGNORECASE
    )
    if match:
        return f"the required {match.group('qualification').strip()} qualification was not confirmed"

    match = re.search(
        r"Required domain (?P<domain>.+?) not found", text, flags=re.IGNORECASE
    )
    if match:
        return f"the resume does not show experience in the required {match.group('domain').strip()} domain"

    return text[:240] or "the current role requirements"


def _fallback_draft(
    candidate: CandidateProfile,
    job: JobRequirement,
    response: ScreeningResponse,
) -> str:
    name = _first_name(candidate)
    role = job.role_title or "the role"

    if response.recommendation == Recommendation.strong_fit:
        strength = _natural_strength(candidate, response)
        return (
            f"Subject: Next steps for your {role} application\n\n"
            f"Hi {name},\n\n"
            f"Thank you for applying for {role}. {strength[0].upper() + strength[1:]} stood out to us, "
            "and we would like to invite you to a structured interview with the hiring team. "
            "Please reply with a few times that work for you, and we will send the format and preparation details.\n\n"
            "Best,\nThe Hiring Team"
        )

    if response.recommendation in {Recommendation.needs_review, Recommendation.borderline}:
        return (
            "Internal draft — do not send\n\n"
            f"{candidate.full_name or 'This candidate'}’s application for {role} needs a human review before a final decision. "
            "Please confirm the remaining extracted fields and any rule concerns in the review panel."
        )

    concern = _natural_reason(response.concerns[0] if response.concerns else "the current role requirements")
    return (
        f"Subject: An update on your {role} application\n\n"
        f"Hi {name},\n\n"
        f"Thank you for your interest in {role} and for the time you put into your application. "
        f"After reviewing your experience against the role, we will not be moving forward at this stage because {concern}. "
        "We appreciate your interest and wish you all the best in your search.\n\n"
        "Best,\nThe Hiring Team"
    )


def _llm_draft(
    candidate: CandidateProfile,
    job: JobRequirement,
    response: ScreeningResponse,
    memory_context: str,
) -> Optional[str]:
    """Ask the configured model to polish a draft without inventing facts."""

    if Groq is None or not GROQ_API_KEY:
        return None

    if response.recommendation == Recommendation.strong_fit:
        audience = "candidate-facing interview invitation"
        instructions = (
            "Invite the candidate to a structured interview, mention one specific strength, "
            "and ask them to share a few suitable times."
        )
    elif response.recommendation == Recommendation.reject:
        audience = "candidate-facing application update"
        instructions = (
            "Thank the candidate, explain the job-related gap in one respectful sentence, "
            "and close warmly without making promises about future roles."
        )
    else:
        audience = "internal reviewer note"
        instructions = (
            "Make clear that a human review is still required. Do not address the candidate "
            "and do not present the result as a final decision."
        )

    prompt = f"""
Write a short, natural {audience} for an HR reviewer.

Rules:
- Sound like a thoughtful human recruiter, not an ATS or a scoring script.
- Use only facts present in SCREENING MEMORY; do not invent interview dates, people, benefits, or qualifications.
- Avoid jargon such as mandatory_fit, hard_fail, soft penalty, rule_id, or confidence score.
- Keep it under 120 words and return plain text only (no markdown fences or commentary).
- {instructions}

{memory_context}
""".strip()

    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write concise, warm HR communications. Be specific without being cold. "
                        "Never infer or mention protected characteristics."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.55,
            max_tokens=220,
        )
        text = (completion.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:text|markdown)?\s*|\s*```$", "", text).strip()
        return text[:1200] if text else None
    except Exception:
        return None


def build_communication_draft(
    candidate: CandidateProfile,
    job: JobRequirement,
    response: ScreeningResponse,
) -> str:
    """Build a natural draft using bounded memory context and a safe fallback."""

    memory_context = render_memory_context(build_screening_memory(candidate, job, response))
    return _llm_draft(candidate, job, response, memory_context) or _fallback_draft(
        candidate, job, response
    )
