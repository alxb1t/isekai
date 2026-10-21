# `interface/ui/` — the app

The library, each batch's hub and Review, served on the loopback address by `isekai ui`. Its files and
who imports them are [`interface/README.md`](../README.md)'s table; this page says what the app does
with them.

```
Home ─ New batch ─▶ import sheet ─▶ <batch>/sources/
hub ─ tick ─▶ assign ─▶ Prepare ─▶ tag → caption → sheet ─▶ /events ─▶ the cells
hub ─ Review next ─▶ Review ─▶ approve
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
- **`/events`** (`events.py`) streams a snapshot of the job slot and the batch's hub on every connect,
  then a `cell` event per progress line, the cell's stage read again from disk.

The columns are the flows `config/ui.json` offers. Nothing here spends money
([D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children)).
