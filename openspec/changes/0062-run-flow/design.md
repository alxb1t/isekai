# Design — 0062 run flow

How the browser starts a batch: import with a bar per file and a privacy check, `assign` for a tick, and Prepare as a
job the page watches. **Verdict: feasible** — cleaning reuses `strip_metadata` and Pillow; a tick is `open_run` and a
directory; Prepare is the existing verbs run as children; the event stream is plain HTTP.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `ac379cf` (`v0.37.0`):

- **The library:** `isekai/interface/ui/library.py` lists batches and reads each cell's stage; a flow's empty
  directory already reads `assigned` (`stage`, `:246-277`); the columns are every tracked flow (`_suffixes`,
  `:229-234`).
- **The server:** `app.py` answers `/api/library`, `/api/b/{batch}/hub` and the review routes, and `index.html` for any
  other path (`isekai/interface/ui/app.py:225-424`); `serve(wired, *, port)` (`isekai/interface/ui/__init__.py:29`).
- **The views:** `ui/src/views/Home.vue`, `Hub.vue`, `Review.vue`; the hub's checkbox is disabled with a state reason.
- **The seam:** `wiring_from` builds the factory `ISEKAI_WIRING` names (`isekai/interface/wiring.py:275-304`);
  `tests/e2e/wiring.py`'s `fake` doubles the reader, both taggers and Comfy (`:19-31`); `tests/e2e/conftest.py:126`
  sets it, and a child process inherits it.
- **What import reuses:** `open_run(photo, runs_root)` (`isekai/foundation/run.py:351`); `strip_metadata`, which keeps
  pixels and orientation and refuses what it cannot walk (`isekai/shared/image.py:371-392`, walkers `_strip_jpeg`
  `:395`, `_strip_png` `:449`); `photo_resolution`, render's header check (`isekai/pipeline/generate.py:394`).
- **The verbs' output:** `_say` prints `{run.id}: {verb} wrote …` or `… is already complete` to `wired.out`
  (`isekai/interface/cli.py:720-725`); `VERBS` lists the subcommands (`:76-86`).
- **Ollama:** the *nothing is listening* refusal lives inside `ask()` (`isekai/boundary/ollama.py:234-238`); there is
  no probe of its own.
- **Refusals ending *"then run this command again"***: `isekai/boundary/ollama.py:117`, `:237`, `:336`, `:344`;
  `isekai/shared/vocabulary.py:66`. No test or spec quotes the phrase.
