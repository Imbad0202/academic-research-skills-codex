# ARS-Codex topology experiment

This directory is the clean-room, local evidence package for issue #37. It
does not copy the private `auto-evolve` implementation. The compatible surface
is a small immutable experiment envelope, an explicit DAG and information
policy, run/agent resource receipts, and a four-dimension evidence report.

## Frozen cohort

`cohort-v1.json` contains exactly 10 tasks:

- three held-out reviewer manuscripts: one clean control and two seeded-defect
  manuscripts;
- seven pipeline integrity fixtures: A1-A5, B5, and D1.

Each task lists only execution-visible files and a canonical input digest over
sorted `(bundle path, file SHA-256)` rows. Held-out manifests, expected audit
findings, good runs, and repository context are not materialized in the agent
sandbox.

The pilot executes 26 task-arm runs: four reviewer arms per manuscript and two
pipeline arms per audit fixture. All arms freeze the exact model ID, reasoning
effort, read-only tool allowance, aggregate token budget, retry policy, and
task input digest. A budget exhaustion remains evidence; it is not erased by a
selective rerun or post-hoc budget increase.

## Information policy

- `inline-solo`: one inline owner, no subagent plan.
- `reviewer-two-plus-synthesis`: two blind reviewer roots, then synthesis.
- `reviewer-five-panel`: five blind reviewer roots, then synthesis.
- `reviewer-full-seven`: field configurer, five blind reviewers, then
  synthesis. The label means seven DAG nodes, not seven reviewers.
- `workflow-current`: the pipeline orchestrator dispatches integrity and state
  roles under explicit dependencies.

Blind reviewer nodes receive the same input digest and frozen role card but no
peer report. Only the synthesis node receives completed review artifacts.

## Reproduction and validation

From the repository root:

```bash
python3 skills/academic-research-suite/codex/scripts/ars_codex_topology_experiment.py validate --require-runs
python3 skills/academic-research-suite/codex/scripts/ars_codex_topology_experiment.py report
python3 skills/academic-research-suite/codex/scripts/ars_codex_quality_gates.py all
```

Running model calls again is intentionally explicit and non-deterministic:

```bash
python3 skills/academic-research-suite/codex/scripts/ars_codex_topology_experiment.py run-all
```

Existing run files are skipped. `--force` exists only on a single `run`
command for diagnosed harness failures; it must not be used to selectively
rerun an unfavorable experimental outcome.

## Interpretation boundary

`results/report.json` and `results/REPORT.md` keep outcome quality,
coordination cost, duplicate contributions, and verifier catches separate.
Unknown measurements remain unknown rather than becoming zero. The local
go/no-go section can recommend retain, reduce, or expanded evidence collection,
but it does not update planner defaults, routing, or a learning projection.

This is one non-deterministic replicate per task-arm. It is enough to decide
whether to expand this local benchmark, not to support a causal claim about
topology or a paper-level threshold.
