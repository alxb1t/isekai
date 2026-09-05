#!/usr/bin/env bash
# Provision the model stack onto the volume, from the pinned manifest beside this file.
#
# Idempotent: an entry already present and verified is skipped, so a re-boot on a warm
# volume is a no-op. NOT skipped by name — `provision.py` hashes every file it finds, so
# an out-of-band swap is caught rather than trusted. A present file that fails is left on
# disk and the run aborts: the volume is shared with another project, and a file this run
# did not write is not this run's to remove.
#
# The split is deliberate (design.md D14): `provision.py` owns every decision and this
# script owns only the transfer. It asks for a plan, runs `wget` for whatever URL it is
# handed, and asks the module to verify and land the result. Nothing lands under its final
# name until its SHA-256 matches the manifest.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROVISION="${HERE}/../isekai/provision.py"

# ComfyUI's models root
MODELS_DIR="${MODELS_DIR:-./models}"

mkdir -p "$MODELS_DIR"

# Decide everything first: an abort anywhere stops the run before a single byte moves.
plan="$(python3 "$PROVISION" plan "$MODELS_DIR")"

# A FETCH line carries every source that survived the pre-flight, tab-separated
# and in the manifest's order, so `$urls` is the remainder of the line. It is left
# unquoted below on purpose: that is the word split that turns it back into a list.
while IFS=$'\t' read -r action dest urls; do
    [ -n "$action" ] || continue
    case "$action" in
        SKIP)
            echo "skip (present, verified): $dest"
            ;;
        FETCH)
            target="${MODELS_DIR}/${dest}"
            mkdir -p "$(dirname "$target")"
            landed=0
            # Walk the sources in order: a dead mirror or bytes that do not verify
            # advance to the next one, and only exhausting them all aborts the run.
            # shellcheck disable=SC2086
            for url in $urls; do
                echo "downloading: $url"
                if ! wget -q --show-progress -O "${target}.partial" "$url"; then
                    rm -f "${target}.partial"
                    echo "WARNING: transfer failed from $url" >&2
                    continue
                fi
                if ! python3 "$PROVISION" land "$MODELS_DIR" "$dest" "${target}.partial"; then
                    echo "WARNING: bytes served by $url did not verify" >&2
                    continue
                fi
                landed=1
                break
            done
            if [ "$landed" -eq 0 ]; then
                echo "ERROR: every source for $dest failed" >&2
                exit 1
            fi
            ;;
        *)
            echo "ERROR: unrecognised plan line: $action" >&2
            exit 1
            ;;
    esac
done <<< "$plan"

echo "models ready under $MODELS_DIR"
