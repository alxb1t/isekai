"""Checks over the tracked pod configuration: the image and the pod lifecycle.

These read the shipped files themselves rather than a fixture copy, for the same
reason the suite reads the shipped graph: a byte-identical copy with no drift
check is a second thing to rename and a silent divergence waiting to happen.
"""

import json
import os
import re
import shlex
import subprocess
import tomllib
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
from tools.derive_image_project import pinned_commits, uv_required

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
    assert f'path: "{VOLUME_MOUNT}"' in up_sh


@pytest.mark.spec_exempt(
    "structural: the mount is a precondition of the namespace, not a scenario"
)
def test_the_pod_no_longer_mounts_the_volume_over_the_models_directory(
    up_sh: str,
) -> None:
    assert f'path: "{MODELS_ROOT}"' not in up_sh


@pytest.mark.spec_exempt(
    "structural: v2 defaults to Secure Cloud, and the pod asks for it by name anyway"
)
def test_the_pod_is_asked_for_secure_cloud(up_sh: str) -> None:
    assert 'cloud: "SECURE",' in up_sh


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
    """Read the shipped `tools/download_models.sh` once for the whole session."""
    return (REPO / "tools" / "download_models.sh").read_text()


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


def held_on_provisioning(start_sh: str) -> bool:
    """Whether the guarded provisioning step's failure branch calls `hold`."""
    lines = start_sh.splitlines()
    guard = lines.index("if ! provision; then")
    end = next(i for i in range(guard, len(lines)) if lines[i] == "fi")
    return any(ln.lstrip().startswith('hold "') for ln in lines[guard:end])


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
    assert held_on_provisioning(start_sh)


@pytest.mark.spec(
    "model-provisioning:reachability:a-provisioning-abort-holds-the-pod-open"
)
def test_the_hold_replaces_the_inference_server_rather_than_preceding_it(
    start_sh: str,
) -> None:
    lines = start_sh.splitlines()
    hold = next(i for i, line in enumerate(lines) if line.lstrip().startswith('hold "'))
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


def shell_function(script: str, name: str) -> str:
    """Return the definition of `name` as the script writes it, or "" if absent.

    e.g. `g` in a script holding `g() { :; }` -> "g() { :; }"
    """
    lines = script.splitlines()
    start = next(
        (i for i, ln in enumerate(lines) if ln.startswith(f"{name}() {{")), None
    )
    if start is None:
        return ""
    if lines[start].rstrip().endswith("}"):
        return lines[start]
    end = next(i for i in range(start, len(lines)) if lines[i] == "}")
    return "\n".join(lines[start : end + 1])


def provision_body(start_sh: str) -> str:
    """Return the body of `start.sh`'s `provision` function.

    The scenario is about provisioning as a whole rather than about one of its
    steps, so what the test needs is which lines are *inside* the guarded unit.
    """
    return shell_function(start_sh, "provision")


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
    assert 'sleep "$HOLD_SECONDS"' in shell_function(start_sh, "hold")
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
    creates = next(i for i, line in enumerate(lines) if 'POST "$API/pods"' in line)
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
        if "down.sh" in line and not line.lstrip().startswith(("#", "echo"))
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
    # ComfyUI's core and the two custom-node packs, each on a full commit sha
    assert len(pinned_commits(dockerfile)) == 3


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
    # That overlay's backing disk is the container `disk`, LARGER than the
    # pod's own volume disk, so a floor that only clears the volume disk lets the
    # overlay through and 16.5 GiB lands on storage that dies at teardown.
    floor = re.search(
        r"^VOLUME_SIZE_FLOOR_KIB=\$\(\((\d+) \* 1024 \* 1024\)\)", start_sh, re.M
    )
    assert floor is not None
    container_disk = re.search(r"\bdisk:\s*(\d+)", up_sh)
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


# The image is built on request, from inputs named by digest, into a locked
# environment: 0033 design D2.

BUILD_WORKFLOW = REPO / ".github" / "workflows" / "build-image.yml"


def workflow_triggers(workflow: str) -> list[str]:
    """Return the event names under a workflow's top-level `on:` key.

    e.g. `on:` over `push:` and `workflow_dispatch:` -> ["push", "workflow_dispatch"]
    """
    lines = workflow.splitlines()
    opens = lines.index("on:")
    triggers = []
    for line in lines[opens + 1 :]:
        if line and not line.startswith(" "):
            break
        found = re.match(r"^  ([a-z_]+):", line)
        if found:
            triggers.append(found.group(1))
    return triggers


@pytest.mark.spec("pod-image:build:only-a-request-builds")
def test_the_image_workflow_builds_only_on_a_manual_request() -> None:
    workflow = BUILD_WORKFLOW.read_text()
    assert workflow_triggers(workflow) == ["workflow_dispatch"]
    assert "${{ steps.build.outputs.digest }}" in workflow
    assert "$GITHUB_STEP_SUMMARY" in workflow


@pytest.mark.spec_exempt(
    "structural: twin of test_the_image_workflow_builds_only_on_a_manual_request"
)
def test_the_check_catches_a_workflow_that_builds_on_a_push() -> None:
    workflow = "on:\n  push:\n    branches: [main]\n  workflow_dispatch:\njobs:\n"
    assert workflow_triggers(workflow) == ["push", "workflow_dispatch"]


def undigested_images(dockerfile: str) -> list[str]:
    """Return each image the build starts from or copies from without a digest."""
    named = re.findall(r"^FROM\s+(\S+)", dockerfile, re.M)
    named += re.findall(r"^COPY\s+--from=(\S+)", dockerfile, re.M)
    return [image for image in named if not re.search(r"@sha256:[0-9a-f]{64}$", image)]


@pytest.mark.spec("pod-image:build:inputs-are-named-by-digest")
def test_the_base_and_the_build_tool_are_named_by_digest(dockerfile: str) -> None:
    assert re.search(r"^FROM\s", dockerfile, re.M)
    assert re.search(r"^COPY\s+--from=", dockerfile, re.M)
    assert undigested_images(dockerfile) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_base_and_the_build_tool_are_named_by_digest"
)
def test_the_check_catches_an_image_named_by_tag() -> None:
    broken = "FROM ubuntu:22.04\nCOPY --from=ghcr.io/astral-sh/uv:latest /uv /\n"
    assert undigested_images(broken) == [
        "ubuntu:22.04",
        "ghcr.io/astral-sh/uv:latest",
    ]


def uv_versions_apart(root: str, ci: str, dockerfile: str, image: str) -> list[str]:
    """Return each place naming a uv version other than the root project's.

    e.g. a `Dockerfile` copying `uv:0.8.24` under `==0.12.19` -> ["Dockerfile"]
    """
    setup = re.search(r"astral-sh/setup-uv@.*\n(?:.*\n)*?\s+version:\s*\"?([\w.]+)", ci)
    copied = re.search(
        r"^COPY\s+--from=ghcr\.io/astral-sh/uv:([\w.]+)@", dockerfile, re.M
    )
    named = {
        "ci.yml": f"=={setup.group(1)}" if setup else None,
        "Dockerfile": f"=={copied.group(1)}" if copied else None,
        "image/pyproject.toml": uv_required(image),
    }
    return [where for where, version in named.items() if version != uv_required(root)]


@pytest.mark.spec_exempt(
    "structural: one uv version, in CI, the image and both projects"
)
def test_every_uv_version_the_build_names_is_the_root_projects(
    dockerfile: str,
) -> None:
    apart = uv_versions_apart(
        (REPO / "pyproject.toml").read_text(),
        (REPO / ".github" / "workflows" / "ci.yml").read_text(),
        dockerfile,
        IMAGE_PROJECT.read_text(),
    )
    assert apart == []


@pytest.mark.spec_exempt(
    "structural: twin of test_every_uv_version_the_build_names_is_the_root_projects"
)
def test_the_check_catches_a_uv_version_that_drifted() -> None:
    root = '[tool.uv]\nrequired-version = "==0.12.19"\n'
    ci = (
        "      - uses: astral-sh/setup-uv@abc # v6\n"
        "        with:\n"
        '          version: "0.12.19"\n'
    )
    dockerfile = (
        "COPY --from=ghcr.io/astral-sh/uv:0.8.24@sha256:abc /uv /usr/local/bin/\n"
    )
    image = '[tool.uv]\nrequired-version = "==0.8.24"\n'
    assert uv_versions_apart(root, ci, dockerfile, image) == [
        "Dockerfile",
        "image/pyproject.toml",
    ]


def unlocked_installs(dockerfile: str) -> list[str]:
    """Return each build line that resolves packages instead of syncing the lock."""
    return [
        line.strip()
        for line in dockerfile.splitlines()
        if re.search(r"\bpip install\b|\buv venv\b|\s-r\s", line)
        or ("uv sync" in line and "--locked" not in line)
    ]


@pytest.mark.spec("pod-image:build:the-environment-is-locked")
def test_the_environment_is_installed_from_the_committed_lock(
    dockerfile: str,
) -> None:
    assert "uv sync --locked" in dockerfile
    assert "image/uv.lock" in image_copies(dockerfile).values()
    assert unlocked_installs(dockerfile) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_environment_is_installed_from_the_committed_lock"
)
def test_the_check_catches_a_resolving_install() -> None:
    broken = "RUN uv pip install -r requirements.txt\nRUN uv sync\n"
    assert unlocked_installs(broken) == [
        "RUN uv pip install -r requirements.txt",
        "RUN uv sync",
    ]


IMAGE_PROJECT = REPO / "image" / "pyproject.toml"


def unhashed_build_tools(image_pyproject: str) -> list[str]:
    """Return each build constraint not named by exact version with a sha256 hash.

    e.g. `"cython==3.3.0"` -> ["cython==3.3.0"]
    """
    uv = tomllib.loads(image_pyproject)["tool"]["uv"]
    tools = uv.get("build-constraint-dependencies", [])
    if not tools:
        return ["none listed"]
    unhashed = []
    for tool in tools:
        tool = tool if isinstance(tool, dict) else {"requirement": tool}
        named, hashes = tool.get("requirement", ""), tool.get("hashes", [])
        if not (
            re.fullmatch(r"[\w.-]+==[\w.]+", named)
            and hashes
            and all(re.fullmatch(r"sha256:[0-9a-f]{64}", h) for h in hashes)
        ):
            unhashed.append(named)
    return unhashed


@pytest.mark.spec("pod-image:build:the-build-tools-are-hashed")
def test_the_build_tools_are_checked_by_hash() -> None:
    assert unhashed_build_tools(IMAGE_PROJECT.read_text()) == []


@pytest.mark.spec_exempt("structural: twin of test_the_build_tools_are_checked_by_hash")
def test_the_check_catches_a_build_tool_by_version_alone() -> None:
    assert unhashed_build_tools("[tool.uv]\n") == ["none listed"]
    digest = "sha256:" + "0" * 64
    image_pyproject = (
        "[tool.uv]\nbuild-constraint-dependencies = [\n"
        '    "cython==3.3.0",\n'
        f'    {{ requirement = "numpy>=2", hashes = ["{digest}"] }},\n'
        '    { requirement = "setuptools==84.0.0", hashes = [] },\n'
        f'    {{ requirement = "wheel==0.45.0", hashes = ["{digest}"] }},\n'
        "]\n"
    )
    assert unhashed_build_tools(image_pyproject) == [
        "cython==3.3.0",
        "numpy>=2",
        "setuptools==84.0.0",
    ]


IMAGE_LOCK = REPO / "image" / "uv.lock"

