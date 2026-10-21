# Design — 0064 the import sheet

How a tile shows its conversion and its preview, and Home its first start in order. **Verdict: feasible** — the
stream, the thumbnail and the reader exist; the upload stops waiting for the read.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `f76c6dc` (`v0.39.0`):

- **The upload reads in its own request**: `put_file` awaits the body, then `importing.receive` in a thread pool, and
  answers with the file's state (`isekai/interface/ui/app.py:344-364`); `receive` and `read` are
  `isekai/pipeline/importing.py:152` and `:112`.
- **The stream:** `GET /events` (`app.py:508`) sends a snapshot, then changes, for the job slot and a batch's hub.
- **Thumbnails:** `library.thumbnail(root, run, image)` serves renders and sources (`app.py:762-768`).
- **The sheet:** `ui/src/components/ImportSheet.vue` sends each file with `XMLHttpRequest`, `upload.onprogress`
  driving its bar (`:25-36`); a tile shows no image.
- **Home:** *New batch* (`ui/src/views/Home.vue:76`) renders above *No batches yet.* (`:82`) and the privacy line (`:84`).
- **The cards:** 0061·R15 — the approval's precondition is proved by a step in the test bound to
  `ui:draft-update:a-stale-precondition-is-refused` (`tests/test_ui_api.py:575`); 0061·R17 — the module docstring
  counts "the four `ui` scenarios" and "gate command five" (`tests/test_ui_api.py:7`, `:13`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_ui_api.py` | 50 | `grep -c "def test_" tests/test_ui_api.py` |
| tests in `tests/e2e/test_import.py` | 3 | `grep -c "def test_" tests/e2e/test_import.py` |

## Goals / Non-Goals

**Goals:** a tile that shows every step of its file and its picture; Home's first start in order; the triggered cards
closed. **Non-Goals:** a requirement added, a format moved, the product changed — this is a patch.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `put_file` holds the body in a dot-named folder inside the staging folder and answers `202 {"state": "waiting"}`; one reader thread per staging folder, `importing`'s own, reads files in the order their bytes landed, publishing each state on `/events?staging=<id>` | the conversion reports itself; a batch of HEICs does not load every core; `commit` and `read` own the folder's undotted names | a read per request; a pool; the upload beside the staged files |
| [D2](#d2) | a tile: `uploading n%` → `waiting` → `converting…` (indeterminate) → ready, refused or `⚠ not cleaned`; Import disabled while any tile uploads, waits or converts | the design's J1·3, J1·4 | a combined bar |
| [D3](#d3) | `GET /api/staging/{id}/files/{name}/thumb` — a downscaled JPEG of the staged file, made on request, never cached | a staging preview lives and dies with its folder | `.cache/` |
| [D4](#d4) | Home's first start: *No batches yet.*, the privacy line, then *New batch*; with a batch, *New batch* stays above the list | the design's J1·1, J7·1 | |
| [D5](#d5) | 0061·R15: the approval's step becomes its own test, bound to `ui:draft-update:a-stale-approval-is-refused`; 0061·R17: the docstring names what is proved and the gate's pytest command | the cards' own fixes | |

### D1

```
PUT bytes ──▶ staging/<id>/.upload-<token>/<name> ─▶ 202 waiting ─▶ queue
reader:  queue ─▶ converting ─▶ importing.read ─▶ ready · refused · not cleaned ─▶ /events?staging=<id>
```

The reader is started with the staging folder and stopped by its cancel, its commit or the surface's stop. `commit`
refuses while any file waits or converts. The stream's snapshot carries every file's state, so a page that connects
late misses none.

## Tests

| layer | added | removed | where |
|---|---|---|---|
| unit | `ui:sheet:an-upload-is-answered-before-reading`; `ui:sheet:the-stream-reports-each-files-reading`; `ui:sheet:a-staged-file-serves-its-preview`; `ui:draft-update:a-stale-approval-is-refused` | none | `tests/test_ui_api.py` |
| e2e | steps, not tests: a tile converting, then showing its preview, in the test bound to `ui:sheet:each-file-shows-its-progress`; Home's first-start order in the same file's first test | none | `tests/e2e/test_import.py` |

**End-to-end runs added:** none. The states and the preview are the server's, so each new scenario is a unit test
(T1); the tile drawing them is a step in an existing browser test, under that test's key (T2). The approval step moves
out of the stale-precondition test into its own; that test keeps its assertions and its key.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a reader thread outlives a cancelled import → the cancel stops it before deleting the folder.
- **[Trade-off]** one file at a time is slower than a pool for many small JPEGs → they only strip, in milliseconds.

## Verdict

**Feasible.** Each piece exists; the patch reorders when the read happens and shows what it already knows.
