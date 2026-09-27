---
name: compare-renders
description: Build the comparison page for a batch that is already rendered — each run's photograph beside each flow's renders — and hand the operator its path. Use when the operator asks for the comparison page of .data/<batch>, or to rebuild it.
---

# compare-renders — the comparison page for a batch

Writes `.data/<batch>/compare.html`: every run's photograph beside each flow's renders under its latest approval,
each render with its positive prompt, and the captions in a row below. The page links the images and embeds none.
Why: [0035 design D2](../../../openspec/changes/archive/0035-the-flow-skills/design.md#d2).

## Never

- **Never read** the page, a photograph, or anything under `runs/`. The verb reads them so you do not.

## Run

```bash
uv run python -m isekai compare .data/<batch>
```

- **Exit 0**: it printed one line, the page's path. Hand that path to the operator.
- **Exit 1**: it printed a `refused:` line naming the directory and the fix. Show it to the operator.

To run the whole batch first, use the `run-flows` skill.
