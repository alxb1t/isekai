---
bump: patch
after: [0192-the-model-manifests]
---

# The command builder

A command a person is told to run is built by one function, `command(verb, *words)` in `isekai/foundation/command.py`, and a test holds that nothing else spells the entry; every printed byte stays equal.

Reading map: [design](design.md) holds the builder, each conversion before and after, and the guard, [tasks](tasks.md) its phases: the builder, the builders, the sites, the guard, the documents.

## Why

A command a refusal or a message prints starts with `python -m isekai`. Builders make it in some places and sites spell it again by hand in others, some behind a `uv run` prefix, so a change to the entry would edit each of them and nothing would fail on one it missed.

The next version, *the isekai command*, changes that entry. It is one edit only once the entry is one constant, and it is safe only once a test fails on a site that spells it by hand.

## What Changes

- `isekai/foundation/command.py` is new: `ENTRY`, the words every printed command starts with, and `command(verb, *words)`, which joins them by one space and quotes none. `run.py` re-exports `ENTRY` and `command`.
- `stage_command`, `migrate_command`, review's `_draft_command`, the CLI's `_named_a_flow` and the parser's `prog` are built from it, each word and each quote as it was.
- The sites that spelt the entry by hand call `command`: the refusals and messages of `edit.py`, `review.py`, `generate.py`, `comfy/client.py`, `compare_view.py`, `ui/surface.py`, `verbs/prepare.py`, `verbs/common.py`, `verbs/edits.py`, `render.py` and `ui/routes/rendering.py`. A site that printed `uv run` keeps it.
- A guard in `tests/test_run_directory.py` holds that no string of `isekai/` outside `command.py` spells the entry, with its twin; cases for `command` are written before it.
- A mutation run over `stage_command` and `migrate_command` passes before a line moves, and over `command` after.
- D75 is added, and [D62](../../../docs/decisions.md#d62--the-run-directory-is-runpy-its-siblings-imported-through-it)'s list of siblings gains `command.py`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Behaviour is unchanged, and the change carries `skip_specs`.

## Impact

- `isekai/foundation/command.py` and `isekai/foundation/run.py`.
- `isekai/pipeline/edit.py`, `isekai/pipeline/review.py`, `isekai/pipeline/generate.py`, `isekai/boundary/comfy/client.py`.
- `isekai/interface/cli.py`, `isekai/interface/compare_view.py`, `isekai/interface/render.py`, `isekai/interface/ui/surface.py`, `isekai/interface/ui/routes/rendering.py`, `isekai/interface/verbs/prepare.py`, `isekai/interface/verbs/common.py`, `isekai/interface/verbs/edits.py`.
- `tests/test_run_directory.py` and, for a find an edit moves, `tests/mutants.json`; no existing test's assertion changes and the recorded wire stays as it is.
- `docs/decisions.md`, `isekai/foundation/README.md`.
- The import graph `python -m isekai` loads is unchanged: `command.py` imports nothing.

## Not in this change

- A refusal's fix as a field of the refusal: nothing reads a fix apart until it rides the wire, which a patch may not add.
- The `isekai ui` texts of `isekai/interface/ui/library.py` and `isekai/interface/ui/bundle.py`: they print another prefix, and *the isekai command* makes that spelling true.
- The argv of `again` in `isekai/interface/render.py` and the children's argv of `isekai/interface/ui/jobs.py`: they are lists, not text a person pastes, and no site prints them as a string.
- The provisioning commands `uv run python -m isekai.boundary.provision` and `unpack`: they name another module.
- Any printed byte, the entry itself, and a new verb.
- Any file under `ui/`, `tools/` or `evaluation/`.
