# #681 Authority-profile content-coverage advisory

## Decision

#681 adds a versioned, explicitly non-determinative advisory surface. It records
whether bounded passages in explicitly session-held submission content appear to
cover structured expectations from an exactly selected authority profile.

It does not decide adequacy, completeness, compliance, legal applicability,
waiver entitlement, institutional acceptance, review pathway, submission
readiness, approval, or authorization. It never changes a #667 carrier.

The canonical artifacts are:

- `shared/contracts/evidence/evidence_row_v1_1.schema.json`
- `shared/contracts/human_subjects/content_coverage_advisory.schema.json`
- `scripts/build_content_coverage_advisory.py`
- `shared/references/authority_content_coverage_advisory_protocol.md`
- this specification

No live model, external API, network request, judge, or held-out scoring run is
part of implementation acceptance.

## 1. Version boundary

`evidence-row/1.0` remains byte- and behavior-compatible. Its only surface is
`phase_e_claim_verification`, and its `claim` and `verdict` fields must not be
repurposed for profile coverage.

#681 therefore uses:

```text
schema_version = evidence-row/1.1
surface = authority_profile_content_coverage
```

The new row deliberately has no `claim`, `verdict`, adequacy, readiness,
authorization, acceptance, confidence, probability, or score field. Judgment is
held separately in the enclosing advisory's `advisory_coverage_status`.

Every draft and final carrier requires:

```text
layer = LLM-ADVISORY
```

Deleting, changing case, adding whitespace, or substituting a synonym is a
contract failure.

## 2. Inputs and replay order

The finalizer receives:

1. a closed advisory draft;
2. a serialized #667 manifest;
3. the exact #667 inventory and packet root;
4. the exactly bound #666 context, registry, and resolved result; and
5. an explicit in-memory `artifact_id -> session content` map.

The public runtime API is:

```python
finalize_advisory(draft, inventory, packet_root, context, registry, resolved, manifest, session_sources)
validate_advisory(advisory, draft, inventory, packet_root, context, registry, resolved, manifest, session_sources)
render_advisory(advisory, draft, inventory, packet_root, context, registry, resolved, manifest, session_sources, *, page=1, page_size=25)
```

The CLI exposes `build|validate|render`. All commands require the draft,
manifest, inventory, packet root, context, registry, resolved result, and explicit
session-content map; validate/render also require the final report. `render`
accepts `--page` and `--page-size`, never `--all`.

All resource ceilings are fail-closed:

- a draft contains at most 4,096 judgments;
- the in-memory `session_sources` map contains at most 512 exact artifact IDs,
  at most 64 MiB of strict UTF-8 content per artifact, and at most 256 MiB in
  aggregate;
- the CLI's shared named-JSON loader separately limits every serialized JSON
  input file, including `--source-map`, to 8 MiB. Therefore the CLI source map
  is bounded by 8 MiB on disk even though the direct API admits the larger
  in-memory ceilings above;
- the final advisory's compact canonical UTF-8 JSON is at most 8 MiB,
  inclusive. `build` writes exactly those canonical bytes without a trailing
  newline, so every successful build artifact remains loadable by the same
  8 MiB CLI loader for `validate` and `render`; and
- one render call accepts a positive page size no greater than 25.

The CLI loads the named deterministic replay inputs, then runs the gate below
before opening the draft or source-map paths. The direct API applies the same
semantic gate before it validates or consumes draft judgments or session
content. Resource-limit failures are contract failures; they never become an
advisory finding.

Its first semantic operation is full #667 replay:

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

Only a successful, resolved, open profile-dependent gate permits registry
dereference or content checking. A partial authority triplet, changed digest,
forged self-consistent manifest, stale pointer, or replay mismatch fails before
draft or content consumption. It is not converted to `not_checked`.

The final `input_binding` is derived, never trusted from the draft. It freezes
the manifest, semantic inventory, packet observation, context, registry, date,
and resolved-result identities used for the advisory.

## 3. Draft API

The closed draft version is `content-coverage-advisory-draft/1.0`. Its machine
shape authority is
`shared/contracts/human_subjects/content_coverage_advisory.schema.json#/$defs/advisory_draft`;
the runtime validates that exact definition before consuming a judgment. A draft
is untrusted observation input, not a final carrier:

