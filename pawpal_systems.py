from typing import Tuple


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
    ):
        """Initialize a care task with its pet, details, and scheduling metadata."""
        self.pet_name: str = pet_name
        self.name: str = name
        self.duration_mins: int = duration_mins
        self.priority: int = priority
        self.category: str = category
        self.is_mandatory: bool = is_mandatory
        self.status: str = "pending"

    def mark_complete(self) -> None:
        """Mark this task as complete."""
        self.status = "complete"


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


class OwnerConstraints:
    """Constraints and preferences the owner places on the daily plan."""

    def __init__(self, max_time_minutes: int, preferred_categories: list = None):
        """Initialize owner constraints with a time budget and preferred categories."""
        self.max_time_minutes: int = max_time_minutes
        self.preferred_categories: list = (
            preferred_categories if preferred_categories is not None else []
        )


class PetCare:
    """Main PawPal+ class. Holds the list of care tasks and the owner's constraints."""

    def __init__(self, tasks: list = None, constraints: OwnerConstraints = None):
        """Initialize the engine with a list of tasks and owner constraints."""
        self.tasks: list = tasks if tasks is not None else []
        self.constraints: OwnerConstraints = constraints

    def generate_daily_plan(self) -> Tuple[list, str]:
        """Build and explain a daily plan from self.tasks, respecting self.constraints.

        Scheduling rules:
          1. Mandatory tasks are always included, even if they exceed the time budget.
          2. Remaining time is filled with optional tasks, most important first.
             A task is ranked by priority (higher = more important); tasks whose
             category is in the owner's preferred_categories are favored as a
             tie/ranking boost.
          3. No task is added if it would push the total past max_time_minutes
             (mandatory tasks are the only exception).

        Returns a (plan, explanation) tuple:
          plan        -> list of scheduled CareTask objects, in the order to do them
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

        def rank(task: CareTask):
            # Sort key: preferred category first, then higher priority, then
            # shorter duration (so we can fit more in). Negatives => descending.
            is_preferred = 1 if task.category in preferred else 0
            return (-is_preferred, -task.priority, task.duration_mins)

        mandatory = [t for t in self.tasks if t.is_mandatory]
        optional = sorted(
            (t for t in self.tasks if not t.is_mandatory), key=rank
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

        explanation_lines.append(
            f"Total scheduled time: {total_minutes} min "
            f"across {len(plan)} task(s)."
        )

        return plan, "\n".join(explanation_lines)
