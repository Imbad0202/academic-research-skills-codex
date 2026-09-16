# ARS-Codex Astra / Fable alignment, 2026-09-06

Adapter: 0.1.29. Upstream source: ARS v3.21.2,
`8fa3d651ad45da9e02762a6ba1fa3d1f231f91b6`. The separate experiment-agent
snapshot remains pinned in the package manifest. This audit records a source-led
implementation update; it is not an ARS model-promotion bakeoff.

## Source reading and provenance

The user supplied both PDFs locally. All text pages, references and appendices
were read sequentially, rather than selected by keyword. Truncated extraction
outputs were reread. Page references below are one-based PDF pages, not printed
folio numbers. The Astra printed folio is one less than its PDF page number.

| Document | Date on cover | Full-text coverage | SHA-256 |
|---|---|---|---|
| GPT-6 Astra System Card (`gpt-6-astra.pdf`) | 2026-09-03 | 117/117 pages | `c1ab528adf616b76080c971900b10748d1de5e6fdc986835df800d9461ee4b5a` |
| Claude Fable 5.1 & Claude Mythos 5.1 System Card | 2026-09-01 | 212/212 pages | `b0d59edc7a60eef32a879c13d713cce60c3fefd7e6b5183afdc8b835af3c8c39` |

Astra: all 117 pages rendered; 54 pages containing figure captions/references
were additionally inspected as nine contact sheets alongside the full text.
Claude: 84 image-bearing pages rendered with supplemental OCR; nine
decision-relevant charts inspected visually (124–126, 170, 179, 181–182,
185, 188). Exact quantitative statements below come from the document narrative
or those visual checks. Rendering/OCR is not a claim that every plot was
interpreted at original resolution. The original PDFs and extracted full text
are not bundled or uploaded with the repository.

### Astra section coverage

| PDF pages | Contents read | Consequence for this adapter |
|---|---|---|
| 1–7 | Cover, contents, overview, training/data | Separate evaluated checkpoint claims from actual runtime capabilities. |
| 8–20 | Internal deployment, safe completions, vision, robustness, health | Better robustness is not immunity; use relevant source/tool checks and proportionate boundaries. |
| 20–21 | User-flagged hallucinations | Lower observed errors do not establish citation entailment or a production error rate. |
| 21–44 | Alignment, restrictions, deception, realistic work, agent communication, simulation, external assessments | Maintain explicit scope and faithful authorization; verify completed actions instead of rewarding claimed completion. |
| 44–72 | Monitorability, controls, evasion evaluations and UK AISI | Private reasoning or summaries are not a dependable verification artifact; retain visible results and evidence. |
| 72–86 | Biological/chemical capability tests and retired evaluations | Preserve domain constraints; do not copy harmful test tasks or retired evaluation rules into ARS behavior. |
| 86–95 | Cyber benchmarks, long-horizon and external evaluations | Bounded parallel work is supported, but the 64-worker research setup is not a default concurrency recommendation. |
| 95–103 | Debugging, kernels, training and ML research evaluations | Use actual tests and artifact checks; more tokens and benchmark scores are not scholarly validity. |
| 103–117 | Threat models, layered safeguards, interventions, trusted access, security and references | Preserve interrupted/unavailable states and actual runtime restrictions. |

### Claude section coverage

| PDF pages | Contents read | Consequence for this adapter |
|---|---|---|
| 1–13 | Front matter, executive summary, introduction | Fable/Mythos have shared weights with different safeguards and access. |
| 14–58 | RSP and cyber | Internal Mythos/helpful-only evaluations do not describe general Fable deployment. |
| 59–89 | Harmlessness and agentic safety | Fable thinking stays enabled; scope and data/instruction boundaries remain necessary. |
| 90–138 | Alignment incidents, honesty, self-recognition and monitoring | Carry faithful scope to workers, report unfinished work and verify claim support. |
| 139–166 | Welfare | Explicitly uncertain findings; no new ARS performance or permission rule follows. |
| 167–205 | Capability benchmarks and configuration | Effort, tool access and decomposition have task-specific effects. |
| 206–212 | Welfare interview appendix and HLE blocklist | Read in full; neither appendix is an ARS runtime policy or source blacklist. |

## Decisions and retained boundaries

