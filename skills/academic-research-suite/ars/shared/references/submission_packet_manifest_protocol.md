# Deterministic Submission-Packet Manifest Protocol (#667)

This protocol governs mechanical human-subjects packet inventory checks. It is
not a committee, legal opinion, prose review, institutional acceptance,
submission authorization, approval, exemption, compliance result, or review
pathway.

Canonical artifacts:

- `shared/contracts/human_subjects/submission_packet_inventory.schema.json`
- `shared/contracts/human_subjects/submission_packet_manifest.schema.json`
- `scripts/build_submission_packet_manifest.py`
- `shared/contracts/human_subjects/irb_context_record.schema.json`
- `shared/contracts/human_subjects/resolved_authority_context.schema.json`
- `shared/human_subjects_authority_registry.json`
- `scripts/resolve_human_subjects_authority.py`
- `docs/design/2026-08-09-667-submission-packet-manifest-spec.md`

The schemas govern local field shape. This protocol governs safe consumption.

## Authority gate

Accept the #666 authority inputs only as a complete context, registry, and
resolved-result triplet. Before dereferencing any authority pointer, call:

```python
validate_resolved_context(resolved, context, registry)
```

Then require both:

```text
resolution_state=resolved
downstream_gate.profile_dependent_result_allowed=true
```

A replay mismatch is a contract error. Do not convert it to an ordinary
unresolved status. If the triplet is intentionally absent, emit a context-free
`APPLICABILITY_UNRESOLVED` result with
`AUTHORITY_INPUT_NOT_PROVIDED`; do not infer a profile from locale, affiliation,
language, filename, packet content, or model memory.

Consume only `requirement_results[]` rows whose `consumer_scopes` includes
`submission_packet`. Preserve all exact requirement, authority, digest, and
pointer fields. Resolve `requirement_pointer` only in the replay-bound registry.
Keep different authorities and collisions parallel. Fail before output if one
requirement would copy more than 512 consumer scopes, or if applicable evidence
entries or excluded requirements would exceed 4,096 rows. Also reject a final
canonical manifest larger than 8 MiB, including its self digest, so a successful
build always round-trips through the CLI input limit.

## Evidence boundary

For an applicable requirement, V1 consumes only these exact
`evidence_expected[]` fields:

- `evidence_id`
- `held_by`
- `artifact_type`

It computes and preserves an `evidence_pointer` and `evidence_digest`. It never
interprets, evaluates, or copies `evidence_expected.description`; the exact
evidence row is canonical-hashed only to bind replay integrity.

V1 must not interpret, evaluate, or repurpose `structured_expectations`, including
rows with `operator=present`. The exact requirement row, including those bytes,
is canonical-hashed only to verify its #666 pointer and digest. Those rows concern
semantic consent or information coverage and belong to #681. Do not interpret or
copy requirement titles, summaries, packet prose, or attachment text. Hashing
bytes for replay integrity is not permission to extract or judge them.

## Inventory handling

The inventory is author-owned and declaration-only. It names packet-responsible
roles, exact attachment paths and hashes, exact expected-evidence bindings,
declared structure metadata, optional waiver/exception claims, and one
caller-supplied authorization-status object.

Open only inventory-listed paths below the explicit packet root. Reject absolute,
dot, dot-dot, non-normalized, repeated-separator, directory, and symlink targets.
Do not scan siblings or follow links. Enforce 512 files, 64 MiB per file, and
256 MiB total observed bytes.

The authorization object contains exactly:

```json
{
  "value": "documented",
  "source_reference": "institution.record.1",
  "provenance": "caller_supplied_no_derivation"
}
```

`documented` requires a non-null reference; `not_provided` and `cannot_verify`
require null. Copy the entire object unchanged. A packet finding cannot promote,
downgrade, verify, or replace it.

`packet_responsibility_role_ids` classifies evidence ownership only. A row is
packet-owned only when both its replay-bound exact `obligated_actor` and exact
expected `held_by` role occur in the list; composite actor ids are never split or
expanded. If either role is outside the list, the row is an
`external_dependency`. Never turn committee-, IRB-, controller-, or other
authority-held evidence into an investigator omission.

