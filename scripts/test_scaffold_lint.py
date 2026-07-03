#!/usr/bin/env python3
"""Tests for scaffold_lint.py — pytest style, `tmp_path`-fixture based.

No git and no real repo are required for the fixture-based tests: each
builds a synthetic scaffold-shaped tree under pytest's `tmp_path` fixture
and runs the linter against it directly, mirroring the conventions in
`scripts/test_knowledge_lint.py`. The live-repo test (task 2.3) is the
one exception — see its own docstring.
"""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scaffold_lint  # noqa: E402

# ===================================================================
# Helpers
# ===================================================================


def _write_tree(root: Path, files: dict[str, str]) -> None:
    """Write *files* (repo-relative path -> text content) under *root*,
    creating parent directories as needed."""
    for relpath, content in files.items():
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _run_main(root: Path) -> tuple[int, str]:
    argv = ["--root", str(root)]
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = scaffold_lint.main(argv)
    return exit_code, buf.getvalue()


# ===================================================================
# A minimal, clean scaffold-shaped fixture tree — satisfies all five
# checks simultaneously. Each violating test mutates a copy of this.
# ===================================================================

_AGENTS_MD_CLEAN = """\
# Test Project

> **MANDATORY — read this first**
>
> Some mandatory content.

## Roles

- Some role content.

## After reading this file
Acknowledge the roles above.
"""

_CONFIG_YAML_CLEAN = """\
schema: "1.0"

context:
  description: "Test project"

rules:
  tasks: "some rule"
"""

_HARNESS_CLEAN = """\
# Delegation harness

## (c) Bounded wait

Wrap every delegated call with `timeout -k <grace> <budget>`.

## (e) Timeout budget table

| Phase | Call | `timeout` flags | Budget (s) | Kill-grace | Notes |
|-------|------|-----------------|------------|------------|-------|
| apply | apply-executor | `-k 30 600` | 600 | 30s | note |
| verify | verifier | `-k 15 780` | 780 | 15s | note |
"""

_SKILL_CLEAN = """\
---
name: openspec-demo
---

Demo skill body. See `openspec-demo` for details and `knowledge-drift-review` for
the knowledge linter.

```bash
timeout -k 30 600 opencode run --dir <repoRoot> --agent apply-executor
```
"""

_KNOWLEDGE_DRIFT_REVIEW_SKILL = """\
---
name: knowledge-drift-review
---

The knowledge-drift-review skill body.
"""

_RUN_AUDIT_SKILL = """\
---
name: run-audit
---

The run-audit skill body.
"""

_AGENT_APPLY_EXECUTOR = """\
# apply-executor

Role description.
"""


def _clean_tree() -> dict[str, str]:
    return {
        "AGENTS.md": _AGENTS_MD_CLEAN,
        "openspec/config.yaml": _CONFIG_YAML_CLEAN,
        "scripts/scaffold_manifest.txt": (
            "scripts/scaffold_manifest.txt\n"
            ".claude/skills/knowledge-drift-review/SKILL.md\n"
            ".claude/skills/openspec-demo/SKILL.md\n"
            ".claude/skills/run-audit/SKILL.md\n"
            ".claude/skills/_shared/delegation-harness.md\n"
            ".claude/agents/apply-executor.md\n"
            ".opencode/agents/apply-executor.md\n"
            "scripts/foo.py\n"
        ),
        "scripts/scaffold_manifest_removed.txt": (
            "# clean fixture — no paths overlap with manifest\n.claude/skills/openspec-onboard/\n"
        ),
        "scripts/foo.py": "# a scaffold-managed script\n",
        ".claude/skills/knowledge-drift-review/SKILL.md": _KNOWLEDGE_DRIFT_REVIEW_SKILL,
        ".claude/skills/openspec-demo/SKILL.md": _SKILL_CLEAN,
        ".claude/skills/run-audit/SKILL.md": _RUN_AUDIT_SKILL,
        ".claude/skills/_shared/delegation-harness.md": _HARNESS_CLEAN,
        ".claude/agents/apply-executor.md": _AGENT_APPLY_EXECUTOR,
        ".opencode/agents/apply-executor.md": _AGENT_APPLY_EXECUTOR,
    }


def _build_clean_repo(tmp_path: Path) -> Path:
    _write_tree(tmp_path, _clean_tree())
    return tmp_path


# ===================================================================
# Whole-linter clean-fixture sanity check
# ===================================================================


