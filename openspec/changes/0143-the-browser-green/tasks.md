# The browser green — tasks

The browser tests' fake and refusals first, then the Hub after a delete. A build cannot start Chromium, so CI proves the browser steps after the merge ([D5](design.md#d5)).

## Progress

- [x] 1 — The fake and the refusals · moderate
- [ ] 2 — The Hub after a delete · moderate

## 1 — The fake and the refusals

- [x] 1.1 In `tests/e2e/test_import.py`, replace the `data:` line of `CONVERTING` with the snapshot of [D2](design.md#d2): one `data:` line holding `jobs`, `billing`, then `files`, built from adjacent string literals. Add to the comment above it that the snapshot carries both slots, as every server snapshot does.
  Verify: `git grep -n -F '"billing": {"pod": false, "volume": null}' -- tests/e2e/test_import.py` prints the line.

- [x] 1.2 In `tests/e2e/test_render.py`, import `Refused` from `tests.e2e.guard` and give `test_the_render_dialog_opens_on_its_first_photograph` a `refusals: list[Refused]` parameter. Its first statement appends `Refused(409, f"/api/c/{RENDER}/sessions/")`, as [D3](design.md#d3) says.
  Verify: `git grep -n -F 'Refused(409, f"/api/c/{RENDER}/sessions/")' -- tests/e2e/test_render.py` prints the line.

- [x] 1.3 In `tests/e2e/test_render.py`, give `test_the_drawer_holds_the_render` the same `refusals` parameter. Its first statements append `Refused(409, f"/api/c/{DRAWN}/sessions/")` and `Refused(409, f"/api/c/{WIDE}/sessions/")`.
  Verify: `git grep -n -F 'Refused(409, f"/api/c/{WIDE}/sessions/")' -- tests/e2e/test_render.py` prints the line.

## 2 — The Hub after a delete

- [ ] 2.1 **HALT CHECK** `ui/src/App.vue` opens the collection store on the route's collection, so the store `RenderLarge.vue` takes in task 2.2 holds the collection the view shows. A miss means the plan is wrong.
  Verify: `git grep -n -F 'collectionStore.open(shown)' -- ui/src/App.vue` prints the line.

- [ ] 2.2 In `ui/src/views/RenderLarge.vue`, import `useCollectionStore` from `../stores/collection`, hold it in `store` after `router`, and make `deleted` the async function of [D4](design.md#d4): it awaits `store.reloadHub()` with a refusal ignored, then pushes `hubCell`. Update the comment above it to say the hub is read again first.
  Verify: `git grep -n -F 'store.reloadHub()' -- ui/src/views/RenderLarge.vue` prints the line.

- [ ] 2.3 In `tests/e2e/test_render.py`, bind `ui:delete-render:the-hub-opens-without-the-deleted-render` on `test_conjure_from_this_opens_review`, after its `yes-opens-the-hub-on-the-cell` marker.
  Verify: `git grep -n -F 'the-hub-opens-without-the-deleted-render' -- tests/e2e/test_render.py` prints the marker.

- [ ] 2.4 In the same test, before the second `Shift+Backspace`, start `asked: list[str] = []` with `page.on("request", lambda request: asked.append(request.url))`. After the `expect(cell).to_be_focused()` expectation, which the Hub meets once it has drawn, assert that no URL in `asked` ends with `f"/api/c/{CONJURED}/renders/{digest}/{FLOW}/v1/7/thumb"`.
  Verify: `git grep -n -F 'page.on("request"' -- tests/e2e/test_render.py` prints the line.
