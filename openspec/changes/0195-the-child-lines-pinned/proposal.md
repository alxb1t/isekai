---
bump: patch
after: [0194-the-onnx-opener]
---

# The child lines pinned

Tests alone: the bytes of every JSON line a child prints, key order included, and a read-back from emitter to parser.

Reading map: [design](design.md) holds the decisions and the sample table, [tasks](tasks.md) its phases: the samples, then the read-back.

## Why

A child prints item lines, and a render session prints step and image lines; the app and the session read them back. Each is held only as a parsed dict, so a changed key order, separator or flush passes every test. The next version declares the shapes once and builds the lines from that declaration, and its proof is that every line stays byte-equal, so the bytes are pinned first.

## What Changes

- `tests/test_progress.py` holds the bytes of the item line: start, done, refused, a photograph's line naming no flow, a render's and an edit's.
- It holds the bytes of the session's step and image lines, and that each line is flushed.
- It reads each kind back through `progress_line`, and a render line through `_Images` into the session's image line.

No requirement is touched.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

Only `tests/test_progress.py` changes, by added tests. No existing test's assertion changes.

## Not in this change

- A record file: the line samples are a person's run, so they stay in a test.
- The declaration of the lines, and moving `Steps`, `_Images` and `progress_line`: the next version's.
- A test through the app's readers in `isekai/interface/ui/jobs.py`: `tests/test_ui_jobs.py` holds them on recorded lines.
- A scenario or a spec delta.
