from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from rag_retriever import RetrievedChunk, normalize_tokens


EMERGENCY_PATTERNS = [
    "can't breathe",
    "cannot breathe",
    "not breathing",
    "vomiting blood",
    "bleeding",
    "collapse",
    "collapsed",
    "seizure",
    "poison",
    "poisoned",
    "toxin",
    "emergency",
]

DIAGNOSIS_PATTERNS = [
    "diagnose",
    "what disease",
    "what illness",
    "what is wrong",
    "infection",
    "kidney failure",
]

DOSAGE_PATTERNS = [
    "dosage",
    "dose",
    "mg",
    "milligrams",
    "how much medicine",
    "how much medication",
]

CITATION_RE = re.compile(r"\[([a-zA-Z0-9_\-]+)\]")


@dataclass
class GuardrailResult:
    allow: bool
    severity: str
    reason: str
    user_message: str


@dataclass
class GroundingResult:
    passed: bool
    score: float
    citation_count: int
    notes: str


def check_user_query(query: str) -> GuardrailResult:
    query_lower = query.lower()

    if any(pattern in query_lower for pattern in EMERGENCY_PATTERNS):
        return GuardrailResult(
            allow=False,
            severity="high",
            reason="emergency",
            user_message=(
                "This sounds urgent. I can help with organization, but I should not handle pet emergencies. "
                "Please contact a licensed veterinarian or emergency clinic immediately."
            ),
        )

    if any(pattern in query_lower for pattern in DOSAGE_PATTERNS):
        return GuardrailResult(
            allow=False,
            severity="high",
            reason="dosage",
            user_message=(
                "I can summarize scheduled medication reminders from PawPal, but I should not give medication "
                "dosages or dosing changes. Please follow the veterinarian's written instructions."
            ),
        )

    if any(pattern in query_lower for pattern in DIAGNOSIS_PATTERNS):
        return GuardrailResult(
            allow=False,
            severity="medium",
            reason="diagnosis",
            user_message=(
                "I can help organize routines and surface saved care tasks, but I should not diagnose illnesses. "
                "A veterinarian should evaluate symptoms and treatment decisions."
            ),
        )

    return GuardrailResult(
        allow=True,
        severity="none",
        reason="allowed",
        user_message="No blocking guardrail triggered.",
    )


def cited_source_ids(answer: str) -> List[str]:
    return CITATION_RE.findall(answer)


def evaluate_grounding(answer: str, sources: Iterable[RetrievedChunk]) -> GroundingResult:
    answer_tokens = set(normalize_tokens(answer))
    source_tokens = set()
    known_ids = set()
    for source in sources:
        source_tokens.update(normalize_tokens(source.text))
        known_ids.add(source.source_id)

    overlap = len(answer_tokens & source_tokens)
    score = overlap / max(1, len(answer_tokens))

    cited_ids = cited_source_ids(answer)
    valid_citations = [source_id for source_id in cited_ids if source_id in known_ids]

    passed = score >= 0.18 and len(valid_citations) >= 1
    notes = (
        f"support_overlap={overlap}, answer_tokens={len(answer_tokens)}, "
        f"valid_citations={len(valid_citations)}"
    )

    return GroundingResult(
        passed=passed,
        score=round(score, 3),
        citation_count=len(valid_citations),
        notes=notes,
    )


def grounded_fallback(sources: Iterable[RetrievedChunk]) -> str:
    lines = [
        "Summary:",
        "I could not verify a fully grounded free-form answer, so here are the most relevant verified facts.",
        "",
        "Action Plan:",
    ]
    source_list = list(sources)
    for source in source_list[:4]:
        lines.append(f"- {source.text} [{source.source_id}]")
    lines.extend(
        [
            "",
            "Why:",
            "- Each action above comes directly from the retrieved PawPal schedule or care notes.",
            "",
            "Sources:",
        ]
    )
    for source in source_list[:4]:
        lines.append(f"- [{source.source_id}] {source.title}")
    lines.extend(
        [
            "",
            "Safety Note:",
            "This assistant is limited to planning and summary support. It does not diagnose illness or set medication dosages.",
        ]
    )
    return "\n".join(lines)