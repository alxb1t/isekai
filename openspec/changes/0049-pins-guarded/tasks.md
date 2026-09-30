# Tasks — 0049 pins guarded

The image's pins, the records, the roots, then drift, per [design](design.md). The delta already holds every new
scenario; each task below adds the tests that bind them.

## Progress

- [x] 1 — The image's pins
- [ ] 2 — The records
- [ ] 3 — The roots
- [ ] 4 — Drift

Line numbers are `df5e436`'s. Every new test carries `@pytest.mark.spec` with the key its task names, or
`@pytest.mark.spec_exempt` as a structural twin.

## 1 — The image's pins

- [x] 1.1 **HALT CHECK** — the clone test counts three, the build-tool map is keyed by name, and no workflow runs on a schedule.
  Verify: `grep -c 'len(pinned_commits(dockerfile)) == 3' tests/test_infra.py` prints `1`, `grep -c '^    "insightface": ' tests/test_infra.py` prints `1`, and `cat .github/workflows/*.yml | grep -c 'schedule:'` prints `0`.
- [x] 1.2 In `tools/derive_image_project.py`, count every `git clone` against the checkouts, per [D1](design.md#d1); in `tests/test_infra.py`, restate `test_every_git_clone_in_the_image_is_pinned_to_a_commit` and add its twin `test_the_count_catches_a_clone_with_a_flag_and_another_host`.
  Verify: `grep -c 'len(pinned_commits(dockerfile)) == 3' tests/test_infra.py` prints `0`, and `grep -c '^def test_the_count_catches_a_clone_with_a_flag_and_another_host(' tests/test_infra.py` prints `1`.
- [x] 1.3 In `tests/test_infra.py`, key `SDIST_BUILDS` by name and version and give `test_the_check_catches_a_source_only_package_the_constraints_miss` a bumped insightface, per [D2](design.md#d2); add the backend row to `docs/pins.md`'s *Not pinned*.
  Verify: `grep -cF '("insightface", "0.7.3")' tests/test_infra.py` prints `1`, and `grep -c 'a build backend adds while it builds' docs/pins.md` prints `1`.

## 2 — The records

- [ ] 2.1 In `tests/test_artifact_bytes.py`, capture `_caption` and `_tags` from readings carrying `artifacts` and `options`, and rewrite `tests/golden/caption.json` and `tests/golden/tags.json`, per [D3](design.md#d3).
  Verify: `cat tests/golden/caption.json tests/golden/tags.json | grep -c '"options"'` prints `2`, and `cat tests/golden/caption.json tests/golden/tags.json | grep -c '"artifacts"'` prints `2`.
- [ ] 2.2 In `isekai/pipeline/generate.py`, make `read_runtime` raise the transport's permanent failure in its words, per [D4](design.md#d4); add `test_a_report_in_an_unread_shape_is_permanent` (`comfy-transport:runtime:an-unread-report-is-permanent`) and `test_an_unfetched_report_keeps_the_transports_kind` (`comfy-transport:runtime:an-unfetched-report-keeps-its-kind`) to `tests/test_generate.py`.
  Verify: `grep -c 'carries no {missing}' isekai/pipeline/generate.py` prints `0`, and `grep -cE '^def test_(a_report_in_an_unread_shape_is_permanent|an_unfetched_report_keeps_the_transports_kind)\(' tests/test_generate.py` prints `2`.
- [ ] 2.3 In `isekai/interface/cli.py`, keep a refused report for the session, per [D4](design.md#d4); add `test_a_refused_report_is_asked_once_and_submits_nothing` (`image-generation:runtime:a-refused-report-is-asked-once`) to `tests/test_generate.py`.
  Verify: `grep -c 'cache(partial(read_runtime' isekai/interface/cli.py` prints `0`, and `grep -c '^def test_a_refused_report_is_asked_once_and_submits_nothing(' tests/test_generate.py` prints `1`.

## 3 — The roots

- [ ] 3.1 In `isekai/shared/vocabulary.py`, anchor `DEFAULT_MODELS_DIR` on `REPOSITORY`; in `evaluation/__main__.py`, import it; in `tests/test_package_paths.py`, add it and `FIELD_MAP_PATH` to `ANCHORS`, per [D5](design.md#d5).
  Verify: `cat isekai/shared/vocabulary.py evaluation/__main__.py | grep -c 'Path("models")'` prints `0`, and `grep -cE 'id="(vocabulary\.DEFAULT_MODELS_DIR|field_map\.FIELD_MAP_PATH)"' tests/test_package_paths.py` prints `2`.
- [ ] 3.2 Drop "16.5 GiB" from `infra/up.sh`'s message and the comments in `tests/test_infra.py`, per [D6](design.md#d6).
  Verify: `cat infra/up.sh tests/test_infra.py | grep -c '16\.5'` prints `0`, and `bash -n infra/up.sh && echo ok` prints `ok`.

## 4 — Drift

- [ ] 4.1 In the `Makefile`, add `drift` and end it in `git diff --exit-code --stat`, and make `derive` run the field map's deriver then `drift`'s recipe; add `.github/workflows/drift.yml`, per [D7](design.md#d7).
  Verify: `grep -c '^drift:' Makefile` prints `1`, `grep -c 'git diff --exit-code --stat' Makefile` prints `1`, `grep -c 'schedule:' .github/workflows/drift.yml` prints `1`, and `grep -c 'make drift' .github/workflows/drift.yml` prints `1`.
- [ ] 4.2 In `tests/test_infra.py`, make `uv_versions_apart` read every workflow's uv version, and restate `test_every_uv_version_the_build_names_is_the_root_projects` and `test_the_check_catches_a_uv_version_that_drifted`.
  Verify: `grep -c 'def uv_versions_apart(root: str, ci: str' tests/test_infra.py` prints `0`.
- [ ] 4.3 Restate the *Known breaks* line in `docs/principles.md`, and name `make drift` in `docs/pins.md`'s *Re-pinning*, per [D7](design.md#d7).
  Verify: `grep -c 'never re-run' docs/principles.md` prints `0`, and `grep -c 'make drift' docs/pins.md` prints `1`.
