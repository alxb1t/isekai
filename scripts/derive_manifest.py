#!/usr/bin/env python3
"""Re-derive `scripts/models.json` from the authored source spec below.

The manifest is *derived*, never transcribed: Hugging Face publishes each LFS
object's SHA-256 as its object id, so every digest in the committed file came
out of the `paths-info` API rather than out of a human reading a web page. An
upgrade is therefore a revision bump plus a re-run, not fifteen manual lookups.

Run it from the repository root:

    uv run python scripts/derive_manifest.py

It rewrites `scripts/models.json` in place. Re-running without editing the spec
must leave the file byte-identical -- `git diff --exit-code scripts/models.json`
is the check, and it is why `PINNED` is a constant here rather than today's date.

Revisions are data in this file, not resolved from a branch at run time. Resolving
`main` would make the tool's output depend on the day it ran, which is the exact
property the pins exist to remove.
"""

import json
import urllib.request
from pathlib import Path
from typing import NamedTuple, TypedDict

MANIFEST_PATH = Path(__file__).resolve().parent / "models.json"

# The date the revisions below were taken. Bumping a revision means bumping this.
PINNED = "2026-09-05"

# Hugging Face orgs that publish the artifact they serve. A primary source outside
# this set is a mirror, and a mirror must declare an alternate (design.md D10).
PUBLISHERS = (
    "InstantX",
    "TTPlanet",
    "xinsir",
    "TheMistoAI",
    "lllyasviel",
)


class ManifestEntry(TypedDict):
    """One emitted manifest entry -- the shape `isekai.provision` reads back."""

    dest: str
    sha256: str
    bytes: int
    sources: list[str]


class Manifest(TypedDict):
    """The emitted manifest."""

    pinned: str
    publishers: list[str]
    entries: list[ManifestEntry]


class Source(NamedTuple):
    """One Hugging Face file, addressed by an immutable revision."""

    repo: str
    revision: str
    path: str

    def url(self) -> str:
        """Return the `resolve/<sha>/` URL that serves exactly these bytes."""
        return f"https://huggingface.co/{self.repo}/resolve/{self.revision}/{self.path}"


class Spec(NamedTuple):
    """A destination under the models tree, and the ordered sources that fill it.

    `expect_sha256` is for an artifact whose publisher is not the host: the
    publisher states a digest, every source is a mirror, and the derived digest
    is checked against the stated one. That check is what makes the mirrors
    interchangeable CDNs rather than trust roots (design.md D1).
    """

    dest: str
    sources: tuple[Source, ...]
    expect_sha256: str | None = None


# --- the authored spec: destinations, and where each one's bytes come from ---

# WAI-illustrious-SDXL v17.0 (Civitai model 827184, version 2883731). The model is
# published on Civitai and has no first-party Hugging Face repo, so every source below
# is a mirror and the digest is the acceptance test (design.md D1). `WAI_SHA256` is the
# SHA-256 Civitai itself publishes for the version -- computed by the platform after
# upload, so an independent cross-check of the mirrors, not a signature by the author.
# The byte count discriminates nothing: every published WAI version reports the same
# one.
WAI_SHA256 = "f116b0c78ff441467b0cdc8f1936e1ed18ea31e9997c7b132b1b8db533f0bd04"
WAI_FILE = "waiIllustriousSDXL_v170.safetensors"

# From the sibling project, which pins the same repo and the same files (design.md D2).
INSTANTID = "57b32dfee076092ad2930c71fd6d439c2c3b1820"
ANTELOPE = "ba0c3e10f4548361eb9a63265d87ce1140ab5a05"
ANTELOPE_ALT = "397cafa6d8310e96e302e96528c20a4c92a884f2"
TILE = "37f1c4575b543fb2036e39f5763d082fdd135318"
OPENPOSE = "23f966cd5cfdd3f7729c903e243d87152162d2b7"
MISTOLINE = "1d9d0b3d48b295cf70d80a0f839a3055672f8393"
DWPOSE = "1a7144101628d69ee7a3768d1ee3a094070dc388"
YOLOX_ALT = "a124b32c3b7c5cebda1c7cd96178f0f9d2050125"
DWPOSE_TS = "359d662a9b33b73f6d0f21732baf8845f17bb4be"
DWPOSE_TS_ALT = "31098820c4d5d126b92e28517380ea1b088f8d53"
ANNOTATORS = "982e7edaec38759d914a963c48c4726685de7d96"

