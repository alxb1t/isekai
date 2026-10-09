# Design — 0057 the removed key

The key set a `spec` marker may name: the living spec's and the effective spec's together.
**Verdict: feasible** — one function, one fixture, one twin.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `ac22bdf`:

- **`spec_keys`** (`tests/test_spec_bindings.py:25-32`) reads the living spec as the open deltas leave it.
  **`living_keys`** (`:35-41`) reads `openspec/specs/` alone. **`demanded`** (`:44-50`) is their intersection.
- **`unknown`** (`:151-157`) lists each marker whose key is not in the set it is given. The `keys` fixture
  (`:170-173`) gives it `spec_keys(REPO_ROOT)`, and `test_every_marker_names_a_key` (`:194-197`) fails on any.
- **Probed on `main`:** a throwaway delta removing `pod-image`'s *No `isekai` pod goes unseen* failed
  `test_every_marker_names_a_key` on every reconcile test. The probe was deleted.
- **The twins** (`:247-417`) build a tree with `_tree` (`:238-244`): `_LIVING` holds `cap:kept:kept` and
  `cap:gone:gone`, `_TESTS` marks a test for each.

## Goals / Non-Goals

**Goals:** a removal is green at its cut; a stray marker on a key in neither set still fails.

**Non-Goals:** a change to `demanded`, to `unbound`, or to how a delta is read.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `nameable(root) = spec_keys(root) \| living_keys(root)`; the `keys` fixture returns it | a living key is still real until the release archives the delta | skipping the check while a change is open |
| [D2](#d2) | one twin: `_TESTS` against a delta that REMOVES `Gone`, where `test_gone` keeps its marker | it pins both halves: removed is nameable, unknown is not | a twin per delta kind |

### D1

```python
def nameable(root: Path) -> set[str]:
    """Return the keys a marker may name: the living ones, and the active deltas'."""
    return spec_keys(root) | living_keys(root)
```

The `keys` fixture returns `nameable(REPO_ROOT)`. The module docstring's "each `spec` marker names a key" becomes
"each `spec` marker names a key the living spec or an open delta holds".

### D2

`test_a_marker_on_a_removed_key_is_not_stray`, marked `spec_exempt("structural: twin of
test_every_marker_names_a_key")`. Its tree is `_TESTS` with the delta `## REMOVED Requirements` / `### Requirement:
Gone`. It asserts `unknown(nameable(root), marked_tests(root)) == []`, `unknown(spec_keys(root), …)` names
`test_gone`, and a marker on `cap:nowhere:x` is still caught by `nameable`.

## Dependencies

None.

## Risks / Trade-offs

- **A marker on a removed key outlives the build** → once the release archives the delta, the key leaves the
  living spec and `test_every_marker_names_a_key` fails at the release's gate.

## Verdict

Feasible: one function and one twin.
