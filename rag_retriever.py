from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from care_knowledge import load_care_docs
from pawpal_system import Owner


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "today",
    "what",
    "with",
    "you",
}


@dataclass
class RetrievedChunk:
    source_id: str
    source_type: str
    title: str
    text: str
    score: float
    metadata: Dict[str, str]


TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")


def normalize_tokens(text: str) -> List[str]:
    return [
        token.lower()
        for token in TOKEN_RE.findall(text)
        if token.lower() not in STOPWORDS and len(token) > 1
    ]


def chunk_text(text: str, max_words: int = 70) -> List[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()]

    chunks: List[str] = []
    start = 0
    overlap = 15
    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]).strip())
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks


def owner_context_lines(owner: Owner) -> List[str]:
    lines: List[str] = [f"Owner: {owner.name}"]
    for pet in owner.pets:
        lines.append(f"Pet {pet.name}: species={pet.species}, age={pet.age}")
        for task in pet.tasks:
            lines.append(
                f"Task for {pet.name}: {task.description} at {task.time_str} on {task.due_date.isoformat()} "
                f"frequency={task.frequency} priority={task.priority} completed={task.completed} category={task.category}"
            )
    return lines


def _score(query_tokens: Sequence[str], text: str, metadata: Dict[str, str]) -> float:
    chunk_tokens = normalize_tokens(text)
    if not chunk_tokens:
        return 0.0

    overlap = len(set(query_tokens) & set(chunk_tokens))
    exact_mentions = sum(1 for token in query_tokens if token in text.lower())
    score = float(overlap) + exact_mentions * 0.15

    joined_query = " ".join(query_tokens)
    for boosted_key in ("pet_name", "category", "priority"):
        value = metadata.get(boosted_key, "").lower()
        if value and value in joined_query:
            score += 1.0

    if metadata.get("source_type") == "task":
        score += 0.25

    return score


def build_task_chunks(owner: Owner) -> List[RetrievedChunk]:
    chunks: List[RetrievedChunk] = []
    for pet in owner.pets:
        pet_summary = (
            f"{pet.name} is a {pet.age}-year-old {pet.species}. "
            f"{pet.name} currently has {len(pet.tasks)} tracked tasks in PawPal."
        )
        chunks.append(
            RetrievedChunk(
                source_id=f"pet_{pet.name.lower()}_profile",
                source_type="pet_profile",
                title=f"{pet.name} profile",
                text=pet_summary,
                score=0.0,
                metadata={"pet_name": pet.name.lower(), "source_type": "pet_profile"},
            )
        )
        for index, task in enumerate(pet.tasks, start=1):
            task_text = (
                f"{pet.name} has task '{task.description}' scheduled for {task.due_date.isoformat()} at {task.time_str}. "
                f"Priority is {task.priority}. Frequency is {task.frequency}. Category is {task.category}. "
                f"Completed status is {task.completed}."
            )
            chunks.append(
                RetrievedChunk(
                    source_id=f"task_{pet.name.lower()}_{index}",
                    source_type="task",
                    title=f"{pet.name} task {index}",
                    text=task_text,
                    score=0.0,
                    metadata={
                        "pet_name": pet.name.lower(),
                        "category": task.category.lower(),
                        "priority": task.priority.lower(),
                        "source_type": "task",
                    },
                )
            )
    return chunks


def build_doc_chunks(doc_dir: str = "data/care_docs") -> List[RetrievedChunk]:
    chunks: List[RetrievedChunk] = []
    for doc in load_care_docs(doc_dir):
        for index, part in enumerate(chunk_text(doc["text"]), start=1):
            chunks.append(
                RetrievedChunk(
                    source_id=f"{doc['source_id']}_chunk_{index}",
                    source_type="care_doc",
                    title=doc["title"],
                    text=part,
                    score=0.0,
                    metadata={"source_type": "care_doc"},
                )
            )
    return chunks


def retrieve_multisource(
    query: str,
    owner: Owner,
    doc_dir: str = "data/care_docs",
    top_k_tasks: int = 4,
    top_k_docs: int = 3,
) -> List[RetrievedChunk]:
    query_tokens = normalize_tokens(query)
    task_chunks = build_task_chunks(owner)
    doc_chunks = build_doc_chunks(doc_dir)

    for chunk in task_chunks:
        chunk.score = _score(query_tokens, chunk.text, chunk.metadata)
    for chunk in doc_chunks:
        chunk.score = _score(query_tokens, chunk.text, chunk.metadata)

    sorted_tasks = sorted(task_chunks, key=lambda item: item.score, reverse=True)
    sorted_docs = sorted(doc_chunks, key=lambda item: item.score, reverse=True)

    selected: List[RetrievedChunk] = []
    selected.extend([chunk for chunk in sorted_tasks if chunk.score > 0][:top_k_tasks])
    selected.extend([chunk for chunk in sorted_docs if chunk.score > 0][:top_k_docs])

    if not selected:
        selected.extend(sorted_tasks[:2])
        selected.extend(sorted_docs[:2])

    return selected


def format_sources_for_prompt(chunks: Iterable[RetrievedChunk]) -> str:
    lines = []
    for chunk in chunks:
        lines.append(f"[{chunk.source_id}] ({chunk.source_type}) {chunk.text}")
    return "\n".join(lines)