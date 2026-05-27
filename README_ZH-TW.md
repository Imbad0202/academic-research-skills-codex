# Academic Research Skills for Codex

[![Version](https://img.shields.io/badge/version-v0.1.8-blue)](VERSION)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Sponsor](https://img.shields.io/badge/sponsor-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/crucify020v)

Academic Research Skills 套件的 Codex 原生封裝版本。這是
[Academic Research Skills for Claude Code](https://github.com/Imbad0202/academic-research-skills)
的姊妹 Codex 發行版。

本儲存庫將 ARS 工作流程內容以單一 Codex 技能的形式進行封裝：

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

原始的 Claude Code ARS 檢出內容不會被修改。上游內容從新的 GitHub 複製中取得，
並透過 `skills/academic-research-suite/SKILL.md` 中的 Codex 路由器進行適配。

## Claude Code 版本

本儲存庫是 Codex 封裝版本。如需 Academic Research Skills 的原始 Claude Code 版本，
請使用
[Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)。

當您需要原生 Claude Code 技能佈局、Claude 專屬的代理團隊行為，或原始 ARS 開發歷史時，
請使用 Claude Code 儲存庫。
當您需要 Codex 原生的單一套件技能時，請使用本儲存庫。

## 版本控制

本 Codex 封裝版本為 `0.1.8`。儲存庫根目錄的 `VERSION` 檔案、
`skills/academic-research-suite/SKILL.md` 的中繼資料版本，以及
`skills/academic-research-suite/manifest.json` 的 `adapter_version` 均獨立追蹤
Codex 封裝版本，與封裝的 ARS 套件版本分開。封裝的上游版本透過 commit 記錄在
`manifest.source_repositories[]` 中。

封裝層級的變更摘要記錄於 [`CHANGELOG.md`](CHANGELOG.md)。

目前封裝的 ARS 原始碼追蹤至
`Imbad0202/academic-research-skills@96b82e82142dc95f117595c207d3e150b078e411`
（`v3.9.4.2`）。v3.9.4.2 的上游差異僅限 `.github/` 下的 CI/發佈閘道變更，
本 Codex 封裝刻意排除這些內容；封裝的執行時期內容包含 ARS v3.9.4.1 的時間戳驗證
熱修復以及 v3.9.1 至 v3.9.4 的工作流程更新。

## 安裝與更新

從本儲存庫路徑安裝技能。請使用 `--method git`，以確保公開與需認證的
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

安裝完成後請開啟新的 Codex 對話。現有的 Codex 工作階段可能保留舊的技能快取；
您不需要關閉不相關的 Claude 或 Codex 工作階段。

使用 `/skills` 驗證：您應該看到一個 ARS 項目，即 `academic-research-suite`
或 `Academic Research ...`。您**不應**看到來自此封裝的獨立 `academic-paper`、
`academic-pipeline`、`deep-research` 或 `academic-paper-reviewer` 技能。
如果有，請使用上述更新指令重新安裝並開啟新的 Codex 對話。

## Codex 文件

- [Codex 設定指南](skills/academic-research-suite/ars/docs/SETUP.md)涵蓋
  安裝、`ars-*` 別名、選用工具、Material Passport 適配器，
  以及不支援的 Claude 外掛功能。
- [Codex 架構說明](skills/academic-research-suite/ars/docs/ARCHITECTURE.md)
  解釋 ARS 邏輯管線與 Codex 執行時期覆蓋層。

## 使用方式

使用 `$academic-research-suite`（單數形式）明確呼叫此套件，然後
描述您的研究任務，並提供任何原始檔案、筆記、草稿文本、
審閱者意見或輸出限制。

```text
Use $academic-research-suite to help me plan a systematic literature review on
AI adoption in higher education quality assurance.
```

Codex 適配器會將請求路由至以下五個 ARS 工作流程之一：

| 工作流程 | 適用情境 | 範例提示 |
|---|---|---|
| `deep-research` | 研究問題精煉、文獻回顧、系統性回顧、後設分析、事實查核 | `Use $academic-research-suite to build a systematic review protocol for AI in higher education QA.` |
| `academic-paper` | 論文大綱、撰寫、摘要、修訂、引用格式、AI 使用聲明 | `Use $academic-research-suite to turn these notes into an IMRaD paper outline and drafting plan.` |
| `academic-paper-reviewer` | 稿件審閱、模擬同儕審查、編輯決策、複審 | `Use $academic-research-suite to review this manuscript and produce a journal-style decision letter.` |
| `academic-pipeline` | 端到端的研究到論文工作流程，包含誠信閘道、審查、修訂及最終檢查 | `Use $academic-research-suite to run an end-to-end research-to-paper pipeline from topic to revised manuscript.` |
| `experiment-agent` | 程式碼實驗規劃、人類研究方案、統計解讀、可重現性驗證 | `Use $academic-research-suite to plan a code experiment and define reproducibility checks.` |

### Claude 風格別名

Claude Code v3.7 會安裝 `/ars-*` 斜線指令。Codex 沒有相同的外掛指令註冊機制，
因此本封裝在單一 `$academic-research-suite` 技能內模擬指令意圖。請使用以下任一形式：

```text
Use $academic-research-suite: ars-plan my paper on AI governance in universities.
```

或者，當您的 Codex 用戶端將斜線前綴的文字作為一般使用者訊息傳遞時：

```text
/ars-plan my paper on AI governance in universities.
```

如果斜線輸入被用戶端攔截，請使用純別名形式：

```text
ars-plan my paper on AI governance in universities.
```

| Claude 指令 | Codex 別名 | 路由工作流程 |
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
| `/ars-full` | `ars-full` | `academic-pipeline` 完整工作流程 |

### 使用模式

為獲得最佳效果，請從工作流程目標和您目前素材的狀態開始：

```text
Use $academic-research-suite.

Goal: write a journal article.
Current materials: I have a literature matrix and rough findings, but no outline.
Output needed now: paper architecture and missing-evidence checklist.
Constraints: English, APA 7, higher education policy audience.
```

如果您只有論文主題或大致研究方向，尚未有明確的研究問題，
Codex 路由器應從 ARS 蘇格拉底式範圍界定開始：

```text
Use $academic-research-suite.

I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
Please use SCR / Socratic dialogue to help me narrow the question first; do not write an outline yet.
```

預期路由：首先進入 `deep-research` `socratic` 模式。ARS 應提出收斂問題，
在研究問題收斂之前不應產生大綱或草稿。

對於審閱任務，請提供稿件或稿件路徑，以及您想要的審閱模式：

```text
Use $academic-research-suite to review this paper.
Mode: full review.
Focus: methodology, contribution, citation integrity, and likely desk-reject risks.
Output: reviewer reports plus editorial decision letter.
```

對於分階段管線，請要求設定檢查點，而非要求 Codex 靜默執行整個流程：

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

接著測試蘇格拉底式路由：

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

- `[features].codex_hooks is deprecated` — 方便時更新您的 Codex 設定即可；
  ARS Codex 在一般使用中不需要 hooks。
- `hooks need review before they can run` — 如果您有使用這些 hooks，請另外審查。
  ARS Codex 將封裝的 Claude hooks 視為可追溯性中繼資料，不會要求它們。

### Codex 適配器行為

ARS 原本為 Claude Code 撰寫。在本 Codex 封裝中：

- 封裝的 `agents/*.md` 檔案作為角色與階段提示詞使用。
- 封裝的 `commands/ars-*.md` 檔案僅作為提示詞範本。Codex 不會將它們
  註冊為斜線指令。
- 封裝的 `hooks/hooks.json` 檔案僅為上游可追溯性而保留。Codex 不會從
  本封裝安裝 Claude Code hooks。
- 除非您明確要求委派或平行代理工作，Codex 不會自動產生背景代理。
- 網頁/來源驗證使用 Codex 瀏覽功能，當涉及時事或外部事實時必須引用來源。
- 跨模型驗證預設為停用。在本 Codex 封裝中明確要求時，需設定
  `ARS_CROSS_MODEL=claude-opus-4.7` 及 `ANTHROPIC_API_KEY`；
  外部審閱者使用 Anthropic Claude Opus 4.7 API，而非 Codex/OpenAI API。
  上游的 GPT/Gemini 二次分派指令在此明確的 Anthropic 設定存在時才會被忽略。
- 上游提及的「新的 Claude Code 工作階段」在本封裝中意指新的 Codex 對話；
  Material Passport 重設語意仍然適用。
- 若引用、來源、統計數據或期刊政策無法驗證，Codex 應將其標記為未驗證，
  而非憑空編造佐證。

### ARS v3.9.4.2 功能對等

本封裝在 Codex 具有對等概念之處，力求與上游 ARS v3.9.4.2 達到相同的使用者面向
工作流程內容。

| 上游 ARS 功能 | Codex 封裝行為 |
|---|---|
| 單一可安裝外掛 | 單一可安裝的 Codex 技能，位於 `skills/academic-research-suite` |
| `/ars-*` 斜線指令 | 透過技能路由器模擬為 `ars-*` 別名；非原生斜線指令 |
| 從 `skills/` 符號連結自動發現的四個上游技能 | 單一 Codex 路由器技能選擇工作流程並讀取封裝的工作流程 `WORKFLOW.md` 檔案 |
| 外掛隨附的代理 | 代理檔案作為角色/階段提示詞；Codex 以內嵌方式執行，除非使用者明確要求委派子代理 |
| `model: opus` / `model: sonnet` 指令路由 | 視為 Claude 中繼資料；Codex 使用當前活動模型 |
| SessionStart 及 SubagentStop hooks | 僅為可追溯性而封裝；Codex 不會安裝或執行 Claude hooks |
| 外掛市集更新/自動更新 | 在此不可用；請透過重新安裝或拉取本 Codex 儲存庫來更新 |
| Claude Code 代理團隊 | 非自動；Codex 子代理需要使用者明確請求委派或平行代理 |
| 來自上游文件的跨模型 GPT/Gemini 分派 | 已停用；Codex 封裝僅在明確設定時支援選用的 Anthropic Claude Opus 4.7 審閱 |

### 選用的 Claude Opus 4.7 審閱者 API

用於審閱者校準或跨模型魔鬼代言人檢查：

```bash
export ANTHROPIC_API_KEY="<your-anthropic-api-key>"
export ARS_CROSS_MODEL="claude-opus-4.7"
```

然後在提示中明確要求跨模型驗證。若未同時設定兩個環境變數，
ARS Codex 將回退至單一執行時期審閱，並應報告 Claude Opus 4.7 驗證者不可用。

## 支持與贊助

如果 ARS Codex 對您的研究工作流程有所幫助，您可以透過
[Buy Me a Coffee](https://buymeacoffee.com/crucify020v) 支持後續維護。

## 安全性

請勿為漏洞開立公開 issue。請遵循
[`SECURITY.md`](SECURITY.md) 進行私密回報，並參閱
[發佈就緒性與安全性報告](security_best_practices_report.md) 以取得最新的本地驗證摘要。

### 進階使用的檔案佈局

入口點為：

```text
skills/academic-research-suite/SKILL.md
```

工作流程內容位於：

```text
skills/academic-research-suite/ars/<workflow>/
```

共享結構描述、合規規則及跨工作流程約定位於：

```text
skills/academic-research-suite/ars/shared/
```

除錯或更新封裝時，請保留這些路徑。許多 ARS 工作流程檔案會交叉引用
`shared/`、`scripts/`、`examples/` 及其他工作流程目錄。

## 更新政策

更新會將選定的上游 ARS 內容同步至 `skills/academic-research-suite/ars/`。
請勿盲目鏡像 Claude Code 儲存庫；排除 Claude/外掛載入器檔案，
如 `.claude/`、`.claude-plugin/`、`.github/`、原始 `.gitignore`，
以及 Codex 中不需要的僅符號連結別名目錄。

### 非活躍的上游腳本

部分上游維護腳本已封裝但在本 Codex 封裝中刻意保持非活躍狀態，
因為它們需要非封裝的 Claude Code 輸入（例如 `.claude/CLAUDE.md`）。
在將任何上游腳本接入 Codex CI 之前，請參閱
`skills/academic-research-suite/manifest.json` 中的 `inactive_upstream_scripts`。

## 貢獻者與致謝

**Cheng-I Wu** — ARS 套件及本 Codex 姊妹發行版的維護者。

**Codex** — 在維護者指導下協助 Codex 適配器封裝、路由策略強化、
測試修復及發佈就緒性審閱。

封裝的上游 ARS 貢獻者列於
[`skills/academic-research-suite/ars/README.md`](skills/academic-research-suite/ars/README.md#contributors)。
