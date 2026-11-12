import json
from collections.abc import Callable, Mapping, Sequence
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request

import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image as Picture

from isekai.boundary import provision
from isekai.boundary.comfy import Image, TransportFailure
from isekai.boundary.comfy import client as comfy_client
from isekai.boundary.ollama import LAYERS
from isekai.boundary.pose import Pose
from isekai.boundary.provision import READER_MANIFEST_PATH, Manifest, load_manifest
from isekai.boundary.sam2 import Embedding
from isekai.foundation.artifacts import DigestRecord
from isekai.foundation.flow import Workflow


def url_of(request: Request | str) -> str:
    """Return the URL a patched opener was handed, a `Request` or a string."""
    return request.full_url if isinstance(request, Request) else request


def stub_comfy(
    monkeypatch: pytest.MonkeyPatch, answer: Callable[[Request | str], object]
) -> None:
    """Send every request `ComfyClient` makes to `answer`, in place of its opener."""

    def open_(request: Request | str, *args: object, **kwargs: object) -> object:
        return answer(request)

    monkeypatch.setattr(comfy_client.OPENER, "open", open_)


# What `FakeComfyClient` reports about itself, in ComfyUI's own shape.
FAKE_SYSTEM = {
    "os": "posix",
    "comfyui_version": "0.3.60",
    "python_version": "3.12.14 (main, Oct 1 2025, 00:00:00) [GCC 13.3.0]",
    "pytorch_version": "2.8.0+cu128",
}

# The device FakeComfyClient lists first, as ComfyUI names it.
FAKE_DEVICE = "cuda:0 NVIDIA L4 : cudaMallocAsync"


class FakeComfyClient:
    """In-memory stand-in for ComfyClient: records calls, replays canned responses.

    Structurally satisfies ComfyTransport, so pipeline.run can't tell it from the
    real client. No network, no GPU.
    """

    def __init__(
        self,
        pending_polls: int = 0,
        image: Image | None = None,
        view_bytes: bytes = b"\x89PNG\r\n",
        report: dict[str, Any] | None = None,
        report_failure: TransportFailure | None = None,
    ) -> None:
        self.pending_polls = pending_polls
        # the system report, or the failure asking for it raises
        if report is None:
            report = {
                "system": dict(FAKE_SYSTEM),
                "devices": [{"name": FAKE_DEVICE, "type": "cuda", "index": 0}],
            }
        self.report = report
        self.report_failure = report_failure
        self.image: Image = image or {
            "filename": "out.png",
            "subfolder": "",
            "type": "output",
        }
        self.view_bytes = view_bytes
        self.prompt_id = "pid-123"
        # recorded calls, for assertions
        self.uploaded: tuple[str, bytes] | None = None
        self.submitted_workflow: Workflow | None = None
        # every submission, in order — `submitted_workflow` keeps only the last,
        # which cannot see a multi-variation run's earlier workflows.
        self.submissions: list[Workflow] = []
        self.history_calls = 0
        self.viewed: Image | None = None
        self.stats_calls = 0

    def upload_image(self, name: str, data: bytes) -> str:
        self.uploaded = (name, data)
        return "uploaded.png"

    def submit(self, workflow: Workflow) -> str:
        self.submitted_workflow = workflow
        self.submissions.append(workflow)
        return self.prompt_id

    def history(self, prompt_id: str) -> dict[str, Any]:
        self.history_calls += 1
        if self.history_calls <= self.pending_polls:
            return {}
        return {prompt_id: {"outputs": {"SaveImage": {"images": [self.image]}}}}

    def view(self, image: Image) -> bytes:
        self.viewed = image
        return self.view_bytes

    def system_stats(self) -> dict[str, Any]:
        self.stats_calls += 1
        if self.report_failure is not None:
            raise self.report_failure
        return self.report


class RecordingComfyClient(FakeComfyClient):
    """A `FakeComfyClient` that keeps every upload, and may reject every graph.

    Each upload is stored under its own name behind `stored-`, so a graph patched
    with the stored names says which image went where.
    """

    def __init__(
        self, *, rejects: TransportFailure | None = None, view_bytes: bytes
    ) -> None:
        super().__init__(view_bytes=view_bytes)
        self.uploads: list[tuple[str, bytes]] = []
        self.rejects = rejects

    def upload_image(self, name: str, data: bytes) -> str:
        self.uploads.append((name, data))
        return f"stored-{name}"

    def submit(self, workflow: Workflow) -> str:
        if self.rejects is not None:
            raise self.rejects
        return super().submit(workflow)


def fetched_by_main(
    monkeypatch: pytest.MonkeyPatch, argv: list[str]
) -> tuple[Manifest, Path]:
    """Return the manifest and models root `provision.main(argv)` hands `fetch`."""
    handed: list[tuple[Manifest, Path]] = []

    def recording(manifest: Manifest, models_dir: Path, fetcher: object) -> int:
        handed.append((manifest, models_dir))
        return 0

    monkeypatch.setattr(provision, "fetch", recording)
    assert provision.main(argv) == 0
    (call,) = handed
    return call


