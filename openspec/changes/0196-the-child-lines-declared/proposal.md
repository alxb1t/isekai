---
bump: patch
after: [0195-the-child-lines-pinned]
---

# The child lines declared

One module, `isekai/interface/progress.py`, declares the JSON lines a child prints and the flag that asks for them; what emits a line and what reads one use it. Every line stays byte-equal.

Reading map: [design](design.md) holds the decisions and the names the module declares, [tasks](tasks.md) its phases: the module, the emitters, the readers, then the decision and the docs.

## Why

A child's item line is spelled in `Reporter.item` and its stages and states at each verb; the session's step and image lines are spelled in `Steps`; and `jobs.py` and `_Images` spell the same keys and words again to read them. `--progress json` is written out again in each verb's argument, the session's argv and each command the app builds. The version before pins every line as bytes, so the declaration can move the code and prove nothing printed changed.

## What Changes

- `isekai/interface/progress.py` is new, standard library only. It holds the shapes of the item line and the session's step and image lines, the stage, state and step names, `--progress json` as one flag, `emit`, `progress_line`, `Steps` and `_Images`.
- `Steps`, `_Images` and `progress_line` leave `isekai/interface/render.py` and are bound back there, so no test import changes.
- `Reporter.item` and `Steps` write through `emit`. The verbs name their stage and state by the declared names.
- `jobs.py` reads the names from the module, and `PREPARE` moves there.
- `docs/decisions.md` gains one decision, and the interface READMEs list the module.

No requirement is touched, and `ui/src/wire.ts` stays byte-identical.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

`isekai/interface/render.py`, `isekai/interface/verbs/common.py`, `isekai/interface/verbs/runner.py`, `isekai/interface/verbs/prepare.py`, `isekai/interface/verbs/generate.py`, `isekai/interface/verbs/edits.py`, `isekai/interface/verbs/session.py` and `isekai/interface/ui/jobs.py` read the new module. `docs/decisions.md`, `docs/modules.md`, `isekai/README.md` and `isekai/interface/README.md` name the module. `tests/test_progress.py` gains cases; no existing test's assertion changes.

## Not in this change

- A line's text, key order or flush: the version before pins them, and this one changes none.
- `ui/src/wire.ts`, `isekai/interface/ui/shapes.py` and the `cell` event: `shapes.py` does not name the line's type, so the wire's deriver sees nothing new.
- The `steps.step(...)` call sites in `render.py`: `tests/mutants.json` finds them by text.
- `Record`, `Records` and `quote`: they stay in `render.py`.
- A record file for the lines, and any file under `tests/record/`, `ui/`, `tools/` or `evaluation/`.
- A scenario or a spec delta.
