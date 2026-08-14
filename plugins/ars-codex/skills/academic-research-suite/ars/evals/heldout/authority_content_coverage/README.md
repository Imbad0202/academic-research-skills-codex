# Authority-profile content coverage — held-out evaluation status

## Current result

**UNMEASURED — no scored held-out measurement row exists.**

The #681 implementation provides a closed advisory carrier, exact source-bound
evidence rows, replay validation, and hermetic contract tests. Those tests show
that the machinery preserves its inputs and boundaries. They do not measure
whether an LLM correctly identifies semantic coverage.

This directory deliberately contains no `measurement-*.json`, no synthetic
"unmeasured" row, no placeholder score, and no inferred baseline. The
`evaluation_status=UNMEASURED` marker in a final advisory is an honest product
boundary, not a measurement artifact.

## Claims prohibited while unmeasured

Until a real scored row exists, ARS must not claim or imply:

- content-coverage accuracy, precision, recall, sensitivity, or specificity;
- improved IRB/committee acceptance or submission readiness;
- fewer missing consent elements in practice;
- equivalence or superiority to a human reviewer; or
- validated performance for a jurisdiction, language, document type, profile,
  model, or prompt.

Contract acceptance phrases such as "exact replay passed" or "mutation test
passed" refer only to carrier integrity and noninterference, never efficacy.

## Required future held-out design

Any future efficacy claim requires a pre-registered held-out suite and a real
scored row under `evals/heldout/MEASUREMENT_CONTRACT.md`. The suite must register
as `llm_judged` before publishing that row and must at minimum freeze:

1. exact selected-profile, effective-date, context, registry, resolved-manifest,
   inventory, and content fixtures;
2. bilingual/multilingual passages where supported, including Unicode and
   document-locator variation;
3. positive coverage, checked absence, genuine conflict, missing access,
   conditional-false, external-actor, and waiver/exception cases;
4. gold expectation-level labels and bounded quoted anchors prepared without
   access to subject output;
5. a precommitted adjudication rubric that distinguishes "appears covered" from
   adequacy, compliance, acceptance, and authorization;
6. at least two disclosed judge configurations from different model families for
   a decision-relevant run, plus the measurement contract's replication,
   blinding, raw-output, and adjudication requirements; and
7. per-expectation false-positive and false-negative accounting, especially the
   prohibited false-missing cases.

Conditional-false requirements and profiled waiver/external-authority boundaries
must be scored as boundary-preservation cases, not ordinary negative-coverage
examples. Missing content must be scored as `not_checked`, never as a pass or a
located omission.

## Separation from hermetic fixtures

Fixtures under `scripts/fixtures/content_coverage_advisory/` are implementation
tests. They may exercise deterministic mappings with caller-supplied draft
observations, but they are visible to maintainers and are not a held-out corpus.
Passing them cannot create a score or change this README's `UNMEASURED` status.
