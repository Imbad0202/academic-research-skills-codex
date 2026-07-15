# Academic Research Skills for Codex

[![Version](https://img.shields.io/badge/version-v0.1.18-blue)](VERSION)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Sponsor](https://img.shields.io/badge/sponsor-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/crucify020v)

Academic Research Skills 套件的 Codex 原生封裝版本。這是
[Academic Research Skills for Claude Code](https://github.com/Imbad0202/academic-research-skills)
的 Codex 發行版本。

本倉庫將 ARS workflow 內容作為單一 Codex skill 提供：

```text
skills/academic-research-suite/
  SKILL.md
  manifest.json
  agents/openai.yaml
  ars/
    deep-research/
    academic-paper/
    academic-paper-reviewer/
    academic-pipeline/
    experiment-agent/
    commands/
    hooks/
    docs/
    tests/
    shared/
```

原始 Claude Code ARS 的 checkout 不會被修改。上游內容從全新的 GitHub clone 複製，
並透過 `skills/academic-research-suite/SKILL.md` 中的 Codex router 進行適配。


## 🚀 快速試用

想在本地安裝前先體驗 Academic Research Suite？可以在 Telegram 或 WhatsApp 中
免費試用：

[在 ClawMama 上試用 Academic Research Suite](https://app.clawmama.run/skills/ymlo6f/hermes?utm_source=github&utm_medium=issue&utm_campaign=skill_outreach_academic_research_skills_codex)

試用滿意後，按下方步驟在 Codex 中安裝即可。


## Claude Code 版本

本倉庫是 Codex 封裝版本。如需 Academic Research Skills 的原始 Claude Code 版本，
請使用 [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)。

當您需要原生 Claude Code skill 佈局、Claude 專屬的 agent-team 行為，
或原始 ARS 開發歷史時，請使用 Claude Code repo。
當您需要 Codex 原生的單一套件 skill 時，請使用本 repo。

## 版本控制

此 Codex 套件版本為 `0.1.18`。倉庫根目錄的 `VERSION` 檔案、
`skills/academic-research-suite/SKILL.md` 的 metadata 版本，
以及 `skills/academic-research-suite/manifest.json` 的 `adapter_version`
獨立追蹤 Codex 套件版本，與內嵌的 ARS 套件版本分開管理。
內嵌的上游版本透過 commit 記錄在 `manifest.source_repositories[]` 中。

套件層級的變更摘要記錄在 [`CHANGELOG.md`](CHANGELOG.md) 中。

目前內嵌的 ARS 原始碼追蹤至
`Imbad0202/academic-research-skills@73c898c842afae3f163ac571dfa098c72d7c82af`
（`v3.16.0`）。內嵌的執行時期內容包含 ARS v3.16 的 model tiering、
風險分層 cross-model 驗證與 blind disagreement checkpoints、GPT-5.6 Sol
暫定 verifier、API 檢索強化、韓文 routing triggers、CARS 引言／標題指引，
以及 WP advisory held-out 評估更新。

## 安裝與更新

從本 repo 路徑安裝 skill。使用 `--method git` 以確保公開和需要認證的
GitHub 存取都能一致運作：

```bash
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

更新現有安裝：

```bash
rm -rf "$HOME/.codex/skills/academic-research-suite"
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

安裝後請開啟新的 Codex 對話。現有的 Codex session 可能保留舊的 skill 快取；
您不需要關閉不相關的 Claude 或 Codex session。

使用 `/skills` 驗證：您應該會看到一個 ARS 項目，即 `academic-research-suite`
或 `Academic Research ...`。您**不應該**看到來自本套件的獨立 `academic-paper`、
`academic-pipeline`、`deep-research` 或 `academic-paper-reviewer` skill。
如果出現，請使用上方的更新指令重新安裝，然後開啟新的 Codex 對話。

## Codex 文件

- [Codex 設定](skills/academic-research-suite/ars/docs/SETUP.md)涵蓋安裝、
  `ars-*` 別名、選用工具、Material Passport 適配器，以及不支援的 Claude plugin 功能。
- [Codex 架構](skills/academic-research-suite/ars/docs/ARCHITECTURE.md)
  說明 ARS 邏輯 pipeline 與 Codex 執行時期疊層。

## 使用方式

使用 `$academic-research-suite`（單數形式）明確呼叫套件，然後描述研究任務，
並提供任何原始檔案、筆記、草稿文本、審稿意見或輸出限制。

```text
Use $academic-research-suite to help me plan a systematic literature review on
AI adoption in higher education quality assurance.
```

Codex adapter 會將請求路由至以下五個 ARS workflow 之一：

| Workflow | 適用情境 | 範例提示 |
|---|---|---|
| `deep-research` | 研究問題精煉、文獻回顧、系統性回顧、後設分析、事實查核 | `Use $academic-research-suite to build a systematic review protocol for AI in higher education QA.` |
| `academic-paper` | 論文大綱、撰寫、摘要、修改、引用格式、AI 使用聲明 | `Use $academic-research-suite to turn these notes into an IMRaD paper outline and drafting plan.` |
| `academic-paper-reviewer` | 稿件審閱、模擬同儕審查、編輯決策、重新審查 | `Use $academic-research-suite to review this manuscript and produce a journal-style decision letter.` |
| `academic-pipeline` | 端到端的研究至論文 workflow，包含誠信閘門、審查、修改與最終檢查 | `Use $academic-research-suite to run an end-to-end research-to-paper pipeline from topic to revised manuscript.` |
| `experiment-agent` | 程式碼實驗規劃、人類研究方案、統計詮釋、可重現性驗證 | `Use $academic-research-suite to plan a code experiment and define reproducibility checks.` |

### Claude 風格別名

Claude Code v3.7 安裝 `/ars-*` 斜線指令。Codex 沒有相同的 plugin 指令註冊機制，
因此本套件在單一 `$academic-research-suite` skill 內模擬指令意圖。可使用以下任一形式：

```text
Use $academic-research-suite: ars-plan my paper on AI governance in universities.
```

或者，當您的 Codex 客戶端將斜線前綴的文字作為一般使用者訊息傳遞時：

```text
/ars-plan my paper on AI governance in universities.
```

如果斜線輸入被客戶端攔截，請使用純文字別名形式：

```text
ars-plan my paper on AI governance in universities.
```

| Claude 指令 | Codex 別名 | 路由的 workflow |
|---|---|---|
| `/ars-plan` | `ars-plan` | `academic-paper` `plan` 模式 |
| `/ars-outline` | `ars-outline` | `academic-paper` `outline-only` 模式 |
| `/ars-abstract` | `ars-abstract` | `academic-paper` `abstract-only` 模式 |
| `/ars-lit-review` | `ars-lit-review` | `academic-paper` `lit-review` 模式 |
| `/ars-citation-check` | `ars-citation-check` | `academic-paper` `citation-check` 模式 |
| `/ars-disclosure` | `ars-disclosure` | `academic-paper` `disclosure` 模式 |
| `/ars-format-convert` | `ars-format-convert` | `academic-paper` `format-convert` 模式 |
| `/ars-revision-coach` | `ars-revision-coach` | `academic-paper` `revision-coach` 模式 |
| `/ars-revision` | `ars-revision` | `academic-paper` `revision` 模式 |
| `/ars-full` | `ars-full` | `academic-pipeline` 完整 workflow |

### 使用模式

為獲得最佳效果，請從 workflow 目標和您目前資料的狀態開始：

```text
Use $academic-research-suite.

Goal: write a journal article.
Current materials: I have a literature matrix and rough findings, but no outline.
Output needed now: paper architecture and missing-evidence checklist.
Constraints: English, APA 7, higher education policy audience.
```

如果您只有論文主題或大方向的研究領域，尚未有明確的研究問題，
Codex router 應從 ARS 蘇格拉底式範圍界定開始：

```text
Use $academic-research-suite.

I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
Please use SCR / Socratic dialogue to help me narrow the question first; do not write an outline yet.
```

預期路由：先進入 `deep-research` `socratic` 模式。ARS 應提出收斂問題，
在研究問題收斂之前不應產生大綱或草稿。

對於審查任務，請提供稿件或稿件路徑，以及您想要的審查模式：

```text
Use $academic-research-suite to review this paper.
Mode: full review.
Focus: methodology, contribution, citation integrity, and likely desk-reject risks.
Output: reviewer reports plus editorial decision letter.
```

對於分階段的 pipeline，請要求設定檢查點，而非讓 Codex 靜默執行整個流程：

```text
Use $academic-research-suite to start an academic-pipeline run.
Begin with Stage 0 intake and stop after producing the pipeline dashboard.
```

### 冒煙測試

在新的 Codex 對話中：

```text
/skills
```

預期結果：僅一個 ARS 項目。

然後測試蘇格拉底式路由：

```text
Use $academic-research-suite.
I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
```

預期結果：路由至 `deep-research` `socratic` 模式並提出收斂問題。

CLI 冒煙測試：

```bash
codex exec --ephemeral --sandbox read-only \
  -C /path/to/academic-research-skills-codex \
  'Use $academic-research-suite. Router smoke test only. User request to classify: I want to write a paper on AI adoption in higher education quality assurance, but I do not yet have a clear research question. According to the academic-research-suite router, classify the workflow and mode.'
```

### 非阻斷性 Codex 警告

以下 Codex 訊息不代表 ARS 安裝失敗：

- `[features].codex_hooks is deprecated` — 方便時更新您的 Codex 設定；
  ARS Codex 在正常使用下不需要 hooks。
- `hooks need review before they can run` — 如果您使用這些 hooks，
  請另外審查。ARS Codex 將內嵌的 Claude hooks 視為可追溯性 metadata，
  不會要求它們。

### Codex Adapter 行為

ARS 最初是為 Claude Code 撰寫的。在此 Codex 套件中：

- 內嵌的 `agents/*.md` 檔案作為角色與階段提示詞使用。
- 內嵌的 `commands/ars-*.md` 檔案僅作為提示詞範本。Codex 不會將它們
  註冊為斜線指令。
- 內嵌的 `hooks/hooks.json` 檔案僅為上游可追溯性而保留。
  Codex 不會從本套件安裝 Claude Code hooks。
- 除非您明確要求委派或平行 agent 工作，否則 Codex 不會自動生成背景 agent。
- 網頁/來源驗證使用 Codex 瀏覽功能，在涉及即時或外部事實時必須引用來源。
- 跨模型驗證預設為停用。在此 Codex 套件中明確要求時，
  請依 `ars/shared/cross_model_verification.md` 設定 provider，先說明
  provider、model 與會送出的內容類別，並在任何外部上傳前取得使用者明確同意。
  外部審查者透過已設定的 provider API 呼叫，不會用目前的 Codex model 模擬。
- 上游提及「fresh Claude Code session」在本套件中意指新的 Codex 對話；
  Material Passport 重設語意仍然適用。
- 如果引用、來源、統計數據或期刊政策無法驗證，Codex 應將其標記為未驗證，
  而非虛構支持內容。

### ARS v3.16 Release 功能對等

本套件旨在與上游 ARS `v3.16.0` 在 Codex 具有對等概念之處，
提供相同的使用者面向 workflow 內容。

| 上游 ARS 功能 | Codex 套件行為 |
|---|---|
| 單一可安裝 plugin | 單一可安裝的 Codex skill，位於 `skills/academic-research-suite` |
| `/ars-*` 斜線指令 | 透過 skill router 作為 `ars-*` 別名模擬；非原生斜線指令 |
| 四個上游 skill 從 `skills/` 符號連結自動發現 | 單一 Codex router skill 選擇 workflow 並讀取內嵌的 workflow `WORKFLOW.md` 檔案 |
| Plugin 隨附的 agent | Agent 檔案作為角色/階段提示詞；Codex 以內嵌方式執行，除非使用者明確要求委派子 agent |
| `model: opus` / `model: sonnet` 指令路由 | 視為 Claude metadata；Codex 使用當前活躍的模型 |
| `ARS_MODEL_TIERING=economy\|quality-boost` | 保留 judgment/execution 分類；僅在 Codex 支援逐次 dispatch 指定模型時套用，否則維持當前模型 |
| SessionStart 和 SubagentStop hooks | 僅為可追溯性而保留；Codex 不安裝或執行 Claude hooks |
| Plugin marketplace 更新/自動更新 | 此處不提供；透過重新安裝或拉取本 Codex repo 來更新 |
| Claude Code Agent Team | 非自動；Codex 子 agent 需要使用者明確要求委派或平行 agent |
| 上游文件中的跨模型 provider 分派 | 預設停用；只有在明確設定 provider 並取得使用者同意時才可使用 |

### 選用的外部跨模型審查者 API

用於審查者校準或跨模型魔鬼代言人檢查時，請依
`ars/shared/cross_model_verification.md` 設定其中一組 provider，例如：

```bash
export OPENAI_API_KEY="<your-openai-api-key>"
export ARS_CROSS_MODEL="gpt-5.5"
```

然後在提示中明確要求跨模型驗證。若未設定 provider 或未取得要送出內容類別的
明確同意，ARS Codex 將回退至單一執行時期審查，並應報告跨模型驗證不可用。

## 支持與贊助

如果 ARS Codex 對您的研究 workflow 有所幫助，您可以透過
[Buy Me a Coffee](https://buymeacoffee.com/crucify020v) 支持後續維護。

## 安全性

請勿為安全漏洞開設公開 issue。請遵循
[`SECURITY.md`](SECURITY.md) 進行私密回報，
並參閱[發布就緒與安全報告](security_best_practices_report.md)了解最新的本地驗證摘要。

### 進階使用的檔案佈局

入口點為：

```text
skills/academic-research-suite/SKILL.md
```

Workflow 內容位於：

```text
skills/academic-research-suite/ars/<workflow>/
```

共享的 schema、合規規則與跨 workflow 契約位於：

```text
skills/academic-research-suite/ars/shared/
```

在除錯或更新套件時，請保留這些路徑。許多 ARS workflow 檔案會交叉引用
`shared/`、`scripts/`、`examples/` 及其他 workflow 目錄。

## 更新政策

更新會將精選的上游 ARS 內容同步至 `skills/academic-research-suite/ars/`。
請勿盲目鏡像 Claude Code repo；應排除 Claude/plugin 載入器檔案，
例如 `.claude/`、`.claude-plugin/`、原始 `.gitignore`，以及 Codex
中不需要的僅符號連結別名目錄。可保留巢狀的上游 `.github/` workflow
作為非活躍 traceability 與自測 fixture。

### 非活躍的上游腳本

部分上游維護腳本已內嵌但在本 Codex 套件中刻意保持非活躍狀態，
因為它們需要非內嵌的 Claude Code 輸入，例如 `.claude/CLAUDE.md`。
在將任何上游腳本接入 Codex CI 之前，請參閱
`skills/academic-research-suite/manifest.json` 中的 `inactive_upstream_scripts`。

## 貢獻者與致謝

**Cheng-I Wu** — ARS 套件及本 Codex 發行版本的維護者。

**Codex** — 在維護者指導下，協助 Codex adapter 封裝、router-policy 強化、
測試修復與發布就緒審查。

內嵌的上游 ARS 貢獻者名單見於
[`skills/academic-research-suite/ars/README.md`](skills/academic-research-suite/ars/README.md#contributors)。
