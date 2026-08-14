# #656 Shared evidence-row contract V1

## Decision

V1 introduces one shared, closed evidence-row contract and one deterministic
rendering vocabulary. The first live surface is the Stage 2.5 / Stage 4.5 Phase E
Claim Verification Report:

```text
integrity_verification_agent
  -> Integrity Report.phases.E_claims.evidence_rows[]
  -> deterministic 25-row Markdown or HTML page
  -> mandatory integrity checkpoint
```

The canonical artifacts are:

- `shared/contracts/evidence/evidence_row.schema.json`
- `scripts/evidence_rows.py`
- `shared/references/evidence_row_protocol.md`
- this specification

The generic row version is `evidence-row/1.0`. Its required
`surface=phase_e_claim_verification` discriminator limits the live V1 producer and
consumer. Later issues may add another surface only by versioning the schema and
preserving every invariant in this document.

The opt-in Stage 4 -> 5 `claim_audit_results[]` lifecycle is explicitly outside
V1. Its schema, audit agent, cache, finalizer, and formatter gate are unchanged.
The shared evidence row also does not alter `literature_corpus[]`, the human-read
ledger, cite-time LOW-WARN promotion, Phase E verdicts, or the integrity gate.

## 1. Ownership and cardinality

The Integrity Verification Agent is the only V1 producer. It emits one evidence
row for each `(claim_id, ref_slug, anchor)` tuple that Phase E selected. A claim
supported by two citations therefore has two rows; it is not flattened into one
ambiguous source cell. An anchorless claim still emits one explicit empty row.

`E_claims.checked`, `E_claims.verified`, the existing `distortions[]`, and the
Phase E verdict summary remain claim-level. Evidence-row counts are not substituted
for distinct-claim counts.

The full ordered array persists inside Schema 5. Rendering is a view over that
array. There is no total-row persistence cap and no silent truncation, deduplication,
or reordering. This matters at Stage 4.5, where Phase E can legitimately contain
an unbounded number of selected rows.

## 2. Canonical row shape

Every object and nested object is closed. Optional evidence is represented with
explicit JSON `null`, not omitted fields or prose sentinels. The schema is the
field-shape authority; the runtime owns the cross-field, digest, source-replay, and
word-count invariants that JSON Schema cannot express.

The conceptual shape is:

```json
{
  "schema_version": "evidence-row/1.0",
  "surface": "phase_e_claim_verification",
  "row_id": "EVR-000001",
  "claim": {
    "claim_id": "E-C-0001",
    "text": "The reported estimate was 15.2%.",
    "paper_locator": "Results, paragraph 3",
    "selection_tier": "ALL"
  },
  "source": {
    "ref_slug": "smith2024",
    "display_label": "Smith (2024)",
    "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "source_content_utf8_bytes": 14820,
    "source_artifact_sha256": null
  },
  "anchor": {
    "kind": "quote",
    "value_encoded": "The%20estimate%20was%2015.2%25.",
    "value_decoded": "The estimate was 15.2%."
  },
  "verdict": "VERIFIED",
  "detail": "The claim preserves the reported value.",
  "excerpt": {
    "state": "verified_exact_match",
    "text": "The estimate was 15.2%.",
    "excerpt_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "source_span_utf8": {"start": 743, "end": 769},
    "captured_at": "2026-08-09T10:00:00Z"
  },
  "cache": {
    "status": "miss",
    "key_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  },
  "content_handling": {
    "contains_external_text": true,
    "sharing_scope": "session_only",
    "rights_basis": "not_assessed"
  },
  "row_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
}
```

`selection_tier` reuses Phase E's
`HIGH-IMPACT|RANDOM|TOP-UP|ALL` vocabulary. A `NOT-SELECTED` registry item is not
a selected report row; if a caller deliberately records an unperformed selected
check, it uses the `not_checked` evidence state. `verdict` reuses the existing
`VERIFIED|MINOR_DISTORTION|MAJOR_DISTORTION|UNVERIFIABLE|UNVERIFIABLE_ACCESS`
taxonomy without deriving or changing it.

## 3. One evidence-state enum and one display vocabulary

`excerpt.state` is the only provenance / empty-state enum:

