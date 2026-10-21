---
version: v0.38
---

# 0062 — run flow

A batch starts in the browser. Photographs chosen in the file dialog upload with a bar each, are cleaned of every
byte a picture does not need, verified, and committed into the library. Flows are ticked per source on the hub, and
*Prepare* runs tag → caption → sheet over what changed, with its progress shown live.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | import and cleaning, `assign`, the job, the event stream, the sheet and the hub |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `import` (new) · `cli` · `ui` |

```
New batch ─▶ file dialog ─▶ upload (a bar each) ─▶ read · clean · verify ─▶ Import ─▶ <batch>/sources/
hub ─▶ tick a flow ─▶ isekai assign ─▶ "3 changes · Prepare" ─▶ tag → caption → sheet ─▶ /events ─▶ cells
```

## Why

**The UI cannot start a batch.** A batch is made by hand in Finder, its runs by the CLI; the hub only reads.

**A photograph carries more than its pixels.** A JPEG keeps its EXIF — location, camera, time — and today a source
and every run's copy keep it; only the upload to the pod strips it. A library of personal photographs should hold
none of it.

**A job needs its progress.** Prepare runs for minutes over Ollama; without a live channel the page shows nothing
until it ends.

## What Changes

- **Import** — a new pipeline module and the verb `isekai import`: read, convert, strip, verify, commit; HEIC
  through `pi-heif` ([D1](design.md#d1), [D2](design.md#d2), [D3](design.md#d3)).
- **`sources/` holds only cleaned images**: no metadata but orientation, colour in sRGB ([D2](design.md#d2)).
- **`isekai assign`** — a tick written as a run and an empty flow directory ([D4](design.md#d4)).
- **The flows the UI offers** come from `config/ui.json` ([D5](design.md#d5)).
- **`--progress json`** on `tag`, `caption` and `sheet` ([D6](design.md#d6)).
- **Prepare as a job**: one slot, CLI children, an Ollama check first, Stop ([D7](design.md#d7)).
- **`/events`** — Server-Sent Events: a snapshot, then changes ([D8](design.md#d8)).
- **The sheet and the hub**: uploads with a bar each, `⚠ not cleaned`, ticking, the Prepare bar, live cells
  ([D9](design.md#d9), [D10](design.md#d10)).
- **Refusals end *"then try again"*** in place of *"then run this command again"* ([D11](design.md#d11)).

## Capabilities

### New Capabilities

- `import`: how a file becomes a source — read, cleaned, verified, and committed into a batch.
  - ADDED *A source is cleaned before it enters a batch*.
  - ADDED *A file that cannot be a source is refused by name*.
  - ADDED *Every source is verified before it is committed, and one that cannot be cleaned is left out unless chosen*.
  - ADDED *Import is staged, and a commit is one move*.

### Modified Capabilities

- `cli`:
  - MODIFIED *A stage verb requires the flows it acts on, and takes more than one* — the serving verb serves the
    flows its configuration offers.
  - ADDED *Assigning a flow writes its run and the flow's empty directory, and nothing else*.
  - ADDED *A stage verb reports its progress as JSON lines when asked*.
- `ui`:
  - MODIFIED *A folder in the library is a batch when it holds `sources/`* — a row counts the flows the UI offers.
  - REMOVED *The hub shows each source's stage in each tracked flow, read from the run directory*, and
  - ADDED *The hub shows each source's stage in each offered flow, and a tick assigns it* — the offered flows, and a
    tick that writes through `assign`.
  - ADDED *Sources are chosen in the file dialog, and each shows its own upload*.
  - ADDED *Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer*.
  - ADDED *The page is told of a job as it runs*.

## Impact

- **Code:** new `isekai/pipeline/importing.py`, `isekai/interface/ui/jobs.py`, `isekai/interface/ui/events.py`;
  `isekai/interface/cli.py` (`import`, `assign`, `--progress`); `isekai/interface/ui/app.py`, `library.py`;
  `isekai/boundary/ollama.py` (a probe); `isekai/shared/vocabulary.py`; `ui/src/`; `config/ui.json`.
- **Dependency:** `pi-heif` ([Dependencies](design.md#dependencies)).
- **Docs:** `docs/decisions.md` (D4; new D42, D43), `docs/data-flow.md`, `docs/modules.md`, `README.md`,
  `ui/design/spec.md` is unchanged.

## Not in this change

- **Render, the Renders view, ④ Renders, billing alerts** — render's.
- **Revise and compare** — revise's.
- **Drag-and-drop onto the page** — parked until choosing files from the dialog is slow.
- **A check on a batch moved in from `.data/`** — parked; moving one is the operator's act.
- **`control-anime-wai` in the UI** — it is approved from summon, in the CLI.
- **Tags or a caption shared across flows** — each flow writes its own.
