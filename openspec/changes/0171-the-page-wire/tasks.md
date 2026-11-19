# The page wire — tasks

The phases move `ui/src/types.ts` onto `ui/src/wire.ts`, one group of types at a time. The typecheck is green at the end of each.

## Progress

- [x] 1 — The first half: library, hub, review and staging · moderate
- [x] 2 — The second half: jobs, quotes, renders, tattoos and compare · moderate
- [ ] 3 — The overlays · moderate
- [ ] 4 — The six that differ · moderate
- [ ] 5 — The documents · moderate

## 1 — The first half: library, hub, review and staging

Each type below is the wire's field for field, so its declaration and doc comment in `ui/src/types.ts` become one re-export line ([D1](design.md#d1)). A type still local to `types.ts` that names a re-exported type imports it from `./wire` in an `import type { … } from './wire'` line at the top of the file ([D2](design.md#d2)).

- [x] 1.1 **HALT CHECK** No page file reads the wire yet: `./wire` is imported by no file of `ui/src`. The plan assumes `types.ts` is the first.
  Verify: `git grep -l -F "'./wire'" -- ui/src` prints nothing.
- [x] 1.2 In `ui/src/types.ts`, replace `FlowCount`, `LibraryRow` and `LibraryInfo` each with its re-export, e.g. `export type { FlowCount } from './wire'`, and `Stage` with `export type { LibraryStage as Stage } from './wire'`, one a line.
  Verify: `git grep -n -E "^export (interface|type) (FlowCount|LibraryRow|LibraryInfo|Stage)( |$)" -- ui/src/types.ts` prints nothing.
- [x] 1.3 In `ui/src/types.ts`, replace `HubCell`, `HubSource`, `HubInfo` and `Assigned` the same way. `CellEvent` still names `HubCell`: add `HubCell` to the import line.
  Verify: `git grep -n -E "^export (interface|type) (HubCell|HubSource|HubInfo|Assigned)( |$)" -- ui/src/types.ts` prints nothing.
- [x] 1.4 In `ui/src/types.ts`, replace the review's types — `Budget`, `ScoredTag`, `OfferedTag`, `FieldCandidates`, `Renders`, `InputDetail`, `Revision`, `Drafted`, `TagMatches`, `DraftedImage`, `RefusedImage` and `DraftRefused` — the same way, and `VocabEntry` with `export type { TagMatch as VocabEntry } from './wire'` and `InputStatus` with `export type { ReviewStatus as InputStatus } from './wire'`. `CollectionInput` names `InputStatus`: add `ReviewStatus as InputStatus` to the import line.
  Verify: `git grep -n -E "^export (interface|type) (Budget|ScoredTag|OfferedTag|FieldCandidates|Renders|InputDetail|Revision|Drafted|VocabEntry|TagMatches|InputStatus|DraftedImage|RefusedImage|DraftRefused)( |$)" -- ui/src/types.ts` prints nothing.
- [x] 1.5 In `ui/src/types.ts`, replace `FileState` and `Committed` the same way, and `StagedState` with `export type { ImportingState as StagedState } from './wire'`. `StagedFile` stays and names `StagedState`: add `ImportingState as StagedState` to the import line.
  Verify: `git grep -n -E "^export (interface|type) (FileState|Committed|StagedState)( |$)" -- ui/src/types.ts` prints nothing.

## 2 — The second half: jobs, quotes, renders, tattoos and compare

The same move for the rest of the types the wire holds field for field. The overlays and the types that differ are the later phases.

- [x] 2.1 In `ui/src/types.ts`, replace `SessionImage` and the jobs' types: `RenderSession` with `export type { JobSession as RenderSession } from './wire'`, `JobKind` with `export type { JobsKind as JobKind } from './wire'`, `JobSlot` with `export type { Job as JobSlot } from './wire'` and `StageCount` with `export type { JobStage as StageCount } from './wire'`. `SessionRecord` still names `SessionImage`: add it to the import line.
  Verify: `git grep -n -E "^export (interface|type) (SessionImage|RenderSession|JobKind|JobSlot|StageCount)( |$)" -- ui/src/types.ts` prints nothing.
