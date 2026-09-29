# Tasks — 0046 the terse specs

The rule, then each capability's rewrite by size, then the guard, per [design](design.md). Each rewrite phase writes
MODIFIED blocks into `openspec/changes/0046-the-terse-specs/specs/<capability>/spec.md`, per [D2](design.md#d2), and
edits that capability's `## Purpose` in place, per [D3](design.md#d3).

## Progress

- [x] 1 — The rule, and the terse capabilities
- [x] 2 — `image-generation`
- [x] 3 — `cli`
- [ ] 4 — `sheet` and `tagging`
- [ ] 5 — `caption` and `review`
- [ ] 6 — `model-provisioning`
- [ ] 7 — `run-directory`, `field-map`, and the guard

Line numbers are `9995b54`'s. `D` below is `openspec/changes/0046-the-terse-specs/specs`.

## 1 — The rule, and the terse capabilities

- [x] 1.1 **HALT CHECK** — `CLAUDE.md` states no spec rule, and the history the design names is in the specs.
  Verify: `grep -c 'How a spec reads' CLAUDE.md` prints `0`, and `grep -c '8baf2b3' openspec/specs/comfy-transport/spec.md` prints `1`.
- [x] 1.2 In `CLAUDE.md`, add *How a spec reads* after *The living spec*, per [D1](design.md#d1).
  Verify: `grep -c 'How a spec reads' CLAUDE.md` prints `1`.
- [x] 1.3 Rewrite `pod-image`, keeping [D4](design.md#d4)'s block, and `agent-skills`, per [D2](design.md#d2).
  Verify: `grep -c '^### Requirement:' openspec/changes/0046-the-terse-specs/specs/agent-skills/spec.md` prints `1`, and `grep -c 'a live pod this project named' openspec/changes/0046-the-terse-specs/specs/pod-image/spec.md` prints `1`.
- [x] 1.4 Rewrite `comfy-transport`, and delete its blockquote, per [D2](design.md#d2) and [D3](design.md#d3).
  Verify: `grep -c '^>' openspec/specs/comfy-transport/spec.md` prints `0`, and `grep -c '8baf2b3' openspec/specs/comfy-transport/spec.md` prints `0`.

## 2 — `image-generation`

- [x] 2.1 Rewrite `image-generation`, per [D2](design.md#d2) and [D3](design.md#d3).
  Verify: `grep -c -E 'v0\.[0-9]+' openspec/changes/0046-the-terse-specs/specs/image-generation/spec.md` prints `0`, and `test "$(grep -c '^### Requirement:' openspec/changes/0046-the-terse-specs/specs/image-generation/spec.md)" -ge 1 && echo ok` prints `ok`.

## 3 — `cli`

- [x] 3.1 Rewrite `cli`, per [D2](design.md#d2) and [D3](design.md#d3).
  Verify: `grep -c -E 'v0\.[0-9]+' openspec/changes/0046-the-terse-specs/specs/cli/spec.md` prints `0`, and `test "$(grep -c '^### Requirement:' openspec/changes/0046-the-terse-specs/specs/cli/spec.md)" -ge 1 && echo ok` prints `ok`.

## 4 — `sheet` and `tagging`

- [ ] 4.1 Rewrite `sheet` and `tagging`, per [D2](design.md#d2) and [D3](design.md#d3).
  Verify: `ls openspec/changes/0046-the-terse-specs/specs/sheet/spec.md openspec/changes/0046-the-terse-specs/specs/tagging/spec.md` lists both, and `cat openspec/changes/0046-the-terse-specs/specs/sheet/spec.md openspec/changes/0046-the-terse-specs/specs/tagging/spec.md | grep -c -e 'used to' -e 'this version'` prints `0`.

## 5 — `caption` and `review`

- [ ] 5.1 Rewrite `caption` and `review`, per [D2](design.md#d2) and [D3](design.md#d3).
  Verify: `ls openspec/changes/0046-the-terse-specs/specs/caption/spec.md openspec/changes/0046-the-terse-specs/specs/review/spec.md` lists both, and `cat openspec/changes/0046-the-terse-specs/specs/caption/spec.md openspec/changes/0046-the-terse-specs/specs/review/spec.md | grep -c -e 'used to' -e 'Until now'` prints `0`.

## 6 — `model-provisioning`

- [ ] 6.1 Rewrite `model-provisioning`, and delete its `</content>` line, per [D2](design.md#d2) and [D3](design.md#d3).
  Verify: `grep -c '</content>' openspec/specs/model-provisioning/spec.md` prints `0`, and `test "$(grep -c '^### Requirement:' openspec/changes/0046-the-terse-specs/specs/model-provisioning/spec.md)" -ge 1 && echo ok` prints `ok`.

## 7 — `run-directory`, `field-map`, and the guard

- [ ] 7.1 Rewrite `run-directory` and `field-map`, per [D2](design.md#d2) and [D3](design.md#d3).
  Verify: `ls openspec/changes/0046-the-terse-specs/specs/run-directory/spec.md openspec/changes/0046-the-terse-specs/specs/field-map/spec.md` lists both, and `grep -c 'first implementation' openspec/changes/0046-the-terse-specs/specs/run-directory/spec.md` prints `0`.
- [ ] 7.2 Write `tests/test_spec_prose.py` over the effective spec, with a twin per rule, per [D5](design.md#d5).
  Verify: `grep -c -e '^def test_no_spec_names_a_version_change_or_commit' -e '^def test_no_spec_line_passes_120_characters' tests/test_spec_prose.py` prints `2`.
