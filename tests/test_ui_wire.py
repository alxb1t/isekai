"""The bodies the page builds, held against the key tuples the server reads.

`ui/src/test/wire.json` is read here and by `ui/src/api.test.ts`: the page's side
asserts what its builders send, this side asserts the server's tuples and routes.
"""

import json
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("fastapi")

from fastapi.routing import APIRoute  # noqa: E402

from isekai.boundary.gpu import Seams  # noqa: E402
from isekai.interface.ui import HOST  # noqa: E402
from isekai.interface.ui import app as app_module  # noqa: E402
from isekai.interface.ui.app import create_app  # noqa: E402
from tests.stages import bare_wiring  # noqa: E402

PORT = 8768
WIRE = Path(__file__).parent.parent / "ui" / "src" / "test" / "wire.json"


def wire_faults(
    bodies: Sequence[Mapping[str, Any]],
    tuples: Mapping[str, Sequence[str]],
    routes: Collection[tuple[str, str]],
) -> list[str]:
    """Return a line for each way `bodies` disagree with `tuples` and `routes`.

    e.g. an entry whose `server` is no tuple -> "bake: BAKE_KEYS is no key tuple"
    """
    faults: list[str] = []
    for body in bodies:
        builder, server = body["builder"], body["server"]
        keys, optional = body["keys"], body.get("optional", [])
        if server not in tuples:
            faults.append(f"{builder}: {server} is no key tuple of the server")
        elif sorted(key for key in keys if key not in optional) != sorted(
            tuples[server]
        ):
            faults.append(f"{builder}: its keys less optional are not {server}")
        for key in optional:
            if key not in keys:
                faults.append(f"{builder}: optional {key} is not among its keys")
        if (body["method"], body["path"]) not in routes:
            faults.append(
                f"{builder}: the server has no {body['method']} {body['path']}"
            )
    named = {body["server"] for body in bodies}
    faults.extend(
        f"{name}: no entry names this tuple" for name in tuples if name not in named
    )
    return faults


def _routes(tmp_path: Path) -> set[tuple[str, str]]:
    """Return the method and path of each route `create_app` serves."""
    (tmp_path / "lib" / "b" / "sources").mkdir(parents=True)
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")
    wired = bare_wiring(
        runs_root=tmp_path / "lib" / "b" / "runs",
        session=Seams(environ={}),
    )
    app = create_app(
        tmp_path / "lib",
        wired,
        flows=("summon-anime-wai",),
        bundle=dist,
        wire=lambda runs: wired,
        host=HOST,
        port=PORT,
    )
    return {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods or ()
    }


@pytest.mark.spec_exempt(
    "structural: the page's request bodies and the server's key tuples agree"
)
def test_the_page_bodies_agree_with_the_server_key_tuples(tmp_path: Path) -> None:
    bodies = json.loads(WIRE.read_text())["bodies"]
    tuples = {
        name: value
        for name, value in vars(app_module).items()
        if name.endswith("_KEYS")
    }

    assert wire_faults(bodies, tuples, _routes(tmp_path)) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_page_bodies_agree_with_the_server_key_tuples"
)
def test_a_fixture_that_drifts_from_the_server_is_caught() -> None:
    tuples = {"A_KEYS": ("x", "y"), "B_KEYS": ("z",), "C_KEYS": ("w",)}
    routes = {("POST", "/a"), ("PUT", "/b")}
    agreeing = [
        {
            "builder": "a",
            "method": "POST",
            "path": "/a",
            "keys": ["x", "y"],
            "server": "A_KEYS",
        },
        {
            "builder": "b",
            "method": "PUT",
            "path": "/b",
            "keys": ["z", "e"],
            "server": "B_KEYS",
            "optional": ["e"],
        },
        {
            "builder": "c",
            "method": "POST",
            "path": "/a",
            "keys": ["w"],
            "server": "C_KEYS",
        },
    ]
    assert wire_faults(agreeing, tuples, routes) == []

    drifted = [
        {**agreeing[0], "keys": ["x"]},
        {**agreeing[1], "server": "NOPE_KEYS"},
        {**agreeing[2], "path": "/gone"},
    ]
    faults = wire_faults(drifted, tuples, routes)

    assert [fault.split(":")[0] for fault in faults] == ["a", "b", "c", "B_KEYS"]
    assert "its keys less optional are not A_KEYS" in faults[0]
    assert "NOPE_KEYS is no key tuple" in faults[1]
    assert "the server has no POST /gone" in faults[2]
    assert "no entry names this tuple" in faults[3]