# Each source-only package in the image's lock, to the tools its build asks for: its
# `build-system.requires`, or setuptools for a `setup.py` with none. uv checks only
# the tools the constraints list, so a package joins this table once its tools do.
SDIST_BUILDS = {
    "antlr4-python3-runtime": ("setuptools",),
    "fvcore": ("setuptools",),
    "insightface": ("setuptools", "numpy", "cython"),
    "iopath": ("setuptools",),
}


def uncovered_sdists(image_lock: str, image_pyproject: str) -> list[str]:
    """Return each source-only package whose build tools the constraints do not name.

    e.g. a lock gaining `pycocotools` as an sdist alone -> ["pycocotools"]
    """
    tools = tomllib.loads(image_pyproject)["tool"]["uv"].get(
        "build-constraint-dependencies", []
    )
    named = {
        re.split(r"[=<>!~ ]", tool if isinstance(tool, str) else tool["requirement"])[0]
        for tool in tools
    }
    uncovered = []
    for package in tomllib.loads(image_lock)["package"]:
        if "sdist" not in package or package.get("wheels"):
            continue
        name = package["name"]
        if name not in SDIST_BUILDS:
            uncovered.append(name)
            continue
        uncovered += [f"{name}: {t}" for t in SDIST_BUILDS[name] if t not in named]
    return uncovered


@pytest.mark.spec("pod-image:build:the-build-tools-are-hashed")
def test_every_source_only_package_builds_with_constrained_tools() -> None:
    assert uncovered_sdists(IMAGE_LOCK.read_text(), IMAGE_PROJECT.read_text()) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_every_source_only_package_builds_with_constrained_tools"
)
def test_the_check_catches_a_source_only_package_the_constraints_miss() -> None:
    image_lock = IMAGE_LOCK.read_text() + (
        '\n[[package]]\nname = "pycocotools"\nversion = "2.0.8"\n'
        'source = { registry = "https://pypi.org/simple" }\n'
        'sdist = { url = "https://example.invalid/pycocotools-2.0.8.tar.gz" }\n'
    )
    image_pyproject = IMAGE_PROJECT.read_text()
    assert uncovered_sdists(image_lock, image_pyproject) == ["pycocotools"]
    no_cython = re.sub(r'\{ requirement = "cython==[^}]*\},?', "", image_pyproject)
    assert uncovered_sdists(IMAGE_LOCK.read_text(), no_cython) == [
        "insightface: cython"
    ]


# The line each step of `start.sh` begins with: the stop timer, the SSH key, sshd,
# provisioning, the download inside it, the memory directories, and ComfyUI.
BOOT_STEPS = (
    '( sleep "$POD_CEILING_SECONDS"',
    "mkdir -p ~/.ssh",
    "mkdir -p /run/sshd",
    "if ! provision; then",
    'MODELS_DIR="$MODELS_ROOT" bash',
    "mkdir -p /dev/shm/comfyui/input",
    "exec python main.py",
)


def unstamped_steps(start_sh: str) -> list[str]:
    """Return each boot step whose line is not preceded by a UTC timestamp."""
    lines = [line.strip() for line in start_sh.splitlines()]
    unstamped = []
    for step in BOOT_STEPS:
        at = next(i for i, line in enumerate(lines) if line.startswith(step))
        if "date -u" not in lines[at - 1]:
            unstamped.append(step)
    return unstamped


@pytest.mark.spec("pod-image:boot:each-step-is-timestamped")
def test_each_boot_step_prints_a_utc_time_before_it_begins(
    start_sh: str, up_sh: str
) -> None:
    assert unstamped_steps(start_sh) == []
    assert "created at $(date -u" in up_sh
    assert "Port 22 mapped at $(date -u" in up_sh


@pytest.mark.spec_exempt(
    "structural: twin of test_each_boot_step_prints_a_utc_time_before_it_begins"
)
def test_the_check_catches_a_step_with_no_timestamp() -> None:
    stamped = "\n".join(f'echo "$(date -u +%FT%TZ)"\n{step}' for step in BOOT_STEPS)
    assert unstamped_steps(stamped) == []
    assert unstamped_steps(
        stamped.replace('echo "$(date -u +%FT%TZ)"\nexec', "exec")
    ) == ["exec python main.py"]


# The pod's own host key, and ComfyUI's writing kept in memory: text checks over
# the shipped files, proved on a pod by `0040` design D6.


def joined_lines(text: str) -> list[str]:
    """Return each line of a script, its continuation lines joined into one."""
    return re.sub(r"\\\n", " ", text).splitlines()


def baked_host_key_faults(dockerfile: str) -> list[str]:
    """Return how a host key could reach the image.

    Kept by the layer installing the SSH server, or made or installed again by any
    other line; comments are not read.
    """
    lines = [
        line for line in joined_lines(dockerfile) if not line.lstrip().startswith("#")
    ]
    install = next(
        line for line in lines if line.startswith("RUN ") and "openssh-server" in line
    )
    faults = []
    if install.find("rm -f /etc/ssh/ssh_host_*") < install.index("openssh-server"):
        faults.append("the install layer keeps its keys")
    if any(
        word in line
        for line in lines
        if line is not install
        for word in ("ssh_host_", "ssh-keygen", "openssh")
    ):
        faults.append("another line touches the SSH server's keys")
    return faults


@pytest.mark.spec("pod-image:host-key:the-image-carries-none")
def test_the_image_carries_no_host_key(dockerfile: str) -> None:
    assert baked_host_key_faults(dockerfile) == []


@pytest.mark.spec_exempt("structural: twin of test_the_image_carries_no_host_key")
def test_the_check_catches_a_host_key_kept_or_made_again() -> None:
    install = (
        "# the keys `openssh-server` makes are deleted here\n"
        "RUN apt-get install -y \\\n        openssh-server \\\n"
        "    && rm -f /etc/ssh/ssh_host_* \\\n"
        "    && rm -rf /var/lib/apt/lists/*\n"
    )
    assert baked_host_key_faults(install) == []
    later = install.replace(" \\\n    && rm -f", "\nRUN rm -f")
    assert baked_host_key_faults(later) == [
        "the install layer keeps its keys",
        "another line touches the SSH server's keys",
    ]
    before = (
        "RUN rm -f /etc/ssh/ssh_host_* \\\n    && apt-get install -y openssh-server\n"
    )
    assert baked_host_key_faults(before) == ["the install layer keeps its keys"]
    for again in ("RUN ssh-keygen -A", "RUN dpkg-reconfigure openssh-server"):
        assert baked_host_key_faults(f"{install}{again}\n") == [
            "another line touches the SSH server's keys"
        ]


def boot_step(start_sh: str, name: str) -> str:
    """Return the `start.sh` step `name` opens, from its timestamp to its blank line."""
    lines = start_sh.splitlines()
    opens = next(i for i, line in enumerate(lines) if line.endswith(f'step: {name}"'))
    closes = next(i for i, line in enumerate(lines[opens:], opens) if not line)
    return "\n".join(lines[opens:closes])


def host_key_faults(start_sh: str) -> list[str]:
    """Return what the sshd step lacks of a key made at boot, served alone, printed."""
    step = boot_step(start_sh, "sshd")
    faults = []
    if "ssh-keygen -A" in step or "ssh-keygen -q -t ed25519" not in step:
        faults.append("makes other than one Ed25519 key")
    if not re.search(r'^/usr/sbin/sshd -o HostKey="\$key"$', step, re.M):
        faults.append("serves other than its own key")
    if 'echo "isekai host key: $(ssh-keygen -lf "$key.pub"' not in step:
        faults.append("prints no fingerprint")
    return faults


@pytest.mark.spec("pod-image:host-key:each-boot-makes-and-prints-one")
def test_each_boot_makes_and_prints_its_own_key(start_sh: str) -> None:
    assert host_key_faults(start_sh) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_each_boot_makes_and_prints_its_own_key"
)
def test_the_check_catches_an_sshd_serving_every_stock_key() -> None:
    stock = 'echo "$(date -u +%FT%TZ) step: sshd"\nssh-keygen -A\n/usr/sbin/sshd\n\n'
    assert host_key_faults(stock) == [
        "makes other than one Ed25519 key",
        "serves other than its own key",
        "prints no fingerprint",
    ]


def serve_command(start_sh: str) -> str:
    """Return the line that starts ComfyUI, its continuation lines joined into one."""
    return next(
        line
        for line in joined_lines(start_sh)
        if line.startswith("exec python main.py")
    )


def comfyui_directories(start_sh: str) -> dict[str, str]:
    """Return each directory ComfyUI writes to, by kind, as its start line sets it.

    e.g. `--temp-directory /dev/shm/comfyui` -> {"temp": "/dev/shm/comfyui/temp"}
    """
    found = dict(
        re.findall(
            r"--(input|output|temp|user)-directory (\S+)", serve_command(start_sh)
        )
    )
    # ComfyUI writes its temp files to `temp` under the directory it is given.
    if "temp" in found:
        found["temp"] += "/temp"
    return found


def before_serve(start_sh: str) -> str:
    """Return the start script up to the line that starts ComfyUI."""
    return start_sh[: start_sh.index("exec python main.py")]


def made_directories(start_sh: str) -> set[str]:
    """Return each directory a `mkdir -p` makes before ComfyUI starts."""
    return {
        path
        for line in before_serve(start_sh).splitlines()
        if line.startswith("mkdir -p ")
        for path in line.split()[2:]
    }


def unmade_directories(start_sh: str) -> list[str]:
    """Return each directory ComfyUI writes to that no `mkdir -p` makes before it."""
    made = made_directories(start_sh)
    return sorted(set(comfyui_directories(start_sh).values()) - made)


@pytest.mark.spec("pod-image:memory:comfyui-writes-to-memory")
def test_comfyui_writes_to_memory(start_sh: str) -> None:
    directories = comfyui_directories(start_sh)
    assert sorted(directories) == ["input", "output", "temp", "user"]
    assert all(path.startswith("/dev/shm/") for path in directories.values())
    assert unmade_directories(start_sh) == []


@pytest.mark.spec_exempt("structural: twin of test_comfyui_writes_to_memory")
def test_the_check_catches_a_directory_on_disk_or_not_made() -> None:
    assert comfyui_directories("exec python main.py --port 8188\n") == {}
    unmade = (
        "mkdir -p /dev/shm/comfyui/input\n"
        "exec python main.py --input-directory /dev/shm/comfyui/input \\\n"
        "    --temp-directory /dev/shm/comfyui\n"
    )
    assert unmade_directories(unmade) == ["/dev/shm/comfyui/temp"]


def memory_hold_faults(start_sh: str) -> list[str]:
    """Return what the memory step lacks of a hold on too little free memory."""
    step = boot_step(start_sh, "the memory directories")
    faults = []
    measured = re.search(r"df -k --output=(\S+) /dev/shm", step)
    if measured is None:
        faults.append("does not measure /dev/shm")
    else:
        columns = measured.group(1).split(",")
        free = columns.index("avail") + 1 if "avail" in columns else 0
        if f"free_kib=\"$(awk '{{print ${free}}}'" not in step:
            faults.append("reads other than the free column")
    if not re.search(
        r'^if \[ "\$free_kib" -lt "\$SHM_FREE_FLOOR_KIB" \]; then$', step, re.M
    ):
        faults.append("compares against no floor")
    if any(int(guess) for guess in re.findall(r"\bfree_kib=(\d+)", step)):
        faults.append("defaults an unreadable figure to free memory")
    if not re.search(r'SHM_FREE_FLOOR_KIB" \]; then\n\s*hold "ERROR: ', step):
        faults.append("does not say why and hold")
    return faults


