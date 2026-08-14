# Authority-profile Content-Coverage Advisory Protocol (#681)

This protocol governs the separate `LLM-ADVISORY` layer that records whether a
bounded, session-held packet passage appears to cover a structured expectation
from an exactly selected human-subjects authority profile. It is not a legal,
adequacy, compliance, readiness, authorization, institutional-acceptance, or
review-pathway determination.

Canonical artifacts:

- `shared/contracts/evidence/evidence_row_v1_1.schema.json`
- `shared/contracts/human_subjects/content_coverage_advisory.schema.json`
- `scripts/build_content_coverage_advisory.py`
- `shared/references/submission_packet_manifest_protocol.md`
- `shared/references/evidence_row_protocol.md`
- `docs/design/2026-08-09-681-authority-content-coverage-advisory-spec.md`

The schemas govern closed field shape. This protocol governs replay,
noninterference, and safe consumption.

The runtime API is `finalize_advisory`, `validate_advisory`, and
`render_advisory` in `scripts/build_content_coverage_advisory.py`. The CLI
commands are `build|validate|render`; every command names the complete replay
inputs and explicit session-content map. Render additionally accepts one
explicit page and bounded page size.

The exact public signatures are:

```python
finalize_advisory(draft, inventory, packet_root, context, registry, resolved, manifest, session_sources)
validate_advisory(advisory, draft, inventory, packet_root, context, registry, resolved, manifest, session_sources)
render_advisory(advisory, draft, inventory, packet_root, context, registry, resolved, manifest, session_sources, *, page=1, page_size=25)
```

Runtime resource ceilings are part of the contract. A draft has at most 4,096
judgments. An in-memory `session_sources` map has at most 512 exact artifact IDs,
64 MiB of strict UTF-8 text per artifact, and 256 MiB total. Independently, the
CLI's shared named-JSON loader caps every serialized JSON input file—including
`--source-map`—at 8 MiB, so the CLI source-map file is more tightly bounded than
the direct in-memory API. A final advisory's compact canonical UTF-8 JSON is at
most 8 MiB inclusive. `build` writes exactly those canonical bytes with no
trailing newline, preserving loadability by the same CLI for `validate` and
`render`. Each render page has at most 25 evidence rows. Crossing any ceiling
fails; it cannot be represented as a coverage observation.

## Version and layer boundary

The evidence carrier is `evidence-row/1.1` with the single surface
`authority_profile_content_coverage`. It is a new version because
`evidence-row/1.0` is closed to `phase_e_claim_verification` and contains Phase E
claim and verdict fields that do not belong here. The 1.0 schema, runtime API,
cache behavior, renderer, and persisted rows remain unchanged.

Every draft and final advisory carries the exact layer literal:

```text
LLM-ADVISORY
```

The advisory status is held only in `advisory_coverage_status`. Never write it
into a #667 `entries[].status`, packet observation, readiness, authorization,
acceptance, pointer, or digest field.

## Mandatory #666/#667 replay

Before reading a draft, dereferencing `structured_expectations`, or consuming
session content, the permitted finalizer must call:

```python
validate_submission_packet_manifest(
    manifest,
    inventory,
    packet_root,
    context=context,
    registry=registry,
    resolved=resolved,
)
```

The context, registry, and resolved inputs are a complete all-or-none triplet.
This surface requires the replay-validated, resolved, open profile-dependent
gate. A replay mismatch is a contract error, not an advisory finding. Shape
validation or a self-consistent `manifest_digest` is insufficient.

The final `input_binding` copies exactly the manifest schema version, manifest,
inventory and observation digests, context and registry identities/digests,
registry `as_of`, and resolved digest. `deterministic_status` copies the complete
four administrative fields plus the fixed acceptance status. The five boundary
booleans are always true.

## Exact requirement and entry seam

Group #667 entries by their exact `requirement_ref`; do not merge parallel
authorities or let display order choose a winner. Each final requirement result
copies:

- the complete `requirement_ref`;
- the dereferenced authority anchor pointer, canonical digest, source id,
  provision, effective date, and HTTPS URL; and
- every matching #667 entry as a `deterministic_entry_refs[]` row containing its
  complete `evidence_ref`, responsibility, status copied under
  `deterministic_status`, reason codes, and matched artifact ids.

