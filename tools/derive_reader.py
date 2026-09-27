"""Re-derive `config/reader.json` -- the files the local reader's model is built from.

Run it from the repository root:

    uv run python -m tools.derive_reader

It rewrites `config/reader.json` in place; re-running leaves it byte-identical,
and `git diff --exit-code config/reader.json` is the check.

**The fourth manifest, and it answers which files an alias is built from.** A flow
names the reader by an alias `ollama create` builds from the Modelfile, and the
files behind that alias shape the prose. `aliases` names, for each alias, which
entry is its model and which its projector, so `isekai/boundary/ollama.py` can
compare them with Ollama's own record before the first call (0033 design D4).
"""

from isekai.boundary.provision import READER_MANIFEST_PATH as MANIFEST_PATH
from isekai.boundary.provision import ReaderModel
from tools.manifest import Manifest, ManifestEntry, Source, Spec, entry_for, write

# The date the revision below was taken. Bumping the revision means bumping this.
PINNED = "2026-09-27"

# concedo publishes the requantisation and the projector together, so the primary
# is a publisher and needs no alternate. It is the only repository that ships the
# projector: see `config/joycaption.Modelfile`.
PUBLISHERS = ("concedo",)

REPOSITORY = "concedo/llama-joycaption-beta-one-hf-llava-mmproj-gguf"
REVISION = "acfe6bf78ae4e411cd5c7c8f4a71ba01f26a5b97"

# Where each file lands: `models/joycaption/`, where the Modelfile's `FROM` lines
# look for them.
MODEL = "joycaption/Llama-Joycaption-Beta-One-Hf-Llava-Q4_K.gguf"
PROJECTOR = "joycaption/llama-joycaption-beta-one-llava-mmproj-model-f16.gguf"

SPECS: tuple[Spec, ...] = tuple(
    Spec(dest, (Source(REPOSITORY, REVISION, dest.split("/", 1)[1]),))
    for dest in (MODEL, PROJECTOR)
)

# The alias every tracked flow names, and the entries `ollama create` builds it from.
ALIASES: dict[str, ReaderModel] = {
    "joycaption-beta-one-q4k": {"model": MODEL, "projector": PROJECTOR},
}


def derive() -> Manifest:
    """Build the reader's manifest: both files by published digest, and the aliases."""
    entries: list[ManifestEntry] = [entry_for(spec) for spec in SPECS]
    return {
        "pinned": PINNED,
        "publishers": list(PUBLISHERS),
        "entries": entries,
        "aliases": ALIASES,
    }


def main() -> None:
    """Derive the reader's manifest and write it to `config/reader.json`."""
    write(derive(), MANIFEST_PATH)


if __name__ == "__main__":
    main()
