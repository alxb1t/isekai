"""Stage (4): assemble every prompt locally, then render what was approved.

**Assembly happens before any endpoint is acquired, for the whole batch.**
Assembly is free and rendering is not, so a malformed sheet should cost nothing
rather than a boot and several minutes of waiting. Doing the whole batch first is
what turns that from a per-item saving into a guarantee -- and it makes the
entirety of prompt construction testable offline.

**Only an approved artifact is rendered.** The correction is the single largest
measured gain in this pipeline; rendering an unapproved draft would silently
spend money producing the result the correction exists to improve on, and would
make the two indistinguishable afterwards.

**Seeds are drawn or named, never both.** One verb explores and the other
reproduces, and combining them has no meaning. The output is named by its seed,
which is the reproducibility contract at the finest grain the system has: one
image, one integer -- a stronger guarantee than "one integer reproduces a run's
whole sequence", because it reproduces an image rather than an ordering.

**No session lifecycle.** This stage talks to an endpoint somebody else brought
up, exactly as the prototype did by hand. Acquiring, tunnelling, releasing and
reconciling orphaned machines land with the version that adds a second flow,
rather than being dragged into the one whose only risk is the architecture. The
cost is that an orphaned machine is exactly as possible as it is today, and no
less.

Stdlib only; the endpoint is behind the repository's existing `ComfyTransport`.
"""

import hashlib
import json
import random
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.comfy_types import ComfyTransport, Workflow
from isekai.flow import Flow, assemble
from isekai.refusal import Refusal
from isekai.review import APPROVED
from isekai.review import DIRECTORY as REVIEW
from isekai.run import (
    Run,
    approved_versions,
    artifact_name,
    check_budget,
    envelope,
    read_artifact,
    record_failure,
    write_atomically,
    write_json,
)
from isekai.sheet import Schema
from isekai.workflow import image_dimensions, working_resolution

STAGE_ASSEMBLE = "assemble"
STAGE_RENDER = "render"
PROMPTS = "prompts"
OUTPUTS = "outputs"

# A seed is what the sampler takes: an unsigned 64-bit integer.
SEED_BITS = 64


@dataclass(frozen=True)
class Render:
    """One rendered image and the provenance that says what produced it."""

    seed: int
    image: Path
    provenance: Path


def draw_seeds(
    count: int, rng: random.Random, already: Sequence[int] = ()
) -> list[int]:
    """Draw `count` seeds that are distinct from each other and from `already`.

    The source is injected, which is what keeps the suite deterministic without
    making production output predictable.
    """
    drawn: list[int] = []
    seen = set(already)
    while len(drawn) < count:
        seed = rng.getrandbits(SEED_BITS)
        if seed in seen:
            continue
        seen.add(seed)
        drawn.append(seed)
    return drawn


def seeds_for(
    count: int | None,
    explicit: Sequence[int] | None,
    rng: random.Random,
    already: Sequence[int] = (),
) -> list[int]:
    """Return the seeds to render, refusing a count and explicit seeds together."""
    if count is not None and explicit:
        raise Refusal(
            "--count and --seed are alternatives: one explores and the other "
            "reproduces, and asking for both has no meaning; drop whichever you "
            "did not mean"
        )
    if explicit:
        return [seed for seed in explicit if seed not in set(already)]
    wanted = 1 if count is None else count
    shortfall = max(wanted - len(already), 0)
    return draw_seeds(shortfall, rng, already)


def approved_artifact(run: Run, flow: str) -> tuple[int, Path]:
    """Return the highest approved artifact for `flow`, or refuse naming the way out."""
    directory = run.directory(REVIEW, flow)
    approved = approved_versions(directory)
    if not approved:
        raise Refusal(
            f"{run.id}: flow {flow} has no approved sheet, and only an approved "
            "sheet is rendered; run `python -m isekai review --flow "
            f"{flow}`, edit the draft, then `python -m isekai approve --flow "
            f"{flow}`"
        )
    return approved[-1], directory / artifact_name(approved[-1], APPROVED)


def approved_flows(run: Run) -> list[str]:
    """Return every flow this run has an approved artifact for, by identifier.

    A listing, so selecting among them needs no flag: a run renders everything it
    has been approved for.
    """
    review = run.directory(REVIEW)
    if not review.is_dir():
        return []
    return sorted(
        directory.name
        for directory in review.iterdir()
        if directory.is_dir() and approved_versions(directory)
    )