An applicability-false #667 `excluded_requirements` row is copied into the final
`excluded_requirements` array and never becomes a content finding. This is the
conditional-requirement false-missing guard.

Only a `packet_owned` entry with deterministic `DOCUMENTED` status and an exact
matched artifact is eligible for a content check. External dependencies,
structural `NOT_LOCATED` or `CONFLICTING` rows, and profiled waiver/exception
cases whose structural result is `ACCEPTANCE_UNVERIFIED` are never converted to
an advisory missing-element finding. Their deterministic facts remain visible in
`deterministic_entry_refs`.

Eligibility is entry-local. An ineligible external or committee sibling entry
does not suppress a coexisting `packet_owned / DOCUMENTED` artifact under the
same requirement. Preserve both deterministic entries while checking only the
eligible artifact; this mixed shape occurs in the live consent requirements.

## Structured-expectation accounting

Dereference only the exact replay-bound `requirement_pointer`, then derive one
pointer and canonical digest for every `structured_expectations[]` row. A draft
names an expectation by that exact pointer; it does not supply trusted field ids,
requirements, authority anchors, hashes, paths, or source metadata. The finalizer
derives those fields from replay-bound inputs.

Every profiled structured expectation is accounted for exactly once in a final
requirement result. A requirement with no structured expectations is not treated
as covered: it is `not_checked`, has null advisory status, and carries
`NO_PROFILED_STRUCTURED_EXPECTATIONS`.

## Explicit session-content map

Packet prose enters only through an explicit in-memory map keyed by exact #667
artifact id. The finalizer never scans the packet, opens a path from the
inventory or draft, retrieves a URL, consults an environment variable, or calls
a model/API. Unknown artifact ids and ambiguous duplicate mappings fail.

For a held string, `source_content_sha256` and
`source_content_utf8_bytes` cover its exact strict-UTF-8 bytes. The raw artifact
digest and byte size are copied from the matching #667 packet observation and
remain separate. Missing, access-failed, and retrieval-failed content has null
content hash/length even when the raw artifact was structurally located.

## Evidence-row/1.1 states

The closed states are:

| State | Meaning |
|---|---|
| `agent_extracted` | The advisory-selected bounded quote is an exact substring of the explicit session string. Its locator is agent supplied and not independently authenticated. |
| `checked_no_match` | Explicit held content was checked but no passage was selected for the expectation. This is not proof of semantic absence or efficacy. |
| `not_checked` | No content-coverage check ran. |
| `source_missing` | The eligible artifact had no explicit session-content value. |
| `access_failed` | An explicitly reported access failure prevented a check. |
| `retrieval_failed` | An explicitly reported upstream retrieval/extraction failure prevented a check. |

`agent_extracted` requires a `quote` anchor, non-null excerpt text/hash/UTF-8
span/capture time, and exact source replay. Its text equals the once-decoded
anchor byte-for-byte. `checked_no_match` is source-bound but has an empty `none`
anchor and null excerpt payload. All unperformed states have empty anchors, null
excerpt payloads, and null source-content hashes/lengths.

Quotes use #656's strict one-time percent decoding: malformed escapes and invalid
UTF-8 fail, `+` remains `+`, and there is no Unicode, whitespace, punctuation,
case, or newline normalization. Quotes remain at most 25 whitespace-split words
and 1,000 Unicode code points. `row_sha256` is SHA-256 over canonical UTF-8 JSON
with only `row_sha256` excluded.

V1.1 performs no cache lookup. Its retained shared cache block is fixed to
`status=not_used` and `key_sha256=null`. External text defaults to
`session_only/not_assessed`; shareable and authorized must occur together. The
quote ceiling is data minimization, not a rights conclusion.

## Draft and aggregation

The draft is a closed `content-coverage-advisory-draft/1.0` observation carrier.
Its machine shape authority is
`shared/contracts/human_subjects/content_coverage_advisory.schema.json#/$defs/advisory_draft`,
which the runtime validates before consuming any judgment. It carries the
mandatory layer, exact requirement/expectation/artifact ids,
`performed|not_checked`, a nullable advisory status, a document locator, one
encoded bounded quote when applicable, an explicit nullable `captured_at`, and a
nullable explicit failure state.
The finalizer, not draft prose, derives every other field.

For performed expectation findings:

