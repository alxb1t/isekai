import copy
import json
import random
from pathlib import Path

import pytest

from isekai.comfy_types import Workflow
from isekai.pipeline import run
from tests.fakes import FakeComfyClient


@pytest.mark.spec("workflow-mutation:variations:mutator-varies-submission")
def test_run_mutates_the_submitted_workflow(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    baked = workflow["10"]["inputs"]["seed"]
    client = FakeComfyClient()
    run(client, workflow, photo, tmp_path / "run", variations=1, seed=7)
    assert client.submitted_workflow is not None
    assert client.submitted_workflow["10"]["inputs"]["seed"] != baked


@pytest.mark.spec("workflow-mutation:reproducibility:every-variation-seed-is-derived")
def test_run_derives_every_seed_including_the_first(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    # v0.7 used --seed verbatim for variation 0, so the flag had two meanings:
    # a stream seed for 1..N and a literal sampler seed for 0. One meaning now.
    client = FakeComfyClient()
    run(
        client,
        workflow,
        photo,
        tmp_path / "run",
        seed=7,
        variations=3,
    )
    stream = random.Random(7)
    expected = [random.Random(stream.getrandbits(64)).getrandbits(64) for _ in range(3)]
    submitted = [wf["10"]["inputs"]["seed"] for wf in client.submissions]

    assert 7 not in submitted
    assert submitted == expected


@pytest.mark.spec("workflow-mutation:reproducibility:seed-is-printed")
def test_run_prints_the_seed_of_every_variation(
    workflow: Workflow, tmp_path: Path, capsys: pytest.CaptureFixture, photo: str
) -> None:
    client = FakeComfyClient()
    run(
        client,
        workflow,
        photo,
        tmp_path / "run",
        seed=7,
        variations=2,
    )
    # Assert the seeds that were actually used, not just that a number appeared:
    # a run printing a different random number would satisfy a substring check
    # most of the time while breaking reproducibility.
    expected = random.Random(7)
    out = capsys.readouterr().out
    for i in range(2):
        assert f"variation {i}: seed {expected.getrandbits(64)}\n" in out


@pytest.mark.spec("workflow-mutation:output-layout:images-numbered-by-variation")
@pytest.mark.spec("workflow-mutation:variations:one-output-per-variation")
def test_run_writes_one_numbered_image_per_variation(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    run_dir = tmp_path / "20260904T141530Z"
    client = FakeComfyClient()
    run(client, workflow, photo, run_dir, variations=3)
    assert {p.name for p in run_dir.iterdir()} == {
        "0.png",
        "1.png",
        "2.png",
        "run.json",
    }


@pytest.mark.spec("workflow-mutation:output-layout:run-gets-its-own-directory")
def test_a_second_run_leaves_the_first_run_s_directory_untouched(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    first = tmp_path / "20260904T141530Z"
    second = tmp_path / "20260904T141600Z"
    run(FakeComfyClient(), workflow, photo, first, variations=2)
    before = {p.name: p.read_bytes() for p in sorted(first.iterdir())}

    run(FakeComfyClient(), workflow, photo, second, variations=2)

    # Asserting the first directory byte for byte, not merely that both exist:
    # a run writing into a shared directory would still leave both paths
    # present while silently overwriting the earlier renders.
    assert {p.name: p.read_bytes() for p in sorted(first.iterdir())} == before
    assert {p.name for p in second.iterdir()} == {"0.png", "1.png", "run.json"}


@pytest.mark.spec("workflow-mutation:output-layout:manifest-records-the-run")
def test_run_writes_a_manifest_recording_the_seeds_and_the_dials(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    run_dir = tmp_path / "20260904T141530Z"
    client = FakeComfyClient()
    run(
        client,
        workflow,
        photo,
        run_dir,
        seed=99,
        variations=5,
        overrides={"denoise": 0.72},
    )
    manifest = json.loads((run_dir / "run.json").read_text())

    assert manifest["seed"] == 99
    assert manifest["variations"] == 5
    assert manifest["overrides"] == {"denoise": 0.72}
    # The recorded seeds must reproduce the renders beside them, not merely be
    # five numbers: a manifest that does not match its own directory is worse
    # than no manifest. Each entry is the per-variation seed the run drew, and
    # the sampler seed on the submitted graph derives from it.
    assert len(manifest["seeds"]) == 5
    assert [random.Random(s).getrandbits(64) for s in manifest["seeds"]] == [
        wf["10"]["inputs"]["seed"] for wf in client.submissions
    ]


# --- Overrides applied before jitter ----------------------------------------


@pytest.mark.spec("workflow-mutation:base-relative:override-applied-before-jitter")
def test_run_applies_override_before_mutate_so_jitter_is_around_the_new_base(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    client = FakeComfyClient()
    run(
        client,
        workflow,
        photo,
        tmp_path / "run",
        seed=42,
        variations=1,
        overrides={"denoise": 0.80},
    )
    assert client.submitted_workflow is not None
    denoise = client.submitted_workflow["10"]["inputs"]["denoise"]
    # Pin the exact value, not just the band: 0.80 is itself inside [0.75, 0.85],
    # so a band assertion also passes when mutate runs BEFORE apply_overrides and
    # the jitter is overwritten by the override.
    seed_0 = random.Random(42).getrandbits(64)
    rng = random.Random(seed_0)
    rng.getrandbits(64)  # the sampler seed mutate draws first
    assert denoise == pytest.approx(min(1.0, max(0.0, rng.uniform(0.75, 0.85))))
    assert denoise != 0.80


@pytest.mark.spec("workflow-mutation:reproducibility:override-plus-seed-reproduces")
def test_run_with_override_and_seed_is_reproducible(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    def once(tag: str) -> Workflow | None:
        client = FakeComfyClient()
        run(
            client,
            copy.deepcopy(workflow),
            photo,
            tmp_path / tag,
            seed=77,
            variations=1,
            overrides={"denoise": 0.72, "cfg": 6.5},
        )
        return client.submitted_workflow

    assert once("a") == once("b")


@pytest.mark.spec("workflow-mutation:reproducibility:seed-covers-every-variation")
@pytest.mark.spec(
    "workflow-mutation:reproducibility:seeded-run-is-reproducible-and-distinct"
)
@pytest.mark.spec("workflow-mutation:variations:variations-differ-from-each-other")
def test_run_with_a_seed_reproduces_every_variation_not_just_the_first(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    # The seed is a reproducibility contract for the whole run. Variations after
    # the first must derive from it too, or `--seed X --variations 3` reproduces
    # only one of the three renders.
    def once(tag: str) -> list[Workflow]:
        client = FakeComfyClient()
        run(
            client,
            copy.deepcopy(workflow),
            photo,
            tmp_path / tag,
            seed=77,
            variations=3,
        )
        return client.submissions

    a, b = once("a"), once("b")

    assert len(a) == len(b) == 3
    for i, (wf_a, wf_b) in enumerate(zip(a, b)):
        assert wf_a == wf_b, f"variation {i} is not reproducible from the seed"

    # Reproducibility alone is satisfied by a run that emits the SAME workflow
    # three times -- which would bill three renders for one image. The variations
    # must also differ from each other.
    assert len({wf["10"]["inputs"]["seed"] for wf in a}) == 3


# --- v0.12: the fixed-dial render, which is what a baseline means --------------


@pytest.mark.spec("workflow-mutation:variations:fixed-dials-are-the-graphs-own")
def test_a_fixed_dial_run_submits_the_graphs_own_dials(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    # Every dial `mutate` moves, read off the graph before the run and compared
    # against what was submitted. Named by node and key rather than by a copy of
    # the values, so a re-tune of the graph cannot make this test vacuous.
    dials = [("10", "denoise"), ("10", "cfg"), ("8", "ip_weight")]
    dials += [(nid, "strength") for nid in ("14", "18", "21")]
    committed = {(nid, key): workflow[nid]["inputs"][key] for nid, key in dials}

    client = FakeComfyClient()
    run(
        client,
        workflow,
        photo,
        tmp_path / "run",
        variations=3,
        seed=7,
        fixed_dials=True,
    )

    for submitted in client.submissions:
        for (nid, key), value in committed.items():
            assert submitted[nid]["inputs"][key] == value


@pytest.mark.spec("workflow-mutation:variations:fixed-dials-are-the-graphs-own")
def test_a_fixed_dial_run_still_applies_the_users_overrides(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    # An override sets the base; holding the dials means not jittering *around*
    # that base, never ignoring it. Otherwise `--fixed-dials --denoise 0.4` would
    # silently render at the graph's 0.65.
    client = FakeComfyClient()
    run(
        client,
        workflow,
        photo,
        tmp_path / "run",
        variations=2,
        seed=7,
        overrides={"denoise": 0.4, "cn_strength": 0.25},
        fixed_dials=True,
    )

    for submitted in client.submissions:
        assert submitted["10"]["inputs"]["denoise"] == 0.4
        assert submitted["8"]["inputs"]["cn_strength"] == 0.25


@pytest.mark.spec("workflow-mutation:variations:fixed-dials-still-vary-the-seed")
def test_a_fixed_dial_run_still_draws_a_seed_per_variation(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    client = FakeComfyClient()
    run(
        client,
        workflow,
        photo,
        tmp_path / "run",
        variations=4,
        seed=7,
        fixed_dials=True,
    )
    seeds = [wf["10"]["inputs"]["seed"] for wf in client.submissions]

    assert len(set(seeds)) == 4
    assert workflow["10"]["inputs"]["seed"] not in seeds


@pytest.mark.spec("workflow-mutation:variations:fixed-dials-still-vary-the-seed")
def test_a_fixed_dial_run_draws_the_same_seeds_as_a_jittered_one(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    # The sampler seed is drawn identically in both modes, so a held run and a
    # jittered run from one run seed differ in the jitter alone. That is what
    # makes the two directly comparable rather than merely both reproducible.
    held, jittered = FakeComfyClient(), FakeComfyClient()
    for client, fixed in ((held, True), (jittered, False)):
        run(
            client,
            copy.deepcopy(workflow),
            photo,
            tmp_path / f"run-{fixed}",
            variations=3,
            seed=7,
            fixed_dials=fixed,
        )

    assert [wf["10"]["inputs"]["seed"] for wf in held.submissions] == [
        wf["10"]["inputs"]["seed"] for wf in jittered.submissions
    ]


@pytest.mark.spec("workflow-mutation:variations:fixed-dials-reproduce-from-the-seed")
def test_two_fixed_dial_runs_from_one_seed_submit_identical_workflows(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    clients = [FakeComfyClient(), FakeComfyClient()]
    for i, client in enumerate(clients):
        run(
            client,
            copy.deepcopy(workflow),
            photo,
            tmp_path / f"run-{i}",
            variations=3,
            seed=7,
            fixed_dials=True,
        )

    assert clients[0].submissions == clients[1].submissions


@pytest.mark.spec("workflow-mutation:variations:mutator-varies-submission")
def test_jitter_is_still_what_a_run_does_when_it_is_not_asked_otherwise(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    # The default is unchanged, and this asserts it against the graph's own dials
    # rather than against the absence of a flag.
    client = FakeComfyClient()
    run(client, workflow, photo, tmp_path / "run", variations=1, seed=7)

    submitted = client.submissions[0]
    assert submitted["10"]["inputs"]["denoise"] != workflow["10"]["inputs"]["denoise"]
    assert submitted["8"]["inputs"]["ip_weight"] != workflow["8"]["inputs"]["ip_weight"]
