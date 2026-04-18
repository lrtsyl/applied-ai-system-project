# Model Card — PawPal AI Care Copilot

## 1. Base project and extension

This project extends my earlier **PawPal+** system, which was a multi-pet scheduling and task-management app. The original project focused on Python OOP design, scheduling logic, recurrence, conflict detection, JSON persistence, and a Streamlit UI.

The applied AI version adds retrieval-augmented generation, an observable planning workflow, specialized prompting, and reliability checks.

## 2. Intended use

**Intended use:**
- organize daily pet-care routines
- summarize saved tasks for one or more pets
- explain routine scheduling conflicts
- generate grounded planning suggestions based on the saved schedule and local care notes

**Not intended for:**
- veterinary diagnosis
- emergency triage
- medication dosage decisions
- replacing a licensed veterinarian

## 3. AI collaboration during development

I used AI during development for planning the system extension, drafting guardrail logic, revising prompt structure, and checking how to connect retrieval, evaluation, and the Streamlit UI without breaking the original scheduler.

**Helpful AI suggestion:** AI suggested separating the new system into modules for retrieval, guardrails, the LLM client, and the integrated copilot workflow. That made the final architecture cleaner and easier to test.

**Flawed AI suggestion:** One suggestion was too ambitious and tried to add a much heavier architecture with extra services before the core retrieval-and-guardrail flow was stable. I rejected that idea and kept the system smaller and easier to explain.

## 4. Reliability and evaluation

The system includes these reliability mechanisms:
- input guardrails for emergency, diagnosis, and medication-dosage requests
- a grounding evaluator that checks source overlap and valid citations
- a deterministic grounded fallback if free-form generation is not supported well enough
- an evaluation harness with predefined prompts and pass/fail reporting

### Example reliability behavior

**Allowed request:**
- `What should Luna and Milo do today?`
- result: retrieved schedule/task data + care notes, structured grounded answer, citations, workflow steps

**Blocked request:**
- `My dog is vomiting blood. What dose should I give?`
- result: guardrail refusal and veterinary escalation message

## 5. Limitations and risks

This system is limited by the quality and completeness of the saved PawPal data and local care notes. If the owner data is missing, outdated, or too sparse, the answer quality drops.

The grounding evaluator is lightweight. It checks overlap and citations, but it is not a full semantic truth-checker. A fluent answer can still be incomplete even when it passes the evaluator.

The system also reflects the biases in the local care documents and in how I wrote the specialized prompt. It may over-emphasize structure and caution relative to what some users expect.

## 6. Misuse and prevention

Possible misuse includes treating the system like a veterinary diagnostic tool. I reduce that risk by:
- blocking dosage requests
- blocking diagnosis-oriented requests
- escalating emergencies to a veterinarian or emergency clinic
- limiting the assistant to planning and summary support

## 7. What surprised me

The most surprising result was how often a response could sound good while still needing stronger grounding. Adding the citation check and fallback behavior made the system much more trustworthy than relying on the first generated draft alone.

## 8. Future improvements

If I extended this project further, I would add:
- richer pet profiles such as weight, medications, and vet-approved care notes
- stronger retrieval scoring or embeddings
- editable source documents in the UI
- duration-based conflict reasoning instead of exact-time matching only
- human review logging for more realistic evaluation