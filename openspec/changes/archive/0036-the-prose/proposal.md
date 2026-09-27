---
version: v0.25.1
backlog: [0021·S1, 0025·S1, 0033·R2, 0033·S1, 0033·S2, 0034·R5, 0035·S6, op·graph-filename]
---

# 0036 — the prose

What the public repository says, and nothing it does: intimate tags leave the prose, a decision states that isekai
restricts no content, the pins guide stops overstating the reader's and the image's pins, the teardown and port
messages name the right fix, and a real photograph's filename leaves a flow's graph. No behaviour and no output
changes.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each rewrite rule, the decision's text, the messages before → after |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | none — no requirement changes ([D8](design.md#d8)) |

## Why

**The repository is public, and its prose quotes the operator's approved sheets.** Archived changes, `CHANGELOG.md`
and the `inflect()` docstring name intimate tags read off real photographs, and per-tag counts from the same sheets.
Those tags belong only in the code and config that map tags to the sheet.

**The rest is prose that says the wrong thing.** Nothing records that the render path restricts no content, so a
review keeps raising it. `docs/pins.md` calls the reader's and the image's pins stronger than they are. The
lost-create, no-record and port messages send the reader to the wrong fix, and a flow's graph carries a real
photograph's filename as a placeholder no render ever sees.

## What Changes

- **The sweep:** every prose line that quotes an intimate tag, a rating term or an intimate example is rewritten by
  describing it, in archived `0018`, `0020`, `0021` and `0025` and in `CHANGELOG.md`; per-tag counts from the
  operator's sheets go the same way ([D1](design.md#d1)).
- **Comments, not code:** the `inflect()` docstring, the per-tag count comment and the false "load-bearing" comment in
  `tools/derive_field_map.py` are rewritten; `FILED`, `SEEDS` and every line of behaviour stay ([D2](design.md#d2)).
- **The check lives outside the tree:** the term list is the gitignored `.minions/prose-terms.txt`
  ([D3](design.md#d3)).
- **D33** — isekai restricts no content; the operator answers for what renders ([D4](design.md#d4)).
- **`docs/pins.md`:** the reader alias's unchecked layers and the image's build tools join *Not pinned*; a leftover
  pod-image record's borrowed pin joins *where it stops* ([D5](design.md#d5)).
- **The scripts' messages:** a lost create and a failed teardown route through `.runpod_pod_id` and
  `infra/down.sh`; the port refusal stops only its own tunnel ([D6](design.md#d6)).
- **The graph's placeholder:** a neutral name, and the flow re-pinned in place ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None — `skip_specs` ([D8](design.md#d8)).

## Impact

- **Files:** archived `openspec/changes/archive/{0018-review-ui,0020-readable-caption,0021-sheet-from-the-tagger,0025-running-the-flow}/`,
  `CHANGELOG.md`, `tools/derive_field_map.py`, `docs/decisions.md`, `docs/pins.md`, `infra/up.sh`, `infra/down.sh`,
  `infra/render.sh`, `flows/summon-anime-wai/graph.json`, `tests/test_flow.py`, `tests/test_infra.py`,
  `tests/test_generate.py`, and the goldens `tests/golden/{sheet,sheet-empty,prompt,render}.json`.
- **Behaviour:** none. The same sheets, prompts, submitted graphs and images; new records name the summon flow's new
  digest.
- **Patch conditions** ([D8](design.md#d8)): no format version moves, no behaviour fix, nothing deprecated, the
  product unchanged.
- **Dependencies:** none.

## Not in this change

- **`FILED`, `--refresh`, `filings()` and the tests that read `.data/`** — they stay as they are.
- **A rating tag, a content filter, or a README line about content** — [D4](design.md#d4) records why not.
- **Rewriting git history** — earlier tags keep what they published.
- **The living specs** — they hold no hit.
- **A terse `CHANGELOG.md`** — its format, rewritten whole, when the operator schedules it.
- **Hashes for the image's build tools** (`0033·S3`'s other half) — with the next image rebuild.
- **The boundaries' behaviour fixes** — the proxy, the deadline, the upload, the review surface, the frame, the
  watchdog — a minor of their own.
