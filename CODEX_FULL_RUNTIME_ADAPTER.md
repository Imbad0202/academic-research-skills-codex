# Codex Full-Runtime Adapter Guide

本文说明 `academic-research-suite` 的 Codex full-runtime adapter 做了什么、如何配置、如何使用，以及与 Claude Code 原版的差异。

## 做了什么

本仓库以 `academic-research-skills-codex` 为 Codex 主开发版本，并把 Claude Code 上游 `Imbad0202/academic-research-skills` 作为 canonical upstream。

本次实现包含三层：

1. 上游同步
   - `skills/academic-research-suite/ars/` 已同步到 upstream `academic-research-skills@cb2f4e07019e1cd72881547e91d880ec7cc0d7fc`。
   - upstream workflow entry 在 Codex 包里保持为 `WORKFLOW.md`，避免 Codex 把 vendored workflows 重复暴露成多个 skill。
   - 只保留少量必要 Codex path patch，用于让 upstream validators 在嵌套 vendored 路径里运行。

2. Codex adapter layer
   - 新增 `skills/academic-research-suite/codex/`。
   - `full-runtime-manifest.json` 定义 Codex runtime profile、命令别名、workflow route、agent-team plan、quality gates。
   - `scripts/ars_codex_full_runtime.py` 是 deterministic planner，用于测试和解释 `ars-*` 入口会如何路由。
   - `agents/*.md` 是 Codex agent-team templates，覆盖 deep-research、academic-paper、academic-pipeline、paper-reviewer、experiment workflows。
   - `hooks/` 提供 disabled-by-default 的 Codex hook pack。
   - `tests/` 提供 adapter smoke/parity tests。

3. Root skill router 更新
   - `skills/academic-research-suite/SKILL.md` 继续是唯一 Codex 入口。
   - 支持 13 个 `ars-*` alias：`ars-plan`、`ars-outline`、`ars-abstract`、`ars-lit-review`、`ars-citation-check`、`ars-disclosure`、`ars-format-convert`、`ars-revision-coach`、`ars-revision`、`ars-full`、`ars-reviewer`、`ars-mark-read`、`ars-unmark-read`。
   - 默认保持 inline mode；full-runtime 和 agent-team 必须显式 opt in。

## 配置

默认无需配置，直接使用 `$academic-research-suite` 即可。默认行为是 inline router，不会自动启动大量子代理或 hooks。

启用 full-runtime planning：

```bash
export ARS_CODEX_FULL_RUNTIME=1
```

启用 Codex agent-team profile：

```bash
export ARS_CODEX_AGENT_TEAM=1
```

启用 hook pack：

```bash
export ARS_CODEX_HOOKS=1
```

推荐组合：

```bash
export ARS_CODEX_FULL_RUNTIME=1
export ARS_CODEX_AGENT_TEAM=1
```

hooks 仍然需要用户显式安装或在 Codex hook 配置里引用 `skills/academic-research-suite/codex/hooks/hooks.json`。当前 hook wrapper 是只读的，只输出静态 adapter 状态，不读取 secret、不访问网络、不修改文件。

## 本地安装

从本仓库安装到当前用户 Codex skills 目录：

```bash
mkdir -p "$HOME/.codex/skills"
rsync -a --delete "skills/academic-research-suite/" "$HOME/.codex/skills/academic-research-suite/"
```

检查 Codex 只会看到一个 root skill：

```bash
find "$HOME/.codex/skills/academic-research-suite" -name SKILL.md -print
find "$HOME/.codex/skills/academic-research-suite/ars" -name SKILL.md -print
```

第一条应该只输出 `academic-research-suite/SKILL.md`；第二条应该没有输出。

## 使用方式

在 Codex 中调用 root skill：

```text
Use $academic-research-suite. ars-plan Research question: How do quality assurance agencies evaluate AI governance in universities?
```

模糊 paper topic 会先进入 Socratic narrowing：

```text
Use $academic-research-suite. I want to write a paper on AI adoption in higher education quality assurance. I do not yet have a clear research question.
```

full pipeline，并要求停在 dashboard checkpoint：

```text
Use $academic-research-suite. ars-full Research question: How do QA agencies evaluate AI governance? Stop after producing the pipeline dashboard.
```

paper reviewer full mode：

```text
Use $academic-research-suite. ars-reviewer full review for this manuscript.
```

lit review：

```text
Use $academic-research-suite. ars-lit-review topic: AI governance evaluation in higher education quality assurance agencies.
```

调试路由时可以直接运行 planner：

```bash
ARS_CODEX_FULL_RUNTIME=1 ARS_CODEX_AGENT_TEAM=1 \
python3 skills/academic-research-suite/codex/scripts/ars_codex_full_runtime.py --pretty \
"ars-reviewer full review for this manuscript."
```

## 验证命令

Adapter gates：

```bash
python3 skills/academic-research-suite/codex/scripts/ars_codex_quality_gates.py all
```

Adapter tests：

```bash
pytest skills/academic-research-suite/codex/tests -q
```

Upstream pytest manifest：

```bash
cd skills/academic-research-suite/ars
PATH="$HOME/miniconda3/bin:$PATH" python scripts/run_ci_pytest_manifest.py
```

注意：Homebrew Python 3.14 在当前机器上缺少 `pytest` / `PyYAML`；已验证 `~/miniconda3/bin/python` 可运行 upstream manifest。

## 已知降级

Codex adapter 不声称 100% 复刻 Claude Code runtime。

- Claude slash commands 没有原生注册；Codex 通过 root skill router 和 planner 解析 `ars-*` aliases。
- Claude marketplace plugin install/update 没有 Codex 等价物；本仓库提供本地 skill 安装路径。
- `opus` / `sonnet` 在 Codex 中保留为 model hint，不会强制切换当前 Codex model。
- Agent-team 是 opt-in profile；默认 inline mode 不自动启动大量子代理。
- Hooks 是 disabled-by-default，并需要手动安装。
- Cross-model verification 不会被静默模拟；需要用户显式配置可用的外部模型或验证源。
- 部分 citation / claim audit / integrity gates 依赖外部资料源或 LLM 判断，只能做到 partial parity。

完整兼容性矩阵见：

```text
skills/academic-research-suite/codex/compatibility-matrix.md
```
