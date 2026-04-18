from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from guardrails import GuardrailResult, GroundingResult, check_user_query, evaluate_grounding, grounded_fallback
from llm_client import LLMClient
from pawpal_system import Owner, Scheduler
from rag_retriever import RetrievedChunk, format_sources_for_prompt, owner_context_lines, retrieve_multisource


@dataclass
class CopilotResponse:
    query: str
    answer: str
    backend: str
    specialized_mode: bool
    plan_steps: List[str] = field(default_factory=list)
    sources: List[RetrievedChunk] = field(default_factory=list)
    guardrail: Optional[GuardrailResult] = None
    grounding: Optional[GroundingResult] = None


class PawPalAICopilot:
    """Integrated RAG + guardrails + observable planning workflow for PawPal+."""

    def __init__(self, llm_client: Optional[LLMClient] = None, doc_dir: str = "data/care_docs") -> None:
        self.llm = llm_client or LLMClient()
        self.doc_dir = doc_dir

    def ask(
        self,
        query: str,
        owner: Owner,
        scheduler: Scheduler,
        specialized_mode: bool = True,
    ) -> CopilotResponse:
        plan_steps: List[str] = []
        plan_steps.append("1. Validate the user request with safety guardrails.")
        guardrail = check_user_query(query)

        if not guardrail.allow:
            answer = (
                "Summary:\n"
                f"{guardrail.user_message}\n\n"
                "Action Plan:\n"
                "- Use PawPal to review the saved routine or reminders you already have.\n"
                "- Contact a licensed veterinarian for medical or emergency decisions.\n\n"
                "Why:\n"
                f"- Guardrail triggered because this request falls into the '{guardrail.reason}' category.\n\n"
                "Sources:\n"
                "- [guardrail_policy]\n\n"
                "Safety Note:\n"
                "This assistant supports organization only and cannot diagnose illness or provide dosing advice."
            )
            grounding = GroundingResult(passed=True, score=1.0, citation_count=1, notes="guardrail response")
            return CopilotResponse(
                query=query,
                answer=answer,
                backend=self.llm.backend,
                specialized_mode=specialized_mode,
                plan_steps=plan_steps,
                sources=[],
                guardrail=guardrail,
                grounding=grounding,
            )

        intent = self._classify_intent(query)
        plan_steps.append(f"2. Classify the request intent as '{intent}'.")

        sources = retrieve_multisource(query, owner, doc_dir=self.doc_dir)
        plan_steps.append(
            f"3. Retrieve relevant context from two sources: PawPal pet/task data and care documents ({len(sources)} chunks)."
        )

        prompt = self._build_user_prompt(query, owner, scheduler, intent, sources)
        system_prompt = self._system_prompt(specialized_mode=specialized_mode)
        plan_steps.append("4. Draft a grounded answer with citations from the retrieved context.")

        answer = self.llm.generate(system_prompt=system_prompt, user_prompt=prompt, temperature=0.2)
        grounding = evaluate_grounding(answer, sources)
        plan_steps.append(
            f"5. Run a grounding check (passed={grounding.passed}, score={grounding.score}, citations={grounding.citation_count})."
        )

        if not grounding.passed:
            answer = grounded_fallback(sources)
            grounding = evaluate_grounding(answer, sources)
            plan_steps.append("6. Replace the answer with a fully grounded fallback summary.")
        else:
            plan_steps.append("6. Finalize the grounded response.")

        return CopilotResponse(
            query=query,
            answer=answer,
            backend=self.llm.backend,
            specialized_mode=specialized_mode,
            plan_steps=plan_steps,
            sources=sources,
            guardrail=guardrail,
            grounding=grounding,
        )

    def _classify_intent(self, query: str) -> str:
        query_lower = query.lower()
        if any(word in query_lower for word in ["conflict", "overlap", "same time"]):
            return "conflict_check"
        if any(word in query_lower for word in ["today", "tomorrow", "plan", "schedule", "weekend"]):
            return "care_planning"
        if any(word in query_lower for word in ["why", "explain", "reason"]):
            return "explanation"
        return "general_pet_care"

    def _system_prompt(self, specialized_mode: bool = True) -> str:
        if not specialized_mode:
            return (
                "You are a helpful assistant. Answer the user's pet-care planning question using the provided context. "
                "Do not invent facts."
            )

        return (
            "You are PawPal AI Care Copilot, a cautious planning assistant for multi-pet routines. "
            "Only use the provided context. Never diagnose illness, never prescribe medication dosages, and never "
            "treat emergencies. If context is missing, say so explicitly. Use this exact structure:\n"
            "Summary:\n"
            "Action Plan:\n"
            "Why:\n"
            "Sources:\n"
            "Safety Note:\n"
            "Cite factual claims inline with square-bracket source IDs like [task_luna_1]. Keep the tone calm, structured, and professional."
        )

    def _build_user_prompt(
        self,
        query: str,
        owner: Owner,
        scheduler: Scheduler,
        intent: str,
        sources: List[RetrievedChunk],
    ) -> str:
        conflicts = scheduler.detect_conflicts()
        owner_lines = owner_context_lines(owner)
        source_block = format_sources_for_prompt(sources)
        conflict_text = "\n".join(f"- {warning}" for warning in conflicts) if conflicts else "- No exact-time conflicts detected."

        return (
            f"User question: {query}\n"
            f"Intent: {intent}\n\n"
            "High-level owner snapshot:\n"
            + "\n".join(owner_lines[:20])
            + "\n\nConflict summary:\n"
            + conflict_text
            + "\n\nRetrieved context:\n"
            + source_block
            + "\n\nRespond using only the facts above."
        )