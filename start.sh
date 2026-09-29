#!/usr/bin/env bash
# Pod entrypoint: enable full SSH (for the tunnel), then run ComfyUI.

set -euo pipefail

# Each step prints the UTC time it begins, so the pod log says where a boot's
# minutes go (0033 design D2).

# 1. The pod stops itself at its ceiling, whatever happens to the machine that
#    created it (0043 design D4). A boot that ends, however it ends, stops the pod
#    too: an exit would restart the container, and the restart arm a fresh ceiling.
POD_CEILING_SECONDS=2700
STOP_POD=/opt/isekai/tools/stop_pod.sh
echo "$(date -u +%FT%TZ) step: the stop timer"
( sleep "$POD_CEILING_SECONDS"; exec bash "$STOP_POD" ) &
trap 'export RUNPOD_API_KEY; exec bash "$STOP_POD"' EXIT

# 2. Install the SSH public key so we can log in with our private key.
echo "$(date -u +%FT%TZ) step: the SSH key"
mkdir -p ~/.ssh
echo "${PUBLIC_KEY:-${SSH_PUBLIC_KEY:-}}" > ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# 3. Start the SSH daemon. The image ships no host key, so the pod makes its own
#    and serves with it alone; the printed line is what a client checks it against
#    (0040 design D1).
echo "$(date -u +%FT%TZ) step: sshd"
mkdir -p /run/sshd
key=/etc/ssh/ssh_host_ed25519_key
[ -f "$key" ] || ssh-keygen -q -t ed25519 -N '' -f "$key"
/usr/sbin/sshd -o HostKey="$key"
echo "isekai host key: $(ssh-keygen -lf "$key.pub" | awk '{print $2}')"

# 4. Where this project's models live, and what a provisioning failure costs.
#
# The volume mounts at the parent of the namespace and nothing here touches
# anything outside $MODELS_NAMESPACE — a second project lives on the same volume.
MODELS_NAMESPACE=/runpod-volume/isekai
MODELS_ROOT=/opt/ComfyUI/models

# The hold below bills while it holds, so it is bounded rather than indefinite.
# 900 s is ~$0.19 at the 4090 rate this project runs on — inside the ~$0.30
# per-session ceiling that a 3600 s hold would more than double (design.md D6).
HOLD_SECONDS=900

# A hold that ended in its process exiting would boot again in a restarted
# container, and hold again, forever; it ends in the stop (0043 design D5).
hold() {  # hold <line>...: say why, stay reachable HOLD_SECONDS, then stop the pod
    printf '%s\n' "$@" >&2
    echo "Holding ${HOLD_SECONDS}s, then stopping the pod." >&2
    sleep "$HOLD_SECONDS"
    exec bash "$STOP_POD"
}

# The marker goes on container disk, never into the namespace: the namespace is
# exactly the thing that may have failed, and a marker a broken volume prevents
# you from writing does not make the failure legible (design.md D6).
FAILURE_MARKER=/opt/isekai/provisioning-failed

# `mountpoint -q` does NOT discriminate here. RunPod mounts the pod's own 20 GB
# volume disk at the mount path when no network volume is attached, so the path
# exists and IS a mountpoint — the wrong one (design.md D5). Capacity does
# discriminate, and capacity is what is measured. There are exactly two wrong
# disks this path can resolve to, and the floor clears BOTH:
#
#   * the pod's own volume disk, `volumeInGb: 20`  →  20e9 B  ≈ 18.6 GiB
#   * the container overlay, `disk: 30` (infra/up.sh) → ≈ 27.9 GiB
#
# The second is the case this pod-side check exists for at all — id set, mount
# silently failed, so the path falls through to the overlay — and a floor sized
# only against the first lets it pass. The network volume this project provisions
# onto is 20 GB, but it reports its storage cluster's capacity, far above both
# (docs D27), so 40 GiB sits clear of both wrong disks with ~12 GiB of headroom
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
# pod holds before it starts instead (0040 design D2).
SHM_FREE_FLOOR_KIB=$((1 * 1024 * 1024))

# 5. Provisioning: prepare this project's namespace on the volume, then ensure the
#    models are on it.
#
# Both steps live in one function because the reachability guarantee is about
# provisioning and not about one of its steps: preparing the volume is
# provisioning by any reading a human would give the word, and a failure there —
# an unwritable volume, a link onto a path that could not be cleared — used to
# terminate the entrypoint exactly as a fetch failure once did. Every step here
# returns rather than exits, so nothing inside can kill the shell that owns the
# sshd started at step 3.
provision() {
    if [ -z "${RUNPOD_VOLUME_ID:-}" ]; then
        echo "ERROR: RUNPOD_VOLUME_ID is empty — the pod was not told which" >&2
        echo "network volume to expect. Refusing to provision." >&2
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
        echo "30 GB container disk, not network volume ${RUNPOD_VOLUME_ID}." >&2
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
    # which takes no config (design.md D17).
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

# A provisioning abort must NOT take the container down. The abort policy leaves a
# mismatched file on disk for a human to inspect (design.md D4), and under `set -e`
# a non-zero exit here would kill PID 1 — taking the sshd started at step 3 with it
# and dying again seconds into every subsequent boot, so there is no way in. Hold
# the pod open in the foreground instead: reachable, ComfyUI not started, nothing
# deleted (design.md D17).
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

# 6. Everything ComfyUI writes goes to memory, which dies with the pod; the
#    container disk may outlive it unwiped (0040 design D2). An upload spools to
#    TMPDIR first, and a /dev/shm that is not memory, or not read, holds (0042 design D2).
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

# ComfyUI needs no key, and code it runs can print its environment. The key
# leaves the environment but stays in this shell, for the stop at its end
# (0043 design D6).
export -n RUNPOD_API_KEY

# 7. ComfyUI in the foreground, as this script's child: when it exits, with
#    success or not, the script ends and step 1's trap stops the pod.
#    It writes its temp files to `temp` under the directory it is given. No render
#    carries metadata, so none carries the prompt (0040 design D3).
echo "$(date -u +%FT%TZ) step: ComfyUI"
python main.py --listen 0.0.0.0 --port 8188 \
    --input-directory /dev/shm/comfyui/input \
    --output-directory /dev/shm/comfyui/output \
    --temp-directory /dev/shm/comfyui \
    --user-directory /dev/shm/comfyui/user \
    --disable-metadata