def prompt_artifact(
    run: Run,
    flow: Flow,
    schema: Schema,
    *,
    new_version: bool = False,
) -> Path:
    """Assemble `flow`'s prompt for this run and write it, without touching a network.

    The artifact takes the approved sheet's number rather than counting its own,
    because only an approved artifact is ever rendered and the chain back to the
    photograph is the producer record.
    """
    version, source = approved_artifact(run, flow.id)
    directory = run.directory(PROMPTS, flow.id)
    path = directory / artifact_name(version)
    if path.exists() and not new_version:
        return path

    check_budget(STAGE_ASSEMBLE, directory, version, run.id)
    try:
        body = read_artifact(source)
        positive, negative = assemble(body["fields"], schema.names, flow)
        # Read here and thrown away, for the reason the whole stage is here: the
        # render target comes from the photograph's own header, and a header
        # nothing can read must cost an assembly rather than a boot.
        photo_resolution(run.photo)
    except (Refusal, KeyError, TypeError) as broken:
        record = record_failure(
            directory,
            version,
            "permanent",
            {"stage": STAGE_ASSEMBLE, "detail": str(broken)},
        )
        raise Refusal(
            f"{run.id}: flow {flow.id}'s approved sheet cannot be assembled -- "
            f"{broken}; see {record.name} in {PROMPTS}/{flow.id}/"
        ) from broken

    write_json(
        path,
        envelope(
            "prompt",
            {"implementation": STAGE_ASSEMBLE, "from": version, "source": REVIEW},
            {
                "flow": flow.id,
                "positive": positive,
                "negative": negative,
                "edited": bool(body["producer"].get("edited")),
            },
        ),
    )
    return path


def prepare(
    run: Run,
    flows: Mapping[str, Flow],
    schema: Schema,
) -> dict[str, Path]:
    """Assemble every approved flow's prompt for one run, before anything is rented.

    A run that has been approved for *nothing* asked for is refused rather than
    returning empty. Selecting among several approved flows still needs no flag --
    the refusal fires only when none of the flows asked for has an approved sheet,
    so "a run renders everything it has been approved for" is unchanged and
    "rendering did nothing and said nothing" is no longer reachable.
    """
    ready = [flow for flow in approved_flows(run) if flow in flows]
    if flows and not ready:
        asked = ", ".join(sorted(flows))
        raise Refusal(
            f"{run.id}: no approved sheet for {asked}, and only an approved sheet "
            "is rendered; run `python -m isekai review`, edit the draft, then "
            "`python -m isekai approve`"
        )
    return {flow: prompt_artifact(run, flows[flow], schema) for flow in ready}


def rendered_seeds(directory: Path) -> list[int]:
    """Return the seeds already rendered into `directory`, from filenames alone."""
    if not directory.is_dir():
        return []
    return sorted(
        int(path.stem)
        for path in directory.iterdir()
        if path.suffix == ".png" and path.stem.isdigit()
    )


def photo_resolution(photo: Path) -> tuple[int, int]:
    """Return the working resolution for `photo`, as a refusal rather than an exit.

    `image_dimensions` belongs to the render path this version does not touch, and
    it stops the process with `sys.exit` -- correct for a single-photograph
    command, wrong here. A batch must survive one unreadable header: `across`
    collects refusals and a `SystemExit` walks straight past it, taking the
    remaining photographs with it after the endpoint is already rented.
    """
    try:
        return working_resolution(*image_dimensions(str(photo)))
    except SystemExit as unreadable:
        raise Refusal(
            f"{unreadable}; the render target is derived from the photograph's "
            "own header and there is nothing to fall back to -- re-export the "
            "photograph as a JPEG or PNG and open the run again"
        ) from unreadable


