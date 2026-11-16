"""The keys a request body names, for the routes that read them."""

# What a body names to save an outline, and to ask the ink view of one.
OUTLINE_KEYS = ("points", "closed", "white", "neutral", "depth")

# What a body names to save a tattoo's pairs on a photograph, and to ask a preview.
STAGE1_KEYS = ("pairs", "not_on_photo")

# What a body names to ask the ink view of an outline.
INK_KEYS = ("points", "white", "neutral", "depth", "digest", "flow")

# What a body names to ask a preview.
PREVIEW_KEYS = (
    "target",
    "digest",
    "flow",
    "version",
    "seed",
    "pairs",
    "limb",
    "exclusions",
)

# What a body names to ask proposed pairs: the render, and the tattoo's points.
PROPOSE_KEYS = ("digest", "flow", "version", "seed", "points")

# What a body names to bake a tattoo.
BAKE_KEYS = ("digest", "flow", "version", "seed", "pairs", "limb", "exclusions")
