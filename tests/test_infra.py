"""Checks over the tracked pod configuration: the image and the pod lifecycle.

These read the shipped files themselves rather than a fixture copy, for the same
reason the suite reads the shipped graph: a byte-identical copy with no drift
check is a second thing to rename and a silent divergence waiting to happen.
"""

import re
from pathlib import Path

import pytest

from isekai.boundary.provision import (
    MANIFEST_PATH,
    MODELS_NAMESPACE,
    MODELS_ROOT,
    VOLUME_MOUNT,
    Manifest,
    annotator_files,
    manifest_dest,
)
from isekai.foundation.flow import Workflow

REPO = Path(__file__).resolve().parent.parent
DOCKERFILE = REPO / "Dockerfile"


def aux_annotator_ckpts_path(dockerfile: str) -> str | None:
    """Return the `AUX_ANNOTATOR_CKPTS_PATH` the image sets, or None if it sets none.

    None is the failure the scenario names: with the variable unset the pack falls
    back to `<node dir>/ckpts`, which is container disk.
    """
    found = re.search(r"^ENV\s+AUX_ANNOTATOR_CKPTS_PATH=(\S+)", dockerfile, re.M)
    return found.group(1) if found else None


@pytest.fixture(scope="session")
def dockerfile() -> str:
    """Read the shipped `Dockerfile` once for the whole session."""
    return DOCKERFILE.read_text()


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_the_image_sets_the_annotator_ckpts_path_inside_the_models_tree(
    dockerfile: str,
) -> None:
    path = aux_annotator_ckpts_path(dockerfile)
    assert path is not None
    assert path.startswith(f"{MODELS_ROOT}/")


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_a_configuration_leaving_the_pack_at_its_own_default_fails_the_check() -> None:
    assert aux_annotator_ckpts_path("FROM scratch\nENV PYTHONUNBUFFERED=1\n") is None


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_every_annotator_checkpoint_the_graph_needs_lands_under_that_path(
    dockerfile: str, workflow: Workflow, manifest: Manifest
) -> None:
    path = aux_annotator_ckpts_path(dockerfile)
    assert path is not None
    needed = annotator_files(workflow)
    assert len(needed) == 2
    for filename in needed:
        dest = manifest_dest(filename, manifest)
        assert dest is not None
        assert f"{MODELS_ROOT}/{dest}".startswith(f"{path}/")


@pytest.mark.spec_exempt(
    "structural: names the 352 MB the redirect exists to move onto the volume"
)
def test_the_annotator_checkpoints_are_the_two_the_preprocessors_fetch(
    workflow: Workflow,
) -> None:
    assert set(annotator_files(workflow)) == {
        "yolox_l.onnx",
        "dw-ll_ucoco_384_bs5.torchscript.pt",
    }


@pytest.fixture(scope="session")
def up_sh() -> str:
    """Read the shipped `infra/up.sh` once for the whole session."""
    return (REPO / "infra" / "up.sh").read_text()


@pytest.fixture(scope="session")
def start_sh() -> str:
    """Read the shipped `start.sh` once for the whole session."""
    return (REPO / "start.sh").read_text()


@pytest.mark.spec_exempt(
    "structural: the mount is a precondition of the namespace, not a scenario"
)
def test_the_pod_mounts_the_volume_at_its_own_root(up_sh: str) -> None:
    assert f'volumeMountPath: "{VOLUME_MOUNT}"' in up_sh


@pytest.mark.spec_exempt(
    "structural: the mount is a precondition of the namespace, not a scenario"
)
def test_the_pod_no_longer_mounts_the_volume_over_the_models_directory(
    up_sh: str,
) -> None:
    assert f'volumeMountPath: "{MODELS_ROOT}"' not in up_sh


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_the_pod_symlinks_the_models_directory_onto_this_project_namespace(
    start_sh: str,
) -> None:
    assert MODELS_NAMESPACE.startswith(f"{VOLUME_MOUNT}/")
    assert MODELS_NAMESPACE != VOLUME_MOUNT
    assert 'ln -s "$MODELS_NAMESPACE" "$MODELS_ROOT"' in start_sh
    assert f"MODELS_NAMESPACE={MODELS_NAMESPACE}" in start_sh
    assert f"MODELS_ROOT={MODELS_ROOT}" in start_sh


