"""Score a batch of runs against the cohort its photographs came from.

    uv run python -m evaluation <batch>/runs --cohort <cohort>

Each run is matched to its cohort photograph by the digest its frame records;
the first seed of each flow's latest render group is ranked against every cohort
photograph. The record is written beside the runs, as `<batch>/evaluation.json`,
and the table printed; a run the record does not score is counted there and named
on stderr alone.
A separate entry point, not a verb: the evaluator measures the pipeline and
`isekai` never imports it.
"""

import argparse
import shlex
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from evaluation.cohort import (
    Cohort,
    Photograph,
    Record,
    Row,
    Vector,
    load_cohort,
    rank,
    record,
    scored,
    table,
    unscored,
)
from evaluation.eval_models import DETECTOR, ENCODER, load_eval_manifest
from evaluation.record import destination as record_destination
from evaluation.record import runs_in
from isekai.boundary.provision import entry_for
from isekai.foundation.artifacts import write_json
from isekai.foundation.flow import FLOWS_DIR, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import OUTPUTS, Run
from isekai.interface.run_view import rendered
from isekai.shared.vocabulary import DEFAULT_MODELS_DIR

# A face's embedding, or None when no face is found; a file that does not decode
# as an image refuses.
Embed = Callable[[Path], Vector | None]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse the command line."""
    p = argparse.ArgumentParser(
        prog="python -m evaluation",
        description="Count, over a cohort, how often each render is nearest its own "
        "photograph and its own person.",
    )
    p.add_argument("runs", type=Path, help="a batch's runs directory")
    p.add_argument(
        "--cohort",
        type=Path,
        required=True,
        help="the directory holding one sub-directory per person",
    )
    p.add_argument(
        "--models",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help="where the pinned detector and encoder live",
    )
    p.add_argument(
        "--flows", type=Path, default=FLOWS_DIR, help="where the flows are declared"
    )
    return p.parse_args(argv)


def _gallery(cohort: Cohort, embed: Embed) -> dict[Photograph, Vector]:
    """Return each cohort photograph's embedding, refusing one with no image or face."""
    gallery: dict[Photograph, Vector] = {}
    for photograph in cohort.photographs:
        try:
            vector = embed(photograph.path)
        except Refusal as undecodable:
            raise Refusal(f"{undecodable}; remove it from the cohort") from undecodable
        if vector is None:
            raise Refusal(
                f"no face is found in {photograph.path}, so no render can be ranked "
                "against it; replace or remove it from the cohort"
            )
        gallery[photograph] = vector
    return gallery


def _rows(
    run: Run,
    source: Photograph,
    gallery: dict[Photograph, Vector],
    embed: Embed,
    flows_dir: Path,
    notes: list[str],
) -> tuple[dict[str, Row], bool]:
    """Return each rendered flow's row, and whether every flow in `run` was read.

    A row ranks the first seed of the flow's latest render group. A flow that does
    not load costs only its own renders, and a render that does not decode is its
    own row; why each was is added to `notes`.
    """
    rows: dict[str, Row] = {}
    whole = True
    for flow in run.flows:
        try:
            suffix = load_flow(flow, flows_dir).output_suffix
        except Refusal as unloadable:
            notes.append(
                f"unreadable: {run.id}: {unloadable}; move {run.directory(flow)} out "
                "of the run, then this command again"
            )
            whole = False
            continue
        renders = [
            (group, seed)
            for _, group, found in rendered(run, flows_dir, flows=(flow,))
            for seed in found
        ]
        if not renders:
            continue
        group = renders[-1][0]
        seed = next(s for g, s in renders if g == group)
        rest = [s for g, s in renders if (g, s) != (group, seed)]
        try:
            vector = embed(
                run.directory(flow, OUTPUTS, f"{group:03d}", f"{seed}{suffix}")
            )
        except Refusal as undecodable:
            notes.append(
                f"unreadable: {undecodable}; render it again or delete it, then this "
                "command again"
            )
            rows[flow] = unscored(source, run.id, seed, "unreadable")
        else:
            rows[flow] = (
                unscored(source, run.id, seed, "no face found")
                if vector is None
                else scored(source, run.id, seed, rank(vector, gallery))
            )
        rows[flow]["also_rendered"] = rest
    return rows, whole