```json
{
  "schema_version": "content-coverage-advisory-draft/1.0",
  "layer": "LLM-ADVISORY",
  "judgments": [
    {
      "requirement_id": "tw.hsra.article-14.consent-information",
      "expectation_pointer": "/profiles/1/requirements/0/structured_expectations/2",
      "artifact_id": "consent.materials",
      "coverage_check_state": "performed",
      "advisory_coverage_status": "DOCUMENTED",
      "document_locator": {
        "kind": "section",
        "value": "研究目的與方法"
      },
      "quoted_anchor_encoded": "%E6%9C%AC%E7%A0%94%E7%A9%B6%E7%9A%84%E7%9B%AE%E7%9A%84%E8%88%87%E6%96%B9%E6%B3%95%E5%A6%82%E4%B8%8B%E3%80%82",
      "captured_at": "2026-08-09T08:00:00Z",
      "failure_state": null
    }
  ]
}
```

For `performed`, status is `DOCUMENTED|NOT_LOCATED|CONFLICTING` and
`failure_state` is null. `DOCUMENTED` and `CONFLICTING` require a non-empty
bounded quote plus an explicit RFC-3339 `captured_at`. `NOT_LOCATED` uses an
empty quote, null `captured_at`, and requires explicit held content.

For `not_checked`, advisory status and `captured_at` are null, the quote is empty, and
`failure_state` is one of `not_checked|source_missing|access_failed|retrieval_failed`.
The finalizer derives all field ids, paths, hashes, authority metadata, reasons,
and evidence rows; a draft cannot override them.

## 4. #667 exact seam

The final requirement result copies the complete #667 `requirement_ref` and each
matching mechanical entry as:

```json
{
  "evidence_ref": {
    "evidence_id": "consent.article-14-materials",
    "evidence_pointer": "/profiles/1/requirements/0/evidence_expected/0",
    "evidence_digest": "1111111111111111111111111111111111111111111111111111111111111111",
    "artifact_type": "consent_materials",
    "held_by": "principal_investigator"
  },
  "responsibility": "packet_owned",
  "deterministic_status": "DOCUMENTED",
  "reason_codes": ["STRUCTURE_DOCUMENTED"],
  "matched_artifact_ids": ["consent.materials"]
}
```

`deterministic_status` is an exact copy of #667 `entry.status`; it is not the
advisory conclusion. Omitting an evidence reference, matched artifact, external
dependency, waiver boundary, or parallel authority is a replay failure.

An applicability-false requirement remains only in the exact copied
`excluded_requirements` array. It cannot become a `NOT_LOCATED` content finding.

## 5. Eligibility and false-missing guards

Content checking is eligible only for an exact #667 entry satisfying all of:

```text
requirement_ref.applicability = true
responsibility = packet_owned
entry.status = DOCUMENTED
matched_artifact_ids is non-empty
```

The following do not dispatch or accept a coverage judgment:

- `external_dependency`;
- deterministic `NOT_LOCATED` or `CONFLICTING`;
- deterministic `APPLICABILITY_UNRESOLVED`;
- a waiver/exception boundary represented as `ACCEPTANCE_UNVERIFIED`; or
- an applicability-false excluded requirement.

These cases remain visible through exact deterministic entry references and use
the matching closed reason. In particular, a profiled route or external
committee artifact cannot create a false missing consent element.

Eligibility is entry-local, not requirement-wide. An external committee sibling
does not suppress a coexisting `packet_owned / DOCUMENTED` participant-material
entry. The final result preserves both deterministic entry references and checks
only the eligible artifact; both live consent requirements use this mixed shape.

The #666 resolved/downstream gate and #667 capability envelope must still be
open. A closed gate has no exact requirement row and is rejected rather than
inventing a carrier row. If the only #667 unresolved reason is
`OVERLAY_SELECTION_NOT_PROVIDED`, selected base requirement entries remain
available but their applicability is incomplete. Each such result is
`not_checked / APPLICABILITY_UNRESOLVED`, retains exact deterministic refs, has
no expectation findings, rejects any draft judgment, and does not inspect
session content.

## 6. Expectation accounting and aggregation

The finalizer dereferences only an exact replay-bound requirement pointer. It
derives and digests every `structured_expectations[]` row. Titles, summaries,
evidence descriptions, filenames, locale, and model memory never select or add a
requirement.

Every profiled expectation is accounted for once. No structured expectations
means `coverage_check_state=not_checked`, null status, and
`NO_PROFILED_STRUCTURED_EXPECTATIONS`; it never means covered.

Expectation aggregation is:

- `DOCUMENTED`: at least one exact replayed bounded passage appears to cover the
  expectation;
- `NOT_LOCATED`: every eligible held artifact was explicitly checked and none
  produced a passage; and
