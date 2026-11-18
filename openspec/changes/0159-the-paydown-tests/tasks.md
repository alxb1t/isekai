# The paydown tests — tasks

The phases close the cards of `debt:` with tests, a scenario split, red runs kept as mutants and checks that edit nothing; no line under `isekai/` or `ui/src/` changes.

## Progress

- [x] 1 — The foreign Host, the upload and the CSS guard · moderate
- [ ] 2 — The third format's own scenario · moderate
- [ ] 3 — The red runs, kept as mutants · moderate
- [ ] 4 — The cards that close on a check · moderate

## 1 — The foreign Host, the upload and the CSS guard

- [x] 1.1 In `tests/test_ui_api.py`, at the end of `test_a_request_carrying_someone_elses_host_is_refused`, add `looked = client.get(_at(made), headers={"host": f"evil.example:{PORT}"})`, then `assert looked.status_code == 403` and `assert looked.json() == {"refusal": "not addressed here"}` ([D1](design.md#d1)). Its name, key and lines stay.
  Verify: `git grep -n -F "looked = client.get(_at(made), headers=" -- tests/test_ui_api.py` prints one line.
- [x] 1.2 In `tests/test_ui_api.py`, add `from starlette.requests import Request  # noqa: E402` after the `TestClient` import ([D2](design.md#d2)). In `test_an_upload_past_its_declared_length_is_refused_before_its_body_is_read`, define `unread(*_args: object, **_keywords: object) -> bytes`, which raises `AssertionError("the request's body was read")`, and add `monkeypatch.setattr(Request, "body", unread)` after the patch of `Reader.put`. Its other patches and assertions stay.
  Verify: `git grep -n -F 'monkeypatch.setattr(Request, "body", unread)' -- tests/test_ui_api.py` prints one line.
- [x] 1.3 In `tests/test_css_files.py`, after the `missing` block of `test_the_check_catches_an_unimported_css_file`, add the trees `commented` and `after_a_line`, each built by `_tree`: `commented`, whose `main.ts` is `"import './css/a.css'\n/*\nimport './css/b.css'\n*/\nimport './css/c.css'\n"`, asserted `css_faults(commented) == ["b.css imported 0 times"]`; and `after_a_line`, whose `main.ts` is `"import './css/a.css'\n// the old /* header\nimport './css/b.css'\nimport './css/c.css'\n"`, asserted `css_faults(after_a_line) == []` ([D3](design.md#d3)).
  Verify: `git grep -n -F "css_faults(commented)" -- tests/test_css_files.py` prints one line.
- [x] 1.4 **HALT CHECK** Run the twin against today's guard: `uv run pytest tests/test_css_files.py` must fail in `test_the_check_catches_an_unimported_css_file` on the `commented` case, `[]` found where `["b.css imported 0 times"]` is expected. A pass means the case misses its card: halt. Keep the failing assertion line for the commit body.
  Verify: `git grep -n -F "assert css_faults(commented)" -- tests/test_css_files.py` prints one line.
- [x] 1.5 In `tests/test_css_files.py`, add `COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)` after `IMPORT`, and make `css_faults` count `IMPORT.findall(COMMENT.sub("", (source / "main.ts").read_text()))`. Add "A comment is no import." to its docstring ([D3](design.md#d3)).
  Verify: `uv run pytest tests/test_css_files.py` exits 0.
- [x] 1.6 Prove the edited tests, the scanner and the bindings.
  Verify: `uv run pytest tests/test_ui_api.py tests/test_css_files.py tests/test_ratchets.py tests/test_spec_bindings.py` exits 0.

## 2 — The third format's own scenario

- [ ] 2.1 In `tests/test_ui_api.py`, above `test_a_source_named_as_a_page_is_served_as_the_image_it_is`, below its existing marker, add `@pytest.mark.spec("ui:renders:a-photograph-in-a-third-format-is-refused")`. No assertion changes ([D4](design.md#d4)).
  Verify: `git grep -c -F "ui:renders:a-photograph-in-a-third-format-is-refused" -- tests/test_ui_api.py` prints `tests/test_ui_api.py:1`.
- [ ] 2.2 Prove the new key against this change's delta `specs/ui/spec.md`, the scenario prose and the bindings.
  Verify: `uv run pytest tests/test_spec_bindings.py tests/test_spec_prose.py tests/test_ui_api.py` exits 0.

## 3 — The red runs, kept as mutants

- [ ] 3.1 In `tests/mutants.json`, insert the objects of [the edits](design.md#the-edits) in their order after the object whose `finding` is `P6` and before the one whose `finding` is `VT-14` ([D5](design.md#d5)). Copy each `find` as written.
  Verify: `git grep -n -E '"finding": "(P6|PD-1|PD-6|VT-14)"' -- tests/mutants.json` prints four lines, in that order.
- [ ] 3.2 Replay every recorded mutant: each `find` must occur once in its file and each must die. A survivor is killed by an assertion in its named test ([D5](design.md#d5)).
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.

## 4 — The cards that close on a check

- [ ] 4.1 **HALT CHECK** `0135·S1`: `_patches` in `tests/test_ratchets.py` binds each node in source order before it reads that node's patch, and the twin holds a rebinding ([D6](design.md#d6)). Edit nothing; the card closes at release.
  Verify: `git grep -c -F "for _, _, index in sorted(positioned)" -- tests/test_ratchets.py` prints `tests/test_ratchets.py:1`.
- [ ] 4.2 `0143·R1`: the archived design of `0143-the-browser-green` is frozen and still says "adds no test and removes none". Edit nothing ([D6](design.md#d6)).
  Verify: `git grep -c -F "adds no test and removes none" -- openspec/changes/archive/0143-the-browser-green/design.md` prints `openspec/changes/archive/0143-the-browser-green/design.md:1`.
- [ ] 4.3 `0144·R1`: the archived design of `0144-one-vitest-file` is frozen and still says "returns each argument with a leading". Edit nothing ([D6](design.md#d6)).
  Verify: `git grep -c -F "returns each argument with a leading" -- openspec/changes/archive/0144-one-vitest-file/design.md` prints `openspec/changes/archive/0144-one-vitest-file/design.md:1`.
- [ ] 4.4 `0156·R1`: the archived proposal of `0156-the-version-limit` is frozen and still says "holds the one phase". Edit nothing ([D6](design.md#d6)).
  Verify: `git grep -c -F "holds the one phase" -- openspec/changes/archive/0156-the-version-limit/proposal.md` prints `openspec/changes/archive/0156-the-version-limit/proposal.md:1`.
- [ ] 4.5 No archived file and no product line changed in this change.
  Verify: `git diff --name-only main...HEAD -- openspec/changes/archive isekai ui/src` prints nothing.
