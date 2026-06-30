import streamlit as st
import pawpal_systems
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="")

# --- Persist the Owner across reruns -------------------------------------
# Streamlit reruns this whole script on every interaction. Without this
# "get-or-create" guard, a fresh (empty) Owner would be made every time and
# all added pets/tasks would be lost. We create the Owner ONCE and store it in
# st.session_state (the "vault"), then reuse the same object on later reruns.
if "owner" not in st.session_state:
    st.session_state.owner = pawpal_systems.Owner(owner_name)

owner = st.session_state.owner
# Keep the name in sync with the input box (the object itself still persists).
owner.name = owner_name

# Maps the friendly priority labels in the UI to the integer priorities the
# scheduler expects (higher number = more important).
PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}

# Weekday labels in scheduler order (index 0 = Monday … 6 = Sunday). Used both
# to collect a weekly task's days and to build the week-long schedule.
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

st.divider()

# --- Add a Pet -----------------------------------------------------------
st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name", value="")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted and pet_name:
    # Owner.add_pet() handles the submitted data and stores it on the
    # persisted owner. The rerun below then re-renders from owner.pets.
    owner.add_pet(pawpal_systems.Pet(pet_name, species))
    st.success(f"Added {pet_name} ({species}).")

if owner.pets:
    st.write(f"**{owner.name}'s pets ({owner.pet_count()}):**")
    for pet in owner.pets:
        st.write(f"- {pet.name} ({pet.species}) — {pet.task_count()} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Schedule a Task -----------------------------------------------------
st.subheader("Add a Task")
if not owner.pets:
    st.info("Add a pet first, then you can assign tasks to it.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_choice = st.selectbox("For which pet?", [p.name for p in owner.pets])
        task_title = st.text_input("Task title", value="")
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        category = st.selectbox(
            "Category", ["exercise", "feeding", "grooming", "hygiene", "other"]
        )
        recurrence = st.selectbox("Recurrence", ["daily", "weekly"])
        is_mandatory = st.checkbox("Mandatory", value=False)
        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted and task_title:
        # Find the selected pet on the persisted owner, build a CareTask, and
        # let Pet.add_task() handle attaching it. A weekly task's day is chosen
        # automatically when the schedule is built (see Build Weekly Schedule).
        target_pet = next(p for p in owner.pets if p.name == pet_choice)
        target_pet.add_task(
            pawpal_systems.CareTask(
                pet_name=target_pet.name,
                name=task_title,
                duration_mins=int(duration),
                priority=PRIORITY_MAP[priority],
                category=category,
                is_mandatory=is_mandatory,
                recurrence=recurrence,
            )
        )
        st.success(f"Added '{task_title}' to {pet_choice}.")

# Show every task across all pets, with optional filtering by pet.
all_tasks = owner.all_tasks()
if all_tasks:
    st.write("Current tasks:")

    # Filter control. We reuse PetCare's filter helper so the UI and the engine
    # agree on what "tasks for a pet" means.
    catalog = pawpal_systems.PetCare(all_tasks)
    pet_filter = st.selectbox(
        "Filter by pet", ["All"] + [p.name for p in owner.pets]
    )

    filtered = all_tasks
    if pet_filter != "All":
        filtered = catalog.tasks_for_pet(pet_filter)

    st.table(
        [
            {
                "pet": t.pet_name,
                "task": t.name,
                "minutes": t.duration_mins,
                "priority": t.priority,
                "category": t.category,
                "recurrence": t.recurrence,
                "day": WEEKDAYS[t.recur_days[0]] if t.recur_days else "—",
                "mandatory": t.is_mandatory,
            }
            for t in filtered
        ]
    )

st.divider()

# --- Build Weekly Schedule -----------------------------------------------
st.subheader("Build Weekly Schedule")
max_time = st.number_input(
    "Time budget per day (minutes)", min_value=1, max_value=1440, value=120
)

if st.button("Generate weekly schedule"):
    if not all_tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        # Give the owner constraints, then build one plan per weekday. Daily and
        # one-off tasks appear every day; a weekly task appears only on its
        # chosen day. Each day's tasks are packed against that day's budget.
        owner.constraints = pawpal_systems.OwnerConstraints(int(max_time))
        engine = pawpal_systems.PetCare(owner.all_tasks(), owner.constraints)

        # Auto-assign each weekly task a weekday, spread round-robin across the
        # week so they don't all pile onto the same day.
        weekly_tasks = [t for t in engine.tasks if t.recurrence == "weekly"]
        for i, task in enumerate(weekly_tasks):
            task.recur_days = [i % len(WEEKDAYS)]

        for index, day_name in enumerate(WEEKDAYS):
            plan, explanation = engine.generate_daily_plan(weekday=index)
            with st.expander(
                f"{day_name} — {len(plan)} task(s)", expanded=(index == 0)
            ):
                if not plan:
                    st.caption("No tasks scheduled for this day.")
                else:
                    for task in plan:
                        st.write(
                            f"- `{task.time_range()}` **{task.pet_name}**: "
                            f"{task.name} ({task.duration_mins} min)"
                        )

                    # Lightweight conflict check — returns a warning string and
                    # never raises, so a clash shows a message, not a crash.
                    warning = engine.conflict_warning(plan)
                    if warning:
                        st.warning(warning)

                    st.text(explanation)