ANTELOPE_FILES = (
    "1k3d68.onnx",
    "2d106det.onnx",
    "genderage.onnx",
    "glintr100.onnx",
    "scrfd_10g_bnkps.onnx",
)

SPECS: tuple[Spec, ...] = (
    # Primary first, then the byte-identical mirrors v0.9's fallback walks in order.
    Spec(
        f"checkpoints/{WAI_FILE}",
        (
            Source(
                "LyliaEngine/waiIllustriousSDXL_v170",
                "5ef4e2da7173a160ad04aebcaa2fdcd6d20ed792",
                WAI_FILE,
            ),
            Source(
                "frankjoshua/waiIllustriousSDXL_v170",
                "9303ce49345822823717889e3677b6ffd43fc6a9",
                WAI_FILE,
            ),
            Source(
                "zhenshipo/waiIllustriousSDXL_v170",
                "81274954afbade01cfbbb68008dfe84fc9e6adb2",
                WAI_FILE,
            ),
            Source(
                "mogaru99/waiIllustriousSDXL_v170",
                "a39fd9086cf0d20c99233d94546a6468c83dffab",
                WAI_FILE,
            ),
            Source(
                "hiusduh/waiIllustriousSDXL_v170",
                "3e2d67a43d078b1860fbc80984235906b1823101",
                WAI_FILE,
            ),
            Source(
                "yufusoft/WAI-illustrious-SDXL",
                "921c723bf2d4e7350f80a362c9de8a23c1377fc9",
                WAI_FILE,
            ),
            Source(
                "zhuhai1234/waiIllustriousSDXL-dimo",
                "606eb271fcd4ff213272f0e1a1c4bcdaf4d19475",
                WAI_FILE,
            ),
        ),
        WAI_SHA256,
    ),
    Spec(
        "instantid/ip-adapter.bin",
        (Source("InstantX/InstantID", INSTANTID, "ip-adapter.bin"),),
    ),
    Spec(
        "controlnet/instantid/diffusion_pytorch_model.safetensors",
        (
            Source(
                "InstantX/InstantID",
                INSTANTID,
                "ControlNetModel/diffusion_pytorch_model.safetensors",
            ),
        ),
    ),
    *(
        Spec(
            f"insightface/models/antelopev2/{name}",
            (
                Source("DIAMONIK7777/antelopev2", ANTELOPE, name),
                Source(
                    "MonsterMMORPG/InstantID_Models",
                    ANTELOPE_ALT,
                    f"models/antelopev2/{name}",
                ),
            ),
        )
        for name in ANTELOPE_FILES
    ),
    Spec(
        "controlnet/TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors",
        (
            Source(
                "TTPlanet/TTPLanet_SDXL_Controlnet_Tile_Realistic",
                TILE,
                "TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors",
            ),
        ),
    ),
    Spec(
        "controlnet/openpose/diffusion_pytorch_model.safetensors",
        (
            Source(
                "xinsir/controlnet-openpose-sdxl-1.0",
                OPENPOSE,
                "diffusion_pytorch_model.safetensors",
            ),
        ),
    ),
    Spec(
        "controlnet/mistoLine_rank256.safetensors",
        (Source("TheMistoAI/MistoLine", MISTOLINE, "mistoLine_rank256.safetensors"),),
    ),
    # The four annotator checkpoints the preprocessors would otherwise fetch for
    # themselves, onto container disk, mid-render. The layout under the redirect
    # is the pack's own: <AUX_ANNOTATOR_CKPTS_PATH>/<repo>/<path> (design.md D7).
    Spec(
        "annotator_ckpts/yzd-v/DWPose/yolox_l.onnx",
        (
            Source("yzd-v/DWPose", DWPOSE, "yolox_l.onnx"),
            Source("hr16/yolox-onnx", YOLOX_ALT, "yolox_l.onnx"),
        ),
    ),
    Spec(
        "annotator_ckpts/hr16/DWPose-TorchScript-BatchSize5/dw-ll_ucoco_384_bs5.torchscript.pt",
        (
            Source(
                "hr16/DWPose-TorchScript-BatchSize5",
                DWPOSE_TS,
                "dw-ll_ucoco_384_bs5.torchscript.pt",
            ),
            Source(
                "Pictorial/DWPose-TorchScript-BatchSize5",
                DWPOSE_TS_ALT,
                "dw-ll_ucoco_384_bs5.torchscript.pt",
            ),
        ),
    ),
    Spec(
        "annotator_ckpts/lllyasviel/Annotators/sk_model.pth",
        (Source("lllyasviel/Annotators", ANNOTATORS, "sk_model.pth"),),
    ),
    Spec(
        "annotator_ckpts/lllyasviel/Annotators/sk_model2.pth",
        (Source("lllyasviel/Annotators", ANNOTATORS, "sk_model2.pth"),),
    ),
)


