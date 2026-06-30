import os
import sys

# Allow importing pawpal_systems from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pawpal_systems


def test_mark_complete_changes_status():
    """Task Completion: calling mark_complete() changes the task's status."""
    task = pawpal_systems.CareTask(
        pet_name="Rex",
        name="Morning walk",
        duration_mins=30,
        priority=5,
        category="exercise",
        is_mandatory=True,
    )

    # A new task starts out pending.
    assert task.status == "pending"

    task.mark_complete()

    # After marking complete, the status has changed.
    assert task.status == "complete"


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet increases that pet's task count."""
    pet = pawpal_systems.Pet(name="Whiskers", species="cat")

    # A new pet has no tasks yet.
    assert pet.task_count() == 0

    task = pawpal_systems.CareTask(
        pet_name="Whiskers",
        name="Clean litter box",
        duration_mins=10,
        priority=4,
        category="hygiene",
        is_mandatory=True,
    )
    pet.add_task(task)

    # The count increased by one.
    assert pet.task_count() == 1

    # Adding another task increases it again.
    pet.add_task(
        pawpal_systems.CareTask(
            pet_name="Whiskers",
            name="Play with toy",
            duration_mins=20,
            priority=3,
            category="exercise",
            is_mandatory=False,
        )
    )
    assert pet.task_count() == 2