Declared version, date, signature-block, and certificate fields receive only
closed syntax and internal-consistency checks. V1 has no universal rule that
each artifact requires any of them. Without a separately versioned,
source-backed mechanical expectation, a null version/date, a `not_located` or
`unknown` signature row, a null certificate, or a certificate whose interval is
future/stale relative to `applicability_as_of` cannot become a gap or conflict.
Only internal contradictions such as expiry before issue or a present
certificate's holder mismatch are mechanical conflicts.

## Capability envelope

The checker supports only the seven exact author-declared facts below:

```text
packet_v1.non_clinical=true
packet_v1.single_institution=true
packet_v1.competent_adults_only=true
packet_v1.biospecimens_involved=false
packet_v1.regulated_clinical_trial=false
packet_v1.cross_border_material_transfer=false
packet_v1.multisite_reliance=false
```

This is a software capability envelope, not a legal characterization. Missing,
unknown, or different facts emit `APPLICABILITY_UNRESOLVED`. They do not select a
pathway or establish non-applicability.

## Status and readiness

After the authority and capability gates permit packet observation, every
explicit inventory row produces a packet observation with
`status=DOCUMENTED|CONFLICTING` and closed reasons for located bytes, absence,
declared hash/size mismatch, an internally impossible certificate interval, or
a certificate holder that differs from the artifact's declared holder. This
observation accounting also covers extra artifacts that no selected requirement
consumes. It is visibility, not an authority requirement:
observation status alone does not change readiness. Only an applicable,
packet-owned evidence entry can turn the same mechanical conflict into a packet
gap.
When either gate is closed, observations remain empty and the checker does not
open the packet root.

The closed entry vocabulary is:

```text
DOCUMENTED
NOT_LOCATED
CONFLICTING
APPLICABILITY_UNRESOLVED
ACCEPTANCE_UNVERIFIED
```

Apply it as follows:

- one exact, located, byte-matched, type-matched, holder-matched, internally
  consistent packet-owned artifact → `DOCUMENTED`, readiness effect `none`;
- no packet-owned evidence binding → `NOT_LOCATED`, effect `gap`;
- duplicate binding, missing declared attachment, byte/type/holder mismatch, or
  declared-structure conflict → `CONFLICTING`, effect `gap`;
- missing authority, closed gate, unresolved/outside envelope, or missing overlay
  selection → `APPLICABILITY_UNRESOLVED`, effect `unresolved`;
- evidence whose obligated actor or expected holder is outside packet
  responsibility → `ACCEPTANCE_UNVERIFIED`, responsibility
  `external_dependency`, effect `none`;
- a packet-owned claim whose route ids exactly equal a profiled route and whose
  located decision artifact is bound to every route requirement →
  `ACCEPTANCE_UNVERIFIED`, effect `unresolved`.

A profiled waiver/exception route means only that a route exists. Only the exact,
located, route-bound structural case above suppresses a false gap; a bare,
unsupported, mismatched, or unlocated claim does not. Neither a claim nor a
located decision artifact proves applicability, request, or grant, and neither
can become `DOCUMENTED`.

Aggregate readiness in this order:

1. a global unresolved condition or packet-owned `unresolved` effect →
   `unresolved`;
2. otherwise a packet-owned `gap` effect → `gaps_located`;
3. otherwise → `no_listed_gaps_located`.

An external dependency and the fixed top-level institutional-acceptance boundary
do not affect packet readiness. `overlay_selection_state=not_provided` does;
`none_declared_by_author` remains visibly distinct and does not by itself prevent
`no_listed_gaps_located`.

`DOCUMENTED` is a mechanical uppercase entry state. It is not the lowercase
authorization value `documented`.

## Pointer, digest, and accounting rules

Use canonical JSON with UTF-8, sorted keys, compact separators, and non-finite
numbers forbidden. Reject control, format, and escaped lone-surrogate code points
before digesting, rendering, or opening any path.