def _models() -> dict[str, dict[str, str]]:
    """Return the detector and the encoder, each by destination and pinned digest."""
    manifest = load_eval_manifest()
    return {
        role: {"dest": dest, "sha256": entry_for(manifest, dest)["sha256"]}
        for role, dest in (("detector", DETECTOR), ("encoder", ENCODER))
    }


def score(
    runs: Path, cohort_dir: Path, embed: Embed, flows_dir: Path
) -> tuple[Record, list[str]]:
    """Return the batch's record, and a line naming each run or render it did not score.

    Every cohort photograph is embedded before any render is opened, so a cohort
    with a faceless photograph refuses while nothing has been scored. A run whose
    frame or a flow refuses is counted as unreadable, and the rest are scored.
    """
    cohort = load_cohort(cohort_dir)
    matched: list[tuple[Run, Photograph]] = []
    outside = unreadable = 0
    notes: list[str] = []
    for run in runs_in(runs):
        try:
            source = cohort.by_digest(run.photo_record["sha256"])
        except Refusal as damaged:
            unreadable += 1
            notes.append(f"unreadable: {run.id}: {damaged}")
            continue
        if source is None:
            outside += 1
            notes.append(f"outside the cohort: {run.id}")
        else:
            matched.append((run, source))
    gallery = _gallery(cohort, embed)
    flows: dict[str, list[Row]] = {}
    for run, source in matched:
        rows, whole = _rows(run, source, gallery, embed, flows_dir, notes)
        unreadable += not whole
        for flow, row in rows.items():
            flows.setdefault(flow, []).append(row)
    rec = record(cohort, flows, outside, _models(), unreadable=unreadable)
    return rec, notes


def _embedder(models: Path) -> Embed:
    """Return the real embedder: the pinned detector and encoder, verified."""
    from evaluation.eval_models import load_eval_manifest, shared_with_the_graph
    from evaluation.face import Detector, Encoder, embed
    from isekai.boundary.provision import DigestMismatch, load_manifest, resolve

    manifest = load_eval_manifest()
    shared = shared_with_the_graph(manifest, load_manifest())
    if shared:
        raise Refusal(
            f"the evaluator's manifest carries {', '.join(shared)}, whose destination "
            "or bytes the generator's manifest carries too, so the count would be the "
            "generator grading itself; pin another model in "
            "`evaluation/eval_models.json`"
        )
    fetch = (
        f"MODELS_DIR={shlex.quote(str(models.resolve()))} bash "
        "tools/download_models.sh evaluation/eval_models.json"
    )
    try:
        detector = Detector(resolve(DETECTOR, models, manifest))
        encoder = Encoder(resolve(ENCODER, models, manifest))
    except FileNotFoundError as absent:
        raise Refusal(
            f"{absent.filename} is not provisioned; run `{fetch}`, then this command "
            "again"
        ) from absent
    except DigestMismatch as swapped:
        raise Refusal(
            f"{swapped}; delete that file, run `{fetch}`, then this command again"
        ) from swapped
    return lambda path: embed(path, detector, encoder)


def main(argv: Sequence[str]) -> int:
    """Score the batch, write its record beside the runs, and print the table."""
    args = parse_args(argv)
    try:
        destination = record_destination(args.runs, "evaluation.json")
        embed = _embedder(args.models)
        rec, notes = score(args.runs, args.cohort, embed, args.flows)
    except Refusal as refused:
        print(f"refused: {refused}", file=sys.stderr)
        return 1
    write_json(destination, rec)
    print(table(rec), end="")
    for note in notes:
        print(note, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