| State | Canonical display label | Meaning |
|---|---|---|
| `verified_exact_match` | `VERIFIED EXACT MATCH` | A once-decoded writer quote is byte-for-byte present in the explicit session-held source text. This verifies the excerpt origin, not the claim verdict. |
| `agent_extracted` | `AGENT-EXTRACTED — NOT AUTHORITATIVE` | The agent-selected passage is byte-for-byte present in the session-held source, but a page/section locator was not independently authenticated by this contract. |
| `unconfirmed_anchor` | `UNCONFIRMED ANCHOR` | A writer quote anchor was checked against held source text and did not match. The writer text may be displayed only as an anchor, never as an excerpt. |
| `not_checked` | `NOT CHECKED` | No excerpt check ran. Paragraph anchors use this state in V1. |
| `source_missing` | `SOURCE NOT HELD` | No explicit session source was supplied to the builder. No path or URL is opened to fill the gap. |
| `access_failed` | `ACCESS FAILED` | Stable access or permission prevented source text from entering the session. |
| `retrieval_failed` | `RETRIEVAL FAILED` | An upstream retrieval or extraction attempt failed. The renderer does not retry it. |
| `anchorless` | `ANCHORLESS — NO EXCERPT` | The anchor kind is `none` or the upstream marker was absent and normalized to `none`. |

No producer or renderer may introduce a synonym such as “verified quote,”
“probably supported,” or “source passage unavailable.” The fixed labels are owned
by the runtime.

### 3.1 Closed transitions

- `quote` + held source + exact once-decoded substring ->
  `verified_exact_match`.
- `quote` + held source + mismatch -> `unconfirmed_anchor`.
- `page` or `section` + held source + an explicitly supplied passage that is an
  exact substring -> `agent_extracted`.
- `page` or `section` without a passage cannot fabricate one; it is
  `not_checked`, `source_missing`, `access_failed`, or `retrieval_failed`.
- `paragraph` is always `not_checked` in V1.
- `none` is always `anchorless`.
- An explicit upstream failure state takes the matching empty state and cannot be
  overwritten by cached evidence.

Only `verified_exact_match` and `agent_extracted` carry non-null excerpt text,
excerpt hash, byte span, and capture time. Every other state requires those fields
to be null. Empty text (`""`) and placeholder prose are not excerpts.

The upstream Phase E verdict cannot upgrade the state. In particular,
`verdict=VERIFIED` does not make writer-emitted anchor text a verified excerpt.

## 4. Exact matching and decoding

The builder accepts source text only as an explicit in-memory argument. It hashes
and compares that exact Python string encoded as strict UTF-8. It does not open a
`source_pointer`, URL, DOI, sibling file, corpus directory, or environment-named
path.

Anchor values are percent-decoded exactly once:

1. every `%` must be followed by exactly two hexadecimal digits;
2. the resulting bytes must decode as UTF-8 with `errors=strict`;
3. `+` remains `+` (form-style `unquote_plus` is prohibited);
4. no Unicode, whitespace, newline, punctuation, case, or quote normalization is
   performed;
5. matching is a literal substring comparison.

Thus `%3Cscript%3E` becomes `<script>` and is then escaped for display;
`%253Cscript%253E` becomes `%3Cscript%3E` and is never decoded a second time.
NFC versus NFD, ASCII space versus NBSP, smart versus straight quotes, and case
changes are mismatches.

The 25-word ceiling uses `len(text.split())`, matching the existing v3.7.3
convention. It is applied after one-time decoding to quote anchors and to every
persisted excerpt. A second 1,000-code-point ceiling prevents unspaced CJK or
zero-width text from bypassing the word limit. Over-budget input is rejected; it
is never silently truncated.

## 5. Hash and span semantics

- `source_content_sha256` is SHA-256 over the exact session-held source text's
  UTF-8 bytes. It is not the PDF, HTML, cache-file, or passport artifact hash.
- `source_content_utf8_bytes` is the length of those same bytes.
- `source_artifact_sha256` is nullable provenance for raw artifact bytes. It can
  never substitute for the content hash.
- `excerpt_sha256` is SHA-256 over the exact excerpt UTF-8 bytes.
- `source_span_utf8.start/end` is a half-open byte interval into the hashed source
  text. Replaying that slice must yield exactly the excerpt bytes.
- `row_sha256` is SHA-256 over deterministic canonical JSON of the complete row
  excluding only `row_sha256`. Cache telemetry is therefore integrity-bound; a
  miss-to-hit replay recomputes the row digest.

Duplicate `row_id` values are invalid within one report. Row order is the
producer's document order and is part of the rendered view.

## 6. Cache behavior

The runtime may receive one prior persisted row as a cache candidate. The key
binds at least the schema version, surface, source-content hash, decoded anchor,
anchor kind, excerpt candidate where applicable, extractor version, and both text
budgets.

