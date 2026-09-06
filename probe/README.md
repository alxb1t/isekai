# Phase 6 — the smoke test and the loader probe

One pod session, on `ghcr.io/alxb1t/isekai:v0.11-rc`, RTX PRO 4500 Blackwell in EU-RO-1.

| | |
|---|---|
| Pod | `2gg3c8ucjtxd50` |
| Created | 2026-09-06T08:01:38Z |
| Torn down | 2026-09-06T08:11:11Z |
| Wall clock | **9 min 33 s** (planned against 24 min, ceiling 45 min) |
| Rate / cost | $0.72/hr → **~$0.11** (ceiling ~$0.30) |
| Teardown confirmed | RunPod MCP `list-pods` → `{"items": [], "total": 0}`; `get-pod 2gg3c8ucjtxd50` → `404 {"detail":"pod not found"}` |

The volume mounted and the models were already on it: `/opt/ComfyUI/models -> /runpod-volume/isekai`,
no fetch, no failure marker at `/opt/isekai/provisioning-failed`. ComfyUI reported version `0.34.0`,
and the pinned core was confirmed on the pod itself —
`git -C /opt/ComfyUI rev-parse HEAD` → `250b2e9551a7bc7a8ebb5beb07e0fecd2983e04a`, the commit
`Dockerfile` names and the one `:v0.10-rc` was built from.

**The images are not here**, following v0.10's precedent: this repository claims reproducibility over
the submitted workflow JSON and never over pixels. The inputs are not here either — they are derived
faces, and a project whose product is identity preservation does not commit them (design.md D14).
What is here is the recipe, the submitted graph, the run manifest and the measurements. Every file
below is reproducible from `build_inputs.py`, and its SHA-256 is recorded so that a re-run can be
checked rather than trusted.

> This is a stated deviation from `tasks.md`'s phase-6 step 4, which says to bring the renders into
> this directory. The v0.10 probe README settles the question the other way, in terms — *"The images
> are not here … this repository claims reproducibility over the submitted workflow JSON, never over
> pixels"* — and one version does not silently reverse a convention the previous one wrote down.

## The inputs

Built by `build_inputs.py` from two sources outside this repository: an 832×1216 synthetic portrait
and a 1248×1824 full-height synthetic portrait. Neither path is tracked; the script takes both as
arguments. ImageMagick's `convert` moves the pixels, because a crop needs an exact origin and
`sips --cropOffset` is measured from the centre. The recipe is byte-reproducible — two consecutive
runs produced identical digests — which is the only reason recording a digest for an uncommitted file
is worth anything.

| | file | stored | SHA-256 |
|---|---|---|---|
| a | `a_landscape.png` | 832×554 | `110a799d47b555807de600d53a05bcde1d3857ce56ea2077af3c2845f5de4c25` |
| b | `b_above_scale.png` | 1248×1400 | `7573a79deae3a323fe3f44891f8395489df093fcf82d0306d6d20ccf5848cad2` |
| c | `c_rotated.jpg` | 1216×832 + EXIF Orientation 6 | `0e8b7555badc442c13c34abca74af21e0a3ec6937c9d6ad025679e7c475fbad4` |
| d | `d_control.jpg` | 832×1216, no EXIF | `8bab3a0651bbb75bf302e4264ef34b0c63f4cdefe5afc15fe6bedf4468871aed` |
| e | `e_png_exif.png` | 832×1216 + `eXIf` Orientation 6 | `db63ef3fdb992bdd8b62ffa02dd777af7fa0d4ecc64aa32c6a56062ae4388748` |

`e` is not a render input. It exists for the loader probe alone.

## 1 — The loader probe · `loader-probe.json`

`LoadImage` → `SaveImage`, no diffusion, over the same HTTP API the renders use. Seconds, no GPU, and
run **before** the render budget was spent. Its graph is `loader_probe_graph.json`, which lives here
and never in `workflows/`, so the one-path rule is untouched.

It exists because **exit 0 cannot answer the rotated case** (design.md D11). If `LoadImage` did not
transpose, the graph would receive landscape pixels and `ImageScale` — which scales to the exact
target rather than fitting to it — would squash them into the portrait target. `run.json` records the
same dimensions either way.

