# Frozen reviewer topology rubric v1

Inspect the manuscript for concrete, consequential defects. Report only findings that can be anchored to the supplied manuscript. Do not browse, call tools, or infer hidden ground truth.

For each finding, record a severity (`P1`, `P2`, or `P3`), a concise defect statement, the manuscript section or line anchor, a short evidence excerpt, and an actionable correction. `P1` means the defect can invalidate the central claim, method, or ethical acceptability; `P2` is material but localized; `P3` is editorial.

Reviewer agents must work blind: they may read the manuscript, this rubric, and their frozen role configuration, but never another reviewer's output. Only the synthesis node may combine reports. Synthesis must preserve corroboration, merge conceptually duplicate findings, and name every contributing agent. A clean manuscript may legitimately produce no findings.

Return only the experiment JSON contract requested by the runner. Do not select a preferred topology.
