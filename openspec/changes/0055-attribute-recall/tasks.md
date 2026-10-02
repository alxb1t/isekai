# Tasks — 0055 attribute recall

The arithmetic, the reader, the command, then the records, per [design](design.md). The deltas hold every new
scenario; each task below adds the tests that bind them.

## Progress

- [ ] 1 — The arithmetic
- [ ] 2 — The reader
- [ ] 3 — The command
- [ ] 4 — The records

Line numbers are `73f45f4`'s. Every new test carries `@pytest.mark.spec` with the key its task names.

## 1 — The arithmetic

- [ ] 1.1 **HALT CHECK** — no code reads `scored`, the tagger's floor is `0.15`, and no recall module exists.
  Verify: `grep -rn 'schema\.scored' isekai evaluation tools --include='*.py' | wc -l` prints `0`, `grep -c '^FLOOR = 0.15' isekai/boundary/wd14.py` prints `1`, and `test ! -e evaluation/recall.py && echo none` prints `none`.
- [ ] 1.2 Write the pure half of `evaluation/recall.py`: `count`, `totals`, `record` and `table`, per [D1](design.md#d1).
  Verify: `grep -cE '^def (count|totals|record|table)\(' evaluation/recall.py` prints `4`.
- [ ] 1.3 Add `tests/test_recall.py` and the pair `tests/recall/recall.json`, `tests/recall/recall.txt`, binding `evaluation:recall:a-missed-tag-is-named`, `evaluation:recall:only-scored-fields-are-counted` and `evaluation:recall:the-table-re-derives-from-the-record`, on tag sets written by hand.
  Verify: `grep -c 'pytest.mark.spec("evaluation:recall:' tests/test_recall.py` prints `3`, and `ls tests/recall` prints `recall.json` and `recall.txt`.

## 2 — The reader

- [ ] 2.1 **HALT CHECK** — the tagger reads `brown hair` from a real render at its own floor.
  Verify: `uv run python -c "import glob,pathlib;from isekai.boundary import wd14;from isekai.shared.vocabulary import normalise;t=wd14.open_session();p=pathlib.Path(glob.glob('.data/v0.30.1/runs/28c3bb7ce031*/summon-anime-wai/outputs/001/*.png')[0]);print('brown hair' in {normalise(s.tag) for s in wd14.scored(p,t.session,t.labels)})"` prints `True`.
- [ ] 2.2 Add `Read` and `_reader` to `evaluation/recall.py`, per [D2](design.md#d2): `wd14.open_session`, `wd14.scored` at the default floor, `normalise`, and a file that does not decode refused by name.
  Verify: `grep -c '^def _reader(' evaluation/recall.py` prints `1`, and `grep -c 'wd14.scored(' evaluation/recall.py` prints `1`.
- [ ] 2.3 Add to `tests/test_recall.py` a test binding `evaluation:recall:a-tag-read-back-is-counted`, with `fake_tagger` from `tests/stages.py`: a tag at or above the floor is read back in the sheet's spelling, one below it is not.
  Verify: `grep -c 'evaluation:recall:a-tag-read-back-is-counted' tests/test_recall.py` prints `1`.

## 3 — The command

- [ ] 3.1 Write `evaluation/record.py` with `destination(runs, name)`, its refusal ending in the move and "then this command again" per [D3](design.md#d3); make `evaluation/__main__.py` call it with `"evaluation.json"` and drop `_destination`.
  Verify: `grep -c '^def destination(' evaluation/record.py` prints `1`, `grep -c 'give a runs directory' evaluation/__main__.py evaluation/record.py | grep -c ':0'` prints `2`, and `grep -c 'then this command again' evaluation/record.py` prints `1`.
- [ ] 3.2 Add `main`, the run narrowing and the row loop to `evaluation/recall.py`, per [D3](design.md#d3), with the `python -m evaluation.recall` entry.
  Verify: `grep -c '^def main(' evaluation/recall.py` prints `1`, and `grep -c '"recall.json"' evaluation/recall.py` prints `1`.
- [ ] 3.3 Add `tests/test_recall_cli.py` binding `evaluation:recall:every-render-is-a-row`, `evaluation:recall:an-unreadable-render-is-a-row`, `evaluation:recall:a-render-without-its-approval-is-a-row`, `evaluation:recall:named-runs-narrow-the-reading`, `evaluation:recall:the-record-names-the-tagger-and-its-floor` and `evaluation:recall:a-record-git-can-reach-is-refused`, on a batch under `tmp_path` with a fake reader.
  Verify: `grep -c 'pytest.mark.spec("evaluation:recall:' tests/test_recall_cli.py` prints `6`.

## 4 — The records

- [ ] 4.1 In `evaluation/__main__.py`, rank the first seed of the latest render group, per [D4](design.md#d4); add to `tests/test_evaluation_cli.py` a test binding `evaluation:table:the-latest-group-is-ranked`.
  Verify: `grep -c 'evaluation:table:the-latest-group-is-ranked' tests/test_evaluation_cli.py` prints `1`, and `grep -c 'renders\[0\], renders\[1:\]' evaluation/__main__.py` prints `0`.
- [ ] 4.2 In `docs/decisions.md`, add D39 after D37 per [D2](design.md#d2).
  Verify: `grep -c "^### D39 · Attribute recall uses the sheet's tagger" docs/decisions.md` prints `1`.
- [ ] 4.3 In `evaluation/README.md`, add the recall command, `recall.py` and `record.py` to *Files* and *Imported by*; rewrite `openspec/specs/evaluation/spec.md:3-11` to carry recall in *Purpose*, *Source* and *Tests*, per [D5](design.md#d5).
  Verify: `grep -c 'evaluation.recall' evaluation/README.md` prints a number above `0`, and `grep -c 'evaluation/recall.py' openspec/specs/evaluation/spec.md` prints `1`.
- [ ] 4.4 Close the cards of [D5](design.md#d5) that are edits: rename the test at `tests/test_cohort.py:63`; add `tests/test_evaluation_cli.py` to `provision.py`'s importers and `evaluation/recall.py` to `wd14.py`'s in `isekai/boundary/README.md`; write "every tracked flow names the same one" at `README.md:19`.
  Verify: `grep -c 'outside_the_cohort_is_listed' tests/test_cohort.py` prints `0`, `grep -c 'test_evaluation_cli' isekai/boundary/README.md` prints `1`, `grep -c 'evaluation/recall.py' isekai/boundary/README.md` prints `1`, and `grep -c 'both tracked flows' README.md` prints `0`.
