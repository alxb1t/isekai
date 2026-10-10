#!/usr/bin/env bash
# Pod entrypoint, run by gpunit's boot script: provision the models, then serve
# ComfyUI. The boot script has armed the pod's stop and started sshd, and stops
# the pod when this script ends, however it ends (D36).

set -euo pipefail

# Each step prints the UTC time it begins, so the pod log says where a boot's
# minutes go.

# 1. Where this project's models live, and what a provisioning failure costs.
#
# gpunit mounts the volume at GPUNIT_VOLUME_PATH, the parent of the namespace, and
# nothing here touches anything outside $MODELS_NAMESPACE — a second project lives
# on the same volume. An unset path is refused inside `provision`, where it holds.
MODELS_NAMESPACE="${GPUNIT_VOLUME_PATH:-}/isekai"
MODELS_ROOT=/opt/ComfyUI/models

# The hold below bills while it holds, so it is bounded rather than indefinite.
# 900 s is ~$0.19 at the 4090 rate this project runs on — inside the ~$0.30
# per-session ceiling that a 3600 s hold would more than double.
HOLD_SECONDS=900

# A hold ends in this script exiting non-zero, which the boot script turns into
# the pod's stop.
hold() {  # hold <line>...: say why, stay reachable HOLD_SECONDS, then stop the pod
    printf '%s\n' "$@" >&2
    echo "Holding ${HOLD_SECONDS}s, then stopping the pod." >&2
    sleep "$HOLD_SECONDS"
    exit 1
}

# The marker goes on container disk, never into the namespace: the namespace is
# exactly the thing that may have failed, and a marker a broken volume prevents
# you from writing does not make the failure legible.
FAILURE_MARKER=/opt/isekai/provisioning-failed

# `mountpoint -q` does NOT discriminate here. RunPod mounts the pod's own 20 GB
# volume disk at the mount path when no network volume is attached, so the path
# exists and IS a mountpoint — the wrong one. Capacity does
# discriminate, and capacity is what is measured. There are exactly two wrong
# disks this path can resolve to, and the floor clears BOTH:
#
#   * the pod's own volume disk, `volumeInGb: 20`  →  20e9 B  ≈ 18.6 GiB
#   * the container overlay, `disk_gb = 30` (gpunit.toml) → ≈ 27.9 GiB
#
# The second is the case this pod-side check exists for at all — id set, mount
# silently failed, so the path falls through to the overlay — and a floor sized
# only against the first lets it pass. The network volume this project provisions
# onto is 20 GB, but it reports its storage cluster's capacity, far above both
# (D27), so 40 GiB sits clear of both wrong disks with ~12 GiB of headroom
# above the larger: wide enough that neither a decimal/binary reading of RunPod's
# sizes nor a filesystem's metadata overhead can move a disk across it.
#
# Deliberately NOT free space. This guard proves identity, and a volume already
# holding 16.5 GiB of this project's models plus a second project's is a
# correctly-attached volume whose free space says nothing about which disk it is.
# Flooring on availability would refuse a warm boot where every entry would SKIP,
# write the failure marker and bill the whole hold, for a pod that needed to
# download nothing — and it would degrade as the shared volume filled.
VOLUME_SIZE_FLOOR_KIB=$((40 * 1024 * 1024))

# Below this much free memory ComfyUI would fail its first save mid-session, so the
# pod holds before it starts instead.
SHM_FREE_FLOOR_KIB=$((1 * 1024 * 1024))

