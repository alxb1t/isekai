import argparse
import json
from pathlib import Path

from isekai.comfy_client import ComfyClient
from isekai.comfy_types import Overrides
from isekai.models import get_model
from isekai.pipeline import run


def _bounded_float(lo: float, hi: float):
    def parse(value: str) -> float:
        v = float(value)
        if not (lo <= v <= hi):
            raise argparse.ArgumentTypeError(f"must be in [{lo}, {hi}], got {v}")
        return v

    return parse


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Photo -> anime via ComfyUI (Qwen-Image-Edit)."
    )
    p.add_argument("input", help="input photo (jpg/png)")
    p.add_argument("-o", "--output", default="out.png", help="output image path")
    p.add_argument("--prompt", required=True, help="edit instruction")
    p.add_argument(
        "--model",
        choices=["qwen", "animagine", "animagine-i2i", "animagine-i2i-cn"],
        default="animagine-i2i",
        help="which pipeline to run",
    )
    p.add_argument(
        "--workflow",
        default=None,
        help="override the model's default workflow JSON (advanced)",
    )
    p.add_argument(
        "--server",
        default="http://127.0.0.1:8188",
        help="ComfyUI base URL (reached via the SSH tunnel)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for reproducible variation (random if unset)",
    )
    p.add_argument(
        "--variations", type=int, default=1, help="number of varied outputs to generate"
    )
    p.add_argument(
        "--denoise",
        type=_bounded_float(0.0, 1.0),
        default=None,
        help="denoise base value [0, 1] (jitter window for --variations)",
    )
    p.add_argument(
        "--cfg",
        type=_bounded_float(0.0, 30.0),
        default=None,
        help="CFG scale base value [0, 30]",
    )
    p.add_argument(
        "--ip-weight",
        type=_bounded_float(0.0, 1.0),
        default=None,
        help="InstantID ip_weight base value [0, 1]",
    )

    return p.parse_args()


def main():
    args = parse_args()
    model = get_model(args.model)
    workflow = json.loads(Path(args.workflow or model.workflow_path).read_text())
    client = ComfyClient(args.server)

    overrides: Overrides = {}
    if args.denoise is not None:
        overrides["denoise"] = args.denoise
    if args.cfg is not None:
        overrides["cfg"] = args.cfg
    if args.ip_weight is not None:
        overrides["ip_weight"] = args.ip_weight

    run(
        client,
        workflow,
        model.inject,
        args.input,
        args.prompt,
        args.output,
        mutate=model.mutate,
        seed=args.seed,
        variations=args.variations,
        overrides=overrides or None,
    )
