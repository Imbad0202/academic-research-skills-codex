# #667 Deterministic submission-packet manifest V1

## Decision

V1 checks an explicit, author-declared packet inventory against replay-validated
human-subjects authority rows. It answers only mechanical questions: whether a
listed file is located, whether its bytes match the declaration, whether its
declared artifact type and holder match an exact expected-evidence row, and
whether the declaration is internally well formed.

It does not judge prose, coverage, adequacy, language quality, legal
applicability, waiver entitlement, institutional acceptance, review level,
approval, compliance, or authorization. It uses no model, network request, or
external API.

Canonical artifacts:

- `shared/contracts/human_subjects/submission_packet_inventory.schema.json`
  (`submission-packet-inventory/1.0`)
- `shared/contracts/human_subjects/submission_packet_manifest.schema.json`
  (`submission-packet-manifest/1.0`)
- `scripts/build_submission_packet_manifest.py`
- `shared/references/submission_packet_manifest_protocol.md`
- the #666 context, registry, resolved-context schemas, registry, and replay
  validator

The two JSON Schemas are authoritative for local field names and shape. This
specification owns the cross-input, state-transition, pointer, digest, and replay
rules that JSON Schema cannot prove by itself.

## 1. Inputs and exact authority seam

The runtime accepts:

1. one inventory object and one explicit packet root; and
2. either all of `context + registry + resolved` or none of them.

A partial authority triplet is a contract error. When all three authority inputs
are present, the runtime first calls:

```python
validate_resolved_context(resolved, context, registry)
```

from `scripts/resolve_human_subjects_authority.py`. Only a replay-validated result
with `resolution_state=resolved` and
`downstream_gate.profile_dependent_result_allowed=true` permits registry
dereferencing. A forged, stale, or mismatched serialized result is a contract
error; it is not converted into an ordinary unresolved manifest.

When the authority triplet is intentionally absent, the runtime emits a
context-free manifest with `AUTHORITY_INPUT_NOT_PROVIDED`, no profile-derived
entries, and `submission_readiness=unresolved`. It never chooses a jurisdiction,
profile, overlay, or newest version.

After the gate opens, V1 filters to exact #666 `requirement_results[]` rows whose
`consumer_scopes` contains `submission_packet`. It preserves, without rewriting:

- `requirement_id`
- `authority_kind`
- `authority_id`
- `authority_version`
- `authority_digest`
- `axis`
- `obligated_actor`
- `consumer_scopes`
- `applicability`
- `requirement_digest`
- `requirement_pointer`
- `authority_anchor_pointer`

It resolves `requirement_pointer` only against the exactly bound registry.
Requirement rows from parallel authorities remain separate even when one artifact
is explicitly bound to both. V1 rejects more than 512 copied consumer scopes on
one requirement and more than 4,096 applicable evidence entries or 4,096 excluded
requirements, before constructing an out-of-contract manifest. The final
canonical manifest, including `manifest_digest`, may not exceed 8 MiB so every
successful build remains readable by the same CLI validation/rendering boundary.

## 2. Inventory contract

The root is closed:

```json
{
  "schema_version": "submission-packet-inventory/1.0",
  "inventory_id": "packet.example",
  "declared_by": "author",
  "packet_responsibility_role_ids": ["principal_investigator"],
  "authorization_status_input": {
    "value": "not_provided",
    "source_reference": null,
    "provenance": "caller_supplied_no_derivation"
  },
  "waiver_or_exception_claims": [],
  "artifacts": []
}
```

`packet_responsibility_role_ids` is an exact author declaration of the roles whose
held evidence belongs in this packet. An evidence row is packet-owned only when
both the replay-bound requirement's exact `obligated_actor` and the exact
`evidence_expected[].held_by` occur in this list. The checker does not split,
expand, or rewrite a composite actor id. If either exact role is outside the list,
the row is an external dependency, not an investigator omission.

`authorization_status_input` is copy-through only. Its exact fields are `value`,
nullable `source_reference`, and
`provenance=caller_supplied_no_derivation`. `documented` requires a non-null opaque
source reference; the other two values require null. The runtime never promotes,
downgrades, or verifies this value from packet findings.