def test_clean_fixture_zero_findings_exit_0(tmp_path):
    _build_clean_repo(tmp_path)

    findings = scaffold_lint.collect_findings(tmp_path)
    assert findings == []

    exit_code, stdout = _run_main(tmp_path)
    assert exit_code == 0
    assert "scaffold-lint: clean" in stdout


# ===================================================================
# manifest-completeness
# ===================================================================


def test_manifest_completeness_unlisted_file_flagged(tmp_path):
    tree = _clean_tree()
    tree[".claude/skills/openspec-other/SKILL.md"] = "---\nname: openspec-other\n---\nBody.\n"
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    manifest_findings = [f for f in findings if f.startswith("manifest-completeness:")]
    assert len(manifest_findings) == 1
    assert ".claude/skills/openspec-other/SKILL.md" in manifest_findings[0]

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


def test_manifest_completeness_missing_on_disk_flagged(tmp_path):
    tree = _clean_tree()
    tree["scripts/scaffold_manifest.txt"] += "scripts/does-not-exist.py\n"
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    manifest_findings = [f for f in findings if f.startswith("manifest-completeness:")]
    assert len(manifest_findings) == 1
    assert "scripts/does-not-exist.py" in manifest_findings[0]
    assert "does not exist on disk" in manifest_findings[0]

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


def test_manifest_completeness_exclusion_list_not_flagged(tmp_path):
    """scaffold_lint.py / test_scaffold_lint.py / sync_scaffold.py / etc. are
    authoring-side and must never be flagged even though they are not
    manifest-listed."""
    tree = _clean_tree()
    tree["scripts/sync_scaffold.py"] = "# sibling authoring tool\n"
    tree["scripts/scaffold_lint.py"] = "# this tool\n"
    tree["scripts/_probe_oneoff.py"] = "# a oneoff\n"
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    manifest_findings = [f for f in findings if f.startswith("manifest-completeness:")]
    assert manifest_findings == []


def test_manifest_completeness_oneoff_sh_excluded(tmp_path):
    """A scripts/_x_oneoff.sh present but not manifest-listed must NOT be
    flagged by manifest-completeness — the exclude glob now covers .sh oneoffs
    (scripts/_*_oneoff.*)."""
    tree = _clean_tree()
    tree["scripts/_x_oneoff.sh"] = "#!/usr/bin/env bash\necho oneoff\n"
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    manifest_findings = [f for f in findings if f.startswith("manifest-completeness:")]
    assert manifest_findings == []


# ===================================================================
# manifest-no-conflict
# ===================================================================


def test_manifest_no_conflict_clean_no_findings(tmp_path):
    _build_clean_repo(tmp_path)
    findings = scaffold_lint.collect_findings(tmp_path)
    assert not any(f.startswith("manifest-no-conflict:") for f in findings)


def test_manifest_no_conflict_overlap_flagged(tmp_path):
    tree = _clean_tree()
    # Add a path to the removed list that also appears in the manifest
    tree["scripts/scaffold_manifest_removed.txt"] = "# fixture — conflict\nscripts/foo.py\n"
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    no_conflict_findings = [f for f in findings if f.startswith("manifest-no-conflict:")]
    assert len(no_conflict_findings) == 1
    assert "scripts/foo.py" in no_conflict_findings[0]
    assert "appears in both" in no_conflict_findings[0]

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


def test_manifest_no_conflict_normalised_overlap_flagged(tmp_path):
    """A dir entry with trailing / in the removed list conflicts with the
    same normalised path in the manifest."""
    tree = _clean_tree()
    tree["scripts/scaffold_manifest_removed.txt"] = (
        "# fixture — normalised conflict\nscripts/foo.py/\n"
    )
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    no_conflict_findings = [f for f in findings if f.startswith("manifest-no-conflict:")]
    assert len(no_conflict_findings) == 1
    assert "scripts/foo.py" in no_conflict_findings[0]

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


# ===================================================================
# agents-md-structure
# ===================================================================


def test_agents_md_structure_clean_no_findings(tmp_path):
    _build_clean_repo(tmp_path)
    findings = scaffold_lint.collect_findings(tmp_path)
    assert not any(f.startswith("agents-md-structure:") for f in findings)


def test_agents_md_structure_anchor_renamed_flagged(tmp_path):
    tree = _clean_tree()
    # Rename to a heading that does NOT retain "## Roles" as a startswith
    # prefix, so both sub-checks (uniqueness count and reused-presence) are
    # genuinely exercised. (A rename like "## RolesRenamed" would still
    # satisfy `startswith("## Roles")` and under-test the uniqueness check.)
    tree["AGENTS.md"] = _AGENTS_MD_CLEAN.replace("## Roles", "## Contributor Info")
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    structure_findings = [f for f in findings if f.startswith("agents-md-structure:")]
    assert structure_findings
    # Renaming breaks both the uniqueness sub-check (count 0) and the
    # reused presence/no-tail sub-check (ValueError).
    assert any("'## Roles' appears 0 time(s)" in f for f in structure_findings)
    assert any("missing required section anchor" in f for f in structure_findings)

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


