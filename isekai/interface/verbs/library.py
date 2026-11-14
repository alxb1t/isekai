"""The library's verbs: `import`, `compare` and `ui`."""

import argparse
from pathlib import Path

from isekai.foundation.refusal import Refusal
from isekai.foundation.run import RUNS_ROOT, across
from isekai.interface.compare_view import write_page
from isekai.interface.verbs.common import Verb
from isekai.interface.wiring import Wiring, trackable
from isekai.pipeline.importing import (
    SOURCES,
    Staged,
    cancel,
    commit,
    read,
    stage,
    upload_limit,
)

# The review surface's loopback port. Declared here rather than in the package it
# starts, because the parser is the one authority for what a flag defaults to --
# and importing the surface at module scope is exactly what the `-S` guard
# forbids this file from doing.
DEFAULT_PORT = 8517


def run_ui(args: argparse.Namespace, wired: Wiring) -> int:
    """Serve the app over the library, blocking until the operator stops it.

    **The import is inside this function, and it is load-bearing.**
    `tests/test_pipeline_cli.py` imports the entry point with `-S`, site-packages
    off the path, and walks this module's module-level imports: nothing there may
    need a wheel, and `isekai.interface.ui` reaches FastAPI. A top-level import
    here would put a web framework on `python -m isekai`'s import graph and turn
    that guard red for every verb, including each one that never serves anything.
    """
    from isekai.interface.ui import serve

    return serve(wired, port=int(args.port))


def run_import(args: argparse.Namespace, wired: Wiring) -> int:
    """Read each file into the collection's staging, commit what is clean, and report.

    No file that is not cleaned is imported: that choice is the page's, one file
    at a time.
    """
    collection = Path(args.collection).resolve()
    if trackable(collection.parent):
        raise Refusal(
            f"--collection {collection} is inside this repository and outside its "
            "ignored .data/ root; a collection holds copies of photographs, so it "
            "would be one `git add` from being published -- point --collection "
            "under .data/ or at a directory outside the repository"
        )
    staging = stage(collection.parent)
    limit = upload_limit()
    staged: list[Staged] = []
    try:
        refused = across(
            list(args.files), lambda file: staged.append(read(file, staging, limit))
        )
        for item in staged:
            print(staged_line(item), file=wired.out)
        if any(item.state in ("ready", "converted") for item in staged):
            add = (collection / SOURCES).is_dir()
            done = commit(staging, collection.parent, collection.name, add=add)
            for name in done.skipped:
                print(f"{name}: skipped, a source holds its bytes", file=wired.out)
            if done.written:
                print(
                    f"{collection.name}: imported {', '.join(done.written)}",
                    file=wired.out,
                )
    except Refusal as uncommitted:
        refused.append(str(uncommitted))
    finally:
        cancel(staging)
    for message in refused:
        print(f"refused: {message}", file=wired.err)
    return 1 if refused else 0


def staged_line(item: Staged) -> str:
    """Return one file's result. e.g. "a.jpg: not cleaned, carries XMP; left out"."""
    if item.state == "not cleaned":
        return f"{item.name}: not cleaned, carries {', '.join(item.carries)}; left out"
    if item.state == "skipped":
        return f"{item.name}: skipped, its bytes are already read"
    return f"{item.name}: {item.state}"


def run_compare(args: argparse.Namespace, wired: Wiring) -> int:
    """Write the collection's page of photographs beside renders, printing its path."""
    print(write_page(args.collection, wired.flows_dir), file=wired.out)
    return 0


def ui_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `ui`'s arguments to `parser`."""
    # No flow, input or runs root: the app serves every collection of the library
    # `ISEKAI_LIBRARY` names, and its page selects one (D1).
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"the loopback port to serve on (default {DEFAULT_PORT})",
    )
    parser.set_defaults(photos=[], runs=RUNS_ROOT)


def import_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `import`'s arguments to `parser`."""
    parser.add_argument(
        "--collection",
        type=Path,
        required=True,
        help="the collection directory; made when absent, else files join its sources/",
    )
    parser.add_argument(
        "files", nargs="+", type=Path, help="the photographs to clean and add"
    )
    parser.set_defaults(photos=[], runs=RUNS_ROOT)


def compare_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `compare`'s arguments to `parser`."""
    parser.add_argument(
        "collection",
        type=Path,
        help="the collection directory, holding runs/; the page is written there",
    )
    # Every namespace keeps one shape; `compare` reads its runs from the collection.
    parser.set_defaults(photos=[], runs=RUNS_ROOT)


IMPORT_ROW = Verb("import", import_arguments, run_import)
COMPARE_ROW = Verb("compare", compare_arguments, run_compare)
UI_ROW = Verb("ui", ui_arguments, run_ui)
