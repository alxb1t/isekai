# The CSS's files — tasks

Move `ui/src/app.css` into the files of `ui/src/css/`, guard that each is imported, and amend the documents. The decisions are in [design](design.md).

## Progress

- [x] 1 — The move · moderate
- [x] 2 — The guard · moderate
- [ ] 3 — The documents · moderate

## 1 — The move

- [x] 1.1 **HALT CHECK** The sheet is the one the cut read: no commit since `7cf59b7d` touched `ui/src/app.css`, so the spans of [D1](design.md#d1) hold.
  Verify: `git diff --name-only 7cf59b7d -- ui/src/app.css` prints nothing.
- [x] 1.2 `mkdir -p ui/src/css`, then for each row of [D1](design.md#d1) run `sed -n '<first>,<last>p' ui/src/app.css > ui/src/css/<file>`.
  Verify: `git ls-files --others --exclude-standard ui/src/css` prints `base.css`, `compare.css`, `dialogs.css`, `home.css`, `hub.css`, `import.css`, `keys.css`, `large.css`, `panel.css`, `place.css`, `prepare.css`, `review-side.css`, `review.css`, `session.css`, `shell.css` and `viewer.css`, each under `ui/src/css/`.
- [x] 1.3 In `ui/src/main.ts` replace the line `import './app.css'` with one line `import './css/<name>.css'` per file, in the order of [D1](design.md#d1), as [D2](design.md#d2) shows.
  Verify: `uv run python -c "import pathlib,re,subprocess; old=subprocess.run(['git','show','7cf59b7d:ui/src/app.css'],capture_output=True,check=True).stdout; names=re.findall(r\"import '\./(css/[\w-]+\.css)'\", pathlib.Path('ui/src/main.ts').read_text()); print(len(names), b'\n'.join(pathlib.Path('ui/src', n).read_bytes() for n in names) == old)"` prints `16 True`.
- [x] 1.4 Delete the sheet: `git rm ui/src/app.css`.
  Verify: `git ls-files ui/src/app.css` prints nothing.
- [x] 1.5 In `ui/src/components/TagInput.vue` rewrite the comment above `DROP_TOP`: before, `/* `.drop`'s `top` in `app.css`: below opens this far under `.row__tags`' top. */`; after, the same text wrapped with `css/review-side.css` for `app.css`.
  Verify: `git grep -n "app\.css" -- ui/src/components/TagInput.vue README.md` prints nothing.
- [x] 1.6 In `tests/test_ratchets.py` remove the row `"ui/src/app.css": 3044,` from `BIG_UI_FILES`, which turns `tests/test_ratchets.py::test_no_big_ui_file_is_unlisted` green again, and set `UI_ROWS = 2`; leave `test_the_check_catches_a_big_ui_file`, whose fixture names `app.css` in a temporary tree.
  Verify: `uv run pytest tests/test_ratchets.py` exits 0.

## 2 — The guard

- [x] 2.1 Add `tests/test_css_files.py` per [D4](design.md#d4): `css_faults(root)`, the guard `test_every_css_file_is_imported_by_main_once` marked `spec_exempt("structural: every file of ui/src/css/ is imported by main.ts once")`, and its twin `test_the_check_catches_an_unimported_css_file` marked `spec_exempt("structural: twin of test_every_css_file_is_imported_by_main_once")`. The twin finds no fault in a clean tree under `tmp_path`, and one fault each for an import line removed, an import repeated and an import naming a missing file.
  Verify: `uv run pytest tests/test_css_files.py` exits 0.

## 3 — The documents

- [ ] 3.1 In `docs/decisions.md` add the decision of [D6](design.md#d6), `### D60 · The page's CSS is the files of ui/src/css/`, after D59's block and before `## Infrastructure`.
  Verify: `git grep -n "^### D60 · The page's CSS is the files" -- docs/decisions.md` prints its line.
- [ ] 3.2 In `README.md` extend the tree row for `ui/src/`: before, `# the app; styles.css is the vendored stylesheet, Inter beside it`; after, the same followed by `; css/ holds the page's rules, a file a screen`.
  Verify: `git grep -n "css/ holds the page's rules" -- README.md` prints the row.
