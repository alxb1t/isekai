"""The pipeline's entry point: `python -m isekai <verb>`.

**A second surface, not an extension of the first.** `convert.py` is a shim over
`isekai.cli`, and that parser drives the render path this version promised not to
touch -- so the staged pipeline gets its own parser in its own module and the
existing single-command surface is unchanged (design.md D1). Four separate scripts
were rejected for the same reason one parser was chosen: it would multiply the
stdlib-only guard by four and give argument parsing four places to drift.

**Six verbs, and schema migration is not one of them.** Only schema version 1
exists, so an upgrade command would be a dispatch table with no entries and its
refusal would be unreachable -- nothing can write a version 2 artifact
(design.md D2).

    caption   (1) a photograph in, descriptive prose out
    sheet     (2) prose in, a sheet of canonical tags out
    review    (3) the machine's sheet copied somewhere a human may edit it
    approve   (3) validate the edited sheet and rename it
    generate  (4) assemble every prompt locally, then render
    show          print a run's artifacts and what produced each one

Stdlib only, and held to that by its own subprocess guard beside the one that
holds `convert.py`.
"""

import argparse
import dataclasses
import random
import sys
import urllib.error
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from isekai.caption import ClaudeReader, Reader, caption
from isekai.comfy_client import ComfyClient
from isekai.comfy_types import ComfyTransport, Image, Workflow
from isekai.flow import FLOWS_DIR, load_flow, tracked_flows
from isekai.generate import prepare, render
from isekai.refusal import Refusal
from isekai.review import approve, review
from isekai.run import FRAME_NAME, RUNS_ROOT, Run, across, open_run
from isekai.sheet import ClaudeSorter, Schema, Sorter, load_schema, sheet
from isekai.show import report
from isekai.vocabulary import Vocabulary
from isekai.vocabulary import load as load_vocabulary

# One line of prose per verb, used for both the subcommand list and its own help,
# so the two cannot disagree about what a stage does.
VERBS: tuple[tuple[str, str], ...] = (
    ("caption", "read a photograph into descriptive prose"),
    ("sheet", "sort a caption into a sheet of canonical tags"),
    ("review", "copy a sheet somewhere a human may edit it"),
    ("approve", "validate an edited sheet and mark it approved"),
    ("generate", "assemble the prompts for a run, then render them"),
    ("show", "print a run's artifacts, versions and producers"),
)


def _seed(value: str) -> int:
    """Parse a seed: an unsigned 64-bit integer, refused at parse time if it is not."""
    try:
        seed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from None
    if not 0 <= seed < 2**64:
        raise argparse.ArgumentTypeError(
            f"{seed} is outside the sampler's unsigned 64-bit range"
        )
    return seed


def _count(value: str) -> int:
    """Parse a render count: a positive integer. Every one of them costs money."""
    try:
        count = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from None
    if count < 1:
        raise argparse.ArgumentTypeError("a render count below 1 renders nothing")
    return count


def build_parser() -> argparse.ArgumentParser:
    """Return the pipeline's parser, with one subparser per verb."""
    parser = argparse.ArgumentParser(
        prog="python -m isekai",
        description="The staged pipeline: photograph -> prose -> sheet -> render.",
    )
    verbs = parser.add_subparsers(dest="verb", metavar="verb", required=True)
    made = {
        name: verbs.add_parser(name, help=summary, description=summary)
        for name, summary in VERBS
    }

    for name in made:
        made[name].add_argument(
            "photos",
            nargs="*",
            help="photographs, or run identifiers for a run that already exists",
        )
        # The root every run lives under. It defaults to `.data/runs`, and it is a
        # flag because a version's acceptance run wants its own directory rather
        # than one pile every version adds to. Anywhere it points is still inside
        # `.data/`, which is gitignored -- a run holds a copy of the photograph,
        # so `runs/` holds personal photographs by construction (design.md D14).
        made[name].add_argument(
            "--runs",
            type=Path,
            default=RUNS_ROOT,
            help=f"the directory runs live under (default {RUNS_ROOT.name}/)",
        )
    for name in ("review", "approve", "generate"):
        made[name].add_argument(
            "--flow",
            default=None,
            help="the flow to act on; every approved one by default",
        )
    for name in ("caption", "sheet", "review"):
        made[name].add_argument(
            "--new-version",
            action="store_true",
            help="write the next numbered artifact instead of doing nothing",
        )

    # Mutually exclusive at parse time, so asking for both is refused before any
    # work begins rather than discovered on a rented machine. One verb explores
    # and the other reproduces, and combining them has no meaning (design.md D13).
    render = made["generate"].add_mutually_exclusive_group()
    render.add_argument(
        "--count",
        type=_count,
        default=None,
        help="how many renders per photograph per flow (default 1, seeds drawn)",
    )
    render.add_argument(
        "--seed",
        type=_seed,
        action="append",
        dest="seeds",
        default=None,
        help="render exactly this seed; repeatable, and not combinable with --count",
    )
    # No default, deliberately. Assembly is free and rendering is not, so the
    # invocation that costs money is the one that names where to spend it --
    # `generate` without `--server` assembles every prompt and stops, which is
    # also how a malformed sheet is found before anything is rented.
    made["generate"].add_argument(
        "--server",
        default=None,
        help=(
            "the ComfyUI endpoint, reached through the tunnel; omit it to "
            "assemble every prompt and stop without rendering"
        ),
    )
    return parser


