import os
import sys

# Allow importing pawpal_systems from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pawpal_systems


def make_task(
    name="Task",
    pet_name="Rex",
    duration_mins=30,
    priority=2,
    category="exercise",
    is_mandatory=False,
    recurrence="none",
    recur_days=None,
):
    """Build a CareTask with sensible defaults so tests only state what matters."""
    return pawpal_systems.CareTask(
        pet_name=pet_name,
        name=name,
        duration_mins=duration_mins,
        priority=priority,
        category=category,
        is_mandatory=is_mandatory,
        recurrence=recurrence,
        recur_days=recur_days,
    )


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


# ---------------------------------------------------------------------------
# 1. generate_daily_plan — the core engine
# ---------------------------------------------------------------------------
def test_plan_orders_optional_by_rank():
    """Optional tasks are ranked: preferred category, then priority, then shorter."""
    constraints = pawpal_systems.OwnerConstraints(
        max_time_minutes=1000, preferred_categories=["grooming"]
    )
    low = make_task(name="low", duration_mins=10, priority=1, category="exercise")
    high = make_task(name="high", duration_mins=10, priority=3, category="exercise")
    preferred = make_task(
        name="preferred", duration_mins=10, priority=1, category="grooming"
    )
    engine = pawpal_systems.PetCare([low, high, preferred], constraints)

    plan, _ = engine.generate_daily_plan()

    # Preferred category wins outright, then higher priority beats lower.
    assert [t.name for t in plan] == ["preferred", "high", "low"]


def test_plan_schedules_mandatory_before_optional_and_packs_back_to_back():
    """Mandatory tasks come first, then tasks are placed back-to-back from day start."""
    constraints = pawpal_systems.OwnerConstraints(
        max_time_minutes=1000, day_start_min=480
    )
    mandatory = make_task(name="m", duration_mins=20, is_mandatory=True)
    optional = make_task(name="o", duration_mins=30, is_mandatory=False)
    engine = pawpal_systems.PetCare([optional, mandatory], constraints)

    plan, _ = engine.generate_daily_plan()

    assert [t.name for t in plan] == ["m", "o"]
    assert plan[0].start_min == 480
    assert plan[0].time_range() == "08:00-08:20"
    # Second task starts exactly where the first ended (no gap, no overlap).
    assert plan[1].start_min == 500
    assert plan[1].time_range() == "08:20-08:50"


def test_plan_with_no_tasks_returns_empty_plan_and_no_day_line():
    """Edge: an owner/pet with no tasks yields an empty plan and never crashes."""
    constraints = pawpal_systems.OwnerConstraints(max_time_minutes=120)
    engine = pawpal_systems.PetCare([], constraints)

    plan, explanation = engine.generate_daily_plan()

    assert plan == []
    # The "Day runs ..." line is guarded by `if plan:` so it must be absent.
    assert "Day runs" not in explanation
    assert "across 0 task(s)" in explanation


def test_mandatory_tasks_exceed_budget_are_still_all_scheduled():
    """Rule 2: mandatory tasks are always included even past the time budget."""
    constraints = pawpal_systems.OwnerConstraints(max_time_minutes=30)
    m1 = make_task(name="m1", duration_mins=40, is_mandatory=True)
    m2 = make_task(name="m2", duration_mins=40, is_mandatory=True)
    optional = make_task(name="o", duration_mins=5, is_mandatory=False)
    engine = pawpal_systems.PetCare([m1, m2, optional], constraints)

    plan, explanation = engine.generate_daily_plan()

    # Both mandatory tasks are present; the optional one cannot fit anymore.
    assert {t.name for t in plan} == {"m1", "m2"}
    assert "exceeds" in explanation


def test_optional_task_equal_to_remaining_budget_is_included():
    """Boundary: a task whose duration exactly fills remaining time fits (<=)."""
    constraints = pawpal_systems.OwnerConstraints(max_time_minutes=30)
    exact = make_task(name="exact", duration_mins=30, is_mandatory=False)
    engine = pawpal_systems.PetCare([exact], constraints)

    plan, _ = engine.generate_daily_plan()

    assert [t.name for t in plan] == ["exact"]


def test_optional_task_one_minute_over_budget_is_skipped():
    """Boundary: one minute past the budget is rejected."""
    constraints = pawpal_systems.OwnerConstraints(max_time_minutes=30)
    over = make_task(name="over", duration_mins=31, is_mandatory=False)
    engine = pawpal_systems.PetCare([over], constraints)

    plan, explanation = engine.generate_daily_plan()

    assert plan == []
    assert "Skipped" in explanation


def test_plan_without_constraints_uses_defaults_and_unlimited_budget():
    """No constraints => infinite budget and default 08:00 day start."""
    engine = pawpal_systems.PetCare([make_task(duration_mins=600)], constraints=None)

    plan, _ = engine.generate_daily_plan()

    assert len(plan) == 1
    assert plan[0].start_min == pawpal_systems.DEFAULT_DAY_START_MIN


