"""The app: the library, each batch's hub and stage ③, served by one local process.

A sibling of `cli.py` rather than a client of it. Both front ends call `wiring`
and the stage functions directly -- no subprocess, no argv serialization, no
exit codes, and a `Refusal` is caught rather than scraped out of stderr prose.

The split is what keeps the suite offline. `library.py` reads the library and
each batch's stages and imports no web framework; `bundle.py` builds the browser
bundle or refuses naming the command; `app.py` is the only module that imports a
web framework at all; and `serve()` below composes the three.

**The library and the bundle are refused before a port is bound**, because the
terminal is where the operator is when they start this. A refusal about one batch
or one run is shown on the page, against what it concerns.

**The server never constructs an artifact.** It passes field values to `review`'s
own functions and they own the file's shape and its name -- held by one grep in
`tests/test_ui.py`, which replaces the structural guarantee a subprocess gave for
free.
"""

from isekai.interface.ui import library
from isekai.interface.ui.bundle import ensure_built
from isekai.interface.wiring import Wiring, wiring_from

HOST = "127.0.0.1"


def serve(wired: Wiring, *, port: int) -> int:
    """Open the library, print the address, and serve until stopped.

    Bound to the loopback address and nothing else. This is a private tool over a
    directory of personal photographs; a surface that listened on every interface
    would be publishing them to the network the operator happens to be on.
    """
    root = library.open_library(library.root())
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
    run(app, host=HOST, port=port)
    return 0