def published_digest(source: Source) -> tuple[str, int]:
    """Return the SHA-256 and size Hugging Face publishes for `source`.

    The digest is the LFS object id, which HF documents as the file's SHA-256. A
    path that is not stored in LFS has no such id, and this raises rather than
    falling back to the git blob sha1 -- a sha1 in a sha256 field would validate
    and verify nothing.
    """
    body = json.dumps({"paths": [source.path]}).encode()
    request = urllib.request.Request(
        f"https://huggingface.co/api/models/{source.repo}/paths-info/{source.revision}",
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "isekai-derive"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.load(response)
    for item in payload:
        if item.get("path") != source.path:
            continue
        lfs = item.get("lfs")
        if not lfs or not lfs.get("oid"):
            raise SystemExit(f"{source.url()}: not an LFS object, no published SHA-256")
        return str(lfs["oid"]), int(item["size"])
    raise SystemExit(f"{source.url()}: not found at that revision")


def derive() -> Manifest:
    """Build the whole manifest, cross-checking every alternate against the primary."""
    entries: list[ManifestEntry] = []
    for spec in SPECS:
        primary, *alternates = spec.sources
        sha256, size = published_digest(primary)
        if spec.expect_sha256 is not None and sha256 != spec.expect_sha256:
            raise SystemExit(
                f"{spec.dest}: {primary.url()} publishes {sha256}, "
                f"but the publisher states {spec.expect_sha256}"
            )
        for alternate in alternates:
            alt_sha, _ = published_digest(alternate)
            if alt_sha != sha256:
                raise SystemExit(
                    f"{spec.dest}: alternate {alternate.url()} publishes {alt_sha}, "
                    f"primary {primary.url()} publishes {sha256}"
                )
        entries.append(
            {
                "dest": spec.dest,
                "sha256": sha256,
                "bytes": size,
                "sources": [source.url() for source in spec.sources],
            }
        )
    return {
        "pinned": PINNED,
        "publishers": list(PUBLISHERS),
        "entries": entries,
    }


def main() -> None:
    """Derive the manifest and write it to `scripts/models.json`."""
    manifest = derive()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    entries = manifest["entries"]
    total = sum(entry["bytes"] for entry in entries)
    print(
        f"wrote {MANIFEST_PATH.name}: {len(entries)} entries, {total / 2**30:.1f} GiB"
    )


if __name__ == "__main__":
    main()