@pytest.mark.spec_exempt(
    "structural: nothing in this project reaches outside its own namespace"
)
def test_the_pod_startup_touches_nothing_outside_the_project_namespace(
    start_sh: str,
) -> None:
    reaches_out = [
        line
        for line in start_sh.splitlines()
        if not line.lstrip().startswith("#")
        and VOLUME_MOUNT in line
        and MODELS_NAMESPACE not in line
    ]
    assert reaches_out == []


@pytest.fixture(scope="session")
def download_models_sh() -> str:
    """Read the shipped `scripts/download_models.sh` once for the whole session."""
    return (REPO / "scripts" / "download_models.sh").read_text()


@pytest.mark.spec(
    "model-provisioning:source-fallback:a-failed-transfer-advances-to-the-next-source"
)
def test_the_driver_walks_every_source_the_plan_carries(
    download_models_sh: str,
) -> None:
    assert "read -r -a fields" in download_models_sh
    assert 'urls=("${fields[@]:2}")' in download_models_sh
    assert 'for url in "${urls[@]}"' in download_models_sh
    # the word split is gone, and so is the suppression that made it legal
    assert "SC2086" not in download_models_sh
    assert "for url in $urls" not in download_models_sh


@pytest.mark.spec(
    "model-provisioning:source-fallback:a-failed-transfer-advances-to-the-next-source"
)
def test_the_driver_aborts_only_once_every_source_is_exhausted(
    download_models_sh: str,
) -> None:
    lines = [line.strip() for line in download_models_sh.splitlines()]
    # a transfer failure and a verification failure each continue the walk ...
    assert lines.count("continue") == 2
    # ... and the only abort on the fetch path is the one after the loop.
    assert "ERROR: every source for $target failed" in download_models_sh
    assert "landed=0" in download_models_sh


@pytest.mark.spec(
    "model-provisioning:reachability:a-provisioning-abort-holds-the-pod-open"
)
def test_a_provisioning_failure_does_not_take_the_container_down(
    start_sh: str,
) -> None:
    provisioning = [
        line for line in start_sh.splitlines() if "download_models.sh" in line
    ]
    assert len(provisioning) == 1
    # It returns rather than exits, and the step it belongs to is itself guarded,
    # so `set -e` cannot terminate the shell that owns sshd.
    assert provisioning[0].rstrip().endswith("|| return 1")
    assert "if ! provision; then" in start_sh
    assert 'exec sleep "$HOLD_SECONDS"' in start_sh


@pytest.mark.spec(
    "model-provisioning:reachability:a-provisioning-abort-holds-the-pod-open"
)
def test_the_hold_replaces_the_inference_server_rather_than_preceding_it(
    start_sh: str,
) -> None:
    lines = start_sh.splitlines()
    hold = next(
        i for i, line in enumerate(lines) if 'exec sleep "$HOLD_SECONDS"' in line
    )
    serve = next(i for i, line in enumerate(lines) if "exec python main.py" in line)
    assert hold < serve
    # nothing on the volume is removed on the failure path
    assert "rm " not in "\n".join(lines[hold - 6 : serve])


# The pod entrypoint's provisioning step, and the two halves of the volume guard.
#
# These are text checks over the shipped shell, for the same reason the checks
# above are: the suite is offline and there is no pod to run the entrypoint on.
# What they hold is the *shape* the scenarios name -- one guarded provisioning
# step, a bounded hold, a marker off the volume, and a refusal on each side of
# the boundary.

# The repository's per-session spending ceiling, in seconds at the halt.
SESSION_CEILING_SECONDS = 45 * 60