Only source-bound `verified_exact_match`, `agent_extracted`, and
`unconfirmed_anchor` rows are cacheable. A hit is accepted only after the current
session source, schema, hashes, exact match or mismatch, and all cross-field
invariants replay successfully. Source, anchor, claim/source identity, schema,
budgets, or excerpt-candidate drift is a miss. A malformed or internally
inconsistent cache candidate fails closed as a cache input: it is discarded and
the builder deterministically rebuilds from the current explicit source/anchor
inputs. Corrupt content is never returned or rendered as a hit.

A hit preserves the original excerpt bytes, byte span, provenance state, and
`captured_at`; only `cache.status`, the integrity-bound row digest, and other
explicit cache telemetry may change. Empty and failure states use
`cache.status=not_used`. The renderer never opens or writes a cache and never
renders cached Markdown or HTML.

## 7. Rendering and paging

The runtime provides deterministic Markdown and HTML renderers. Before a
source-bound row (`verified_exact_match`, `agent_extracted`, or
`unconfirmed_anchor`) can render, the caller MUST pass an explicit in-memory
`ref_slug -> exact session-held source text` map. The renderer replay-validates
the content hash, byte length, once-decoded anchor, exact match or mismatch,
excerpt hash, and byte span against that text. A persisted row and its unkeyed
hashes are integrity checks, not signatures, and cannot establish provenance by
themselves. Missing replay text is a render failure; the renderer never follows
a source pointer to fill it.

Rendering performs no source retrieval, ambient filesystem read, network call,
model call, extraction, state derivation, or cache lookup. Replay validation may
recompute the strict once-decode and hashes from the immutable row plus the
explicit source map; it never decodes the stored display value a second time or
changes the row.

Every external string is treated as untrusted data. The HTML renderer uses
attribute-safe HTML escaping. The Markdown renderer escapes HTML, table pipes,
backslashes, link/image syntax, emphasis, code fences, headings, comments, and
line boundaries. Controls and bidi formatting cannot create a second row,
heading, cell, link, image, tag, comment, or instruction channel. The renderer
shows only the bounded excerpt or decoded anchor stored in the row; surrounding
source text never appears.

The default and maximum page size are 25 rows; callers may request a smaller
positive page. There is no `--all` mode. Every page reports:

```text
Page P/N, rows A-B of M
```

Walking the requested pages must reproduce every original `row_id` exactly once
and in order. Page zero, negative or out-of-range pages, page size zero, and page
sizes above 25 fail rather than wrap or truncate.

## 8. Persistence, legacy reports, and handoff

`phases.E_claims.evidence_rows[]` is additive to Schema 5. A current producer
emits one row for every selected tuple, including explicit empty states. The full
array travels with the existing Integrity Report at Stage 2.5 -> 3 and Stage 4.5
-> 5; no new passport aggregate or transition is introduced.

A positively identified pre-#656 report may omit `evidence_rows`. Consumers use
the explicit `--allow-legacy-absence` compatibility flag and label that state
`LEGACY — EVIDENCE ROWS UNAVAILABLE`. Missing-field shape alone is never legacy
proof: without the flag, render fails. Absence is not an empty successful check,
does not manufacture excerpts, and does not retroactively change the report's
historical Phase E verdict. A current producer emitting selected claims but
omitting rows is a contract failure and may not use the compatibility flag.

For a current report, the runtime adapter requires the number of distinct
`claim_id` values to equal `E_claims.checked`, the number of distinct claims
whose unchanged Phase E verdict is `VERIFIED` to equal `E_claims.verified`, and
every row sharing a `claim_id` to carry the same claim object and verdict. Thus
`checked > 0` with an empty array and contradictory multi-source rows fail.
The E1 Claim Registry remains the selection authority for the exact
`(claim_id, ref_slug, anchor)` tuple set; V1 does not persist a second selection
manifest, so tuple-by-tuple completeness beyond these report-level checks is a
producer/checkpoint obligation rather than a fact derivable from the row array
alone.

Downstream prompts point to this contract and consume rows by pointer. They do
not copy the enum, infer provenance from prose, or use a rendered table as the
machine artifact.

## 9. Rights and private-data boundary

Persisting a 25-word excerpt is an adjudication aid, not a rights determination.
Every row carries:

- `sharing_scope=session_only|user_confirmed_shareable`
- `rights_basis=not_assessed|user_declared_authorized`

The default is `session_only + not_assessed`. A shareable row requires the
explicit authorized pair; the runtime never infers permission from an open URL,
repository, DOI, or “public” label. Exporters that cannot preserve the caveat
must remove the excerpt rather than silently publicize it. Private corpus text,
abstracts, notes, and surrounding context never enter the row.

## 10. Verdict and read-ledger noninterference

