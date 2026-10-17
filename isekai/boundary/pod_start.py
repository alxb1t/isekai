"""Start the pod: check the volume, link the models, provision, prepare memory, serve.

The image's command, run by gpunit's boot script, which has armed the pod's stop and
started sshd, and stops the pod when this process ends, however it ends (D36).
ComfyUI replaces this process, so its exit is the boot's end.

Stdlib only, and run as a file rather than imported: the image holds this module and
`provision.py` beside it, not the package.
"""

import os
import shutil
import subprocess
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# The hold bills while it holds, so it is bounded: 900 s is ~$0.19 at the 4090 rate,
# inside the ~$0.30 per-session ceiling.
HOLD_SECONDS = 900

# A floor on total size, never on free space: it proves which disk this is (D27).
# It clears both wrong disks — the pod's 20 GB volume disk and its 30 GB container
# disk — while the network volume reports its cluster's capacity, far above both.
VOLUME_SIZE_FLOOR = 40 * 1024**3

# Below this much free memory ComfyUI would fail its first save mid-session.
SHM_FREE_FLOOR = 1024**3

# Where `fetch` lives in the image, beside this file.
PROVISION = Path(__file__).resolve().parent / "provision.py"


@dataclass(frozen=True)
class Pod:
    """Every path the start reads or writes, so a test can point them at a tree."""

    comfyui: Path = Path("/opt/ComfyUI")
    models_root: Path = Path("/opt/ComfyUI/models")
    # On container disk: the volume is exactly the thing that may have failed.
    marker: Path = Path("/opt/isekai/provisioning-failed")
    shm: Path = Path("/dev/shm")
    mountinfo: Path = Path("/proc/self/mountinfo")
    swaps: Path = Path("/proc/swaps")
    swap_max: Path = Path("/sys/fs/cgroup/memory.swap.max")

    @property
    def memory(self) -> Path:
        """Return the directory everything ComfyUI writes lives under."""
        return self.shm / "comfyui"


POD = Pod()


class Hold(Exception):
    """A step failed: its lines say why, and the pod holds rather than serve."""

    def __init__(self, *lines: str) -> None:
        """Keep the lines the hold prints."""
        super().__init__("\n".join(lines))
        self.lines = lines


def step(name: str) -> None:
    """Print the UTC time a step begins, so the log says where a boot's minutes go."""
    print(f"{datetime.now(UTC):%Y-%m-%dT%H:%M:%SZ} step: {name}", flush=True)


def hold(lines: tuple[str, ...]) -> int:
    """Say why, stay reachable over sshd for the window, then return the stop's code."""
    for line in lines:
        print(line, file=sys.stderr)
    print(
        f"Holding {HOLD_SECONDS}s, then stopping the pod.", file=sys.stderr, flush=True
    )
    time.sleep(HOLD_SECONDS)
    return 1


def check_volume(env: Mapping[str, str]) -> Path:
    """Return this project's namespace on the volume, once the volume is proven."""
    volume_id = env.get("GPUNIT_VOLUME_ID", "")
    volume = env.get("GPUNIT_VOLUME_PATH", "")
    if not volume_id or not volume:
        raise Hold(
            "ERROR: GPUNIT_VOLUME_ID or GPUNIT_VOLUME_PATH is empty — the pod was",
            "not told which network volume to expect. Refusing to provision.",
        )
    try:
        stats = os.statvfs(volume)
    except OSError as unread:
        raise Hold(
            f"ERROR: could not read the total size of {volume}: {unread}.",
            "Refusing to provision onto a volume that cannot be measured.",
        ) from unread
    size = stats.f_blocks * stats.f_frsize
    if size < VOLUME_SIZE_FLOOR:
        raise Hold(
            f"ERROR: measured {volume} at a total size of {size} B, below the",
            f"{VOLUME_SIZE_FLOOR} B floor — a disk that small is the pod's own",
            f"ephemeral storage, not network volume {volume_id}.",
            "Refusing to download the models onto storage that dies at teardown.",
        )
    return Path(volume) / "isekai"


def link_namespace(namespace: Path, models_root: Path) -> None:
    """Point ComfyUI's models root at the namespace, so every node resolves there.

    One link rather than one per folder: the InstantID node and the Impact Subpack
    ignore `extra_model_paths.yaml`. The tree replaced is the image's own; a
    non-empty tree mounted there is somebody's real models, and is refused.
    """
    namespace.mkdir(parents=True, exist_ok=True)
    if not models_root.is_symlink():
        if os.path.ismount(models_root) and any(models_root.iterdir()):
            raise Hold(
                f"ERROR: refusing to delete {models_root} — it is a non-empty",
                "mount, not the image's own models tree.",
            )
        if models_root.exists():
            shutil.rmtree(models_root)
        models_root.symlink_to(namespace)
    print(f"models namespace: {models_root} -> {os.readlink(models_root)}")


def provision(models_root: Path) -> None:
    """Land and verify every model the manifest declares, through `fetch`."""
    command = [
        sys.executable,
        str(PROVISION),
        "fetch",
        "--models-dir",
        str(models_root),
    ]
    returncode = subprocess.run(command, check=False).returncode
    if returncode != 0:
        raise Hold(f"ERROR: fetch exited {returncode}.")


