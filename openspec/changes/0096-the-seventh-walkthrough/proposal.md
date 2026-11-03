---
bump: minor
backlog: [0091·R2]
---

# 0096 — the seventh walkthrough

What the operator's seventh pass found, fixed in one version: the hub's focus hint and the library's flow counts gone,
the viewer steady while an image loads and its title contained, the pick inside the window, a drafted draft's caption and
tags found, and a discard that undoes a drafted draft whole.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each fix |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui`, `sheet`, `review` |

```
1 the hub       the hint gone · the ↵ hint takes no line · the library row's flow counts gone
2 the viewer    a fixed frame · the title without the seed, cut by an ellipsis · the pick's height
3 the chain     tags_from followed to the flow that tagged: the sheet, the caption, both tag lists
4 the discard   a drafted draft's flow undone whole · 0091·R2's cites
```

## Why

**With five flows the screens built for three crowd and jump.** A focused cell grows by its hint, the library's chips
wrap, the viewer blinks while an image loads and its long title widens it, and the pick runs past the window. A flow
drafted from a drafted flow finds no caption and no tags, and its discarded draft comes back empty.

## What Changes

- **The hub and the library** lose the hint and the per-flow counts ([D1](design.md#d1), [D2](design.md#d2)).
- **The viewer and the pick** hold their size ([D3](design.md#d3), [D4](design.md#d4)).
- **A drafted sheet, its caption and its tag lists** come from the flow that tagged ([D5](design.md#d5)).
- **A discarded drafted draft** takes its sheet and its flow with it ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — *A missing caption is shown with the command that writes it*: the caption followed to the flow that tagged.
- `ui` — *Both tag lists are shown beside the prose…*: the lists followed the same way.
- `ui` — *A folder in the library is a collection when it holds `sources/`*: removed, and added as *…, listed by its
  sources*, without the per-flow counts.
- `sheet` — *A sheet is filled from another flow's tag list when the operator names it*: a source without a list leads on.
- `review` — *An unapproved draft can be discarded*: a drafted draft undone whole.

## Impact

- `ui/src/`: `views/Hub.vue`, `views/Home.vue`, `components/ImageViewer.vue`, `components/ComparePick.vue`,
  `composables/useSessionViewer.ts`, `app.css`, `types.ts`; `ui/design/spec.md`.
- `isekai/`: `interface/drafting.py`, `pipeline/sheet.py`, `pipeline/review.py`, `interface/ui/app.py`, `interface/ui/library.py`.
- Comments the card names, across `ui/src/`.

## Not in this change

- A photograph's caption and tags stored once, shared by every flow: their own version.
- Review's render lens title: it keeps its seed.