- digest the semantic inventory for `inventory_digest`: sort packet-responsibility
  roles; sort claims by requirement id and nullable decision-artifact id and sort
  their route ids; sort artifacts by artifact id and relative path; sort each
  artifact's evidence bindings by requirement/evidence id and signature blocks by
  role/state; leave every scalar unchanged;
- digest packet observations sorted by artifact id and relative path for
  `observation_digest`;
- recompute every dereferenced requirement and match `requirement_digest`;
- derive `evidence_pointer` from the exact requirement pointer and evidence index,
  then digest the exact evidence row;
- copy #666 context and registry pointers and the resolved digest exactly; and
- digest the completed manifest with `manifest_digest` excluded.

Sort matched artifact ids lexically; entries by axis, authority kind, authority
id, requirement id, and evidence pointer; excluded requirements by axis,
authority kind, authority id, and requirement id; unresolved reasons by code,
nullable fact id, and nullable overlay kind; and capability facts in the fixed
seven-fact order. Never use #666 `trace_order` as a semantic sort key.

Do not compute a raw context digest. #666 uses a semantic digest that excludes
`confirmed_at` and normalizes unordered fields.

Account for every selected `submission_packet` requirement exactly once:

- applicability true: one entry for every expected-evidence row;
- applicability false: one `excluded_requirements` row with
  `resolved_predicate_false`;
- applicability unknown: never crosses the #666 gate.

Do not invent `NOT_APPLICABLE`, suppress a parallel authority, merge evidence
rows, or let display precedence affect semantic output.

Before accepting or rendering a serialized manifest, call
`validate_submission_packet_manifest` with the same inventory, packet root, and
authority-input mode. It replays the entire build and requires canonical exact
equality. Shape validation or a self-consistent manifest digest alone is not
sufficient.

Treat every rendered identifier, pointer, and inventory path as untrusted data.
Escape it deterministically so it cannot create raw HTML, a Markdown link/image,
an extra table row, or another structural token.

## Fixed administrative output

Rendered output includes these four fixed #665 status lines:

```text
Review pathway: institutional determination required
Submission readiness: gaps_located | no_listed_gaps_located | unresolved
Authorization status: documented | not_provided | cannot_verify
Review timeline: unknown — obtain current institutional estimate
```

Two additional lines preserve the caller-supplied authorization source reference
and `caller_supplied_no_derivation` provenance without changing any status.

and ends with:

> **Human-subjects boundary:** This output does not authorize recruitment,
> consent, access to identifiable data, intervention, or data collection.

The JSON carrier preserves the same fixed text exactly:

```text
Human-subjects boundary: This output does not authorize recruitment, consent, access to identifiable data, intervention, or data collection.
```

It never emits a review level, content verdict, approval, adequacy finding, prose,
quote, excerpt, or legal conclusion.

## #681 handoff

#681 consumes only a manifest that first passes
`validate_submission_packet_manifest(...)` against the exact inventory, packet
root, context, registry, and resolved artifact, plus separately and explicitly
session-held content keyed by matched artifact id. Its finalizer is
`scripts/build_content_coverage_advisory.py`, and its closed carrier/protocol are
`shared/contracts/human_subjects/content_coverage_advisory.schema.json` and
`shared/references/authority_content_coverage_advisory_protocol.md`.

The advisory groups exact requirement refs without merging parallel
authorities, copies every deterministic entry ref, and dereferences only the
matching replay-bound `structured_expectations[]` rows. `DOCUMENTED` remains a
structural signal, not content coverage. A packet gap, external-holder row,
waiver/exception boundary, or applicability-false exclusion cannot be converted
into a semantic missing-element finding.

The output must carry `LLM-ADVISORY`, a separate
`advisory_coverage_status`, and `evaluation_status=UNMEASURED`. It may not update
any deterministic status, readiness, authorization, acceptance, pointer, or
digest field. Missing or unavailable session content is an explicit
`not_checked` result with null advisory status, never a fabricated
`NOT_LOCATED`. UNMEASURED is not a scored measurement row or an efficacy claim.
