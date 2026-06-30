import pawpal_systems


def main():
    # Owner has two pets: Rex (dog) and Whiskers (cat).
    tasks = [
        # Rex's tasks
        pawpal_systems.CareTask("Rex", "Morning walk", 30, 5, "exercise", True),
        pawpal_systems.CareTask("Rex", "Feed breakfast", 10, 5, "feeding", True),
        pawpal_systems.CareTask("Rex", "Brush coat", 15, 2, "grooming", False),
        # Whiskers's tasks
        pawpal_systems.CareTask("Whiskers", "Feed breakfast", 10, 5, "feeding", True),
        pawpal_systems.CareTask("Whiskers", "Clean litter box", 10, 4, "hygiene", True),
        pawpal_systems.CareTask("Whiskers", "Play with toy", 20, 3, "exercise", False),
    ]

    # Owner constraints: at most 90 minutes today, prefers exercise tasks.
    constraints = pawpal_systems.OwnerConstraints(
        max_time_minutes=90,
        preferred_categories=["exercise"],
    )

    engine = pawpal_systems.PetCare(tasks=tasks, constraints=constraints)

    plan, explanation = engine.generate_daily_plan()

    print("=== Daily Plan ===")
    for task in plan:
        print(
            f"- {task.time_range()}  {task.pet_name}: "
            f"{task.name} ({task.duration_mins} min)"
        )

    print("\n=== Explanation ===")
    print(explanation)

    # Filtering: every task belonging to one pet.
    print("\n=== Rex's tasks ===")
    for task in engine.tasks_for_pet("Rex"):
        print(f"- {task.name} ({task.category})")

    # Conflict detection: lightweight check returns a warning string (or empty).
    warning = engine.conflict_warning(plan)
    print("\n=== Conflict check ===")
    print(warning if warning else "No conflicts.")


if __name__ == "__main__":
    main()