# 2. Provisioning: prepare this project's namespace on the volume, then ensure the
#    models are on it.
#
# Both steps live in one function because the reachability guarantee is about
# provisioning and not about one of its steps: preparing the volume is
# provisioning by any reading a human would give the word, and a failure there —
# an unwritable volume, a link onto a path that could not be cleared — would
# terminate the entrypoint exactly as a fetch failure would. Every step here
# returns rather than exits, so nothing inside can end the boot before the hold.
provision() {
    if [ -z "${GPUNIT_VOLUME_ID:-}" ] || [ -z "${GPUNIT_VOLUME_PATH:-}" ]; then
        echo "ERROR: GPUNIT_VOLUME_ID or GPUNIT_VOLUME_PATH is empty — the pod was" >&2
        echo "not told which network volume to expect. Refusing to provision." >&2
        return 1
    fi

    local volume size_kib
    volume="$(dirname "$MODELS_NAMESPACE")"
    size_kib="$(df -k --output=size "$volume" | tail -n 1 | tr -d ' ')"
    case "$size_kib" in
        '' | *[!0-9]*)
            echo "ERROR: could not read the total size of $volume." >&2
            echo "Refusing to provision onto a volume that cannot be measured." >&2
            return 1
            ;;
    esac
    if [ "$size_kib" -lt "$VOLUME_SIZE_FLOOR_KIB" ]; then
        echo "ERROR: measured $volume at a total size of ${size_kib} KiB, below" >&2
        echo "the ${VOLUME_SIZE_FLOOR_KIB} KiB floor — a disk that small is the" >&2
        echo "pod's own ephemeral storage, either its 20 GB volume disk or its" >&2
        echo "30 GB container disk, not network volume ${GPUNIT_VOLUME_ID}." >&2
        echo "Refusing to download 16.5 GiB onto storage that dies at teardown." >&2
        return 1
    fi

    # One symlink, not one per model folder: `folder_paths.models_dir` is then
    # itself inside the namespace, so EVERY node resolves there — including the
    # InstantID node and the Impact Subpack, which ignore `extra_model_paths.yaml`
    # and, without this, auto-download a broken nested antelopev2 pack.
    #
    # The tree being replaced is the image's own, on container disk. It is NOT
    # empty: the ComfyUI clone tracks `models/configs/*.yaml`, and the delete
    # drops them knowingly, because the graph uses `CheckpointLoaderSimple`,
    # which takes no config.
    mkdir -p "$MODELS_NAMESPACE" || return 1
    if [ ! -L "$MODELS_ROOT" ]; then
        # Guarded on the delete's premise, not on its proxy: what makes it safe
        # is that this is the image's own tree on container disk. A non-empty
        # tree someone has mounted here is a real models tree, and deleting one
        # is an explicit operator act, never a silent entrypoint step.
        if mountpoint -q "$MODELS_ROOT" && [ -n "$(ls -A "$MODELS_ROOT")" ]; then
            echo "ERROR: refusing to delete $MODELS_ROOT — it is a non-empty" >&2
            echo "mount, not the image's own models tree." >&2
            return 1
        fi
        rm -rf "$MODELS_ROOT" || return 1
        ln -s "$MODELS_NAMESPACE" "$MODELS_ROOT" || return 1
    fi
    echo "models namespace: $MODELS_ROOT -> $(readlink "$MODELS_ROOT")"

    # Downloads once, re-verified on later boots.
    echo "$(date -u +%FT%TZ) step: the download"
    MODELS_DIR="$MODELS_ROOT" bash /opt/isekai/tools/download_models.sh || return 1
}

# A provisioning abort must NOT end the boot at once. The abort policy leaves a
# mismatched file on disk for a human to inspect, and under `set -e` a non-zero
# exit here would stop the pod before anyone could get in. Hold the pod open in
# the foreground instead: reachable over the boot script's sshd, ComfyUI not
# started, nothing deleted.
#
# Bounded, and marked. A pod holding open reports as running and healthy while it
# bills, so the failure that outlasts a session's spending ceiling is the one
# nobody is watching.
echo "$(date -u +%FT%TZ) step: provisioning"
if ! provision; then
    mkdir -p "$(dirname "$FAILURE_MARKER")"
    date -u +"provisioning failed at %Y-%m-%dT%H:%M:%SZ" > "$FAILURE_MARKER"
    hold "ERROR: provisioning failed — holding the pod open for inspection." \
        "Nothing was deleted. SSH in and look under $MODELS_NAMESPACE." \
        "Marker: $FAILURE_MARKER"
fi

# 3. Everything ComfyUI writes goes to memory, which dies with the pod; the
#    container disk may outlive it unwiped. An upload spools to
#    TMPDIR first, and a /dev/shm that is not memory, or not read, holds.
echo "$(date -u +%FT%TZ) step: the memory directories"
mkdir -p /dev/shm/comfyui/input /dev/shm/comfyui/output /dev/shm/comfyui/temp /dev/shm/comfyui/user /dev/shm/comfyui/tmp
export TMPDIR=/dev/shm/comfyui/tmp
shm_type="$(stat -f -c %T /dev/shm)" || shm_type=''
shm_kib="$(df -k --output=size,avail /dev/shm | tail -n 1)" || shm_kib=''
echo "/dev/shm is ${shm_type}; KiB, size and free:${shm_kib}"
if [ "$shm_type" != "tmpfs" ]; then
    hold "ERROR: /dev/shm is '${shm_type}', not a tmpfs — the photograph would reach a disk." \
        "ComfyUI was not started."
fi
free_kib="$(awk '{print $2}' <<<"$shm_kib")"
case "$free_kib" in
    '' | *[!0-9]*)
        hold "ERROR: could not read /dev/shm's free space from '${shm_kib}'." \
            "ComfyUI was not started."
        ;;
esac
if [ "$free_kib" -lt "$SHM_FREE_FLOOR_KIB" ]; then
    hold "ERROR: /dev/shm has ${free_kib} KiB free, below the ${SHM_FREE_FLOOR_KIB} KiB" \
        "floor — too little memory to hold the photograph and its renders." \
        "ComfyUI was not started."
fi

# 4. ComfyUI replaces this script, so its exit is the boot's end and the boot
#    script stops the pod. It writes its temp files to `temp` under the directory
#    it is given. No render carries metadata, so none carries the prompt.
echo "$(date -u +%FT%TZ) step: ComfyUI"
exec python main.py --listen 0.0.0.0 --port 8188 \
    --input-directory /dev/shm/comfyui/input \
    --output-directory /dev/shm/comfyui/output \
    --temp-directory /dev/shm/comfyui \
    --user-directory /dev/shm/comfyui/user \
    --disable-metadata
