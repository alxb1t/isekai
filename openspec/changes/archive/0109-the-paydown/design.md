# Design — 0109 the paydown

Each paid card's fix, the accent as text, and the cards closed with no work. **Verdict: feasible.**

## Context

Each card in `.minions/debt.md` was read against `main` at `eea5ebd9` (`v0.72.0`). See
[proposal](proposal.md) — Why. The paid ones are a test step or a line. The closed ones cite work that never reached
`main`, archived changes whose triggers passed, a fold already made, or a record not edited. The kept ones wait on a
rebuild, a design or a trigger.

## Goals / Non-Goals

**Goals:** each paid card's fix held by a test or a visible line; `--color-accent` as text at AA in every Catppuccin
theme.

**Non-Goals:** `isekai/boundary/pod_start.py`, which the image pins; the Render dialog, `isekai/interface/render.py`,
`isekai/interface/ui/app.py`, `isekai/interface/ui/jobs.py` and `isekai/interface/cli.py`, which `0108` edits; any
change to a sheet, a prompt or an image.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | Two browser steps, in existing tests. In `test_importing_a_new_collection_opens_its_hub_with_every_source_unassigned` (`tests/e2e/test_import.py`), while the commit is held, a `filechooser` listener records, `Shift+A` is pressed, and nothing is recorded (`0099·R1`). In `test_a_reload_lands_on_the_same_hub_and_the_same_review` (`tests/e2e/test_routes.py`), a short window, `j` to the last row, `k` back to the first, with *New collection* out of view and then in view (`0099·R2`) | the guard at `ui/src/components/ImportSheet.vue:380` and `reveal` at `ui/src/views/Home.vue:59` are each held by no test; a step in a test that reaches the state costs no page (`T2`, `T6`) | a new e2e test; a unit test of `Home.vue`, which `useEdges.test.ts` already is in all but the wiring |
| <a id="d2"></a>**D2** | The copy's `schema_remedy` in `isekai/pipeline/review.py:1069` runs `_again(run, flow)` in place of `` `{stage_command(run, STAGE, flow)}` `` (`0101·R5`) | `review` writes no draft for a flow that holds a version, unless `--new-version` asks (`review.py:174-175`); the other remedies already use `_again` | |
| <a id="d3"></a>**D3** | Latte's `--color-accent` (`ui/src/themes.css:33`) `#8839ef` → `#7c3dd4`; Frappé's (`:103`) `#ca9ee6` → `#c9a8e9`, each its theme's `--accent-ink`. Latte's link rule (`:309-310`) and its blank line go. `PAIRS` in `ui/src/themes.test.ts` gains `[['--color-accent'], ['--color-bg', '--color-surface'], 4.5]` | a token, not a per-screen rule ([D48](../../../docs/decisions.md#d48--a-theme-is-a-token-set-chosen-in-the-browser)); every text use of `--color-accent`, in `styles.css` and `app.css`, is fixed at once. `--accent`, a token of its own (`themes.css:85`), is left as it is | a rule per text site; Latte's link rule kept beside the token |
| <a id="d4"></a>**D4** | `ui/design/spec.md`'s *a missing image* row (`:489`) narrows to *a missing image, its record kept*, and a *a deleted render* row follows it (`0106·R8`). D48's lead in `docs/decisions.md:464-465` drops ", and nothing else but Latte's link colour", and its **Made by** gains `0109` | each says what holds after [D3](#d3) and `0106`'s second refusal (`app.py:1007-1008`) | |
| <a id="d5"></a>**D5** | No spec delta: `skip_specs: true` and `specs/.gitkeep`. The themes requirement already says the sheet's text meets 4.5:1; the `⇧A` exception and the edge-row scenario are already worded; the copy refusal's remedy is not specified. `ui:batch-folder:an-edge-row-shows-the-head` keeps `Layers: unit`, since `useEdges.test.ts` still holds it, and gains the browser step as a second binding | each fix makes the code meet a requirement as it stands; a patch adds no requirement (`CONTRIBUTING.md:57-66`). Decided by the cutter | a MODIFIED block that restates a requirement unchanged |

**The cards closed with no work:**

- `0095·R4`, `R5`, `R6`, `R7`, `R9`, `R11`, `R12`, `R18`, `R20`, `R21`, `S6` — the session queue never reached `main`:
  `git grep -n -e QUEUE_KEYS -e held_sheets` finds nothing. Its one real route is carded afresh, below.
- `0096·R8`, `0096·R9`, `0101·R4` — they cite archived changes, and their triggers have passed.
- `0103·R7` — fixed by `v0.69.0`'s fold: `openspec/specs/caption/spec.md:107` and `openspec/specs/tagging/spec.md:167`
  say "until a verb asks".
- `0097·R1` — accepted, wontfix.
- `0101·R1` — `CHANGELOG.md:105-106` is a released entry, and `CONTRIBUTING.md:54-55` calls the CHANGELOG "a release
  record, not a source".

**The card written at the cut:** `op·chained-source`, under `## operator` in `.minions/debt.md`. `_requested`'s last
branch (`isekai/interface/render.py:991-997`, its docstring at `:981` claiming "with the most images it renders") and
`in_session_sources` (`:132-149`) defer only a by-count source and refuse no chain. So a chained `S=U T=S` line can be
planned short. A design change; its trigger is the next change to `_requested` or a session's limit.

## Tests

The change adds and removes no test; it adds steps and one assertion row.

| layer | adds | removes |
|---|---|---|
| unit | the `PAIRS` row in `ui/src/themes.test.ts` ([D3](#d3)); the `--new-version` assertion in `test_a_copy_carries_the_sources_fields_and_the_targets_schema_validates_them` ([D2](#d2)) | none |
| end-to-end | a step in `test_importing_a_new_collection_opens_its_hub_with_every_source_unassigned` and one in `test_a_reload_lands_on_the_same_hub_and_the_same_review` ([D1](#d1)) | none |

`tests/e2e/` holds 19 tests at the base (`git grep -c '^def test_' eea5ebd9 -- tests/e2e`, summed), on Chromium
alone; this change leaves 19 and adds no end-to-end run. Both steps are the guards' twins (`T6`): with the guard at
`ImportSheet.vue:380` removed, the `⇧A` step records a dialog; with `reveal` removed from `Home.vue`'s `walk`, the
focus moves with `preventScroll` and nothing scrolls, so the step fails at `not_to_be_in_viewport()`.

The existing assertion `stage_command(run, "review", CONTROL) in str(refused.value)` at `tests/test_review.py:985` turns
red under [D2](#d2): `stage_command` puts `--new-version` before the run id, so the plain command is no longer a
substring. It becomes the command with `options=NEW_VERSION`.

## Dependencies

None.

## Risks / Trade-offs

- **The accent darkens on Latte and lightens on Frappé** → every use of `--color-accent` moves with it, borders and
  fills too; the hex is the theme's own `--color-accent-400`, so the look stays in its ramp.
- **`.appbar__count` keeps `var(--accent)`** (`ui/src/app.css:2370`) → on Latte's `--ground-deep` it reads 4.45:1, under
  AA. `--accent` is not in the settled fix, and no `PAIRS` row holds it; it is named in the proposal's
  *Not in this change*.
- **`0108` edits `ui/design/spec.md`'s state table** → the edits are textual and in other rows; integrate merges them.
- **The Home step leans on the `served` library overflowing a 300 px window** → it holds a collection per approval
  test and per hub test beside its own (`tests/e2e/conftest.py`'s `QUEUES` and `FRESH`); the step asserts the head out
  of view before it asserts it back.

## Verdict

**feasible.** Every file named exists at `eea5ebd9`, each fix is required by an existing requirement or states what
already holds, and nothing moves a format, a verb or the product.
