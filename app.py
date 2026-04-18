from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from care_copilot import PawPalAICopilot
from demo_data import build_demo_owner
from pawpal_system import Owner, Pet, Scheduler, Task


DATA_FILE = "pawpal_data.json"
PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}
CATEGORY_ICON = {
    "feeding": "🍽️",
    "walk": "🚶",
    "medication": "💊",
    "vet": "🩺",
    "grooming": "🛁",
    "play": "🎾",
    "general": "📌",
}


EXAMPLE_PROMPTS = [
    "What should Luna and Milo do today?",
    "Are there any conflicts in my schedule today?",
    "Plan tomorrow morning for all pets and explain why.",
    "My dog is vomiting blood. What dose should I give?",
]


def load_owner() -> Owner:
    if Path(DATA_FILE).exists():
        return Owner.load_from_json(DATA_FILE)
    return build_demo_owner()


def save_owner() -> None:
    st.session_state.owner.save_to_json(DATA_FILE)


def rebuild_scheduler() -> None:
    st.session_state.scheduler = Scheduler(st.session_state.owner)


def schedule_rows(tasks):
    rows = []
    for pet, task in tasks:
        rows.append(
            {
                "Date": task.due_date.isoformat(),
                "Time": task.time_str,
                "Pet": pet.name,
                "Task": f"{CATEGORY_ICON.get(task.category, '📌')} {task.description}",
                "Priority": f"{PRIORITY_ICON[task.priority]} {task.priority.title()}",
                "Frequency": task.frequency.title(),
                "Status": "✅ Done" if task.completed else "⏳ Pending",
            }
        )
    return rows


def task_option_label(item):
    pet, task = item
    return (
        f"{pet.name} | {task.due_date.isoformat()} {task.time_str} | "
        f"{task.description} | {task.frequency}"
    )


st.set_page_config(page_title="PawPal AI Care Copilot", page_icon="🐾", layout="wide")

if "owner" not in st.session_state:
    st.session_state.owner = load_owner()
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)
if "copilot" not in st.session_state:
    st.session_state.copilot = PawPalAICopilot()
if "last_ai_response" not in st.session_state:
    st.session_state.last_ai_response = None

owner = st.session_state.owner
scheduler = st.session_state.scheduler
copilot = st.session_state.copilot

st.title("🐾 PawPal AI Care Copilot")
st.caption(
    "An applied AI extension of PawPal+ with multi-source retrieval, observable planning steps, guardrails, and evaluation-friendly outputs."
)

with st.sidebar:
    st.header("System")
    st.write(f"Saved file: `{DATA_FILE}`")
    st.write(f"LLM backend: `{copilot.llm.backend}`")
    st.write("RAG sources: PawPal pet/task data + local care documents")

    if st.button("Save now"):
        save_owner()
        st.success("Saved current owner, pets, and tasks.")

    if st.button("Load demo AI data"):
        st.session_state.owner = build_demo_owner()
        rebuild_scheduler()
        save_owner()
        st.success("Loaded demo data for AI examples.")
        st.rerun()

    if st.button("Reset all data"):
        st.session_state.owner = Owner("Jordan")
        rebuild_scheduler()
        if Path(DATA_FILE).exists():
            Path(DATA_FILE).unlink()
        st.success("Cleared saved data.")
        st.rerun()

manage_tab, ai_tab = st.tabs(["Scheduler", "AI Care Copilot"])