### 2.1 Artifact rows

Every `artifacts[]` row declares one attached regular file:

```json
{
  "artifact_id": "consent.materials.v1",
  "relative_path": "packet/consent.pdf",
  "declared_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "declared_size_bytes": 123,
  "media_type": "application/pdf",
  "artifact_type": "consent_materials",
  "declared_holder_role_id": "principal_investigator",
  "evidence_bindings": [
    {
      "requirement_id": "tw.hsra.article-14.consent-information",
      "evidence_id": "consent.article-14-materials"
    }
  ],
  "declared_structure": {
    "version_id": "v1",
    "document_date": "2026-08-09",
    "signature_blocks": [
      {"role_id": "participant", "state": "present"}
    ],
    "certificate": null
  }
}
```

The list is not a directory-scan hint. The runtime opens only named paths. A path
must be canonical POSIX-relative and may not be absolute, empty, dot, dot-dot,
non-normalized, repeated-separator, a directory, or a symlink. Artifact ids,
relative paths, and evidence-binding pairs are semantically unique. Limits are
512 declared files, 64 MiB per file, and 256 MiB total observed bytes.

An artifact row's presence is itself the author's declaration that the file is
attached. A missing listed file is therefore a declared-vs-observed conflict. An
applicable packet-owned expected-evidence row with no artifact binding is instead
`NOT_LOCATED`.

`declared_structure` is declaration-only metadata. Dates must be real ISO 8601
calendar dates and signature roles are unique. An expiry before issue and an
existing certificate whose `holder_role_id` differs from the artifact holder are
retained as declarations, then surfaced as a mechanical observation conflict
when the gates permit packet observation. Agreement with the exact expected-
evidence holder is additionally required before an applicable evidence entry can
be internally consistent. These checks do not authenticate a signature or
certificate.

V1 does not invent a general rule that every artifact needs a version, date,
signature, or certificate. A null field remains visible and mechanically typed;
it becomes a gap only when an exact, future source-backed mechanical expectation
expressly requires it. No such live expectation exists in the #666 registry at
V1 launch. In particular, without such an expectation, a null version or date, a
`not_located` or `unknown` signature declaration, a null certificate, and a
certificate whose issue/expiry interval does not contain `applicability_as_of`
must not become `NOT_LOCATED`, `CONFLICTING`, or another readiness effect. V1
checks only closed syntax and internal consistency such as `expires_on >=
issued_on` and the holder agreement of a certificate that is actually present.

### 2.2 Waiver and exception claims

A claim contains exactly:

```json
{
  "requirement_id": "example.base-requirement",
  "route_requirement_ids": ["example.profiled-route"],
  "decision_artifact_id": null,
  "declared_by": "author"
}
```

An exact profiled route proves only that the route is represented in the selected
registry. Only a claim whose route ids exactly equal that profiled route, whose
decision artifact is located, and whose artifact bindings cover the profiled
route requirements can suppress a false `NOT_LOCATED` gap. The base evidence row
then becomes packet-owned `ACCEPTANCE_UNVERIFIED` with
`readiness_effect=unresolved`; it does not become a `DOCUMENTED` waiver. A bare,
unsupported, mismatched, or unlocated claim does not suppress the ordinary
missing-evidence result. Neither form proves that the route applies, was requested
successfully, or was granted.

## 3. V1 capability envelope

The capability envelope is an implementation boundary, not a legal category.
The #666 registry fact catalogue supplies seven author-declared boolean facts:

| Fact id | Required value |
|---|---:|
| `packet_v1.non_clinical` | `true` |
| `packet_v1.single_institution` | `true` |
| `packet_v1.competent_adults_only` | `true` |
| `packet_v1.biospecimens_involved` | `false` |
| `packet_v1.regulated_clinical_trial` | `false` |
| `packet_v1.cross_border_material_transfer` | `false` |
| `packet_v1.multisite_reliance` | `false` |

