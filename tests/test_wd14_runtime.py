"""The WD14 boundary's runtime half: the preparation, the opener and one real graph.

`tests/test_wd14.py` holds the boundary with no wheel, so `prepare`, `OnnxSession` and
`open_session` reach none of their lines there. This file imports `numpy` and `Pillow`
and holds those lines by value: the preparation on photographs small enough to write
out, the opener over a stub runtime, and one tiny graph through the real runtime, its
bytes built from the standard library.
"""

import importlib
from pathlib import Path

import numpy
import pytest
from PIL import Image

from isekai.boundary import provision, wd14
from isekai.boundary.wd14 import (
    LABELS_DEST,
    MODEL_DEST,
    OnnxSession,
    open_session,
    prepare,
    read_labels,
)
from tests.stages import INDEX
from tests.test_wd14 import TELEMETRY_SWITCH, _planted

WHITE = [255, 255, 255]


# --- the preparation ------------------------------------------------------------


@pytest.mark.spec("tagging:seam:the-photograph-is-prepared-by-the-graphs-rule")
def test_a_photograph_with_a_transparent_pixel_is_composited_padded_and_handed_over_blue_first(  # noqa: E501 -- the name is the one the plan's check runs
    tmp_path: Path,
) -> None:
    photo = tmp_path / "wide.png"
    image = Image.new("RGBA", (2, 1))
    image.putpixel((0, 0), (0, 0, 0, 0))
    image.putpixel((1, 0), (255, 0, 0, 255))
    image.save(photo)

    prepared = numpy.asarray(prepare(photo, 2))

    assert prepared.dtype == numpy.float32
    assert prepared.tolist() == [[[WHITE, [0, 0, 255]], [WHITE, WHITE]]]


@pytest.mark.spec("tagging:seam:the-photograph-is-prepared-by-the-graphs-rule")
def test_an_opaque_photograph_is_centred_on_white_in_blue_green_red(
    tmp_path: Path,
) -> None:
    photo = tmp_path / "wide.png"
    image = Image.new("RGB", (4, 2), (10, 20, 30))
    image.paste((40, 50, 60), (2, 0, 4, 2))
    image.save(photo)

    prepared = numpy.asarray(prepare(photo, 4))

    cut = [[30, 20, 10], [30, 20, 10], [60, 50, 40], [60, 50, 40]]
    assert prepared.tolist() == [[[WHITE] * 4, cut, cut, [WHITE] * 4]]


# --- the opener -----------------------------------------------------------------


class _Input:
    name = "x"
    shape = ("batch", 4, 4, 3)


class _Opened:
    def get_inputs(self) -> list[_Input]:
        return [_Input()]


class _RecordingRuntime:
    """A stand-in `onnxruntime` that records what it was asked to open."""

    def __init__(self) -> None:
        self.opened: list[tuple[str, list[str]]] = []

    def InferenceSession(self, path: str, providers: list[str]) -> _Opened:  # noqa: N802
        self.opened.append((path, providers))
        return _Opened()


def _stubbed(monkeypatch: pytest.MonkeyPatch) -> _RecordingRuntime:
    """Return the runtime `wd14` now imports, with the telemetry switch undone."""
    runtime = _RecordingRuntime()
    monkeypatch.setenv(TELEMETRY_SWITCH, "0")
    monkeypatch.delenv(TELEMETRY_SWITCH)
    monkeypatch.setattr(
        wd14,
        "_require",
        lambda module: (
            runtime if module == "onnxruntime" else importlib.import_module(module)
        ),
    )
    return runtime


@pytest.mark.spec("tagging:pin:the-graph-is-opened-only-after-both-digests-verify")
def test_a_graph_whose_bytes_differ_from_its_pin_is_never_opened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = _planted(tmp_path, {LABELS_DEST: INDEX.encode(), MODEL_DEST: b"graph"})
    (tmp_path / MODEL_DEST).write_bytes(b"other bytes")
    monkeypatch.setattr(provision, "load_manifest", lambda _path=None: manifest)
    runtime = _stubbed(monkeypatch)

    with pytest.raises(provision.DigestMismatch) as refused:
        open_session(tmp_path)

    assert MODEL_DEST in str(refused.value)
    assert runtime.opened == []


@pytest.mark.spec("tagging:pin:the-graph-is-opened-only-after-both-digests-verify")
def test_the_session_opens_the_verified_path_on_the_cpu(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = _planted(tmp_path, {LABELS_DEST: INDEX.encode(), MODEL_DEST: b"graph"})
    monkeypatch.setattr(provision, "load_manifest", lambda _path=None: manifest)
    runtime = _stubbed(monkeypatch)

    tagger = open_session(tmp_path)

    assert runtime.opened == [(str(tmp_path / MODEL_DEST), ["CPUExecutionProvider"])]
    assert tagger.labels == tuple(read_labels(INDEX))
    assert tagger.pins == {
        entry["dest"]: {"sha256": entry["sha256"]} for entry in manifest["entries"]
    }


# --- one tiny graph through the real runtime ------------------------------------


def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        low = value & 0x7F
        value >>= 7
        if value:
            out.append(low | 0x80)
        else:
            out.append(low)
            return bytes(out)


def _number(field: int, value: int) -> bytes:
    return _varint(field << 3) + _varint(value)


def _message(field: int, body: bytes) -> bytes:
    return _varint(field << 3 | 2) + _varint(len(body)) + body


def _text(field: int, value: str) -> bytes:
    return _message(field, value.encode())


def _dimension(size: int | str) -> bytes:
    return _message(1, _number(1, size) if isinstance(size, int) else _text(2, size))


def _tensor(name: str, shape: tuple[int | str, ...]) -> bytes:
    dims = b"".join(_dimension(size) for size in shape)
    kind = _message(1, _number(1, 1) + _message(2, dims))
    return _text(1, name) + _message(2, kind)


def _tiny_graph(edge: int) -> bytes:
    """Return an ONNX model of one `Flatten` over a batch of `edge` by `edge` RGB."""
    node = _text(1, "x") + _text(2, "y") + _text(3, "flatten") + _text(4, "Flatten")
    graph = (
        _message(1, node)
        + _text(2, "tiny")
        + _message(11, _tensor("x", ("batch", edge, edge, 3)))
        + _message(12, _tensor("y", ("batch", edge * edge * 3)))
    )
    return _number(1, 8) + _message(8, _number(2, 13)) + _message(7, graph)


@pytest.mark.spec("tagging:seam:the-photograph-is-prepared-by-the-graphs-rule")
def test_a_tiny_graph_run_through_the_real_runtime_returns_what_prepare_handed_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(TELEMETRY_SWITCH, "0")
    monkeypatch.delenv(TELEMETRY_SWITCH)
    model = tmp_path / "tiny.onnx"
    model.write_bytes(_tiny_graph(3))
    photo = tmp_path / "square.png"
    image = Image.new("RGB", (3, 3), (200, 100, 50))
    image.putpixel((0, 0), (10, 20, 30))
    image.save(photo)

    session = OnnxSession(model)
    answered = list(session.run(photo))

    assert session.dimension == 3
    assert answered == numpy.asarray(prepare(photo, 3)).reshape(-1).tolist()
    assert answered[:3] == [30.0, 20.0, 10.0]