@pytest.mark.spec("pod-image:memory:too-little-memory-holds")
def test_too_little_memory_holds_the_pod(start_sh: str) -> None:
    floor = re.search(
        r"^SHM_FREE_FLOOR_KIB=\$\(\((\d+) \* 1024 \* 1024\)\)$", start_sh, re.M
    )
    assert floor is not None
    assert int(floor.group(1)) >= 1
    assert memory_hold_faults(start_sh) == []
    step = boot_step(start_sh, "the memory directories")
    assert start_sh.index(step) < start_sh.index("exec python main.py")


@pytest.mark.spec_exempt("structural: twin of test_too_little_memory_holds_the_pod")
def test_the_check_catches_a_memory_step_that_never_holds() -> None:
    holds = (
        'echo "$(date -u +%FT%TZ) step: the memory directories"\n'
        "mkdir -p /dev/shm/comfyui/input\n"
        "shm_kib=\"$(df -k --output=size,avail /dev/shm | tail -n 1)\" || shm_kib=''\n"
        'free_kib="$(awk \'{print $2}\' <<<"$shm_kib")"\n'
        'case "$free_kib" in\n'
        "    '' | *[!0-9]*) free_kib=0 ;;\n"
        "esac\n"
        'if [ "$free_kib" -lt "$SHM_FREE_FLOOR_KIB" ]; then\n'
        '    hold "ERROR: too little"\n'
        "fi\n\n"
    )
    assert memory_hold_faults(holds) == []
    silent = holds.replace('    hold "ERROR: too little"\n', "    true\n")
    assert memory_hold_faults(silent) == ["does not say why and hold"]
    for inverted in ('[ "$free_kib" -ge', '! [ "$free_kib" -lt'):
        assert memory_hold_faults(holds.replace('[ "$free_kib" -lt', inverted)) == [
            "compares against no floor"
        ]
    size_column = holds.replace("{print $2}", "{print $1}")
    assert memory_hold_faults(size_column) == ["reads other than the free column"]
    guessed = holds.replace("free_kib=0 ;;", "free_kib=99999999 ;;")
    assert memory_hold_faults(guessed) == [
        "defaults an unreadable figure to free memory"
    ]


def spool_faults(start_sh: str) -> list[str]:
    """Return what the start script lacks of a `TMPDIR` made in memory for ComfyUI."""
    exported = re.search(r"^export TMPDIR=(\S+)$", before_serve(start_sh), re.M)
    if exported is None:
        return ["sets no TMPDIR"]
    faults = []
    if not exported.group(1).startswith("/dev/shm/"):
        faults.append("spools outside /dev/shm")
    if exported.group(1) not in made_directories(start_sh):
        faults.append("spools to a directory not made")
    return faults


@pytest.mark.spec("pod-image:memory:uploads-spool-to-memory")
def test_comfyui_spools_uploads_to_memory(start_sh: str) -> None:
    assert spool_faults(start_sh) == []


@pytest.mark.spec_exempt("structural: twin of test_comfyui_spools_uploads_to_memory")
def test_the_check_catches_an_upload_spooled_to_disk() -> None:
    made = "mkdir -p /dev/shm/comfyui/tmp\n"
    serve = "exec python main.py\n"
    assert spool_faults(made + serve) == ["sets no TMPDIR"]
    assert spool_faults(made + serve + "export TMPDIR=/dev/shm/comfyui/tmp\n") == [
        "sets no TMPDIR"
    ]
    assert spool_faults(made + "export TMPDIR=/tmp\n" + serve) == [
        "spools outside /dev/shm",
        "spools to a directory not made",
    ]


def run_memory_step(
    step: str, tmp_path: Path, shm_type: str | None, df_row: str
) -> subprocess.CompletedProcess[str]:
    """Run the memory step on a `/dev/shm` of `shm_type` whose `df` row is `df_row`.

    None is a `stat` that fails. A hold prints `held`; a start prints `started`.
    """
    stubs = tmp_path / "bin"
    stubs.mkdir(exist_ok=True)
    # `exec` finds only a file on PATH, so a hold's `sleep` is one.
    (stubs / "sleep").write_text("#!/bin/sh\necho held\n")
    (stubs / "sleep").chmod(0o755)
    hold = 'hold() { printf "%s\\n" "$@" >&2; echo held; exit 0; }'
    stat = f"echo {shlex.quote(shm_type)}" if shm_type is not None else "return 1"
    program = "\n".join(
        [
            "set -euo pipefail",
            "HOLD_SECONDS=900 SHM_FREE_FLOOR_KIB=$((1 * 1024 * 1024))",
            "mkdir() { :; }",
            f"stat() {{ {stat}; }}",
            f"df() {{ printf '%s\\n' '1K-blocks Avail' {shlex.quote(df_row)}; }}",
            hold,
            step,
            "echo started",
        ]
    )
    return subprocess.run(
        ["bash", "-c", program],
        env={"PATH": f"{stubs}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


ROOMY = "8388608 8388608"


@pytest.mark.spec("pod-image:memory:a-disk-backed-shm-holds")
def test_a_shm_that_is_not_memory_holds_the_pod(start_sh: str, tmp_path: Path) -> None:
    step = boot_step(start_sh, "the memory directories")
    assert run_memory_step(step, tmp_path, "tmpfs", ROOMY).stdout.endswith("started\n")
    for shm_type in ("ext2/ext3", "overlayfs"):
        done = run_memory_step(step, tmp_path, shm_type, ROOMY)
        assert done.stdout.endswith("held\n")
        assert shm_type in done.stderr
    assert run_memory_step(step, tmp_path, None, ROOMY).stdout.endswith("held\n")


@pytest.mark.spec_exempt(
    "structural: twin of test_a_shm_that_is_not_memory_holds_the_pod"
)
def test_the_check_catches_a_shm_never_typed(start_sh: str, tmp_path: Path) -> None:
    step = boot_step(start_sh, "the memory directories")
    untyped = re.sub(r'\nif \[ "\$shm_type".*?\nfi', "", step, flags=re.S)
    assert untyped != step
    done = run_memory_step(untyped, tmp_path, "ext2/ext3", ROOMY)
    assert done.stdout.endswith("started\n")


@pytest.mark.spec("pod-image:memory:an-unread-figure-holds")
def test_an_unread_figure_holds_the_pod(start_sh: str, tmp_path: Path) -> None:
    step = boot_step(start_sh, "the memory directories")
    for row in ("", "- -", "8388608 n/a"):
        done = run_memory_step(step, tmp_path, "tmpfs", row)
        assert done.stdout.endswith("held\n")
        assert "could not read /dev/shm's free space" in done.stderr


@pytest.mark.spec_exempt("structural: twin of test_an_unread_figure_holds_the_pod")
def test_the_check_catches_an_unread_figure_taken_as_zero(
    start_sh: str, tmp_path: Path
) -> None:
    # Held, but by the floor, saying the pod has too little memory: a guess.
    step = boot_step(start_sh, "the memory directories")
    guessed = re.sub(r"(\*\[!0-9\]\*\)).*?;;", r"\1 free_kib=0 ;;", step, flags=re.S)
    assert guessed != step
    done = run_memory_step(guessed, tmp_path, "tmpfs", "- -")
    assert done.stdout.endswith("held\n")
    assert "could not read /dev/shm's free space" not in done.stderr


@pytest.mark.spec("pod-image:render-metadata:none-is-written")
def test_comfyui_writes_no_metadata(start_sh: str) -> None:
    assert "--disable-metadata" in serve_command(start_sh).split()


@pytest.mark.spec_exempt("structural: twin of test_comfyui_writes_no_metadata")
def test_the_check_catches_the_flag_outside_the_start_line() -> None:
    elsewhere = "# --disable-metadata\nexec python main.py --port 8188\n"
    assert "--disable-metadata" not in serve_command(elsewhere).split()


WORKFLOWS = sorted((REPO / ".github" / "workflows").glob("*.yml"))


def unparseable_run_lines(workflow: str) -> list[str]:
    """Return each one-line `run:` whose value holds `: `, which YAML rejects.

    GitHub then refuses the whole workflow, so a dispatch-only build cannot start.
    """
    found = (
        re.match(r"^\s*(?:- )?run: (?![|>])(.*)$", line)
        for line in workflow.splitlines()
    )
    return [
        match.group(0).strip() for match in found if match and ": " in match.group(1)
    ]


@pytest.mark.spec("pod-image:build:only-a-request-builds")
def test_every_workflow_run_line_is_one_yaml_accepts() -> None:
    assert WORKFLOWS
    for workflow in WORKFLOWS:
        assert unparseable_run_lines(workflow.read_text()) == [], workflow.name


@pytest.mark.spec_exempt(
    "structural: twin of test_every_workflow_run_line_is_one_yaml_accepts"
)
def test_the_check_catches_a_plain_run_line_holding_a_colon() -> None:
    broken = '      - run: echo "a: b"\n        run: |\n          echo "a: b"\n'
    assert unparseable_run_lines(broken) == ['- run: echo "a: b"']


# A pod boots the digest `config/image.json` pins, and nothing else: 0033 design D3.

IMAGE_CONFIG = REPO / "config" / "image.json"
IMAGE_REFERENCE = (
    """image_ref="$(jq -r '"\\(.image)@\\(.digest)"' config/image.json)\""""
)


def pinned_reference(config: dict[str, str]) -> str | None:
    """Return `<image>@<digest>` for an image config, or None if it pins no digest."""
    digest = config.get("digest", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        return None
    return f"{config['image']}@{digest}"


@pytest.mark.spec("pod-image:boot:the-pinned-digest-is-booted")
def test_the_pod_is_created_from_the_pinned_digest(up_sh: str) -> None:
    assert pinned_reference(json.loads(IMAGE_CONFIG.read_text())) is not None
    assert IMAGE_REFERENCE in up_sh
    assert '--arg image  "$image_ref"' in up_sh
    assert "image: $image," in up_sh
    assert ":latest" not in up_sh


@pytest.mark.spec_exempt(
    "structural: twin of test_the_pod_is_created_from_the_pinned_digest"
)
def test_the_check_catches_an_image_config_naming_only_a_tag() -> None:
    assert pinned_reference({"image": "ghcr.io/a/b", "tag": "latest"}) is None
    assert pinned_reference({"image": "ghcr.io/a/b", "digest": "latest"}) is None


def image_overrides(up_sh: str) -> list[str]:
    """Return each line that sets the booted image from anything but the pin."""
    return [
        line.strip()
        for line in up_sh.splitlines()
        if re.search(r"^\s*(image_ref|\w*IMAGE\w*)=", line)
        and line.strip() != IMAGE_REFERENCE
    ]


@pytest.mark.spec("pod-image:boot:no-override")
def test_nothing_in_the_environment_overrides_the_image(up_sh: str) -> None:
    assert image_overrides(up_sh) == []
    assert "RUNPOD_IMAGE" not in up_sh


@pytest.mark.spec_exempt(
    "structural: twin of test_nothing_in_the_environment_overrides_the_image"
)
def test_the_check_catches_an_image_the_environment_can_set() -> None:
    broken = 'RUNPOD_IMAGE="${RUNPOD_IMAGE:-ghcr.io/a/b:latest}"\n' + IMAGE_REFERENCE
    assert image_overrides(broken) == [
        'RUNPOD_IMAGE="${RUNPOD_IMAGE:-ghcr.io/a/b:latest}"'
    ]


def removed_on_204(down_sh: str) -> str:
    """Return the line `down.sh` runs right after a 204, the record files' removal."""
    down = down_sh.splitlines()
    deleted = next(i for i, line in enumerate(down) if '"$code" = "204"' in line)
    return down[deleted + 1]


def unrecorded_boot(up_sh: str, down_sh: str) -> list[str]:
    """Return what is missing of the boot record's write and its removal on 204."""
    missing = []
    up = up_sh.splitlines()
    pod_id = next(
        i for i, line in enumerate(up) if line == 'echo "$pod_id" > .runpod_pod_id'
    )
    if 'echo "$image_ref" > .runpod_pod_image' not in up[pod_id:]:
        missing.append("written beside the pod id")
    if ".runpod_pod_image" not in removed_on_204(down_sh):
        missing.append("removed on 204")
    return missing


@pytest.mark.spec("pod-image:boot:the-booted-image-is-recorded")
def test_the_booted_reference_is_recorded_and_removed_with_the_pod(
    up_sh: str, down_sh: str
) -> None:
    assert unrecorded_boot(up_sh, down_sh) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_booted_reference_is_recorded_and_removed_with_the_pod"
)
def test_the_check_catches_a_boot_record_left_behind() -> None:
    up_sh = 'echo "$pod_id" > .runpod_pod_id\n'
    down_sh = 'if [ "$code" = "204" ]; then\n  rm -f .runpod_pod_id\n'
    assert unrecorded_boot(up_sh, down_sh) == [
        "written beside the pod id",
        "removed on 204",
    ]


# RunPod retires REST v1 on 2026-11-15, after which no pod can be torn down
# through it: 0034 design D5.
RETIRED_API = "rest.runpod.io"


def retired_api_calls(scripts: dict[str, str]) -> list[str]:
    """Return each script that names RunPod's retired REST v1 host, by name."""
    return sorted(name for name, text in scripts.items() if RETIRED_API in text)


@pytest.mark.spec_exempt("structural: no requirement names RunPod's API version")
def test_no_script_calls_the_retired_api() -> None:
    scripts = {p.name: p.read_text() for p in (REPO / "infra").iterdir() if p.is_file()}
    assert "up.sh" in scripts and "down.sh" in scripts
    assert retired_api_calls(scripts) == []


@pytest.mark.spec_exempt("structural: twin of test_no_script_calls_the_retired_api")
def test_the_retired_api_check_catches_a_v1_call() -> None:
    scripts = {
        "up.sh": 'curl -s "https://api.runpod.io/v2/pods"\n',
        "down.sh": 'curl -s -X DELETE "https://rest.runpod.io/v1/pods/$pod_id"\n',
    }
    assert retired_api_calls(scripts) == ["down.sh"]


# Every call to RunPod goes through one helper: the key reaches curl on a file
# descriptor rather than its argv, where any process listing reads it, and every
# call is bounded, so a stalled read cannot hold the poll past its teardown.
def unsafe_api_calls(scripts: dict[str, str]) -> list[str]:
    """Return each script whose curl puts the key on argv or has no time bound."""
    found = []
    for name, text in sorted(scripts.items()):
        code = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
        if any("Bearer" in ln and "@<(printf" not in ln for ln in code):
            found.append(f"{name}: key on argv")
        if any("curl " in ln and "--max-time" not in ln for ln in code):
            found.append(f"{name}: unbounded curl")
    return found


@pytest.mark.spec_exempt("structural: how the scripts hand curl the key and a bound")
def test_every_api_call_is_bounded_and_keeps_the_key_off_argv() -> None:
    scripts = {p.name: p.read_text() for p in (REPO / "infra").iterdir() if p.is_file()}
    scripts["tools/stop_pod.sh"] = (REPO / "tools" / "stop_pod.sh").read_text()
    assert all("curl " in scripts[n] for n in ("up.sh", "down.sh", "tools/stop_pod.sh"))
    assert unsafe_api_calls(scripts) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_every_api_call_is_bounded_and_keeps_the_key_off_argv"
)
def test_the_api_call_check_catches_a_key_on_argv_and_an_unbounded_read() -> None:
    scripts = {
        "down.sh": 'curl -s -X DELETE "$u" -H "Authorization: Bearer $KEY"\n',
        "up.sh": "curl -s --max-time 30 -H @<(printf 'Authorization: Bearer %s' $k)\n",
    }
    assert unsafe_api_calls(scripts) == [
        "down.sh: key on argv",
        "down.sh: unbounded curl",
    ]


def unwarned_lost_create(up_sh: str) -> list[str]:
    """Return what `up.sh` omits when a create's outcome is unknown."""
    missing = []
    lines = up_sh.splitlines()
    post = next(i for i, line in enumerate(lines) if 'POST "$API/pods"' in line)
    statement = next(i for i in range(post, len(lines)) if not lines[i].endswith("\\"))
    if not lines[statement].endswith("|| true"):
        missing.append("a transport failure is reported")
    unknown = [ln for ln in lines if ln.lstrip().startswith("201|5??|000|")]
    if not unknown:
        missing.append("201 without an id, 5xx and no answer are unknown")
    if "bash infra/down.sh" not in shell_function(up_sh, "lost"):
        missing.append("names down.sh")
    return missing


@pytest.mark.spec("pod-image:reconcile:a-lost-create-names-the-teardown")
def test_a_create_whose_outcome_is_unknown_says_a_pod_may_exist(up_sh: str) -> None:
    assert unwarned_lost_create(up_sh) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_a_create_whose_outcome_is_unknown_says_a_pod_may_exist"
)
def test_the_lost_create_check_catches_a_silent_create() -> None:
    up_sh = 'out=$(curl -s -X POST "$API/pods" \\\n  -d "$body")\n'
    assert unwarned_lost_create(up_sh) == [
        "a transport failure is reported",
        "201 without an id, 5xx and no answer are unknown",
        "names down.sh",
    ]


