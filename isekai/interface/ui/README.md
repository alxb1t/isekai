# `interface/ui/` — the app

The library, each batch's hub and Review, served on the loopback address by `isekai ui`. Its files and
who imports them are [`interface/README.md`](../README.md)'s table; this page says what the app does
with them.

```
Home ─ New batch ─▶ import sheet ─▶ <batch>/sources/
hub ─ tick ─▶ assign ─▶ Prepare ─▶ tag → caption → sheet ─▶ /events ─▶ the cells
hub ─ Review next ─▶ Review ─▶ approve
hub ─ Render ─▶ quote ─▶ confirm ─▶ volume up ─▶ render ─▶ volume down ─▶ /events ─▶ the session
```

- **Import.** The sheet sends each chosen file in its own `PUT`, a bar each. The server reads it into
  the library's `.staging/` through `pipeline/importing.py`, which cleans it to its pixels and
  orientation and verifies it; Import commits the batch's `sources/` in one move. A staging folder left
  behind is swept when the server starts.
- **A tick** is `POST /api/b/{batch}/assign`, the same `assign` `isekai assign` runs: a flow's empty
  directory in the source's run. An untick past assigned is refused, so a tick never deletes work.
- **Prepare** is one job in one slot (`jobs.py`). It asks Ollama first, then runs `isekai tag`,
  `caption` and `sheet` per flow as children, each with `--progress json`, their prose appended to the
  batch's `log.txt`. Stop, and the server stopping, send the child SIGINT.
- **Render** is the slot's other job. `POST …/render/quote` takes the render verb's own quote: per flow
  what renders, what is left out and why, the estimate, the limit and the price at most. Only
  `POST …/render` rents: `gpunit volume up --yes`, then `isekai render --limit … --progress json`,
  then `volume down` unless the window is kept.
- **Renders** reads each source's approvals newest first with their images; the large view shows an
  image beside the approval's filled fields. A thumbnail is made once, into the library's `.cache/`.
- **Billing** (`billing.py`) is read from gpunit's records in `.gpunit/`: a pod alert, the window's quiet
  item, or the band. gpunit is asked at start, every half minute while a session runs or an alert is
  open, and on Check again.
- **`/events`** (`events.py`) streams a snapshot of the job slot, billing and the batch's hub on every
  connect, then a `cell` event per progress line, the cell's stage read again from disk.

The columns are the flows `config/ui.json` offers. The render's confirmation is the one act that
spends money, and only as the CLI's own verb
([D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children)).