@dataclass
class Wiring:
    """Everything the verbs reach the outside world through, in one place.

    A parameter is a seam only if something else is actually passed through it,
    and something is passed through every one of these: the reader and the sorter
    take their offline doubles, the transport takes the fake the existing suite
    already drives `pipeline.run` with, and the roots take a temporary directory.
    That is what makes the resume assertion -- run everything twice, and nothing
    moved and nothing was called -- provable without a GPU or a network.
    """

    reader: Reader
    sorter: Sorter
    client: ComfyTransport | None
    schema: Schema
    # A thunk, not a value. Only `sheet` and `approve` read the vocabulary, and
    # parsing the 308 KB tag list costs ~50 ms -- but the real cost is that an
    # eager read made `python -m isekai show` impossible on a clone that had not
    # provisioned it. The doubles still inject one; they inject a lambda.
    vocabulary: Callable[[], Vocabulary]
    runs_root: Path = RUNS_ROOT
    flows_dir: Path = FLOWS_DIR
    present: Sequence[str] | None = None
    rng: random.Random = dataclasses.field(default_factory=random.Random)
    out: TextIO = sys.stdout
    err: TextIO = sys.stderr


def wiring(args: argparse.Namespace) -> Wiring:
    """Build the real wiring: the hosted reader and sorter, and the HTTP transport.

    The vocabulary and the schema are read here rather than inside a stage,
    because reading a file is I/O and the stages are the part that must stay
    testable without any.
    """
    server = getattr(args, "server", None)
    return Wiring(
        reader=ClaudeReader(),
        sorter=ClaudeSorter(),
        client=ComfyClient(server) if server else None,
        schema=load_schema(),
        vocabulary=load_vocabulary,
        runs_root=args.runs,
    )


def _run_for(identifier: str, wired: Wiring) -> Run:
    """Return the run an argument names: a photograph to open, or a run to resume.

    A photograph is offered by path and an existing run by its id, and which one
    was meant is decided by what is on disk rather than by a flag.
    """
    directory = wired.runs_root / identifier
    if (directory / FRAME_NAME).is_file():
        return Run(identifier, directory)
    photo = Path(identifier)
    if not photo.is_file():
        raise Refusal(
            f"{identifier!r} is neither a photograph on disk nor a run under "
            f"{wired.runs_root.name}/; give the path to a JPEG or PNG, or the id "
            "`python -m isekai show` prints"
        )
    return open_run(photo, wired.runs_root)


def _flows_for(args: argparse.Namespace, wired: Wiring) -> list[str]:
    """Return the flows a verb acts on: the one named, or every tracked one."""
    named = getattr(args, "flow", None)
    return [named] if named else tracked_flows(wired.flows_dir)


def _matching_flows(wired: Wiring) -> list[str]:
    """Return the flows whose schema and vocabulary this fill would serve.

    The sorting stage is filled once per distinct pair and written to every flow
    declaring it, which is why the stage is never told which flow asked.
    """
    vocabulary = wired.vocabulary()
    return [
        name
        for name in tracked_flows(wired.flows_dir)
        if (flow := load_flow(name, wired.flows_dir)).schema
        == f"{wired.schema.name}.v{wired.schema.version}"
        and flow.vocabulary["sha256"] == vocabulary.digest
    ]


def dispatch(args: argparse.Namespace, wired: Wiring) -> int:
    """Run one verb over every identifier given, reporting every refusal together.

    **Batch is the general form here and per-item is the special case.** Assembly
    has to finish for the whole batch before any endpoint is acquired, so
    `generate` takes the targets itself; every other verb is per-item, and one
    photograph's failure does not cost the others their turn. Refusals are
    collected and printed at the end, and the exit status says whether any fired.
    """
    verb = str(args.verb)
    targets = list(args.photos)
    if verb == "generate":
        refused = _generate(args, wired, targets)
    else:
        refused = across(targets, _per_item(verb, args, wired))
    for message in refused:
        print(f"refused: {message}", file=wired.err)
    return 1 if refused else 0


