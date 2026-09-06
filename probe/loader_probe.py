r"""Ask the pod's own `LoadImage` what it does with an EXIF `Orientation`.

Exit 0 cannot answer this. If `LoadImage` did **not** transpose, the graph would
receive landscape pixels and `ImageScale` -- which scales to the exact target
rather than fitting to it -- would squash them into the portrait target. The
render succeeds either way and `run.json` records the same dimensions either
way, so the working case and the broken case are indistinguishable from the
outside (design.md D11).

So: a two-node graph, `LoadImage` -> `SaveImage`, no diffusion, over the same
HTTP API the renders use. The saved file's dimensions are the answer --
transposed gives one pair, untransposed the other. It costs seconds and no GPU,
which is why it runs before the render budget is spent.

The same call settles the PNG question phase 7 turns on (design.md D12): PNG can
carry an `eXIf` chunk that Pillow reads and `ImageOps.exif_transpose` acts on,
and every input this project has ever rendered is a PNG. Reading `nodes.py`
would establish what Pillow is *asked* to do, not what the pinned build does.

This graph lives here and never in `workflows/`, so the one-path rule is
untouched.

    python probe/loader_probe.py --server http://127.0.0.1:8188 \
        --out <dir> <image> [<image> ...]
"""

import argparse
import json
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from isekai.comfy_client import ComfyClient  # noqa: E402

PROBE_GRAPH_PATH = Path(__file__).resolve().parent / "loader_probe_graph.json"


def png_dimensions(data: bytes) -> tuple[int, int]:
    """Return the width and height a PNG's IHDR declares."""
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def probe_one(client: ComfyClient, path: Path, out: Path) -> dict[str, object]:
    """Round-trip one image through `LoadImage` -> `SaveImage` and measure it."""
    uploaded = client.upload_image(str(path))
    graph = json.loads(PROBE_GRAPH_PATH.read_text())
    graph["1"]["inputs"]["image"] = uploaded

    prompt_id = client.submit(graph)
    while True:
        history = client.history(prompt_id)
        if prompt_id in history:
            break
        time.sleep(1)

    image = history[prompt_id]["outputs"]["2"]["images"][0]
    data = client.view(image)
    saved = out / f"{path.stem}.saved.png"
    saved.write_bytes(data)

    width, height = png_dimensions(data)
    return {
        "input": path.name,
        "uploaded_as": uploaded,
        "saved_as": saved.name,
        "saved_width": width,
        "saved_height": height,
    }


def main() -> int:
    """Probe every image given and write the verdicts as JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--out", required=True, help="destination directory")
    parser.add_argument("images", nargs="+")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    client = ComfyClient(args.server)

    results = [probe_one(client, Path(p), out) for p in args.images]
    (out / "loader_probe.json").write_text(json.dumps(results, indent=2) + "\n")

    for r in results:
        print(f"{r['input']:<20} saved {r['saved_width']}x{r['saved_height']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
