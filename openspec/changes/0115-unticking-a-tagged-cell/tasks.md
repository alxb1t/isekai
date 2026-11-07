# Tasks — 0115 unticking a tagged cell

The untick and its tests, then the prose, per [design](design.md). Paths are from the repository root.

## Progress

- [x] 1 — The untick
- [ ] 2 — The prose

## 1 — The untick

- [x] 1.1 **HALT CHECK** — Discard takes only a cell reading *assigned*, as [Context](design.md#context) says.
  Verify: `grep -n -F "cell(one, flow).stage === 'assigned'" ui/src/views/Hub.vue` prints one line.
- [x] 1.2 In `ui/src/cells.ts`, make `action` return `tick` for `tagged`, per [D1](design.md#d1), and add
  `export function pending(cell: HubCell): boolean` and `export function locked(cell: HubCell): boolean` after it, per
  [D2](design.md#d2) and its table. Verify: `grep -n 'export function locked(cell: HubCell): boolean' ui/src/cells.ts` prints one line.
- [x] 1.3 In `ui/src/views/Hub.vue`, delete its own `pending` and `locked` with their comment, import both from
  `../cells`, and make `discard` filter on `pending`, per [D2](design.md#d2). Comments: `changes`' "every assigned cell"
  → "every pending cell"; `toggle`'s "while it is only assigned" → "while it is pending". Verify: `grep -n -F 'sources.value.filter((one) => pending(cell(one, flow)))' ui/src/views/Hub.vue` prints one line.
- [x] 1.4 In `ui/src/views/Hub.vue`, set the checkbox's class `hub__tick--pending` by `pending(cell(source, flow))`,
  and in `ui/src/app.css` rename `.hub__tick--assigned` to `.hub__tick--pending`, per [D3](design.md#d3).
  Verify: `grep -n -F "'hub__tick--pending': pending(cell(source, flow))" ui/src/views/Hub.vue` prints one line.
- [x] 1.5 In `ui/src/cells.test.ts`, turn `ui:hub:a-click-follows-the-cells-stage`'s `tagged` row to `'tick'`, and add
  `spec('ui:hub:a-tagged-cell-with-no-work-unticks', …)` holding `pending` and `locked` per the D2 table, per
  [Tests](design.md#tests). Verify: `grep -n -F "spec('ui:hub:a-tagged-cell-with-no-work-unticks'" ui/src/cells.test.ts` prints one line.
- [x] 1.6 In `tests/test_ui_api.py`, rename `test_unticking_a_cell_past_assigned_is_refused_and_changes_nothing` to
  `test_an_untick_is_refused_on_work_and_takes_an_empty_tagged_flow`, add its marker and its step, per
  [Tests](design.md#tests). Verify: `uv run pytest tests/test_ui_api.py -k takes_an_empty_tagged_flow` exits 0.

## 2 — The prose

Each edit keeps its grepped phrase on one line, rewrapping around it.

- [ ] 2.1 In `ui/design/spec.md`, *The tick*: "accent fill is assigned and can be unticked" → "accent fill is pending —
  assigned or tagged — and can be unticked". Verify: `grep -n -F 'accent fill is pending' ui/design/spec.md` prints one line.
- [ ] 2.2 In `ui/design/spec.md`, *A click or ↵ follows the stage*: "unassigned or assigned ticks and unticks; tagged or
  unreadable does nothing" → "unassigned, assigned or tagged ticks and unticks; unreadable does nothing".
  Verify: `grep -n -F 'assigned or tagged ticks and unticks; unreadable does nothing' ui/design/spec.md` prints one line.
- [ ] 2.3 In `isekai/interface/ui/README.md`, *A tick*: "An untick past assigned is refused" → "An untick of a
  directory holding work is refused". Verify: `grep -n -F 'An untick of a directory holding work is refused' isekai/interface/ui/README.md` prints one line.
- [ ] 2.4 In `ui/src/api.ts`, `assign`'s comment: "an untick past assigned is refused" → "an untick of a directory
  holding work is refused". Verify: `grep -n -F 'an untick of a directory holding work is refused' ui/src/api.ts` prints one line.
