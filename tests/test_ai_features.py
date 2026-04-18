from care_copilot import PawPalAICopilot
from demo_data import build_demo_owner
from guardrails import check_user_query, evaluate_grounding
from llm_client import LLMClient, LLMConfig
from pawpal_system import Scheduler
from rag_retriever import retrieve_multisource


def build_mock_copilot() -> PawPalAICopilot:
    return PawPalAICopilot(llm_client=LLMClient(LLMConfig(backend="mock")))


def test_multisource_retrieval_returns_task_and_doc_chunks():
    owner = build_demo_owner()
    results = retrieve_multisource("What should Luna do today?", owner)

    source_types = {item.source_type for item in results}
    assert "task" in source_types or "pet_profile" in source_types
    assert "care_doc" in source_types


def test_guardrail_blocks_emergency_and_dosage_questions():
    result = check_user_query("My dog is vomiting blood. What dose should I give?")
    assert result.allow is False
    assert result.reason in {"emergency", "dosage"}


def test_copilot_returns_observable_steps_and_grounded_output():
    owner = build_demo_owner()
    scheduler = Scheduler(owner)
    copilot = build_mock_copilot()

    response = copilot.ask("What should Luna and Milo do today?", owner, scheduler, specialized_mode=True)

    assert len(response.plan_steps) >= 5
    assert "Summary:" in response.answer
    assert response.grounding is not None
    assert response.grounding.passed is True


def test_grounding_evaluator_accepts_cited_answer():
    owner = build_demo_owner()
    sources = retrieve_multisource("What should Luna do today?", owner)
    answer = f"Summary:\nLuna has a morning walk scheduled at 08:00 [task_luna_1].\n\nSources:\n- [task_luna_1]"
    result = evaluate_grounding(answer, sources)

    assert result.passed is True
    assert result.citation_count >= 1