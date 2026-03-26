import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
PawPal+ helps a pet owner build a daily pet care plan based on time available,
task priority, and preferred time of day.
"""
)

st.divider()

st.subheader("Owner + Pet Info")
owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available time today (minutes)", min_value=10, max_value=480, value=120)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Tasks")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

preferred_time = st.selectbox("Preferred time", ["morning", "afternoon", "evening", "anytime"])

if st.button("Add task"):
    st.session_state.tasks.append(
        {
            "title": task_title,
            "duration_minutes": int(duration),
            "priority": priority,
            "preferred_time": preferred_time,
        }
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    owner = Owner(owner_name, available_minutes=available_minutes)
    pet = Pet(pet_name, species)

    for item in st.session_state.tasks:
        pet.add_task(
            Task(
                title=item["title"],
                duration_minutes=item["duration_minutes"],
                priority=item["priority"],
                preferred_time=item["preferred_time"],
            )
        )

    scheduler = Scheduler(owner, pet)
    plan = scheduler.build_daily_plan()
    explanations = scheduler.explain_plan(plan)

    if not plan:
        st.warning("No tasks fit inside the available time.")
    else:
        st.success("Daily schedule generated.")

        plan_rows = []
        for task in plan:
            plan_rows.append(
                {
                    "Task": task.title,
                    "Duration": task.duration_minutes,
                    "Priority": task.priority,
                    "Preferred Time": task.preferred_time,
                }
            )

        st.markdown("### Planned Tasks")
        st.table(plan_rows)

        st.markdown("### Why this plan was chosen")
        for reason in explanations:
            st.write(f"- {reason}")