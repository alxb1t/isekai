#!/usr/bin/env python3
"""PROTOTYPE — T3: one variable at a time, against the style axis.

F7 says our renders are not under-stylized, they are **off-axis**: posterisation
equal to the photograph's, linework 60x *below* it. Two independent deficits, so
probably two levers. This runs each candidate alone, at one seed, on one subject,
and measures every result on the axes built in T1 and T2.

Patches the graph directly rather than going through the CLI, because the two
levers that matter most -- the negative prompt and the ControlNet leg strengths --
are graph configuration with no flag, by design (`noprompt`, and the deferred
per-leg CLI item). A prototype may reach into the graph; a version may not.

    python prototype/ladder.py --server http://127.0.0.1:8188
"""

import argparse
import copy
import json
from pathlib import Path

from isekai.comfy_client import ComfyClient
from isekai.pipeline import run

SUBJECT = "s4_multitone_bob"  # lost the most: necklace, earrings, hair colour, tee colour
PHOTO = f"inputs/baseline/{SUBJECT}.png"
SEED = 20260907

NEGATIVE = "4"  # CLIPTextEncode, the negative
TILE = "14"  # ControlNetApplyAdvanced, TTPlanet tile
LINEART = "21"  # ControlNetApplyAdvanced, MistoLine


def variants(graph: dict) -> dict[str, tuple[dict, dict]]:
    """Return name -> (patched graph, overrides). One change each, never two."""
    out: dict[str, tuple[dict, dict]] = {}

    out["1_control"] = (copy.deepcopy(graph), {})

    # Q1 / posterisation. v0.10 dropped this pair following the publisher's short
    # form; the renders came back semi-realistic and it was never put back.
    g = copy.deepcopy(graph)
    g[NEGATIVE]["inputs"]["text"] = "realistic, photorealistic, " + g[NEGATIVE]["inputs"]["text"]
    out["2_negative"] = (g, {})

    # F7's larger, cleaner gap. MistoLine is the only leg that draws edges and it
    # runs at 0.2 -- so the graph has an edge mechanism that is nearly switched off.
    g = copy.deepcopy(graph)
    g[LINEART]["inputs"]["strength"] = 0.6
    out["3_lineart"] = (g, {})

    # Q2. The card recommends 0.9 against the 0.2 shipped; tile is the leg that
    # would hold local colour and structure -- the pendant, the tee, the background.
    g = copy.deepcopy(graph)
    g[TILE]["inputs"]["strength"] = 0.9
    out["4_tile"] = (g, {})

    # Last, because it is only meaningful once the register is right.
    out["5_denoise"] = (copy.deepcopy(graph), {"denoise": 0.45})

    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=Path("prototype/renders"))
    p.add_argument("--only", default=None, help="run one variant by name")
    args = p.parse_args()

    graph = json.loads(Path("workflows/pipeline.json").read_text())
    client = ComfyClient(args.server)

    for name, (patched, overrides) in variants(graph).items():
        if args.only and name != args.only:
            continue
        print(f"\n=== {name} {'=' * (60 - len(name))}")
        run(
            client,
            patched,
            PHOTO,
            args.out / name,
            variations=1,
            seed=SEED,
            overrides=overrides or None,
            fixed_dials=True,  # no jitter: the only difference is the one change
        )
        (args.out / name / "variant.json").write_text(
            json.dumps(
                {
                    "variant": name,
                    "subject": SUBJECT,
                    "seed": SEED,
                    "overrides": overrides,
                    "negative": patched[NEGATIVE]["inputs"]["text"],
                    "tile_strength": patched[TILE]["inputs"]["strength"],
                    "lineart_strength": patched[LINEART]["inputs"]["strength"],
                },
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
