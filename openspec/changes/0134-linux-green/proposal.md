---
bump: patch
---

# Linux green

`main` is red on Linux because tests hold what only the Mac produces; each cause is fixed where it lies, and each fix has a twin that holds on any machine.

Reading map: [design](design.md) holds the causes, each fix and the test cost, [tasks](tasks.md) holds the phases: the edge, the digests, the interpreter.

## Why

CI runs Linux and the Mac runs macOS: the chain's sampler reads a point 3e-15 px past the ink's edge as outside on OpenBLAS and inside on Accelerate. The PNG digests in the edit golden and the run's record hold bytes that zlib-ng and stock zlib deflate differently. The verbs' record holds `required` for a positional, which argparse changed in Python 3.12.7, and CI runs the system's 3.12.3.

```
 chain       OpenBLAS vs Accelerate      y = -3e-15 -> transparent white     phase 1  product + test
 digests     zlib vs zlib-ng             PNG bytes differ, pixels do not     phase 2  tests
 verbs       Python 3.12.3 vs 3.12.14    nargs="*" required: True vs False   phase 3  pin + test
```

## What Changes

- **The edge.** `_sample` in `isekai/shared/chain.py` takes a point within 1e-9 px of the ink's edge as on it, under the requirement *Ink is placed by thin-plate splines*. A test puts a point a hair outside each edge and a point past the tolerance.
- **The digests.** The edit golden and the run's record check each PNG digest against its file's bytes, then compare a placeholder. A twin deflates the same pixels at another level.
- **The interpreter.** `.python-version` is `3.12.14`. The verbs' record names an action by its kind, not by argparse's private class.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `tattoo`: the requirement *Ink is placed by thin-plate splines* gains one scenario, *a point a hair past the edge is on it*. Its SHALL paragraph is as it was; its why paragraph says the tolerance.

## Impact

- `isekai/shared/chain.py`: a constant and the `inside` test of `_sample`, and its docstring.
- `tests/test_chain.py`, `tests/test_artifact_bytes.py`, `tests/golden/edit.json`, `tests/record.py`, `tests/test_record.py`, `tests/record/run.json`, `tests/record/verbs.json`.
- `.python-version`.
- No format version moves, no verb or flag changes, and the product's output is the same for every input a platform computes alike: this meets each condition of a patch in [CONTRIBUTING](../../../CONTRIBUTING.md#how-a-change-lands).

## Not in this change

- A Linux run before a merge, or a step that runs the browser tests before one; CI is read after the merge.
- A deterministic PNG encoder for the product: the files travel as bytes and are never re-encoded.
- A pin of the Python patch in the pod image; the image's `.python-version` is frozen.
- The paydown: the mutation runner and its replay, the audit's mutants, the patch scanner and the prose cards.
