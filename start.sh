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

# 3. Ensure models are on the volume — downloads once, skipped on later boots.
MODELS_DIR=/opt/ComfyUI/models bash /opt/isekai/scripts/download_models.sh

# 4. ComfyUI in the foreground — the main process. If it exits, the pod stops.
exec python main.py --listen 0.0.0.0 --port 8188
