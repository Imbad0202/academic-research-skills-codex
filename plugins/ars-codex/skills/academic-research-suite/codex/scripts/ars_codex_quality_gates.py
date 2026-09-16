#!/usr/bin/env python3
"""Static quality gates for the ARS-Codex full-runtime adapter."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable


SCRIPT = Path(__file__).resolve()
CODEX_ROOT = SCRIPT.parents[1]
SUITE_ROOT = SCRIPT.parents[2]
ARS_ROOT = SUITE_ROOT / "ars"
PLUGIN_ROOT_CANDIDATE = SUITE_ROOT.parents[1]
PLUGIN_ROOT = (
    PLUGIN_ROOT_CANDIDATE
    if (PLUGIN_ROOT_CANDIDATE / ".codex-plugin" / "plugin.json").is_file()
    else SUITE_ROOT.parents[1] / "plugins" / "ars-codex"
)
FULL_RUNTIME_MANIFEST = CODEX_ROOT / "full-runtime-manifest.json"
PACKAGE_MANIFEST = SUITE_ROOT / "manifest.json"
HOOK_PACK = CODEX_ROOT / "hooks" / "hooks.json"
TOPOLOGY_RUNNER = CODEX_ROOT / "scripts" / "ars_codex_topology_experiment.py"

FORBIDDEN_HOOK_PATTERNS = (
    r"\benv\b",
    r"\bprintenv\b",
    r"\bexport\b",
    r"\bcurl\b",
    r"\bwget\b",
    r"\brm\b",
    r"\bmv\b",
    r"\bcp\b",
    r"\bsudo\b",
    r"\bchmod\b",
    r"\bchown\b",
    r">",
    r"\|\s*sh\b",
    r"\|\s*bash\b",
    r"\.ssh",
    r"ANTHROPIC_API_KEY",
    r"OPENAI_API_KEY",
)


class GateFailure(RuntimeError):
    pass


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_manifest_path(value: str) -> Path:
    path = Path(value)
    if path.parts and path.parts[0] == "skills":
        return SUITE_ROOT.parents[1] / path
    return SUITE_ROOT / path


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GateFailure(message)


_WORKFLOW_NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_ROUTER_WORKFLOW_RE = re.compile(
    r"`ars/([a-z0-9]+(?:-[a-z0-9]+)*)/WORKFLOW\.md`"
)
_REQUIRED_WORKFLOWS = frozenset(
    {
        "deep-research",
        "academic-paper",
        "academic-paper-reviewer",
        "academic-pipeline",
        "experiment-agent",
    }
)


def _top_level_source_paths(source: object) -> set[str]:
    """Return canonical one-segment paths declared by one source lock."""
    if not isinstance(source, dict):
        return set()
    included_paths = source.get("included_paths")
    if not isinstance(included_paths, list):
        return set()
    names: set[str] = set()
    for value in included_paths:
        if not isinstance(value, str):
            continue
        path = Path(value)
        if len(path.parts) == 1 and _WORKFLOW_NAME_RE.fullmatch(path.name):
            names.add(path.name)
    return names


def _external_workflow_names(package: dict[str, Any]) -> set[str]:
    """Return separately sourced top-level names, excluding primary overlaps.

    A secondary source such as ``experiment-agent`` may live beside the four
    canonical ARS workflows without becoming part of the ARS inventory parity
    contract. A name also declared by the primary ARS source remains core: a
    secondary lock must never make a canonical workflow disappear from this
    gate.
    """
    sources = package.get("source_repositories")
    _require(isinstance(sources, list), "package manifest source_repositories must be a list")
    primary: set[str] = set()
    secondary: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            continue
        names = _top_level_source_paths(source)
        if source.get("name") == "academic-research-skills":
            primary.update(names)
        else:
            secondary.update(names)
    return secondary - primary


def _root_router_workflow_names(root_skill: Path) -> set[str]:
    """Read workflow names from the root router table, not incidental prose."""
    text = root_skill.read_text(encoding="utf-8")
    section = re.search(
        r"(?ms)^## Workflow Router\s*$\n(?P<body>.*?)(?=^##\s|\Z)",
        text,
    )
    _require(bool(section), "root SKILL.md is missing the Workflow Router section")
    table: list[str] = []
    for line in section.group("body").splitlines():
        if line.lstrip().startswith("|"):
            table.append(line)
        elif table:
            break
    _require(bool(table), "root SKILL.md Workflow Router table is missing")

    def cells(line: str) -> list[str]:
        stripped = line.strip()
        _require(
            stripped.startswith("|") and stripped.endswith("|"),
            f"root SKILL.md Workflow Router has malformed table row: {line!r}",
        )
        return [cell.strip() for cell in stripped[1:-1].split("|")]

    _require(
        len(table) >= 3,
        "root SKILL.md Workflow Router table needs a header, divider, and workflow row",
    )
    headers = cells(table[0])
    expected_headers = ("User intent", "Read first")
    _require(
        all(headers.count(header) == 1 for header in expected_headers),
        "root SKILL.md Workflow Router table headers must include exactly one "
        f"'User intent' and 'Read first': {headers}",
    )
    divider = cells(table[1])
    _require(
        len(divider) == len(headers)
        and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in divider),
        "root SKILL.md Workflow Router table divider does not match its headers",
    )
    read_first_index = headers.index("Read first")
    matches: list[str] = []
    for row_number, line in enumerate(table[2:], start=1):
        row = cells(line)
        _require(
            len(row) == len(headers),
            f"root SKILL.md Workflow Router row {row_number} has {len(row)} columns; "
            f"expected {len(headers)}",
        )
        row_matches = _ROUTER_WORKFLOW_RE.findall(row[read_first_index])
        _require(
            len(row_matches) == 1,
            f"root SKILL.md Workflow Router row {row_number} Read first cell must "
            "contain exactly one ars/<workflow>/WORKFLOW.md path",
        )
        matches.extend(row_matches)
    duplicates = sorted(name for name in set(matches) if matches.count(name) > 1)
    _require(not duplicates, f"root SKILL.md Workflow Router has duplicate workflows: {duplicates}")
    return set(matches)


def _runtime_workflow_names(manifest: dict[str, Any]) -> set[str]:
    workflows = manifest.get("workflows")
    _require(isinstance(workflows, dict), "full-runtime manifest workflows must be an object")
    invalid = sorted(
        str(name)
        for name in workflows
        if not isinstance(name, str) or _WORKFLOW_NAME_RE.fullmatch(name) is None
    )
    _require(not invalid, f"full-runtime manifest has invalid workflow names: {invalid}")
    return set(workflows)


def _require_inventory_equal(
    disk: set[str], other: set[str], surface: str
) -> None:
    missing = sorted(disk - other)
    extra = sorted(other - disk)
    _require(
        not missing and not extra,
        f"core workflow inventory mismatch for {surface}: "
        f"missing_from_{surface}={missing}, extra_in_{surface}={extra}",
    )


def check_manifest() -> list[str]:
    manifest = _json(FULL_RUNTIME_MANIFEST)
    messages = ["full-runtime manifest parses as JSON"]

    package = _json(PACKAGE_MANIFEST)
    adapter_version = package.get("adapter_version")
    suite_match = re.search(
        r'(?m)^\s+version:\s*"([^"]+)"\s*$',
        (ARS_ROOT / "academic-pipeline" / "WORKFLOW.md").read_text(encoding="utf-8"),
    )
    _require(bool(suite_match), "academic-pipeline suite version is missing")
    _require(
        suite_match.group(1) == adapter_version,
        f"upstream suite version {suite_match.group(1)!r} != adapter version {adapter_version!r}",
    )
    sources = [source for source in package.get("source_repositories", [])
               if source.get("name") == "academic-research-skills"]
    _require(len(sources) == 1, "package requires exactly one ARS source lock")
    _require(
        sources[0].get("version") == adapter_version
        and sources[0].get("tag") == f"v{adapter_version}",
        "ARS source version/tag must match the adapter release",
    )
    skill_match = re.search(
        r'(?m)^\s+version:\s*"([^"]+)"\s*$',
        (SUITE_ROOT / "SKILL.md").read_text(encoding="utf-8"),
    )
    _require(bool(skill_match), "root SKILL.md metadata version is missing")
    _require(
        skill_match.group(1) == adapter_version,
        f"SKILL.md version {skill_match.group(1)!r} != adapter version {adapter_version!r}",
    )
    plugin_version = _json(PLUGIN_ROOT / ".codex-plugin" / "plugin.json").get("version")
    _require(
        plugin_version == adapter_version,
        f"Desktop plugin version {plugin_version!r} != adapter version {adapter_version!r}",
    )
    repo_version_path = SUITE_ROOT.parents[1] / "VERSION"
    if repo_version_path.is_file():
        repo_version = repo_version_path.read_text(encoding="utf-8").strip()
        _require(
            repo_version == adapter_version,
            f"repo VERSION {repo_version!r} != adapter version {adapter_version!r}",
        )
    messages.append(f"package version {adapter_version} is aligned across upstream suite, source tag, skill, manifest, plugin, and VERSION")

    for key, value in manifest["paths"].items():
        if key in {"adapter_root"}:
            continue
        path = _resolve_manifest_path(value)
        _require(path.exists(), f"manifest path missing for {key}: {value}")
    messages.append("declared adapter paths exist")

    aliases: set[str] = set()
    for command in manifest["commands"]:
        for alias in command["aliases"]:
            _require(alias not in aliases, f"duplicate alias: {alias}")
            aliases.add(alias)
        recipe = SUITE_ROOT / command["recipe"]
        _require(recipe.exists(), f"command recipe missing: {command['recipe']}")
    for required in (
        "ars-reviewer",
        "ars-mark-read",
        "ars-unmark-read",
        "ars-cache-invalidate",
        "ars-3w",
        "ars-rebuttal-audit",
        "ars-full",
        "ars-plan",
        "ars-lit-review",
    ):
        _require(required in aliases, f"required alias absent: {required}")
    messages.append(f"{len(manifest['commands'])} command routes have recipes")

    for name, workflow in manifest["workflows"].items():
        workflow_path = SUITE_ROOT / workflow["workflow_path"]
        _require(workflow_path.exists(), f"workflow path missing for {name}: {workflow['workflow_path']}")
        template = SUITE_ROOT / workflow["agent_template"]
        _require(template.exists(), f"agent template missing for {name}: {workflow['agent_template']}")
    messages.append(f"{len(manifest['workflows'])} workflows have templates")

    allowed_gate_kinds = {
        "packaging",
        "routing",
        "agent-team",
        "review",
        "integrity",
        "material-passport",
        "evaluation",
        "transparency",
        "hooks",
        "provenance",
    }
    allowed_parity = {"full", "near", "partial", "exploratory"}
    local_runners = {"manifest", "router", "fixture", "topology-experiment", "hook-safety"}
    gate_ids: set[str] = set()
    active_upstream_paths: set[Path] = set()
    for index, gate in enumerate(manifest.get("quality_gates", [])):
        _require(isinstance(gate, dict), f"quality_gates[{index}] must be an object")
        for key in ("id", "kind", "runner", "parity"):
            _require(
                isinstance(gate.get(key), str) and bool(gate[key]),
                f"quality_gates[{index}] missing non-empty {key}",
            )
        gate_id = gate["id"]
        _require(gate_id not in gate_ids, f"duplicate quality gate id: {gate_id}")
        gate_ids.add(gate_id)
        _require(gate["kind"] in allowed_gate_kinds, f"unknown quality gate kind: {gate['kind']}")
        _require(gate["parity"] in allowed_parity, f"unknown quality gate parity: {gate['parity']}")
        execution = gate.get("execution")
        _require(
            execution is None or execution == "hermetic",
            f"quality gate {gate_id} has unsupported execution mode: {execution!r}",
        )
        runner = gate["runner"]
        if runner.startswith("upstream:"):
            runner_path = SUITE_ROOT / runner.removeprefix("upstream:")
            _require(runner_path.is_file(), f"quality gate runner missing for {gate_id}: {runner}")
            active_upstream_paths.add(runner_path.resolve())
        else:
            _require(runner in local_runners, f"unknown local quality gate runner: {runner}")
    messages.append(f"{len(gate_ids)} quality gates have unique ids and resolvable runners")

    inactive_paths: set[Path] = set()
    for index, entry in enumerate(package.get("inactive_upstream_scripts", [])):
        _require(
            isinstance(entry, dict),
            f"inactive_upstream_scripts[{index}] must be an object",
        )
        value = entry.get("path")
        reason = entry.get("reason")
        _require(isinstance(value, str) and bool(value), f"inactive entry {index} has no path")
        _require(isinstance(reason, str) and bool(reason.strip()), f"inactive entry {value} has no reason")
        inactive_path = _resolve_manifest_path(value)
        _require(inactive_path.is_file(), f"inactive upstream path missing: {value}")
        resolved = inactive_path.resolve()
        _require(resolved not in inactive_paths, f"duplicate inactive upstream path: {value}")
        _require(
            resolved not in active_upstream_paths,
            f"inactive upstream path is also registered as an active gate: {value}",
        )
        inactive_paths.add(resolved)
    messages.append(f"{len(inactive_paths)} inactive upstream paths are unique and documented")
    return messages


def check_single_root_skill() -> list[str]:
    root_skill = SUITE_ROOT / "SKILL.md"
    _require(root_skill.exists(), "root SKILL.md missing")
    vendored_skill_files = sorted(ARS_ROOT.rglob("SKILL.md"))
    _require(not vendored_skill_files, "vendored workflow SKILL.md files would expose duplicate Codex skills: " + ", ".join(str(p) for p in vendored_skill_files))
    workflow_files = sorted(ARS_ROOT.glob("*/WORKFLOW.md"))
    disk_names = {path.parent.name for path in workflow_files}
    router_names = _root_router_workflow_names(root_skill)
    runtime_names = _runtime_workflow_names(_json(FULL_RUNTIME_MANIFEST))
    external_names = _external_workflow_names(_json(PACKAGE_MANIFEST))

    for surface, names in (
        ("root router", router_names),
        ("full-runtime manifest", runtime_names),
    ):
        dangling = sorted(names - disk_names)
        _require(
            not dangling,
            f"{surface} lists workflows without WORKFLOW.md on disk: {dangling}",
        )

    for surface, names in (
        ("disk", disk_names),
        ("root router", router_names),
        ("full-runtime manifest", runtime_names),
    ):
        missing_required = sorted(_REQUIRED_WORKFLOWS - names)
        _require(
            not missing_required,
            f"{surface} is missing required workflows: {missing_required}",
        )

    router_external = router_names & external_names
    runtime_external = runtime_names & external_names
    _require(
        router_external == runtime_external,
        "separately sourced workflow inventory mismatch between root router and "
        "full-runtime manifest: "
        f"missing_from_root_router={sorted(runtime_external - router_external)}, "
        f"missing_from_full_runtime_manifest={sorted(router_external - runtime_external)}",
    )

    disk_core = disk_names - external_names
    _require_inventory_equal(disk_core, router_names - external_names, "root_router")
    _require_inventory_equal(
        disk_core,
        runtime_names - external_names,
        "full_runtime_manifest",
    )
    return [
        "single root skill is the only Codex-discoverable skill",
        f"{len(disk_core)} core workflows match disk, root router, and full-runtime manifest",
        f"{len(disk_names & external_names)} separately sourced workflow(s) excluded from core parity",
    ]


def check_hook_safety() -> list[str]:
    pack = _json(HOOK_PACK)
    _require(pack.get("default_enabled") is False, "hook pack must be disabled by default")
    _require(pack.get("enabled_when") == "ARS_CODEX_HOOKS=1", "hook pack must require ARS_CODEX_HOOKS=1")
    hooks = pack.get("hooks", [])
    _require(isinstance(hooks, list), "hooks must be a list")
    for hook in hooks:
        _require(hook.get("mutates_files") is False, f"hook mutates files: {hook.get('id')}")
        command = hook.get("command", "")
        _require(command.startswith("python3 "), f"hook command must use python3 wrapper: {command}")
        _require("ars_codex_hook.py" in command, f"hook command must use adapter hook wrapper: {command}")
        for pattern in FORBIDDEN_HOOK_PATTERNS:
            _require(not re.search(pattern, command), f"unsafe hook command pattern {pattern!r}: {command}")
    return [f"{len(hooks)} hook command(s) are disabled-by-default and pass static safety checks"]


def check_reviewer_fixture(fixture: Path | None = None) -> list[str]:
    fixture = fixture or CODEX_ROOT / "tests" / "fixtures" / "reviewer_full_independent_sections.md"
    text = fixture.read_text(encoding="utf-8")
    required = [
        "## Independent Reviewer: Journal-Fit",
        "## Independent Reviewer: Methodology",
        "## Independent Reviewer: Domain",
        "## Independent Reviewer: Interdisciplinary",
        "## Independent Reviewer: Devil's Advocate",
        "## Editorial Synthesis",
    ]
    positions = []
    for heading in required:
        matches = list(re.finditer(r"^" + re.escape(heading) + r"\s*$", text, re.MULTILINE))
        _require(len(matches) == 1, f"reviewer fixture requires one heading: {heading}")
        positions.append(matches[0].start())
    _require(positions == sorted(positions), "editorial synthesis must appear after independent reviewer sections")
    synthesis = text[positions[-1]:]
    for marker in (
        "journal-fit concern retained", "methodology concern retained",
        "domain concern retained", "interdisciplinary concern retained",
        "devil's advocate dissent retained",
    ):
        _require(marker in synthesis, f"synthesis dropped minority marker: {marker}")
    return ["paper-reviewer full-mode fixture preserves independent reviewer sections before synthesis"]


def check_upstream_lock() -> list[str]:
    package = _json(PACKAGE_MANIFEST)
    sources = {item["name"]: item for item in package["source_repositories"]}
    ars = sources.get("academic-research-skills")
    _require(bool(ars), "package manifest missing academic-research-skills source")
    commit = ars.get("commit", "")
    _require(bool(re.fullmatch(r"[0-9a-f]{40}", commit)), f"academic-research-skills lock is not a full SHA: {commit}")
    included = set(ars.get("included_paths", []))
    for path in ("commands", "hooks", "tests", "docs", "shared", "scripts"):
        _require(path in included or any(path in item for item in included), f"included_paths missing {path}")
    return [f"upstream lock pins academic-research-skills@{commit[:7]}"]


def check_topology_experiment() -> list[str]:
    spec = importlib.util.spec_from_file_location("ars_codex_topology_experiment", TOPOLOGY_RUNNER)
    _require(bool(spec and spec.loader), "topology experiment runner cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.validate_all(require_runs=False)
    _require(result["status"] == "PASS", "topology experiment contract failed: " + ", ".join(result["reason_codes"]))
    _require(result["task_count"] == 10, "topology experiment cohort must contain exactly 10 tasks")
    _require(result["expected_run_count"] == 26, "topology experiment must declare exactly 26 matched task-arm runs")
    return [
        "topology experiment cohort freezes 10 tasks across reviewer and research/pipeline strata",
        "26 task-arm plans have valid input digests and acyclic DAGs",
    ]


def check_desktop_plugin_bundle() -> list[str]:
    plugin_manifest = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
    plugin_skills = PLUGIN_ROOT / "skills"
    suite_entry = plugin_skills / "academic-research-suite"
    skill_md = suite_entry / "SKILL.md"
    package_manifest = suite_entry / "manifest.json"

    _require(plugin_manifest.is_file(), f"Desktop plugin manifest missing: {plugin_manifest}")
    manifest = _json(plugin_manifest)
    _require(manifest.get("name") == "ars-codex", "Desktop plugin name must be ars-codex")
    _require(
        manifest.get("interface", {}).get("displayName") == "ARS-Codex",
        "Desktop plugin display name must be ARS-Codex",
    )
    _require(
        PLUGIN_ROOT.name == manifest.get("name"),
        "Desktop plugin directory must match plugin manifest name",
    )
    _require(manifest.get("skills") == "./skills/", "Desktop plugin manifest must point at ./skills/")
    _require(plugin_skills.exists(), f"Desktop plugin skills path missing: {plugin_skills}")
    _require(plugin_skills.is_dir(), "Desktop plugin skills path must be a directory")
    _require(not plugin_skills.is_symlink(), "Desktop plugin skills path must not be a symlink")
    _require(suite_entry.is_dir(), "Desktop plugin bundle must include academic-research-suite")
    _require(skill_md.is_file(), "Desktop plugin bundle academic-research-suite is missing SKILL.md")
    _require(package_manifest.is_file(), "Desktop plugin bundle academic-research-suite is missing manifest.json")

    marketplace_path = SUITE_ROOT.parents[1] / ".agents" / "plugins" / "marketplace.json"
    if marketplace_path.is_file():
        marketplace = _json(marketplace_path)
        _require(marketplace.get("name") == "ars-codex", "repo marketplace name must be ars-codex")
        _require(
            marketplace.get("interface", {}).get("displayName") == "ARS-Codex",
            "repo marketplace display name must be ARS-Codex",
        )
        entries = [entry for entry in marketplace.get("plugins", []) if entry.get("name") == "ars-codex"]
        _require(len(entries) == 1, "repo marketplace must contain exactly one ars-codex entry")
        source = entries[0].get("source", {})
        _require(source.get("source") == "local", "ars-codex marketplace source must be local")
        _require(source.get("path") == "./plugins/ars-codex", "ars-codex marketplace path is incorrect")
        policy = entries[0].get("policy", {})
        _require(policy.get("installation") == "AVAILABLE", "ars-codex must be available to install")
        _require(policy.get("authentication") == "ON_INSTALL", "ars-codex auth policy must be ON_INSTALL")
        _require(entries[0].get("category") == "Research", "ars-codex marketplace category must be Research")

    symlinks = sorted(
        str(path.relative_to(PLUGIN_ROOT))
        for path in plugin_skills.rglob("*")
        if path.is_symlink()
    )
    _require(
        not symlinks,
        "Desktop plugin bundle must not contain symlinks: " + ", ".join(symlinks[:20]),
    )

    ignored_names = {".DS_Store", ".pytest_cache", "__pycache__"}

    def materialized_files(root: Path) -> dict[str, Path]:
        return {
            path.relative_to(root).as_posix(): path
            for path in root.rglob("*")
            if path.is_file()
            and not any(part in ignored_names for part in path.relative_to(root).parts)
            and path.suffix != ".pyc"
            and path.suffix != ".log"
        }

    if suite_entry.resolve() != SUITE_ROOT.resolve():
        canonical = materialized_files(SUITE_ROOT)
        bundled = materialized_files(suite_entry)
        missing = sorted(canonical.keys() - bundled.keys())
        extra = sorted(bundled.keys() - canonical.keys())
        changed = sorted(
            rel_path
            for rel_path in canonical.keys() & bundled.keys()
            if canonical[rel_path].read_bytes() != bundled[rel_path].read_bytes()
        )
        _require(
            not (missing or extra or changed),
            "Desktop plugin bundle differs from canonical skill: "
            f"missing={missing[:10]}, extra={extra[:10]}, changed={changed[:10]}",
        )
    return [
        "ARS-Codex plugin and marketplace identities are aligned",
        "Desktop plugin bundle uses a materialized skills directory",
        "academic-research-suite is bundled without symlinks",
        "Desktop plugin bundle is byte-identical to the canonical skill",
    ]


GATES: dict[str, Callable[[], list[str]]] = {
    "desktop-plugin-bundle": check_desktop_plugin_bundle,
    "manifest": check_manifest,
    "single-root-skill": check_single_root_skill,
    "hook-safety": check_hook_safety,
    "reviewer-fixture": check_reviewer_fixture,
    "upstream-lock": check_upstream_lock,
    "topology-experiment": check_topology_experiment,
}


def run_gate(name: str) -> list[str]:
    return GATES[name]()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gate", choices=sorted([*GATES, "all"]))
    parser.add_argument("--json", action="store_true", help="Emit machine-readable result")
    args = parser.parse_args()

    selected = list(GATES) if args.gate == "all" else [args.gate]
    results: dict[str, Any] = {}
    failed = False
    for name in selected:
        try:
            results[name] = {"ok": True, "messages": run_gate(name)}
        except GateFailure as exc:
            failed = True
            results[name] = {"ok": False, "error": str(exc)}

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        for name, result in results.items():
            if result["ok"]:
                print(f"OK {name}: " + "; ".join(result["messages"]))
            else:
                print(f"FAIL {name}: {result['error']}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
