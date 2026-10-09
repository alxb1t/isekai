---
version: v0.34.2
---

# 0057 — the removed key

A cut that removes a requirement keeps the gate green until its build deletes the tests. The spec↔test checker lets a
`spec` marker name a key the living spec still holds while an open delta removes it.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the key set a marker may name, and the twin |
| [tasks](tasks.md) | the one phase |

## Why

**A cut that removes a requirement is red.** `test_every_marker_names_a_key` reads the keys as the open deltas leave
them, so the tests of a REMOVED requirement name keys that no longer exist. A cut may touch nothing outside its
change directory, so it cannot delete those tests, and it must leave the gate green. A MODIFIED requirement that drops
a scenario does the same.

**The next change removes keys.** The move of the pod's lifecycle to gpunit retires the `pod-image` requirements gpunit
now holds.

## What Changes

- **A `spec` marker may name a key in the living spec or in the effective spec** ([D1](design.md#d1)).
- **A twin proves it:** a marker on a key an open delta removes is not stray; a marker on a key in neither still is
  ([D2](design.md#d2)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The checker is a structural test; no requirement changes.

## Impact

- **Files:** `tests/test_spec_bindings.py`.
- **Behaviour:** none of the product's. A cut that removes keys is green; a test the build forgets fails once the
  release archives the delta.
- **Dependencies:** none ([Dependencies](design.md#dependencies)).

## Not in this change

- **What a key demands** — `demanded` already reads both sets.
- **The archive** — still not read.
- **Any spec.**
