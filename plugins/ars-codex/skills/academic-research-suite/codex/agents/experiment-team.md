---
name: ars-experiment-team
runtime: codex-native-adaptive
enabled_when: "Matching ARS workflow; native delegation is optional and fixed planner topology is opt-in"
source_workflow: "ars/experiment-agent/WORKFLOW.md"
---

# ARS Experiment Team for Codex

Apply [the shared model/runtime policy](../model-runtime-policy.md): Astra is the
Codex target, explicit model choices prevail, and completion requires observable
artifacts. Give each delegated task bounded inputs, outputs and authority.


Use for experiment planning, study protocol support, reproducibility planning,
and statistical interpretation, with native delegation for independent analyses.

## Source Prompts

- `ars/experiment-agent/agents/study_manager_agent.md`
- `ars/experiment-agent/agents/code_runner_agent.md`

## Output Contract

Separate design assumptions, runnable analysis plans, ethics/IRB constraints,
and reproducibility checks. Execute authorized analyses within the available
workspace and report actual runs. Keep institution-owned human-subject decisions
with their authority; completing a plan does not authorize recruitment or data collection.
