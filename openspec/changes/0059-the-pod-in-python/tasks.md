# Tasks — 0059 the pod in Python

`fetch`, the start module, the image on them, the browser check, then the metered proof with the pod read; then
`fetch`'s retry and a second metered proof on the image rebuilt for it, per [design](design.md). Every new test carries `@pytest.mark.spec` with the key its task names.

## Progress

- [x] 1 — fetch
- [x] 2 — The start module
- [x] 3 — The image on Python
- [x] 4 — The browser check, and no bash left
- [x] 5 — ⚠️ **HUMAN · METERED** — build, re-pin, read the pod, one render session
- [ ] 6 — fetch tries again
- [ ] 7 — ⚠️ **HUMAN · METERED** — rebuild as rc3, re-pin, read the pod, one render session

## 1 — fetch

- [x] 1.1 **HALT CHECK** — three bash files are tracked, and `provision.py` has no `fetch`.
  Verify: `git ls-files '*.sh' | wc -l | tr -d ' '` prints `3`, and `grep -c '^def fetch' isekai/boundary/provision.py` prints `0`.
- [x] 1.2 In `isekai/boundary/provision.py`, add `fetch` and `Fetcher.get`, and put `main` on argparse with `fetch`, `plan` and `land`, per [D3](design.md#d3); in `tests/test_provision.py` bind `model-provisioning:source-fallback:a-failed-transfer-advances-to-the-next-source` to `fetch` on a fake `Fetcher`.
  Verify: `uv run python isekai/boundary/provision.py fetch --help | grep -c 'models-dir'` prints a number of at least `1`, and `grep -c 'source-fallback:a-failed-transfer' tests/test_provision.py` prints a number of at least `1`.
- [x] 1.3 Point the remedies at `fetch` in `isekai/shared/vocabulary.py`, `isekai/boundary/ollama.py` and the docstring of `provision.py`, and their assertions in `tests/test_caption.py` and `tests/test_vocabulary_manifest.py`, per [D3](design.md#d3).
  Verify: `grep -c 'download_models' isekai/shared/vocabulary.py isekai/boundary/ollama.py | grep -v ':0$' | wc -l | tr -d ' '` prints `0`.

## 2 — The start module

- [x] 2.1 Write `isekai/boundary/pod_start.py` per [D1](design.md#d1), [D2](design.md#d2) and [D4](design.md#d4).
  Verify: `grep -c '^def ' isekai/boundary/pod_start.py` prints a number of at least `5`, and `grep -c 'RUNPOD' isekai/boundary/pod_start.py` prints `0`.
- [x] 2.2 Write `tests/test_pod_start.py` binding every key of [D6](design.md#d6)'s successor column, the change's new `pod-image:memory:an-unread-type-holds` and `pod-image:memory:swap-is-reported` among them.
  Verify: `grep -o -E '(pod-image|model-provisioning):[a-z-]+:[a-z-]+' tests/test_pod_start.py | sort -u | wc -l | tr -d ' '` prints a number of at least `15`.

## 3 — The image on Python

- [x] 3.1 In `Dockerfile`, copy `isekai/boundary/pod_start.py` beside `provision.py`, set `CMD ["python", "/opt/isekai/isekai/boundary/pod_start.py"]`, drop the `start.sh` and `download_models.sh` copies and `chmod`, and `wget` from apt; delete `start.sh` and `tools/download_models.sh`; drop `plan`, `land` and `plan()` from `provision.py`, and `VOLUME_MOUNT` and `MODELS_NAMESPACE` (`0058·R9`); per [D1](design.md#d1), [D3](design.md#d3) and [D7](design.md#d7).
  Verify: `grep -c 'pod_start.py' Dockerfile` prints a number of at least `2`, and `grep -c -E 'start\.sh|download_models|wget' Dockerfile` prints `0`.
- [x] 3.2 Delete the tests and helpers of `tests/test_infra.py` that read `start.sh` or `download_models.sh`, and the constants it imports from `provision.py`; repoint `DRIVER_PATH` in `tests/test_vocabulary_manifest.py` and the path in `tests/test_resume.py` at `provision.py`;
  drop `start.sh` from `tests/test_docs.py`'s `ROOT_FILES` and `tests/test_spec_prose.py`'s `_COMMENT_TREES`.
  Verify: `grep -rc --include='*.py' -E 'start_sh|download_models|VOLUME_MOUNT' tests | grep -v ':0$' | wc -l | tr -d ' '` prints `0`.
- [x] 3.3 In `tools/image_record.py`, refuse a `COPY` it cannot read (`0058·R4`), with a test in `tests/test_infra.py`; re-derive `config/image.json`'s `files`; per [D7](design.md#d7).
  Verify: `uv run python -m tools.image_record | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r == json.load(open("config/image.json"))["files"])'` prints `True`.
- [x] 3.4 Repoint `docs/principles.md`'s *Held by* at `tests/test_pod_start.py`; add the host's swap to D35 in `docs/decisions.md`; rewrite `docs/pins.md`'s pod image recipe to rebuild before re-recording (`0058·R3`) and its reader line to `fetch`; name `fetch` and `pod_start.py` in `README.md`'s download lines and layout; per [D4](design.md#d4), [D6](design.md#d6) and [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_principles.py tests/test_docs.py` exits 0, and `grep -c -E 'download_models|start\.sh' README.md docs/pins.md | grep -v ':0$' | wc -l | tr -d ' '` prints `0`.

## 4 — The browser check, and no bash left

- [x] 4.1 Write `tools/typecheck_ui.py` per [D5](design.md#d5), with a test of each refusal; run it from `Makefile`'s `gate`; delete `tools/typecheck_ui.sh`; name it in `README.md`.
  Verify: `make -n gate | grep -c 'uv run python -m tools.typecheck_ui'` prints `1`, and `grep -c 'typecheck_ui.sh' README.md Makefile | grep -v ':0$' | wc -l | tr -d ' '` prints `0`.
- [x] 4.2 Name `isekai render` in `tests/test_docs.py`'s docstring example (`0058·R2`), and drop the change citation from `.github/workflows/build-image.yml`'s header comment (`0058·R8`), per [D7](design.md#d7).
  Verify: `grep -c 'up.sh' tests/test_docs.py` prints `0`, and `grep -c -E '00[0-9]{2} design' .github/workflows/build-image.yml` prints `0`.
- [x] 4.3 Confirm no bash is tracked.
  Verify: `git ls-files '*.sh' | wc -l | tr -d ' '` prints `0`.

## 5 — ⚠️ **HUMAN · METERED** — build, re-pin, read the pod, one render session

- [x] 5.1 **HUMAN · METERED** — push `v0.35.1_the_pod_in_python`; dispatch `build-image.yml` on it with tag `v0.35.1-rc2`; check its printed files equal `config/image.json`'s `files`; write the tag and digest into `config/image.json` and the digest into `gpunit.toml`; per [D8](design.md#d8).
  Verify: `grep -c '"tag": "v0.35.1-rc2"' config/image.json` prints `1`.
- [x] 5.2 **HUMAN · METERED** — run `uv run python -m isekai render` on a small batch; while it is open, read the pod over `uv run gpunit ssh` and the saved PNG as [D8](design.md#d8) lists, and write the readings to `.minions/0059_pod_proof.txt`, one a line; confirm through the RunPod MCP that no `gpunit-isekai` pod is left.
  Verify: `grep -c -E 'tmpfs|--disable-metadata|TMPDIR=/dev/shm/comfyui/tmp|no text chunk' .minions/0059_pod_proof.txt` prints `4`, and `uv run gpunit status` prints `no session is recorded`.

## 6 — fetch tries again

- [ ] 6.1 **HALT CHECK** — `fetch` makes one attempt a source.
  Verify: `grep -c '^ATTEMPTS' isekai/boundary/provision.py` prints `0`.
- [ ] 6.2 In `isekai/boundary/provision.py`, try a broken transfer again from the same source, `ATTEMPTS = 3`, waiting 10 s then 30 s, through a wait `fetch` takes as a parameter; a digest mismatch is not tried again; per [D9](design.md#d9). In `tests/test_provision.py`, bind `model-provisioning:source-fallback:a-broken-transfer-is-tried-again` to a fake `Fetcher` that fails once then serves, and to one that fails every attempt and moves on; update the source lists the existing fallback tests expect for a source whose transfer breaks.
  Verify: `grep -c 'source-fallback:a-broken-transfer-is-tried-again' tests/test_provision.py` prints a number of at least `2`, and `grep -c '^ATTEMPTS = 3$' isekai/boundary/provision.py` prints `1`.
- [ ] 6.3 Re-derive `config/image.json`'s `files`, since `provision.py` changed; per [D7](design.md#d7).
  Verify: `uv run python -m tools.image_record | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r == json.load(open("config/image.json"))["files"])'` prints `True`.
- [ ] 6.4 Land `config/vocabulary.json` with the real transfer into an empty directory, per [D9](design.md#d9).
  Verify: `d=$(mktemp -d) && uv run python -m isekai.boundary.provision fetch --models-dir "$d" config/vocabulary.json | grep -c 'saved (verified)'` prints `2`.

## 7 — ⚠️ **HUMAN · METERED** — rebuild as rc3, re-pin, read the pod, one render session

- [ ] 7.1 **HUMAN · METERED** — push `v0.35.1_the_pod_in_python`; dispatch `build-image.yml` on it with tag `v0.35.1-rc3`; check its printed files equal `config/image.json`'s `files`; write the tag and digest into `config/image.json` and the digest into `gpunit.toml`; per [D8](design.md#d8) and [D9](design.md#d9).
  Verify: `grep -c '"tag": "v0.35.1-rc3"' config/image.json` prints `1`.
- [ ] 7.2 **HUMAN · METERED** — run `uv run python -m isekai render` on a small batch; while it is open, read the pod over `uv run gpunit ssh` and the saved PNG as [D8](design.md#d8) lists, and write the readings to `.minions/0059_pod_proof_rc3.txt`, one a line; confirm through the RunPod MCP that no `gpunit-isekai` pod is left.
  Verify: `grep -c -E 'tmpfs|--disable-metadata|TMPDIR=/dev/shm/comfyui/tmp|no text chunk' .minions/0059_pod_proof_rc3.txt` prints `4`, and `uv run gpunit status` prints `no session is recorded`.