with manage_tab:
    st.subheader("Owner")
    owner_name = st.text_input("Owner name", value=owner.name, key="owner_name")
    if owner_name != owner.name:
        owner.name = owner_name
        save_owner()

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown("### Add a Pet")
        with st.form("add_pet_form", clear_on_submit=True):
            pet_name = st.text_input("Pet name")
            species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Other"])
            age = st.number_input("Age", min_value=0, max_value=40, value=1, step=1)
            add_pet_clicked = st.form_submit_button("Add pet")

            if add_pet_clicked:
                if not pet_name.strip():
                    st.error("Enter a pet name.")
                elif owner.get_pet(pet_name.strip()) is not None:
                    st.error("A pet with that name already exists.")
                else:
                    owner.add_pet(Pet(pet_name.strip(), species, int(age)))
                    rebuild_scheduler()
                    save_owner()
                    st.success(f"Added {pet_name.strip()}.")
                    st.rerun()

        st.markdown("### Current Pets")
        if owner.pets:
            st.table(
                [
                    {
                        "Name": pet.name,
                        "Species": pet.species,
                        "Age": pet.age,
                        "Tasks": len(pet.tasks),
                    }
                    for pet in owner.pets
                ]
            )
        else:
            st.info("No pets yet. Add one to begin.")

    with col_b:
        st.markdown("### Schedule a Task")
        if owner.pets:
            with st.form("add_task_form", clear_on_submit=True):
                selected_pet = st.selectbox("Choose pet", [pet.name for pet in owner.pets])
                description = st.text_input("Task description")
                due_date_value = st.date_input("Due date", value=date.today())
                time_str = st.text_input("Time (HH:MM)", value="08:00")
                frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
                priority = st.selectbox("Priority", ["high", "medium", "low"])
                category = st.selectbox(
                    "Category",
                    ["feeding", "walk", "medication", "vet", "grooming", "play", "general"],
                )
                add_task_clicked = st.form_submit_button("Add task")

                if add_task_clicked:
                    pet = owner.get_pet(selected_pet)
                    if pet is None:
                        st.error("Select a valid pet.")
                    elif not description.strip():
                        st.error("Enter a task description.")
                    else:
                        try:
                            pet.add_task(
                                Task(
                                    description=description.strip(),
                                    time_str=time_str,
                                    due_date=due_date_value,
                                    frequency=frequency,
                                    priority=priority,
                                    category=category,
                                )
                            )
                        except ValueError:
                            st.error("Time must use 24-hour HH:MM format, such as 08:30.")
                        else:
                            rebuild_scheduler()
                            save_owner()
                            st.success(f"Added task for {selected_pet}.")
                            st.rerun()
        else:
            st.info("Add a pet first so tasks have somewhere to go.")

    st.divider()
    st.subheader("Today’s Schedule")
    todays_tasks = scheduler.todays_schedule()
    if todays_tasks:
        st.table(schedule_rows(todays_tasks))
    else:
        st.info("No tasks scheduled for today.")

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.markdown("### Conflict Warnings")
        for warning in conflicts:
            st.warning(warning)
    else:
        st.success("No scheduling conflicts detected.")

    next_slot = scheduler.next_available_slot()
    if next_slot:
        st.info(f"Next available exact slot today: {next_slot}")

    st.divider()
    st.subheader("Filter Tasks")

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        pet_filter = st.selectbox("Pet filter", ["All pets"] + [pet.name for pet in owner.pets])
    with filter_col2:
        status_filter = st.selectbox("Status filter", ["All", "Pending", "Completed"])
    with filter_col3:
        priority_filter = st.selectbox("Priority filter", ["All", "high", "medium", "low"])

    completed_filter = None
    if status_filter == "Pending":
        completed_filter = False
    elif status_filter == "Completed":
        completed_filter = True

    filtered_tasks = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed=completed_filter,
        priority=None if priority_filter == "All" else priority_filter,
    )

    if filtered_tasks:
        st.table(schedule_rows(scheduler.sort_by_priority_then_time(filtered_tasks)))
    else:
        st.info("No tasks match the current filters.")

    st.divider()
    st.subheader("Mark a Task Complete")

    incomplete_tasks = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    if incomplete_tasks:
        selected_task = st.selectbox(
            "Choose an incomplete task",
            incomplete_tasks,
            format_func=task_option_label,
        )
        if st.button("Mark selected task complete"):
            pet, task = selected_task
            was_updated = scheduler.mark_task_complete(
                pet.name,
                task.description,
                task.time_str,
                task.due_date,
            )
            if was_updated:
                save_owner()
                st.success("Task marked complete. Recurring tasks were advanced automatically if needed.")
                st.rerun()
            else:
                st.error("Task could not be updated.")
    else:
        st.info("There are no incomplete tasks right now.")

with ai_tab:
    st.subheader("Ask the AI Care Copilot")
    st.write(
        "This tab adds the new AI system behavior: multi-source retrieval, observable planning steps, prompt specialization, and reliability checks."
    )

    selected_example = st.selectbox("Sample prompt", EXAMPLE_PROMPTS)
    query = st.text_area("Ask a pet-care planning question", value=selected_example, height=120)
    specialized_mode = st.checkbox("Use specialized PawPal prompt", value=True)
    show_steps = st.checkbox("Show agent workflow steps", value=True)

    if st.button("Run AI Copilot"):
        response = copilot.ask(query=query, owner=owner, scheduler=scheduler, specialized_mode=specialized_mode)
        st.session_state.last_ai_response = response

    response = st.session_state.last_ai_response
    if response is not None:
        guardrail = response.guardrail
        grounding = response.grounding

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Backend", response.backend)
        metric_col2.metric("Grounding score", grounding.score if grounding else "n/a")
        metric_col3.metric("Valid citations", grounding.citation_count if grounding else "n/a")

        if guardrail and not guardrail.allow:
            st.error(f"Guardrail triggered: {guardrail.reason}")
        elif guardrail:
            st.success("Guardrail check passed.")

        st.markdown("### AI Answer")
        st.markdown(response.answer)

        if show_steps:
            st.markdown("### Observable Agent Workflow")
            for step in response.plan_steps:
                st.write(f"- {step}")

        st.markdown("### Retrieved Sources")
        if response.sources:
            for source in response.sources:
                st.code(f"[{source.source_id}] ({source.source_type}) {source.text}")
        else:
            st.info("No retrieval sources were used because a safety guardrail handled the request.")

        st.markdown("### Reliability Notes")
        if grounding:
            st.write(f"Passed grounding check: `{grounding.passed}`")
            st.write(f"Details: `{grounding.notes}`")

        st.markdown("### Suggested demo inputs")
        st.write("1. What should Luna and Milo do today?")
        st.write("2. Are there any conflicts in my schedule today?")
        st.write("3. My dog is vomiting blood. What dose should I give?")