def test_agents_md_structure_anchor_duplicated_flagged(tmp_path):
    tree = _clean_tree()
    tree["AGENTS.md"] = _AGENTS_MD_CLEAN + "\n## Roles\n\nA second Roles heading.\n"
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    structure_findings = [f for f in findings if f.startswith("agents-md-structure:")]
    # Duplication is caught by the uniqueness sub-check even though the
    # reused sync_scaffold function (re.search, first-match) would not
    # detect it on its own.
    assert any("'## Roles' appears 2 time(s)" in f for f in structure_findings)

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


def test_agents_md_structure_anchor_deleted_flagged(tmp_path):
    tree = _clean_tree()
    lines = _AGENTS_MD_CLEAN.splitlines()
    lines = [ln for ln in lines if not ln.startswith("## After reading this file")]
    tree["AGENTS.md"] = "\n".join(lines) + "\n"
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    structure_findings = [f for f in findings if f.startswith("agents-md-structure:")]
    assert any("'## After reading this file' appears 0 time(s)" in f for f in structure_findings)
    assert any("missing required section anchor" in f for f in structure_findings)

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


def test_agents_md_structure_tail_present_flagged(tmp_path):
    tree = _clean_tree()
    tree["AGENTS.md"] = _AGENTS_MD_CLEAN + "\n# Unexpected tail section\n\nMore content.\n"
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    structure_findings = [f for f in findings if f.startswith("agents-md-structure:")]
    assert any("unexpected tail" in f for f in structure_findings)

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


# ===================================================================
# config-rules-last
# ===================================================================


def test_config_rules_last_clean_no_findings(tmp_path):
    _build_clean_repo(tmp_path)
    findings = scaffold_lint.collect_findings(tmp_path)
    assert not any(f.startswith("config-rules-last:") for f in findings)


def test_config_rules_last_extra_key_after_rules_flagged(tmp_path):
    tree = _clean_tree()
    tree["openspec/config.yaml"] = _CONFIG_YAML_CLEAN + '\nextra_key: "invalid here"\n'
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    config_findings = [f for f in findings if f.startswith("config-rules-last:")]
    assert len(config_findings) == 1
    assert "extra_key" in config_findings[0]

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


def test_config_rules_last_missing_block_flagged(tmp_path):
    tree = _clean_tree()
    tree["openspec/config.yaml"] = 'schema: "1.0"\n\ncontext:\n  description: "No rules here"\n'
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    config_findings = [f for f in findings if f.startswith("config-rules-last:")]
    # Both sub-checks fire here: (a) the explicit missing-block check, and
    # (b) sync_config_yaml's own early raise when the scaffold-side text it
    # is called with (the same text, reused reflexively) has no rules:
    # block at all — a distinct code path from the "target lacks it but
    # source has it" append case task 1.4(b) documents.
    assert len(config_findings) == 2
    assert any("no rules: block found in openspec/config.yaml" in f for f in config_findings)
    assert any("scaffold openspec/config.yaml has no rules: block" in f for f in config_findings)

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


# ===================================================================
# dangling-skill-refs
# ===================================================================


def test_dangling_skill_refs_clean_no_findings(tmp_path):
    _build_clean_repo(tmp_path)
    findings = scaffold_lint.collect_findings(tmp_path)
    assert not any(f.startswith("dangling-skill-refs:") for f in findings)


def test_dangling_skill_refs_unknown_token_flagged(tmp_path):
    tree = _clean_tree()
    tree["AGENTS.md"] = _AGENTS_MD_CLEAN + "\nSee `openspec-nonexistent` for details.\n"
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    dangling_findings = [f for f in findings if f.startswith("dangling-skill-refs:")]
    assert len(dangling_findings) == 1
    assert "AGENTS.md" in dangling_findings[0]
    assert "openspec-nonexistent" in dangling_findings[0]

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


def test_dangling_skill_refs_allowlisted_token_not_flagged(tmp_path):
    tree = _clean_tree()
    tree["AGENTS.md"] = _AGENTS_MD_CLEAN + "\nSee the openspec-scaffold repo.\n"
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    assert not any(f.startswith("dangling-skill-refs:") for f in findings)


