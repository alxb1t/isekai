import argparse
import json
from pathlib import Path

from isekai.comfy_client import ComfyClient
from isekai.pipeline import run


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Photo -> anime via ComfyUI (Qwen-Image-Edit)."
    )
    p.add_argument("input", help="input photo (jpg/png)")
    p.add_argument("-o", "--output", default="out.png", help="output image path")
    p.add_argument("--prompt", required=True, help="edit instruction")
    p.add_argument(
        "--workflow",
        default="workflows/qwen-image-edit.json",
        help="API-format ComfyUI workflow JSON",
    )
    p.add_argument(
        "--server",
        default="http://127.0.0.1:8188",
        help="ComfyUI base URL (reached via the SSH tunnel)",
    )

    return p.parse_args()


def main():
    args = parse_args()
    workflow = json.loads(Path(args.workflow).read_text())
    client = ComfyClient(args.server)
    run(client, workflow, args.input, args.prompt, args.output)
