"""The ComfyUI HTTP transport -- the one place this package touches the network."""

import json
import urllib.error
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib import parse, request

from isekai.boundary.comfy.contract import ComfyTransport, Image, Unreachable
from isekai.boundary.comfy.multipart import build_multipart
from isekai.foundation.flow import Workflow


class ComfyClient(ComfyTransport):
    """Thin HTTP transport to a running ComfyUI; a network error is `Unreachable`."""

    def __init__(self, server: str) -> None:
        """Point the client at a ComfyUI base URL, trailing slash optional."""
        self.server = server.rstrip("/")

    def upload_image(self, path: str) -> str:
        """Upload a local image into ComfyUI's input/ folder.

        Returns the stored filename.
        """
        with _reported():
            body, content_type = build_multipart(
                fields={"overwrite": "true"},
                files={
                    "image": (
                        Path(path).name,
                        Path(path).read_bytes(),
                        "application/octet-stream",
                    )
                },
            )

            req = request.Request(
                f"{self.server}/upload/image",
                data=body,
                headers={"Content-Type": content_type},
                method="POST",
            )

            with request.urlopen(req) as resp:
                return json.loads(resp.read())["name"]

    def submit(self, workflow: Workflow) -> str:
        """Queue a workflow and return its prompt_id."""
        with _reported():
            req = request.Request(
                f"{self.server}/prompt",
                data=json.dumps({"prompt": workflow}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with request.urlopen(req) as resp:
                return json.loads(resp.read())["prompt_id"]

    def history(self, prompt_id: str) -> dict[str, Any]:
        """Return the /history record for prompt_id."""
        with _reported():
            with request.urlopen(f"{self.server}/history/{prompt_id}") as resp:
                return json.loads(resp.read())

    def view(self, image: Image) -> bytes:
        """Download one generated image, given its {filename, subfolder, type} dict."""
        with _reported():
            query = parse.urlencode(
                {
                    "filename": image["filename"],
                    "subfolder": image["subfolder"],
                    "type": image["type"],
                }
            )
            with request.urlopen(f"{self.server}/view?{query}") as resp:
                return resp.read()


@contextmanager
def _reported() -> Iterator[None]:
    """Turn a transport-level network error into a `Refusal` naming the remedy.

    `Unreachable` rather than a bare `Refusal`, because nothing that reaches
    here says anything about the graph: the pod went away, the tunnel closed, or
    it was never opened. Every caller that only reports a refusal is unaffected;
    the one that writes an error record records this as transient (v0.13 R7).
    """
    try:
        yield
    except (urllib.error.URLError, OSError) as unreachable:
        raise Unreachable(
            f"the rendering endpoint could not be reached ({unreachable}); "
            "bring a pod up with `bash infra/up.sh`, open the tunnel, and pass "
            "its address with `--server` -- or drop `--server` to assemble the "
            "prompts and stop"
        ) from unreachable