- `CONFLICTING`: at least two exact replayed passages support a conflicting
  coverage observation.

Conflict passages may come from the same artifact or different artifacts, but
their anchors/UTF-8 spans must be distinct. The draft/finalizer must therefore
not use artifact id alone as the uniqueness key.

Requirement aggregation is deterministic over those advisory observations:

1. any `CONFLICTING` -> `CONFLICTING`;
2. otherwise any `NOT_LOCATED` -> `NOT_LOCATED`;
3. otherwise all `DOCUMENTED` -> `DOCUMENTED`.

If any expectation is unperformed, the requirement is `not_checked` with null
advisory status. A partial positive result is not promoted.

The only non-null advisory status values are:

```text
DOCUMENTED
NOT_LOCATED
CONFLICTING
APPLICABILITY_UNRESOLVED
ACCEPTANCE_UNVERIFIED
```

The last two may only preserve the corresponding deterministic boundary. A
draft observation cannot derive applicability or acceptance.

## 7. Evidence-row/1.1

The row carries one exact requirement/expectation binding, an agent-supplied
document locator, one exact #667 artifact binding, an anchor/excerpt block, the
shared rights block, and a canonical digest.

The closed states are:

```text
agent_extracted
checked_no_match
not_checked
source_missing
access_failed
retrieval_failed
```

`agent_extracted` means only that the bounded once-decoded quote is an exact
substring of the supplied session string. It does not authenticate the page or
section locator and does not prove coverage, adequacy, compliance, or acceptance.

`checked_no_match` is source-bound: it records the exact content hash/length that
was checked, but carries no quote or excerpt. It is not available when content is
missing. The four unperformed states carry null content hashes/lengths and null
excerpt fields.

Positive-row `captured_at` is copied from the evaluator's explicit draft field;
it is never synthesized from `context.confirmed_at`, whose value is deliberately
excluded from the #666 semantic context digest and does not attest excerpt
capture.

The row retains the #656 budgets and replay rules: strict UTF-8, one percent
decode, `+` preservation, literal substring matching, no normalization, at most
25 whitespace-split words and 1,000 code points, exact excerpt hash and half-open
UTF-8 span. V1.1 does not cache advisory output; its cache block is fixed to
`not_used/null`.

An illustrative positive row is valid JSON:

```json
{
  "schema_version": "evidence-row/1.1",
  "surface": "authority_profile_content_coverage",
  "row_id": "EVR-COV-000001",
  "coverage_subject": {
    "requirement_id": "tw.hsra.article-14.consent-information",
    "requirement_pointer": "/profiles/1/requirements/0",
    "authority_anchor_pointer": "/profiles/1/requirements/0/authority_anchor",
    "expectation_field_id": "consent.purpose_and_methods",
    "expectation_pointer": "/profiles/1/requirements/0/structured_expectations/2",
    "expectation_digest": "2222222222222222222222222222222222222222222222222222222222222222",
    "document_locator": {
      "kind": "section",
      "value": "研究目的與方法",
      "provenance": "agent_supplied_not_independently_authenticated"
    }
  },
  "source": {
    "artifact_id": "consent.materials",
    "relative_path": "consent-materials.txt",
    "source_artifact_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
    "source_artifact_size_bytes": 57,
    "source_content_sha256": "4444444444444444444444444444444444444444444444444444444444444444",
    "source_content_utf8_bytes": 57
  },
  "anchor": {
    "kind": "quote",
    "value_encoded": "%E6%9C%AC%E7%A0%94%E7%A9%B6%E7%9A%84%E7%9B%AE%E7%9A%84%E8%88%87%E6%96%B9%E6%B3%95%E5%A6%82%E4%B8%8B%E3%80%82",
    "value_decoded": "本研究的目的與方法如下。"
  },
  "excerpt": {
    "state": "agent_extracted",
    "text": "本研究的目的與方法如下。",
    "excerpt_sha256": "5555555555555555555555555555555555555555555555555555555555555555",
    "source_span_utf8": {"start": 0, "end": 36},
    "captured_at": "2026-08-09T08:00:00Z"
  },
  "cache": {"status": "not_used", "key_sha256": null},
  "content_handling": {
    "contains_external_text": true,
    "sharing_scope": "session_only",
    "rights_basis": "not_assessed"
  },
  "row_sha256": "6666666666666666666666666666666666666666666666666666666666666666"
}
```

## 8. Final carrier and reasons

The final root is closed and contains exactly the schema/layer/evaluation
markers, input binding, deterministic status copy, requirement results, excluded
requirements, boundary booleans, and report digest.