- `DOCUMENTED` requires at least one replay-confirmed `agent_extracted` row;
- `NOT_LOCATED` requires source-bound `checked_no_match` rows covering every
  eligible checked artifact and no positive quote; and
- `CONFLICTING` requires at least two replay-confirmed passages supporting the
  stated conflict boundary.

The two conflict passages may occur in one artifact or different artifacts.
Their evidence anchors/UTF-8 spans must be distinct; artifact id alone is not the
judgment identity and cannot prohibit two passages from one document.

`DOCUMENTED` and `CONFLICTING` draft observations require an explicit RFC-3339
`captured_at`, which the finalizer copies into the evidence row. `NOT_LOCATED`
and every unperformed observation require null. Never substitute
`context.confirmed_at`: #666 deliberately excludes it from the semantic context
digest, and confirmation time is not excerpt-capture provenance.

Aggregate a completely performed requirement in this order:

1. any expectation `CONFLICTING` -> `CONFLICTING`;
2. otherwise any expectation `NOT_LOCATED` -> `NOT_LOCATED`;
3. otherwise every expectation `DOCUMENTED` -> `DOCUMENTED`.

If any profiled expectation was not checked, the requirement is `not_checked`
and does not publish a partial coverage conclusion. Missing content therefore
uses `advisory_coverage_status=null`, never `DOCUMENTED` or `NOT_LOCATED`.
`APPLICABILITY_UNRESOLVED` and `ACCEPTANCE_UNVERIFIED` may only preserve their
matching deterministic boundary; an advisory observation cannot derive either.

The #666 resolved/downstream gate and the #667 capability envelope must be open.
A closed gate has no exact requirement rows and is a contract error for this
surface. The one open-gate unresolved case is an explicitly unprovided
institutional or funder overlay selection: #667 retains the selected base
requirement entries while reporting `OVERLAY_SELECTION_NOT_PROVIDED`. For each
such requirement, #681 emits `not_checked`,
`advisory_coverage_status=APPLICABILITY_UNRESOLVED`, the matching canonical
reason, unchanged deterministic entry refs, and no expectation findings. It
rejects draft judgments and does not inspect the session-content map in that
state.

The closed advisory reason codes are:

```text
ALL_EXPECTATIONS_APPEAR_COVERED
EXPECTATION_NOT_LOCATED
CONFLICTING_COVERAGE_OBSERVATIONS
COVERAGE_CHECK_NOT_PERFORMED
SESSION_CONTENT_NOT_PROVIDED
SOURCE_ACCESS_FAILED
SOURCE_RETRIEVAL_FAILED
DETERMINISTIC_PACKET_GAP
DETERMINISTIC_PACKET_CONFLICT
WAIVER_OR_EXCEPTION_BOUNDARY
EXTERNAL_DEPENDENCY
APPLICABILITY_UNRESOLVED
NO_PROFILED_STRUCTURED_EXPECTATIONS
INSTITUTIONAL_ACCEPTANCE_REQUIRED
```

## Validation and rendering

The final report digest uses canonical UTF-8 JSON with sorted keys, compact
separators, non-finite values forbidden, and only `report_digest` excluded.
Validation replays #667 and every source-bound evidence row against the same
named inputs. A report cannot validate or render from self-digests alone.

Rendering performs no retrieval or status derivation. Treat every identifier,
path, locator, authority string, and excerpt as untrusted. Markdown/HTML escaping
must prevent raw tags, comments, links, images, URL autolinks, headings, fences,
extra cells/rows, control characters, bidi controls, and line-boundary injection.

The final JSON persists every evidence row in canonical order, but one render
call exposes exactly one bounded evidence page. Default and maximum page size are
25; a caller may request a smaller positive size and an explicit one-based page.
The rendered navigation states previous page, next page, and the explicit valid
page range. Page zero, negative/out-of-range pages, size zero, and size above 25
fail. There is no concatenate-all loop, render-all API, or `--all` flag. Walking
pages must reproduce every row exactly once and in order.

## Measurement boundary

The final carrier contains the exact marker `evaluation_status=UNMEASURED`.
That marker is not a measurement row. No held-out scored row exists for this
surface, so ARS makes no accuracy, precision, recall, coverage-improvement, or
efficacy claim. A future efficacy claim requires a real held-out scored row under
the shared held-out measurement contract; never synthesize an "unmeasured"
measurement JSON file.
