# Tasks — 0058 gpunit integration

The configuration, the verb, the pod, the scripts retired, the documents, the build record, then the one metered
proof, per [design](design.md). Every new test carries `@pytest.mark.spec` with the key its task names.

## Progress

- [x] 1 — The configuration
- [x] 2 — The render verb
- [x] 3 — The pod
- [x] 4 — The scripts retired
- [x] 5 — The documents
- [x] 6 — The build record
- [ ] 7 — ⚠️ **HUMAN · METERED** — build, re-pin, one render session

## 1 — The configuration

- [x] 1.1 **HALT CHECK** — gpunit `v0.2.0` is on its remote, and isekai does not depend on it yet.
  Verify: `git ls-remote --tags https://github.com/alxb1t/gpunit v0.2.0 | grep -c 'refs/tags/v0.2.0$'` prints `1`, and `grep -c gpunit pyproject.toml` prints `0`.
- [x] 1.2 Add `gpunit` to `pyproject.toml`'s `dependencies` and lock it with `uv lock`; name it in `RUNTIME_STACK` in `tests/test_packaging.py`; per [D6](design.md#d6).
  Verify: `grep -c 'gpunit @ git+https://github.com/alxb1t/gpunit@v0.2.0' pyproject.toml` prints `1`, and `grep -c '^name = "gpunit"' uv.lock` prints `1`.
