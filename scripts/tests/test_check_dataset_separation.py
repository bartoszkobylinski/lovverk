"""Writer separation between the Lovdata datasets and the local one, on a real git repo."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import ModuleType

import pytest


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def commit(repo: Path, files: dict[str, str], message: str) -> str:
    for relative, content in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    git(repo, "add", "--", *files)
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    commit(
        tmp_path,
        {"manifest.json": '{"documents": {}}\n', "lover/akt.md": "# Akt\n"},
        "init",
    )
    return tmp_path


def test_local_only_change_passes(separation: ModuleType, repo: Path) -> None:
    base = git(repo, "rev-parse", "HEAD")
    head = commit(repo, {"lokale-forskrifter/manifest.json": "{}\n"}, "local")
    assert separation.check(repo, base, head, aggregate=True) == []


def test_central_only_change_passes(separation: ModuleType, repo: Path) -> None:
    base = git(repo, "rev-parse", "HEAD")
    head = commit(repo, {"manifest.json": '{"documents": {"a": {}}}\n'}, "sync")
    assert separation.check(repo, base, head, aggregate=True) == []


@pytest.mark.parametrize("central", ["manifest.json", "lover/akt.md", "forskrifter/ny.md"])
def test_commit_touching_both_fails(separation: ModuleType, repo: Path, central: str) -> None:
    base = git(repo, "rev-parse", "HEAD")
    head = commit(repo, {"lokale-forskrifter/manifest.json": "{}\n", central: "changed\n"}, "both")
    problems = separation.check(repo, base, head)
    assert len(problems) == 1
    assert central in problems[0]


def test_scripts_and_docs_with_local_change_pass(separation: ModuleType, repo: Path) -> None:
    base = git(repo, "rev-parse", "HEAD")
    head = commit(
        repo,
        {
            "lokale-forskrifter/manifest.json": "{}\n",
            "README.md": "# r\n",
            "scripts/check.py": "pass\n",
        },
        "skeleton",
    )
    assert separation.check(repo, base, head, aggregate=True) == []


def test_split_across_commits_fails_only_in_aggregate(separation: ModuleType, repo: Path) -> None:
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, {"lokale-forskrifter/manifest.json": "{}\n"}, "local")
    head = commit(repo, {"manifest.json": '{"documents": {"x": {}}}\n'}, "root")
    assert separation.check(repo, base, head) == []
    problems = separation.check(repo, base, head, aggregate=True)
    assert len(problems) == 1
    assert "manifest.json" in problems[0]


def test_unknown_base_checks_the_head_commit(separation: ModuleType, repo: Path) -> None:
    head = commit(
        repo, {"lokale-forskrifter/manifest.json": "{}\n", "manifest.json": "{}\n"}, "both"
    )
    assert len(separation.check(repo, "0" * 40, head)) == 1


def test_root_commit_touching_both_fails(separation: ModuleType, tmp_path: Path) -> None:
    git(tmp_path, "init", "-q", "-b", "main")
    head = commit(
        tmp_path, {"lokale-forskrifter/manifest.json": "{}\n", "manifest.json": "{}\n"}, "root"
    )
    assert len(separation.check(tmp_path, "0" * 40, head)) == 1


def test_main_usage_and_exit_codes(
    separation: ModuleType, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(separation, "REPO_ROOT", repo)
    base = git(repo, "rev-parse", "HEAD")
    assert separation.main([]) == 2
    head = commit(repo, {"lokale-forskrifter/manifest.json": "{}\n"}, "local")
    assert separation.main([base, head, "--aggregate"]) == 0
    head = commit(repo, {"lokale-forskrifter/x.md": "x\n", "manifest.json": "{}\n"}, "both")
    assert separation.main([base, head]) == 1
