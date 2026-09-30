# Tasks — 0050 the colour profile

The refusals first, then the allowlist, per [design](design.md). The delta already holds the new scenario; phase 2
adds its test.

## Progress

- [ ] 1 — The refusals
- [ ] 2 — The colour profile

Line numbers are `e08e775`'s. Every new test carries `@pytest.mark.spec` with the key its task names.

## 1 — The refusals

- [ ] 1.1 **HALT CHECK** — the allowlist keeps the profile, and `tests/test_image.py` expects no stripper refusal.
  Verify: `grep -c 'b"ICC_PROFILE' isekai/shared/image.py` prints `1`, `grep -c 'b"iCCP"' isekai/shared/image.py` prints `1`, and `grep -c 'Refusal' tests/test_image.py` prints `0`.
- [ ] 1.2 Add `test_each_unwalkable_photograph_is_refused_by_name` (`image-generation:photo-metadata:an-unwalkable-photograph-is-refused`) to `tests/test_image.py`, parametrised over the cases in [D2](design.md#d2).
  Verify: `grep -c '^def test_each_unwalkable_photograph_is_refused_by_name(' tests/test_image.py` prints `1`.

## 2 — The colour profile

- [ ] 2.1 In `isekai/shared/image.py`, drop APP2 from `_JPEG_KEPT_APPS` and the colour chunks from `_PNG_KEPT_CHUNKS`, and restate `strip_metadata`'s docstring, per [D1](design.md#d1).
  Verify: `grep -c 'ICC_PROFILE' isekai/shared/image.py` prints `0`, `grep -c 'iCCP' isekai/shared/image.py` prints `0`, and `grep -c 'colour profile' isekai/shared/image.py` prints `0`.
- [ ] 2.2 In `tests/test_image.py`, restate `test_no_block_outside_the_allowlist_survives` and add `test_no_colour_profile_leaves` (`image-generation:photo-metadata:no-colour-profile-leaves`), per [D1](design.md#d1).
  Verify: `grep -c 'b"iCCP", b"IDAT"' tests/test_image.py` prints `0`, and `grep -c '^def test_no_colour_profile_leaves(' tests/test_image.py` prints `1`.