A valid empty-carrier shape (semantic replay still decides whether empty result
arrays are correct for its named inputs) is:

```json
{
  "schema_version": "content-coverage-advisory/1.0",
  "layer": "LLM-ADVISORY",
  "evaluation_status": "UNMEASURED",
  "input_binding": {
    "manifest_schema_version": "submission-packet-manifest/1.0",
    "manifest_digest": "7777777777777777777777777777777777777777777777777777777777777777",
    "inventory_id": "packet.inventory.1",
    "inventory_digest": "8888888888888888888888888888888888888888888888888888888888888888",
    "observation_digest": "9999999999999999999999999999999999999999999999999999999999999999",
    "context_record_id": "irb.context.1",
    "context_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "registry_id": "human.subjects.authority.registry",
    "registry_version": "2026-08-09.1",
    "registry_as_of": "2026-08-09",
    "registry_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "resolved_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  },
  "deterministic_status": {
    "review_pathway": "institutional determination required",
    "submission_readiness": "no_listed_gaps_located",
    "authorization_status": {
      "value": "not_provided",
      "source_reference": null,
      "provenance": "caller_supplied_no_derivation"
    },
    "review_timeline": "unknown — obtain current institutional estimate",
    "acceptance_status": "ACCEPTANCE_UNVERIFIED"
  },
  "requirement_results": [],
  "excluded_requirements": [],
  "boundary": {
    "deterministic_status_unchanged": true,
    "submission_readiness_unchanged": true,
    "authorization_status_unchanged": true,
    "institutional_acceptance_unchanged": true,
    "adequacy_not_assessed": true
  },
  "report_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
}
```

The 14 reason literals are:

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

No prose reason or synonym is accepted.

`row_sha256` and `report_digest` use strict canonical JSON: UTF-8, sorted keys,
compact separators, non-finite values forbidden, and only their own digest field
excluded. Unkeyed hashes are integrity checks, not signatures; validation and
rendering still require exact named-input replay.

## 9. Noninterference and rendering

The final deterministic status object is an exact copy of #667:

- `review_pathway`;
- `submission_readiness`;
- the complete caller-supplied `authorization_status` object;
- `review_timeline`; and
- `acceptance_status=ACCEPTANCE_UNVERIFIED`.

The boundary block has five schema-constant true values:

```text
deterministic_status_unchanged
submission_readiness_unchanged
authorization_status_unchanged
institutional_acceptance_unchanged
adequacy_not_assessed
```

Rendering replays the report and all source-bound evidence rows. It never opens a
source, follows a path, calls a model, retrieves a URL, derives a status, or
mutates a carrier. Escape all external values so they cannot create HTML,
comments, links, images, URL autolinks, Markdown headings/fences, extra table
cells/rows, control channels, bidi reordering, or line injection.

The final carrier persists the complete ordered evidence-row array. Each render
call displays exactly one page: default and maximum page size 25, optionally a
smaller positive size, with an explicit one-based page argument. Output names
the previous page, next page, and valid page range. Invalid page/size values fail.
There is no concatenate-all loop, unbounded render path, or `--all` option;
walking pages must yield every evidence row exactly once in carrier order.

## 10. Measurement boundary

Every final carrier has:

```text
evaluation_status = UNMEASURED
```

This is an honest marker, not a measurement record. There is no scored held-out
row for #681, and implementation emits none. No accuracy, precision, recall,
coverage-improvement, or efficacy claim is permitted until a real held-out run is
pre-registered, executed, adjudicated, and published under the shared held-out
measurement contract.

## 11. Hermetic acceptance

Acceptance includes mutation coverage for:

- the exact `LLM-ADVISORY` label and closed root/nested objects;
- #666/#667 all-or-none and exact replay before content access;
- every input binding, requirement/evidence/expectation/authority pointer and
  digest;
- deterministic entry accounting, parallel authorities, conditional exclusions,
  external dependencies, and waiver boundaries;
- positive quote, one-code-point mismatch, strict decode, byte span/hash drift,
  25/26 words, 1,000/1,001 code points, Unicode and `+` handling;
- checked-no-match versus missing/not-checked/access/retrieval states;
- missing content never producing `DOCUMENTED` or `NOT_LOCATED`;
- complete expectation accounting and aggregate precedence;
- no ambient scans, network, subprocess, model, API, cache, or source retrieval;
- inert Markdown/HTML rendering; and
- `UNMEASURED` documentation with no fictitious measurement JSON row.