def test_dangling_skill_refs_non_openspec_skill_without_dir_flagged(tmp_path):
    """Regression: a non-openspec skill in _NON_OPENSPEC_SKILL_TOKENS whose
    directory exists resolves cleanly; one whose directory does NOT exist is
    flagged as a dangling ref (detect-then-validate holds for the generalized
    set, not only a single hardcoded literal)."""
    tree = _clean_tree()
    # Remove run-audit dir + manifest entry so only knowledge-drift-review
    # exists on disk; reference both in AGENTS.md.
    tree.pop(".claude/skills/run-audit/SKILL.md")
    tree["scripts/scaffold_manifest.txt"] = tree["scripts/scaffold_manifest.txt"].replace(
        ".claude/skills/run-audit/SKILL.md\n", ""
    )
    tree["AGENTS.md"] = _AGENTS_MD_CLEAN + (
        "\nUse `knowledge-drift-review` for the LLM pass and `run-audit` for the audit cycle.\n"
    )
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    dangling_findings = [f for f in findings if f.startswith("dangling-skill-refs:")]
    assert len(dangling_findings) == 1
    assert "AGENTS.md" in dangling_findings[0]
    assert "run-audit" in dangling_findings[0]

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


# ===================================================================
# budget-agreement
# ===================================================================


def test_budget_agreement_clean_no_findings(tmp_path):
    _build_clean_repo(tmp_path)
    findings = scaffold_lint.collect_findings(tmp_path)
    assert not any(f.startswith("budget-agreement:") for f in findings)


def test_budget_agreement_embedded_pair_not_sanctioned_flagged(tmp_path):
    tree = _clean_tree()
    tree[".claude/skills/openspec-demo/SKILL.md"] = (
        _SKILL_CLEAN + "\n```bash\ntimeout -k 15 999 opencode run --dir <repoRoot>\n```\n"
    )
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    budget_findings = [f for f in findings if f.startswith("budget-agreement:")]
    assert len(budget_findings) == 1
    assert "openspec-demo/SKILL.md" in budget_findings[0]
    assert "-k 15 999" in budget_findings[0]

    exit_code, _stdout = _run_main(tmp_path)
    assert exit_code == 1


def test_budget_agreement_table_not_found_flagged(tmp_path):
    tree = _clean_tree()
    tree[".claude/skills/_shared/delegation-harness.md"] = (
        "# Delegation harness\n\nNo §e section here.\n"
    )
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    budget_findings = [f for f in findings if f.startswith("budget-agreement:")]
    assert any("§e table not found" in f for f in budget_findings)


# ===================================================================
# Live-repo test — SEAL
# ===================================================================


def test_live_repo_lints_clean():
    """Running scaffold_lint.py against THIS repo (the real, live tree —
    not a tmp_path fixture) reports zero findings and exits 0.

    This test is a SEAL, not test fragility: once it is green, any future
    instruction-file edit (AGENTS.md, a SKILL.md, an agent file, the
    delegation-harness budget table, openspec/config.yaml) that introduces
    a manifest-completeness / manifest-no-conflict / agents-md-structure /
    config-rules-last / dangling-skill-refs / budget-agreement violation
    will fail the suite by design. That IS the enforcement mechanism this
    change adds — a red result here means a real invariant was violated,
    not that the test is brittle. If this test ever surfaces a violation,
    the correct response is to fix the violating instruction file (or, if
    the fix is genuinely out of scope, to stop and report it as a blocker)
    — never to loosen or delete this test to make it pass.
    """
    repo_root = Path(__file__).resolve().parent.parent
    findings = scaffold_lint.collect_findings(repo_root)
    assert findings == [], "\n".join(findings)

    exit_code, stdout = _run_main(repo_root)
    assert exit_code == 0
    assert "scaffold-lint: clean" in stdout


def test_budget_agreement_could_not_parse_table_flagged(tmp_path):
    tree = _clean_tree()
    tree[".claude/skills/_shared/delegation-harness.md"] = (
        "# Delegation harness\n\n## (e) Timeout budget table\n\n"
        "| Phase | Call | flags | Budget | Grace |\n"
        "|-------|------|-------|--------|-------|\n"
        "| apply | apply-executor | -k 30 600 (no backticks) | 600 | 30s |\n"
    )
    _write_tree(tmp_path, tree)

    findings = scaffold_lint.collect_findings(tmp_path)
    budget_findings = [f for f in findings if f.startswith("budget-agreement:")]
    assert any("could not parse §e table" in f for f in budget_findings)