def provision_body(start_sh: str) -> str:
    """Return the body of `start.sh`'s `provision` function.

    The scenario is about provisioning as a whole rather than about one of its
    steps, so what the test needs is which lines are *inside* the guarded unit.
    """
    lines = start_sh.splitlines()
    opens = next(i for i, line in enumerate(lines) if line.startswith("provision()"))
    closes = next(i for i, line in enumerate(lines[opens:], opens) if line == "}")
    return "\n".join(lines[opens : closes + 1])


@pytest.mark.spec("model-provisioning:reachability:namespace-setup-is-held-open-too")
def test_preparing_the_namespace_is_inside_the_guarded_provisioning_step(
    start_sh: str,
) -> None:
    body = provision_body(start_sh)
    # every step of preparing the namespace, and the fetch, in one unit ...
    assert 'mkdir -p "$MODELS_NAMESPACE"' in body
    assert 'ln -s "$MODELS_NAMESPACE" "$MODELS_ROOT"' in body
    assert "download_models.sh" in body
    # ... and no step of it can exit the shell that owns sshd.
    assert "exit " not in body


@pytest.mark.spec("model-provisioning:reachability:namespace-setup-is-held-open-too")
def test_the_whole_provisioning_step_is_guarded_exactly_once(start_sh: str) -> None:
    calls = [
        line.strip()
        for line in start_sh.splitlines()
        if line.strip().startswith(("provision", "if ! provision"))
        and not line.startswith("provision()")
    ]
    assert calls == ["if ! provision; then"]


@pytest.mark.spec("model-provisioning:reachability:namespace-setup-is-held-open-too")
def test_deleting_a_non_empty_mounted_models_tree_is_refused(start_sh: str) -> None:
    body = provision_body(start_sh)
    guard = next(line for line in body.splitlines() if "mountpoint -q" in line)
    # the premise of the delete: the image's own tree on container disk. A
    # non-empty mount here is somebody's real models tree.
    assert 'mountpoint -q "$MODELS_ROOT"' in guard
    assert 'ls -A "$MODELS_ROOT"' in guard
    delete = next(i for i, line in enumerate(body.splitlines()) if "rm -rf" in line)
    assert body.splitlines().index(guard) < delete


@pytest.mark.spec("model-provisioning:reachability:the-hold-is-bounded-and-marked")
def test_the_hold_ends_on_its_own_well_inside_the_session_ceiling(
    start_sh: str,
) -> None:
    bound = re.search(r"^HOLD_SECONDS=(\d+)$", start_sh, re.M)
    assert bound is not None
    assert 0 < int(bound.group(1)) < SESSION_CEILING_SECONDS
    assert 'exec sleep "$HOLD_SECONDS"' in start_sh
    # an indefinite hold bills until a human notices it
    assert "tail -f /dev/null" not in start_sh


@pytest.mark.spec("model-provisioning:reachability:the-hold-is-bounded-and-marked")
def test_the_failure_marker_is_written_off_the_volume(start_sh: str) -> None:
    marker = re.search(r"^FAILURE_MARKER=(\S+)$", start_sh, re.M)
    assert marker is not None
    # the volume is exactly the thing that may have failed
    assert not marker.group(1).startswith(f"{VOLUME_MOUNT}/")
    assert '> "$FAILURE_MARKER"' in start_sh


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_client_refuses_to_create_a_pod_without_a_named_volume(
    up_sh: str,
) -> None:
    lines = up_sh.splitlines()
    guard = next(i for i, line in enumerate(lines) if 'RUNPOD_VOLUME_ID:-}" ]' in line)
    creates = next(
        i for i, line in enumerate(lines) if "POST https://rest.runpod.io" in line
    )
    assert guard < creates
    assert "exit 1" in "\n".join(lines[guard : guard + 6])


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_pod_is_told_which_volume_to_expect(up_sh: str) -> None:
    assert "RUNPOD_VOLUME_ID: $vol" in up_sh