def shm_type(pod: Pod) -> str | None:
    """Return the type of the mount the memory directory's device is, or None.

    e.g. "36 25 0:5 / /dev/shm rw - tmpfs tmpfs rw" on device 0:5 -> "tmpfs". The
    device, not the mount point's text, says which filesystem is under the directory;
    the last line wins, as a later mount shadows an earlier one.
    """
    try:
        lines = pod.mountinfo.read_text().splitlines()
        dev = os.stat(pod.memory).st_dev
    except OSError:
        return None
    wanted = f"{os.major(dev)}:{os.minor(dev)}"
    found = None
    for line in lines:
        fields = line.split()
        if len(fields) >= 3 and fields[2] == wanted and "-" in fields[3:]:
            after = fields[fields.index("-", 3) + 1 :]
            if after:
                found = after[0]
    return found


def can_swap(pod: Pod) -> bool | None:
    """Return whether the container can swap, or None when its swap table is unread.

    It can when a device is listed and swap is not capped at 0.
    """
    try:
        devices = pod.swaps.read_text().splitlines()[1:]
    except OSError:
        return None
    try:
        cap = pod.swap_max.read_text().strip()
    except OSError:
        cap = ""
    return any(line.strip() for line in devices) and cap != "0"


def prepare_memory(pod: Pod, env: dict[str, str]) -> None:
    """Make ComfyUI's directories in memory and point `TMPDIR` there, or hold.

    The container disk may outlive the pod unwiped; memory dies with it. An upload
    spools to `TMPDIR` first. The swap is the host's, so it is reported, never held
    for (D35).
    """
    for name in ("input", "output", "temp", "user", "tmp"):
        (pod.memory / name).mkdir(parents=True, exist_ok=True)
    env["TMPDIR"] = str(pod.memory / "tmp")
    kind = shm_type(pod)
    try:
        stats = os.statvfs(pod.shm)
        free: int | None = stats.f_bavail * stats.f_frsize
        size: int | None = stats.f_blocks * stats.f_frsize
    except OSError:
        free = size = None
    print(f"{pod.shm} is {kind}; size {size} B, free {free} B")
    swap = can_swap(pod)
    if swap is None:
        print("swap: could not read whether the container can swap")
    else:
        print(f"swap: the container {'can' if swap else 'cannot'} swap")
    if kind is None:
        raise Hold(
            f"ERROR: could not read {pod.shm}'s filesystem type.",
            "ComfyUI was not started.",
        )
    if kind != "tmpfs":
        raise Hold(
            f"ERROR: {pod.shm} is '{kind}', not a tmpfs —",
            "the photograph would reach a disk. ComfyUI was not started.",
        )
    if free is None:
        raise Hold(
            f"ERROR: could not read {pod.shm}'s free space.",
            "ComfyUI was not started.",
        )
    if free < SHM_FREE_FLOOR:
        raise Hold(
            f"ERROR: {pod.shm} has {free} B free, below the {SHM_FREE_FLOOR} B floor",
            "— too little memory to hold the photograph and its renders.",
            "ComfyUI was not started.",
        )


def serve(pod: Pod, env: dict[str, str]) -> None:
    """Replace this process with ComfyUI, writing only to memory and no metadata.

    ComfyUI puts its temp files in `temp` under the directory it is given.
    """
    memory = pod.memory
    os.chdir(pod.comfyui)
    os.execvpe(
        "python",
        [
            "python",
            "main.py",
            "--listen",
            "0.0.0.0",
            "--port",
            "8188",
            "--input-directory",
            str(memory / "input"),
            "--output-directory",
            str(memory / "output"),
            "--temp-directory",
            str(memory),
            "--user-directory",
            str(memory / "user"),
            "--disable-metadata",
        ],
        env,
    )


def main(env: Mapping[str, str] = os.environ, pod: Pod = POD) -> int:
    """Run every step in order; return 1 after a hold, and never return from a serve.

    A provisioning failure leaves its files for a human, so it holds the pod open,
    marked, rather than ending the boot before anyone can get in.
    """
    environment = dict(env)
    try:
        step("the volume")
        namespace = check_volume(environment)
        step("the namespace")
        link_namespace(namespace, pod.models_root)
        step("provisioning")
        provision(pod.models_root)
    except (Hold, OSError) as failed:
        pod.marker.parent.mkdir(parents=True, exist_ok=True)
        pod.marker.write_text(
            f"provisioning failed at {datetime.now(UTC):%Y-%m-%dT%H:%M:%SZ}\n"
        )
        lines = failed.lines if isinstance(failed, Hold) else (f"ERROR: {failed}",)
        return hold(
            (
                *lines,
                "ERROR: provisioning failed — holding the pod open for inspection.",
                f"Nothing was deleted. SSH in and look under {pod.models_root}.",
                f"Marker: {pod.marker}",
            )
        )
    try:
        step("the memory")
        prepare_memory(pod, environment)
    except Hold as failed:
        return hold(failed.lines)
    step("ComfyUI")
    serve(pod, environment)
    return 0


if __name__ == "__main__":
    sys.exit(main())
