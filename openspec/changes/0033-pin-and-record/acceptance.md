Image: ghcr.io/alxb1t/isekai:v0.24-rc1@sha256:d6f12d02b1fb6b0d2c4c6d0505c70193202c647d57c27b7e1235845427dbb500

# Acceptance — 0033 pin and record

The evidence each HUMAN phase closes on. Paths are repository-relative.

## 3 — the rc build

- `gh workflow run build-image.yml --ref v0.24_pin_and_record -f tag=v0.24-rc1`, at `42da914`: run
  `36298537985`, `success`.
- The digest the build step reported and the one `docker buildx imagetools inspect
  ghcr.io/alxb1t/isekai:v0.24-rc1` reads agree: `sha256:d6f12d02b1fb6b0d2c4c6d0505c70193202c647d57c27b7e1235845427dbb500`.
- A first dispatch at `09e3111` was refused: `build-image.yml` did not parse. Fixed in `42da914`.