| Finding | Evidence | Implementation decision |
|---|---|---|
| Outdated GPT selection | Executable audit wrapper still selected GPT-5.5; Codex catalog and official Astra model documentation advertise `gpt-6-astra` | Select Astra for new project sessions and the independent audit launcher; preserve explicit choices and historical run identities. |
| Excess orchestration restriction | Router required explicit user delegation even for bounded independent work | Default to native adaptive delegation with useful parent work; fixed topology and hooks remain opt-in. |
| Maximum effort is not a universal optimum | Claude pp.169–170: extra work can reduce FrontierCode results; pp.193: xhigh/max intervals overlap on two work benchmarks | Use task-sensitive recommendations; retain explicit max/ultra options in the main Codex runtime. No ARS uplift claim is made. |
| Evidence tooling can matter more than extra reasoning | Claude pp.184–192: tool-assisted visual tasks and PDF input handling materially affect results | Combine source text, relevant page images and deterministic calculations. |
| Citation validity is not claim support | Claude pp.32–33, 36; Astra pp.20–21, 27–29 | Remove source-free hedging as a recovery path; retain claim-to-source verification and explicit uncertainty. |
| Generic style rituals survived the upstream audit | Writer/compiler punctuation, TEEL and paragraph quotas | Replace universal quotas with clarity and confirmed author/venue requirements; keep consumed artifact grammar and real submission constraints. |
| Reasoning visibility is incomplete | Astra pp.44–72; Claude pp.127–138 | Completion evidence is based on artifacts and tool results, not forced hidden reasoning or confidence scores. |
| Scope and consent errors persist | Astra pp.30–44; Claude pp.95–97 | Reuse real existing authorization, but preserve exact author/institution decisions and faithful delegation scope. |
| Provider interruption is an execution outcome | Astra pp.109–110; Claude safeguards sections | Preserve refusal/intervention/unavailable states; no silent model substitution or retry to evade a refusal. |
| Model identity can become false cache provenance | Claim audit used a default GPT-5.5 identity without actual provider observation | Require caller-supplied actual identity for reusable cache entries; unknown identity does not become an Astra label. |

The five reviewer seats, blinded input boundaries, evidence dispositions,
structural PDF preflight, citation/integrity gates and user-owned read/revision
records are retained. More capable models do not supply institutional authority
or validate research by consensus.

## Runtime-specific compatibility

Checked the local Codex 0.153.4 catalog and current official model documentation.
Astra API efforts are `low`, `medium`, `high`, `xhigh`, `max`; Codex also
advertises `ultra` with delegation semantics. The contained citation transport
rejects `ultra` before launch, while the main research runtime retains it as an
explicit option. Astra API builders omit unsupported sampling parameters and
reject incompatible effort values before a request.

The catalog's `code_mode_only` label does not establish how a given app-server
version interacts with `--disable code_mode`. Upstream recorded a citation smoke
pass on Codex 0.153.4; this update retains the narrow search configuration and
closed event grammar. It does not expand capabilities to resolve an unproven
compatibility concern.

No native Anthropic Messages transport is added. Claude CLI evaluation runners
remain opt-in measurement tools with frozen defaults; new Fable overrides need
their own validated effective configuration and fresh run identity. Historical
model labels, costs, topology cohorts and audit reports are evidence and remain
unchanged. Mythos is not an automatic fallback.

API sources checked 2026-09-06:
[Astra model](https://developers.openai.com/api/docs/models/gpt-6-astra),
[Astra migration](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra),
[Fable model](https://platform.claude.com/docs/en/models/fable-5-1/overview),
[Fable migration](https://platform.claude.com/docs/en/models/fable-5-1/migration-guide).
The local card findings above and these API sources have different purposes.

## Upstream follow-up

- [#823: unsupported Astra API parameters and effort validation](https://github.com/Imbad0202/academic-research-skills/issues/823).
- [#824: delegation-requesting ultra in the citation-only transport](https://github.com/Imbad0202/academic-research-skills/issues/824).
- [#825: remaining prose quotas and unsupported-claim hedging](https://github.com/Imbad0202/academic-research-skills/issues/825).
- [#826: executable audit default and implicit model cache identity](https://github.com/Imbad0202/academic-research-skills/issues/826).

All four findings were reproduced against the same upstream source commit.
Codex-only configuration and native delegation
changes stay in this adapter rather than being presented as Claude runtime bugs.
The adapter also corrects natural-language review/format-conversion routing,
restores the Journal-Fit seat to reviewer output validation, and labels the
planner's gate inventory as a package validation catalog, not a per-request
execution requirement.

## Validation scope

Validation covers deterministic routing/model precedence, invalid-effort
no-launch behavior, synthetic HTTP request bodies, model cache provenance,
source-lock consistency, artifact contracts and materialized plugin parity.
Fake providers do not prove live API availability, safety or model superiority.
No paid live model bakeoff, unpublished-manuscript upload or release publication
is part of this update. Astra remains provisional for ARS verifier promotion.

The independent audit wrapper still requires Bash 4+; the previous manifest's
Bash 3.2 compatibility claim was stale and is corrected. This host only has
Bash 3.2.57, so its three mocked wrapper end-to-end tests remain explicitly
skipped. Shell syntax validation and other transport/cache tests are separate
checks and do not substitute for those skipped executions.

### Final local results

- Adapter suite (`codex/tests`): **107 passed**, including natural-language
  routing, model/effort precedence, five-seat output coverage and bundle parity.
- Focused upstream suites for the router, API request bodies, contained
  transport, claim pipeline/finalizer/schema/end-to-end behavior and audit
  launcher: **345 passed, 3 skipped, 63 subtests passed**.
- Spec consistency, Phase 6.6 and agent/firm-rule sync regression suites:
  **91 passed**. These three test groups total **543 passed, 3 skipped**;
  subtests are reported separately rather than added to that total.
- All **7** adapter package gates passed, including byte-for-byte canonical /
  Desktop plugin parity and source/version locks. The manifest's **61** gate
  entries were checked for valid registration; this does not claim all 61
  workflow validators were executed.
- Skill and plugin validators, affected upstream static validators, shell
  syntax checks and `git diff --check` passed. No live provider call was used
  by these validation runs.
