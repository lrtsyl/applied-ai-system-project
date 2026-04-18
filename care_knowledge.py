from __future__ import annotations

from pathlib import Path
from typing import Dict, List


DEFAULT_CARE_DOCS: List[Dict[str, str]] = [
    {
        "source_id": "care_routine_basics",
        "title": "Routine basics",
        "text": (
            "Pets usually benefit from consistent routines for feeding, exercise, play, grooming, "
            "and rest. Repeating tasks at similar times each day can reduce missed care steps and "
            "make it easier to notice unusual changes in behavior."
        ),
    },
    {
        "source_id": "care_medication_safety",
        "title": "Medication safety",
        "text": (
            "Medication reminders should match the veterinarian's written instructions. A planning "
            "assistant should never guess a dosage, change a medicine schedule on its own, or claim "
            "to diagnose symptoms. If a pet has a bad reaction, contact a licensed veterinarian."
        ),
    },
    {
        "source_id": "care_exercise_enrichment",
        "title": "Exercise and enrichment",
        "text": (
            "Dogs often need walks or active play, cats often benefit from short play sessions and "
            "environmental enrichment, and rabbits often need supervised movement and a clean habitat. "
            "The exact amount depends on the pet's age, health, and veterinarian guidance."
        ),
    },
    {
        "source_id": "care_grooming_hygiene",
        "title": "Grooming and hygiene",
        "text": (
            "Regular grooming, litter or habitat cleaning, and clean food and water setups support daily "
            "pet care. Grooming schedules vary by species, coat type, and health needs."
        ),
    },
    {
        "source_id": "care_emergency_escalation",
        "title": "Emergency escalation",
        "text": (
            "If a pet has severe breathing trouble, uncontrolled bleeding, collapse, seizures, suspected "
            "poisoning, or other urgent warning signs, the safest action is immediate veterinary help or "
            "an emergency clinic. A general AI planner should not treat emergencies."
        ),
    },
]


def load_care_docs(doc_dir: str = "data/care_docs") -> List[Dict[str, str]]:
    """Load custom care documents from disk, or fall back to built-in docs."""
    path = Path(doc_dir)
    docs: List[Dict[str, str]] = []

    if path.exists():
        for file_path in sorted(path.iterdir()):
            if file_path.suffix.lower() not in {".txt", ".md"}:
                continue
            text = file_path.read_text(encoding="utf-8").strip()
            if not text:
                continue
            docs.append(
                {
                    "source_id": f"doc_{file_path.stem.lower().replace(' ', '_')}",
                    "title": file_path.stem,
                    "text": text,
                }
            )

    return docs or DEFAULT_CARE_DOCS