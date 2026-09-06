#!/usr/bin/env bash
# Pod entrypoint: enable full SSH (for the tunnel), then run ComfyUI.

set -euo pipefail

# 1. Install the SSH public key so we can log in with our private key.
mkdir -p ~/.ssh
echo "${PUBLIC_KEY:-${SSH_PUBLIC_KEY:-}}" > ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# 2. Start the SSH daemon.
mkdir -p /run/sshd
ssh-keygen -A
/usr/sbin/sshd

# 3. Where this project's models live, and what a provisioning failure costs.
#
# The volume mounts at the parent of the namespace and nothing here touches
# anything outside $MODELS_NAMESPACE — a second project lives on the same volume.
MODELS_NAMESPACE=/runpod-volume/isekai
MODELS_ROOT=/opt/ComfyUI/models

# The hold below bills while it holds, so it is bounded rather than indefinite.
# 900 s is ~$0.19 at the 4090 rate this project runs on — inside the ~$0.30
# per-session ceiling that a 3600 s hold would more than double (design.md D6).
HOLD_SECONDS=900

# The marker goes on container disk, never into the namespace: the namespace is
# exactly the thing that may have failed, and a marker a broken volume prevents
# you from writing does not make the failure legible (design.md D6).
FAILURE_MARKER=/opt/isekai/provisioning-failed

# `mountpoint -q` does NOT discriminate here. RunPod mounts the pod's own 20 GB
# volume disk at volumeMountPath when no network volume is attached, so the path
# exists and IS a mountpoint — the wrong one (design.md D5). Capacity does
# discriminate, and capacity is what is measured: that disk is 20 GB, so its
# filesystem can never report more than 18.6 GiB of total size, while the volume
# this project provisions onto is far larger. The floor sits between the two.
#
# Deliberately NOT free space. This guard proves identity, and a volume already
# holding 16.5 GiB of this project's models plus a second project's is a
# correctly-attached volume whose free space says nothing about which disk it is.
# Flooring on availability would refuse a warm boot where every entry would SKIP,
# write the failure marker and bill the whole hold, for a pod that needed to
# download nothing — and it would degrade as the shared volume filled.
VOLUME_SIZE_FLOOR_KIB=$((20 * 1024 * 1024))

# 4. Provisioning: prepare this project's namespace on the volume, then ensure the
#    models are on it.
#
# Both steps live in one function because the reachability guarantee is about
# provisioning and not about one of its steps: preparing the volume is
# provisioning by any reading a human would give the word, and a failure there —
# an unwritable volume, a link onto a path that could not be cleared — used to
# terminate the entrypoint exactly as a fetch failure once did. Every step here
# returns rather than exits, so nothing inside can kill the shell that owns the
# sshd started at step 2.
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
        echo "ERROR: $volume has a total size of ${size_kib} KiB, below the" >&2
        echo "${VOLUME_SIZE_FLOOR_KIB} KiB floor — a disk that small is the pod's" >&2
        echo "own ephemeral one, not network volume ${RUNPOD_VOLUME_ID}. Refusing" >&2
        echo "to download 16.5 GiB onto storage that does not survive the pod." >&2
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
    MODELS_DIR="$MODELS_ROOT" bash /opt/isekai/scripts/download_models.sh || return 1
}

# A provisioning abort must NOT take the container down. The abort policy leaves a
# mismatched file on disk for a human to inspect (design.md D4), and under `set -e`
# a non-zero exit here would kill PID 1 — taking the sshd started at step 2 with it
# and dying again seconds into every subsequent boot, so there is no way in. Hold
# the pod open in the foreground instead: reachable, ComfyUI not started, nothing
# deleted (design.md D17).
#
# Bounded, and marked. A pod holding open reports as running and healthy while it
# bills, so the failure that outlasts a session's spending ceiling is the one
# nobody is watching.
if ! provision; then
    echo "ERROR: provisioning failed — holding the pod open for inspection." >&2
    echo "Nothing was deleted. SSH in and look under $MODELS_NAMESPACE." >&2
    mkdir -p "$(dirname "$FAILURE_MARKER")"
    date -u +"provisioning failed at %Y-%m-%dT%H:%M:%SZ" > "$FAILURE_MARKER"
    echo "Holding ${HOLD_SECONDS}s, then exiting. Marker: $FAILURE_MARKER" >&2
    exec sleep "$HOLD_SECONDS"
fi

# 5. ComfyUI in the foreground — the main process. If it exits, the pod stops.
exec python main.py --listen 0.0.0.0 --port 8188
