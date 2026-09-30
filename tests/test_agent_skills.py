"""The agent skills: every command they name is one this build accepts.

A skill exists so an agent runs the flows without reading the source, and it is
worth that only while its commands are true.
"""

import re
import shlex
from pathlib import Path

import pytest

from isekai.interface.cli import build_parser

SKILLS = Path(__file__).resolve().parent.parent / ".claude" / "skills"
ENTRY = "python -m isekai"
# Where a command's own words end and the shell's begin.
SHELL = {">", ">>", "2>&1", "&", ";", "&&", "||", "|"}
FENCE = re.compile(r"^```[a-z]*\n(.*?)^```", re.M | re.S)


def commands(text: str) -> list[str]:
    """Return each `python -m isekai` line inside a code block, continuations joined."""
    lines = []
    for block in FENCE.findall(text):
        for line in block.replace("\\\n", " ").splitlines():
            if ENTRY in line:
                lines.append(" ".join(line.split()))
    return lines


def refused(skills: dict[str, str]) -> list[str]:
    """Return `<skill>: <line>` for every command the parser does not accept."""
    found = []
    for name, text in sorted(skills.items()):
        for line in commands(text):
            words = shlex.split(line.split(ENTRY, 1)[1])
            argv = words[: next((i for i, w in enumerate(words) if w in SHELL), None)]
            try:
                build_parser().parse_args(argv)
            except SystemExit:
                found.append(f"{name}: {line}")
    return found


@pytest.mark.spec("agent-skills:commands:every-command-parses")
def test_every_command_a_skill_names_parses(capsys: pytest.CaptureFixture[str]) -> None:
    skills = {p.parent.name: p.read_text() for p in SKILLS.glob("*/SKILL.md")}
    assert {"run-flows", "compare-renders"} <= set(skills)
    assert all(commands(text) for text in skills.values())

    assert refused(skills) == []


@pytest.mark.spec("agent-skills:commands:a-stale-command-fails")
def test_a_skill_naming_a_flag_the_parser_refuses_is_reported(
    capsys: pytest.CaptureFixture[str],
) -> None:
    skill = (
        "```bash\n"
        'uv run python -m isekai compare .data/b1 >> "$BATCH/log.txt" 2>&1\n'
        "uv run python -m isekai tag --flows summon-anime-wai \\\n"
        '  --runs "$BATCH/runs" "$BATCH"/photos/*\n'
        "```\n"
    )

    assert refused({"stale": skill}) == [
        "stale: uv run python -m isekai tag --flows summon-anime-wai "
        '--runs "$BATCH/runs" "$BATCH"/photos/*'
    ]
