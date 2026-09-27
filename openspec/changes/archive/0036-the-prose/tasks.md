# Tasks — 0036 the prose

The sweep first, then the docs, the scripts' messages, and the graph's placeholder — each phase prose, comments, messages and an
inert value, per [design](design.md).

## Progress

- [x] 1 — The sweep
- [x] 2 — The docs
- [x] 3 — The scripts' messages
- [x] 4 — The graph's placeholder

Line numbers are `7aa23d3`'s; find each site by the text [design](design.md) names. `.minions/prose-terms.txt` is
the term list per [D3](design.md#d3).

## 1 — The sweep

- [x] 1.1 **HALT CHECK** — the term list hits the archived changes and the changelog, and `FILED`, `SEEDS` and
  `PRECEDENCE` hold what they held at the cut.
  Verify: `git ls-files '*.md' | xargs grep -wiIl -F -f .minions/prose-terms.txt | grep -c .` prints `11`, and
  `uv run python -c "import json,hashlib; from tools import derive_field_map as m; print(hashlib.sha256(json.dumps([m.FILED, m.SEEDS, m.PRECEDENCE], sort_keys=True, default=sorted).encode()).hexdigest()[:16])"` prints `b8f6544393739af5`.
- [x] 1.2 Rewrite archived `0018`'s `design.md:573` and `tasks.md:281`, and `0020`'s `design.md:86`, per [D1](design.md#d1).
  Verify: `cat openspec/changes/archive/0018-review-ui/design.md openspec/changes/archive/0018-review-ui/tasks.md openspec/changes/archive/0020-readable-caption/design.md | grep -wicF -f .minions/prose-terms.txt` prints `0`.
- [x] 1.3 Rewrite archived `0021`'s lines [D1](design.md#d1) lists, in `design.md`, `proposal.md`, `specs/sheet/spec.md` and `tasks.md`, the per-tag counts included.
  Verify: `cat openspec/changes/archive/0021-sheet-from-the-tagger/*.md openspec/changes/archive/0021-sheet-from-the-tagger/specs/sheet/spec.md | grep -wicF -f .minions/prose-terms.txt` prints `0`, and `cat openspec/changes/archive/0021-sheet-from-the-tagger/*.md | grep -c -e 'hair ×' -e 'realistic ×'` prints `0`.
- [x] 1.4 Rewrite archived `0025`'s `design.md:20, 23, 25`, `proposal.md:11, 35` and `tasks.md:46, 49, 56`, per [D1](design.md#d1).
  Verify: `cat openspec/changes/archive/0025-running-the-flow/*.md | grep -wicF -f .minions/prose-terms.txt` prints `0`.
- [x] 1.5 Rewrite `CHANGELOG.md`'s lines [D1](design.md#d1) lists, the per-tag counts included.
  Verify: `grep -wicF -f .minions/prose-terms.txt CHANGELOG.md` prints `0`, `grep -c -e 'hair ×' -e 'lips. twice' CHANGELOG.md` prints `0`, and `git ls-files '*.md' | xargs grep -wiIl -F -f .minions/prose-terms.txt` prints nothing.
- [x] 1.6 Rewrite `tools/derive_field_map.py`'s comments at `:70-75` and `:207-211` and the `inflect()` docstring at `:369-375`, per [D2](design.md#d2); no other line changes.
  Verify: `grep -c -e 'load-bearing' -e 'brown hair. x5' tools/derive_field_map.py` prints `0`; `uv run python -c "import ast,tokenize as k,pathlib as l;F=[*l.Path('tools').rglob('*.py'),*l.Path('isekai').rglob('*.py')];[print(t.string) for p in F for t in k.generate_tokens(open(p).readline) if t.type==k.COMMENT];[print(ast.get_docstring(n)) for p in F for n in ast.walk(ast.parse(open(p).read())) if isinstance(n,(ast.Module,ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and ast.get_docstring(n)]" | grep -wiF -f .minions/prose-terms.txt` prints nothing; and 1.1's digest command still prints `b8f6544393739af5`.

## 2 — The docs

- [x] 2.1 Add D33 to `docs/decisions.md` under `## The product`, after D30, with the text [D4](design.md#d4) gives verbatim.
  Verify: `grep -c '^### D33 · The operator decides what is rendered' docs/decisions.md` prints `1`.
- [x] 2.2 Edit `docs/pins.md` per [D5](design.md#d5): `:42`'s *pinned by*, `:88`'s *what stands in*, the *Not pinned* rows after `:90`, and `:26`'s *where it stops*.
  Verify: `grep -c -e "the reader alias's template" -e "the build tools of the image's sdist-only packages" -e 'borrows .runpod_pod_image' -e "the alias's model and projector layers are checked" docs/pins.md` prints `4`, and `grep -c 'a lock with every hash; Python by patch' docs/pins.md` prints `0`.

## 3 — The scripts' messages

- [x] 3.1 **HALT CHECK** — `lost()` still sends teardown to the MCP.
  Verify: `grep -c 'delete-pod' infra/up.sh` prints `1`.
- [x] 3.2 Rewrite `infra/up.sh`'s `lost()` and `infra/down.sh:16` per [D6](design.md#d6).
  Verify: `grep -c 'delete-pod' infra/up.sh` prints `0`, `grep -c 'list-pods' infra/up.sh` prints `1`, and `cat infra/up.sh infra/down.sh | grep -c 'write its id to .runpod_pod_id'` prints `2`.
- [x] 3.3 In `tests/test_infra.py`'s `test_the_timeout_teardown_resolves_from_the_root_the_script_moved_to`, make the teardown line's filter `not line.lstrip().startswith(("#", "echo"))`, per [D6](design.md#d6).
  Verify: `grep -cF 'startswith(("#", "echo"))' tests/test_infra.py` prints `1`.
- [x] 3.4 Add the `rm` line to `infra/down.sh`'s other-status branch, before its `exit 1`, per [D6](design.md#d6).
  Verify: `grep -c 'Once the RunPod MCP confirms it gone: rm .runpod_pod_id .runpod_pod_image' infra/down.sh` prints `1`.
- [x] 3.5 Rewrite `infra/render.sh`'s port refusal at `:46-47` per [D6](design.md#d6).
  Verify: `grep -c 'lsof -t' infra/render.sh` prints `0`, and `grep -cF "pkill -f -- '-L 8188:localhost:8188'" infra/render.sh` prints `1`.

## 4 — The graph's placeholder

- [x] 4.1 **HALT CHECK** — the summon flow still holds its timestamped placeholder, pinned at the cut's digest.
  Verify: `grep -c '"image": "photo_' flows/summon-anime-wai/graph.json` prints `1`, and `grep -c 039a1a80f2b43069e8e1bffcc4e1665417c4aa73e1c2f40fca783379c351669b tests/test_flow.py` prints `1`.
- [x] 4.2 Set `flows/summon-anime-wai/graph.json:13`'s `LoadImage` `image` to `photo.jpeg`, per [D7](design.md#d7).
  Verify: `grep -c '"image": "photo_' flows/summon-anime-wai/graph.json` prints `0`, and `grep -c '"image": "photo.jpeg"' flows/summon-anime-wai/graph.json` prints `1`.
- [x] 4.3 Re-pin per [D7](design.md#d7): `PINNED`'s `summon-anime-wai` digest in `tests/test_flow.py`, the `flow_digest` in `tests/golden/{sheet,sheet-empty,prompt,render}.json`, and `render.json`'s `flow_graph_sha256`.
  Verify: `cat tests/test_flow.py tests/golden/sheet.json tests/golden/sheet-empty.json tests/golden/prompt.json tests/golden/render.json | grep -c -e 039a1a80f2b43069 -e ed7f29827fff1612` prints `0`.
- [x] 4.4 Add `test_the_graph_placeholder_never_reaches_a_submitted_graph` to `tests/test_generate.py`, `spec_exempt`, per [D7](design.md#d7).
  Verify: `grep -c '^def test_the_graph_placeholder_never_reaches_a_submitted_graph' tests/test_generate.py` prints `1`.
