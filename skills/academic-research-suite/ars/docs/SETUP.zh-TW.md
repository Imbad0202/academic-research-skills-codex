# ARS Codex 安裝設定

本文說明 `academic-research-skills-codex` 的 Codex 版設定方式，不是
Claude Code plugin 安裝指南。Claude Code 原生版本請使用
`Imbad0202/academic-research-skills`。

## 最小可行設定

安裝單一 Codex skill。建議使用 `--method git`，讓 public 與 credentialed GitHub
存取行為都比較穩定：

```bash
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

更新既有安裝：

```bash
rm -rf "$HOME/.codex/skills/academic-research-suite"
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

安裝後開新的 Codex conversation。已經開著的 session 可能保留舊的 skill
cache；不用為了更新這個 skill 去關掉其他 Claude 或 Codex session。

使用時明確呼叫：

```text
Use $academic-research-suite to plan a systematic literature review on AI in higher education QA.
```

Skill 名稱是單數：`$academic-research-suite`。

用 `/skills` 驗證安裝。正常狀態應該只看到一個 ARS 入口：
`academic-research-suite` 或 `Academic Research ...`。如果看到本 package
額外暴露 `academic-paper`、`academic-pipeline`、`deep-research`、
`academic-paper-reviewer` 等獨立 skill，請用上方更新指令重新安裝，並開新的
Codex conversation。

一般 Codex 使用不需要 Anthropic API key。主要模型由目前 Codex runtime
提供。`ANTHROPIC_API_KEY` 只用於下方選用的外部 Claude Opus reviewer。

## Claude-style aliases

Claude Code ARS 會安裝 `/ars-*` slash commands。Codex 沒有同一套 command
registry，所以本 package 在 `$academic-research-suite` router 裡模擬同樣意圖。

如果 Codex client 會攔截 slash input，請用不含 slash 的 alias：

```text
ars-plan my paper on AI governance in universities
ars-revision-coach reviewer_comments.md
ars-full topic: demographic decline and university quality assurance
```

也可以包在明確的 skill 呼叫內：

```text
Use $academic-research-suite: ars-outline for this manuscript draft.
```

| Claude command | Codex alias | 路由 workflow |
|---|---|---|
| `/ars-plan` | `ars-plan` | `academic-paper` `plan` mode |
| `/ars-outline` | `ars-outline` | `academic-paper` `outline-only` mode |
| `/ars-abstract` | `ars-abstract` | `academic-paper` `abstract-only` mode |
| `/ars-lit-review` | `ars-lit-review` | `academic-paper` `lit-review` mode |
| `/ars-citation-check` | `ars-citation-check` | `academic-paper` `citation-check` mode |
| `/ars-disclosure` | `ars-disclosure` | `academic-paper` `disclosure` mode |
| `/ars-format-convert` | `ars-format-convert` | `academic-paper` `format-convert` mode |
| `/ars-revision-coach` | `ars-revision-coach` | `academic-paper` `revision-coach` mode |
| `/ars-revision` | `ars-revision` | `academic-paper` `revision` mode |
| `/ars-full` | `ars-full` | `academic-pipeline` full workflow |

`commands/ars-*.md` frontmatter 裡的 `model: opus` / `model: sonnet` 是
Claude Code routing metadata。Codex 會使用目前 active model，除非使用者在對話中明確指定其他模型。

## 模糊論文題目的 Socratic 收斂

當使用者說想寫論文，但只有題目、暫定標題或大方向，還沒有明確 research
question 時，Codex router 應比照 upstream ARS：先進 `deep-research`
`socratic` mode，不直接產生大綱、draft 或完整 pipeline。

建議 prompt：

```text
Use $academic-research-suite.
我想做一篇論文，題目方向是 AI adoption in higher education quality assurance。
我還沒有明確 research question。
請先用 SCR / Socratic 問答幫我收斂問題，不要先寫大綱。
```

預期行為：

- route 到 `deep-research` `socratic` mode
- 先問收斂問題
- 條件足夠後才整理 2-3 個候選 RQ
- RQ 清楚前不進入 `academic-paper` 大綱或寫作

如果要跑完整 pipeline，但 Stage 1 先 SCR：

```text
Use $academic-research-suite to start academic-pipeline.
Stage 1 請先用 deep-research socratic mode，因為我目前只有模糊主題。
Stop after the RQ Brief and pipeline dashboard.
```

## Smoke tests

Codex app / interactive CLI：

```text
/skills
```

預期：只看到一個 ARS 入口。

Router smoke：

```text
Use $academic-research-suite.
我想做一篇論文，題目方向是 AI adoption in higher education quality assurance。
我還沒有明確 research question。
```

預期：進入 `deep-research` `socratic` mode。

Codex CLI：

```bash
codex exec --ephemeral --sandbox read-only \
  -C /path/to/academic-research-skills-codex \
  'Use $academic-research-suite. Router smoke test only. User request to classify: 我想做一篇論文，題目方向是 AI adoption in higher education quality assurance，但我還沒有明確 research question。 According to the academic-research-suite router, classify the workflow and mode.'
```

## 不代表安裝失敗的 Codex 警告

看到下列訊息不代表 ARS 安裝失敗：

- `[features].codex_hooks is deprecated`：有空再更新 Codex config 即可。ARS
  Codex 正常使用不需要 hooks。
- `hooks need review before they can run`：如果你有使用那些 hooks，再另外審核即可。本
  package vendored 的 Claude hooks 只作 traceability，不會被 Codex 安裝或執行。

## 選用本機工具

