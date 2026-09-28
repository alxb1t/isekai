# Tasks — 0039 the photo metadata

The stripper first, with its tests; then the upload through a narrower seam, the scenarios and the PyAV check, per
[design](design.md).

## Progress

- [x] 1 — The stripper
- [x] 2 — The upload

Line numbers are `984a74f`'s. Every new test carries `@pytest.mark.spec` with the key its task names, or `spec_exempt` where
the task says so.

## 1 — The stripper

- [x] 1.1 **HALT CHECK** — the upload sends the file as it is, and no stripper exists.
  Verify: `grep -c 'Path(path).read_bytes()' isekai/boundary/comfy/client.py` prints `1`, and `grep -c 'def strip_metadata' isekai/shared/image.py` prints `0`.
- [x] 1.2 Add `strip_metadata` to `isekai/shared/image.py` per [D1](design.md#d1), [D2](design.md#d2) and [D5](design.md#d5), stdlib only.
  Verify: `grep -c '^def strip_metadata' isekai/shared/image.py` prints `1`, and `grep -cE '^(import|from) (PIL|numpy|av)' isekai/shared/image.py` prints `0`.
- [x] 1.3 Add to `tests/test_image.py`, per [D6](design.md#d6): `test_the_orientation_survives_the_strip` (`image-generation:photo-metadata:the-orientation-survives`), `test_the_pixels_are_unchanged_by_the_strip` (`image-generation:photo-metadata:the-pixels-are-unchanged`), and `test_no_block_outside_the_allowlist_survives`, `test_the_hand_built_photographs_still_walk`, each `spec_exempt`.
  Verify: `grep -c -e '^def test_the_orientation_survives_the_strip' -e '^def test_the_pixels_are_unchanged_by_the_strip' -e '^def test_no_block_outside_the_allowlist_survives' -e '^def test_the_hand_built_photographs_still_walk' tests/test_image.py` prints `4`.

## 2 — The upload

- [x] 2.1 Change `upload_image` to take a name and bytes in `isekai/boundary/comfy/contract.py`, `isekai/boundary/comfy/client.py` and `tests/fakes.py`, and move the calls in `tests/test_generate.py` and `tests/test_resume.py`, per [D4](design.md#d4).
  Verify: `cat isekai/boundary/comfy/contract.py isekai/boundary/comfy/client.py tests/fakes.py | grep -c 'def upload_image(self, name: str, data: bytes) -> str'` prints `3`, and `grep -c 'Path(path).read_bytes()' isekai/boundary/comfy/client.py` prints `0`.
- [x] 2.2 Upload `strip_metadata(run.photo)` under `run.photo.name` in `isekai/pipeline/generate.py`, per [D3](design.md#d3); add to `tests/test_generate.py` `test_the_endpoint_receives_no_metadata` (`image-generation:photo-metadata:no-metadata-leaves-the-machine`), `test_the_runs_copy_keeps_its_bytes` (`image-generation:photo-metadata:the-runs-copy-is-untouched`) and `test_an_unwalkable_photograph_is_refused_before_upload` (`image-generation:photo-metadata:an-unwalkable-photograph-is-refused`).
  Verify: `grep -c 'strip_metadata(run.photo)' isekai/pipeline/generate.py` prints `1`, and `grep -c -e '^def test_the_endpoint_receives_no_metadata' -e '^def test_the_runs_copy_keeps_its_bytes' -e '^def test_an_unwalkable_photograph_is_refused_before_upload' tests/test_generate.py` prints `3`.
- [x] 2.3 Name the stripping in `isekai/shared/README.md`'s row for `image.py`, per [D6](design.md#d6).
  Verify: `grep -c "strips a photograph's metadata for upload" isekai/shared/README.md` prints `1`.
- [x] 2.4 Run the PyAV check [D6](design.md#d6) describes and record its output in `openspec/changes/0039-the-photo-metadata/acceptance.md`: for a JPEG and a PNG with orientation 6, the original and the stripped file decode to identical arrays and the same rotation.
  Verify: `grep -c '^identical: ' openspec/changes/0039-the-photo-metadata/acceptance.md` prints `2`.
