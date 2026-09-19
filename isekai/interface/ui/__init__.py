"""The review surface: stage ③ in a browser, served by one local process.

A sibling of `cli.py` rather than a client of it. Both front ends call `wiring`
and the stage functions directly -- no subprocess, no argv serialization, no
exit codes, and a `Refusal` is caught rather than scraped out of stderr prose
(design.md D1).

Four modules, and the split is what keeps the suite offline. `batch.py` holds the
batch and the whole startup refusal order and imports no web framework, so that
order is tested without the `ui` extra; `bundle.py` builds the browser bundle or
refuses naming the command; `app.py` is the only module that imports the extra at
all; and `serve()` below composes the three.

**Everything refusable is refused before a port is bound**, because the terminal
is where the operator already is when they start this, and a `Refusal` there can
name a command and a path. The browser has no designed home for one until a
refusal surface exists, so it gets a single header line and nothing more.

**The server never constructs an artifact.** It passes field values to `review`'s
own functions and they own the envelope and the filename -- held by one grep in
`tests/test_ui.py`, which replaces the structural guarantee a subprocess gave for
free.
"""

from collections.abc import Sequence

from isekai.interface.ui.batch import establish
from isekai.interface.ui.bundle import ensure_built
from isekai.interface.wiring import Wiring

HOST = "127.0.0.1"


def serve(wired: Wiring, flow: str, identifiers: Sequence[str], *, port: int) -> int:
    """Establish the batch, print the address, and serve until stopped.

    Bound to the loopback address and nothing else. This is a private tool over a
    directory of personal photographs; a surface that listened on every interface
    would be publishing them to the network the operator happens to be on.
    """
    batch = establish(wired, flow, identifiers, bundle=ensure_built)

    # Imported here, not at module scope: this is the only line that needs the
    # `ui` extra, and the batch above is established without it.
    from isekai.interface.ui.app import create_app, run

    print(
        f"{batch.flow.id}: {len(batch.inputs)} inputs, "
        f"{batch.approved_count} approved -- http://{HOST}:{port}",
        file=wired.out,
    )
    run(create_app(wired, batch), host=HOST, port=port)
    return 0