def unnamed_record_removal(down_sh: str) -> bool:
    """Whether `down.sh`'s 404 refusal omits the files to delete once confirmed."""
    lines = down_sh.splitlines()
    start = next(i for i, line in enumerate(lines) if '"$code" = "404"' in line)
    end = next(
        i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("el")
    )
    fix = "rm .runpod_pod_id .runpod_pod_image .runpod_known_hosts"
    return fix not in "\n".join(lines[start:end])


@pytest.mark.spec_exempt("structural: a refusal names its fix, per docs/principles.md")
def test_a_404_teardown_names_the_record_files_to_remove(down_sh: str) -> None:
    assert not unnamed_record_removal(down_sh)


@pytest.mark.spec_exempt(
    "structural: twin of test_a_404_teardown_names_the_record_files_to_remove"
)
def test_the_record_removal_check_catches_a_404_naming_no_file() -> None:
    down_sh = (
        'elif [ "$code" = "404" ]; then\n'
        '  echo "Confirm it is gone with the RunPod MCP." >&2\n'
        "  exit 1\n"
        "else\n"
    )
    assert unnamed_record_removal(down_sh)


@pytest.fixture(scope="session")
def render_sh() -> str:
    """Read the shipped `infra/render.sh` once for the whole session."""
    return (REPO / "infra" / "render.sh").read_text()


@pytest.fixture(scope="session")
def down_sh() -> str:
    """Read the shipped `infra/down.sh` once for the whole session."""
    return (REPO / "infra" / "down.sh").read_text()


def _code(script: str) -> list[str]:
    """Return the script's lines with comment lines blanked, so indices hold."""
    return ["" if ln.lstrip().startswith("#") else ln for ln in script.splitlines()]


def untrapped_teardown(script: str) -> list[str]:
    """Return what a render session's trap misses of tearing the pod down.

    e.g. a script whose trap is set after `up.sh` -> ["set before the pod"]
    """
    lines = _code(script)
    traps = [i for i, ln in enumerate(lines) if ln.startswith("trap ")]
    if not traps:
        return ["a trap"]
    trap = lines[traps[0]]
    missing = [f"on {sig}" for sig in ("EXIT", "INT", "TERM", "HUP") if sig not in trap]
    handler = re.search(r"trap '?(\w+)", trap)
    name = f"{handler[1]}()" if handler else None
    start = next(
        (i for i, ln in enumerate(lines) if name and ln.startswith(name)), None
    )
    body = ""
    if start is not None:
        end = next(i for i in range(start, len(lines)) if lines[i] == "}")
        body = "\n".join(lines[start:end])
    if "./infra/down.sh" not in body:
        missing.append("runs down.sh")
    if "kill " not in body:
        missing.append("closes the tunnel")
    # Ignored, not reset: a second Ctrl-C would otherwise kill down.sh mid-DELETE.
    if "trap '' INT TERM HUP" not in body:
        missing.append("ignores a second signal")
    up = next(i for i, ln in enumerate(lines) if "infra/up.sh" in ln)
    if traps[0] > up:
        missing.append("set before the pod")
    return missing


@pytest.mark.spec("pod-image:session:every-exit-tears-down")
def test_every_way_out_of_a_render_session_tears_the_pod_down(render_sh: str) -> None:
    assert untrapped_teardown(render_sh) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_every_way_out_of_a_render_session_tears_the_pod_down"
)
def test_the_teardown_check_catches_a_late_trap_that_leaves_the_tunnel() -> None:
    script = (
        "bash ./infra/up.sh\n"
        "teardown() {\n  bash ./infra/down.sh\n}\n"
        "trap teardown EXIT\n"
    )
    assert untrapped_teardown(script) == [
        "on INT",
        "on TERM",
        "on HUP",
        "closes the tunnel",
        "ignores a second signal",
        "set before the pod",
    ]


def unbounded_session(script: str) -> list[str]:
    """Return what a render session misses of halting at the pod ceiling.

    `CLAUDE.md` makes 45 minutes a halt, so a watchdog started before the pod
    signals the script, whose trap tears the pod down, and stops the command in
    flight, which would otherwise hold the trap until it ended.
    e.g. a script with no watchdog -> ["a stated ceiling", ...]
    """
    lines = _code(script)
    missing = []
    ceiling = re.search(r"^CEILING=(\d+)", script, re.M)
    if ceiling is None or not 0 < int(ceiling[1]) <= 45 * 60:
        missing.append("a stated ceiling")
    started = [i for i, ln in enumerate(lines) if "end=$((SECONDS + CEILING))" in ln]
    trap = next((i for i, ln in enumerate(lines) if ln.startswith("trap ")), None)
    up = next(i for i, ln in enumerate(lines) if "infra/up.sh" in ln)
    if not started or trap is None or not trap < started[0] < up:
        missing.append("started after the trap, before the pod")
    if not any("kill -TERM $$" in ln for ln in lines):
        missing.append("ends through the trap")
    if not any("pkill -TERM -P $$" in ln for ln in lines):
        missing.append("stops the command in flight")
    if not any('kill "$watchdog"' in ln for ln in lines):
        missing.append("stopped at teardown")
    return missing


@pytest.mark.spec_exempt(
    "structural: CLAUDE.md's 45-minute pod ceiling, which no requirement names"
)
def test_a_render_session_halts_at_the_pod_ceiling(render_sh: str) -> None:
    assert unbounded_session(render_sh) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_a_render_session_halts_at_the_pod_ceiling"
)
def test_the_ceiling_check_catches_a_session_with_no_watchdog() -> None:
    script = 'trap teardown EXIT\nbash ./infra/up.sh\ngenerate --server "$SERVER"\n'
    assert unbounded_session(script) == [
        "a stated ceiling",
        "started after the trap, before the pod",
        "ends through the trap",
        "stops the command in flight",
        "stopped at teardown",
    ]


