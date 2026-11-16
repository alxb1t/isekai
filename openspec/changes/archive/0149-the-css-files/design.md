# The CSS's files — design

`ui/src/app.css` is cut at its blank lines into the files of `ui/src/css/`, in today's order, and `main.ts` imports them in that order. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`ui/src/main.ts` imports `styles.css` (the vendored tokens), `themes.css` and `app.css`, the page's own rules. `app.css` holds every screen's rules and is the largest row of the ratchet's `ui/src` table ([docs D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)).

Evidence, at the cut's base `7cf59b7d`:

| fact | command | prints |
|---|---|---|
| the sheet's lines | `wc -l ui/src/app.css` | `3053 ui/src/app.css` |
| the sheet's imports | `git grep -n "css'" -- ui/src/main.ts` | `main.ts:5`, `:6`, `:7` — `styles.css`, `themes.css`, `app.css` |
| nothing in the sheet reads a path | `git grep -c -e "url(" -e "@import" -- ui/src/app.css` | nothing, exit 1 |
| the ratchet's row | `git grep -n "ui/src/app.css" -- tests/test_ratchets.py` | the row and the twin's fixture |
| no mutant names a sheet | `git grep -c "css" -- tests/mutants.json` | nothing, exit 1 |
| one comment names the sheet | `git grep -n "app\.css" -- ui README.md` | `ui/src/components/TagInput.vue:54` |

No test reads `app.css`, and vitest serves a sheet as text, so a move breaks no test but the ratchet row.

## Goals / Non-Goals