class FakeFetcher:
    """In-memory stand-in for the network seam: canned answers, no network.

    Structurally satisfies `Fetcher`, so `decide` and `fetch` cannot tell it from
    the real thing. `published` maps a source URL to the digest that source claims
    it would serve; a URL absent from the map publishes nothing, which is the case
    where pre-flight has to degrade to post-download verification rather than to
    trust. `served` maps a source URL to the bytes it serves; a URL absent from it
    fails its transfer. `breaks` maps a served URL to how many of its first
    transfers break before it serves. `refuses` maps a URL to the HTTP code it
    answers every transfer with.
    """

    def __init__(
        self,
        published: dict[str, str] | None = None,
        served: dict[str, bytes] | None = None,
        breaks: dict[str, int] | None = None,
        refuses: dict[str, int] | None = None,
    ) -> None:
        self.published = published or {}
        self.served = served or {}
        self.breaks = dict(breaks or {})
        self.refuses = refuses or {}
        # every URL asked about, in order — so a test can assert that a source
        # rejected before transfer was still pre-flighted.
        self.asked: list[str] = []
        # every transfer attempted, in order, with the path it wrote to.
        self.fetched: list[tuple[str, Path]] = []

    def published_digest(self, url: str) -> str | None:
        self.asked.append(url)
        return self.published.get(url)

    def get(self, url: str, into: Path) -> None:
        self.fetched.append((url, into))
        if url in self.refuses:
            into.write_bytes(b"an error page")
            raise HTTPError(url, self.refuses[url], "refused", Message(), None)
        if url not in self.served or self.breaks.get(url, 0) > 0:
            self.breaks[url] = self.breaks.get(url, 0) - 1
            into.write_bytes(b"half a file")
            raise OSError(f"{url} did not answer")
        into.write_bytes(self.served[url])


# The alias `config/caption.json` names, and so the one a real adapter is tested on.
READER = "joycaption-beta-one-q4k"

# The reference a render session's pod boots, as gpunit names it.
SESSION_IMAGE = "ghcr.io/alxb1t/isekai@sha256:" + "d" * 64


def _reader_artifacts() -> dict[str, DigestRecord]:
    """Return the files `config/reader.json` builds `READER` from, keyed by `dest`."""
    manifest = load_manifest(READER_MANIFEST_PATH)
    built = manifest.get("aliases", {})[READER]
    pins = {entry["dest"]: entry["sha256"] for entry in manifest["entries"]}
    return {built[role]: {"sha256": pins[built[role]]} for role in LAYERS}


# What a verified `READER` records as its `artifacts`, in `LAYERS` order.
READER_ARTIFACTS = _reader_artifacts()


def ollama_records(
    root: Path, model: str = READER, *, model_digest: str | None = None
) -> Path:
    """Write Ollama's record of `model` under `root`, and return `root`.

    The record names the files `config/reader.json` pins for `READER`, unless
    `model_digest` names another model file.
    """
    pinned = (record["sha256"] for record in READER_ARTIFACTS.values())
    digests = dict(zip(LAYERS, pinned, strict=True))
    if model_digest is not None:
        digests["model"] = model_digest
    layers = [
        {"mediaType": LAYERS[role], "digest": f"sha256:{digest}"}
        for role, digest in digests.items()
    ]
    record = root / model / "latest"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps({"layers": layers}))
    return root


class FakePoseFinder:
    """A pose finder that answers each `find` with the next pose it was given.

    The photograph is found first and the render second, as `propose` asks. A call
    past the poses given is an `IndexError`, so a test names every call it expects.
    """

    def __init__(self, *poses: Pose | None) -> None:
        """Hold `poses`, one per call, a `None` for an image with no person."""
        self._poses = list(poses)
        self.seen: list[Picture.Image] = []

    def find(self, image: Picture.Image) -> Pose | None:
        """Record `image` and return the next pose."""
        self.seen.append(image)
        return self._poses.pop(0)


class _NoDecoder:
    """A decoder session that is never run: a fake embedding paints its own masks."""

    def get_inputs(self) -> list[Any]:
        raise AssertionError("a fake embedding has no decoder")

    def run(self, outputs: Sequence[str], feed: Mapping[str, Any]) -> list[Any]:
        raise AssertionError("a fake embedding has no decoder")


Point = tuple[float, float]
Painter = Callable[
    [tuple[int, int], Sequence[Point], Sequence[Point]], NDArray[np.bool_]
]


class _Painted(Embedding):
    """An embedding whose mask is `paint`'s, and which records each prompt."""

    def __init__(
        self,
        size: tuple[int, int],
        paint: Painter,
        prompts: list[tuple[int, Any]],
        number: int,
    ) -> None:
        super().__init__(_NoDecoder(), {}, size)
        self._paint = paint
        self._prompts = prompts
        self._number = number

    def mask(
        self, positive: Sequence[Point], negative: Sequence[Point]
    ) -> NDArray[np.bool_]:
        """Record the prompt and return what `paint` makes of it."""
        self._prompts.append((self._number, (list(positive), list(negative))))
        return self._paint(self.size, positive, negative)


class FakeSegmenter:
    """A segmenter whose masks are painted by a function of the size and the prompt.

    `embedded` holds each image given to `embed`, in order; `prompts` holds each
    prompt as the number of the embedding that took it and its positives and negatives.
    """

    def __init__(self, paint: Painter) -> None:
        """Hold `paint`, called with the image's size and the prompt's points."""
        self._paint = paint
        self.embedded: list[Picture.Image] = []
        self.prompts: list[tuple[int, Any]] = []

    def embed(self, image: Picture.Image) -> Embedding:
        """Record `image` and return an embedding that paints its masks."""
        self.embedded.append(image)
        return _Painted(image.size, self._paint, self.prompts, len(self.embedded) - 1)
