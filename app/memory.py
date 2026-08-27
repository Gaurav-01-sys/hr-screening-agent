"""Small, local context builder inspired by MemPalace's palace model.

MemPalace keeps source material verbatim in drawers and uses wings, halls, and
rooms to make the right context easy to retrieve. This adapter applies the
same bounded idea to one screening run without adding a second database or
silently persisting candidate data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .schemas import CandidateProfile, JobRequirement, ScreeningResponse


@dataclass(frozen=True)
class MemoryDrawer:
    """One source-backed piece of context for a response prompt."""

    wing: str
    hall: str
    room: str
    content: str
    source: Optional[str] = None


def _clean(value: object) -> str:
    return " ".join(str(value or "").split())


def build_screening_memory(
    candidate: CandidateProfile,
    job: JobRequirement,
    response: Optional[ScreeningResponse] = None,
) -> List[MemoryDrawer]:
    """Build a small, explicit palace for the current screening context.

    Evidence snippets are kept as-is inside evidence drawers. Only job-related
    fields are included; protected characteristics are never copied into the
    response context.
    """

    drawers: List[MemoryDrawer] = []
    candidate_facts = [
        fact
        for fact in (
            f"Name: {_clean(candidate.full_name)}" if candidate.full_name else "",
            f"Current role: {_clean(candidate.current_title)}"
            if candidate.current_title
            else "",
            f"Total experience: {candidate.total_experience_months} months",
            f"Skills: {_clean(', '.join(item.skill for item in candidate.skills[:8]))}"
            if candidate.skills
            else "",
        )
        if fact
    ]
    if candidate_facts:
        drawers.append(
            MemoryDrawer(
                wing="screening",
                hall="hall_facts",
                room="candidate",
                content="; ".join(candidate_facts),
                source="resume",
            )
        )

    job_facts = [
        f"Role: {_clean(job.role_title)}",
        f"Mandatory skills: {_clean(', '.join(job.mandatory_skills[:8]))}"
        if job.mandatory_skills
        else "",
        f"Preferred skills: {_clean(', '.join(job.preferred_skills[:8]))}"
        if job.preferred_skills
        else "",
    ]
    drawers.append(
        MemoryDrawer(
            wing="screening",
            hall="hall_facts",
            room="role",
            content="; ".join(fact for fact in job_facts if fact),
            source="job description",
        )
    )

    for skill in candidate.skills[:8]:
        for evidence in skill.evidence[:2]:
            snippet = _clean(evidence.snippet)
            if snippet:
                drawers.append(
                    MemoryDrawer(
                        wing="screening",
                        hall="hall_evidence",
                        room=f"skill:{_clean(skill.skill).lower()}",
                        content=f"{skill.skill}: {skill.months} months. {snippet}",
                        source=evidence.source_document,
                    )
                )

    if response is not None:
        if response.strengths:
            drawers.append(
                MemoryDrawer(
                    wing="screening",
                    hall="hall_decision",
                    room="strengths",
                    content="; ".join(_clean(item) for item in response.strengths[:3]),
                    source="screening rubric",
                )
            )
        if response.concerns:
            drawers.append(
                MemoryDrawer(
                    wing="screening",
                    hall="hall_decision",
                    room="concerns",
                    content="; ".join(_clean(item) for item in response.concerns[:3]),
                    source="screening rubric",
                )
            )
        drawers.append(
            MemoryDrawer(
                wing="screening",
                hall="hall_decision",
                room="outcome",
                content=(
                    f"Recommendation: {response.recommendation.value}; "
                    f"final score: {response.scores.final_score:.1f}; "
                    f"hard fail: {'yes' if response.hard_fail else 'no'}"
                ),
                source="screening rubric",
            )
        )

    return drawers


def render_memory_context(drawers: Iterable[MemoryDrawer], max_chars: int = 3200) -> str:
    """Render bounded room-labeled context for a natural-language prompt."""

    lines = ["SCREENING MEMORY (source-backed context; do not invent facts)"]
    total = len(lines[0])
    for drawer in drawers:
        source = f" ({drawer.source})" if drawer.source else ""
        line = f"[{drawer.wing}/{drawer.hall}/{drawer.room}] {drawer.content}{source}"
        if total + len(line) + 1 > max_chars:
            lines.append("[screening/hall_facts/context] More source context is available in the review tables.")
            break
        lines.append(line)
        total += len(line) + 1
    return "\n".join(lines)
