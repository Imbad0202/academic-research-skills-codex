# Issue #37 topology pilot report

Status: **EXPLORATORY_COMPLETE**. This is exploratory local evidence from 10 frozen tasks and 26 matched task-arm runs.

## Evidence

### Reviewer

| Arm | Seeded recall | Critical recall | Clean false findings | Total tokens | Wall time (s) | Budget exhausted | Reported retries | Reported duplicates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `inline-solo` | 12/20 (60%) | 4/6 (67%) | 0 | 151,309 | 96.6 | 0 | 0 | 0 |
| `reviewer-five-panel` | 16/20 (80%) | 4/6 (67%) | 0 | 1,134,960 | 427.6 | 0 | 0 | 26 |
| `reviewer-full-seven` | 17/20 (85%) | 4/6 (67%) | 0 | 1,373,334 | 494.0 | 1 | 0 | 20 |
| `reviewer-two-plus-synthesis` | 14/20 (70%) | 3/6 (50%) | 0 | 661,445 | 295.8 | 0 | 0 | 1 |

### Pipeline integrity audit

| Arm | Seeded P1 recall | Citation/source faithfulness | Correct block actions | Total tokens | Wall time (s) | Reported retries | Reported duplicates |
|---|---:|---:|---:|---:|---:|---:|---:|
| `inline-solo` | 7/7 (100%) | 4/4 | 7/7 | 474,116 | 230.6 | 0 | 0 |
| `workflow-current` | 6/7 (86%) | 3/4 | 6/7 | 1,143,850 | 493.4 | 0 | 10 |

Verifier catches remain **unknown**, not zero, because the CLI event stream does not expose per-agent verifier events.

## Local go/no-go

- **retain** `inline-solo` for reviewer / routine: The pilot is single-replicate and no multi-agent arm improved critical recall over inline while staying proportionate in cost.
- **expand** `reviewer-five-panel` for reviewer / high: Seeded-defect recall rose from 0.60 to 0.80, but critical recall stayed 0.67 and token cost increased substantially; replicate before any routing change.
- **reduce** `reviewer-full-seven` for reviewer / high: The extra configuration node yielded only 0.05 recall over the five-seat arm and one of two defective runs exhausted the matched token budget.
- **retain** `inline-solo` for pipeline / integrity-audit: Inline found and blocked all 7 seeded P1 patterns in this cohort.
- **reduce** `workflow-current` for pipeline / integrity-audit: The three-role arm missed B5 and returned pass while using more coordination resources; do not expand it for this audit stratum.

Inline remains the default. This report does not mutate routing or learning state.

## Limitations

- One non-deterministic replicate per task-arm; no variance or causal topology claim is estimable.
- Post-freeze adjudication was not blinded to arm identity.
- Per-agent usage and verifier-catch events are unavailable in Codex CLI JSON and remain unknown rather than zero.
- The ephemeral CLI stream did not expose independently replayable spawn events; declared/completed agent IDs are validated from the frozen structured output.
- Reviewer extra findings are unscored unless factually false; they are not automatically false positives.
- This report records local evidence only and does not update planner defaults or learning state.

Report digest: `d85533c9c8b33ef68adfaa7fbe8d8870d714884cd2d393d809b66f4a962e2d39`