def _per_item(
    verb: str, args: argparse.Namespace, wired: Wiring
) -> Callable[[str], None]:
    """Return the work one identifier gets, with everything run-independent done.

    The flows a verb acts on are a property of the wiring, not of the photograph,
    so they are resolved once here rather than re-read from disk per identifier.
    """
    new_version = bool(getattr(args, "new_version", False))
    flows = _flows_for(args, wired) if verb in ("review", "approve") else []
    matching = _matching_flows(wired) if verb == "sheet" else []

    def work(identifier: str) -> None:
        run = _run_for(identifier, wired)
        if verb == "caption":
            _say(
                wired,
                run,
                "caption",
                caption(run, wired.reader, new_version=new_version),
            )
        elif verb == "sheet":
            written = sheet(
                run,
                wired.sorter,
                wired.schema,
                wired.vocabulary(),
                matching,
                new_version=new_version,
            )
            for path in written or [None]:
                _say(wired, run, "sheet", path)
        elif verb == "review":
            for flow in flows:
                _say(wired, run, "review", review(run, flow, new_version=new_version))
        elif verb == "approve":
            for flow in flows:
                written, warnings = approve(run, flow, wired.schema, wired.vocabulary())
                for warning in warnings:
                    print(f"warning: {warning}", file=wired.err)
                _say(wired, run, "approve", written)
        elif verb == "show":
            for line in report(run):
                print(line, file=wired.out)
        else:
            raise Refusal(f"{verb!r} is not a stage this build runs")

    return work


def _generate(
    args: argparse.Namespace, wired: Wiring, targets: Sequence[str]
) -> list[str]:
    """Assemble every prompt in the batch, and only then reach for the endpoint.

    **The whole batch, before anything is acquired.** Assembly is free and
    rendering is not, so a malformed sheet should cost nothing rather than a boot
    and several minutes of waiting -- and doing the batch first is what turns that
    from a per-item saving into a guarantee. Interleaving them would rent a
    machine and then discover the third sheet was broken.
    """
    flows = {name: load_flow(name, wired.flows_dir) for name in _flows_for(args, wired)}
    ready: list[tuple[Run, str]] = []

    def assemble_one(identifier: str) -> None:
        run = _run_for(identifier, wired)
        for flow, path in prepare(run, flows, wired.schema).items():
            print(f"{run.id}: assembled {flow}/{path.name}", file=wired.out)
            ready.append((run, flow))

    refused = across(list(targets), assemble_one)
    if wired.client is None:
        return refused

    client = _Reporting(wired.client)

    def render_one(pair: tuple[Run, str]) -> None:
        run, flow = pair
        produced = render(
            run,
            flows[flow],
            client,
            count=args.count,
            seeds=args.seeds,
            rng=wired.rng,
            present=wired.present,
        )
        for made in produced:
            print(f"{run.id}: rendered {flow}/{made.image.name}", file=wired.out)
        if not produced:
            print(f"{run.id}: {flow} is already rendered", file=wired.out)

    return refused + across(ready, render_one)


@dataclass(frozen=True)
class _Reporting:
    """The transport, with every network error turned into a named refusal."""

    inner: ComfyTransport

    def upload_image(self, path: str) -> str:
        """Upload a photograph, refusing legibly if the endpoint is unreachable."""
        with _reported():
            return self.inner.upload_image(path)

    def submit(self, workflow: Workflow) -> str:
        """Queue a graph, refusing legibly if the endpoint is unreachable."""
        with _reported():
            return self.inner.submit(workflow)

    def history(self, prompt_id: str) -> dict[str, Any]:
        """Poll a queued graph, refusing legibly if the endpoint is unreachable."""
        with _reported():
            return self.inner.history(prompt_id)

    def view(self, image: Image) -> bytes:
        """Download one render, refusing legibly if the endpoint is unreachable."""
        with _reported():
            return self.inner.view(image)


@contextmanager
def _reported() -> Iterator[None]:
    """Turn a transport-level network error into a `Refusal` naming the remedy."""
    try:
        yield
    except (urllib.error.URLError, OSError) as unreachable:
        raise Refusal(
            f"the rendering endpoint could not be reached ({unreachable}); "
            "bring a pod up with `bash infra/up.sh`, open the tunnel, and pass "
            "its address with `--server` -- or drop `--server` to assemble the "
            "prompts and stop"
        ) from unreachable


def _say(wired: Wiring, run: Run, verb: str, written: Path | None) -> None:
    """Report what a stage did, including that it was already complete."""
    if written is None:
        print(f"{run.id}: {verb} is already complete", file=wired.out)
    else:
        print(f"{run.id}: {verb} wrote {written.name}", file=wired.out)


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the pipeline's arguments and dispatch to the named stage."""
    args = build_parser().parse_args(argv)
    try:
        return dispatch(args, wiring(args))
    except Refusal as refused:
        print(f"refused: {refused}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