def unlogged_refusal(script: str) -> list[str]:
    """Return what a render session's `refuse()` misses of reaching the batch's log.

    The run-flows skill discards render.sh's own output and reads the log, so a
    refusal only on stderr reaches no one. e.g. `echo ... >&2` -> ["the log"]
    """
    body = next((ln for ln in _code(script) if ln.startswith("refuse()")), "")
    missing = []
    if 'tee -a "${log:-' not in body:
        missing.append("the log")
    if ">&2" not in body:
        missing.append("stderr")
    return missing


@pytest.mark.spec_exempt(
    "structural: a refusal is never silent, per docs/principles.md"
)
def test_a_render_sessions_refusal_reaches_the_batchs_log(render_sh: str) -> None:
    assert unlogged_refusal(render_sh) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_a_render_sessions_refusal_reaches_the_batchs_log"
)
def test_the_refusal_check_catches_one_only_on_stderr() -> None:
    script = 'refuse() { echo "refused: $*" >&2; exit 1; }\n'
    assert unlogged_refusal(script) == ["the log"]


def unawaited_endpoint(script: str) -> list[str]:
    """Return what a render session misses of waiting, boundedly, for the endpoint."""
    lines = _code(script)
    missing = []
    asked = [
        i for i, ln in enumerate(lines) if "/system_stats" in ln and "until " in ln
    ]
    render = next(i for i, ln in enumerate(lines) if "--server" in ln)
    if not asked or asked[0] > render:
        missing.append("asked before any render")
    bound = re.search(r"^WAIT=(\d+)", script, re.M)
    if bound is None or not 0 < int(bound[1]) <= 600:
        missing.append("a stated bound")
    if not any("$deadline" in ln for ln in lines) or not any(
        "within ${WAIT}s" in ln for ln in lines
    ):
        missing.append("gives up past it")
    return missing


@pytest.mark.spec("pod-image:session:the-endpoint-is-awaited")
def test_a_render_session_waits_for_the_endpoint_within_a_bound(
    render_sh: str,
) -> None:
    assert unawaited_endpoint(render_sh) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_a_render_session_waits_for_the_endpoint_within_a_bound"
)
def test_the_wait_check_catches_a_render_before_an_unbounded_wait() -> None:
    script = (
        'generate --server "$SERVER"\n'
        'until curl -sf --max-time 5 "$SERVER/system_stats"; do sleep 5; done\n'
    )
    assert unawaited_endpoint(script) == [
        "asked before any render",
        "a stated bound",
        "gives up past it",
    ]


# The watchdog's check that its session still runs, and its exit once it does not.
ALIVE = "kill -0 $$ 2>/dev/null || exit 0"


def outliving_watchdog(script: str) -> list[str]:
    """Return what a render session's watchdog misses of ending with its session.

    e.g. a watchdog that sleeps the whole ceiling once -> ["polls its session", ...]
    """
    lines = _code(script)
    end = len(lines)
    loop = next(
        (i for i, ln in enumerate(lines) if ln.strip().startswith("while ")), end
    )
    done = next((i for i in range(loop, end) if lines[i].strip() == "done"), end)
    body = lines[loop:done]
    missing = []
    if not (any(ALIVE in ln for ln in body) and any("sleep 5" in ln for ln in body)):
        missing.append("polls its session")
    signal = next((i for i, ln in enumerate(lines) if "kill -TERM $$" in ln), None)
    checked = [i for i in range(done, end) if ALIVE in lines[i]]
    if signal is None or not checked or checked[0] > signal:
        missing.append("checks before it signals")
    return missing


@pytest.mark.spec("pod-image:session:the-watchdog-ends-with-its-session")
def test_the_watchdog_ends_with_its_session(render_sh: str) -> None:
    assert outliving_watchdog(render_sh) == []


@pytest.mark.spec_exempt("structural: twin of test_the_watchdog_ends_with_its_session")
def test_the_watchdog_check_catches_one_that_sleeps_the_ceiling() -> None:
    script = '(\n  sleep "$CEILING"\n  kill -TERM $$\n) &\n'
    assert outliving_watchdog(script) == [
        "polls its session",
        "checks before it signals",
    ]


def shared_host_keys(render_sh: str, down_sh: str) -> list[str]:
    """Return what a render session misses of tunnelling with the pod's checked key.

    e.g. a tunnel with `StrictHostKeyChecking=accept-new` -> ["strict checking", ...]
    """
    lines = _code(render_sh.replace("\\\n", " "))
    missing = []
    tunnel = [ln for ln in lines if ln.strip().startswith("ssh ") and "-L " in ln]
    if not tunnel or "UserKnownHostsFile=.runpod_known_hosts" not in tunnel[0]:
        missing.append("the tunnel names the pod's file")
    if not tunnel or "StrictHostKeyChecking=yes" not in tunnel[0]:
        missing.append("strict checking")
    if ".runpod_known_hosts" not in removed_on_204(down_sh):
        missing.append("removed at teardown")
    return missing


@pytest.mark.spec("pod-image:session:host-keys-are-the-sessions-own")
def test_a_sessions_host_keys_are_its_own(render_sh: str, down_sh: str) -> None:
    assert shared_host_keys(render_sh, down_sh) == []


@pytest.mark.spec_exempt("structural: twin of test_a_sessions_host_keys_are_its_own")
def test_the_host_key_check_catches_a_key_trusted_on_first_sight() -> None:
    render_sh = (
        "ssh -o StrictHostKeyChecking=accept-new \\\n"
        '  -o UserKnownHostsFile="$known_hosts" \\\n'
        '  -N -L 8188:localhost:8188 "root@$host" &\n'
    )
    down_sh = 'if [ "$code" = "204" ]; then\n  rm -f .runpod_pod_id .runpod_pod_image\n'
    assert shared_host_keys(render_sh, down_sh) == [
        "the tunnel names the pod's file",
        "strict checking",
        "removed at teardown",
    ]


def proxied_requests(script: str) -> list[str]:
    """Return every `curl` to the endpoint's address that would follow a proxy.

    e.g. `curl -sf "$SERVER/system_stats"` -> that line
    """
    return [
        ln.strip()
        for ln in _code(script)
        if "curl " in ln and '"$SERVER' in ln and "--noproxy '*'" not in ln
    ]


@pytest.mark.spec("pod-image:session:the-tunnel-is-reached-directly")
def test_the_session_reaches_its_tunnel_without_a_proxy(render_sh: str) -> None:
    assert any("curl " in ln and '"$SERVER' in ln for ln in _code(render_sh))
    assert proxied_requests(render_sh) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_session_reaches_its_tunnel_without_a_proxy"
)
def test_the_proxy_check_catches_a_curl_that_follows_one() -> None:
    script = 'until curl -sf --max-time 5 "$SERVER/system_stats"; do sleep 5; done\n'
    assert proxied_requests(script) == [script.strip()]