@pytest.mark.spec_exempt(
    "structural: where the teardown call resolves from, not a scenario about readiness"
)
def test_the_timeout_teardown_resolves_from_the_root_the_script_moved_to(
    up_sh: str,
) -> None:
    lines = up_sh.splitlines()
    moved = next(i for i, line in enumerate(lines) if line.startswith("cd "))
    teardown = next(
        i
        for i, line in enumerate(lines)
        if "down.sh" in line and not line.lstrip().startswith("#")
    )

    # The script has already moved to the repository root, so the teardown is
    # spelled from there. Re-deriving `dirname "$0"` after the move interprets a
    # path relative to the *old* working directory against the new one, which
    # resolves only when the invocation path's last component happens to repeat
    # -- and a teardown that fails to resolve leaves the pod billing.
    assert moved < teardown
    assert 'dirname "$0"' not in lines[teardown]
    assert "./infra/down.sh" in lines[teardown]


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_entrypoint_refuses_before_preparing_the_namespace(start_sh: str) -> None:
    body = provision_body(start_sh).splitlines()
    named = next(i for i, line in enumerate(body) if 'RUNPOD_VOLUME_ID:-}" ]' in line)
    floor = next(i for i, line in enumerate(body) if "VOLUME_SIZE_FLOOR_KIB" in line)
    prepares = next(
        i for i, line in enumerate(body) if 'mkdir -p "$MODELS_NAMESPACE"' in line
    )
    assert named < prepares
    assert floor < prepares
    # a capacity floor, not `mountpoint`: RunPod mounts the pod's own volume
    # disk at the same path when no network volume is attached, so the path is a
    # mountpoint either way.
    assert "df -k --output=size" in "\n".join(body)


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_volume_guard_measures_capacity_rather_than_fill_level(
    start_sh: str,
) -> None:
    # What the guard proves is identity -- the 20 GB ephemeral container disk is
    # not the network volume -- and capacity discriminates those two whatever the
    # volume's fill level is. Free space does not: this project already put
    # 16.5 GiB on a volume it shares with a second project, so a floor on
    # availability degrades as the volume fills and would refuse a warm boot that
    # needed to download nothing.
    body = provision_body(start_sh)
    assert "--output=avail" not in body
    floor = re.search(r"^VOLUME_SIZE_FLOOR_KIB=", start_sh, re.M)
    assert floor is not None
    # and the message says what is measured
    assert "free" not in body.lower()


@pytest.mark.spec_exempt(
    "structural: a clone with no checkout is not a pin, and this holds all three"
)
def test_every_git_clone_in_the_image_is_pinned_to_a_commit(dockerfile: str) -> None:
    clones = re.findall(r"git clone \S+ \\?\s*(\S+)", dockerfile)
    checkouts = re.findall(r"git checkout ([0-9a-f]{40})\b", dockerfile)
    # ComfyUI's core and the two custom-node packs, each on a full commit sha
    assert len(clones) == 3
    assert len(checkouts) == 3


@pytest.mark.spec(
    "model-provisioning:immutable-pins:an-escaping-destination-is-refused"
)
def test_the_driver_joins_no_path_of_its_own(download_models_sh: str) -> None:
    assert 'target="${MODELS_DIR}/${dest}"' not in download_models_sh
    assert 'target="${fields[1]:-}"' in download_models_sh


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_capacity_floor_clears_the_container_disk_as_well(
    start_sh: str, up_sh: str
) -> None:
    # The one case this pod-side guard still exists for is the one `up.sh` cannot
    # see: the id is set and the mount silently failed, so `/runpod-volume`
    # resolves to the container overlay rather than to the volume (design.md D5).
    # That overlay's backing disk is `containerDiskInGb`, which is LARGER than the
    # pod's own volume disk, so a floor that only clears the volume disk lets the
    # overlay through and 16.5 GiB lands on storage that dies at teardown.
    floor = re.search(
        r"^VOLUME_SIZE_FLOOR_KIB=\$\(\((\d+) \* 1024 \* 1024\)\)", start_sh, re.M
    )
    assert floor is not None
    container_disk = re.search(r"containerDiskInGb:\s*(\d+)", up_sh)
    assert container_disk is not None
    # RunPod states those sizes in decimal GB, and decimal is the reading that
    # makes the disk look BIGGEST in KiB, so it is the one the floor must clear.
    largest_container_kib = int(container_disk.group(1)) * 1000**3 // 1024
    assert int(floor.group(1)) * 1024 * 1024 > largest_container_kib


