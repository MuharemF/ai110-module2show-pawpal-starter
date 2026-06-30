from typing import List, Tuple

# Where the scheduler starts placing tasks when no day start is given (08:00).
DEFAULT_DAY_START_MIN: int = 8 * 60

# Allowed recurrence values for a CareTask.
RECURRENCES = ("none", "daily", "weekly")


def format_time(total_min: int) -> str:
    """Convert minutes-since-midnight into a 24-hour ``HH:MM`` string."""
    hours, minutes = divmod(int(total_min), 60)
    return f"{hours % 24:02d}:{minutes:02d}"


class CareTask:
    """A single pet care task to be scheduled."""

    def __init__(
        self,
        pet_name: str,
        name: str,
        duration_mins: int,
        priority: int,
        category: str,
        is_mandatory: bool,
        recurrence: str = "none",
        recur_days: list = None,
    ):
        """Initialize a care task with its pet, details, and scheduling metadata.

        recurrence  -> "none", "daily", or "weekly".
        recur_days  -> for weekly tasks, the weekdays it runs on as ints
                       (0 = Monday … 6 = Sunday). Ignored for other recurrences.
        """
        self.pet_name: str = pet_name
        self.name: str = name
        self.duration_mins: int = duration_mins
        self.priority: int = priority
        self.category: str = category
        self.is_mandatory: bool = is_mandatory
        self.recurrence: str = recurrence
        self.recur_days: list = recur_days if recur_days is not None else []
        self.status: str = "pending"
        # Filled in by the scheduler once the task is placed in a plan. Stored as
        # minutes since midnight (None means "not yet scheduled").
        self.start_min: int = None

    def mark_complete(self) -> None:
        """Mark this task as complete."""
        self.status = "complete"

    def end_min(self):
        """Return the task's finish time (minutes since midnight), or None."""
        if self.start_min is None:
            return None
        return self.start_min + self.duration_mins

    def time_range(self) -> str:
        """Return a 'HH:MM-HH:MM' label once scheduled, else 'unscheduled'."""
        if self.start_min is None:
            return "unscheduled"
        return f"{format_time(self.start_min)}-{format_time(self.end_min())}"

    def occurs_on(self, weekday: int) -> bool:
        """Return whether this task should run on the given weekday (0=Mon).

        "none" and "daily" tasks always run; "weekly" tasks run only on the
        weekdays listed in recur_days.
        """
        if self.recurrence == "weekly":
            return weekday in self.recur_days
        return True


class Pet:
    """A pet owned by the user, holding its own list of care tasks."""

    def __init__(self, name: str, species: str = ""):
        """Initialize a pet with a name, optional species, and empty task list."""
        self.name: str = name
        self.species: str = species
        self.tasks: list = []

    def add_task(self, task: "CareTask") -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def task_count(self) -> int:
        """Return the number of tasks assigned to this pet."""
        return len(self.tasks)