- [x] 1.3 Write `gpunit.toml` per [D6](design.md#d6), the volume taken from `.env`'s `RUNPOD_VOLUME_ID`; add `.gpunit/` to `.gitignore`; cut `.env.example` to `RUNPOD_API_KEY`; drop the volume id from `CLAUDE.md`'s *Guardrails* secrets.
  Verify: `uv run python -c 'import gpunit; s = gpunit.load_spec(__import__("pathlib").Path("gpunit.toml")); print(s.project, s.ceiling_s, s.ports[0].remote)'` prints `isekai 2700 8188`, and `grep -c 'RUNPOD_' .env.example` prints `1`.
- [x] 1.4 In `tests/test_infra.py`, add tests reading `gpunit.toml`: its `image` equals `config/image.json`'s reference and digest (`pod-image:boot:the-pinned-digest-is-booted`); its floors (`pod-image:placement:the-create-carries-the-floors`); its `volume` is set (`model-provisioning:reachability:provisioning-requires-the-network-volume`); its `[env]` sets no telemetry switch (`pod-image:telemetry:the-switches-are-off`).
  Verify: `grep -c 'gpunit.toml' tests/test_infra.py` prints a number of at least `4`.

## 2 — The render verb

- [x] 2.1 Write `isekai/boundary/gpu.py` per [D2](design.md#d2), importing `gpunit` only inside `open_session`.
  Verify: `grep -c '^import gpunit\|^from gpunit' isekai/boundary/gpu.py` prints `0`, and `grep -c 'def read_env\|def open_session' isekai/boundary/gpu.py` prints `2`.
- [x] 2.2 Add `image` to `Wiring` in `isekai/interface/wiring.py` and read it in `_generate` in `isekai/interface/cli.py`; delete `booted_image` and `POD_IMAGE`, with their uses in `tests/conftest.py`, `tests/test_package_paths.py`, `tests/fakes.py` and `tests/test_generate.py`; per [D5](design.md#d5).
  Verify: `grep -rc --include='*.py' --exclude=test_infra.py 'booted_image\|POD_IMAGE\|runpod_pod_image' isekai tests | grep -v ':0$' | wc -l | tr -d ' '` prints `0`; 4.1 removes the scripts' tests that name them.
- [x] 2.3 Write `isekai/interface/render.py` and register `render` in `isekai/interface/cli.py`, per [D1](design.md#d1), [D3](design.md#d3) and [D4](design.md#d4).
  Verify: `uv run python -m isekai render --help | grep -c '<flow>=<count|source>'` prints a number of at least `1`.
- [x] 2.4 Write `tests/test_render.py` on a fake `open_session`, binding every `pod-image:session:*` scenario of the change's `pod-image` spec, `pod-image:boot:no-override`, `pod-image:boot:the-booted-image-is-recorded`, and `image-generation:seeds-from:a-copy-behind-a-source-rendering-first-is-refused-first`.
  Verify: `grep -o 'pod-image:[a-z-]*:[a-z-]*' tests/test_render.py | sort -u | wc -l | tr -d ' '` prints `7`.

## 3 — The pod

- [x] 3.1 In `Dockerfile`, add `boot.sh` from gpunit `v0.2.0` with its checksum, set the `ENTRYPOINT`, and drop the `stop_pod.sh` copy and `chmod`; per [D7](design.md#d7).
  Verify: `grep -c '^ENTRYPOINT \["/opt/gpunit/boot.sh", "--"\]$' Dockerfile` prints `1`, and `grep -c 'stop_pod' Dockerfile` prints `0`.
- [x] 3.2 In `start.sh`, remove steps 1–3 and `STOP_POD`, read `GPUNIT_VOLUME_PATH` and `GPUNIT_VOLUME_ID`, end `hold()` in `exit 1`, remove `export -n RUNPOD_API_KEY`, and `exec` ComfyUI; delete `tools/stop_pod.sh`; per [D7](design.md#d7).
  Verify: `grep -c -E 'RUNPOD_|STOP_POD|/runpod-volume' start.sh` prints `0`, `grep -c '^exec python main.py' start.sh` prints `1`, and `ls tools/stop_pod.sh 2>&1 | grep -c 'No such file'` prints `1`.
- [x] 3.3 Rewrite the `start.sh`, `Dockerfile` and stop tests of `tests/test_infra.py` for [D7](design.md#d7) and the map in [D8](design.md#d8): `BOOT_STEPS`, `serve_command`, the stop helpers, the volume and namespace checks, the capacity floor against `gpunit.toml`'s `disk_gb`, the `ENTRYPOINT` and `ADD` test, the `ADD --checksum` case of the digest check; delete the tests of `tools/stop_pod.sh`.
  Verify: `grep -c 'stop_pod' tests/test_infra.py` prints `0`, and `uv run pytest -q tests/test_infra.py` exits 0.

## 4 — The scripts retired

- [x] 4.1 Delete `infra/up.sh`, `infra/down.sh`, `infra/pods.sh` and `infra/render.sh`, and the tests, twins and helpers of `tests/test_infra.py` that read them; drop `infra` from `tests/test_docs.py`'s `ROOTS` and `tests/test_spec_prose.py`'s `_COMMENT_TREES`.
  Verify: `ls infra 2>&1 | grep -c 'No such file'` prints `1`, and `grep -c -E 'up_sh|down_sh|pods_sh|render_sh' tests/test_infra.py` prints `0`.
- [x] 4.2 Name `isekai render` in the remedies of `isekai/boundary/comfy/client.py`, `isekai/pipeline/generate.py` and `evaluation/record.py`, and in `evaluation/README.md`; update `tests/test_resume.py` and `tests/test_generate.py` to match; per [D9](design.md#d9).
  Verify: `grep -rc --include='*.py' --include='*.md' 'infra/' isekai evaluation tests | grep -v ':0$' | wc -l | tr -d ' '` prints `0`.
- [x] 4.3 Repoint `docs/principles.md`'s *Held by* to tests that exist, and `docs/pins.md`'s pod image row to `gpunit.toml` and `config/image.json`, per [D9](design.md#d9).
  Verify: `uv run pytest -q tests/test_principles.py tests/test_docs.py` exits 0, and `grep -c 'infra/' docs/pins.md docs/principles.md | grep -v ':0$' | wc -l | tr -d ' '` prints `0`.

## 5 — The documents

- [x] 5.1 Rewrite D27, D28, D35 and D36 in `docs/decisions.md`, per [D9](design.md#d9).
  Verify: `grep -c '### D36 · A render session is .isekai render.' docs/decisions.md` prints `1`, and `grep -c 'up.sh' docs/decisions.md` prints `0`.
- [x] 5.2 Rewrite `README.md`'s lifecycle, ④–⑦, layout and provisioning flow, `CLAUDE.md`'s metered protocol, `docs/pins.md`'s *Re-pinning*, and `.claude/skills/run-flows/SKILL.md`, per [D9](design.md#d9).
  Verify: `grep -c -E 'up\.sh|down\.sh|render\.sh|runpod_pod' README.md CLAUDE.md docs/pins.md .claude/skills/run-flows/SKILL.md | grep -v ':0$' | wc -l | tr -d ' '` prints `0`.

## 6 — The build record

- [x] 6.1 Write `tools/image_record.py`, add its `files` to `config/image.json`, and run it from `build-image.yml` into the summary, per [D10](design.md#d10); in `tests/test_infra.py` bind `pod-image:build:the-record-matches-the-tree` and `pod-image:build:the-workflow-prints-the-record`.
  Verify: `uv run python -m tools.image_record | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r == json.load(open("config/image.json"))["files"])'` prints `True`, and `grep -c 'tools.image_record' .github/workflows/build-image.yml` prints `1`.

## 7 — ⚠️ **HUMAN · METERED** — build, re-pin, one render session

- [ ] 7.1 **HUMAN · METERED** — push `v0.35_gpunit_integration`; dispatch `build-image.yml` on it with tag `v0.35-rc1`; check the summary's files equal `config/image.json`'s `files`; write the tag and digest into `config/image.json` and the digest into `gpunit.toml`'s `image`; render one flow on a small batch with `uv run python -m isekai render`; confirm through the RunPod MCP that no `gpunit-isekai` pod is left; per [D11](design.md#d11).
  Verify: `grep -c '"tag": "v0.35-rc1"' config/image.json` prints `1`, and `uv run gpunit status` prints `no session is recorded`.