Evidence provenance describes how the displayed excerpt was obtained. It does
not decide whether a claim is supported. Phase E continues to own claim verdicts,
severity, issue counts, `PASS|PASS WITH NOTES|FAIL`, and correction routing.

Displaying an excerpt is not reading the source. Building, validating, caching,
or rendering rows must not import, invoke, or write `/ars-mark-read`,
`human_read_log`, `human_read_source`, `read_scope`, or cite-time LOW-WARN
promotion. The #513 latest-event and read-scope semantics remain byte-for-byte
outside this contract.

## 11. Failure behavior and CLI

The executable is standard-library-only, loads strict UTF-8 JSON with duplicate
keys and non-finite numbers rejected, and opens only the explicitly named row and
session-source fixture paths supplied to the CLI. It never follows a source value
inside those files.

Both CLI `validate` and CLI `render` require `--source-map` whenever any input
row is source-bound. The direct Python `validate(row)` call without its optional
source argument is structural/integrity validation only and must not be
represented as provenance replay.

CLI `render` treats a missing `evidence_rows` field as a contract failure by
default. `--allow-legacy-absence` is an explicit compatibility assertion for a
positively identified pre-#656 report; only then does it emit the fixed legacy
marker with exit 0.

Exit classes are:

- `0`: valid row set or rendered page;
- `1`: schema, semantic, hash, replay, duplicate-id, or page-data failure;
- `2`: named-input read/parse or command-line invocation/usage failure.

No live API, model, judge, browser, or source retrieval is part of acceptance.

## 12. Acceptance and mutation coverage

Hermetic acceptance covers at least:

- exact quote, one-code-point mismatch, page/section extraction, paragraph/none,
  missing source, access failure, retrieval failure, and not-checked states;
- strict single decoding, malformed escapes, invalid UTF-8, double encoding,
  encoded whitespace, and `+` preservation;
- 25/26 words, 1,000/1,001 code points, CJK, emoji, combining sequences, NBSP,
  and ZWSP;
- forged provenance, changed source, wrong content versus artifact hash, changed
  byte span, changed excerpt hash, rebound row digest, and a fully rebound row
  refused at render time without the original explicit session source;
- cache hit, miss, content drift, anchor drift, corrupt payload, and timestamp
  preservation;
- Markdown/HTML table, heading, fence, tag, comment, link, image, control, bidi,
  percent-encoded, and prompt-injection payloads;
- 0/1/25/26/1,001-row paging with no loss, duplication, reorder, or `--all`;
- unchanged human-read ledger bytes and adjacent #513/v3.7.3 tests;
- static pointers from Schema 5, the Phase E protocol and producer, and the
  mandatory checkpoint renderer to this single contract.

## 13. Explicit non-goals

V1 does not:

- add or modify `claim_audit_results[]`;
- fetch a source at display time (the caller supplies already-held source text
  only for deterministic replay validation);
- prove that a page or section locator is authoritative;
- treat an exact quote match as proof that the surrounding claim is supported;
- persist full source text, abstracts, private notes, or rendered markup;
- mark a source as human-read or alter LOW-WARN promotion;
- add a new stage, gate, passport aggregate, or closure condition;
- claim that the 25-word ceiling grants quotation or redistribution rights.

## 14. Versioned #681 extension

#681 adds `evidence-row/1.1` at
`shared/contracts/evidence/evidence_row_v1_1.schema.json` rather than widening
the closed 1.0 object. Its only surface is
`authority_profile_content_coverage`, and it replaces Phase E claim/verdict
fields with exact authority requirement, structured-expectation, packet
artifact, and advisory document-locator bindings. Version 1.0 schema bytes,
builder defaults, cache behavior, Phase E report adapter, and rendered output
remain the compatibility baseline.

The extension reuses the strict once-decode, exact UTF-8 source replay,
25-word/1,000-code-point limit, byte-span/hash, inert rendering,
content-handling, and read-ledger boundaries. It introduces no cache use and no
new provenance authority: its `agent_extracted` locator is explicitly
agent-supplied and not independently authenticated. `checked_no_match` records
that named session content was inspected without a selected bounded passage;
it is not proof of semantic absence. Other failure states remain explicit and
empty.

The containing `content-coverage-advisory/1.0` carrier is a distinct
`LLM-ADVISORY` surface governed by
`shared/references/authority_content_coverage_advisory_protocol.md`. Exact
passage provenance never changes a #667 deterministic status, readiness,
authorization value, institutional acceptance, or adequacy assessment. The
surface remains `UNMEASURED` until a real held-out scored row exists; the
marker itself is not a measurement artifact.
