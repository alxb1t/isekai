#!/usr/bin/env python3
"""PROTOTYPE — T6/T6b: the chosen register across every subject, and its frontier.

**T5 is answered: the target register is `notile`** — a rendered anime
illustration, not a flat cel screencap (FINDINGS.md F10). That is the shipped
graph with **one leg switched off**: TTPlanet's tile ControlNet, which conditions
on the photograph's local colour and continuous tone and therefore keeps dragging
the render back toward looking photographic.

Two questions, one session:

    T6   does the register hold beyond s4?      all six subjects
    T6b  does LOW denoise recover identity      the F9 direction, re-run under
         under THIS register?                   the chosen register rather than
                                                the flat-cel one it was found in

F9's frontier was found under the *flat* register (cel-shading prompt, lineart
0.6). The chosen register is different, so its frontier has to be found again --
carrying the number over would be assuming the answer.

    python prototype/notile.py --server http://127.0.0.1:8188
"""

import argparse
import copy
import json
from pathlib import Path

from isekai.comfy_client import ComfyClient
from isekai.pipeline import run
from prototype.archive.ladder import TILE

SUBJECTS = [
    "s1_control_blonde",
    "s2_control_brunette",
    "s3_multitone_balayage",
    "s4_multitone_bob",
    "s5_small_face",
    "s6_landscape",
]
SEED = 20260907
SEEDS_B = [20260908, 20260909]  # seed stability, on one subject only


def notile(graph: dict) -> dict:
    """The chosen register: everything shipped, tile off."""
    g = copy.deepcopy(graph)
    g[TILE]["inputs"]["strength"] = 0.0
    return g


def jobs() -> list[tuple[str, str, float, int]]:
    """(name, subject, denoise, seed). Kept flat so the plan is readable."""
    out = []
    # T6 -- the register at its shipped denoise, everywhere.
    for s in SUBJECTS:
        out.append((f"20_notile_d065/{s}", s, 0.65, SEED))
    # T6b -- the identity-recovery candidate, everywhere, so the comparison is
    # per subject rather than pooled.
    for s in SUBJECTS:
        out.append((f"21_notile_d045/{s}", s, 0.45, SEED))
    # Is lower still better? Two subjects is enough to see a direction.
    for s in ("s4_multitone_bob", "s1_control_blonde"):
        out.append((f"22_notile_d035/{s}", s, 0.35, SEED))
    # Seed stability at the candidate, one subject. F9 was one seed throughout,
    # which is the weakest thing about it.
    for i, seed in enumerate(SEEDS_B):
        out.append((f"23_notile_d045_seed{i + 1}/s4_multitone_bob", "s4_multitone_bob", 0.45, seed))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=Path("prototype/renders"))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    graph = notile(json.loads(Path("workflows/pipeline.json").read_text()))
    plan = jobs()
    print(f"{len(plan)} renders, tile={graph[TILE]['inputs']['strength']}")
    for name, subject, denoise, seed in plan:
        print(f"  {name:44s} d={denoise} seed={seed}")
    if args.dry_run:
        return

    client = ComfyClient(args.server)
    for name, subject, denoise, seed in plan:
        print(f"\n=== {name} d={denoise} ===")
        run(
            client,
            graph,
            f"inputs/baseline/{subject}.png",
            args.out / name,
            variations=1,
            seed=seed,
            overrides={"denoise": denoise},
            fixed_dials=True,
        )


if __name__ == "__main__":
    main()