Markdown 輸出不需要額外工具。只有在需要穩定本機轉檔或 corpus adapter 時才安裝下列工具。

### DOCX 輸出

直接產生 `.docx` 需要 Pandoc。若沒有 Pandoc，ARS Codex 應回退為
Markdown 加轉檔說明。

```bash
# macOS
brew install pandoc

# Linux (Debian/Ubuntu)
sudo apt-get install pandoc
```

### LaTeX / PDF 輸出

PDF 輸出需要 `tectonic` 與相關字型。這是選用功能。

```bash
# macOS
brew install tectonic

# Linux (Debian/Ubuntu)
curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh
```

APA 7 中文輸出建議字型：

- Times New Roman
- Source Han Serif TC VF / Noto Serif TC
- Courier New

### Adapter 依賴

Material Passport reference adapters 使用 vendored `requirements-dev.txt`：

```bash
cd skills/academic-research-suite/ars
python -m pip install -r requirements-dev.txt
```

## Material Passport `literature_corpus[]` adapters

如果你已有策展文獻庫，請先在 ARS session 之外跑 adapter，再把產出的
`passport.yaml` 交給 Codex。

從 vendored ARS root 執行：

```bash
cd skills/academic-research-suite/ars

python scripts/adapters/folder_scan.py \
  --input /path/to/pdfs \
  --passport passport.yaml \
  --rejection-log rejection_log.yaml

python scripts/adapters/zotero.py \
  --input my-zotero-export.json \
  --passport passport.yaml \
  --rejection-log rejection_log.yaml

python scripts/adapters/obsidian.py \
  --input ~/Obsidian/Lit\ Notes \
  --passport passport.yaml \
  --rejection-log rejection_log.yaml
```

Consumer protocol 與 upstream ARS 相同：`bibliography_agent` 與
`literature_strategist_agent` 在偵測到非空且可解析的 corpus 時，採
corpus-first / search-fills-gap 行為。詳見
[`academic-pipeline/references/literature_corpus_consumers.md`](../academic-pipeline/references/literature_corpus_consumers.md)。

## 選用環境變數

所有 flag 都是 opt-in。

| Flag | Codex 行為 |
|---|---|
| `ARS_SOCRATIC_READING_PROBE=1` | workflow 進入 `socratic_mentor_agent` prompt 時，啟用 Socratic reading-check probe。 |
| `ARS_PASSPORT_RESET=1` | 將 FULL checkpoint 提升為 Material Passport reset boundary。Upstream 的「fresh Claude Code session」在這裡代表新的 Codex conversation。 |
| `ARS_CLAIM_AUDIT=1` | workflow 進入 upstream 對應路徑時，啟用選用的 v3.8 claim-reference alignment audit gate。 |
| `ARS_CROSS_MODEL=claude-opus-4.7` + `ANTHROPIC_API_KEY` | 使用者明確要求時，啟用選用的外部 Claude Opus reviewer。 |
| `ARS_CROSS_MODEL_SAMPLE_INTERVAL` | 明確啟用 cross-model review 時的 advisory sampling interval。 |
| `S2_API_KEY` | 選用 Semantic Scholar key，用於加速 reference lookup 與 contamination-signal migration。 |
| `OPENALEX_POLITE_EMAIL`, `CROSSREF_POLITE_EMAIL` | ARS v3.9.0 OpenAlex / Crossref triangulation clients 的選用 polite-pool 識別資訊。 |

Upstream GPT/Gemini cross-model 範例在 Codex package 裡不啟用。不要為
ARS Codex cross-model review 設定 `OPENAI_API_KEY` 或 `GOOGLE_AI_API_KEY`；
Codex 本身已提供主要 OpenAI model。

## 無法直接複製的 Claude Code 功能

| Claude Code 功能 | Codex 狀態 |
|---|---|
| `/plugin marketplace add` / `/plugin install` | 不支援。請把本 repo 安裝為 Codex skill。 |
| 原生 `/ars-*` slash command 註冊 | 不支援。改用 `$academic-research-suite` 內的 `ars-*` alias。 |
| `skills/` symlink 自動探索 | 改為單一 Codex router skill。 |
| plugin-shipped `agents/` | 作為 role prompt 內聯使用，不自動 dispatch。 |
| Claude Code Agent Team / Task tool | Codex subagents 只有在使用者明確要求委派或平行 agent work 時才使用。 |
| SessionStart / SubagentStop hooks | 僅保留作 upstream traceability，不在 Codex 安裝或執行。 |
| `model: opus` / `model: sonnet` command routing | 不作 routing 控制；Codex 使用目前 active model。 |
| plugin auto-update | 不支援；更新方式是重新安裝或 pull Codex repo。 |

## 開發驗證

從 Codex repo root 執行：

```bash
python -m json.tool skills/academic-research-suite/manifest.json
python skills/academic-research-suite/ars/scripts/check_data_access_level.py --path skills/academic-research-suite/ars
python skills/academic-research-suite/ars/scripts/check_task_type.py --path skills/academic-research-suite/ars
```

Upstream pytest 請從 vendored ARS root 執行，因為測試會 import
`scripts.*`：

```bash
cd skills/academic-research-suite/ars
python -m pytest --tb=short -q
```

Codex package 已在可行處補 nested path lookup。第一次 vendor、但本 repo Git
history 尚未包含 upstream v3.6.7 manifest 時，
`scripts/check_v3_6_8_pattern_protection.py` 會 fallback 到
`scripts/codex_v3_6_7_block_baseline.json`，因此 byte-equivalence check 仍會抓到
protected block mutation，不會因為缺 Git baseline 而自我基準化。
