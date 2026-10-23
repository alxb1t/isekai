---
version: v0.40.1
backlog: [0063·R24, 0063·R25, 0063·R26, 0063·R27, 0063·R28, 0064·R7, 0064·R8, 0065·R16, 0065·R18]
---

# The quick patch

Restore Prepare's totals and orderly shutdown; correct count labels, hub spacing and stale claims.
Read the [decisions and evidence](design.md), [UI delta](specs/ui/spec.md) and [build tasks](tasks.md).

## Why

Stopping the surface with event streams open prints cancellation errors, and a failed window close can leave no terminal remedy.
Prepare shows stage names instead of its designed totals; count grammar, header spacing and current documentation need repair.

## What Changes

- **A folder in the library is a batch when it holds `sources/`** — clarify count-label grammar; cover singular and plural labels.
- **The hub shows each source's stage in each offered flow, and a tick assigns it** — state the header's control gap.
- **Sources are chosen in the file dialog, and each shows its own upload** — remove the redundant preview clause; retain its scenario and tests, per [D1](design.md#d1).
- **Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer** — cover visible cell totals and elapsed time.
- **The page is told of a job as it runs** — cover progress in reconnect snapshots and streams ending before shutdown's grace period expires.
- **Render is confirmed in a dialog that quotes what renders, its limit and its price at most** — correct its why to the existing total/limit boundary, per [D2](design.md#d2).
- **The render job opens the volume, renders, and closes the volume unless kept** — base terminal recovery on close state, including a failed close within the wait.
- Correct the UI package's child-process docstring and the Known breaks in `docs/principles.md`; clarify Render's boundary in `docs/decisions.md`.
- Carry the historical route and Impact errata in [the disposition table](design.md#historical-errata), preserving frozen archives.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: display and shutdown repairs, progress scenarios and prose clarifications under existing requirements.

## Impact

- **Server:** `isekai/interface/ui/__init__.py`, `app.py`, `events.py`, `jobs.py`.
- **Browser:** `ui/src/App.vue`, `types.ts`, `app.css`, `composables/useLive.ts`, `views/Home.vue`, `views/Hub.vue`,
  `components/AppHeader.vue`, `ImportSheet.vue`, `RenderDialog.vue`, `SheetHeader.vue`; new `ui/src/words.ts` and its test.
- **Tests:** `tests/test_ui.py`, `tests/test_ui_jobs.py`, `tests/e2e/test_prepare.py`, `tests/e2e/conftest.py`,
  `tests/e2e/wiring.py`; extend existing browser tests rather than adding page setups.
- **Documentation:** `docs/principles.md`, `docs/decisions.md`, `ui/design/spec.md`.
- **State:** additive in-memory job metadata; no run-file kind, format version, dependency, endpoint or paid work added.

## Not in this change

Pinia, a key registry, source thumbnails, dimensions, Review navigation/layout, animated progress, Sessions and another job slot.
Exact source/approval identity confirmation, architectural extraction, archive edits, retroactive tags and changed model output are excluded.
