"""Each metric script counts what it names and refuses what it cannot read.

The scripts under `scripts/metrics/` print one number; their counting functions are
imported from their files and fed a tree built in `tmp_path`.
"""

import subprocess
from pathlib import Path

import pytest

from scripts.metrics import (
    backlog,
    conformance,
    counts,
    reading_set,
    references,
    tests_collected,
)

CHANGE = "0092-x"


def write(root: Path, name: str, text: str) -> None:
    """Write `text` to `name` under `root`, making its directories."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit(root: Path, message: str) -> str:
    """Return the sha of an empty commit with `message`."""
    conformance.git(
        root,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.com",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "--allow-empty",
        "-m",
        message,
    )
    return conformance.git(root, "rev-parse", "HEAD").strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    conformance.git(tmp_path, "init", "-q")
    return tmp_path


@pytest.mark.spec_exempt("structural: the collected count is the selected one")
@pytest.mark.parametrize(
    ("summary", "count"),
    [
        ("1447 tests collected in 0.68s", 1447),
        ("3/5 tests collected (2 deselected) in 0.10s", 3),
        ("1 test collected in 0.01s", 1),
        ("no tests collected in 0.01s", 0),
    ],
)
def test_the_collected_count_is_the_selected_one(summary: str, count: int) -> None:
    assert tests_collected.selected(f"tests/a.py::test_a\n\n{summary}\n") == count


@pytest.mark.spec_exempt("structural: twin of the collected count")
def test_a_collect_output_with_no_summary_is_refused() -> None:
    with pytest.raises(ValueError, match="collected"):
        tests_collected.selected("tests/a.py::test_a\n")


@pytest.mark.spec_exempt("structural: a failed pytest run is refused")
def test_a_pytest_run_that_errors_is_refused(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess([], 2, "", "")

    monkeypatch.setattr(tests_collected.subprocess, "run", fail)

    assert tests_collected.main([]) == 1
    assert "exited 2" in capsys.readouterr().err


@pytest.mark.spec_exempt("structural: the collected count is printed")
def test_the_count_is_printed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def collect(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess([], 0, "7/9 tests collected in 1s\n", "")

    monkeypatch.setattr(tests_collected.subprocess, "run", collect)

    assert tests_collected.main([]) == 0
    assert capsys.readouterr().out == "7\n"


@pytest.mark.spec_exempt("structural: a card opens with a bold id and a dot")
def test_a_card_opens_with_a_bold_id_and_a_dot() -> None:
    text = (
        "# Backlog\n\n"
        "- **0060·R5 — a**\n  body\n\n"
        "- **op·fix — b**\n\n"
        "- **no dot here**\n"
        "  - **0001·x — nested**\n"
    )

    assert backlog.cards(text) == 2


@pytest.mark.spec_exempt("structural: a missing backlog is refused")
def test_a_missing_backlog_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(backlog, "backlog_path", lambda: tmp_path / "none.md")

    assert backlog.main() == 1
    assert "unreadable" in capsys.readouterr().err


@pytest.mark.spec_exempt("structural: the backlog is the primary checkout's")
def test_the_backlog_is_in_the_primary_checkouts_minions(
    monkeypatch: pytest.MonkeyPatch, repo: Path
) -> None:
    monkeypatch.chdir(repo)

    assert backlog.backlog_path() == repo.resolve() / ".minions" / "debt.md"


@pytest.mark.spec_exempt("structural: a commit needs the change's trailer")
def test_a_commit_without_the_changes_trailer_is_counted(repo: Path) -> None:
    base = commit(repo, "chore: base")
    commit(repo, f"feat: a\n\nCo-Authored-By: t <t@example.com>\nChange: {CHANGE}")
    commit(repo, "feat: b")
    commit(repo, "feat: c\n\nChange: 0001-other")

    assert conformance.commits_without_trailer(repo, CHANGE, base, "HEAD") == 2
    assert conformance.commits_without_trailer(repo, CHANGE, "HEAD", "HEAD") == 0


@pytest.mark.spec_exempt("structural: an amend is a named subject")
def test_an_amend_is_a_named_subject(repo: Path) -> None:
    base = commit(repo, "chore: base")
    commit(repo, f"docs({CHANGE}): amend the change directory")
    commit(repo, f"docs({CHANGE}): land the change directory")
    commit(repo, "docs(0001-other): amend the change directory")

    assert conformance.amends(repo, CHANGE, base, "HEAD") == 1


@pytest.mark.spec_exempt("structural: a tracked .minions file is counted")
def test_a_tracked_minions_file_is_counted(repo: Path) -> None:
    write(repo, ".minions/a.json", "{}")
    write(repo, ".minions/sub/b.json", "{}")
    write(repo, "other.txt", "x")
    conformance.git(repo, "add", ".minions/a.json", "other.txt")

    assert conformance.minions_files_tracked(repo) == 1


@pytest.mark.spec_exempt("structural: a measure and its inputs are required")
def test_a_missing_measure_or_input_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo: Path,
) -> None:
    monkeypatch.chdir(repo)
    for name in ("MF_METRICS_CHANGE", "MF_METRICS_BASE", "MF_METRICS_HEAD"):
        monkeypatch.delenv(name, raising=False)

    assert conformance.main(["nonsense"]) == 1
    assert "usage" in capsys.readouterr().err
    assert conformance.main(["trailer"]) == 1
    assert "MF_METRICS_CHANGE" in capsys.readouterr().err


@pytest.mark.spec_exempt("structural: the measure runs on the collector's inputs")
def test_the_trailer_measure_reads_the_collectors_inputs(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo: Path,
) -> None:
    base = commit(repo, "chore: base")
    commit(repo, "feat: a")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("MF_METRICS_CHANGE", CHANGE)
    monkeypatch.setenv("MF_METRICS_BASE", base)
    monkeypatch.setenv("MF_METRICS_HEAD", "HEAD")

    assert conformance.main(["trailer"]) == 0
    assert capsys.readouterr().out == "1\n"


@pytest.mark.spec_exempt("structural: a bad revision is refused")
def test_a_bad_revision_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo: Path,
) -> None:
    commit(repo, "chore: base")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("MF_METRICS_CHANGE", CHANGE)
    monkeypatch.setenv("MF_METRICS_BASE", "no-such-revision")
    monkeypatch.setenv("MF_METRICS_HEAD", "HEAD")

    assert conformance.main(["amends"]) == 1
    assert "git failed" in capsys.readouterr().err


def docs_tree(root: Path) -> None:
    """Write a docs tree with one good and four broken references."""
    write(root, "docs/decisions.md", "# Decisions\n\n### D1 · The first\n\nbody\n")
    write(root, "docs/other.md", "# Other\n\n## A heading\n\n## A heading\n")
    write(
        root,
        "AGENTS.md",
        "[ok](docs/decisions.md#d1--the-first) [dup](docs/other.md#a-heading-1)\n"
        "[no file](docs/gone.md) [no anchor](docs/other.md#nope)\n"
        "[web](https://example.com/x) [self](#top) `[code](docs/gone.md)`\n"
        "See D1 and D9.\n\n```\n[fenced](docs/gone.md)\n```\n",
    )


@pytest.mark.spec_exempt(
    "structural: a link or decision that points nowhere is counted"
)
def test_a_reference_that_points_nowhere_is_counted(tmp_path: Path) -> None:
    docs_tree(tmp_path)

    assert references.broken_links(tmp_path, "AGENTS.md") == 3
    assert references.dangling_decisions(tmp_path, "AGENTS.md", {"1"}) == 1


@pytest.mark.spec_exempt("structural: the count spans the top-level docs and docs/")
def test_the_references_count_spans_the_scanned_docs(tmp_path: Path) -> None:
    docs_tree(tmp_path)

    assert references.scanned(tmp_path) == [
        "AGENTS.md",
        "docs/decisions.md",
        "docs/other.md",
    ]
    assert references.count(tmp_path) == 4


@pytest.mark.spec_exempt("structural: a heading's anchor is GitHub's")
def test_a_headings_anchor_is_githubs() -> None:
    assert references.slug("D10 · The face, `x`") == "d10--the-face-x"
    assert (
        references.slug("D1 · Stage ① is two independent verbs")
        == "d1--stage--is-two-independent-verbs"
    )
    assert references.anchors('# A\n\n## A\n\n<a id="Custom"></a>\n') == {
        "a",
        "a-1",
        "custom",
    }


@pytest.mark.spec_exempt("structural: missing decisions are refused")
def test_a_missing_decisions_file_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert references.main() == 1
    assert "unreadable" in capsys.readouterr().err


@pytest.mark.spec_exempt("structural: the reading set is its files' words")
def test_the_reading_set_is_its_files_words(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    for name in reading_set.READING_SET:
        write(tmp_path, name, "one two\nthree\n")
    monkeypatch.chdir(tmp_path)

    assert reading_set.words(tmp_path) == 3 * len(reading_set.READING_SET)
    assert reading_set.main() == 0
    assert capsys.readouterr().out == f"{3 * len(reading_set.READING_SET)}\n"


@pytest.mark.spec_exempt("structural: twin of the reading set's count")
def test_a_missing_reading_set_file_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert reading_set.main() == 1
    assert "unreadable" in capsys.readouterr().err


def counted_tree(root: Path) -> None:
    """Write a tree holding two flows, three scenarios and two decisions."""
    write(
        root,
        "tests/test_flow.py",
        'OTHER = {"x": 1}\nPINNED: dict[str, str] = {"a": "1", "b": "2"}\n',
    )
    write(root, "openspec/specs/one/spec.md", "#### Scenario: a\n#### Scenario: b\n")
    write(root, "openspec/specs/two/spec.md", "#### Scenario: c\n### Requirement: d\n")
    write(root, "docs/decisions.md", "### D0 · a\n\n### D1 · b\n\nD2 · not a heading\n")


@pytest.mark.spec_exempt("structural: each count reads what it names")
def test_each_count_reads_what_it_names(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    counted_tree(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert counts.pinned(tmp_path) == 2
    assert counts.scenarios(tmp_path) == 3
    assert counts.decisions(tmp_path) == 2
    assert counts.main(["scenarios"]) == 0
    assert capsys.readouterr().out == "3\n"


@pytest.mark.spec_exempt("structural: a count it cannot read is refused")
def test_a_count_it_cannot_read_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    write(tmp_path, "tests/test_flow.py", "OTHER = {}\n")
    monkeypatch.chdir(tmp_path)

    assert counts.main(["pinned"]) == 1
    assert "PINNED" in capsys.readouterr().err
    assert counts.main(["decisions"]) == 1
    assert counts.main(["nonsense"]) == 1
    assert "usage" in capsys.readouterr().err
