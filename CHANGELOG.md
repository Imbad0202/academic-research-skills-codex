# Changelog

All notable changes to the Codex package are documented here.

## Unreleased

- Added Windows marketplace recovery guidance for
  [#43](https://github.com/Imbad0202/academic-research-skills-codex/issues/43),
  linked from all four READMEs: preserve a working snapshot, replace the ARS Git
  source with a local marketplace, verify installation, and update or roll back
  manually. Codex CLI 0.164.0 ships upstream staging-cleanup fixes, so the
  guide asks users to check the bundled CLI version first. The Windows
  `os error 5` failure in #43 has not been retested on 0.164.0.

## [3.24.0] - 2026-10-27

### What's Changed

- Synced the tagged ARS v3.24.0 release at
  `b34c63f828b3535f403079a4f42bc7955da2f64b`, preserving Codex WORKFLOW
  overlays, the single registered router, and the separately pinned
  experiment-agent. No new workflow.
- Review letters gain two advisory attachments before the acronym check.
  The suggested-reference check looks up the works Reviewer 2 and Reviewer 3
  recommend. In Codex it runs only on an explicit request, because it calls the
  four bibliographic resolver clients; otherwise its section says the check did
  not run. A found record does not show that a work supports the recommendation.
- The reviewer claim check sends the seat-blind panel findings and the
  manuscript to one fresh, tool-less native worker of the active Codex model,
  and lists a contradiction only when the judge's quotation matches the
  manuscript. It is on by default; `ARS_PANEL_CLAIM_CHECK=0` turns it off.
  Without an isolated worker it does not run and is never judged inline. The
  upstream contrast gate passed `gpt-6-astra`, Gemini 4 Argon, and two Claude
  models; `gpt-6-astra` is the only Codex model it measured.
  Neither attachment feeds the decision, roadmap, or re-review criteria.
- Adopted the integrity-rule repairs: a prior report is fresh only under 24
  hours, also within one session; a revised paper entering at Stage 5 runs
  Stage 4.5 first; Stage 4' follows Stage 3' only after a Major decision.
- The held-out #1002 audit dispatcher, the one-process guard launcher, the
  guard's tool-name notes, and the update-only startup notice are preserved as
  inactive references. Hermetic tests do not establish live Codex compliance or
  the checks' accuracy on real reviews.
- Updated source/version metadata, four-language guidance, runtime contracts,
  quality gates, boundary content locks, citation metadata, and the
  materialized plugin mirror.

## [3.23.2] - 2026-10-26

### What's Changed

- Added `CITATION.cff` and a DOI badge in all four READMEs for the Zenodo
  concept DOI [10.5281/zenodo.20784820](https://doi.org/10.5281/zenodo.20784820).
  Zenodo reads the citation file for later releases, so their creators follow its
  author list instead of the GitHub contributor list.

- Synced the tagged ARS v3.23.2 release at
  `863e1c754f0e97062d271dcb42a9483c9ef34aa9`, preserving Codex WORKFLOW
  overlays, the single registered router, and the separately pinned
  experiment-agent. No new workflow.
- Claim checks at Stage 2.5 and 4.5 use only the manuscript's cited version.
  Unreadable versions produce `UNVERIFIABLE_ACCESS` and a request for that
  version's PDF; ambiguous citations also record `VERSION_INCONSISTENT_CITATION`.
  Evidence rows identify the version, and one source's access limitation does
  not hide distortion found in another source.
- Stage 2.5 always runs before Stage 3. A prior verified, fresh report on the
  current version is context, never a replacement. Missing required inputs
  block handoff with `HANDOFF_INCOMPLETE`; recommended inputs remain advisory.
- Adopted Obsidian ISO-date support, rejection of boolean and superscript-digit
  years, six POSIX-path lint repairs, and the Socratic mentor example that
  preserves the user's authorship of research questions.
- Preserved upstream SessionStart user-notice and Pi structured-prompt repairs
  as inactive reference integrations. Hermetic tests and upstream Claude
  fixture results do not establish live Codex compliance or Windows execution.
- Updated source/version metadata, four-language guidance, runtime contracts,
  boundary content locks, citation metadata, and the materialized plugin mirror.

## [3.23.1] - 2026-10-16

### What's Changed

- Synced the tagged ARS v3.23.1 release at
  `4c5449017f46eb64d112a301d4817d22c7c9f3d9`, preserving Codex runtime/path
  overlays and the separately pinned experiment-agent v1.1.0. No new workflow.
- Released directly after v3.22.2. The v3.23.0 sync remains in main history at
  `52228e8280dd1770e18ecfc3b1fdf16b13b58104`; no v3.23.0 tag or GitHub Release
  was published. This release includes that sync without backfilling a release.
- Adopted the sr-screener CSV repair: detect only the delimiter and retain
  RFC 4180 double-quote escaping, including quoted fields beyond the sample,
  apostrophes, leading spaces, and single-column exports. Added Codex import
  regression coverage alongside the six upstream cases.
- Vendored the write-scope guard's own-plugin prefix normalization, compatible
  timeout probe, captured payload fixtures, and coverage documentation.
  These are inactive Claude-hook references in Codex; its optional hook pack
  only announces metadata and provides no PreToolUse write fence. Even the
  upstream fence requires a named Bucket A agent type and excludes inline roles.
- Carried the upstream `gemini-4-argon` Google verifier recommendation as
  provisional; `gemini-3.1-pro-preview` retains its upstream validated status.
  Gemini notices no longer direct users to the OpenAI-only smoke script.
  No Gemini smoke, bakeoff, or Codex provider validation is claimed, and the
  native Codex model policy and explicit provider/content/cost consent remain.
- Propagated the mid-message `[direct-mode]` rule into the single Codex router
  and core workflows. The planner strips residual tokens before forwarding a
  request, without granting mid-message or later-turn escape-hatch authority.
  Upstream #892 remains open after its Claude smoke failed
  acceptance; deterministic Codex tests do not establish live model compliance.
- Preserved upstream lint and Windows path repairs and the md-to-word
  third-party listing. Updated four-language version guidance, source locks,
  runtime boundaries, and the materialized Desktop bundle.

## [3.23.0] - 2026-10-04

### What's Changed

- Synced the tagged ARS v3.23.0 release at
  `6ab4b03bf70a118a1b3ee7f3263ed9f19031061b` (released upstream on October 3),
  preserving Codex runtime/path overlays and the separately pinned
  experiment-agent v1.1.0.
- Added `sr-screener` v1.0.0 as the sixth local workflow behind the single
  Codex router. Its eight modes are `protocol`, `quick`, `pilot`, `ta-screen`,
  `ft-screen`, `adjudicate`, `audit`, and `report`. Screening requires an
  explicit request; `deep-research` `systematic-review` never starts it
  automatically. Two blinded reviewer roles and an adjudicator support
  author-confirmed eligibility rules, with local import, deduplication,
  screening-log, RIS, PRISMA-count, methods-draft, and corpus exports.
- Preserved screening safeguards: the full title/abstract run requires a
  pilot against the review team's labels with no missed advanced records
  unless the user records an override; joint exclusions need a reproducible
  senior-reviewer QC sample (minimum 20, default 100; all when fewer are
  available) before counts become final. Missing or malformed decisions remain
  pending, spreadsheet exports
  neutralise formula text, and the review team verifies AI decisions.
  Synthetic script tests do not establish screening accuracy.
- Adopted pipeline repairs: the external Audit Artifact Gate is opt-in and
  off by default; the Stage 2.5 and 4.5 integrity gates remain active.
  Experiment intake comes from the scholar's answer, confirmed run-wide
  constraints retain the author's words, and a declined-only Major may offer
  an author-approved limitations-only revision. Stages 5 and 6 produce only
  requested files, while opt-in finalization refusals surface at Stage 4.5.
- Carried forward integrity evidence replay from the orchestrator's named
  folder, consistent integrity policy, and exclusion of sources found
  fabricated from later revisions. Ledger `report` and `show` share trusted
  reads; parse errors omit ledger text, and writers share atomic replacement.
- Added provenance-labelled per-source method weaknesses, the neutral
  author-owned review-form note, and the RQ Brief schema/producer alignment.
  New held-out cases and routing fixtures remain bounded evaluation inputs;
  prompt adherence and Codex model effectiveness are unmeasured.
- Updated the upstream `ars-citation-check` recipe to inherit the session
  model alongside `ars-full`, `ars-reviewer`, and `ars-revision-coach`.
  Remaining `sonnet` hints are Claude metadata and do not select a Codex model.
- Updated four-language release guidance and the materialized Desktop bundle.
  Claude loader files and hooks remain inactive in the Codex distribution.

## [3.22.2] - 2026-09-28

### What's Changed
- Synced the tagged ARS v3.22.2 release at
  `7de1c9dfb7af9c02a9b57750761323f35a743aa2`, including v3.22.1 repairs,
  while preserving Codex runtime/path overlays and the separately pinned
  experiment-agent v1.1.0.
- Added the local run-ledger schema, CLI, and pipeline instructions for exact
  user wording, step receipts, file hashes, and rendered English/Traditional
  Chinese handoff checks after compaction, resume, and subagent returns.
  Receipt input hashes are computed on append and rechecked on report; ledger
  contents do not create user authorization, and its hash chain detects
  accidental damage rather than deliberate edits, rollback, or a lost tail.
- Added the deterministic, local acronym checker for saved manuscripts and
  abstracts. Coverage limits remain explicit; review reports are advisory
  attachments excluded from decisions, revision roadmaps, and re-review criteria.
- Adopted the broader instruction/data boundary across intake, dispatches,
  passport imports, and tool reads. The changed opt-in claim-audit judge prompt
  partitions cache entries from older prompt versions.
- Carried forward routing fixes that keep explicit requests in their selected
  mode when inputs are missing, retain literature review within its chosen
  workflow, and distinguish peer review from committee correspondence.
- Adopted Chinese APA 7 citation-check repairs: preserve abbreviation
  exceptions and reference-list authors, require evidence of stroke-order
  inversion, and separate visible syntax errors from unverified source claims.
- Updated four-language release guidance and the materialized Desktop bundle.
  Upstream Claude model audits, routing smoke results, and plugin evaluation
  fixtures remain reference evidence; they do not establish Codex model
  effectiveness. Claude plugin hooks remain inactive, and prompt adherence is
  unmeasured.

## [3.22.0] - 2026-09-16

### What's Changed
- Aligned the ARS-Codex release number with ARS, replacing the independent
  `0.1.x` numbering from this release onward. Historical entries keep their
  original versions; package and upstream suite versions are checked together.
- Synced the tagged ARS v3.22.0 release at
  `3c546bc08c56f79e0068f1ea4f0acedf5bf69b5e`, preserving Codex path overlays,
  runtime policy, and the separately pinned experiment-agent v1.1.0.
- Added the Phase-1 `output_language_pair` contract and abstract consumer chain.
  Only `zh-tw-en` is registered; omitted values retain legacy output, while
  malformed or unsupported values fail visibly. Spanish output packs remain
  outside this release's supported registry.
- Propagated Spanish intent triggers into the single Codex router and planner,
  including separate manuscript-revision and reviewer-simulation routes.
- Adopted the upstream Windows file-lock helper and canonical API-effort,
  contained citation-transport, audit-provenance, and writing-diagnostic fixes.
  Unknown judge identities now isolate cache entries by audit run, retaining
  deduplication within that run without cross-run reuse.
- Vendored reviewer-calibration infrastructure, Claude plugin eval source
  suites, Spanish README, and frozen locale changelog archives. These sources
  do not establish measured Codex effectiveness or launch live evaluations.
- Updated four-language release guidance and the materialized Desktop bundle.

## [0.1.29] - 2026-09-06

### What's Changed
- Synced ARS v3.21.2 at `8fa3d651ad45da9e02762a6ba1fa3d1f231f91b6`,
  preserving Codex path overlays and the separately pinned experiment-agent.
- Read the complete Astra (117 pages) and Fable/Mythos 5.1 (212 pages) system
  cards; recorded source hashes, section coverage and implementation decisions
  in `codex/audits/2026-09-06-model-alignment.md`.
- Added project-scoped GPT-6 Astra/xhigh configuration and an explicit planner
  model policy: routine medium, complex judgement xhigh, supported overrides,
  launch arguments, and separate requested/caller-observed provenance.
- Replaced manual-only native delegation with adaptive bounded collaboration;
  retained opt-in fixed topologies/hooks, blinded review, author authority and
  integrity gates. Removed stale self-scoring, fixed question counts and generic
  punctuation/paragraph quotas; unsupported facts cannot be repaired by hedging.
- Corrected upstream Astra API payloads and effort preflight, rejected
  delegation-requesting ultra in the citation-only transport, and updated the
  independent audit launcher to Astra. General Codex research still supports
  explicit max/ultra; API and contained transport vocabularies remain distinct.
- Removed the implicit old-model identity from claim-audit cache provenance;
  unknown model identity bypasses cache instead of mislabelling execution.
- Fixed natural-language review and format-conversion routing, restored all
  five reviewer seats in output validation, and clarified that the planner's
  package gate catalog is not a requirement to execute every gate per request.
- Opened upstream issues #823–#826 for the confirmed API, transport, writing
  harness and executable/cache findings.
- Updated four-language setup guidance and materialized Desktop plugin bundle.
  Historical model measurements remain unchanged; Astra verifier promotion
  remains provisional pending a real transport-specific bakeoff.

## [0.1.28] - 2026-09-02

### What's Changed
- Synced the vendored ARS suite through post-`v3.21.1` upstream `main` commit
  `94436237913091d4739870159d241660527e8338`; upstream suite metadata remains
  at `3.21.1`, and component metadata remains unchanged.
- Added Chinese-aware title matching across the four bibliographic index
  resolvers and restricted CJK outer-wrapper stripping to one balanced unit.
- Declared the `markdown-it-py` development dependency used by surface-form
  checks, made a missing PyYAML dependency fail visibly, and expanded the
  associated hermetic regression coverage.
- Vendored the new upstream skill-inventory parity lint and mutation tests.
  Its Claude-distribution real-tree gate remains inactive because ARS-Codex
  intentionally uses one router, `WORKFLOW.md` entries, and no Claude loader
  manifests or skill symlinks; the Codex-native gate now requires exact core
  workflow parity among disk, the root router, and the full-runtime manifest.
- Hardened source ownership validation so a secondary repository cannot claim
  a core workflow path and silently exempt it from version checks.
- Added the September harness-retirement audit and synchronized the R10 risk
  register, MLA citation-key wording, setup guidance, and upstream test
  manifest.
- Preserved the single-root Codex router, existing path-sensitive validator
  overlays, materialized Desktop plugin mirror, and separately pinned
  experiment-agent v1.1.0 tree.

## [0.1.27] - 2026-08-24

### What's Changed
- Synced the vendored ARS suite to the signed `v3.21.1` release at
  `127ff85e4bbfcdd10b95040537b6c6bd7ad17aeb`.
- Added the default-off deterministic research-workflow profile substrate and
  opt-in `ARS_INQUIRY_LEDGER=1` branch-ledger alpha, preserving explicit
  selection, visible field-general fallback, append-only correction, bounded
  summaries, and non-destructive stale-state semantics.
- Vendored sealed preregistration contracts and hermetic tests for future model
  promotion bakeoffs, plus the retained GPT-5.6 Sol Codex-transport bakeoff
  evidence. The history-dependent tree verifier remains an upstream
  release-discipline tool because the vendored subtree has no upstream Git
  history.
- Adopted the Codex CLI 0.147.0 citation-transport repairs: authentication
  attestation may arrive on stdout or stderr, the provider schema omits
  unsupported `uniqueItems` while local duplicate rejection stays fail-closed,
  and the bounded search host remains available without widening the accepted
  event grammar.
- Added the source-backed review-criteria proving set, exact-profile source
  receipts, shared Markdown grammar, workflow-profile and inquiry-ledger
  runtimes, contracts, and hermetic tests.
- Preserved the single-root Codex router, `WORKFLOW.md` entrypoint and content
  lock overlays, inactive Claude-only validators, MiniMax compatibility layer,
  materialized Desktop plugin mirror, and separately pinned experiment-agent
  v1.1.0 tree.

## [0.1.26] - 2026-08-18

### What's Changed
- Synced the vendored ARS suite through the signed `v3.21.0` release at
  `2b639c12ee4e7c694a32336cc59dc2616e0d89fe`, rolling the unreleased
  v3.20.1 alignment into the same Codex package version.
- Added the default Socratic non-generation exit: non-convergence alone no
  longer authorizes system-authored research-question candidates.
- Adopted categorical, criterion-bound reviewer judgements, `NOT_CALIBRATED`
  live packages, and six-axis panel provenance while retiring numeric reviewer
  scores, weights, aggregates, and score trajectories.
- Added exact-span/raw-byte claim-registry coverage, claim-strength disposition
  sidecars, required scope for new human-read attestations, and a closed
  deterministic attestation resolver.
- Vendored the bounded claim-standing stance and blind ideation-assignment
  evaluation infrastructure with its consent, provenance, no-call, and
  unmeasured boundaries.
- Added the v3.21 claim-standing query-plan, affirmative-consent, freshness,
  transmission-ledger, and pipeline-wiring contracts. Eligibility remains an
  offer signal and never dispatches an external call.
- Vendored the canonical data-flow map, control-availability matrix,
  stage-capability matrix, risk register, governance statement, and their
  deterministic transparency checks.
- Documented the Codex bibliographic routing boundary: ordinary discovery and
  inline ingest use browsing; `ars-full` alone does not launch the four Python
  resolver clients; programmatic citation verification and claim-standing
  discovery retain separate explicit triggers.
- Preserved the single-root Codex router, `WORKFLOW.md` path adaptations,
  inactive Claude-only calibration and distribution-surface gates,
  materialized Desktop plugin mirror, and the separately pinned
  experiment-agent v1.1.0 tree.

## [0.1.25] - 2026-08-14

### What's Changed
- Synced the vendored ARS suite to the `v3.20.0` release at
  `3af9f03d5aadb0bca51af1440f20b5cbf97d6dba`.
- Added evidence-bound review and revision contracts, including durable
  evidence rows, author-confirmed review criteria, non-ranking revision
  roadmaps, author adjudication, and revision-evidence bundles.
- Added the contained, consent-gated Codex citation transport for narrow
  citation-integrity checks, plus stronger human-subjects authority boundaries.
- Vendored the optional sandboxed PDF content classifier as an advisory tool;
  it is not a required dependency and does not change structural PDF preflight.
- Adapted the v3.20 indirect-injection no-call envelope to verify its upstream
  suite commit through the package source lock when the nested vendor tree has
  no `.git` directory.
- Preserved the single-root Codex router, `WORKFLOW.md` entrypoint mapping,
  inactive Claude-only hooks, and separately vendored experiment-agent v1.1.0.

## [0.1.24] - 2026-08-06

### What's Changed
- Updated the separately vendored experiment-agent tree from
  `9b063fa895eaf1f63ac99ac03f924f8d31aa8d26` (pre-`v1.0.1`) to
  `e291e7dc7ca268b2de7e1a9cf23bc2eef5dc0651` (`v1.1.0`, upstream main head).
- Added the v1.1.0 session-resume capability for `study_manager_agent`: the
  study-state protocol (`references/study_state_protocol.md`), the
  `study_state.md` template and worked example, the session-resume design
  spec and implementation plan under `docs/`, and the expanded
  `study_manager_agent` resume flow.
- Preserved the experiment-agent `WORKFLOW.md` entrypoint rename with its
  Codex `data_access_level`/`task_type` frontmatter overlay; upstream
  `.claude/` and `.github/` dev files remain excluded. The ARS vendored tree
  is unchanged from 0.1.23 (still pinned at `5769d7b`).

### Notes
- This closes the experiment-agent half of the 2026-08-06 alignment; both
  vendored source repositories now track their upstream main heads.

## [0.1.23] - 2026-08-06

### What's Changed
- Updated the vendored ARS runtime from
  `828ef3b613b0e8b91830da3328a1e33d4eb5ab4c` (`v3.19.0`) to
  `5769d7b51adfba45593ad95721436fd114aaa735` (post-`v3.19.0` main,
  2026-08-06). No worktree or branch content is included — the pin is the
  upstream `main` head.
- Added the reviewer hardening track: the #574 role-scoped scoring contract
  with abstention and per-mode decision contracts, typed evidence anchors,
  coverage receipts and severity transport, the #576 three-gate Stage 3'
  re-review pre-commitment contract (schemas + synthesis checker +
  patch_digest), the #608 dispatch harness, the #609 empty-dissent rule, the
  #610 AR arithmetic-receipt grammar with the step-5 deterministic receipt
  calculator, and #611 protocol text-consistency locks.
- Vendored the new held-out eval sets and adjudicated cohorts (seeded
  defects, persuasion-invariance paired controls, #610 baseline/post
  cohorts), medical venue disclosure policies with fail-closed rendering and
  the Frontiers submission-action fix, the Chinese-literature resolver client
  and API protocol, CARE / STARD 2015 / TRIPOD+AI condensed guidance with a
  study-design routing sequence, and bare `/ars-*` alias frontmatter names.
- Vendored the community-maintained Pi wrapper (`pi/` + root `package.json`)
  and `.gitleaksignore` for traceability; the Pi wrapper targets upstream
  SKILL.md paths and is not a Codex entrypoint.
- Extended the `WORKFLOW.md` path adaptation to the new reviewer-contract
  lint family (decision contract, reviewer finding contract, reviewer role
  label, venue disclosure harness, and their tests); re-pinned the pipeline
  content locks after the overlay. Declared `check_calibration_tiers.py`
  inactive (it requires the non-vendored `.claude/CLAUDE.md`) and removed its
  entry from the vendored local pytest manifest.
- Preserved the single-root-skill layout, `WORKFLOW.md` entrypoint mapping,
  Codex provider/content/consent boundaries, nested-distribution validator
  adaptations, macOS/Python compatibility patches, and materialized Desktop
  plugin bundle.

### Notes
- This sync pins upstream `main` at `5769d7b` (44 commits past `v3.19.0`);
  the upstream suite version remains 3.19.0 until the next ARS release tag.

## [0.1.22] - 2026-07-22

### What's Changed
- Updated the vendored ARS runtime from
  `bbc0659272a511b422f6856cd6f44b6ccb2ac213` (`v3.18.0`) to
  `828ef3b613b0e8b91830da3328a1e33d4eb5ab4c` (`v3.19.0`).
- Added the local-PDF read-integrity preflight and sidecar contract, optional
  human-read `read_scope` attestations with partial-coverage handling, and
  revision-round claim-drift guards built from the claim-strength ladder and
  deterministic token-conservation checker.
- Vendored the new human-read ledger schema, revision evidence and held-out
  measurement set, plus the PDF/read-scope design records and associated test
  coverage.
- Preserved the single-root-skill layout, `WORKFLOW.md` entrypoint mapping,
  Codex provider/content/consent boundaries, nested-distribution validator
  adaptations, macOS/Python compatibility patches, and materialized Desktop
  plugin bundle. Re-pinned the pipeline content lock after the v3.19 overlay.

### Notes
- This sync pins the exact ARS release tag `v3.19.0`.

## [0.1.21] - 2026-07-18

### Changed
- Renamed the Codex plugin identity, marketplace, and plugin directory to
  `ars-codex` so the Codex-native sibling is clearly distinguished from the
  upstream Claude Code ARS distribution.
- Updated the plugin display name to `ARS-Codex` and added CLI-first
  marketplace installation instructions for external users.
- Kept the bundled skill identifier `$academic-research-suite` stable to avoid
  breaking existing Codex workflow prompts and direct skill installations.

## [0.1.20] - 2026-07-18

### What's Changed
- Updated the vendored ARS runtime from
  `039d94f670c47d996ca919d37b8753b0a8d4a140` (`v3.17.0`) to
  `bbc0659272a511b422f6856cd6f44b6ccb2ac213` (`v3.18.0`).
- Added the fixed-seat cross-model Reviewer 2 track, independent re-review
  judge pass and Judge Record, cache-age advisories with opt-in live
  re-validation, high-impact-first claim sampling, scope-conformance and
  search-bounded novelty advisories, and the held-out pipeline robustness set.
- Preserved Codex provider/content/consent boundaries: external reviewer and
  judge tracks are never simulated, single-family or fallback execution is
  disclosed, and live cache re-validation stays tied to explicit verification
  work.
- Vendored the upstream SessionStart update checker for traceability and tests
  without installing it as a Codex hook. Preserved the single-root-skill
  layout, `WORKFLOW.md` entrypoint mapping, nested-distribution validator
  patches, macOS/Python compatibility patches, and the materialized Desktop
  plugin bundle.

### Notes
- This sync pins the exact ARS release tag `v3.18.0`.

## [0.1.19] - 2026-07-17

### What's Changed
- Updated the vendored ARS runtime from
  `73c898c842afae3f163ac571dfa098c72d7c82af` (`v3.16.0`) to
  `039d94f670c47d996ca919d37b8753b0a8d4a140` (`v3.17.0`).
- Added the canonical cross-model handoff envelope and dispatcher contract,
  least-privilege tools allowlists, executable panel-synthesis validation,
  pinned Stage 5/6 boundary semantics, the machine-readable degradation
  registry, and hermetic citation-gate transport fixtures.
- Mapped dispatched cross-model transport to the Codex dispatching context,
  preserved explicit provider/content/consent gates, and exposed the new
  upstream validators in the optional full-runtime manifest.
- Preserved the single-root-skill layout, `WORKFLOW.md` entrypoint renaming,
  nested-distribution validator patches, macOS/Python compatibility patches,
  and the materialized Codex Desktop plugin bundle. The pipeline-orchestrator
  content-lock hash changes only for the Codex `WORKFLOW.md` path overlay.

### Notes
- This sync pins the exact ARS release tag `v3.17.0`.

## [0.1.18] - 2026-07-13

### What's Changed
- Updated the vendored ARS runtime from
  `f86d68a80a6fd05bf51688ff39297ea603eda912` (`v3.15.0`) to
  `73c898c842afae3f163ac571dfa098c72d7c82af` (`v3.16.0`).
- Added upstream model tiering, risk-stratified cross-model verification and
  blind disagreement checkpoints, GPT-5.6 Sol provisional verifier support,
  API retrieval hardening, CARS introduction/title guidance, WP advisory
  evaluation updates, Korean routing triggers, and `THIRD_PARTY.md`.
- Propagated Korean intent boundaries into the Codex router and planner, kept
  model tiering advisory unless per-dispatch Codex model selection exists, and
  retained explicit consent for all external cross-model uploads.
- Preserved the single-root-skill layout, `WORKFLOW.md` entrypoint renaming,
  nested-distribution validator patches, macOS compatibility patches, and the
  materialized Codex Desktop plugin bundle.

### Notes
- This sync pins the exact ARS release tag `v3.16.0`.

## [0.1.17] - 2026-07-04

### What's Changed
- Updated the vendored ARS runtime from
  `8157a15b3bfad94af5c3ac4d7a79d5a9362622f4` (`v3.14.0`) to
  `f86d68a80a6fd05bf51688ff39297ea603eda912` (`v3.15.0`).
- Added upstream ARS v3.15 release content, including release-gate hardening,
  command-invariants and changelog coverage checks, prompt-debt retirement
  round 2, defrift locks, SETUP cross-model parity checks, and the
  `tools/release-discipline` snapshot.
- Preserved Codex packaging behavior: one root router skill, vendored workflow
  entry files named `WORKFLOW.md`, excluded Claude/plugin loader files,
  Codex-specific spec-consistency adaptations, Python 3.9 compatibility patches,
  and the materialized Codex Desktop plugin bundle.

### Notes
- This sync pins the exact ARS release tag `v3.15.0`.

## [0.1.16] - 2026-07-02

### What's Changed
- Updated the vendored ARS runtime from
  `17c518b286e48bbcd19fa7d05ec4f7d2aeb01641` (`v3.13.0-5-g17c518b`,
  ARS main after the platform-port reminder update) to
  `8157a15b3bfad94af5c3ac4d7a79d5a9362622f4` (`v3.14.0`).
- Added upstream ARS v3.14 release content, including eval-harness PR comment
  rendering, prompt-debt retirement updates, the July harness-retirement audit,
  release-aligned README/CITATION/MODE_REGISTRY surfaces, and refreshed setup
  and architecture docs.
- Preserved Codex packaging behavior: one root router skill, vendored workflow
  entry files named `WORKFLOW.md`, excluded Claude/plugin loader files,
  Codex-specific spec-consistency adaptations, and the materialized Codex
  Desktop plugin bundle.

### Notes
- This sync pins the exact ARS release tag `v3.14.0`, not post-release
  `ars/main`.

## [0.1.15] - 2026-06-29

### What's Changed
- Updated the vendored ARS runtime from
  `c22c17eed8a5753aa60681be9734919f2e2f5b42` (`v3.13.0-2-gc22c17e`,
  ARS main after GitHub Copilot documentation updates) to
  `17c518b286e48bbcd19fa7d05ec4f7d2aeb01641` (`v3.13.0-5-g17c518b`,
  current ARS main).
- Added the native-reviewed upstream Korean README and its spec-consistency
  lint coverage while preserving Codex-specific nested-distribution patches.
- Added the upstream platform-port reminder workflow and pull request template
  reminder text in the vendored traceability copy.

### Notes
- This sync pins ARS `main`, not an exact upstream tag. The nearest upstream tag
  remains `v3.13.0`.

## [0.1.14] - 2026-06-21

### Fixed
- Replaced the Codex Desktop plugin's `skills` symlink with a materialized
  bundled `skills/academic-research-suite` directory so Windows plugin caches
  register the bundled skill reliably.
- Added a package quality gate that fails if the Desktop plugin bundle reverts
  to symlink-based skill packaging.

## [0.1.13] - 2026-06-20

### What's Changed
- Updated the vendored ARS runtime from
  `529c6d25a3778843fb94edf9f03eda4cd7e0f416` (`v3.12.0-19-g529c6d2`,
  ARS main after the submission-package verifier slices) to
  `c22c17eed8a5753aa60681be9734919f2e2f5b42` (`v3.13.0-2-gc22c17e`,
  ARS main after the GitHub Copilot documentation updates).
- Added upstream ARS v3.12.1 and v3.13 mainline content, including
  reviewer-response triage modes, diff/patch revision mode adoption,
  format-profile support, provider-agnostic cross-model verification,
  Windows hook portability, Socratic adjacent-framing probe support,
  CITATION metadata, and repository instruction docs.
- Added Codex alias coverage for `ars-3w` and `ars-rebuttal-audit` in both
  the root router and the optional full-runtime planner.
- Preserved Codex packaging behavior: one root router skill, vendored workflow
  entry files named `WORKFLOW.md`, excluded Claude/plugin loader files,
  preserved nested upstream `.github` and root `agents` mirrors as inactive
  traceability/self-test fixtures, Codex setup/architecture overlays at the
  package root, nested-path lint adaptations, macOS Bash 3.2 audit wrapper
  compatibility, and explicit cross-model consent boundaries.

### Notes
- This sync pins ARS `main`, not an exact upstream tag. The nearest upstream tag
  is `v3.13.0`.

## [0.1.12] - 2026-06-11

### What's Changed
- Updated the vendored ARS runtime from
  `2560a072386d4b1a035e5a40ed24ce1edbc0a356` (`v3.11.1`) to
  `529c6d25a3778843fb94edf9f03eda4cd7e0f416` (`v3.12.0-19-g529c6d2`,
  ARS main after the submission-package verifier slices).
- Added upstream ARS v3.12 and post-tag mainline content, including
  sub-claim decomposition, cross-paper contradiction inventory, figure/table
  fidelity, experiment provenance intake, field-norm severity calibration,
  surface-form parity checks, repository hygiene config, and the submission
  package verifier.
- Added Codex alias coverage for `ars-cache-invalidate`.
- Preserved Codex packaging behavior: one root router skill, vendored workflow
  entry files named `WORKFLOW.md`, Codex setup/architecture overlays, excluded
  Claude/plugin loader files, nested-path lint adaptations, macOS Bash 3.2
  audit wrapper compatibility, and explicit cross-model consent boundaries.

### Notes
- This sync pins ARS `main`, not an exact upstream tag. The nearest upstream tag
  is `v3.12.0`.

## [0.1.11] - 2026-06-06

### What's Changed
- Updated the vendored ARS runtime from
  `ca5b713d9d802af85d4c74552604b062a618b1c1` (`v3.11.0` plus the first
  post-tag #310 follow-up fixes) to
  `2560a072386d4b1a035e5a40ed24ce1edbc0a356` (`v3.11.1`).
- In plain terms: this brings the Codex package up to the ARS patch release
  that cleaned up the first wave of post-ship problems after v3.11.0. The main
  changes are correctness and hardening fixes for citation verification,
  domain evidence profiles, eval thresholds, policy markers, provenance joins,
  and edge cases around schema-valid security-boundary inputs.
- Preserved the Codex packaging layer: one root router skill, vendored
  workflow entry files named `WORKFLOW.md`, Codex setup/architecture overlays,
  excluded Claude/plugin loader files, package-specific lint adaptations, and
  the explicit cross-model consent boundary.
- Kept local Codex validation runnable on macOS Python 3.9 by avoiding
  Python-3.11-only standard-library assumptions in the vendored test utilities
  and by using the active Python executable in adapter subprocess tests.

### Notes
- No new Codex package feature was added. This is a vendor sync plus metadata
  release so Codex users get the same v3.11.1 runtime fixes as upstream ARS.

## [0.1.10] - 2026-06-04

### Added
- Added an optional Codex full-runtime adapter profile under
  `skills/academic-research-suite/codex/`, including deterministic route
  planning, Codex agent-team templates, a disabled-by-default hook pack, and
  adapter quality gates. Default ARS Codex behavior remains inline role-prompt
  execution.

### Changed
- Vendored upstream ARS from `4c38571798da4b1ed604ec2c1e01a6f66a7de5a7`
  (`v3.10.0` plus release-manifest alignment) to
  `ca5b713d9d802af85d4c74552604b062a618b1c1` (`v3.11.0` plus post-tag #310
  follow-up fixes).
- Added ARS v3.11 runtime content, including the deterministic citation
  verification gate, arXiv resolver, persistent verification cache, citation
  verification summary contract, standalone verification gate API, and
  `ars-cache-invalidate` command recipe.
- Kept Codex-specific overlays: single root router skill, `WORKFLOW.md`
  vendored workflow entry files, Codex setup/architecture docs, nested-path lint
  patches, excluded showcase PDFs, macOS Bash 3.2 audit wrapper compatibility,
  and explicit cross-model consent boundaries.

### Security
- Added Codex security boundaries for untrusted research inputs, cross-model
  consent, local adapter filesystem handling, and fixed-host bibliographic API
  lookups.

## [0.1.9] - 2026-06-01

### Changed
- Vendored upstream ARS from `96b82e82142dc95f117595c207d3e150b078e411` (`v3.9.4.2`) to `4c38571798da4b1ed604ec2c1e01a6f66a7de5a7` (`v3.10.0` plus release-manifest alignment).
- Added ARS v3.10 runtime content, including the triangulation policy layer, eval harness/gold sets, Schema 11 commitment-ledger refactor, domain-evidence/version-family updates, and scoped-write guard scripts.
- Added newly vendored upstream `README.zh-CN.md`, `README.ja-JP.md`, `evals/`, `conftest.py`, and new `ars-*` command recipes.
- Kept Codex-specific overlays: single root router skill, `WORKFLOW.md` vendored workflow entry files, Codex setup/architecture docs, nested-path lint patches, excluded showcase PDFs, and macOS Bash 3.2 audit wrapper compatibility.
- Clarified beginner install instructions by using `python3` in command
  examples and documenting the `python` fallback when it points to Python 3.
- Added community acknowledgements for beginner-install feedback and issue
  discussion support.

## [0.1.8] - 2026-05-19

### Changed
- Vendored upstream ARS from `74413a42571867abece7b8b76f7a24ac472ab2a0` (`v3.9.0`) to `96b82e82142dc95f117595c207d3e150b078e411` (`v3.9.4.2`).
- Added ARS v3.9.1 client hardening, v3.9.2 phase-boundary routing discipline, v3.9.3 shared client utilities, and v3.9.4/v3.9.4.1 temporal verification runtime content.
- Kept Codex-specific overlays: single root router skill, `WORKFLOW.md` vendored workflow entry files, Codex setup/architecture docs, nested-path lint patches, and macOS Bash 3.2 audit wrapper compatibility.

### Notes
- Upstream v3.9.4.2 changes only `.github` CI/release-gate files, which are intentionally excluded from this Codex package. The manifest still pins the exact v3.9.4.2 commit for provenance.

## [0.1.7] - 2026-05-17

### Changed
- Aligned the Codex package with upstream ARS `v3.9.0`.