Missing and `state=unknown` are not false. If any fact is missing, unknown, or
differs from the required envelope value, the result is
`APPLICABILITY_UNRESOLVED` with a closed reason. It does not say that the study is
legally inapplicable, impermissible, or assigned to another pathway.

## 4. Manifest contract

The manifest root contains exactly:

- `schema_version`
- `inventory_pointer`
- `authority_binding`
- `packet_pointer`
- `packet_observations`
- `capability_envelope`
- `overlay_selection_state`
- `administrative_status`
- `acceptance_boundary`
- `entries`
- `excluded_requirements`
- `unresolved_reasons`
- `boundary_footer`
- `manifest_digest`

The following is a non-normative, abbreviated schema-shape illustration of a
context-free unresolved carrier. Its all-zero digests are placeholders and its
per-fact unresolved rows are omitted for readability; it is not a replay-valid
manifest and must not be accepted by `render` or an acceptance test:

```json
{
  "schema_version": "submission-packet-manifest/1.0",
  "inventory_pointer": {
    "inventory_id": "packet.example",
    "schema_version": "submission-packet-inventory/1.0",
    "inventory_digest": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "authority_binding": {
    "state": "not_provided",
    "context_pointer": null,
    "registry_pointer": null,
    "resolved_digest": null,
    "resolution_state": null,
    "downstream_gate": null
  },
  "packet_pointer": {
    "scope": "explicit_inventory_paths_only",
    "observation_digest": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "packet_observations": [],
  "capability_envelope": {
    "state": "unresolved",
    "facts": [
      {"fact_id": "packet_v1.non_clinical", "required_value": true, "declared_state": "missing", "declared_value": null},
      {"fact_id": "packet_v1.single_institution", "required_value": true, "declared_state": "missing", "declared_value": null},
      {"fact_id": "packet_v1.competent_adults_only", "required_value": true, "declared_state": "missing", "declared_value": null},
      {"fact_id": "packet_v1.biospecimens_involved", "required_value": false, "declared_state": "missing", "declared_value": null},
      {"fact_id": "packet_v1.regulated_clinical_trial", "required_value": false, "declared_state": "missing", "declared_value": null},
      {"fact_id": "packet_v1.cross_border_material_transfer", "required_value": false, "declared_state": "missing", "declared_value": null},
      {"fact_id": "packet_v1.multisite_reliance", "required_value": false, "declared_state": "missing", "declared_value": null}
    ],
    "reason_codes": ["V1_ENVELOPE_FACT_MISSING"]
  },
  "overlay_selection_state": null,
  "administrative_status": {
    "review_pathway": "institutional determination required",
    "submission_readiness": "unresolved",
    "authorization_status": {
      "value": "not_provided",
      "source_reference": null,
      "provenance": "caller_supplied_no_derivation"
    },
    "review_timeline": "unknown — obtain current institutional estimate"
  },
  "acceptance_boundary": {
    "status": "ACCEPTANCE_UNVERIFIED",
    "reason_code": "INSTITUTIONAL_DETERMINATION_REQUIRED",
    "affects_submission_readiness": false
  },
  "entries": [],
  "excluded_requirements": [],
  "unresolved_reasons": [
    {
      "status": "APPLICABILITY_UNRESOLVED",
      "code": "AUTHORITY_INPUT_NOT_PROVIDED",
      "fact_id": null,
      "overlay_kind": null
    }
  ],
  "boundary_footer": "Human-subjects boundary: This output does not authorize recruitment, consent, access to identifiable data, intervention, or data collection.",
  "manifest_digest": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

### 4.1 Authority binding

`authority_binding` records `state`, exact copies of the resolved
`context_pointer` and `registry_pointer`, the exact `resolved_digest`, the
resolved artifact's `resolution_state`, and its exact four-boolean
`downstream_gate`. The copies are replay invariants, not independent claims.

When authority inputs are absent, all five bound values are null. When replay
succeeds, none is null, even if the resolved result's downstream gate is closed.
A closed gate emits no dereferenced profile entries.

### 4.2 Packet observations

Once the authority and capability gates permit packet observation, every
explicitly inventoried path has one canonical `packet_observations[]` row, even
when no selected authority row consumes that artifact. In addition to the
path, located/not-located state, observed byte count, and observed SHA-256, the
row carries `status=DOCUMENTED|CONFLICTING` plus closed `reason_codes`.
Missing declared attachments, declared-vs-observed hash or size differences, and
an internally impossible certificate interval or certificate holder that differs
from the artifact's declared holder remain visible here. A consistent observation
uses `STRUCTURE_DOCUMENTED`; it does not mean that any authority requires,
accepts, or has reviewed the file.

Observation status does not by itself change submission readiness. Readiness is
derived only after an observation is joined to an applicable, packet-owned
expected-evidence entry. This preserves declared-vs-attached visibility for an
extra or currently unselected artifact without manufacturing a jurisdiction- or
profile-dependent packet gap.

A closed authority or capability gate emits `packet_observations=[]` and never
opens the packet root.

### 4.3 Entries and exact accounting

Every applicable expected-evidence entry contains exactly:

- `requirement_ref`
- `evidence_ref`
- `responsibility`
- one of the five status tokens
- `readiness_effect`
- closed `reason_codes`
- `matched_artifact_ids`

The five status tokens are:

```text
DOCUMENTED
NOT_LOCATED
CONFLICTING
APPLICABILITY_UNRESOLVED
ACCEPTANCE_UNVERIFIED
```

`DOCUMENTED` means only that the listed bytes and declared mechanical structure
are located and consistent. It is not the lowercase #665
`authorization_status.value=documented`, and never changes that field.

An `evidence_ref` carries only `evidence_id`, `evidence_pointer`,
`evidence_digest`, `artifact_type`, and `held_by`. It does not copy the registry
description. A requirement with resolved applicability false appears once in
`excluded_requirements` with `exclusion_basis=resolved_predicate_false`; V1 does
not invent a sixth `NOT_APPLICABLE` status.

Exact accounting requires:

- every selected `submission_packet` requirement with applicability true has one
  entry for every `evidence_expected[]` row;
- every such requirement with applicability false has exactly one excluded row;
- no requirement or evidence row occurs in both collections;
- collisions and parallel authorities are never merged; and
- changing #666 display precedence does not change the semantic manifest.

### 4.4 State transitions and readiness

Global transitions occur before registry dereferencing:

| Condition | Result |
|---|---|
| Authority triplet intentionally absent | `AUTHORITY_INPUT_NOT_PROVIDED`; readiness `unresolved`; no entries |
| Replay-valid result has a closed gate | `AUTHORITY_RESOLUTION_NOT_PERMITTED`; readiness `unresolved`; no entries |
| Envelope fact missing/unknown/outside | corresponding `V1_ENVELOPE_*`; readiness `unresolved`; no entries |
| Either overlay selection state is `not_provided` | `OVERLAY_SELECTION_NOT_PROVIDED`; readiness `unresolved`; known base entries may remain visible |
| Overlay state is `none_declared_by_author` | state remains visible; it does not by itself prevent `no_listed_gaps_located` |

For each applicable expected-evidence row:

| Condition | Responsibility/status/effect |
|---|---|
| Exact obligated actor or expected holder is outside packet responsibility roles | `external_dependency / ACCEPTANCE_UNVERIFIED / none` |
| Exact profiled route claim with located, route-bound structural evidence | `packet_owned / ACCEPTANCE_UNVERIFIED / unresolved` |
| No exact artifact binding | `packet_owned / NOT_LOCATED / gap` |
| More than one binding | `packet_owned / CONFLICTING / gap` |
| Named artifact missing, hash/size/type/holder differs, or declared structure conflicts | `packet_owned / CONFLICTING / gap` |
| Exactly one mechanically consistent artifact | `packet_owned / DOCUMENTED / none` |

Readiness aggregation is ordered:

1. any global unresolved condition or packet-owned `readiness_effect=unresolved`
   yields `unresolved`;
2. otherwise any packet-owned `readiness_effect=gap` yields `gaps_located`;
3. otherwise `no_listed_gaps_located`.

An external IRB-, committee-, controller-, or other authority-held dependency is
visible as `ACCEPTANCE_UNVERIFIED` but does not become a packet gap. The fixed
top-level `acceptance_boundary` also has
`affects_submission_readiness=false`. Neither rule changes authorization.

## 5. Content boundary

V1 never interprets, evaluates, or copies live `structured_expectations`,
including apparently mechanical operators such as `present`. Current rows such as
`consent.purpose_and_methods` and
`consent.applicable_elements_addressed` concern semantic coverage and belong to
#681. The exact requirement and evidence rows are canonical-hashed only for
pointer/digest replay integrity; that hashing is not semantic consumption. V1
does not interpret, parse, or copy:

- `requirement.title`
- `requirement.summary`
- `evidence_expected.description`
- manuscript or packet prose

The runtime hashes attachment bytes but does not extract their text. The manifest
contains no prose, quote, excerpt, free-text reason, content verdict, or language
score. A future mechanical-expectation extension requires a separately versioned,
source-backed closed contract; it may not overload current #666 content fields.

The shipped registry has two live `submission_packet` requirements and no live
certificate requirement or institutional overlay. Certificate, signature,
waiver, and overlay behavior therefore uses synthetic registries and overlays in
tests. V1 must not invent a live institutional rule to make a fixture pass.

## 6. Canonical digests and replay

Canonical JSON uses UTF-8, sorted object keys, compact separators, and
`allow_nan=false`, matching #666. Duplicate JSON keys and non-finite numbers are
rejected. Text must contain inert Unicode scalar values; control, format, and
escaped lone-surrogate code points are contract errors rather than deferred
filesystem, rendering, or encoding failures.

- `inventory_digest = SHA-256(canonical semantic inventory)`.
- `observation_digest = SHA-256(canonical packet observations sorted by
  artifact_id and relative_path)`.
- `evidence_digest = SHA-256(canonical exact dereferenced evidence row)`.
- `manifest_digest = SHA-256(canonical manifest with manifest_digest removed)`.

The semantic inventory is a deep copy with only set-like arrays normalized:

- sort `packet_responsibility_role_ids`;
- sort waiver/exception claims by `requirement_id` and nullable
  `decision_artifact_id`, and sort each claim's `route_requirement_ids`;
- sort artifacts by `artifact_id` and `relative_path`;
- sort each artifact's evidence bindings by `requirement_id` and `evidence_id`;
  and
- sort each artifact's signature blocks by `role_id` and `state`.

All scalar values and closed objects otherwise remain unchanged. Output uses the
following exact semantic order:

- packet observations by `(artifact_id, relative_path)`;
- matched artifact ids lexicographically;
- applicable entries by `(axis, authority_kind, authority_id, requirement_id,
  evidence_pointer)`;
- excluded requirements by `(axis, authority_kind, authority_id,
  requirement_id)`;
- unresolved reasons by `(code, fact_id-or-empty, overlay_kind-or-empty)`; and
- capability facts in the seven-fact order in section 3.

Reordering a set-like input array therefore does not change the manifest or its
digest. #666 `trace_order` is never a semantic sort key.

The context and registry pointers are copied from the replay-validated resolved
artifact. The runtime must not compute `digest(context)` directly: #666's
`context_digest` is a semantic digest that excludes `confirmed_at` and normalizes
unordered collections. Each dereferenced requirement must recompute to its
`requirement_digest` before its expected-evidence rows are used.

`validate_submission_packet_manifest` repeats inventory validation, packet byte
observation, #666 replay, envelope checking, pointer resolution, accounting,
status derivation, and digest calculation. It then requires canonical exact
object equality. JSON Schema alone is insufficient.

## 7. Public API and CLI

The standard-library runtime exposes:

```python
validate_submission_packet_inventory(inventory)
observe_submission_packet(inventory, packet_root)
build_submission_packet_manifest(
    inventory, packet_root, *, context=None, registry=None, resolved=None
)
validate_submission_packet_manifest(
    manifest, inventory, packet_root, *, context=None, registry=None, resolved=None
)
render_submission_packet_manifest(manifest)
main(argv=None)
```

The CLI uses non-abbreviating subcommands:

```bash
python scripts/build_submission_packet_manifest.py build \
  --inventory inventory.json \
  --packet-root packet \
  --context context.json \
  --registry shared/human_subjects_authority_registry.json \
  --resolved resolved-authority-context.json \
  --output submission-packet-manifest.json

