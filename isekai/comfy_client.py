"""The ComfyUI HTTP transport -- the one place this package touches the network."""

import json
from pathlib import Path
from typing import Any
from urllib import parse, request

from isekai.comfy_types import ComfyTransport, Image, Workflow
from isekai.multipart import build_multipart


class ComfyClient(ComfyTransport):
    """Thin HTTP transport to a running ComfyUI."""

    def __init__(self, server: str) -> None:
        """Point the client at a ComfyUI base URL, trailing slash optional."""
        self.server = server.rstrip("/")

    def upload_image(self, path: str) -> str:
        """Upload a local image into ComfyUI's input/ folder.

        Returns the stored filename.
        """
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
        with request.urlopen(f"{self.server}/history/{prompt_id}") as resp:
            return json.loads(resp.read())

    def view(self, image: Image) -> bytes:
        """Download one generated image, given its {filename, subfolder, type} dict."""
        query = parse.urlencode(
            {
                "filename": image["filename"],
                "subfolder": image["subfolder"],
                "type": image["type"],
            }
        )
        with request.urlopen(f"{self.server}/view?{query}") as resp:
            return resp.read()
