# PawPal AI Care Copilot

PawPal AI Care Copilot is the final applied AI extension of my earlier **PawPal+** project.

## Base project and original scope

The original project was **PawPal+**, a Python OOP pet-care scheduler with a CLI demo and a Streamlit UI. It let one owner manage multiple pets, add care tasks, sort and filter tasks, detect exact-time conflicts, advance recurring tasks, and save/load data with JSON persistence.

That original system was useful for organizing care schedules, but it did not understand natural-language questions or explain plans in a grounded AI-assisted way.

## What this new system does

This new version extends PawPal+ into an applied AI system that can answer pet-care planning questions using:

- the owner’s saved pet/task data
- local care documents
- guardrails for unsafe medical requests
- a grounding check for answer reliability
- observable plan steps so the workflow is inspectable

Example questions:
- `What should Luna and Milo do today?`
- `Are there any conflicts in my schedule today?`
- `Plan tomorrow morning for all pets and explain why.`
- `My dog is vomiting blood. What dose should I give?`

## New AI features added

This system includes:

1. **Retrieval-Augmented Generation (RAG)**
   - retrieves relevant chunks from two sources before answering:
     - structured PawPal pet/task data
     - custom care documents in `data/care_docs/`

2. **Observable agentic workflow**
   - the system shows planning steps such as guardrail validation, intent classification, retrieval, answer drafting, and grounding checks

3. **Specialized prompting**
   - uses a PawPal-specific prompt that forces structured sections:
     - Summary
     - Action Plan
     - Why
     - Sources
     - Safety Note

4. **Reliability harness**
   - blocks emergency, diagnosis, and medication-dosage requests
   - checks whether answers are grounded in retrieved sources
   - falls back to a deterministic grounded summary when free-form generation is not sufficiently supported

## Architecture overview

See `assets/architecture_mermaid.md` for the system diagram.

The main flow is:
1. user asks a question in Streamlit or CLI
2. guardrails inspect the request
3. retriever pulls relevant schedule data and care notes
4. prompt builder creates a grounded AI request
5. model generates an answer
6. grounding evaluator checks citations and source overlap
7. final answer, reliability metrics, and planning steps are shown to the user

## Project files

- `pawpal_system.py` — original backend classes and scheduling logic
- `app.py` — Streamlit UI with scheduler + AI copilot tab
- `main.py` — CLI demo for end-to-end AI examples
- `care_copilot.py` — integrated AI workflow
- `rag_retriever.py` — multi-source retrieval over tasks and care docs
- `guardrails.py` — safety rules and grounding checks
- `llm_client.py` — mock / Ollama / OpenAI-compatible LLM backend wrapper
- `demo_data.py` — demo pets and tasks for consistent examples
- `eval_harness.py` — evaluation script with pass/fail summary
- `tests/` — pytest suite
- `assets/architecture_mermaid.md` — system architecture diagram

## Setup instructions

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Choose an LLM backend

This project supports three modes:

**Option A: mock mode (fastest for testing)**
```bash
export LLM_BACKEND=mock
```

**Option B: Ollama**
```bash
export LLM_BACKEND=ollama
export LLM_MODEL=llama3.1
```

**Option C: OpenAI-compatible endpoint**
```bash
export LLM_BACKEND=openai_compat
export OPENAI_API_KEY=your_key_here
export OPENAI_COMPAT_URL=https://api.openai.com/v1/chat/completions
export LLM_MODEL=gpt-4o-mini
```

### 4. Run the Streamlit app

```bash
streamlit run app.py
```

### 5. Run the CLI demo

```bash
python main.py
```

### 6. Run the evaluation harness

```bash
python eval_harness.py
```

### 7. Run tests

```bash
pytest
```

## Sample interactions

### Example 1 — normal planning request

Input:
```
What should Luna and Milo do today?
```

Expected behavior:
- retrieves Luna and Milo task chunks
- retrieves care document chunks
- returns a structured answer with citations
- shows planning steps and grounding score

### Example 2 — conflict request

Input:
```
Are there any conflicts in my schedule today?
```

Expected behavior:
- surfaces the exact-time conflict at 18:00
- explains which pets/tasks are involved
- cites retrieved schedule sources

### Example 3 — unsafe medical request

Input:
```
My dog is vomiting blood. What dose should I give?
```

Expected behavior:
- blocks the request with a guardrail
- tells the user to contact a veterinarian or emergency clinic
- does not give a dose or diagnosis

## Design decisions and trade-offs

I kept retrieval lightweight and transparent by using rule-based keyword scoring instead of a full vector database. That made the project easier to explain, inspect, and test within the time limits.

I also restricted the AI system to routine planning and grounded summaries. That means the system is safer and easier to evaluate, but it also means it cannot answer specialized medical questions or handle complex cases that need professional judgment.

## Testing summary

The project includes:
- backend scheduling tests from the original PawPal+ system
- AI feature tests for retrieval, guardrails, planning steps, and grounding
- an evaluation harness that runs several predefined prompts and prints:
  - pass/fail checks
  - average grounding score
  - baseline vs specialized prompt comparison

## Reflection

This project showed me that the hardest part of building applied AI systems is not just generating text. It is making the AI retrieve the right information, limit unsafe behavior, and explain what it is doing in a way that another person can inspect and trust.

## Demo walkthrough

![PawPal AI Care Copilot walkthrough](assets/walkthrough.gif)