def build_graph(
    flow: Flow, photo: Path, image_name: str, prompt: Mapping[str, Any], seed: int
) -> Workflow:
    """Return the graph to submit: the flow's own, with its dials and this seed.

    The dials come from the manifest and not from the graph file. `summon-v1`'s
    graph carries cfg 7 and identity strength 0.5; the measured configuration is
    5 and 0.8, and a render that used the file's values would be a configuration
    nothing measured (design.md D12).
    """
    graph = flow.graph()
    dials = flow.dials
    width, height = photo_resolution(photo)

    graph[flow.node("photo")]["inputs"]["image"] = image_name
    graph[flow.node("positive")]["inputs"]["text"] = prompt["positive"]
    graph[flow.node("negative")]["inputs"]["text"] = prompt["negative"]

    for role in ("scale", "latent"):
        graph[flow.node(role)]["inputs"].update(width=width, height=height)

    identity = graph[flow.node("identity")]["inputs"]
    identity["ip_weight"] = dials["ip_weight"]
    identity["cn_strength"] = dials["identity_cn_strength"]
    graph[flow.node("openpose")]["inputs"]["strength"] = dials["openpose_strength"]
    graph[flow.node("clip_skip")]["inputs"]["stop_at_clip_layer"] = dials["clip_skip"]

    sampler = graph[flow.node("sampler")]["inputs"]
    sampler["seed"] = seed
    for dial in ("steps", "cfg", "sampler_name", "scheduler", "denoise"):
        sampler[dial] = dials[dial]

    hires = graph[flow.node("hires_resize")]["inputs"]
    scaled = (round(width * dials["hires_scale"]), round(height * dials["hires_scale"]))
    # SDXL's VAE needs a multiple of 8. 1.5x of a /64 canvas always is, and this
    # asserts it rather than trusting it.
    if any(side % 8 for side in scaled):
        raise Refusal(
            f"flow {flow.id}: a hires target of {scaled} is not a multiple of 8, "
            "which the VAE requires; change `hires_scale` under a new flow "
            "identifier"
        )
    hires["width"], hires["height"] = scaled

    second = graph[flow.node("hires_sampler")]["inputs"]
    second["seed"] = seed
    second["steps"] = dials["hires_steps"]
    second["denoise"] = dials["hires_denoise"]
    for dial in ("cfg", "sampler_name", "scheduler"):
        second[dial] = dials[dial]
    return graph


def graph_digest(graph: Workflow) -> str:
    """Return the digest of the graph as submitted, keys sorted so it is stable."""
    return hashlib.sha256(
        json.dumps(graph, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def render(
    run: Run,
    flow: Flow,
    client: ComfyTransport,
    *,
    count: int | None = None,
    seeds: Sequence[int] | None = None,
    rng: random.Random | None = None,
    poll: float = 1.0,
) -> list[Render]:
    """Render `flow`'s approved sheet for this run, one image per seed.

    Idempotent per image: a seed whose output already exists is not rendered
    again, and raising the count renders only the shortfall. Rendering is the one
    step that costs money on every pass, so it is where idempotence is worth the
    most -- and the decision is a directory listing, the same rule every other
    stage is held to.
    """
    version, _ = approved_artifact(run, flow.id)
    prompt = read_artifact(run.directory(PROMPTS, flow.id) / artifact_name(version))
    directory = run.directory(OUTPUTS, flow.id, f"{version:03d}")
    already = rendered_seeds(directory)
    wanted = seeds_for(count, seeds, rng or random.Random(), already)
    if not wanted:
        return []

    check_budget(STAGE_RENDER, directory, version, run.id)

    image_name = client.upload_image(str(run.photo))
    # Constant across seeds: the flow's graph on disk does not change mid-render.
    flow_graph = flow.graph_digest()
    produced: list[Render] = []
    for seed in wanted:
        image = directory / f"{seed}.png"
        # `build_graph` is inside the guard and not before it: it refuses on an
        # unreadable photograph header, and a refusal this stage does not record
        # leaves resume nothing on disk to reason about.
        try:
            graph = build_graph(flow, run.photo, image_name, prompt, seed)
            body = _submit(client, graph, poll)
        except Refusal as failed:
            record_failure(
                directory,
                version,
                "permanent",
                {"stage": STAGE_RENDER, "seed": seed, "detail": str(failed)},
            )
            raise
        # Atomically, like every other artifact in a run, and for a sharper
        # reason: `rendered_seeds` treats the presence of `<seed>.png` as proof
        # the seed is done, so a truncated file is a seed resume skips forever --
        # on the one stage that costs money on every pass.
        write_atomically(image, body)
        provenance = directory / f"{seed}.json"
        write_json(
            provenance,
            envelope(
                STAGE_RENDER,
                {"implementation": STAGE_RENDER, "from": version, "source": PROMPTS},
                {
                    "flow": flow.id,
                    "seed": seed,
                    "sheet_version": version,
                    "graph_sha256": graph_digest(graph),
                    "flow_graph_sha256": flow_graph,
                    "edited": prompt["edited"],
                },
            ),
        )
        produced.append(Render(seed, image, provenance))
    return produced


def _submit(client: ComfyTransport, graph: Workflow, poll: float) -> bytes:
    """Queue one graph, wait for it, and return the image's bytes."""
    prompt_id = client.submit(graph)
    while prompt_id not in (history := client.history(prompt_id)):
        time.sleep(poll)
    for output in history[prompt_id]["outputs"].values():
        if "images" in output:
            return client.view(output["images"][0])
    raise Refusal(
        "the endpoint returned no image for a graph it accepted; check the pod's "
        "ComfyUI log, then render again"
    )
