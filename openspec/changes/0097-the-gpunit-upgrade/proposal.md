---
bump: minor
backlog: [0074·R6]
---

# 0097 — the gpunit upgrade

gpunit re-pinned from `v0.7.0` to `v0.12.0`: a window volume that vanished is remade by gpunit's own `volume up`, and
the drawer and `isekai render` say which kind of refusal gpunit made, quoting its reason.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, and the tests |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui`, `cli`, `pod-image` |

```
1 the pin      pyproject.toml + uv.lock at v0.12.0 · the boot script's tag untied · docs/pins.md · Volume's exits
2 the lines    run_gpunit hands each line to say as it comes (0074·R6)
3 the reason   run_gpunit returns the exit and the last refused line · the drawer's message by kind ·
               isekai render exits gpunit's code · D36
```

## Why

**gpunit `v0.7.0` refuses a window volume the provider has deleted, and reads every refusal as exit 1.** `v0.12.0`'s
`volume up` remakes a vanished volume, and its exits tell no card in stock (4) from no card that fits (5). Today the
drawer says only "did not open the window (exit 1)", and gpunit's lines reach `log.txt` only once its verb exits.

## What Changes

- **The pin** moves to `v0.12.0`; the image's boot script keeps `v0.7.0`'s `boot.sh`, its tag pinned on its own, so
  nothing is rebuilt ([D1](design.md#d1), [D2](design.md#d2)).
- **gpunit's lines** reach the log as gpunit writes them ([D4](design.md#d4)).
- **A refusal for stock or fit** leads the drawer's message with its kind, then quotes gpunit's `refused:` line and
  names the log; `isekai render` exits gpunit's code and prints the same kind ([D5](design.md#d5)–[D8](design.md#d8)).
- **D36** gains a bullet on gpunit's exit and line ([D9](design.md#d9)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — *The render job opens the volume, renders, and closes the volume unless kept*: a refusal for stock or fit
  names its kind, gpunit's reason and the log.
- `cli` — *A render session writes its record into the collection, from its start to its end*: a refused session
  exits with gpunit's code.
- `pod-image` — *A pod makes its own host key and prints its fingerprint*: the boot script comes from a pinned gpunit
  tag, no longer the tag `pyproject.toml` pins.

## Impact

- `pyproject.toml`, `uv.lock`.
- `isekai/`: `boundary/gpu.py`, `interface/render.py`, `interface/ui/jobs.py`.
- `tests/`: `test_infra.py`, `test_gpu.py` (new), `test_ui_jobs.py`, `test_render.py`, `test_ui_billing.py`,
  `test_ui.py`, `stages.py`, `e2e/wiring.py`.
- `docs/pins.md`, `docs/decisions.md`.
- No image rebuild: `Dockerfile`, `config/image.json` and `gpunit.toml` are untouched.

## Not in this change

- `stock_wait`: a wait between the quote and the pod stretches the quoted window; it needs its own grilling.
- `boot.py`, the `Dockerfile` and any rebuild: the split-image version's, which re-ties the boot tag to the pin.
- The CLI's live but gone volume: `session()` refuses with "run gpunit volume up", and `REMEDY` already adds the `.env`
  note to it.
- A pod proof of `v0.12.0` on this boot script: the person renders by hand after release.