# The image mirrors the repository's layout, and no boot proves a rebuilt image
# before a pod uses it, so these hold its paths statically: `0029` design D5.

IMAGE_ROOT = "/opt/isekai"


def image_copies(dockerfile: str) -> dict[str, str]:
    """Return each destination a `COPY` from the build context names, to its source.

    e.g. `COPY start.sh /start.sh` -> {"/start.sh": "start.sh"}
    """
    found = re.findall(r"^COPY\s+(?!--)(\S+)\s+(\S+)\s*$", dockerfile, re.M)
    return {dest: source for source, dest in found}


def missing_copy_sources(dockerfile: str) -> list[str]:
    """Return each `COPY` source that is not a file in the repository."""
    return [
        source
        for source in image_copies(dockerfile).values()
        if not (REPO / source).is_file()
    ]


def uncopied_provisioner(dockerfile: str, start_sh: str) -> str | None:
    """Return the provisioner the entrypoint runs, or None if the image copies it."""
    found = re.search(rf"bash ({IMAGE_ROOT}/\S+/download_models\.sh)", start_sh)
    assert found is not None
    called = found.group(1)
    return None if called in image_copies(dockerfile) else called


def manifest_in_image() -> str:
    """Return where `provision.py`'s anchor finds the manifest inside the image."""
    return f"{IMAGE_ROOT}/{MANIFEST_PATH.relative_to(REPO).as_posix()}"


@pytest.mark.spec_exempt("structural: the image copies files the repository holds")
def test_every_file_the_image_copies_exists(dockerfile: str) -> None:
    assert image_copies(dockerfile)
    assert missing_copy_sources(dockerfile) == []


@pytest.mark.spec_exempt("structural: twin of test_every_file_the_image_copies_exists")
def test_the_check_catches_a_copy_of_a_file_that_is_gone() -> None:
    broken = "FROM scratch\nCOPY start.sh /start.sh\nCOPY gone/models.json /x\n"
    assert missing_copy_sources(broken) == ["gone/models.json"]


@pytest.mark.spec_exempt("structural: the entrypoint runs a script the image holds")
def test_the_entrypoint_runs_the_provisioner_the_image_copies(
    dockerfile: str, start_sh: str
) -> None:
    assert uncopied_provisioner(dockerfile, start_sh) is None


@pytest.mark.spec_exempt(
    "structural: twin of test_the_entrypoint_runs_the_provisioner_the_image_copies"
)
def test_the_check_catches_an_entrypoint_calling_a_path_not_copied() -> None:
    broken = f"COPY x/download_models.sh {IMAGE_ROOT}/x/download_models.sh\n"
    start_sh = f"bash {IMAGE_ROOT}/y/download_models.sh || return 1\n"
    assert (
        uncopied_provisioner(broken, start_sh) == f"{IMAGE_ROOT}/y/download_models.sh"
    )


@pytest.mark.spec_exempt(
    "structural: the provisioner's anchor resolves to a file inside the image"
)
def test_the_manifest_the_provisioner_reads_is_copied_where_it_looks(
    dockerfile: str,
) -> None:
    assert manifest_in_image() in image_copies(dockerfile)


@pytest.mark.spec_exempt(
    "structural: twin of "
    "test_the_manifest_the_provisioner_reads_is_copied_where_it_looks"
)
def test_the_check_catches_a_manifest_copied_beside_where_it_looks() -> None:
    broken = f"COPY models.json {IMAGE_ROOT}/elsewhere/models.json\n"
    assert manifest_in_image() not in image_copies(broken)
