"""The ComfyUI HTTP transport -- the one place this package touches the network."""

import http.client
import json
import urllib.error
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib import parse, request

from isekai.boundary.comfy.contract import ComfyTransport, Image, TransportFailure
from isekai.boundary.comfy.multipart import build_multipart
from isekai.foundation.flow import Workflow

# The opener every request goes through. `ProxyHandler({})` reads no environment,
# so an exported `http_proxy` never receives the photograph (docs D6).
OPENER = request.build_opener(request.ProxyHandler({}))

# Seconds a socket operation may wait: a stopped pod must not hold a request open
# while it bills (`0037` design D2).
TIMEOUT = 60


class ComfyClient(ComfyTransport):
    """Thin HTTP transport to a running ComfyUI; a failure is a `TransportFailure`."""

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

            with OPENER.open(req, timeout=TIMEOUT) as resp:
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

            with OPENER.open(req, timeout=TIMEOUT) as resp:
                prompt_id = json.loads(resp.read())["prompt_id"]
            if not isinstance(prompt_id, str) or not prompt_id:
                raise ValueError(f"prompt_id {prompt_id!r} is not a non-empty string")
            return prompt_id

    def history(self, prompt_id: str) -> dict[str, Any]:
        """Return the /history record for prompt_id."""
        with _reported():
            url = f"{self.server}/history/{parse.quote(prompt_id, safe='')}"
            with OPENER.open(url, timeout=TIMEOUT) as resp:
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
            with OPENER.open(f"{self.server}/view?{query}", timeout=TIMEOUT) as resp:
                return resp.read()

    def system_stats(self) -> dict[str, Any]:
        """Return the server's /system_stats report, its versions under `system`."""
        with _reported():
            url = f"{self.server}/system_stats"
            with OPENER.open(url, timeout=TIMEOUT) as resp:
                return json.loads(resp.read())


# How much of an error body a refusal quotes: ComfyUI's names the node and the
# input, and a proxy's HTML page is noise past its first lines.
ERROR_BODY_CHARS = 500


@contextmanager
def _reported() -> Iterator[None]:
    """Turn a failed request into a `TransportFailure` of the kind it was.

    e.g. HTTP 400 -> permanent, HTTP 502 -> transient, a refused connection ->
    transient, a body that is not JSON or not the object asked for -> permanent
    (`0030` design D3).
    """
    try:
        yield
    # Before `URLError`, which `HTTPError` subclasses: an answer is not a tunnel.
    except urllib.error.HTTPError as answered:
        body = _error_body(answered)
        if answered.code < 500:
            raise TransportFailure(
                "permanent",
                f"the endpoint rejected the request with HTTP {answered.code}: {body}",
            ) from answered
        raise TransportFailure(
            "transient",
            f"the endpoint failed with HTTP {answered.code} ({body}); check the "
            "pod's ComfyUI log",
        ) from answered
    except http.client.HTTPException as cut:
        raise TransportFailure(
            "transient",
            f"the endpoint's answer was cut off ({cut!r}); check the pod's ComfyUI log",
        ) from cut
    except (urllib.error.URLError, OSError) as unreachable:
        # A timeout arrives raw or wrapped in a `URLError`; read as its parent
        # class it would send the operator to bring up a pod that is up.
        if isinstance(getattr(unreachable, "reason", unreachable), TimeoutError):
            raise TransportFailure(
                "transient",
                f"the endpoint did not answer within {TIMEOUT} s; check the pod's "
                "ComfyUI log",
            ) from unreachable
        raise TransportFailure(
            "transient",
            f"the rendering endpoint could not be reached ({unreachable}); "
            "bring a pod up with `bash infra/up.sh`, open the tunnel, and pass "
            "its address with `--server` -- or drop `--server` to assemble the "
            "prompts and stop",
        ) from unreachable
    except (ValueError, KeyError, TypeError) as unread:
        raise TransportFailure(
            "permanent",
            "the endpoint answered in a shape this build does not read "
            f"({unread!r}); check that `--server` names a ComfyUI",
        ) from unread


def _error_body(answered: urllib.error.HTTPError) -> str:
    """Return the start of an error response's body, or say it could not be read.

    Printable characters only: the refusal reaches a terminal and an agent.
    """
    try:
        text = answered.read().decode(errors="replace")
        printable = "".join(c for c in text if c.isprintable())
        return printable.strip()[:ERROR_BODY_CHARS]
    except (OSError, http.client.HTTPException):
        return "no body could be read"
