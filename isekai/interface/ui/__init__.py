"""The app: the library, each collection's hub and stage ③, served by one local process.

A sibling of `cli.py` rather than a client of it. Review, a tick and an import
call `wiring` and the owning functions directly, and a `Refusal` is caught rather
than scraped out of stderr prose. Prepare and Render are the exceptions by design:
`jobs.py` runs the CLI's stage verbs as children, reading `--progress json` (D4).

The split is what keeps the suite offline. `library.py` reads the library and
each collection's stages and imports no web framework; `bundle.py` builds the browser
bundle or refuses naming the command; `jobs.py` and `events.py` run Prepare and
Render and stream their progress; `app.py` imports the web framework; and
`serve()` below composes them.

**The library and the bundle are refused before a port is bound**, because the
terminal is where the operator is when they start this. A refusal about one collection
or one run is shown on the page, against what it concerns.

**The server never constructs an artifact.** It passes field values to `review`'s
own functions and they own the file's shape and its name -- held by one grep in
`tests/test_ui.py`.
"""

from pathlib import Path

from isekai.foundation.run import Run
from isekai.interface.ui import library
from isekai.interface.ui.bundle import ensure_built
from isekai.interface.wiring import Wiring, wiring_from
from isekai.pipeline.importing import sweep

HOST = "127.0.0.1"


def collection_runs() -> list[Path]:
    """Return the `runs/` of every collection in the library, by collection name.

    A library git can reach is refused as `open_library` refuses it (D18); an absent
    one holds no collection, and nothing is created.
    """
    found = library.root()
    if not found.is_dir():
        return []
    opened = library.open_library(found)
    return [
        folder / library.RUNS
        for folder in library.listed(opened)
        if library.is_collection(folder)
    ]


def drop_thumbnails(run: Run, image: Path) -> list[Path]:
    """Delete `image`'s thumbnails from its library's cache, for the `discard` verb."""
    return library.drop_thumbnails(run, image)


def render_running(run: Run) -> bool:
    """Return whether a render holds `run`'s collection, for the `discard` verb."""
    return library.render_running(run)


def serve(wired: Wiring, *, port: int) -> int:
    """Open the library, print the address, and serve until stopped.

    Bound to the loopback address and nothing else. This is a private tool over a
    directory of personal photographs; a surface that listened on every interface
    would be publishing them to the network the operator happens to be on.
    """
    root = library.open_library(library.root())
    # An import that did not end leaves only staging, which nothing reads again.
    sweep(root)
    flows = library.offered(wired.flows_dir)
    bundle = ensure_built()

    # Imported here, not at module scope: this is the only line that needs a web
    # framework. That keeps FastAPI off `python -m isekai`'s import graph even
    # though it is a declared dependency and so resolvable -- which is the whole
    # of what the `-S` guard in `tests/test_pipeline_cli.py` checks.
    from isekai.interface.ui.app import create_app, run

    print(f"isekai: the library -- http://{HOST}:{port}", file=wired.out)
    app = create_app(
        root,
        wired,
        flows=flows,
        bundle=bundle,
        wire=lambda runs: wiring_from(runs=runs),
        host=HOST,
        port=port,
    )
    # gpunit is asked once now, then only while a session runs or an alert is open.
    app.state.billing.watch()
    try:
        run(app, host=HOST, port=port)
    except KeyboardInterrupt:
        return 130
    return 0