def run_functions(
    script: str,
    names: tuple[str, ...],
    stubs: str,
    cwd: Path,
    call: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run `call`, or the last named function, in strict bash beside the stubs.

    e.g. `call='f "a b"'` runs `f` with one argument.
    """
    program = "\n".join(
        [
            "set -euo pipefail",
            stubs,
            *(shell_function(script, n) for n in names),
            call or names[-1],
        ]
    )
    return subprocess.run(
        ["bash", "-c", program],
        cwd=cwd,
        env={"PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def volume_refusal(up_sh: str, answer: dict[str, object]) -> str:
    """Return what `check_volume` refuses with for this answer, or "" if it passes."""
    stubs = (
        "API=https://api.test\nRUNPOD_VOLUME_ID=vol-test\nRUNPOD_DATACENTER=EU-RO-1\n"
        f"api() {{ printf '%s\\n' {shlex.quote(json.dumps(answer))}; }}"
    )
    done = run_functions(up_sh, ("refuse", "check_volume"), stubs, REPO)
    return done.stderr.strip() if done.returncode else ""


BROKEN_VOLUME_CHECK = "refuse() { exit 1; }\ncheck_volume() {\n  :\n}\n"


def checked_before_create(up_sh: str) -> bool:
    """Whether `up.sh` checks the volume before its create call."""
    lines = up_sh.splitlines()
    checks = [i for i, ln in enumerate(lines) if ln.strip() == "check_volume"]
    creates = next(i for i, line in enumerate(lines) if 'POST "$API/pods"' in line)
    return bool(checks) and checks[0] < creates


@pytest.mark.spec("pod-image:volume:another-data-centre-is-refused")
def test_another_data_centre_is_refused(up_sh: str) -> None:
    refusal = volume_refusal(up_sh, {"dataCenter": "US-KS-2", "size": 100})
    assert refusal.startswith("refused: ")
    assert "EU-RO-1" in refusal and "US-KS-2" in refusal
    assert volume_refusal(up_sh, {"dataCenter": "EU-RO-1", "size": 100}) == ""
    assert checked_before_create(up_sh)


@pytest.mark.spec_exempt("structural: twin of test_another_data_centre_is_refused")
def test_the_data_centre_check_catches_a_volume_never_read() -> None:
    assert (
        volume_refusal(BROKEN_VOLUME_CHECK, {"dataCenter": "US-KS-2", "size": 100})
        == ""
    )
    assert not checked_before_create('out=$(api -X POST "$API/pods")\ncheck_volume\n')


@pytest.mark.spec("pod-image:volume:a-volume-too-small-is-refused")
def test_a_volume_too_small_is_refused(up_sh: str, manifest: Manifest) -> None:
    need = sum(entry["bytes"] for entry in manifest["entries"])
    refusal = volume_refusal(up_sh, {"dataCenter": "EU-RO-1", "size": 10})
    assert refusal.startswith("refused: ")
    assert "10 GB" in refusal and f"{need} bytes" in refusal
    assert checked_before_create(up_sh)


@pytest.mark.spec_exempt("structural: twin of test_a_volume_too_small_is_refused")
def test_the_size_check_catches_a_volume_never_read() -> None:
    assert (
        volume_refusal(BROKEN_VOLUME_CHECK, {"dataCenter": "EU-RO-1", "size": 10}) == ""
    )


TELEMETRY_SWITCHES = (
    "ORT_DISABLE_TELEMETRY",
    "HF_HUB_DISABLE_TELEMETRY",
    "DO_NOT_TRACK",
    "NO_ALBUMENTATIONS_UPDATE",
)


def telemetry_left_on(dockerfile: str, up_sh: str) -> list[str]:
    """Return each switch the image's `ENV` leaves off, and each `up.sh` sets again.

    A switch's last assignment is the one the image keeps, so a later `=0` turns it off.
    e.g. `up.sh` setting `DO_NOT_TRACK` -> [..., "up.sh: DO_NOT_TRACK"]
    """
    env = " ".join(line for line in joined_lines(dockerfile) if line.startswith("ENV "))
    last = dict(re.findall(r"\b(\w+)=(\S*)", env))
    left = [s for s in TELEMETRY_SWITCHES if last.get(s) != "1"]
    return left + [f"up.sh: {s}" for s in TELEMETRY_SWITCHES if s in up_sh]


@pytest.mark.spec("pod-image:telemetry:the-switches-are-off")
def test_the_pod_is_created_with_telemetry_off(dockerfile: str, up_sh: str) -> None:
    assert telemetry_left_on(dockerfile, up_sh) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_pod_is_created_with_telemetry_off"
)
def test_the_telemetry_check_catches_a_switch_left_out() -> None:
    dockerfile = (
        "# DO_NOT_TRACK=1\nENV ORT_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_TELEMETRY=10\n"
    )
    up_sh = 'env: { PUBLIC_KEY: $pubkey,\n  NO_ALBUMENTATIONS_UPDATE: "1" } }\n'
    assert telemetry_left_on(dockerfile, up_sh) == [
        "HF_HUB_DISABLE_TELEMETRY",
        "DO_NOT_TRACK",
        "NO_ALBUMENTATIONS_UPDATE",
        "up.sh: NO_ALBUMENTATIONS_UPDATE",
    ]


@pytest.mark.spec_exempt(
    "structural: twin of test_the_pod_is_created_with_telemetry_off"
)
def test_the_telemetry_check_catches_a_switch_set_back(dockerfile: str) -> None:
    set_back = dockerfile + "\nENV DO_NOT_TRACK=0\n"
    assert telemetry_left_on(set_back, "") == ["DO_NOT_TRACK"]


# A throwaway Ed25519 key made for these tests, and its fingerprint and another's.
HOST_KEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIM0fZgRnEY7GjNNDufoBjTKT9gPx9sN+vZmUWHVzN/Gn"
)
HOST_KEY_FINGERPRINT = "SHA256:rtGEsOEKPlWyEuNlB72E8dAPjGTYjbj3Dkf/rRhsz0U"
OTHER_FINGERPRINT = "SHA256:NNz7DVAOPM3aU8pc65cmp696rualwnvB7DaCYclXg64"
HOST_KEY_FUNCTIONS = (
    "refuse_and_tear_down",
    "printed_fingerprint",
    "scanned_key",
    "verify_host_key",
)
TORN_DOWN = "torn down: ./infra/down.sh"
RE_RUN = "the pod is torn down, and bash infra/up.sh boots a fresh one\n"


def check_host_key(
    up_sh: str,
    printed: str | None,
    cwd: Path,
    *,
    answers: bool = True,
    torn: bool = True,
) -> tuple[subprocess.CompletedProcess[str], str | None]:
    """Run `verify_host_key` against a pod log and a scan that answers `HOST_KEY`.

    Return the run and the known-hosts file it left, if any. `printed` is the
    fingerprint the log carries; None is a log that never prints one. With
    `answers` False, the scan never answers; with `torn` False, `down.sh` fails.
    """
    scan = f'echo "[$host]:$port {HOST_KEY}"' if answers else ":"
    lines = ["step: sshd"] + ([f"isekai host key: {printed}"] if printed else [])
    events = "".join(
        f"data: {json.dumps({'ts': '', 'source': 'container', 'line': ln})}\n"
        for ln in lines
    )
    stubs = "\n".join(
        [
            "API=https://api.test pod_id=pod-test since=2026-09-28T00:00:00Z",
            "host=203.0.113.7 port=40022",
            f"api() {{ printf '%s' {shlex.quote(events)}; }}",
            f"ssh-keyscan() {{ {scan}; }}",
            "sleep() { SECONDS=$((SECONDS + $1)); }",
            'bash() { echo "torn down: $*"; }'
            if torn
            else 'bash() { echo "delete failed: $*"; return 1; }',
        ]
    )
    done = run_functions(up_sh, HOST_KEY_FUNCTIONS, stubs, cwd)
    kept = cwd / ".runpod_known_hosts"
    return done, kept.read_text() if kept.exists() else None


def unchecked_connections(up_sh: str) -> list[str]:
    """Return each connection line `up.sh` prints that does not use the checked key."""
    lines = up_sh.splitlines()
    checked = next((i for i, ln in enumerate(lines) if ln == "verify_host_key"), None)
    return [
        ln.strip()
        for i, ln in enumerate(lines)
        if ln.startswith(('echo "  SSH:', 'echo "  Tunnel:'))
        and (
            checked is None
            or i < checked
            or "-o UserKnownHostsFile=.runpod_known_hosts" not in ln
            or "-o StrictHostKeyChecking=yes" not in ln
        )
    ]


BROKEN_HOST_KEY_CHECK = (
    "refuse_and_tear_down() { exit 1; }\n"
    "verify_host_key() {\n"
    '  echo "[$host]:$port $(ssh-keyscan)" > .runpod_known_hosts\n'
    "}\n"
)


@pytest.mark.spec("pod-image:host-key:a-matching-key-is-kept")
def test_a_matching_key_is_kept(
    up_sh: str, render_sh: str, down_sh: str, tmp_path: Path
) -> None:
    done, kept = check_host_key(up_sh, HOST_KEY_FINGERPRINT, tmp_path)
    assert done.returncode == 0, done.stderr
    assert kept == f"[203.0.113.7]:40022 {HOST_KEY}\n"
    assert f"Host key verified: {HOST_KEY_FINGERPRINT}" in done.stdout
    assert unchecked_connections(up_sh) == []
    assert "Tunnel:" in up_sh and "SSH:" in up_sh
    assert shared_host_keys(render_sh, down_sh) == []


@pytest.mark.spec_exempt("structural: twin of test_a_matching_key_is_kept")
def test_the_kept_key_check_catches_a_connection_before_the_check() -> None:
    up_sh = (
        'echo "  SSH:    ssh root@$host -p $port"\n'
        "verify_host_key\n"
        'echo "  Tunnel: ssh -o UserKnownHostsFile=.runpod_known_hosts'
        ' -o StrictHostKeyChecking=yes -N root@$host -p $port"\n'
    )
    assert unchecked_connections(up_sh) == ['echo "  SSH:    ssh root@$host -p $port"']


@pytest.mark.spec("pod-image:host-key:a-mismatch-is-refused")
def test_a_mismatch_is_refused(up_sh: str, tmp_path: Path) -> None:
    done, kept = check_host_key(up_sh, OTHER_FINGERPRINT, tmp_path)
    assert done.returncode == 1
    assert kept is None
    assert done.stderr.startswith(
        f"refused: the pod's host key {HOST_KEY_FINGERPRINT} does not match"
        f" the fingerprint it printed, {OTHER_FINGERPRINT}\n{TORN_DOWN}\n"
    )
    assert done.stderr.endswith(RE_RUN)
    assert "pod-test" not in done.stderr


@pytest.mark.spec_exempt("structural: twin of test_a_mismatch_is_refused")
def test_the_mismatch_check_catches_a_key_kept_unchecked(tmp_path: Path) -> None:
    done, kept = check_host_key(BROKEN_HOST_KEY_CHECK, OTHER_FINGERPRINT, tmp_path)
    assert done.returncode == 0
    assert kept is not None
    assert TORN_DOWN not in done.stderr


@pytest.mark.spec("pod-image:host-key:a-mismatch-is-refused")
def test_a_scan_no_one_answers_is_refused_as_such(up_sh: str, tmp_path: Path) -> None:
    done, kept = check_host_key(up_sh, HOST_KEY_FINGERPRINT, tmp_path, answers=False)
    assert done.returncode == 1
    assert kept is None
    assert done.stderr.startswith(
        f"refused: the pod's SSH answered no host-key scan within 180 s\n{TORN_DOWN}\n"
    )
    assert "does not match" not in done.stderr
    assert done.stderr.endswith(RE_RUN)


@pytest.mark.spec("pod-image:host-key:a-mismatch-is-refused")
@pytest.mark.parametrize(
    ("printed", "answers"),
    [(OTHER_FINGERPRINT, True), (HOST_KEY_FINGERPRINT, False)],
    ids=["mismatch", "no-scan"],
)
def test_a_failed_teardown_claims_none_and_names_no_re_run(
    up_sh: str, tmp_path: Path, printed: str, answers: bool
) -> None:
    done, kept = check_host_key(up_sh, printed, tmp_path, answers=answers, torn=False)
    assert done.returncode == 1
    assert kept is None
    assert done.stderr.endswith("delete failed: ./infra/down.sh\n")
    assert "torn down" not in done.stderr
    assert "bash infra/up.sh" not in done.stderr


@pytest.mark.spec_exempt(
    "structural: twin of test_a_scan_no_one_answers_is_refused_as_such"
)
def test_the_scan_check_catches_a_key_kept_with_none_scanned(tmp_path: Path) -> None:
    done, kept = check_host_key(
        BROKEN_HOST_KEY_CHECK, HOST_KEY_FINGERPRINT, tmp_path, answers=False
    )
    assert done.returncode == 0
    assert kept is not None
    assert TORN_DOWN not in done.stderr


@pytest.mark.spec("pod-image:host-key:no-fingerprint-is-refused")
def test_no_fingerprint_is_refused(up_sh: str, tmp_path: Path) -> None:
    done, kept = check_host_key(up_sh, None, tmp_path)
    assert done.returncode == 1
    assert kept is None
    assert done.stderr.startswith(
        "refused: the pod printed no host-key fingerprint within 60 s;"
    )
    assert "stream-pod-logs" in done.stderr
    assert TORN_DOWN in done.stderr
    assert "pod-test" not in done.stderr


@pytest.mark.spec_exempt("structural: twin of test_no_fingerprint_is_refused")
def test_the_fingerprint_check_catches_a_key_kept_with_none_printed(
    tmp_path: Path,
) -> None:
    done, kept = check_host_key(BROKEN_HOST_KEY_CHECK, None, tmp_path)
    assert done.returncode == 0
    assert kept is not None
    assert TORN_DOWN not in done.stderr


@pytest.fixture(scope="session")
def pods_sh() -> str:
    """Read the shipped `infra/pods.sh` once for the whole session."""
    return (REPO / "infra" / "pods.sh").read_text()


def create_body(up_sh: str) -> dict[str, object]:
    """Return the create request `up.sh` builds for a card named `card`."""
    lines = up_sh.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip() == "body=$(jq -n \\")
    end = next(i for i in range(start, len(lines)) if lines[i].endswith("')"))
    floors = [ln for ln in lines if re.match(r"(RAM_FLOOR_GB|CUDA_FLOOR)=", ln)]
    program = "\n".join(
        [
            "image_ref=img gpu=card RUNPOD_VOLUME_ID=vol RUNPOD_DATACENTER=dc",
            "PUBKEY=key",
            *floors,
            *lines[start : end + 1],
            'printf "%s" "$body"',
        ]
    )
    done = subprocess.run(
        ["bash", "-c", program], capture_output=True, text=True, timeout=30, check=True
    )
    return json.loads(done.stdout)


def unfloored_create(up_sh: str) -> list[str]:
    """Return each floor the create request does not carry.

    e.g. a body with `gpu: { id: $gpu, count: 1 }` -> ["host memory", "CUDA version"]
    """
    gpu = create_body(up_sh)["gpu"]
    assert isinstance(gpu, dict)
    missing = []
    ram = gpu.get("minRamPerGpu")
    if not (isinstance(ram, int) and ram >= 24):
        missing.append("host memory")
    # torch's cu128 build, which the Blackwell pod needs (CLAUDE.md).
    if gpu.get("minCudaVersion") != "12.8":
        missing.append("CUDA version")
    return missing


@pytest.mark.spec("pod-image:placement:the-create-carries-the-floors")
def test_the_create_carries_the_floors(up_sh: str) -> None:
    assert unfloored_create(up_sh) == []


@pytest.mark.spec_exempt("structural: twin of test_the_create_carries_the_floors")
def test_the_floor_check_catches_a_create_with_none() -> None:
    up_sh = (
        "  body=$(jq -n \\\n"
        '    --arg gpu    "$gpu" \\\n'
        "    '{ gpu: { id: $gpu, count: 1 } }')\n"
    )
    assert unfloored_create(up_sh) == ["host memory", "CUDA version"]


# RunPod's catalogue, as `placeable_gpus` reads it: a card's VRAM, or a 404.
CATALOGUE_STUBS = "\n".join(
    [
        "API=https://api.test VRAM_FLOOR_GB=24",
        "api() {",
        '  case "${@: -1}" in',
        "    */RTX%204090) printf '{\"memory\":24}\\n200' ;;",
        "    */RTX%20A4000) printf '{\"memory\":16}\\n200' ;;",
        '    *) printf \'{"title":"Not Found"}\\n404\' ;;',
        "  esac",
        "}",
    ]
)
BROKEN_PLACEMENT = 'refuse() { exit 1; }\nplaceable_gpus() {\n  echo "$1"\n}\n'


def placement(up_sh: str, cards: str) -> subprocess.CompletedProcess[str]:
    """Run `placeable_gpus` over `cards`, one per line, against the catalogue stub."""
    return run_functions(
        up_sh,
        ("refuse", "placeable_gpus"),
        CATALOGUE_STUBS,
        REPO,
        call=f"placeable_gpus {shlex.quote(cards)}",
    )


def placed_before_create(up_sh: str) -> bool:
    """Whether `up.sh` reads the catalogue before its create call."""
    lines = up_sh.splitlines()
    placed = [i for i, ln in enumerate(lines) if ln.startswith("gpus=$(placeable_gpus")]
    creates = next(i for i, line in enumerate(lines) if 'POST "$API/pods"' in line)
    return bool(placed) and placed[0] < creates


@pytest.mark.spec("pod-image:placement:a-card-short-of-memory-is-skipped")
def test_a_card_short_of_memory_is_skipped(up_sh: str) -> None:
    done = placement(up_sh, "RTX A4000\nRTX 4090")
    assert done.returncode == 0, done.stderr
    assert done.stdout == "RTX 4090\n"
    assert done.stderr == "skipped: RTX A4000 has 16 GB, below 24\n"
    assert placed_before_create(up_sh)


@pytest.mark.spec_exempt("structural: twin of test_a_card_short_of_memory_is_skipped")
def test_the_skip_check_catches_a_card_never_read() -> None:
    done = placement(BROKEN_PLACEMENT, "RTX A4000\nRTX 4090")
    assert done.stdout == "RTX A4000\nRTX 4090\n"
    assert not placed_before_create('out=$(api -X POST "$API/pods")\n')


@pytest.mark.spec("pod-image:placement:an-unknown-card-is-refused")
def test_an_unknown_card_is_refused(up_sh: str) -> None:
    done = placement(up_sh, "RTX 4090\nRTX 4O90")
    assert done.returncode == 1
    assert done.stderr == (
        "refused: RUNPOD_GPU_TYPE names RTX 4O90, which RunPod does not know;"
        " fix .env\n"
    )
    assert placed_before_create(up_sh)


@pytest.mark.spec_exempt("structural: twin of test_an_unknown_card_is_refused")
def test_the_unknown_card_check_catches_a_card_passed_through() -> None:
    assert placement(BROKEN_PLACEMENT, "RTX 4090\nRTX 4O90").returncode == 0


IMAGE_NAME = json.loads(IMAGE_CONFIG.read_text())["image"]


def listed_pod(pod_id: str, status: str, name: str = "isekai") -> dict[str, str]:
    """Return a pod as RunPod's v2 list gives it, booted from this project's image."""
    return {
        "id": pod_id,
        "name": name,
        "image": f"{IMAGE_NAME}@sha256:0",
        "status": status,
    }


def pod_pages(first: list[dict[str, str]], second: list[dict[str, str]]) -> list[str]:
    """Return a two-page v2 listing, the first page naming a cursor to the second."""
    return [
        json.dumps(
            {"pods": first, "pagination": {"nextCursor": "p2", "hasNextPage": True}}
        ),
        json.dumps(
            {"pods": second, "pagination": {"nextCursor": None, "hasNextPage": False}}
        ),
    ]


def pod_check(
    script: str, cwd: Path, pages: list[str] | None
) -> tuple[subprocess.CompletedProcess[str], bool]:
    """Run `check_no_pod` against `pages`; None is a listing that fails.

    Return the run and whether it called RunPod at all.
    """
    (cwd / "config").mkdir(exist_ok=True)
    (cwd / "config" / "image.json").write_text(IMAGE_CONFIG.read_text())
    first, second = pages or ["", ""]
    listing = (
        "return 22"
        if pages is None
        else f'case "$*" in *cursor=*) printf "%s" {shlex.quote(second)} ;;'
        f' *) printf "%s" {shlex.quote(first)} ;; esac'
    )
    stubs = f"API=https://api.test\napi() {{ touch called; {listing}; }}"
    done = run_functions(script, ("refuse", "isekai_pods", "check_no_pod"), stubs, cwd)
    return done, (cwd / "called").exists()


def checked_before_volume(up_sh: str) -> bool:
    """Whether `up.sh` looks for another pod before the volume check and the create."""
    lines = up_sh.splitlines()
    checks = [i for i, ln in enumerate(lines) if ln == "check_no_pod"]
    volume = next((i for i, ln in enumerate(lines) if ln == "check_volume"), None)
    return bool(checks) and volume is not None and checks[0] < volume


BROKEN_POD_CHECK = "refuse() { exit 1; }\ncheck_no_pod() {\n  :\n}\n"
RECORD_ONLY_POD_CHECK = (
    "refuse() { exit 1; }\ncheck_no_pod() {\n  [ ! -f .runpod_pod_id ] || refuse\n}\n"
)


@pytest.mark.spec("pod-image:reconcile:a-recorded-pod-refuses")
def test_a_recorded_pod_refuses_a_creation(
    up_sh: str, pods_sh: str, tmp_path: Path
) -> None:
    (tmp_path / ".runpod_pod_id").write_text("pod-a\n")
    done, called = pod_check(up_sh + pods_sh, tmp_path, pod_pages([], []))
    assert done.returncode == 1
    assert done.stderr == (
        "refused: a pod is already recorded in .runpod_pod_id; run bash infra/down.sh\n"
    )
    assert not called
    assert checked_before_volume(up_sh)


@pytest.mark.spec_exempt("structural: twin of test_a_recorded_pod_refuses_a_creation")
def test_the_record_check_catches_a_record_never_read(tmp_path: Path) -> None:
    (tmp_path / ".runpod_pod_id").write_text("pod-a\n")
    done, _ = pod_check(BROKEN_POD_CHECK, tmp_path, pod_pages([], []))
    assert done.returncode == 0
    assert not checked_before_volume("check_volume\ncheck_no_pod\n")


@pytest.mark.spec("pod-image:reconcile:a-listed-pod-refuses")
def test_a_listed_pod_refuses_a_creation(
    up_sh: str, pods_sh: str, tmp_path: Path
) -> None:
    script = up_sh + pods_sh
    others = [
        listed_pod("pod-x", "RUNNING", name="other"),
        listed_pod("pod-t", "TERMINATED"),
    ]
    done, _ = pod_check(
        script, tmp_path, pod_pages(others, [listed_pod("pod-b", "EXITED")])
    )
    assert done.returncode == 1
    assert done.stderr == (
        "refused: an 'isekai' pod already exists: pod-b (EXITED);"
        " run bash infra/down.sh\n"
    )
    done, _ = pod_check(script, tmp_path, pod_pages(others, []))
    assert done.returncode == 0, done.stderr
    done, _ = pod_check(script, tmp_path, None)
    assert done.returncode == 1
    assert "list-pods" in done.stderr
    assert checked_before_volume(up_sh)


@pytest.mark.spec_exempt("structural: twin of test_a_listed_pod_refuses_a_creation")
def test_the_listing_check_catches_a_pod_never_listed(tmp_path: Path) -> None:
    pages = pod_pages([], [listed_pod("pod-b", "EXITED")])
    done, _ = pod_check(RECORD_ONLY_POD_CHECK, tmp_path, pages)
    assert done.returncode == 0


# RunPod's API as down.sh reaches it through curl: pages from files, deletes logged.
FAKE_CURL = """#!/usr/bin/env bash
url="${@: -1}"
case " $* " in
  *" -X DELETE "*)
    echo "${url##*/}" >> "$FAKE/deleted"
    if grep -qx "${url##*/}" "$FAKE/refused" 2>/dev/null; then
      printf '{}\\n500'
    else
      printf '\\n204'
    fi ;;
  *)
    [ -f "$FAKE/page1" ] || exit 22
    case "$url" in *cursor=*) cat "$FAKE/page2" ;; *) cat "$FAKE/page1" ;; esac ;;
