# Tasks — 0084 flat summon

The candidates, the operator's photographs, the sheets, the render and count, the verdict, then the winner, per
[design](design.md). The prototype is the directory `.data/flat-summon-prototype/`; in a shell,
`C=.data/flat-summon-prototype; R="$C/runs"; P=("$C"/sources/*)`.

```
.data/flat-summon-prototype/
  sources/<person>-<n>.<ext>  the operator's, by hand
  cohort/<person>/<photo>     the same files, by person, for the evaluator
  runs/                       assign … render
  sessions/                 render's record
  evaluation.json           the cohort count
  compare.html              each photograph beside its renders
```

## Progress

- [x] 1 — The candidate flows
- [x] 2 — The prototype photographs **HUMAN
- [x] 3 — The sheets
- [x] 4 — The render and the count ⚠️ GPU
- [x] 5 — The verdict **HUMAN
- [ ] 6 — The winner

## 1 — The candidate flows

- [x] 1.1 **HALT CHECK** — summon's graph runs InstantID to the end.
  Verify: `python3 -c "import json;print(json.load(open('flows/summon-anime-wai/graph.json'))['8']['inputs']['end_at'])"` prints `1`.
- [x] 1.2 Add `flows/summon-flat-a-anime-wai/` per [D1](design.md#d1) and `flows/summon-flat-b-anime-wai/` per
  [D2](design.md#d2); pin both in `PINNED`, add `FLATS` and bind the three `image-generation:flat:` keys in
  `tests/test_flow.py` per [D3](design.md#d3); `config/ui.json` stays as it is.
  Verify: `grep -c 'image-generation:flat:' tests/test_flow.py` prints `3`, and `grep -c 'summon-flat' config/ui.json` prints `0`, and `uv run pytest -q tests/test_flow.py` exits 0.

## 2 — The prototype photographs **HUMAN

- [x] 2.1 The operator puts fifteen photographs of five people, three each, under
  `.data/flat-summon-prototype/sources/`, each named `<person>-<n>.<ext>`.
  Verify: `ls .data/flat-summon-prototype/sources | wc -l` prints `15`.

## 3 — The sheets

- [x] 3.1 Assign the three flows: `uv run python -m isekai assign --runs "$R" --flow summon-anime-wai --flow
  summon-flat-a-anime-wai --flow summon-flat-b-anime-wai "${P[@]}"`.
  Verify: `ls -d .data/flat-summon-prototype/runs/*/summon-flat-b-anime-wai | wc -l` prints `15`.
- [x] 3.2 Fill, correct and approve summon's sheets: `uv run python -m isekai.boundary.provision fetch
  config/reader.json`, then `tag`, `sheet` and `review` as `uv run python -m isekai tag --runs "$R" --flow
  summon-anime-wai "${P[@]}"`; edit each draft against its photograph per [D4](design.md#d4); then `approve`.
  Verify: `ls .data/flat-summon-prototype/runs/*/summon-anime-wai/review/001.approved.json | wc -l` prints `15`.
- [x] 3.3 Copy them: `uv run python -m isekai approve --runs "$R" --flow summon-flat-a-anime-wai --flow
  summon-flat-b-anime-wai --from summon-anime-wai "${P[@]}"`.
  Verify: `ls .data/flat-summon-prototype/runs/*/summon-flat-b-anime-wai/review/001.approved.json | wc -l` prints `15`.

## 4 — The render and the count ⚠️ GPU

- [x] 4.1 Open the volume, render the three on summon's seeds in one session, close the volume:
  `uv run --env-file .env gpunit volume up --yes`; `uv run python -m isekai render "$R" summon-anime-wai=1
  summon-flat-a-anime-wai=summon-anime-wai summon-flat-b-anime-wai=summon-anime-wai`;
  `uv run --env-file .env gpunit volume down`.
  Verify: `ls .data/flat-summon-prototype/runs/*/summon-flat-b-anime-wai/outputs/001/*.png | wc -l` prints `15`, and `test -e .gpunit/pod; echo $?` prints `1`.
- [x] 4.2 Count and lay out the renders: `for f in "${P[@]}"; do b=$(basename "$f"); mkdir -p "$C/cohort/${b%%-*}";
  cp "$f" "$C/cohort/${b%%-*}/"; done`, `uv run python -m evaluation "$R" --cohort "$C/cohort"`, then
  `uv run python -m isekai compare "$C"`.
  Verify: `ls .data/flat-summon-prototype/evaluation.json .data/flat-summon-prototype/compare.html | wc -l` prints `2`.

## 5 — The verdict **HUMAN

- [x] 5.1 The operator judges the three flows by eye in `.data/flat-summon-prototype/compare.html`, then writes
  `openspec/changes/0084-flat-summon/verdict.md` per [D5](design.md#d5): a line
  `winner: summon-flat-a-anime-wai`, `winner: summon-flat-b-anime-wai` or `winner: none`, and each flow's count.
  Verify: `grep -cE '^winner: (summon-flat-a-anime-wai|summon-flat-b-anime-wai|none)$' openspec/changes/0084-flat-summon/verdict.md` prints `1`.

## 6 — The winner

- [ ] 6.1 **HALT CHECK** — a candidate won; on `winner: none` the build halts and the operator destroys the branch.
  Verify: `grep -cE '^winner: summon-flat-[ab]-anime-wai$' openspec/changes/0084-flat-summon/verdict.md` prints `1`.
- [ ] 6.2 Move the winner to `flows/summon-flat-anime-wai/` with its identifier, delete the loser, and name the winner
  alone in `PINNED` and `FLATS` (`tests/test_flow.py`), per [D6](design.md#d6).
  Verify: `ls flows | grep -c 'summon-flat-[ab]-anime-wai'` prints `0`, and `test -d flows/summon-flat-anime-wai; echo $?` prints `0`, and `uv run pytest -q tests/test_flow.py` exits 0.
- [ ] 6.3 Add D44 to `docs/decisions.md`, and name `summon-flat-anime-wai` in `AGENTS.md`'s flows and `README.md`'s
  tree, per [D6](design.md#d6).
  Verify: `grep -c '### D44 · A flat flow is summon with the face chain ending early' docs/decisions.md` prints `1`, and `grep -c 'summon-flat-anime-wai' AGENTS.md README.md` prints a number of at least `1` for each file.