def test_regenerating_plan_clears_stale_start_min_on_dropped_tasks():
    """A task excluded from a new plan must have its start_min reset to None."""
    constraints = pawpal_systems.OwnerConstraints(max_time_minutes=20)
    kept = make_task(name="kept", duration_mins=20, is_mandatory=True)
    dropped = make_task(name="dropped", duration_mins=20, is_mandatory=False)
    engine = pawpal_systems.PetCare([kept, dropped], constraints)

    # First plan schedules `kept`; `dropped` does not fit.
    engine.generate_daily_plan()
    assert kept.start_min is not None
    assert dropped.start_min is None

    # Manually dirty the dropped task, then regenerate — it must be cleared.
    dropped.start_min = 999
    engine.generate_daily_plan()
    assert dropped.start_min is None


# ---------------------------------------------------------------------------
# 2. Recurrence filtering
# ---------------------------------------------------------------------------
def test_occurs_on_none_and_daily_always_run():
    none_task = make_task(recurrence="none")
    daily_task = make_task(recurrence="daily")
    for weekday in range(7):
        assert none_task.occurs_on(weekday) is True
        assert daily_task.occurs_on(weekday) is True


def test_occurs_on_weekly_only_runs_on_listed_days():
    weekly = make_task(recurrence="weekly", recur_days=[2])
    assert weekly.occurs_on(2) is True
    assert weekly.occurs_on(3) is False


def test_weekly_task_with_empty_recur_days_is_excluded_every_day():
    """Edge: a weekly task with no assigned days never appears in any daily plan."""
    constraints = pawpal_systems.OwnerConstraints(max_time_minutes=120)
    weekly = make_task(name="weekly", recurrence="weekly")  # recur_days defaults to []
    engine = pawpal_systems.PetCare([weekly], constraints)

    for weekday in range(7):
        plan, _ = engine.generate_daily_plan(weekday=weekday)
        assert plan == []


def test_weekday_none_skips_recurrence_filter():
    """weekday=None considers every task regardless of recurrence days."""
    constraints = pawpal_systems.OwnerConstraints(max_time_minutes=120)
    weekly = make_task(name="weekly", recurrence="weekly", recur_days=[0])
    engine = pawpal_systems.PetCare([weekly], constraints)

    plan, _ = engine.generate_daily_plan(weekday=None)

    assert [t.name for t in plan] == ["weekly"]


# ---------------------------------------------------------------------------
# 3. find_conflicts / conflict_warning
# ---------------------------------------------------------------------------
def _scheduled(name, start_min, duration_mins):
    task = make_task(name=name, duration_mins=duration_mins)
    task.start_min = start_min
    return task


def test_back_to_back_tasks_do_not_conflict():
    """Half-open intervals: b.start == a.end is NOT an overlap."""
    a = _scheduled("a", 480, 20)
    b = _scheduled("b", 500, 20)
    assert pawpal_systems.PetCare.find_conflicts([a, b]) == []


def test_tasks_at_same_start_time_conflict():
    """Edge: two tasks at the exact same time overlap."""
    a = _scheduled("a", 480, 20)
    b = _scheduled("b", 480, 20)
    conflicts = pawpal_systems.PetCare.find_conflicts([a, b])
    assert len(conflicts) == 1


def test_three_overlapping_tasks_report_all_pairs():
    """An early break must not drop the (b, c) pair when all three overlap."""
    a = _scheduled("a", 480, 60)
    b = _scheduled("b", 490, 60)
    c = _scheduled("c", 500, 60)
    conflicts = pawpal_systems.PetCare.find_conflicts([a, b, c])
    assert len(conflicts) == 3


def test_find_conflicts_skips_unscheduled_tasks():
    a = _scheduled("a", 480, 20)
    unscheduled = make_task(name="u", duration_mins=20)  # start_min is None
    assert pawpal_systems.PetCare.find_conflicts([a, unscheduled]) == []


def test_conflict_warning_flags_overlap():
    a = _scheduled("a", 480, 30)
    b = _scheduled("b", 490, 30)
    engine = pawpal_systems.PetCare([a, b])
    warning = engine.conflict_warning()
    assert "overlaps" in warning


def test_conflict_warning_flags_mandatory_over_budget():
    """The one clash a back-to-back plan can still produce: mandatory > budget."""
    constraints = pawpal_systems.OwnerConstraints(max_time_minutes=30)
    m = make_task(name="m", duration_mins=60, is_mandatory=True)
    engine = pawpal_systems.PetCare([m], constraints)
    warning = engine.conflict_warning([m])
    assert "budget" in warning


def test_conflict_warning_never_raises_on_malformed_task():
    """Graceful degradation: a broken task yields a message, not an exception."""
    broken = make_task(name="broken", duration_mins=None)
    broken.start_min = 480  # scheduled but end_min() will fail on None duration
    other = _scheduled("other", 480, 20)
    engine = pawpal_systems.PetCare([broken, other])
    warning = engine.conflict_warning()
    assert warning.startswith("Could not fully check")


def test_conflict_warning_empty_when_no_problems():
    a = _scheduled("a", 480, 20)
    b = _scheduled("b", 500, 20)
    engine = pawpal_systems.PetCare([a, b])
    assert engine.conflict_warning() == ""