esac
"""


def tear_down(
    down_sh: str,
    pods_sh: str,
    root: Path,
    *,
    recorded: str | None,
    pages: list[str] | None,
    refused: tuple[str, ...] = (),
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    """Run `down.sh` in a copy of the repository against a fake RunPod.

    Return the run and the pod ids it deleted, in order. `pages` None is a
    listing that fails; `refused` pods answer a delete with 500.
    """
    (root / "infra").mkdir(parents=True)
    (root / "infra" / "down.sh").write_text(down_sh)
    (root / "infra" / "pods.sh").write_text(pods_sh)
    (root / "config").mkdir()
    (root / "config" / "image.json").write_text(IMAGE_CONFIG.read_text())
    (root / ".env").write_text("RUNPOD_API_KEY=test-key\n")
    if recorded:
        (root / ".runpod_pod_id").write_text(f"{recorded}\n")
    fake = root / "fake"
    fake.mkdir()
    for n, page in enumerate(pages or [], start=1):
        (fake / f"page{n}").write_text(page)
    (fake / "refused").write_text("".join(f"{p}\n" for p in refused))
    bin_dir = root / "bin"
    bin_dir.mkdir()
    (bin_dir / "curl").write_text(FAKE_CURL)
    (bin_dir / "curl").chmod(0o755)
    done = subprocess.run(
        ["bash", "infra/down.sh"],
        cwd=root,
        env={"PATH": f"{bin_dir}:{os.environ['PATH']}", "FAKE": str(fake)},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    deleted = fake / "deleted"
    return done, deleted.read_text().split() if deleted.exists() else []


RECORD_ONLY_DOWN = """#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .runpod_pod_id ] || exit 0
curl -s --max-time 30 -w '\\n%{http_code}' -X DELETE \\
  "https://api.test/pods/$(cat .runpod_pod_id)"
