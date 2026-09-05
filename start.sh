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

# 3. Namespace the models directory onto this project's slice of the volume.
#
# One symlink, not one per model folder: `folder_paths.models_dir` is then itself
# inside the namespace, so EVERY node resolves there — including the InstantID
# node and the Impact Subpack, which ignore `extra_model_paths.yaml` and, without
# this, auto-download a broken nested antelopev2 pack (design.md D8).
#
# The directory being replaced is the image's own empty models tree on container
# disk. The volume mounts at /runpod-volume and nothing here touches anything
# outside $MODELS_NAMESPACE — a second project lives on the same volume.
MODELS_NAMESPACE=/runpod-volume/isekai
MODELS_ROOT=/opt/ComfyUI/models

mkdir -p "$MODELS_NAMESPACE"
if [ ! -L "$MODELS_ROOT" ]; then
    rm -rf "$MODELS_ROOT"
    ln -s "$MODELS_NAMESPACE" "$MODELS_ROOT"
fi
echo "models namespace: $MODELS_ROOT -> $(readlink "$MODELS_ROOT")"

# 4. Ensure models are on the volume — downloads once, re-verified on later boots.
#
# A provisioning abort must NOT take the container down. The abort policy leaves a
# mismatched file on disk for a human to inspect (design.md D4), and under `set -e`
# a non-zero exit here would kill PID 1 — taking the sshd started at step 2 with it
# and dying again seconds into every subsequent boot, so there is no way in. Hold
# the pod open in the foreground instead: reachable, ComfyUI not started, nothing
# deleted (design.md D17).
if ! MODELS_DIR="$MODELS_ROOT" bash /opt/isekai/scripts/download_models.sh; then
    echo "ERROR: provisioning failed — holding the pod open for inspection." >&2
    echo "Nothing was deleted. SSH in and look under $MODELS_NAMESPACE." >&2
    exec tail -f /dev/null
fi

# 5. ComfyUI in the foreground — the main process. If it exits, the pod stops.
exec python main.py --listen 0.0.0.0 --port 8188
