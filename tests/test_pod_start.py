import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from isekai.boundary import pod_start
from isekai.boundary.pod_start import (
    HOLD_SECONDS,
    PROVISION,
    SHM_FREE_FLOOR,
    VOLUME_SIZE_FLOOR,
    Pod,
)
from isekai.boundary.provision import MODELS_ROOT

REPO = Path(__file__).resolve().parent.parent
SESSION_CEILING_SECONDS = 45 * 60
STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z step: (.+)$")
STEPS = ["the volume", "the namespace", "provisioning", "the memory", "ComfyUI"]


@dataclass
class Exec:
    """One `os.execvpe`, with the directories that existed when it ran."""

    file: str
    argv: list[str]
    env: dict[str, str]
    existing: set[str]


class Boot:
    """A pod start against a temporary tree, every effect replaced and recorded."""

    def __init__(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        comfyui = tmp_path / "ComfyUI"
        # the image's own tree, which the ComfyUI clone fills with configs
        (comfyui / "models" / "configs").mkdir(parents=True)
        (comfyui / "models" / "configs" / "v1.yaml").write_text("image's own\n")
        shm = tmp_path / "shm"
        shm.mkdir()
        self.pod = Pod(
            comfyui=comfyui,
            models_root=comfyui / "models",
            marker=tmp_path / "opt" / "provisioning-failed",
            shm=shm,
            mounts=tmp_path / "mounts",
            swaps=tmp_path / "swaps",
            swap_max=tmp_path / "memory.swap.max",
        )
        self.pod.mounts.write_text(
            f"overlay / overlay rw 0 0\ntmpfs {shm} tmpfs rw 0 0\n"
        )
        self.pod.swaps.write_text("Filename Type Size Used Priority\n")
        self.pod.swap_max.write_text("max\n")
        self.volume = tmp_path / "volume"
        self.volume.mkdir()
        self.env = {
            "GPUNIT_VOLUME_ID": "vol",
            "GPUNIT_VOLUME_PATH": str(self.volume),
            "PATH": "/usr/bin",
        }
        # path -> (total, free) in bytes; None reads as an unreadable figure
        self.figures: dict[str, tuple[int, int] | None] = {
            str(self.volume): (VOLUME_SIZE_FLOOR * 2, VOLUME_SIZE_FLOOR),
            str(shm): (SHM_FREE_FLOOR * 8, SHM_FREE_FLOOR * 8),
        }
        self.fetch_code = 0
        self.ran: list[list[str]] = []
        self.slept: list[float] = []
        self.execs: list[Exec] = []
        # what was printed before each effect, in order: (effect, stdout so far)
        self.events: list[tuple[str, str]] = []
        self._capsys = capsys
        self.out = ""
        self.err = ""
        monkeypatch.setattr(os, "statvfs", self._statvfs)
        monkeypatch.setattr(os, "execvpe", self._execvpe)
        monkeypatch.setattr(os, "chdir", lambda path: None)
        monkeypatch.setattr(time, "sleep", self._sleep)
        monkeypatch.setattr(subprocess, "run", self._run)

    def _note(self, effect: str) -> None:
        captured = self._capsys.readouterr()
        self.out += captured.out
        self.err += captured.err
        self.events.append((effect, self.out))

    def _statvfs(self, path: str | Path) -> SimpleNamespace:
        self._note(f"statvfs {path}")
        figure = self.figures[str(path)]
        if figure is None:
            raise OSError(f"cannot stat {path}")
        total, free = figure
        return SimpleNamespace(f_blocks=total, f_frsize=1, f_bavail=free)

    def _execvpe(self, file: str, argv: list[str], env: dict[str, str]) -> None:
        self._note("exec")
        existing = {arg for arg in [*argv, *env.values()] if Path(arg).is_dir()}
        self.execs.append(Exec(file, list(argv), dict(env), existing))

    def _sleep(self, seconds: float) -> None:
        self._note("sleep")
        self.slept.append(seconds)

    def _run(self, command: list[str], check: bool) -> SimpleNamespace:
        self._note("fetch")
        self.ran.append(command)
        return SimpleNamespace(returncode=self.fetch_code)

    def start(self) -> int:
        """Run the start and return its exit code, with all it printed collected."""
        code = pod_start.main(self.env, self.pod)
        self._note("end")
        return code

    def before(self, effect: str) -> str:
        """Return the last line printed before the first effect named `effect`."""
        out = next(text for name, text in self.events if name.startswith(effect))
        return out.splitlines()[-1]


@pytest.fixture
def boot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> Boot:
    return Boot(tmp_path, monkeypatch, capsys)


def held(boot: Boot) -> bool:
    """Return whether the start held: it slept the window and served nothing."""
    return boot.slept == [HOLD_SECONDS] and boot.execs == []


def flag(argv: list[str], name: str) -> str:
    """Return the value following `name` in an argument list."""
    return argv[argv.index(name) + 1]


# --- the memory ---------------------------------------------------------------


@pytest.mark.spec("pod-image:memory:comfyui-writes-to-memory")
def test_comfyui_writes_to_memory(boot: Boot) -> None:
    boot.start()
    (served,) = boot.execs
    memory = boot.pod.shm / "comfyui"
    flags = {
        "--input-directory": memory / "input",
        "--output-directory": memory / "output",
        "--temp-directory": memory,
        "--user-directory": memory / "user",
    }
    for name, path in flags.items():
        assert flag(served.argv, name) == str(path)
        assert str(path) in served.existing


@pytest.mark.spec("pod-image:memory:too-little-memory-holds")
def test_too_little_memory_holds_the_pod(boot: Boot) -> None:
    boot.figures[str(boot.pod.shm)] = (SHM_FREE_FLOOR * 8, SHM_FREE_FLOOR - 1)
    assert boot.start() == 1
    assert held(boot)
    assert f"{SHM_FREE_FLOOR - 1} B free" in boot.err


@pytest.mark.spec("pod-image:memory:too-little-memory-holds")
def test_memory_at_the_floor_is_enough(boot: Boot) -> None:
    boot.figures[str(boot.pod.shm)] = (SHM_FREE_FLOOR * 8, SHM_FREE_FLOOR)
    boot.start()
    assert len(boot.execs) == 1


@pytest.mark.spec("pod-image:memory:uploads-spool-to-memory")
def test_comfyui_spools_uploads_to_memory(boot: Boot) -> None:
    boot.start()
    (served,) = boot.execs
    spool = str(boot.pod.shm / "comfyui" / "tmp")
    assert served.env["TMPDIR"] == spool
    assert spool in served.existing


@pytest.mark.spec("pod-image:memory:a-disk-backed-shm-holds")
def test_a_shm_that_is_not_memory_holds_the_pod(boot: Boot) -> None:
    boot.pod.mounts.write_text(f"/dev/sda1 {boot.pod.shm} ext4 rw 0 0\n")
    assert boot.start() == 1
    assert held(boot)
    assert "'ext4', not a tmpfs" in boot.err


@pytest.mark.spec("pod-image:memory:a-disk-backed-shm-holds")
def test_a_later_mount_shadows_an_earlier_one(boot: Boot) -> None:
    shm = boot.pod.shm
    boot.pod.mounts.write_text(
        f"tmpfs {shm} tmpfs rw 0 0\n/dev/sda1 {shm} ext4 rw 0 0\n"
    )
    assert boot.start() == 1
    assert held(boot)


@pytest.mark.spec("pod-image:memory:an-unread-figure-holds")
def test_an_unread_figure_holds_the_pod(boot: Boot) -> None:
    boot.figures[str(boot.pod.shm)] = None
    assert boot.start() == 1
    assert held(boot)
    assert "could not read" in boot.err
    assert "free space" in boot.err


@pytest.mark.spec("pod-image:memory:an-unread-type-holds")
def test_no_line_for_the_memory_mount_holds_the_pod(boot: Boot) -> None:
    boot.pod.mounts.write_text("overlay / overlay rw 0 0\n")
    assert boot.start() == 1
    assert held(boot)
    assert "could not read" in boot.err
    assert "filesystem type" in boot.err


@pytest.mark.spec("pod-image:memory:an-unread-type-holds")
def test_an_unreadable_mount_table_holds_the_pod(boot: Boot) -> None:
    boot.pod.mounts.unlink()
    assert boot.start() == 1
    assert held(boot)
    assert "filesystem type" in boot.err


@pytest.mark.spec("pod-image:memory:swap-is-reported")
@pytest.mark.parametrize(
    ("devices", "cap", "reading"),
    [
        ("/swapfile file 8388604 0 -2\n", "max\n", "can swap"),
        ("", "max\n", "cannot swap"),
        ("/swapfile file 8388604 0 -2\n", "0\n", "cannot swap"),
    ],
)
def test_swap_is_reported_and_never_held_for(
    boot: Boot, devices: str, cap: str, reading: str
) -> None:
    boot.pod.swaps.write_text(f"Filename Type Size Used Priority\n{devices}")
    boot.pod.swap_max.write_text(cap)
    boot.start()
    assert f"swap: the container {reading}" in boot.out
    assert len(boot.execs) == 1


# --- metadata, steps and the end ----------------------------------------------


@pytest.mark.spec("pod-image:render-metadata:none-is-written")
def test_comfyui_writes_no_metadata(boot: Boot) -> None:
    boot.start()
    (served,) = boot.execs
    assert served.file == "python"
    assert served.argv[:2] == ["python", "main.py"]
    assert "--disable-metadata" in served.argv


@pytest.mark.spec("pod-image:boot:each-step-is-timestamped")
def test_each_boot_step_prints_a_utc_time_before_it_begins(boot: Boot) -> None:
    boot.start()
    steps = [m.group(1) for line in boot.out.splitlines() if (m := STAMP.match(line))]
    assert steps == STEPS
    assert boot.before(f"statvfs {boot.volume}").endswith("step: the volume")
    assert boot.before("fetch").endswith("step: provisioning")
    assert boot.before("exec").endswith("step: ComfyUI")


@pytest.mark.spec("pod-image:stop:a-hold-ends-in-the-stop")
def test_a_memory_hold_exits_non_zero_after_its_window(boot: Boot) -> None:
    boot.figures[str(boot.pod.shm)] = None
    assert boot.start() == 1
    assert boot.slept == [HOLD_SECONDS]
    assert boot.events[-2][0] == "sleep"


@pytest.mark.spec("pod-image:stop:a-hold-ends-in-the-stop")
def test_a_provisioning_hold_exits_non_zero_after_its_window(boot: Boot) -> None:
    boot.fetch_code = 1
    assert boot.start() == 1
    assert boot.slept == [HOLD_SECONDS]


@pytest.mark.spec("pod-image:stop:a-boot-that-ends-stops-the-pod")
def test_a_clean_boot_ends_by_becoming_comfyui(boot: Boot) -> None:
    boot.start()
    assert len(boot.execs) == 1
    assert boot.slept == []
    assert [name for name, _ in boot.events][-2:] == ["exec", "end"]


@pytest.mark.spec("pod-image:stop:a-boot-that-ends-stops-the-pod")
def test_the_file_hands_mains_code_to_the_exit() -> None:
    source = Path(pod_start.__file__).read_text()
    assert source.rstrip().endswith('if __name__ == "__main__":\n    sys.exit(main())')


# --- provisioning -------------------------------------------------------------


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_the_models_root_becomes_a_link_onto_the_project_namespace(boot: Boot) -> None:
    boot.start()
    root = boot.pod.models_root
    assert root.is_symlink()
    assert root.readlink() == boot.volume / "isekai"
    # the image's own tree is gone; nothing else on the shared volume is touched
    assert not (boot.volume / "isekai" / "configs").exists()
    assert [p.name for p in boot.volume.iterdir()] == ["isekai"]


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_fetch_lands_the_models_through_the_link(boot: Boot) -> None:
    boot.start()
    assert boot.ran == [
        [
            sys.executable,
            str(PROVISION),
            "fetch",
            "--models-dir",
            str(boot.pod.models_root),
        ]
    ]


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_the_start_links_the_models_root_the_annotator_path_sits_under() -> None:
    assert pod_start.POD.models_root == Path(MODELS_ROOT)


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_a_link_already_in_place_is_kept(boot: Boot) -> None:
    root = boot.pod.models_root
    (boot.volume / "isekai").mkdir()
    shutil.rmtree(root)
    root.symlink_to(boot.volume / "isekai")
    boot.start()
    assert root.readlink() == boot.volume / "isekai"
    assert len(boot.execs) == 1


@pytest.mark.spec(
    "model-provisioning:reachability:a-provisioning-abort-holds-the-pod-open"
)
def test_a_failed_fetch_holds_the_pod_open_and_removes_nothing(boot: Boot) -> None:
    kept = boot.volume / "isekai" / "checkpoints" / "mismatched.safetensors"
    kept.parent.mkdir(parents=True)
    kept.write_text("left for inspection")
    boot.fetch_code = 1
    assert boot.start() == 1
    assert held(boot)
    assert kept.read_text() == "left for inspection"
    assert "fetch exited 1" in boot.err
    assert "holding the pod open" in boot.err


@pytest.mark.spec("model-provisioning:reachability:namespace-setup-is-held-open-too")
def test_a_non_empty_mounted_models_tree_is_refused_not_deleted(
    boot: Boot, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = boot.pod.models_root
    monkeypatch.setattr(os.path, "ismount", lambda path: Path(path) == root)
    assert boot.start() == 1
    assert held(boot)
    assert boot.pod.marker.exists()
    assert (root / "configs" / "v1.yaml").exists()
    assert boot.ran == []


@pytest.mark.spec("model-provisioning:reachability:namespace-setup-is-held-open-too")
def test_a_namespace_that_cannot_be_made_holds_like_a_fetch(boot: Boot) -> None:
    (boot.volume / "isekai").write_text("a file where the namespace goes")
    assert boot.start() == 1
    assert held(boot)
    assert boot.pod.marker.exists()
    assert boot.ran == []


@pytest.mark.spec("model-provisioning:reachability:the-hold-is-bounded-and-marked")
def test_the_hold_ends_on_its_own_well_inside_the_session_ceiling() -> None:
    assert 0 < HOLD_SECONDS < SESSION_CEILING_SECONDS


@pytest.mark.spec("model-provisioning:reachability:the-hold-is-bounded-and-marked")
def test_a_provisioning_hold_writes_its_marker_off_the_volume(boot: Boot) -> None:
    boot.fetch_code = 1
    boot.start()
    assert boot.pod.marker.read_text().startswith("provisioning failed at ")
    assert not boot.pod.marker.is_relative_to(boot.volume)
    assert str(boot.pod.marker) in boot.err


@pytest.mark.spec("model-provisioning:reachability:the-hold-is-bounded-and-marked")
def test_a_memory_hold_writes_no_provisioning_marker(boot: Boot) -> None:
    boot.figures[str(boot.pod.shm)] = None
    boot.start()
    assert not boot.pod.marker.exists()


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
@pytest.mark.parametrize("unset", ["GPUNIT_VOLUME_ID", "GPUNIT_VOLUME_PATH"])
def test_an_unnamed_volume_is_refused_before_the_namespace(
    boot: Boot, unset: str
) -> None:
    del boot.env[unset]
    assert boot.start() == 1
    assert held(boot)
    assert not (boot.volume / "isekai").exists()
    assert boot.ran == []


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_a_volume_below_the_floor_is_refused_before_the_namespace(boot: Boot) -> None:
    boot.figures[str(boot.volume)] = (VOLUME_SIZE_FLOOR - 1, VOLUME_SIZE_FLOOR - 1)
    assert boot.start() == 1
    assert held(boot)
    assert not (boot.volume / "isekai").exists()
    assert "total size" in boot.err


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_an_unmeasured_volume_is_refused(boot: Boot) -> None:
    boot.figures[str(boot.volume)] = None
    assert boot.start() == 1
    assert held(boot)
    assert not (boot.volume / "isekai").exists()


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_volume_guard_measures_capacity_rather_than_fill_level(boot: Boot) -> None:
    # a warm, shared volume with nothing free is still the right disk
    boot.figures[str(boot.volume)] = (VOLUME_SIZE_FLOOR, 0)
    boot.start()
    assert len(boot.execs) == 1


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_capacity_floor_clears_the_container_disk_as_well() -> None:
    # The mount can fail silently onto the container overlay, the larger of the
    # pod's own disks (D27). RunPod's sizes are decimal, the reading that makes
    # the disk biggest, so it is the one the floor must clear.
    spec = tomllib.loads((REPO / "gpunit.toml").read_text())
    container_disk = spec.get("disk_gb")
    assert isinstance(container_disk, int)
    assert VOLUME_SIZE_FLOOR > container_disk * 1000**3