| input | stored | tag | saved by the pod | transposed? |
|---|---|---|---|---|
| `c_rotated.jpg` | 1216×832 | EXIF Orientation 6 | **832×1216** | **yes** |
| `e_png_exif.png` | 832×1216 | `eXIf` Orientation 6 | **1216×832** | **yes** |
| `d_control.jpg` | 832×1216 | none | 832×1216 | no |

**Both codecs are transposed.** `d` is the control, and it is what makes the other two attributable to
the tag rather than to the codec.

The JPEG result confirms the rule v0.10 shipped. **The PNG result is a defect**: `_png_dimensions`
reads IHDR and stops, so injection measures a PNG as its header states it while the loader hands the
graph the transposed pixels — the same mismatch v0.10 called blocking, in the codec branch that was
not fixed, and **every input this project has ever rendered is a PNG**. Phase 7 takes the first of its
two legitimate outcomes: the fix, with a scenario.

The saved probe PNGs are not committed. They are round-trips of the input faces, so D14's rule applies
to them exactly as it applies to the inputs; the dimensions above are the whole finding.

## 2 — Four renders at a fixed seed · `renders.run.json`

`convert.py <photo> --variations 1 --seed 20260906`, one seed across all four. One variation, because
the criteria are dimensional and structural: variations jitter dials, not dimensions.

**This table is the authoritative tie between each input, its computed target and what came back.**
It has to be, because `run.json` cannot be: all four runs produced a **byte-identical** manifest,
`18e666656ebdb1d6fedaba686213576331ee182d534f72326844e2182630d882`, since the seed stream does not
depend on the photo. One copy is kept rather than four identical ones, and the fact itself is the
record (0010:R8).

| | input | loader presents | target `working_resolution` computes | rendered | SHA-256 of the render |
|---|---|---|---|---|---|
| a | `a_landscape.png` | 832×554 | 1536×1024 | **1536×1024** ✓ | `448051fa789d3b4f7249f4f50ada4238244323e6bf6f94d659a6c59cf293e304` |
| b | `b_above_scale.png` | 1248×1400 | 1024×1152 | **1024×1152** ✓ | `0289e1e380b4a10219d072a7165a76b33ca47bdcf32bad1df347c039a7d737b5` |
| c | `c_rotated.jpg` | 832×1216 | 1024×1472 | **1024×1472** ✓ | `5bcbf9e63d210d7488cbcdb6f2c8602ca34ce6670bd6a5ea60466d48ba32214b` |
| d | `d_control.jpg` | 832×1216 | 1024×1472 | **1024×1472** ✓ | `bdf2cfe6c5edc163fe24e79d3a8caf28067eab1fc6297248ab35e44e4f0379d8` |

All four exited 0. Every rendered pair equals the target computed from that file's own header.

- **a** is the first time short-side rounding ran on the **height** axis, and 1536×1024 is a target no
  prior run produced.
- **b** is a crop to an aspect no prior run produced; uncropped, 1248×1824 is the same aspect as the
  832×1216 photo v0.10 rendered and would have computed to the identical 1024×1472, proving nothing.
- **c** and **d** share a target by design. That is the point of the control.

## What this session established, and what it did not

**Established.** The path runs end to end at four input shapes v0.10 did not test. Each render's
dimensions equal the target injection computes from that file's header. The pinned ComfyUI core is
the one on the pod. `LoadImage` at that commit applies EXIF `Orientation` to **both** JPEG and PNG.

**Not established**, and no sentence anywhere should read as if it were:

- **Nothing about identity, fidelity or quality.** No evaluator exists and none was run. Not one
  render was judged.
- **Not that renders are unchanged from v0.10.** The core is pinned to the commit v0.10 booted, so the
  core is not a variable — but the image's Python dependency closure was re-resolved at build
  (design.md D4), and no v0.10 PNG baseline was kept, so there is nothing to diff against. Render
  equivalence is unestablished and stays that way.
- **Not the volume guard and not the bounded hold.** Both shipped in phase 1 and both are suite-bound
  and unexercised here: the pod booted with its volume, provisioning succeeded, and neither guard was
  reached. Exercising them would mean deliberately breaking a configuration this repository no longer
  produces, on metered time.
- **Nothing about mutation.** Each photo ran at one variation.
