---
schema_version: 1
study_id: <slug, e.g. "your-study-id">
study_title: <human-readable title>
state_path_relative: <path to this file relative to workspace root>
state_path_absolute_at_write: <absolute path at last write — diagnostic only>
created: <ISO 8601 with timezone, e.g. 2026-05-02T11:30:00+08:00>
updated: <ISO 8601 with timezone>
revision: 1
current_phase: PLAN
pending_question: null
recruitment:
  target: null
  current: null
  completed: null
  partial: null
  excluded: null
timeline:
  collection_start: null
  collection_end_target: null
  collection_end_actual: null
track_summary:
  last_event_ts: null
  current_counts: null
  open_flags: []
  recent_changes: null
  next_action: null
  narrative: |
    <2-3 sentence prose summary for human readability>
---

## Protocol Summary

<Cumulative protocol notes from PLAN phase: research question, design,
variables, population, instruments, timeline, analysis plan. Free-form
Markdown. Build up across PLAN turns.>

## Ethics Checklist Status

<Items from references/irb_ethics_checklist.md, indexed by canonical ID
from references/study_state_protocol.md. Item 5.1 is NOT in this list —
it lives in the `irb` block below.>

```yaml
items:
  - id: "1.1"
    status: NEEDS_ACTION
    answered_at: null
    note: null
  # ... populate all checklist items 1.1-1.8, 2.1-2.6, 3.1-3.6,
  #     4.1-4.5, 5.2, 5.3, 6.1-6.4 (every row except 5.1)
  # See templates/study_state.example.md for the fully-populated form.
irb:
  required: true
  status: NOT_YET_SUBMITTED
  status_changed_at: null
  approval_reference: null
```

## TRACK Log

<Chronological list of user-reported events. Append-only — old entries
never edited or deleted.>

```yaml
events: []
```

## COLLECT Readiness

<Only filled when current_phase=COLLECT. Four checks: sample_size,
missing_data, format, timeline. Each PASS | FAIL | WARN with one-line
justification.>

_(empty until COLLECT phase)_
