# The paydown, the page — tasks

Each late completion of the page becomes a unit its component calls, held by a case with a deferred answer, and the units' guards are red in `tests/mutants.json`.

## Progress

- [x] 1 — The leaving · moderate
- [x] 2 — The deletion · moderate
- [ ] 3 — The picker · moderate
- [ ] 4 — The red runs · moderate

## 1 — The leaving

- [x] 1.1 Create `ui/src/composables/useDeletion.ts` as [D1](design.md#d1) gives it: `latest` moved whole from `ui/src/views/RenderLarge.vue`, and `useDeletion`, which returns `{ deleted }`.
  Verify: `grep -c -F "export function useDeletion" ui/src/composables/useDeletion.ts` prints `1`.
- [x] 1.2 Create `ui/src/composables/useDeletion.test.ts` with `spec('ui:delete-render:a-reload-that-lands-after-leaving-moves-nothing', …)` as [D5](design.md#d5) says: scope stopped before the read answers, answered and refused, then the scope kept.
  Verify: `uv run python -m tools.test_ui ui/src/composables/useDeletion.test.ts` exits 0.
- [x] 1.3 In `ui/src/views/RenderLarge.vue` delete the plain `<script lang="ts">` block, and replace `leaving`, `onUnmounted(leaving.drop)` and `deleted` with the `useDeletion` call of [D1](design.md#d1). Import `useDeletion` from `'../composables/useDeletion'` and drop `onUnmounted` from the `'vue'` import.
  Verify: `git grep -n -F "onUnmounted" -- ui/src/views/RenderLarge.vue` prints nothing.
- [x] 1.4 In `ui/src/views/RenderLarge.test.ts` change the import line to `import { latest } from '../composables/useDeletion'` and nothing else ([D7](design.md#d7)).
  Verify: `uv run python -m tools.test_ui ui/src/views/RenderLarge.test.ts` exits 0.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.

## 2 — The deletion

- [x] 2.1 In `ui/src/composables/useDeletion.ts` add `through` as [D2](design.md#d2) gives it, import `reporting` from `'../confirm'`, and return `{ deleted, through }`.
  Verify: `grep -c -F "const through" ui/src/composables/useDeletion.ts` prints `1`.
- [x] 2.2 In `ui/src/composables/useDeletion.test.ts` add `spec('ui:delete-render:a-dismissed-dialog-still-opens-the-hub', …)` as [D5](design.md#d5) says: `through(remove)()` begun with no dialog, answered, then refused.
  Verify: `uv run python -m tools.test_ui ui/src/composables/useDeletion.test.ts` exits 0.
- [x] 2.3 In `ui/src/views/RenderLarge.vue` take `through` from `useDeletion` in place of `deleted`, pass `:run="through(() => deleteRender(place))"` to the delete `ConfirmDialog` and remove its `@done="deleted"` line ([D2](design.md#d2)).
  Verify: `git grep -n -F "@done" -- ui/src/views/RenderLarge.vue` prints nothing.
  Verify: `git grep -c -h -F "through(() => deleteRender(place))" -- ui/src/views/RenderLarge.vue` prints `1`.

## 3 — The picker

- [ ] 3.1 Create `ui/src/composables/useRemoval.ts` as [D3](design.md#d3) gives it, and `ui/src/composables/useRemoval.test.ts` with `spec('ui:picker:a-dismissed-removal-still-lists-the-rest', …)` as [D5](design.md#d5) says.
  Verify: `uv run python -m tools.test_ui ui/src/composables/useRemoval.test.ts` exits 0.
- [ ] 3.2 In `ui/src/components/TattooPicker.vue` replace `asking`, `question` and `removed` with the `useRemoval` call of [D3](design.md#d3), import `useRemoval`, and drop the `'../confirm'` import line.
  Verify: `git grep -n -E "reporting|removal\(" -- ui/src/components/TattooPicker.vue` prints nothing.
- [ ] 3.3 Create `ui/src/composables/useCutInk.ts` as [D4](design.md#d4) gives it, and `ui/src/composables/useCutInk.test.ts` with `spec('ui:picker:a-crop-that-lands-after-leaving-is-dropped', …)` as [D5](design.md#d5) says.
  Verify: `uv run python -m tools.test_ui ui/src/composables/useCutInk.test.ts` exits 0.
- [ ] 3.4 In `ui/src/components/CutImage.vue` replace the refs, the `asking` controller, the `gone` flag, `onMounted`'s body and `onUnmounted` with the `useCutInk` call and `onMounted(load)` of [D4](design.md#d4), and drop the imports nothing then reads.
  Verify: `git grep -n -E "onUnmounted|AbortController|inkUrl" -- ui/src/components/CutImage.vue` prints nothing.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 3.5 Hold each new key's binding and the page's ratchet.
  Verify: `grep -c -E "^spec\('ui:picker:a-(dismissed-removal|crop)" ui/src/composables/useRemoval.test.ts ui/src/composables/useCutInk.test.ts` prints `1` for each file.
  Verify: `uv run pytest tests/test_spec_bindings.py tests/test_ratchets.py` exits 0.

## 4 — The red runs

- [ ] 4.1 Append the entries of [D6](design.md#d6) to `tests/mutants.json`, after `VT-18c`'s object and before the closing `]`, each in the file's two-space layout.
  Verify: `git grep -c -h -E "\"finding\": \"PG-" -- tests/mutants.json` prints `4`.
- [ ] 4.2 Replay the file: each new edit is red by its case, and no edit survives.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.