"""


@pytest.mark.spec("pod-image:reconcile:the-teardown-leaves-none")
def test_the_teardown_leaves_no_pod(down_sh: str, pods_sh: str, tmp_path: Path) -> None:
    pages = pod_pages(
        [listed_pod("pod-a", "RUNNING"), listed_pod("pod-x", "RUNNING", name="other")],
        [listed_pod("pod-b", "EXITED")],
    )
    done, deleted = tear_down(
        down_sh, pods_sh, tmp_path / "rec", recorded="pod-a", pages=pages
    )
    assert done.returncode == 0, done.stderr
    assert deleted == ["pod-a", "pod-b"]
    assert "Removed pod-b (EXITED)." in done.stdout
    assert not (tmp_path / "rec" / ".runpod_pod_id").exists()

    done, deleted = tear_down(
        down_sh, pods_sh, tmp_path / "bare", recorded=None, pages=pages
    )
    assert done.returncode == 0, done.stderr
    assert deleted == ["pod-a", "pod-b"]

    empty = pod_pages([], [])
    done, deleted = tear_down(
        down_sh, pods_sh, tmp_path / "none", recorded=None, pages=empty
    )
    assert (done.returncode, deleted, done.stdout) == (0, [], "No pod to tear down.\n")

    done, deleted = tear_down(
        down_sh,
        pods_sh,
        tmp_path / "held",
        recorded=None,
        pages=pages,
        refused=("pod-a",),
    )
    assert done.returncode == 1
    assert deleted == ["pod-a", "pod-b"]

    done, deleted = tear_down(
        down_sh, pods_sh, tmp_path / "blind", recorded="pod-a", pages=None
    )
    assert done.returncode == 1
    assert deleted == ["pod-a"]
    assert "list-pods" in done.stderr


@pytest.mark.spec_exempt("structural: twin of test_the_teardown_leaves_no_pod")
def test_the_teardown_check_catches_one_that_removes_the_record_alone(
    pods_sh: str, tmp_path: Path
) -> None:
    pages = pod_pages([listed_pod("pod-a", "RUNNING")], [listed_pod("pod-b", "EXITED")])
    _, deleted = tear_down(
        RECORD_ONLY_DOWN, pods_sh, tmp_path, recorded="pod-a", pages=pages
    )
    assert deleted == ["pod-a"]


def session_on_record(
    render_sh: str, root: Path
) -> tuple[subprocess.CompletedProcess[str], bool]:
    """Run a render session in a copy of the repository beside a recorded pod.

    Return the run and whether its teardown ran `down.sh`.
    """
    (root / "infra").mkdir(parents=True)
    (root / "infra" / "render.sh").write_text(render_sh)
    (root / "infra" / "down.sh").write_text('touch "$(dirname "$0")/../torn"\n')
    (root / ".runpod_pod_id").write_text("pod-a\n")
    run = root / ".data" / "b" / "runs" / "r1"
    run.mkdir(parents=True)
    (run / "run.json").write_text("{}")
    done = subprocess.run(
        ["bash", "infra/render.sh", ".data/b/runs", "summon-anime-wai=1"],
        cwd=root,
        env={"PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return done, (root / "torn").exists()


LATE_RECORD_CHECK = """#!/usr/bin/env bash
cd "$(dirname "$0")/.."
teardown() { bash ./infra/down.sh; }
trap teardown EXIT
[ ! -f .runpod_pod_id ] || { echo "refused: a pod is already recorded" >&2; exit 1; }
"""


@pytest.mark.spec("pod-image:reconcile:a-session-refuses-a-recorded-pod")
def test_a_session_refuses_a_recorded_pod(render_sh: str, tmp_path: Path) -> None:
    done, torn = session_on_record(render_sh, tmp_path)
    assert done.returncode == 1
    assert done.stderr == (
        "refused: a pod is already recorded in .runpod_pod_id;"
        " run bash infra/down.sh first\n"
    )
    assert not torn
    assert (tmp_path / ".runpod_pod_id").exists()


@pytest.mark.spec_exempt("structural: twin of test_a_session_refuses_a_recorded_pod")
def test_the_session_check_catches_a_record_read_after_the_trap(tmp_path: Path) -> None:
    done, torn = session_on_record(LATE_RECORD_CHECK, tmp_path)
    assert done.returncode == 1
    assert torn


TIMER = '( sleep "$POD_CEILING_SECONDS"; exec bash "$STOP_POD" ) &'


def unarmed_stop(start_sh: str, dockerfile: str) -> list[str]:
    """Return what `start.sh` lacks of a stop armed, in the background, at boot.

    e.g. a script whose first step is the SSH key -> ["armed first", ...]
    """
    faults = []
    steps = [ln for ln in start_sh.splitlines() if re.search(r'step: [^"]+"$', ln)]
    if not steps or not steps[0].endswith('step: the stop timer"'):
        faults.append("armed first")
    ceiling = re.search(r"^POD_CEILING_SECONDS=(\d+)$", start_sh, re.M)
    if ceiling is None or not 0 < int(ceiling[1]) <= SESSION_CEILING_SECONDS:
        faults.append("a ceiling within the session's")
    if TIMER not in start_sh.splitlines():
        faults.append("in the background")
    stop = re.search(r"^STOP_POD=(\S+)$", start_sh, re.M)
    if stop is None or image_copies(dockerfile).get(stop[1]) != "tools/stop_pod.sh":
        faults.append("a stop the image holds")
    return faults


@pytest.mark.spec("pod-image:stop:armed-at-boot")
def test_the_pod_arms_its_stop_first(start_sh: str, dockerfile: str) -> None:
    assert unarmed_stop(start_sh, dockerfile) == []


@pytest.mark.spec_exempt("structural: twin of test_the_pod_arms_its_stop_first")
def test_the_armed_stop_check_catches_a_late_foreground_timer(dockerfile: str) -> None:
    late = (
        'echo "$(date -u +%FT%TZ) step: the SSH key"\n'
        "POD_CEILING_SECONDS=3600\nSTOP_POD=/opt/isekai/stop.sh\n"
        'echo "$(date -u +%FT%TZ) step: the stop timer"\n'
        'sleep "$POD_CEILING_SECONDS"; bash "$STOP_POD"\n'
    )
    assert unarmed_stop(late, dockerfile) == [
        "armed first",
        "a ceiling within the session's",
        "in the background",
        "a stop the image holds",
    ]


def unstopped_holds(start_sh: str, tmp_path: Path) -> list[str]:
    """Return how `start.sh` holds without ending in the stop.

    Runs `hold` with `sleep` and the stop's `bash` stubbed; each line outside it
    that waits out `HOLD_SECONDS` is a hold that bypasses it.
    """
    body = shell_function(start_sh, "hold")
    faults = [
        f"holds outside hold(): {ln.strip()}"
        for ln in start_sh.replace(body, "").splitlines()
        if "HOLD_SECONDS" in ln
        and not ln.lstrip().startswith("#")
        and not ln.startswith("HOLD_SECONDS=")
    ]
    stubs = tmp_path / "bin"
    stubs.mkdir(exist_ok=True)
    (stubs / "bash").write_text('#!/bin/sh\necho "stopped $*"\n')
    (stubs / "bash").chmod(0o755)
    program = "\n".join(
        [
            "set -euo pipefail",
            "HOLD_SECONDS=900 STOP_POD=/opt/isekai/tools/stop_pod.sh",
            'sleep() { echo "slept $1"; }',
            body,
            'hold "ERROR: why"',
            "echo returned",
        ]
    )
    done = subprocess.run(
        ["/bin/bash", "-c", program],
        env={"PATH": f"{stubs}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if done.stdout != "slept 900\nstopped /opt/isekai/tools/stop_pod.sh\n":
        faults.append("hold() does not stop the pod once it has waited")
    if not done.stderr.startswith("ERROR: why\n"):
        faults.append("hold() does not say why")
    return faults


@pytest.mark.spec("pod-image:stop:a-hold-ends-in-the-stop")
def test_every_hold_ends_in_the_stop(start_sh: str, tmp_path: Path) -> None:
    assert unstopped_holds(start_sh, tmp_path) == []
    calls = [ln for ln in start_sh.splitlines() if ln.lstrip().startswith('hold "')]
    assert len(calls) >= 1


@pytest.mark.spec_exempt("structural: twin of test_every_hold_ends_in_the_stop")
def test_the_hold_check_catches_a_hold_that_exits(tmp_path: Path) -> None:
    exits = (
        "HOLD_SECONDS=900\n"
        'hold() {\n    printf "%s\\n" "$@" >&2\n    sleep "$HOLD_SECONDS"\n}\n'
        'if ! provision; then\n    exec sleep "$HOLD_SECONDS"\nfi\n'
    )
    assert unstopped_holds(exits, tmp_path) == [
        'holds outside hold(): exec sleep "$HOLD_SECONDS"',
        "hold() does not stop the pod once it has waited",
    ]


STOP_SH = (REPO / "tools" / "stop_pod.sh").read_text()
TRIED_ONCE = (
    "code=$(curl -s --max-time 30 -o /dev/null -w '%{http_code}' -X POST"
    ' "$API/pods/$RUNPOD_POD_ID/action")\n'
    '[ "$code" = "200" ]\n'
)


def stop_attempts(
    script: str, codes: list[str], tmp_path: Path
) -> tuple[int, list[str], list[str]]:
    """Run the stop script against RunPod answering `codes`, one per attempt.

    Return its exit code, each attempt's curl arguments, and each wait between them.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "codes").write_text("".join(f"{c}\n" for c in codes))
    stubs = "\n".join(
        [
            "export RUNPOD_API_KEY=test-key RUNPOD_POD_ID=pod-test",
            'curl() { echo "$*" >> attempts;'
            ' sed -n "$(wc -l < attempts | tr -d " ")p" codes; }',
            'sleep() { echo "$1" >> slept; SECONDS=$((SECONDS + $1)); }',
        ]
    )
    done = subprocess.run(
        ["bash", "-c", f"{stubs}\n{script}"],
        cwd=tmp_path,
        env={"PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    def read(name: str) -> list[str]:
        path = tmp_path / name
        return path.read_text().splitlines() if path.exists() else []

    return done.returncode, read("attempts"), read("slept")


@pytest.mark.spec("pod-image:stop:a-failed-stop-is-retried")
def test_a_failed_stop_is_retried_then_given_up(tmp_path: Path) -> None:
    code, attempts, slept = stop_attempts(
        STOP_SH, ["500", "000", "200"], tmp_path / "ok"
    )
    assert (code, len(attempts), slept) == (0, 3, ["30", "30"])
    for attempt in attempts:
        assert (
            '-d {"action":"stop"} https://api.runpod.io/v2/pods/pod-test/action'
            in attempt
        )
    code, attempts, slept = stop_attempts(STOP_SH, ["500"] * 20, tmp_path / "down")
    assert code == 1
    # tried every 30 s until 300 s had passed
    assert (len(attempts), slept) == (11, ["30"] * 10)


@pytest.mark.spec_exempt(
    "structural: twin of test_a_failed_stop_is_retried_then_given_up"
)
def test_the_retry_check_catches_a_stop_tried_once(tmp_path: Path) -> None:
    code, attempts, slept = stop_attempts(TRIED_ONCE, ["500", "200"], tmp_path)
    assert (code, len(attempts), slept) == (1, 1, [])


def key_left_for_comfyui(start_sh: str) -> list[str]:
    """Return how the key could still reach ComfyUI, or be gone before the timer."""
    lines = before_serve(start_sh).splitlines()
    unset = [i for i, ln in enumerate(lines) if ln == "unset RUNPOD_API_KEY"]
    if not unset:
        return ["never unset"]
    faults = []
    timer = next((i for i, ln in enumerate(lines) if ln == TIMER), None)
    if timer is None or unset[0] < timer:
        faults.append("unset before the timer forks")
    if any("RUNPOD_API_KEY=" in ln for ln in lines[unset[-1] :]):
        faults.append("set again before ComfyUI")
    return faults


@pytest.mark.spec("pod-image:stop:comfyui-holds-no-key")
def test_comfyui_starts_without_the_key(start_sh: str) -> None:
    assert key_left_for_comfyui(start_sh) == []


@pytest.mark.spec_exempt("structural: twin of test_comfyui_starts_without_the_key")
def test_the_key_check_catches_a_key_kept_or_unset_too_early() -> None:
    serve = "exec python main.py\n"
    assert key_left_for_comfyui(f"{TIMER}\n{serve}") == ["never unset"]
    assert key_left_for_comfyui(f"unset RUNPOD_API_KEY\n{TIMER}\n{serve}") == [
        "unset before the timer forks"
    ]
