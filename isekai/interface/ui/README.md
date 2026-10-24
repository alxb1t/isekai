# `interface/ui/` — the app

The library, each batch's hub and Review, served on the loopback address by `isekai ui`. Its files and
who imports them are [`interface/README.md`](../README.md)'s table; this page says what the app does
with them.

```
Home ─ New batch ─▶ import sheet ─▶ <batch>/sources/
hub ─ tick ─▶ assign ─▶ Prepare ─▶ tag → caption → sheet ─▶ /events ─▶ the cells
Review ─▶ /b/<batch>/review ─▶ the head ─▶ Review ─▶ approve
hub ─ Render ─▶ quote ─▶ confirm ─▶ volume up ─▶ render ─▶ volume down ─▶ /events ─▶ the session
render ─▶ <batch>/sessions/<id>.json ─▶ /b/<batch>/sessions ─▶ /b/<batch>/sessions/<id>
```

- **Import.** The sheet sends each chosen file in its own `PUT`, a bar each, answered once its bytes
  land. The import's reader in `pipeline/importing.py` then reads the files into the library's
  `.staging/` one at a time, cleaning each to its pixels and orientation and verifying it, and
  the page's stream, naming the import, reports each tile's step; a read tile shows its preview. Each upload
  keeps its own state under the upload id its `PUT` answers, so two files of one name are two tiles. Import
  seals the reader, so no upload lands once it commits the batch's `sources/` in one move. A staging
  folder left behind is swept when the server starts.
- **A tick** is `POST /api/b/{batch}/assign`, the same `assign` `isekai assign` runs: a flow's empty
  directory in the source's run. An untick past assigned is refused, so a tick never deletes work.
- **Prepare** is one job in one slot (`jobs.py`). It asks Ollama first, then runs `isekai tag`,
  `caption` and `sheet` per flow as children, each with `--progress json`, their prose appended to the
  batch's `log.txt`. Stop, and the server stopping, send the child SIGINT.
- **Render** is the slot's other job. `POST …/render/quote` takes the render verb's own quote: per flow
  what renders, what is left out and why, the estimate, the limit and the price at most. Only
  `POST …/render` rents: `gpunit volume up --yes`, then `isekai render --limit … --session <id> --progress
  json`, then `volume down` unless the window is kept.
- **Sessions** are read from the records the render verb writes, `<batch>/sessions/<id>.json`:
  `GET …/sessions` lists them, the running one first, and `GET …/sessions/<id>` serves one. The job slot adds
  the volume steps and Stop. `GET /api/sessions/running` reads process-held liveness locks across the library,
  each before its record, so a damaged record refuses only its own batch's list; local polling refreshes observed
  records and lists every two seconds, so terminal renders show on every screen too. A failed poll marks the last
  answer unconfirmed on every screen, and an unconfirmed render never hides the billing alert.
  The alert's way out is `/billing`, which distinguishes unknown billing, an open volume and confirmed absence.
- **Renders** reads each cell's images, versions oldest to newest, with how many its newest approval still lacks,
  the render stage's own count; Render comes from its bar, as on the hub. The large view shows an image
  beside the approval's filled fields. A thumbnail, a render's or a source's, is made once, into the
  library's `.cache/`.
- **Billing** (`billing.py`) is read from gpunit's records in `.gpunit/`: a pod alert, the window's quiet
  item, or the band. gpunit is asked at start, every half minute while a session runs or an alert is
  open, and on Check again.
- **`/events`** (`events.py`) streams a snapshot of the job slot, billing, the batch's hub and the import's
  files on every connect, then a `cell` event per progress line, the cell's stage read again from disk. A page
  holds one stream, naming its batch and its open import, and it opens again when either changes. A batch or
  an import it cannot read is left out of the snapshot, so the stream still opens.

The columns are the flows `config/ui.json` offers. The render's confirmation is the one act that
spends money, and only as the CLI's own verb
([D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children)).
