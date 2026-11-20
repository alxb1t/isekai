# The render names — design

`render_image` and `render_record` in `isekai/foundation/layout.py` name a render's image and record, and the sites that only build a name call them, with the answer unchanged. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

A render's image is `<seed><suffix>` in its group and its record is `<seed>.render.json`. The paid stage, review's `draft_from`, the comparison page and the evaluator each spell one of the two by hand, and three of them also spell the group's folder where `group_of` builds it. `isekai/foundation/layout.py` already holds `group_of`, the listing ([D69](../../../docs/decisions.md#d69--a-render-groups-files-are-listed-in-foundationlayoutpy-and-a-module-above-the-pipeline-reads-the-listing-from-the-foundation)) and `SIDECAR` as an import; `run.py` re-exports every name of it under `__all__` ([D62](../../../docs/decisions.md#d62--the-run-directory-is-runpy-its-siblings-imported-through-it)), and a module outside the foundation reads them from there.

`image_of` names a function in the stage, `image_of(run, flow, version, seed)` in `isekai/pipeline/generate.py`, and another in the edit, `image_of(record)` in `isekai/pipeline/edit.py`.

## Goals / Non-Goals

**Goals:**

- One builder for a render's image and one for its record, in the layout.
- Each site that only builds a name calls it, and each site that spells a group's folder calls `group_of`.
- Behaviour unchanged: every path built is the path built today, and no existing assertion changes.

**Non-Goals:**

