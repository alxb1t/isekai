# This folder is an imported artifact

It is the handoff from a Claude Design session, run on 2026-09-17, copied here verbatim so the build has
the frames, the copy and the token sheet it is held to. **It is read-only.** A design is corrected by
running another session and replacing the folder, never by editing a handoff in place.

Two things were left out of the import, deliberately:

- `screens/isekai-review-design.html` — the whole design as one self-contained 9.9 MB file. The markdown
  here says everything it says.
- `screens/source/` — the unbundled markup behind that page, which carries a second copy of it.

**Where it disagrees with the change, the change wins.** `openspec/changes/0018-review-ui/design.md`
§ *Frame deltas* enumerates every place the build deliberately differs from these frames, and § *Build
reference* carries the component tree, the build order and the keyboard model as the change settled them.
Everything not in that table is binding at full fidelity.

**Its sample data is invented** — captions, post counts, filenames and timestamps are plausible
fabrications. Do not seed fixtures from them. One figure it apologises for is in fact exact: the
vocabulary really does hold 8,106 tags.