class Owner:
    """A pet owner, holding their pets and care constraints."""

    def __init__(self, name: str, constraints: "OwnerConstraints" = None):
        """Initialize an owner with a name, empty pet list, and optional constraints."""
        self.name: str = name
        self.pets: list = []
        self.constraints: "OwnerConstraints" = constraints

    def add_pet(self, pet: "Pet") -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def pet_count(self) -> int:
        """Return the number of pets this owner has."""
        return len(self.pets)

    def all_tasks(self) -> list:
        """Return every care task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class OwnerConstraints:
    """Constraints and preferences the owner places on the daily plan."""

    def __init__(
        self,
        max_time_minutes: int,
        preferred_categories: list = None,
        day_start_min: int = DEFAULT_DAY_START_MIN,
    ):
        """Initialize owner constraints with a time budget and preferred categories.

        day_start_min is when the scheduler begins placing tasks, expressed as
        minutes since midnight (defaults to 08:00).
        """
        self.max_time_minutes: int = max_time_minutes
        self.preferred_categories: list = (
            preferred_categories if preferred_categories is not None else []
        )
        self.day_start_min: int = day_start_min


class PetCare:
    """Main PawPal+ class. Holds the list of care tasks and the owner's constraints."""

    def __init__(self, tasks: list = None, constraints: OwnerConstraints = None):
        """Initialize the engine with a list of tasks and owner constraints."""
        self.tasks: list = tasks if tasks is not None else []
        self.constraints: OwnerConstraints = constraints

    # --- Filtering -------------------------------------------------------
    def tasks_for_pet(self, pet_name: str) -> list:
        """Return all tasks belonging to the given pet."""
        return [t for t in self.tasks if t.pet_name == pet_name]

    def tasks_by_status(self, status: str) -> list:
        """Return all tasks with the given status ('pending' or 'complete')."""
        return [t for t in self.tasks if t.status == status]

    def tasks_by_recurrence(self, recurrence: str) -> list:
        """Return all tasks with the given recurrence ('none'/'daily'/'weekly')."""
        return [t for t in self.tasks if t.recurrence == recurrence]

    # --- Sorting ---------------------------------------------------------
    @staticmethod
    def sort_by_time(tasks: list) -> list:
        """Return tasks ordered by scheduled start time; unscheduled ones last."""
        return sorted(
            tasks, key=lambda t: (t.start_min is None, t.start_min or 0)
        )

    # --- Conflict detection ---------------------------------------------
    @staticmethod
    def find_conflicts(tasks: list) -> List[Tuple["CareTask", "CareTask"]]:
        """Find pairs of scheduled tasks whose time windows overlap.

        The owner can only do one task at a time, so any two tasks whose
        ``[start_min, end_min)`` ranges overlap are in conflict. Unscheduled
        tasks (``start_min is None``) are skipped. Returns a list of
        ``(task_a, task_b)`` pairs ordered by start time.

        Note: ``generate_daily_plan`` packs tasks back-to-back, so a generated
        plan never contains overlaps. This stays a reusable check for plans
        built another way (e.g. hand-assigned or merged from several sources).
        """
        scheduled = sorted(
            (t for t in tasks if t.start_min is not None),
            key=lambda t: t.start_min,
        )
        conflicts: list = []
        for i, a in enumerate(scheduled):
            for b in scheduled[i + 1:]:
                if b.start_min >= a.end_min():
                    # Sorted by start, so no later task can overlap `a` either.
                    break
                conflicts.append((a, b))
        return conflicts

    def conflict_warning(self, tasks: list = None) -> str:
        """Lightweight conflict check that returns a warning string, never raises.

        Designed for graceful degradation: instead of raising on a clash (which
        would force every caller into a try/except and risk crashing the app),
        this always returns a plain string — empty when everything is fine, or a
        human-readable warning otherwise. Callers just do ``if warning:``.

        It reports two kinds of trouble:
          * time-window overlaps between scheduled tasks (via find_conflicts), and
          * mandatory tasks whose total time exceeds the owner's budget — the one
            clash that can still happen once tasks are packed back-to-back.

        Even malformed task data degrades to a best-effort message rather than
        propagating an exception.
        """
        if tasks is None:
            tasks = self.tasks

        messages: list = []
        try:
            for a, b in self.find_conflicts(tasks):
                messages.append(
                    f"'{a.name}' ({a.time_range()}) overlaps "
                    f"'{b.name}' ({b.time_range()})"
                )

            if self.constraints is not None:
                mandatory_total = sum(
                    t.duration_mins for t in tasks if t.is_mandatory
                )
                budget = self.constraints.max_time_minutes
                if mandatory_total > budget:
                    messages.append(
                        f"mandatory tasks need {mandatory_total} min but the "
                        f"budget is only {budget} min"
                    )
        except Exception as exc:  # never crash the caller over a conflict check
            return f"Could not fully check for conflicts: {exc}"

        if not messages:
            return ""
        return "Possible conflict(s): " + "; ".join(messages) + "."

    def generate_daily_plan(self, weekday: int = None) -> Tuple[list, str]:
        """Build and explain a daily plan from self.tasks, respecting self.constraints.

        Scheduling rules:
          1. If weekday (0=Mon … 6=Sun) is given, weekly tasks not scheduled
             for that day are dropped first; "none"/"daily" tasks always apply.
          2. Mandatory tasks are always included, even if they exceed the time budget.
          3. Remaining time is filled with optional tasks, most important first.
             A task is ranked by priority (higher = more important); tasks whose
             category is in the owner's preferred_categories are favored as a
             tie/ranking boost.
          4. No task is added if it would push the total past max_time_minutes
             (mandatory tasks are the only exception).
          5. Selected tasks are placed back-to-back starting at the owner's
             day_start_min, giving each a concrete start_min (and a clock time).

        Returns a (plan, explanation) tuple:
          plan        -> list of scheduled CareTask objects, in time order
          explanation -> human-readable string describing the choices made
        """
        max_minutes = (
            self.constraints.max_time_minutes
            if self.constraints is not None
            else float("inf")
        )
        preferred = (
            self.constraints.preferred_categories
            if self.constraints is not None
            else []
        )
        day_start = (
            self.constraints.day_start_min
            if self.constraints is not None
            else DEFAULT_DAY_START_MIN
        )

        def rank(task: CareTask):
            # Sort key: preferred category first, then higher priority, then
            # shorter duration (so we can fit more in). Negatives => descending.
            is_preferred = 1 if task.category in preferred else 0
            return (-is_preferred, -task.priority, task.duration_mins)

        # 0. Recurrence filter: only keep tasks that occur on the chosen day.
        if weekday is None:
            candidates = self.tasks
        else:
            candidates = [t for t in self.tasks if t.occurs_on(weekday)]

        mandatory = [t for t in candidates if t.is_mandatory]
        optional = sorted(
            (t for t in candidates if not t.is_mandatory), key=rank
        )

        plan: list = []
        total_minutes = 0
        explanation_lines: list = []

        # 1. Always schedule mandatory tasks.
        for task in mandatory:
            plan.append(task)
            total_minutes += task.duration_mins
            explanation_lines.append(
                f"Included '{task.name}' for {task.pet_name} "
                f"({task.duration_mins} min) — mandatory."
            )

        if total_minutes > max_minutes:
            explanation_lines.append(
                f"Note: mandatory tasks total {total_minutes} min, which exceeds "
                f"the {max_minutes} min budget."
            )

        # 2. Fill remaining time with the most important optional tasks.
        for task in optional:
            if total_minutes + task.duration_mins <= max_minutes:
                plan.append(task)
                total_minutes += task.duration_mins
                reason = (
                    "preferred category"
                    if task.category in preferred
                    else f"priority {task.priority}"
                )
                explanation_lines.append(
                    f"Included '{task.name}' for {task.pet_name} "
                    f"({task.duration_mins} min) — {reason}."
                )
            else:
                explanation_lines.append(
                    f"Skipped '{task.name}' for {task.pet_name} "
                    f"({task.duration_mins} min) — not enough time remaining."
                )

        # 3. Auto-assign clock times: pack the plan back-to-back from day_start.
        #    This also leaves the plan in time order for free.
        cursor = day_start
        for task in plan:
            task.start_min = cursor
            cursor += task.duration_mins

        # Tasks left out of the plan are not scheduled today; clear any stale time.
        scheduled_ids = {id(t) for t in plan}
        for task in self.tasks:
            if id(task) not in scheduled_ids:
                task.start_min = None

        explanation_lines.append(
            f"Total scheduled time: {total_minutes} min "
            f"across {len(plan)} task(s)."
        )
        if plan:
            explanation_lines.append(
                f"Day runs {format_time(day_start)}-{format_time(cursor)}."
            )

        return plan, "\n".join(explanation_lines)
