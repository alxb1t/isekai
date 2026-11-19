# The page stream — tasks

Type the live store's `listen` by the wire's `Events`, drop the casts on the stream, and close what D66 accepted. The decisions are in [design](design.md).

## Progress

- [x] 1 — The typed stream · moderate
- [ ] 2 — The decision · moderate

## 1 — The typed stream

- [x] 1.1 In `ui/src/types.ts`, add `export type { Events } from './wire'` on the line after `export type { CellEvent } from './wire'` ([D1](design.md#d1)).
  Verify: `git grep -n -F "export type { Events } from './wire'" -- ui/src/types.ts` prints one line.

- [x] 1.2 In `ui/src/stores/live.ts`, add `Events` to the import from `'../types'`. Replace the `KINDS` and `Kind` lines with the lines of [D3](design.md#d3): `KINDS` with `satisfies readonly (keyof Events)[]`, `Kind`, and the `listed` constant. Leave `Handler`, `Snapshot` and the `Map` as they are.
  Verify: `git grep -n -F "keyof Events" -- ui/src/stores/live.ts` prints two lines.

- [x] 1.3 **HALT CHECK** In `ui/src/stores/live.ts`, replace `type Handler = (data: unknown) => void` with `type Handler<K extends Kind> = (data: Events[K]) => void`. Replace the `handlers` `Map` with the object of [D2](design.md#d2), one key a kind, each `new Set()`. Rewrite `listen` and `emit` as generic in the kind, as [D2](design.md#d2) shows. A refusal by the typecheck means that index is wrong: halt, and the plan takes the fallback [D2](design.md#d2) names.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.

- [x] 1.4 In `ui/src/stores/live.ts`, drop each `as` cast on a payload: the parameter of each `listen` handler is the payload, so `listen('snapshot', (found) => {` loses its `const found = data as Snapshot` line, and the `file` handler reads `const { upload, ...state } = data` and keeps its spread. Delete `export interface Snapshot` and its comment, and `HubInfo` from the import.
  Verify: `git grep -n -F "data as " -- ui/src/stores/live.ts` prints nothing.

- [x] 1.5 In `ui/src/stores/collection.ts`, delete `type Snapshot` from the import of `'./live'` and `CellEvent` from the import of `'../types'`. The `snapshot` handler reads `data.hub`, and the `cell` handler's parameter is named `event`, so its `const event = data as CellEvent` line goes with its `data as ` cast.
  Verify: `git grep -n -F "data as " -- ui/src/stores/collection.ts` prints nothing.

- [x] 1.6 Show each direction of [D3](design.md#d3) once. Take `'file'` out of `KINDS` in `ui/src/stores/live.ts` and run `uv run python -m tools.typecheck_ui`: it fails. Put `'file'` back. Add `'stream'` to `KINDS` and run it again: it fails. Take `'stream'` out. Leave the file as 1.2 wrote it.
  Verify: `git grep -c -F "'billing', 'cell', 'file'] as const satisfies readonly (keyof Events)[]" -- ui/src/stores/live.ts` prints `ui/src/stores/live.ts:1`.

## 2 — The decision

- [ ] 2.1 In `docs/decisions.md`, amend D66 as [D6](design.md#d6) says: its *Accepts* line says the typecheck holds the page's kinds to `Events`' keys, which a test holds to `EVENTS`', and drops the clause `no test holds` and the sentence beginning `Reopen`; its *Made by* line reads `` `0166`, `0167`, `0172` ``. Add no decision.
  Verify: `git grep -n -F "no test holds" -- docs/decisions.md` prints nothing.
