---
version: v0.55
---

# 0082 — the collection

A library folder is a **collection** — photographs gathered with a logic behind them. A **batch** is what one run of
a verb or one render session processes. Every word, URL, flag and identifier that calls a library folder a batch says
collection; nothing on disk moves.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the two senses, what is renamed and what is not |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` · `import` · `cli` · `evaluation` · `pod-image` |

```
Library ─▶ collection   a folder holding sources/ and runs/         /c/<collection>/…   import --collection
verb, session ─▶ batch  what one invocation or render processes      unchanged
```

## Why

**One word names two things.** The Library's folders and the set a verb or a render processes are both a batch, and
the render that spans many folders needs the second meaning alone.

## What Changes

- **The two senses** — a folder is a collection; a processed set stays a batch ([D1](design.md#d1)).
- **The CLI and the stages** — `import --collection`, the compare and render wording, evaluation's record
  ([D2](design.md#d2)).
- **The app** — `/c/<collection>/…`, `/api/c/<collection>/…`, every payload key, identifier and word
  ([D3](design.md#d3)).
- **The docs** — D40 retitled, the README, the data flow, the design spec ([D4](design.md#d4)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - REMOVED and ADDED, renamed: *A folder in the library is a batch when it holds `sources/`* → *…a collection…*;
    *Every screen has a URL naming its batch and its run* → *…its collection…*; *Review opens a batch at its own
    address…* → *Review opens a collection…*.
  - MODIFIED, the word alone: *An approved input is read-only…*, *Both tag lists are shown…*, *A missing caption is
    shown…*, *The surface serves one library…*, *The hub shows each source's stage…*, *Sources are chosen in the file
    dialog…*, *Prepare runs what changed…*, *The page is told of a job…*, *Render is confirmed in a dialog…*, *The
    render job opens the volume…*, *The Renders view shows each source's images…*, *Conjure from this drafts…*, *A
    dialog holds the focus…*, *The running render opens in a drawer…*.
- `import`:
  - REMOVED and ADDED, renamed: *A source is cleaned before it enters a batch* → *…a collection*.
  - MODIFIED, the word alone: *Import is staged, and a commit is one move*.
- `cli`:
  - REMOVED and ADDED, renamed: *A render session writes its record into the batch…* → *…into the collection…*.
  - MODIFIED, the word alone: *A comparison page shows every run's photograph…*, *A stage verb requires the flows…*,
    *The approve verb cancels an approval with `--cancel`*.
- `evaluation`:
  - MODIFIED, the word alone: *Every render is a row*, *Every model the evaluator loads is pinned and verified*,
    *Attribute recall counts…*.
- `pod-image`:
  - MODIFIED, the word alone: *A render session's watchdog ends with it*.

## Impact

- **Code:** `isekai/interface/` (but `wiring.py`), `isekai/pipeline/importing.py`, `isekai/foundation/artifacts.py`,
  `evaluation/`, `tools/derive_field_map.py`, `ui/src/`.
- **Tests:** `tests/test_importing.py`, `tests/test_pipeline_cli.py`, `tests/test_compare.py`, `tests/test_render.py`,
  `tests/test_ui_api.py`, `tests/test_ui_library.py`, `tests/test_ui_jobs.py`, `tests/e2e/`, `ui/src/**/*.test.ts`.
- **Docs:** `README.md`, `AGENTS.md`, `docs/decisions.md`, `docs/data-flow.md`, `docs/modules.md`,
  `ui/design/spec.md`, the `README.md` of each code folder renamed in.

## Not in this change

- **A file on disk** — a collection is the folder a batch was: `sources/`, `runs/`, `log.txt`, `sessions/`.
- **The scenario keys and their headings in a block that keeps its title** — a key is an id; the spec audit tidies
  the headings.
- **The processed-set sense** — the stages, `principles.md` and the specs that mean it keep *batch*.
