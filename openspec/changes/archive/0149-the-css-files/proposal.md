---
bump: patch
version: 0.87.5
after: [0148-the-render-routes]
---

# The CSS's files

The page's one stylesheet, `ui/src/app.css`, becomes the files of `ui/src/css/`, each a span of it in today's order; no rule is edited.

Reading map: [design](design.md) holds the cut table, the proof and the guard, [tasks](tasks.md) the move, the guard and the documents.

## Why

`ui/src/app.css` is the largest row of the ratchet's `ui/src` table ([docs D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)), and a new rule for any screen lands in it. A file a screen makes the rule's home easy to find, and the table loses its biggest offender.

The cut is by construction: the files joined in order equal the old sheet byte for byte, so the cascade is unchanged. Nothing in the gate renders the page, so the join is the proof.

## What Changes

- `ui/src/css/` holds the files of [D1](design.md#d1), each a span of `ui/src/app.css` cut at a blank line.
- `ui/src/main.ts` imports each on its own line after `themes.css`, in the order of the table, and `ui/src/app.css` is deleted.
- The ratchet's `ui/src` table loses its `ui/src/app.css` row.
- `ui/src/components/TagInput.vue`'s comment names the file that holds `.drop`.
- `tests/test_css_files.py` holds that every file of `ui/src/css/` is imported by `main.ts` once, and its twin ([D4](design.md#d4)).
- A decision says where the page's CSS lives; the README's tree names `css/` ([D6](design.md#d6)).

No requirement is added, changed or removed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- Code: `ui/src/main.ts`, `ui/src/components/TagInput.vue` (a comment), `ui/src/app.css` (deleted), `ui/src/css/` (the new files).
- Tests: `tests/test_ratchets.py` (a table row and its count), `tests/test_css_files.py` (new).
- Documents: `docs/decisions.md`, `README.md`.
- No format version moves, no flow is re-pinned, no frozen image file is touched, and the page renders as before.

## Not in this change

- Any rule's text or order.
- The rules a file holds for another screen: moving them needs the cascade's argument, so it waits until the rules are regrouped by screen.
- The overridden `.tile--ready` rule: whether it is a defect is the person's to judge on the page ([D5](design.md#d5)).
- A header comment in a file: it would break the join.
- A CSS linter.
- A test that renders the page.