- The sites where a name is a test for "rendered" ([D3](#d3)).
- A builder that takes a `Flow`, a ref type, a rule for "rendered", a spec delta.
- Any change to `render_groups`, `is_render` or the other listing names.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `render_image(group, seed, suffix)` and `render_record(group, seed)` in `layout.py`, re-exported by `run.py` | one place says how a render is named; `image_of` names the stage's function and the edit's already | a new `image_of`; a builder returning the pair as a tuple, which a caller would index |
| [D2](#d2) | The sites that only build a name switch; the ones that spell the group's folder call `group_of`; the stage's `image_of` stays and calls the builder | those sites only build a name, and `image_of` has callers in the routes and the tests | removing `image_of`, which changes its importers |
| [D3](#d3) | The sites where a name is a test for "rendered" stay as they are | the next version rewrites them by one rule; switching them twice pins what the rule changes | switching them here |
| [D4](#d4) | Proof by the suite as it stands, a case for each builder written first, a mutation run over each switched line under `isekai/` that holds a mutant, before and after, and one replay of the standing mutants (C14) | a rewrite is pre-flighted; `tools.mutate` refuses a line it finds no mutant in; the evaluator's sites are held by its own tests | a run over a line with no mutant, which exits 2; a run over a whole file; a run over the evaluator |
| [D5](#d5) | `skip_specs`; [D69](../../../docs/decisions.md#d69--a-render-groups-files-are-listed-in-foundationlayoutpy-and-a-module-above-the-pipeline-reads-the-listing-from-the-foundation)'s *Accepts* is amended and the change adds no decision | no requirement fits a rename of a call; a home a later version reads is D69's | a new decision for the builders |

### D1

`layout.py` gains, after `is_sidecar`:

```python
def render_image(group: Path, seed: int, suffix: str) -> Path:
    """Return the path of `seed`'s image in `group`, for a flow producing `suffix`."""
    return group / f"{seed}{suffix}"


def render_record(group: Path, seed: int) -> Path:
    """Return the path of `seed`'s record in `group`."""
    return group / f"{seed}{SIDECAR}"
```

`run.py` imports both from `layout.py` and lists them in `__all__`. `layout.py` imports nothing new: `SIDECAR` and `Path` are there already. Both are pure: they read no disk, and they take the suffix from the caller, since the flow's answer is the caller's ([D69](../../../docs/decisions.md#d69--a-render-groups-files-are-listed-in-foundationlayoutpy-and-a-module-above-the-pipeline-reads-the-listing-from-the-foundation)'s `rendered_seeds` does the same).

### D2

The sites, each read at the cut:

| site | spelled today | after |
|---|---|---|
| `image_of`, `isekai/pipeline/generate.py:190` | `group_of(run, flow.id, version) / f"{seed}{flow.output_suffix}"` | `render_image(group_of(run, flow.id, version), seed, flow.output_suffix)` |
| `discard_render`, `generate.py:352` | `group / f"{image.stem}{SIDECAR}"` | `render_record(group, seed)`; `seed` is read at `generate.py:349` |
| `render`, `generate.py:571` | `directory / f"{seed}{flow.output_suffix}"` | `render_image(directory, seed, flow.output_suffix)` |
| `render`, `generate.py:585` | `directory / f"{seed}{SIDECAR}"` | `render_record(directory, seed)` |
| `draft_from`, `isekai/pipeline/review.py:275` | `group_of(run, source, approval) / f"{seed}{OUTPUT_SUFFIX}"` | `render_image(group_of(run, source, approval), seed, OUTPUT_SUFFIX)` |
| `_renders`, `isekai/interface/compare_view.py:140` | `run.directory(name, OUTPUTS, f"{approved[-1]:03d}")` | `group_of(run, name, approved[-1])` |
| `_renders`, `compare_view.py:146` | `directory / f"{seed}{flow.output_suffix}"` | `render_image(directory, seed, flow.output_suffix)` |
| `evaluation/recall.py:341` | `run.directory(flow, OUTPUTS, f"{group:03d}", f"{seed}{suffix}")` | `render_image(group_of(run, flow, group), seed, suffix)` |
| `evaluation/__main__.py:126` | the same line | the same call |

`group_of` builds `run.directory(flow, OUTPUTS, f"{version:03d}")`, so each path is the one built today. The evaluator and `compare_view.py` import `group_of` and `render_image` from `isekai.foundation.run`, as they import `OUTPUTS` and `rendered` from it now. `OUTPUTS` goes from their imports and `SIDECAR` from `generate.py`'s, which nothing there reads after the switch; `ruff` names any other.

### D3

The sites that test for a render stay: `drafting_approval` (`review.py:329`, the record or the image), `refuse_revision` (`review.py:499`, the record), `_refuse_unchanged` (`review.py:1157`, the record) and `Surface.rendered` (`isekai/interface/ui/surface.py:223`, the record). They are the sites where "rendered" is defined, and the version after this one rewrites them by one rule. `source_copy` (`review.py:375`) names the draft's source copy, which is no render's file, and stays.

### D4

Each builder has a case in `tests/test_generate.py` before the builder exists, and a further case reads each name through `is_render` and `is_sidecar`, so the builders and the listing agree. No existing test's assertion changes.

A switched line under `isekai/` that holds a mutant has one `uv run python -m tools.mutate <path>:<lines> --tests <files>` run before its switch and one over its new lines after, as [CONTRIBUTING](../../../CONTRIBUTING.md) says a rewrite is pre-flighted. A survivor is killed by a case written first, or named equivalent in the phase's commit body.

`tools.mutate` mutates a comparison, a boolean, a `not`, an int, an arithmetic operator, a `raise`, a `return` and a statement of one call, and refuses a line with none (exit 2). Only `image_of`'s return in `generate.py` and `_renders`' group line in `compare_view.py` hold one. The other switched lines only assign a path, and the builders' cases and the suite as it stands hold them (C14).

The evaluator's sites are held by `tests/test_evaluation_cli.py` and `tests/test_recall_cli.py`. `uv run python -m tools.mutate --edits tests/mutants.json` replays the standing mutants once, after the switches. The new lines are the old ones moved down by the import edits of their file.

### D5

The change has no spec delta, and `.openspec.yaml` says `skip_specs: true`. [D69](../../../docs/decisions.md#d69--a-render-groups-files-are-listed-in-foundationlayoutpy-and-a-module-above-the-pipeline-reads-the-listing-from-the-foundation) is edited where it lives: its bold line names the builders, its *Accepts* says the sites that test for a render still name the files by hand, and *Made by* adds `0175`.

## Tests

The change adds unit tests and no end-to-end test; a render is named by a pure function, so the lowest layer holds it. No test is deleted or merged, so there is no `I16` table.

| layer | added | removed | command |
|---|---|---|---|
| unit | the cases of the builders and of their agreement with the listing, in `tests/test_generate.py` | none | `git grep -c -E "^def test_(render_image\|render_record\|a_built_name)" -- tests/test_generate.py` prints `3` after phase 1 |
| end-to-end | none | none | `git grep -c -E "render_image\|render_record" -- tests/e2e` exits 1 |

## Dependencies

None.

## Risks / Trade-offs

- **An import left unused fails the gate.** `ruff` names `SIDECAR` in `generate.py` and `OUTPUTS` in `compare_view.py`, `recall.py` and `__main__.py` once the switch leaves them unread; each task removes its own.
- **A mutation run's lines move with the imports.** The post-switch ranges are the old lines moved down by the import edits; the tasks give them, and `git grep -n` prints a site's real line.
- **A path assignment has no mutant.** The sites that only assign a path take no mutation run, so the builders' cases and the standing suite are their proof (C14).
- **A survivor before the switch** is an existing gap, not this change's; D4 says how it is closed, and a case for it extends [tasks](tasks.md) in the phase that finds it.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the builders and their cases, the stage's sites, the other sites, and the documents.
