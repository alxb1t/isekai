"""A run's id and the names of its layout.

The id's constants and the functions that build it from a photograph's bytes, and the
directory names and filename patterns every other part of the run directory reads.
`run.py` re-exports each name; a module outside the foundation imports them from there.

Stdlib only, and on `python -m isekai`'s import graph.
"""

import hashlib
import re

from isekai.foundation.refusal import Refusal

# Enough of the digest to separate two photographs and few enough characters to
# leave the slug legible in a listing. The whole digest is in the frame.
ID_DIGEST_CHARS = 12

# What separates the digest from the slug. An underscore, because `slug` maps
# every unsafe character to a hyphen and a hyphenated slug would leave a reader no
# way to see where the digest ended. A slug can never contain an underscore, so the
# boundary is unambiguous. Nothing splits the id on it -- `startswith` on the
# prefix is its only use -- so this is readability alone.
ID_SEPARATOR = "_"

# How much of a filename stem survives into the id. A stem is a human's label,
# not an identifier, so it is truncated rather than refused.
ID_SLUG_CHARS = 32

# Anything outside this is replaced in a slug. Deliberately narrow: the id becomes
# a directory name and is interpolated into messages, so a stem carrying a path
# separator, a shell metacharacter or a control byte must not survive it.
_UNSAFE = re.compile(r"[^a-z0-9]+")

# The magic bytes the header parser on the render path reads, and the extension
# and media type each one *is*. The extension is derived from the bytes rather
# than copied from the source name: the rule is that a filename must not lie
# about its contents, and copying a `.jpg` that holds a PNG would enshrine the
# lie inside the run.
_SIGNATURES: tuple[tuple[bytes, str, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
)

# The most leading bytes `media_type` reads, so a caller may hand it a file's head.
SIGNATURE_BYTES = max(len(signature) for signature, _, _ in _SIGNATURES)

# The frame: what the run is, written once when the run is created.
FRAME_NAME = "run.json"

# The stage directories, and the label an approved artifact carries. The run owns
# the layout, so a stage that needs another stage's directory asks the run rather
# than importing the stage. `approved` and `draft` are here for the same reason:
# `review` writes them and other parts of the run read them.
#
# **The photograph's description sits in `photo/`, every other stage under a
# flow**: `runs/<input-id>/photo/<stage>/` and `runs/<input-id>/<flow-id>/<stage>/`.
# Above the flow split is what every flow shares: the input, and the caption and
# tag lists every flow reads alike (D17). Adding a flow adds one subtree, and
# retiring one flow's work is removing one directory.
CAPTIONS = "captions"
WD14 = "wd14"
TAGS = "tags"
PHOTO = "photo"
DESCRIPTION = (CAPTIONS, WD14, TAGS)
# The verbs that write the description, and so name no flow.
PHOTOGRAPH_VERBS = ("caption", "tag")
SHEETS = "sheets"
REVIEW = "review"
PROMPTS = "prompts"
OUTPUTS = "outputs"
SOURCES = "sources"
APPROVED = "approved"
DRAFT = "draft"

# `001`, and `001.draft` / `001.approved` where a stage has that concept. No
# other label is a version, so a render's `123.render.json` is never one.
ARTIFACT = re.compile(r"^(?P<version>\d{3})(?:\.(?P<label>draft|approved))?\.json$")

# `001.error.1.transient` -- the version it stands in for, the attempt ordinal,
# and the kind, all decidable without opening anything.
ERROR = re.compile(
    r"^(?P<version>\d{3})\.error\.(?P<attempt>\d+)\.(?P<kind>transient|permanent)\.json$"
)


# --- identity -----------------------------------------------------------------


def slug(stem: str) -> str:
    """Return the readable half of a run id: lowercase, hyphenated, bounded.

    A stem that survives nothing -- all punctuation, or empty -- yields `photo`,
    so the id is always `<digest>_<something>` and never ends in a bare underscore.
    Every unsafe character becomes a hyphen, which is why the id's own separator
    is an underscore: a slug can never contain one, so the boundary between the
    digest and the readable half is unambiguous.
    """
    cleaned = _UNSAFE.sub("-", stem.lower()).strip("-")[:ID_SLUG_CHARS].strip("-")
    return cleaned or "photo"


def digest_of(body: bytes) -> str:
    """Return the SHA-256 of `body`, lowercase and in full."""
    return hashlib.sha256(body).hexdigest()


def run_id(digest: str, stem: str) -> str:
    """Return the run id for a photograph: a digest prefix, then a readable slug."""
    return f"{digest[:ID_DIGEST_CHARS]}{ID_SEPARATOR}{slug(stem)}"


def media_type(body: bytes) -> tuple[str, str]:
    """Return the media type and canonical extension the photograph's bytes are.

    Read from the bytes, never from the name. A header this build cannot identify
    stops the run rather than defaulting -- the render path reads JPEG and PNG
    headers and nothing else, so a third format would fail later and further from
    the cause.
    """
    for signature, kind, suffix in _SIGNATURES:
        if body.startswith(signature):
            return kind, suffix
    raise Refusal(
        "this build reads JPEG and PNG photographs, and these bytes are neither; "
        "convert the photograph to JPEG or PNG and offer it again"
    )
