# Design — 0110 the small fixes

The count's token, and the debt file the measure reads. **Verdict: feasible.**

## Context

Every fact was re-read at `main` `c8e7fdc1`, the merge after `v0.73.0`. See [proposal](proposal.md) — Why.

- `.appbar__count` (`ui/src/app.css:2386-2391`) draws `color: var(--accent)` on `.appbar`'s `--ground-deep`
  (`:57-66`). It is the Review tab's count (`ui/src/App.vue:124`). Every other `--accent` use is a fill, border or
  outline. `.appbar__render`, on the same bar, reads `--accent-ink` (`:97`).
- `ui/design/spec.md:52` gives `--accent-ink` to commands; `:88` says the count is "mono 11 `accent`".
- `PAIRS` in `ui/src/themes.test.ts` holds `--accent-ink` on `--ground`, `--raised` and `--raised-2`, not on
  `--ground-deep`. Each Catppuccin block of `ui/src/themes.css` sets `--ground-deep`.
- `scripts/metrics/backlog.py:34` returns the primary's `.minions/backlog.md`; that file is gone, and
  `.minions/debt.md` holds the cards, in the shape `CARD` (`:15`) already matches.
- `tests/test_metric_scripts.py:132` asserts the `backlog.md` path. `metrics/catalogue.toml:29` titles the measure.

## Goals / Non-Goals

**Goals:** the count at 4.5:1 in every Catppuccin theme, held by `PAIRS`; the measure readable again.

**Non-Goals:** any `--accent` value; the measure's id; any record under `metrics/changes/`; a sheet, a prompt or an image.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `.appbar__count`'s `color: var(--accent);` (`ui/src/app.css:2389`) → `color: var(--accent-ink);`. `ui/design/spec.md:88`'s "mono 11 `accent`" → "mono 11 `accent-ink`". `PAIRS`'s `[['--accent-ink'], ['--ground', '--raised', '--raised-2'], 4.5],` gains `'--ground-deep'` | the only `--accent` drawn as text; on `--ground-deep`, `--accent-ink` reads Latte 4.97, Frappé 6.75, Macchiato 8.06, Mocha 9.26 (the brief's Q1); the bar's *Render* already reads it | darkening Latte's `--accent`, which moves every fill and makes it equal `--accent-ink`; a Latte-only rule, which [D48](../../../docs/decisions.md#d48--a-theme-is-a-token-set-chosen-in-the-browser) rules out |
| <a id="d2"></a>**D2** | `scripts/metrics/backlog.py` returns `.minions/debt.md` (`:34`); its docstrings (`:5`, `:19`, `:27`) say *debt file* for *backlog*; its error (`:43`) says `debt unreadable`. `tests/test_metric_scripts.py:132` asserts `debt.md`. `metrics/catalogue.toml:29`'s title → `Open debt cards`; the id `open-backlog-cards`, the script's name and `backlog_path` stay | one series across the records; records are history ([D47](../../../docs/decisions.md#d47--a-change-is-measured-from-isekais-own-catalogue)) | a new id, which splits the series; rewriting `0107`–`0109`'s records |
| <a id="d3"></a>**D3** | No spec delta: `skip_specs: true` and `specs/.gitkeep` | the themes requirement already holds `accent-ink` at 4.5:1 on the grounds it is drawn on; no requirement specifies the measure; a patch adds no requirement (`CONTRIBUTING.md:57-66`) | a MODIFIED block that restates a requirement unchanged |

## Tests

The change adds and removes no test; it widens one assertion row and edits one assertion.

| layer | adds | removes |
|---|---|---|
| unit | `'--ground-deep'` in `PAIRS`'s `--accent-ink` row ([D1](#d1)); `debt.md` in `test_the_backlog_is_in_the_primary_checkouts_minions` ([D2](#d2)) | none |
| end-to-end | none | none |

`tests/e2e/` holds 19 tests at the base (`git grep -c '^def test_' c8e7fdc1 -- tests/e2e`, summed), on Chromium
alone; this change leaves 19 and adds no end-to-end run.

The existing assertion at `tests/test_metric_scripts.py:132` turns red under [D2](#d2); task 2.1 edits it.
`test_a_missing_backlog_is_refused` asserts only `unreadable` in the error, and stays green. The widened `PAIRS` row
holds `--accent-ink` on `--ground-deep` in every Catppuccin theme. It reads `themes.css` alone, so no test reads which
token `.appbar__count` draws: task 1.2's check and review hold that line.

## Dependencies

None.

## Risks / Trade-offs

- **The count's colour lightens or darkens a step in every theme** → it matches the bar's *Render* link, the one other
  text on that bar in the accent family.
- **The record keeps the old title's id** → the id names the series; the title is what a reader sees.

## Verdict

**feasible.** Every file and line named exists at `c8e7fdc1`, each fix meets a requirement or decision as it stands,
and nothing moves a format, a verb or the product.
