# The vocabulary refusal — tasks

The case and the refusal land together, then the documents they make true ([D4](design.md#d4)).

## Progress

- [x] 1 — The refusal and its case · moderate
- [x] 2 — The documents · moderate

## 1 — The refusal and its case

- [x] 1.1 Before any edit, run `grep -n -e "^def load_vocabulary(" -e "^def wiring_from(" isekai/interface/wiring.py`, which prints the line of each def. Run `uv run python -m tools.mutate isekai/interface/wiring.py:<first>-<second minus 1> --tests tests/test_vocabulary_manifest.py tests/test_vocabulary.py`. Put its summary in the phase's commit body, each survivor listed as the baseline with its operator and the text of its line ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_vocabulary_manifest.py tests/test_vocabulary.py -q` exits 0.
- [x] 1.2 In `tests/test_vocabulary_manifest.py`, after `test_an_unprovisioned_vocabulary_refuses_naming_the_command`, add `def test_a_label_index_whose_bytes_differ_is_refused_naming_the_fetch`, the case of [Tests](design.md#tests), verbatim.
  Verify: `git grep -c -F "def test_a_label_index_whose_bytes_differ_is_refused_naming_the_fetch" -- tests/test_vocabulary_manifest.py` prints the path and `1`.
- [x] 1.3 **HALT CHECK** The case fails before the fix, naming the raw mismatch. It passes: the defect is not where [Context](design.md#context) puts it. Put the red run in the phase's commit body.
  Verify: `uv run pytest tests/test_vocabulary_manifest.py -k label_index_whose_bytes -q` exits 1 and prints `DigestMismatch`.
- [x] 1.4 In `isekai/interface/wiring.py`, add the `except DigestMismatch as altered:` clause of [D1](design.md#d1) after `except FileNotFoundError` in `load_vocabulary`'s `try`.
  Verify: `git grep -c -F "except DigestMismatch as altered" -- isekai/interface/wiring.py` prints the path and `1`.
- [x] 1.5 In `load_vocabulary`'s docstring, replace the sentence, across a line break, that holds `rather than at module scope, so it stays off` and ends at `import graph.` with the text of [D3](design.md#d3), and add its sentence on bytes that differ after the sentence on the digest check.
  Verify: `git grep -c -F "so it stays off" -- isekai/interface/wiring.py` prints nothing.
- [x] 1.6 The case passes, and so do the tests the change reaches.
  Verify: `uv run pytest tests/test_vocabulary_manifest.py tests/test_wd14.py tests/test_pipeline_cli.py tests/test_layers.py tests/test_docs.py tests/test_spec_bindings.py tests/test_spec_prose.py -q` exits 0.
- [x] 1.7 The standing mutant BD-1b still finds its text once: the module holds no second `except DigestMismatch as swapped`. This holds before the edit too, and guards a rename.
  Verify: `git grep -n -c -F "except DigestMismatch as swapped" -- isekai/interface/wiring.py` prints the path and `1`.
- [x] 1.8 Run task 1.1's commands again over the new lines, with the range they print now. Match a survivor to the baseline by its operator and the text of its line, since the new clause shifts the numbers. One the baseline does not list is killed by an assertion added to the case of task 1.2. When a mutant is equivalent and no assertion can kill it, name it equivalent in the commit body ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_vocabulary_manifest.py tests/test_vocabulary.py -q` exits 0.

## 2 — The documents

- [x] 2.1 In `docs/principles.md`, in the bullet *Known breaks* of *Only a front end composes*, change `a missing or undeclared vocabulary` to `a missing, undeclared or altered vocabulary`, re-wrapping the lines it spans and keeping `undeclared or altered vocabulary` on one line.
  Verify: `git grep -c -F "undeclared or altered vocabulary" -- docs/principles.md` prints the path and `1`.
- [x] 2.2 Replay the standing mutants, which exits 0 with no survivor.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
