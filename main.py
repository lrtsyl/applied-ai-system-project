from __future__ import annotations

from care_copilot import PawPalAICopilot
from demo_data import build_demo_owner
from pawpal_system import Scheduler


DEMO_QUERIES = [
    "What should Luna and Milo do today?",
    "Are there any conflicts in my schedule today?",
    "My dog is vomiting blood. What dose should I give?",
]


def main() -> None:
    owner = build_demo_owner()
    scheduler = Scheduler(owner)
    copilot = PawPalAICopilot()

    print("PawPal AI Care Copilot CLI Demo")
    print("=" * 32)
    print(f"Backend: {copilot.llm.backend}")
    print()

    for index, query in enumerate(DEMO_QUERIES, start=1):
        response = copilot.ask(query=query, owner=owner, scheduler=scheduler, specialized_mode=True)
        print(f"Demo {index}: {query}")
        print("-" * (len(query) + 8))
        print("Workflow steps:")
        for step in response.plan_steps:
            print(f"  - {step}")
        print()
        print(response.answer)
        if response.grounding:
            print()
            print(
                f"Grounding -> passed={response.grounding.passed}, score={response.grounding.score}, citations={response.grounding.citation_count}"
            )
        print("\n" + "=" * 32 + "\n")


if __name__ == "__main__":
    main()