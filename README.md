# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:
=== Daily Plan ===
- Rex: Morning walk (30 min)
- Rex: Feed breakfast (10 min)
- Whiskers: Feed breakfast (10 min)
- Whiskers: Clean litter box (10 min)
- Whiskers: Play with toy (20 min)

=== Explanation ===
Included 'Morning walk' for Rex (30 min) � mandatory.
Included 'Feed breakfast' for Rex (10 min) � mandatory.
Included 'Feed breakfast' for Whiskers (10 min) � mandatory.
Included 'Clean litter box' for Whiskers (10 min) � mandatory.
Included 'Play with toy' for Whiskers (20 min) � preferred category.
Skipped 'Brush coat' for Rex (15 min) � not enough time remaining.
Total scheduled time: 80 min across 5 task(s).

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## ✨ Features

PawPal+ implements the following scheduling algorithms, all in `pawpal_systems.py`:

- **Constraint-aware daily planning** — `PetCare.generate_daily_plan()` builds a
  one-day plan that always includes every **mandatory** task (even if it blows the
  time budget), then greedily fills the owner's remaining time with the most
  important **optional** tasks.
- **Priority & preference ranking** — optional tasks are ordered by a three-part
  key: the owner's **preferred categories** first, then higher **priority**, then
  shorter **duration** (so more tasks fit). Ties break deterministically.
- **Time-budget filling** — a task is added only if it fits within
  `max_time_minutes`; otherwise it is skipped and the reason is recorded.
- **Automatic time assignment** — selected tasks are packed **back-to-back** from
  the owner's `day_start_min`, giving each a concrete start/end (`08:00–08:30`).
- **Sorting by time** — `PetCare.sort_by_time()` returns tasks in chronological
  order, with any unscheduled tasks pushed to the end.
- **Conflict detection** — `PetCare.find_conflicts()` flags any two scheduled
  tasks whose `[start, end)` windows overlap (back-to-back tasks do **not**
  conflict; identical start times **do**).
- **Conflict warnings** — `PetCare.conflict_warning()` returns a human-readable
  warning string (never raises), covering both time overlaps and the case where
  mandatory tasks exceed the time budget.
- **Daily & weekly recurrence** — tasks recur `daily` or `weekly`;
  `CareTask.occurs_on(weekday)` decides whether a task runs on a given day, and
  `generate_daily_plan(weekday=...)` filters the plan accordingly.
- **Recurrence roll-over** — `PetCare.complete_task()` marks a task complete and,
  for recurring tasks, enqueues a fresh pending occurrence for the following day
  (via `CareTask.next_occurrence()`).
- **Filtering** — tasks can be filtered by pet (`tasks_for_pet`), by status
  (`tasks_by_status`), or by recurrence (`tasks_by_recurrence`).
- **Plain-language explanations** — every plan returns an explanation string
  describing why each task was included, skipped, or flagged.

### Method reference

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Daily plan generation | `PetCare.generate_daily_plan(weekday=None)` | Mandatory-first, then greedy optional fill within the time budget |
| Task ranking | `generate_daily_plan` (internal `rank`) | Preferred category → higher priority → shorter duration |
| Sorting by time | `PetCare.sort_by_time(tasks)` | Chronological; unscheduled tasks sorted last |
| Conflict detection | `PetCare.find_conflicts(tasks)` | Overlapping `[start, end)` windows; identical start times conflict |
| Conflict warnings | `PetCare.conflict_warning(tasks=None)` | Returns a warning string, never raises; also flags mandatory-over-budget |
| Recurrence check | `CareTask.occurs_on(weekday)` | `daily`/`none` always run; `weekly` runs on `recur_days` |
| Recurrence roll-over | `PetCare.complete_task()`, `CareTask.next_occurrence()` | Completing a recurring task creates the next-day occurrence |
| Filtering | `tasks_for_pet`, `tasks_by_status`, `tasks_by_recurrence` | Filter by pet, status, or recurrence |
| Time formatting | `format_time(total_min)`, `CareTask.time_range()` | Minutes-since-midnight → `HH:MM`; wraps at 24h |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
 ## Testing PawPal+
 python -m pytest Runs a my testPawPal file making sure that pet could have a name and a weekly schedule could be made with a given time constraint from the owner 
 ## terminal output
 platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\programming\Git Rep\A110\project 2\ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 32 items                                                                                                                                                                                                      

tests\test_pawpal.py ................................                                                                                                                                                             [100%]

================================================================================================== 32 passed in 0.05s =================================================================================================
## confidence level 
3