# ---------------------------------------------------------------------------
# 4. sort_by_time
# ---------------------------------------------------------------------------
def test_sort_by_time_orders_scheduled_and_pushes_unscheduled_last():
    later = _scheduled("later", 600, 20)
    earlier = _scheduled("earlier", 480, 20)
    unscheduled = make_task(name="unscheduled")
    ordered = pawpal_systems.PetCare.sort_by_time([later, unscheduled, earlier])
    assert [t.name for t in ordered] == ["earlier", "later", "unscheduled"]


def test_sort_by_time_midnight_task_sorts_before_unscheduled():
    """Edge: start_min == 0 must not be treated like None (the `or 0` trap)."""
    midnight = _scheduled("midnight", 0, 20)
    unscheduled = make_task(name="unscheduled")
    ordered = pawpal_systems.PetCare.sort_by_time([unscheduled, midnight])
    assert [t.name for t in ordered] == ["midnight", "unscheduled"]


# ---------------------------------------------------------------------------
# Rubric requirement: Sorting Correctness — chronological order
# ---------------------------------------------------------------------------
def test_sorting_returns_tasks_in_chronological_order():
    """Scheduled tasks come back ordered earliest start time first."""
    nine_am = _scheduled("9am", 540, 30)
    eight_am = _scheduled("8am", 480, 30)
    noon = _scheduled("noon", 720, 30)

    ordered = pawpal_systems.PetCare.sort_by_time([noon, nine_am, eight_am])

    # Chronological: 08:00, then 09:00, then 12:00.
    assert [t.start_min for t in ordered] == [480, 540, 720]
    assert [t.name for t in ordered] == ["8am", "9am", "noon"]


# ---------------------------------------------------------------------------
# Rubric requirement: Recurrence Logic — completing a daily task rolls over
# ---------------------------------------------------------------------------
def test_completing_daily_task_creates_followup_for_next_day():
    """Marking a daily task complete enqueues a fresh task for the next day."""
    daily = make_task(name="Morning walk", recurrence="daily")
    engine = pawpal_systems.PetCare([daily])

    follow_up = engine.complete_task(daily)

    # The original task is now done.
    assert daily.status == "complete"
    # A brand-new occurrence was created for the following day...
    assert follow_up is not None
    assert follow_up is not daily          # a distinct object, not the same one
    assert follow_up.status == "pending"   # ...and it starts fresh as pending.
    assert follow_up.name == "Morning walk"
    assert follow_up.recurrence == "daily"
    # The follow-up was added to the scheduler's task list (2 tasks total now).
    assert follow_up in engine.tasks
    assert len(engine.tasks) == 2


def test_completing_non_recurring_task_creates_no_followup():
    """A one-off ("none") task does not regenerate when completed."""
    one_off = make_task(name="Vet visit", recurrence="none")
    engine = pawpal_systems.PetCare([one_off])

    follow_up = engine.complete_task(one_off)

    assert one_off.status == "complete"
    assert follow_up is None
    assert len(engine.tasks) == 1


# ---------------------------------------------------------------------------
# Rubric requirement: Conflict Detection — flag duplicate times
# ---------------------------------------------------------------------------
def test_scheduler_flags_tasks_at_duplicate_times():
    """Two tasks scheduled at the same start time are reported as a conflict."""
    a = _scheduled("a", 480, 30)
    b = _scheduled("b", 480, 30)  # same start time as `a` => duplicate
    engine = pawpal_systems.PetCare([a, b])

    conflicts = pawpal_systems.PetCare.find_conflicts([a, b])
    assert len(conflicts) == 1
    assert set(conflicts[0]) == {a, b}

    # The human-readable warning surfaces the clash too.
    assert "overlaps" in engine.conflict_warning()


# ---------------------------------------------------------------------------
# 5. format_time / time_range
# ---------------------------------------------------------------------------
def test_format_time_basic_values():
    assert pawpal_systems.format_time(0) == "00:00"
    assert pawpal_systems.format_time(480) == "08:00"
    assert pawpal_systems.format_time(1439) == "23:59"


def test_format_time_wraps_past_midnight():
    """The `% 24` makes times past 24h wrap around."""
    assert pawpal_systems.format_time(1440) == "00:00"
    assert pawpal_systems.format_time(1500) == "01:00"


def test_time_range_unscheduled():
    assert make_task().time_range() == "unscheduled"


# ---------------------------------------------------------------------------
# 6. Filtering helpers
# ---------------------------------------------------------------------------
def test_tasks_for_pet_and_by_recurrence_and_status():
    rex_walk = make_task(name="walk", pet_name="Rex", recurrence="daily")
    mochi_feed = make_task(name="feed", pet_name="Mochi", recurrence="weekly")
    mochi_feed.mark_complete()
    engine = pawpal_systems.PetCare([rex_walk, mochi_feed])

    assert engine.tasks_for_pet("Rex") == [rex_walk]
    assert engine.tasks_by_recurrence("weekly") == [mochi_feed]
    assert engine.tasks_by_status("complete") == [mochi_feed]
    assert engine.tasks_by_status("pending") == [rex_walk]