**Goals**
- The files of [D1](design.md#d1), each a span of the old sheet, and their join equal to it byte for byte.
- A guard that no file of `ui/src/css/` goes unimported.
- The documents the move makes false amended in this diff.

**Non-Goals**
- Any rule's text or order, a header comment, a linter.
- Moving a rule to the screen that wears it: [D5](design.md#d5).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the cut is the table of spans, each file named for its screen or part | a blank line falls between complete rules, so no rule is split | a cut by line count, which splits a rule |
| [D2](#d2) | `main.ts` imports each file on its own line after `themes.css`, in the order of D1 | the order is visible where the sheets load, and the cascade's order is the file order | one `index.css` of `@import`s, which hides the order |
| [D3](#d3) | the proof is the join: the files in `main.ts`'s order, joined by one newline each, equal `app.css` at the base | the bytes and the cascade are unchanged by construction, and nothing in the gate renders the page | a screenshot compare, which no gate runs |
| [D4](#d4) | the guard is a pytest structural test with a twin, `tests/test_css_files.py` | a vitest test binds through `spec(...)` and no requirement demands a sheet guard | a vitest test, which the binder refuses |
| [D5](#d5) | a rule stays in the file its span was in, and `.tile--ready` stays before `.tile` | a regrouping by screen needs the cascade's argument; a move keeps behaviour | regrouping now |
| [D6](#d6) | a decision says where the page's CSS lives; the README's tree names `css/` | a rule gets a decision, and the documents a move makes false are amended in its diff | no decision |

### D1

The files, in order. The spans are lines of `ui/src/app.css` at `7cf59b7d`; each ends on a line before a blank line, and the next starts after it.

| file | lines | first line of the span |
|---|---|---|
| `base.css` | 1-36 | `/* This application's own layout, kept apart from the token sheet in` |
| `shell.css` | 38-190 | `/* — the shell — */` |
| `dialogs.css` | 192-447 | `/* — the Render dialog (J4·1) — */` |
| `session.css` | 449-675 | `/* — the render session (J4·2, J4·3, J8b` … |
| `large.css` | 677-837 | `/* — the tile and the large view (J5·2) …` |
| `compare.css` | 839-915 | `/* — Compare: two images at equal size, …` |
| `home.css` | 917-1047 | `/* — Home — */` |
| `review.css` | 1049-1442 | `/* — collection rail — */` |
| `review-side.css` | 1444-1734 | `/* — ④ renders — */` |
| `viewer.css` | 1736-1876 | `/* — the image viewer — */` |
| `hub.css` | 1878-2049 | `/* — the hub — */` |
| `import.css` | 2051-2261 | `/* — the import sheet — */` |
| `prepare.css` | 2263-2383 | `.home__head {` |
| `keys.css` | 2385-2462 | `/* — the key list: a modal dialog, centr…` |
| `panel.css` | 2464-2522 | `/* The image panel: the viewport clips t…` |
| `place.css` | 2524-3053 | `/* — The placement screen (design spec J…` |

Each file is its lines with their newlines, nothing added: `sed -n '<first>,<last>p' ui/src/app.css > ui/src/css/<file>`. A file ends on a newline, so the join of D3 puts back the blank line the cut removed. The longest, `place.css`, is under the ceiling the ratchet holds for a file of `ui/src`.

### D2

`ui/src/main.ts` after the change:

```
import './styles.css'
import './themes.css'
import './css/base.css'
import './css/shell.css'
  … one line a file, in the order of D1 …
import './css/place.css'
```

The line `import './app.css'` goes. A vendored sheet and the theme sheet come first, as today, so every file of `css/` still follows the tokens.

### D3

The proof, run at the cut's base so it holds after the sheet is deleted. It prints `16 True`: the files `main.ts` imports under `css/`, and whether their join equals the old sheet.

```
uv run python -c "import pathlib,re,subprocess; old=subprocess.run(['git','show','7cf59b7d:ui/src/app.css'],capture_output=True,check=True).stdout; names=re.findall(r\"import '\./(css/[\w-]+\.css)'\", pathlib.Path('ui/src/main.ts').read_text()); print(len(names), b'\n'.join(pathlib.Path('ui/src', n).read_bytes() for n in names) == old)"
```

### D4

`tests/test_css_files.py` holds one pure function over a root, as `tests/test_ratchets.py` holds each of its rules:

- `css_faults(root)` reads `ui/src/main.ts` for the lines `import './css/<name>.css'` and lists a line for each file of `ui/src/css/` imported other than once, and for each import whose file is missing.
- `test_every_css_file_is_imported_by_main_once` asserts `css_faults(REPO_ROOT) == []` and that `ui/src/css/` holds a file. It carries `spec_exempt("structural: every file of ui/src/css/ is imported by main.ts once")`: no requirement of the `ui` spec demands a sheet guard, and a patch adds a scenario only under a requirement that does.
- `test_the_check_catches_an_unimported_css_file` is its twin, `spec_exempt("structural: twin of test_every_css_file_is_imported_by_main_once")`. It builds a tree under `tmp_path` that is clean, then removes one import line, imports another twice and names a missing file, and expects a fault for each.

It pins no rule: a feature stays free to edit a rule.

### D5

Each file keeps the rules its span held, including the rules an element of another screen wears. `.tile--ready` is declared before `.tile` and both sit on `ui/src/views/Hub.vue`'s tile, so the later rule overrides its border and cursor today. The order of the files keeps that, and no rule is edited. Whether the override is a defect is the person's to judge on the page.

### D6

The decision, added to `docs/decisions.md` after D59 under *Code and environment*, numbered the next free (D60 at the cut):

```
### D60 · The page's CSS is the files of ui/src/css/

**The page's own rules are the files of `ui/src/css/`, imported by `main.ts` each on its own line after `themes.css`, in the order the cascade needs. A new rule goes in its screen's file, and each file is imported once.**

- **Why:** one sheet held every screen's rules and was the largest row of the ratchet's `ui/src` table ([D56](#d56--size-and-patches-are-held-by-ratchets)). A file a screen puts a rule where a reader looks, and the order of the imports is the cascade's.
- **Accepts:** a file holds some rules another screen's element wears, and some files depend on their order. Reopen when the rules are regrouped by screen.
- **Made by:** `0149`.
```

The README's tree row for `ui/src/` gains the sentence "css/ holds the page's rules, a file a screen".

## Tests

The change adds the guard and its twin, both unit tests, and removes none. No existing test's assertion changes: `tests/test_ratchets.py` loses a table row and its count, which are data ([docs D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)).

| layer | tests added | tests removed | command |
|---|---|---|---|
| unit (pytest) | `test_every_css_file_is_imported_by_main_once` and its twin | none | `git grep -c "^def test_" -- tests/test_css_files.py` prints `tests/test_css_files.py:2` |
| browser (vitest) | none | none | `git diff --name-only main -- 'ui/src/*.test.ts'` prints nothing |
| end-to-end | none, so no run on any engine | none | `git diff --name-only main -- tests/e2e` prints nothing |

- **Why no end-to-end test:** the move changes no behaviour, and what a browser would show — the page's look — no test of the repository compares; the join is the proof (T1). The guard sits at the lowest layer that can fail, a unit test of a pure function.
- **Turned red by the change:** `tests/test_ratchets.py::test_no_big_ui_file_is_unlisted`, when the row for `ui/src/app.css` stays after the file goes. Task 1.5 removes the row.
- **Deleted or merged:** no test, so there is no table of what carries its assertions.

## Dependencies

None.

## Risks / Trade-offs

| risk | held by |
|---|---|
| a rule moves out of its place and the cascade changes | D3's join: the order and every byte are the old sheet's |
| the page renders differently and no gate sees it | the join is the proof; nothing under `ui/src` but `main.ts` and a comment changes |
| a feature adds a rule to `app.css` on a branch beside this one | it conflicts on the deleted file: a feature that shares `ui/src` rules is cut before or after this version, never beside it |
| a file is added to `ui/src/css/` and nobody imports it | D4's guard fails |
| the join's base commit leaves the history | `7cf59b7d` is on `main` and stays |

## Verdict

Ready to build. One move, one guard, one set of documents; the join is the proof of the move.