- **`review()`** starts a new draft from the last approval, as its docstring states (`isekai/pipeline/review.py:124-131`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_ui_library.py` | 12 | `grep -c "def test_" tests/test_ui_library.py` |
| tests in `tests/test_ui_api.py` | 44 | `grep -c "def test_" tests/test_ui_api.py` |
| tests under `tests/e2e/` | 8 | `grep -c "def test_" tests/e2e/test_*.py \| awk -F: '{s+=$2} END {print s}'` |

## Goals / Non-Goals

**Goals:** a batch made, cleaned and prepared from the browser; no metadata in `sources/`; a page that shows a job as
it runs; every new behaviour tested on doubles.

**Non-Goals:** render, Renders, ④ Renders, revise; drag-and-drop; checking a batch moved in from `.data/`; `control`
in the UI; tags shared across flows.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `isekai/pipeline/importing.py` — `read`, `verify`, `commit`, `cancel`, `sweep`; called in process by the server; the verb `isekai import --batch <dir> <file…>` composes them | reading files is not a job; one module owns writing a source | the server running the verb as a child |
| [D2](#d2) | cleaning: JPEG/PNG in sRGB or none → `strip_metadata`; another profile → sRGB, re-encode at 95; other formats → JPEG 95, PNG with transparency; orientation applied on conversion | no metadata in a source; colour kept true | byte-for-byte copies; dropping a profile unconverted |
| [D3](#d3) | `verify` after `read`; on failure one re-encode from pixels, then verify; still failing → `not cleaned`, left out unless chosen; `commit` verifies again | the check is the import's own | trusting the reader |
| [D4](#d4) | `isekai assign --flow F … --runs <runs> <source…> [--remove]`: `open_run` and an empty flow directory; `--remove` only on an empty one | a tick is the layout's own fact | a state file of ticks |
| [D5](#d5) | `config/ui.json` — `flows` the UI offers, `upload_limit_mb` | `control` stays the CLI's; a limit is configuration | a flag on a flow's manifest |
| [D6](#d6) | `--progress json` on `tag`, `caption`, `sheet`: JSON lines on stdout, human lines on stderr | the page reads a format meant for it | parsing human lines or `log.txt` |
| [D7](#d7) | `isekai/interface/ui/jobs.py`: one slot; Prepare runs, per flow, `tag`, `caption`, `sheet` as children over that flow's cells; a probe first; Stop and server stop send SIGINT | the CLI is the one path; a job outlives its tab | stages called in process |
| [D8](#d8) | `GET /events[?batch=]` — Server-Sent Events: a snapshot, then a change per progress line | one-way push on plain HTTP | a WebSocket; polling |
| [D9](#d9) | the staging API and the sheet: raw `PUT` per file by `XMLHttpRequest`, a bar each | upload progress per file; no multipart dependency | `fetch()`; a form post |
| [D10](#d10) | the hub ticks through `POST /api/b/{batch}/assign`; the Prepare bar; cells live from `/events` | the design's J2 | ticks held in the page |
| [D11](#d11) | the refusals end *"then try again"*; D4, D42, D43 in `docs/decisions.md` | the page shows a refusal verbatim; a decision lives where it is in force | rewording on the page |

### D1

```
read(file, staging)  ──▶ staging/<name>        decode · clean · verify · re-encode once
verify(path)         ──▶ what it still carries, or nothing
commit(staging, library, name, as_is)  ──▶ <library>/<name>/sources/ in one rename; staging deleted
cancel(staging) · sweep(library)  ──▶ staging deleted; every .staging/<id>/ deleted at start
```

`read` refuses per file, by name: over the limit, RAW (by signature: CR2, NEF, DNG, ARW), not decodable, more than one
frame, and what `photo_resolution` refuses. A same-bytes source is skipped; a taken name becomes `<stem>-2`. The batch
name is checked as the [import spec](specs/import/spec.md) says. `isekai import --batch <dir> <file…>` reads into the
batch's own staging, commits, and reports each file; it imports no uncleaned file.

### D2

Pillow opens every format; `pi_heif.register_heif_opener()` adds HEIC, called inside `read` so the entry point's import
graph is unchanged (D20). A profile is read from `image.info["icc_profile"]`; a non-sRGB one goes through
`PIL.ImageCms.profileToProfile` to sRGB. `ImageOps.exif_transpose` applies orientation on every conversion. A file
that stays JPEG or PNG keeps its pixels byte for byte through `strip_metadata`.

### D3

`verify` walks the file with the same walkers `strip_metadata` uses and lists every block it keeps beyond pixel data
and orientation — EXIF beyond orientation, XMP, IPTC, a profile, bytes after the end — then decodes it and runs
`photo_resolution`. An empty list passes. `commit` runs `verify` over every staged file again and refuses the commit
when one fails that was not chosen *as is*.

### D4

`assign` is a verb in `VERBS`; it takes `--flow` like a stage verb and is not one — it calls no model. For each source
it calls `open_run(source, runs)` and creates `run.directory(flow)`; with `--remove` it deletes that directory if empty
and refuses otherwise. The hub's `POST /api/b/{batch}/assign` runs the same function in process.

### D5

```json
{ "flows": ["summon-anime-wai", "conjure-anime-wai"], "upload_limit_mb": 200 }
```

`library._suffixes` takes the offered flows, each still checked as tracked; a name that is not tracked is refused at
start. `tests/test_ui_library.py` reads its own copy.

### D6

`_say` and the stage loops emit through one reporter: human lines to `wired.out` without the flag; with it, JSON lines
to `wired.out` and human lines to `wired.err`. Each item reports `start`, then `done` or `refused`.

### D7

```
Prepare ─▶ probe ─ no answer ─▶ refused, nothing runs
            └ answers ─▶ for each flow with assigned cells:
                          isekai tag     --flow F --runs R --progress json <runs…>
                          isekai caption --flow F --runs R --progress json <runs…>
                          isekai sheet   --flow F --runs R --progress json <runs…>
```

The probe is a `Wiring` field, `probe`, defaulting to `ollama.probe()` — a `GET /api/version` raising the same refusal
`ask()` raises — so the doubles answer it in tests. A child's stderr is appended to `<batch>/log.txt`; its stdout is
read line by line into the job's state. Stop sends the current child SIGINT; the job then ends.

### D8

`/events` streams `text/event-stream`: on connect, one `snapshot` event (the job slot; with `?batch`, that batch's hub);
then a `cell` event per progress line, carrying the cell's stage re-read from disk, and a `job` event on each change of
the slot. Home connects without `?batch`.

### D9

```
POST   /api/staging                         → {id}
PUT    /api/staging/{id}/files/{name}       body: the file      → the file's result
DELETE /api/staging/{id}                    → cancel
POST   /api/staging/{id}/commit             {batch, as_is: [names]} → the hub's URL
```

`ui/src/components/ImportSheet.vue` sends each file with `XMLHttpRequest`, its `upload.onprogress` driving the tile's
bar. New batch on Home and Add sources on the hub open it; Add sources commits into the open batch.

### D10

A tick or an untick posts to `/api/b/{batch}/assign`; the cell reads `assigned` from the answer. Assigned cells with no
sheet feed the bar, `n changes · Prepare ⌘↵`, and `Discard` unticks them all. `Hub.vue` opens `/events?batch=` and
applies each `cell` event. A source still carrying metadata — `verify` on its file — shows `⚠ not cleaned`.

### D11

Each listed refusal's *"then run this command again"* → *"then try again"*. In `docs/decisions.md`: D4 → *the UI runs
stages only as the CLI's children; nothing in it spends money*; added **D42 · A new draft starts from the last
approval** and **D43 · A source holds pixels and orientation only**.

## Tests

| layer | added | removed | where |
|---|---|---|---|
| unit, pytest | every `unit` scenario of the [import](specs/import/spec.md), [cli](specs/cli/spec.md) and [ui](specs/ui/spec.md) deltas | none | `tests/test_importing.py`, `tests/test_assign.py`, `tests/test_progress.py`, `tests/test_ui_jobs.py`, `tests/test_ui_library.py`, `tests/test_ui_api.py` |
| e2e, Playwright | `ui:sheet:*`, `ui:hub:a-tick-assigns-the-flow`, `ui:prepare:prepare-runs-the-assigned-cells` | none | `tests/e2e/test_import.py`, `tests/e2e/test_prepare.py` |

**Fixtures:** a HEIC made once with macOS `sips` from a synthetic solid-colour PNG, committed as
`tests/fixtures/sources/plain.heic`; the other formats are built by Pillow in the tests.

**End-to-end runs added:** the e2e scenarios above, each once, on Chromium. Each needs a browser (T1): a file dialog
and its bars, a tick surviving a reload, cells moving live. The import scenarios share one test file's server; the
Prepare scenario extends the tick's test (T2).

## Dependencies

| package | where | constraint | why |
|---|---|---|---|
| `pi-heif` | `pyproject.toml` `dependencies` | `==1.4.0` | HEIC decode ([D2](#d2)); wheels LGPLv3, decode only — `pillow-heif`'s are GPLv2 for the bundled x265 encoder |

## Risks / Trade-offs

- **[Risk]** a re-encode loses quality → only a non-sRGB profile or a file that failed `verify` is re-encoded, at 95.
- **[Risk]** an `XMP` or `IPTC` block the walkers do not know → `_strip_jpeg` already refuses an unknown marker;
  `verify` lists it, and re-encoding drops it.
- **[Risk]** a job's child outlives a crashed server → children start in their own session and the server's stop
  signals them; an orphan is the CLI's own process and writes atomically.
- **[Trade-off]** a re-added HEIC after a Pillow upgrade may encode to new bytes and arrive as a second source.

## Verdict

**Feasible.** Each piece reuses what the pipeline has: the strip, the header check, `open_run`, the verbs; the new
parts are the conversion, the job runner, the stream and two screens.