python scripts/build_submission_packet_manifest.py validate \
  --manifest submission-packet-manifest.json \
  --inventory inventory.json \
  --packet-root packet \
  --context context.json \
  --registry shared/human_subjects_authority_registry.json \
  --resolved resolved-authority-context.json

python scripts/build_submission_packet_manifest.py render \
  --manifest submission-packet-manifest.json \
  --inventory inventory.json \
  --packet-root packet \
  --context context.json \
  --registry shared/human_subjects_authority_registry.json \
  --resolved resolved-authority-context.json
```

`render` replay-validates before emitting four fixed #665 administrative-status
lines followed by two authorization-provenance copy-through lines,
packet-observation rows, applicable evidence rows, excluded-requirement
rows, and the fixed non-authorization footer. It emits no
review level or verdict. `build`, `validate`, and `render` return zero for valid
manifests regardless of readiness state; malformed input, unsafe paths, I/O
failure, and replay mismatch return 2.

Every dynamic Markdown cell is rendered as inert data. In particular, an
inventory path or pointer containing Markdown punctuation, raw-HTML delimiters,
an apparent link/image, or a URL-like scheme cannot create markup, a second row,
or an active link.

## 8. #681 handoff

The manifest is a pointer-only deterministic input to #681. The #681 finalizer
must first repeat `validate_submission_packet_manifest(...)` with the exact
inventory, packet root, context, registry, and resolved artifact; schema shape
or a self-consistent digest alone is insufficient. Only after replay may it
join separately session-held packet content by an exact matched artifact id and
dereference replay-bound `structured_expectations[]` rows. It may not treat
`DOCUMENTED` as semantic coverage.

The versioned output is defined by
`shared/contracts/human_subjects/content_coverage_advisory.schema.json` and
`shared/references/authority_content_coverage_advisory_protocol.md`. It labels
its own result `LLM-ADVISORY`, uses a separate
`advisory_coverage_status`, and copies each exact deterministic entry ref. It
may not overwrite the manifest status, submission readiness, authorization
input, acceptance boundary, pointer, or manifest digest. Applicability-false
requirements remain exclusions, and structural gaps, external dependencies, or
waiver/exception boundaries cannot be relabeled as missing content. No verdict
field is shared between the layers.

The carrier remains `evaluation_status=UNMEASURED` until a real held-out scored
row exists. This marker is not itself a measurement record or efficacy claim.

## 9. Acceptance matrix

Fixtures and mutation tests must establish at least:

- all five status tokens and all three readiness values;
- identical packet observations but different manifest accounting under different
  author-declared applicability facts;
- missing and unknown envelope facts never becoming false;
- profile/context absence yielding an unresolved manifest without jurisdiction
  fallback;
- replay failure rejecting rather than degrading;
- exact waiver routes preventing a false gap without becoming a granted waiver;
- external-holder rows never becoming investigator packet gaps;
- missing overlay selection yielding unresolved while
  `none_declared_by_author` remains distinct;
- file absence, duplicate binding, digest, size, artifact-type, holder, certificate
  holder, and declared-structure conflicts;
- path traversal, absolute path, symlink, directory, oversized file, and total-size
  rejection;
- requirement/evidence exact accounting, digest binding, collision preservation,
  and display-order invariance;
- no semantic access to or copying of `structured_expectations`, descriptions,
  or prose (whole-row bytes may only be hashed for replay integrity), and no
  network, model, or external API; and
- fixed #665 pathway, independent authorization copy-through, timeline, and
  footer with no review-level, verdict, approval, or adequacy field.
