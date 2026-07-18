# ARS-Codex

[![Version](https://img.shields.io/badge/version-v0.1.21-blue)](VERSION)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Sponsor](https://img.shields.io/badge/sponsor-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/crucify020v)

ARS-Codex 是
[Academic Research Skills（ARS）Claude Code 版](https://github.com/Imbad0202/academic-research-skills)
的 Codex 原生 sibling。它是独立的 Codex 发行版，拥有自己的 plugin 标识、
打包、版本和 runtime adapter。

本仓库将 ARS workflow 内容作为单个 Codex skill 进行内嵌分发：

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

原始的 Claude Code ARS checkout 不会被修改。上游内容从最新的 GitHub clone 中复制，并通过 `skills/academic-research-suite/SKILL.md` 中的 Codex router 进行适配。

## 与 Claude Code ARS 的关系

本仓库是 ARS-Codex。如需原始 Claude Code ARS 发行版，请使用
[Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)。

当你需要原生 Claude Code skill 布局、Claude 特有的 agent team 行为或原始 ARS 开发历史时，请使用 Claude Code repo。
当你需要 Codex 原生的单套件 skill 时，请使用本 repo。

## 版本管理

本 ARS-Codex 打包版本为 `0.1.21`。repo 根目录的 `VERSION` 文件、`skills/academic-research-suite/SKILL.md` 中的元数据版本，以及 `skills/academic-research-suite/manifest.json` 中的 `adapter_version` 独立追踪 Codex 打包版本，与内嵌的 ARS 套件版本无关。内嵌的上游版本通过 commit 记录在 `manifest.source_repositories[]` 中。

打包层面的变更汇总在 [`CHANGELOG.md`](CHANGELOG.md) 中。

当前内嵌的 ARS 源码追踪至
`Imbad0202/academic-research-skills@bbc0659272a511b422f6856cd6f44b6ccb2ac213`
（`v3.18.0`）。内嵌内容新增固定席位的 cross-model Reviewer 2 与 re-review
Judge Record、引用缓存陈旧提醒及可选实时重验、高影响主张优先抽样、
scope-conformance 与 search-bounded novelty advisory，以及 held-out pipeline
robustness 测试集；v3.17 的 dispatcher、最小权限与完整性检查契约仍完整保留。

## 安装 ARS-Codex Plugin

通过 Codex CLI 添加 GitHub marketplace 并安装 ARS-Codex：

```bash
codex plugin marketplace add Imbad0202/academic-research-skills-codex --ref main
codex plugin add ars-codex@ars-codex
```

以后更新 plugin：

```bash
codex plugin marketplace upgrade ars-codex
codex plugin add ars-codex@ars-codex
```

在 Codex Desktop 中，也可以从 **Plugins** 添加此 repo，然后安装
**ARS-Codex**：

```text
Marketplace source: https://github.com/Imbad0202/academic-research-skills-codex.git
Branch/ref: main
Plugin: ars-codex
```

Plugin 根目录为 `plugins/ars-codex/`。其中的 `skills/` 是
`academic-research-suite` 的实体副本而不是符号链接，确保 Windows 上的
Codex Desktop plugin 缓存也能正确注册 bundled skill。

安装后请打开新的 Codex 对话，然后调用 `$academic-research-suite`，或直接描述符合
内置 workflow 的学术研究任务。

## 直接安装或更新 Skill

除了 plugin 以外，也可以从此 repo 路径直接安装 skill。使用 `--method git`
以确保公开访问和带凭据的 GitHub 访问均可正常工作：

```bash
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

更新已有安装：

```bash
rm -rf "$HOME/.codex/skills/academic-research-suite"
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

安装后请打开一个新的 Codex 对话。已有的 Codex 会话可能保留旧的 skill 缓存；你不需要关闭无关的 Claude 或 Codex 会话。

使用 `/skills` 验证：你应该看到一个 ARS-Codex 条目，即 `academic-research-suite` 或 `ARS-Codex`。你**不应该**看到来自此包的独立的 `academic-paper`、`academic-pipeline`、`deep-research` 或 `academic-paper-reviewer` skill。如果看到了，请使用上述更新命令重新安装并打开新的 Codex 对话。

## Codex 文档

- [Codex 配置说明](skills/academic-research-suite/ars/docs/SETUP.md) 涵盖安装、`ars-*` 别名、可选工具、Material Passport 适配器，以及不支持的 Claude plugin 功能。
- [Codex 架构说明](skills/academic-research-suite/ars/docs/ARCHITECTURE.md) 解释了 ARS pipeline 的逻辑结构及 Codex 运行时覆盖层。

## 使用方法

使用 `$academic-research-suite`（单数形式）显式调用此套件，然后描述研究任务并提供任何源文件、笔记、草稿文本、审稿人意见或输出约束。

```text
Use $academic-research-suite to help me plan a systematic literature review on
AI adoption in higher education quality assurance.
```

Codex adapter 会将请求路由到以下五个 ARS workflow 之一：

| Workflow | 适用场景 | 示例提示词 |
|---|---|---|
| `deep-research` | 研究问题精炼、文献综述、系统综述、元分析、事实核查 | `Use $academic-research-suite to build a systematic review protocol for AI in higher education QA.` |
| `academic-paper` | 论文大纲、起草、摘要、修订、引用格式化、AI 使用声明 | `Use $academic-research-suite to turn these notes into an IMRaD paper outline and drafting plan.` |
| `academic-paper-reviewer` | 稿件审阅、模拟同行评审、编辑决策、复审 | `Use $academic-research-suite to review this manuscript and produce a journal-style decision letter.` |
| `academic-pipeline` | 端到端的研究到论文 workflow，含完整性检查、审阅、修订和最终检查 | `Use $academic-research-suite to run an end-to-end research-to-paper pipeline from topic to revised manuscript.` |
| `experiment-agent` | 代码实验规划、人类研究协议、统计解读、可重复性验证 | `Use $academic-research-suite to plan a code experiment and define reproducibility checks.` |

### Claude 风格别名

Claude Code v3.7 安装了 `/ars-*` 斜杠命令。Codex 没有相同的 plugin 命令注册机制，因此本包在单个 `$academic-research-suite` skill 内部模拟了这些命令的意图。可使用以下任一形式：

```text
Use $academic-research-suite: ars-plan my paper on AI governance in universities.
```

或者，当你的 Codex 客户端将斜杠前缀文本作为普通用户消息传递时：

```text
/ars-plan my paper on AI governance in universities.
```

如果斜杠输入被客户端拦截，请使用纯别名形式：

```text
ars-plan my paper on AI governance in universities.
```

| Claude 命令 | Codex 别名 | 路由到的 workflow |
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

为获得最佳效果，请在开始时说明 workflow 目标和当前材料的准备状态：

```text
Use $academic-research-suite.

Goal: write a journal article.
Current materials: I have a literature matrix and rough findings, but no outline.
Output needed now: paper architecture and missing-evidence checklist.
Constraints: English, APA 7, higher education policy audience.
```

如果你只有一个论文主题或大致研究方向，尚未形成明确的研究问题，Codex router 应首先启动 ARS Socratic 范围界定：

```text
Use $academic-research-suite.

I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
Please use SCR / Socratic dialogue to help me narrow the question first; do not write an outline yet.
```

预期路由：首先进入 `deep-research` `socratic` 模式。ARS 应提出聚焦问题，在研究问题收敛之前不应生成大纲或草稿。

对于审阅任务，请提供稿件或稿件路径，以及你想要的审阅模式：

```text
Use $academic-research-suite to review this paper.
Mode: full review.
Focus: methodology, contribution, citation integrity, and likely desk-reject risks.
Output: reviewer reports plus editorial decision letter.
```

对于分阶段 pipeline，请要求设置检查点，而不是让 Codex 静默运行整个过程：

```text
Use $academic-research-suite to start an academic-pipeline run.
Begin with Stage 0 intake and stop after producing the pipeline dashboard.
```

### 冒烟测试

在新的 Codex 对话中：

```text
/skills
```

预期结果：仅一个 ARS 条目。

然后测试 Socratic 路由：

```text
Use $academic-research-suite.
I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
```

预期结果：路由到 `deep-research` `socratic` 模式并提问聚焦问题。

CLI 冒烟测试：

```bash
codex exec --ephemeral --sandbox read-only \
  -C /path/to/academic-research-skills-codex \
  'Use $academic-research-suite. Router smoke test only. User request to classify: I want to write a paper on AI adoption in higher education quality assurance, but I do not yet have a clear research question. According to the academic-research-suite router, classify the workflow and mode.'
```

### 非阻塞的 Codex 警告

以下 Codex 消息并不意味着 ARS 安装失败：

- `[features].codex_hooks is deprecated` — 请在方便时更新你的 Codex 配置；ARS-Codex 在正常使用中不需要 hook。
- `hooks need review before they can run` — 如果你需要使用这些 hook，请单独审查。ARS-Codex 将内嵌的 Claude hook 视为可追溯性元数据，不要求其运行。

### Codex Adapter 行为

ARS 最初是为 Claude Code 编写的。在本 Codex 打包版本中：

- 内嵌的 `agents/*.md` 文件用作角色和阶段提示词。
- 内嵌的 `commands/ars-*.md` 文件仅作为提示词模板。Codex 不会将它们注册为斜杠命令。
- 内嵌的 `hooks/hooks.json` 文件仅为上游可追溯性而保留。Codex 不会从此包安装 Claude Code hook。
- Codex 不会自动生成后台 agent，除非你明确要求委派或并行 agent 工作。
- Web/源码验证使用 Codex 浏览功能，在涉及当前或外部事实时必须引用来源。
- 跨模型验证默认禁用。在本 Codex 打包版本中明确请求时，请按 `ars/shared/cross_model_verification.md` 配置 provider，先说明 provider、model 和将发送的内容类别，并在任何外部上传前取得用户明确同意。外部审阅者通过已配置的 provider API 调用，不会用当前 Codex model 模拟。
- 上游对"新 Claude Code 会话"的引用在本包中等同于新的 Codex 对话；Material Passport 重置语义仍然适用。
- 如果引用、来源、统计数据或期刊政策无法验证，Codex 应将其标记为未验证，而非编造支撑依据。

### ARS v3.18 Release 功能对等

本包旨在 Codex 具有等效概念的地方，提供与上游 ARS `v3.18.0` 相同的用户侧 workflow 内容。

| 上游 ARS 功能 | Codex 打包版本行为 |
|---|---|
| 一个可安装的 plugin | 原生 Codex plugin `ars-codex`，内含单个 `academic-research-suite` skill |
| `/ars-*` 斜杠命令 | 通过 skill router 以 `ars-*` 别名模拟；非原生斜杠命令 |
| 从 `skills/` 符号链接自动发现的四个上游 skill | 单个 Codex router skill 选择 workflow 并读取内嵌的 workflow `WORKFLOW.md` 文件 |
| Plugin 附带的 agent | Agent 文件用作角色/阶段提示词；Codex 内联运行，除非用户明确要求委派子 agent |
| `model: opus` / `model: sonnet` 命令路由 | 视为 Claude 元数据；Codex 使用当前活动模型 |
| `ARS_MODEL_TIERING=economy\|quality-boost` | 保留 judgment/execution 分类；仅在 Codex 支持逐次 dispatch 指定模型时应用，否则保持当前模型 |
| 受保护 agent 的 `tools:` allowlist | 保留为最小权限角色边界；被委派的 owner 不获得 Bash 或网络 transport |
| Canonical cross-model handoff envelope | Dispatcher 验证 envelope、取得同意后仅传输 payload，并遵循封闭的结果路由 contract |
| Cross-model Reviewer 2 与 re-review judge | 仅在 provider 已配置且取得内容传输同意时启用；保留固定席位、Judge Record、单一模型族与 fallback 披露 |
| 缓存陈旧 advisory 与实时重验 | 默认使用本地缓存；陈旧行仅为 advisory，`ARS_CACHE_REVALIDATE=1` 才启用实时书目重验 |
| 风险分层主张、范围与新颖性检查 | 保留高影响主张优先抽样，以及不阻断 gate 的 scope 与 search-bounded novelty advisory |
| Panel／degradation／pipeline-boundary 可执行检查 | 连同 hermetic 测试一起内嵌，并由可选 full-runtime manifest 暴露 |
| SessionStart 和 SubagentStop hook（含更新提醒） | 仅为可追溯性而内嵌保留；Codex 不安装或执行 Claude hook |
| Plugin marketplace 更新 | 执行 `codex plugin marketplace upgrade ars-codex` 后重新添加 `ars-codex@ars-codex`；直接安装的 skill 仍通过重新安装或 pull 更新 |
| Claude Code Agent Team | 非自动；Codex 子 agent 需要用户明确请求委派或并行 agent |
| 上游文档中的跨模型 provider 调度 | 默认禁用；仅在明确配置 provider 并取得用户同意时可用 |

### 可选的外部跨模型审阅者 API

用于审阅者校准或跨模型"魔鬼代言人"检查时，请按
`ars/shared/cross_model_verification.md` 配置其中一组 provider，例如：

```bash
export OPENAI_API_KEY="<your-openai-api-key>"
export ARS_CROSS_MODEL="gpt-5.5"
```

然后在提示词中明确请求跨模型验证。如果未配置 provider 或未取得要发送内容类别的明确同意，ARS-Codex 将回退到单运行时审阅，并报告跨模型验证不可用。

## 支持与赞助

如果 ARS-Codex 对你的研究 workflow 有所帮助，欢迎通过 [Buy Me a Coffee](https://buymeacoffee.com/crucify020v) 支持维护工作。

## 安全

请勿为漏洞问题公开提交 issue。请遵循 [`SECURITY.md`](SECURITY.md) 进行私下报告，并参阅[发布就绪与安全报告](security_best_practices_report.md)获取最新的本地验证摘要。

### 高级用途的文件布局

入口文件为：

```text
skills/academic-research-suite/SKILL.md
```

Workflow 内容位于：

```text
skills/academic-research-suite/ars/<workflow>/
```

共享的 schema、合规规则和跨 workflow 契约位于：

```text
skills/academic-research-suite/ars/shared/
```

在调试或更新此包时，请保留这些路径。许多 ARS workflow 文件交叉引用了 `shared/`、`scripts/`、`examples/` 及其他 workflow 目录。

## 更新策略

更新会将选定的上游 ARS 内容同步到 `skills/academic-research-suite/ars/`。
不要盲目镜像 Claude Code repo；应排除 Claude/plugin 加载器文件，如 `.claude/`、`.claude-plugin/`、源码 `.gitignore`，以及 Codex 中不需要的纯符号链接别名目录。可保留嵌套的上游 `.github/` workflow 作为非活跃 traceability 和自测 fixture。

### 非活跃的上游脚本

部分上游维护脚本已内嵌但在此 Codex 打包版本中被刻意设为非活跃状态，因为它们需要非内嵌的 Claude Code 输入（如 `.claude/CLAUDE.md`）。在将任何上游脚本接入 Codex CI 之前，请参阅 `skills/academic-research-suite/manifest.json` 中的 `inactive_upstream_scripts`。

## 贡献者与致谢

**Cheng-I Wu** — ARS 套件及本 Codex 发行版的维护者。

**Codex** — 在维护者的指导下协助完成 Codex adapter 打包、router 策略加固、测试修复和发布就绪审查。

内嵌上游 ARS 的贡献者名单详见
[`skills/academic-research-suite/ars/README.md`](skills/academic-research-suite/ars/README.md#contributors)。