- [x] 2.2 In `ui/src/types.ts`, rewrite `JobSlots` as the one-line alias `export type JobSlots = Record<JobsKind, Job | null>`, importing `Job` and `JobsKind` from `./wire` ([D2](design.md#d2)).
  Verify: `git grep -n -F "export type JobSlots = Record<JobsKind, Job | null>" -- ui/src/types.ts` prints one line.
- [x] 2.3 In `ui/src/types.ts`, replace the quotes' types: `QuoteBake` with `export type { QuotedBake as QuoteBake } from './wire'`, `QuotedCollection` with `export type { QuotedRow as QuotedCollection } from './wire'`, and `Quote` and `RenderOffer` plain. `QuoteSource` and `TakenOut` stay.
  Verify: `git grep -n -E "^export (interface|type) (QuoteBake|QuotedCollection|Quote|RenderOffer)( |$)" -- ui/src/types.ts` prints nothing.
- [x] 2.4 In `ui/src/types.ts`, replace `RenderDetail` and `Bake` plain, and `Baked` with `export type { BakeQueued as Baked } from './wire'`.
  Verify: `git grep -n -E "^export (interface|type) (RenderDetail|Bake|Baked)( |$)" -- ui/src/types.ts` prints nothing.
- [x] 2.5 In `ui/src/types.ts`, replace `TattooLimits`, `CompareSide` and `Comparison` plain. `Preview` and `InkView` stay. `TattooList` still names `TattooLimits`: add it to the import line.
  Verify: `git grep -n -E "^export (interface|type) (TattooLimits|CompareSide|Comparison)( |$)" -- ui/src/types.ts` prints nothing.

## 3 — The overlays

Each overlay is an `extends Omit<…>` of the wire's type that narrows a pair to the page's `Point` and `Pair`, which stay in `types.ts` ([D6](design.md#d6)). Import the wire's type under a `Wire` prefix, e.g. `Tattoo as WireTattoo`, so the overlay can keep the page's name.

- [ ] 3.1 In `ui/src/types.ts`, rewrite `Tattoo` as `extends Omit<WireTattoo, 'size' | 'downscaled_from'>` with `size: [number, number]` and `downscaled_from: [number, number] | null`, and `Outline` as `extends Omit<WireOutline, 'points'>` with `points: Point[]`.
  Verify: `git grep -n -E "^export interface (Tattoo|Outline) \{" -- ui/src/types.ts` prints nothing.
- [ ] 3.2 In `ui/src/types.ts`, rewrite `Stage1` as `extends Omit<WireStage1, 'pairs'>` with `pairs: Pair[]`, and `Proposal` as `extends Omit<Proposed, 'pairs'>` with `pairs: Pair[]`.
  Verify: `git grep -n -E "^export interface (Stage1|Proposal) \{" -- ui/src/types.ts` prints nothing.
- [ ] 3.3 In `ui/src/types.ts`, rewrite `TattooList` as `extends Omit<Tattoos, 'tattoos' | 'stage1'>` with `tattoos: Tattoo[]` and `stage1: Record<string, Stage1>`, both the page's overlays, and no `stage1?:` left ([D6](design.md#d6)).
  Verify: `git grep -n -F "stage1?:" -- ui/src/types.ts` prints nothing.

## 4 — The six that differ

`SessionRecord`, `RunningSession`, `Billing`, `QuoteSource`, `CellEvent` and `TattooList` are the types that differ ([design](design.md#context)); `TattooList` was phase 3. The page takes the wire's wider type where it was narrower ([D3](design.md#d3)).

- [ ] 4.1 In `ui/src/types.ts`, replace `Billing`, whose volume state is `'open' | 'band'`, with `export type { Billing } from './wire'`. No site changes: each only compares the volume's state.
  Verify: `git grep -n -F "'open' | 'band'" -- ui/src/types.ts` prints nothing.
- [ ] 4.2 In `ui/src/types.ts`, replace `CellEvent`, whose state is `'start' | 'done' | 'refused'`, with `export type { CellEvent } from './wire'`.
  Verify: `git grep -n -F "'start' | 'done' | 'refused'" -- ui/src/types.ts` prints nothing.
- [ ] 4.3 In `ui/src/stores/collection.ts`, make the cell listener keep the stage only when it is set, as [D7](design.md#d7) shows. The `data as CellEvent` cast stays.
  Verify: `git grep -c -F "if (event.state === 'start' && event.stage) running.value[here] = event.stage" -- ui/src/stores/collection.ts` prints `ui/src/stores/collection.ts:1`.
- [ ] 4.4 In `ui/src/types.ts`, rewrite `QuoteSource` as `export type QuoteSource = Omit<QuotedSource, 'images'>`, importing `QuotedSource` from `./wire` ([D5](design.md#d5)).
  Verify: `git grep -n -F "export type QuoteSource = Omit<QuotedSource, 'images'>" -- ui/src/types.ts` prints one line.
- [ ] 4.5 In `ui/src/types.ts`, replace `SessionRecord` with `export type { ServedSession as SessionRecord } from './wire'` and `RunningSession` with `export type { RunningSession } from './wire'` ([D4](design.md#d4)).
  Verify: `git grep -n -E "^export interface (SessionRecord|RunningSession) \{" -- ui/src/types.ts` prints nothing.
- [ ] 4.6 Give the `SessionRecord` fixtures `schema: { name: 'session', version: 1 }`: `record()` in `ui/src/sessions.test.ts` and the `b` record of the `drawer.records` literal in `ui/src/components/SessionDrawer.test.ts`. No assertion changes.
  Verify: `git grep -c -F "schema: { name: 'session', version: 1 }" -- ui/src/sessions.test.ts` prints `ui/src/sessions.test.ts:1`.
- [ ] 4.7 Give the `RunningSession` fixtures `schema: { name: 'session', version: 1 }`, `ended: null`, `limit: 1200`, `asked: {}`, `steps: {}`, `images: []`, `outcome: 'running'` and `message: null`: `terminal` in `ui/src/stores/live.test.ts` and the entry of `live.activeSessions` in `ui/src/components/SessionDrawer.test.ts`. No assertion changes.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.

## 5 — The documents

- [ ] 5.1 In `ui/src/types.ts`, replace the header comment, which names `app.py`, with one that says the file holds the page's names for the wire: the re-exports, the overlays and the types only the page holds.
  Verify: `git grep -n -F "app.py" -- ui/src/types.ts` prints nothing.
- [ ] 5.2 In `ui/src/components/SourcePanel.vue`, add the line `/* A null \`wd14\` is never a failure: the panel is not drawn. */` directly above the comment of `const scored` ([D8](design.md#d8)).
  Verify: `git grep -c -F "is never a failure: the panel is not drawn" -- ui/src/components/SourcePanel.vue` prints `ui/src/components/SourcePanel.vue:1`.
- [ ] 5.3 In `ui/src/stores/live.ts`, add the line `/* \`band\` is the window volume past its end or unanswered; the wire types its state \`str\`. */` directly above the comment of `alerting` ([D8](design.md#d8)).
  Verify: `git grep -c -F "is the window volume past its end or unanswered" -- ui/src/stores/live.ts` prints `ui/src/stores/live.ts:1`.
- [ ] 5.4 In `docs/decisions.md`, edit D67 where it lives ([D10](design.md#d10)). Replace its *Accepts* line's last sentence, which says the page reads the file from `the-page-wire`, with: `` `ui/src/types.ts` is the one page file that imports `wire.ts`, and narrows a pair in the overlays `Tattoo`, `Outline`, `Stage1`, `Proposal` and `TattooList`. ``
  Its *Made by* line becomes `` `0168`, `0171`. ``
  Verify: `git grep -n -F "until then no page file imports" -- docs/decisions.md` prints nothing.
- [ ] 5.5 `ui/src/types.ts` holds only the re-exports, the overlays and the page's own types, in at most 250 lines.
  Verify: `wc -l ui/src/types.ts` prints a number no greater than 250.
