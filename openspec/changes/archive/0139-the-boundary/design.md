# The boundary — design

The tag stage, the tagger, the provisioner, the pose module and Ollama's transport are held by tests that never reach their lines, and a digest mismatch and an undecodable photograph end in a traceback where a requirement says refuse. This change reaches each line, fixes those, and holds all of them with mutants. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The audit ran each test against mutants of the product. The findings below survived or never ran, read at the cut at `d3f72349`. `0135-the-paydown` adds the replay mode `--edits`, `tests/mutants.json` and `make mutants`; `0136-the-cli-and-the-session`, `0137-the-server` and `0138-the-review-and-the-import` fill the file with their entries. Phase 5 appends to it.

| gap | where it lives at the cut |
|---|---|
| the label index's digest is never planted wrong, and a mismatch ends `tag` and `prepare` in a traceback | `isekai/boundary/wd14.py` `verified_paths`; `isekai/interface/wiring.py` `tagger_for`; `tests/test_wd14.py` |
| a photograph too large to decode raises an error that is not an `OSError`, so the tag stage crashes with no failure record | `isekai/boundary/wd14.py` `prepare`; `isekai/pipeline/tagging.py` `tag_wd14` |
| the preparation, the session and the opener run in no test | `isekai/boundary/wd14.py` `prepare`, `OnnxSession`, `open_session` |
| the published-digest pre-flight reads a header no test supplies | `isekai/boundary/provision.py` `HuggingFaceFetcher.published_digest`; `tests/test_provision.py` |
| `post` and `probe` catch an answered status in no test | `isekai/boundary/ollama.py`; `tests/test_ollama.py` |
| the pose crop is held by its shape alone | `isekai/boundary/pose.py` `crop_input`; `tests/test_pose.py` |

```
 wiring.py      tagger_for                                        (phase 1)
 wd14.py        verified_paths · prepare · OnnxSession · open_session   (phases 1, 2, 3)
 provision.py   published_digest   (frozen into the pod image: tests only)   (phase 4)
 ollama.py      post · probe                                      (phase 4)
 pose.py        crop_input                                        (phase 4)
 tests/mutants.json ◀── mutants.json                              (phase 5)
```

## Goals / Non-Goals

**Goals**
- Each half of the pin is planted wrong, and a mismatch reaches the verb as a refusal, the hosted tagger still running.
- A photograph that will not decode is a refusal the stage records.
- The preparation, the session and the opener are held by value, and one tiny model runs through the real runtime.
- The published digest is read offline from a redirect, `post` and `probe` answer a status, and the pose crop is held by value.
- Each finding's mutant dies, and stays dead in `tests/mutants.json`.

**Non-Goals**
- A format version, a flag, a verb, a decision in force, or a requirement's text. `docs/decisions.md` is not edited.
- A line of `isekai/boundary/provision.py`, which the pod image freezes.
- The boundary's other findings of the audit.
- A patch of `isekai.pipeline.tagging` or `isekai.boundary.pose`, which would add a row to the patch ratchet.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Each finding is held at the lowest layer that fails for its mutant: the boundary function first, the verb only for what a refusal must reach | a layer above costs setup and hides the line | an end-to-end test for each |
| [D2](#d2) | A digest mismatch becomes a refusal in `tagger_for`, the place `proposer_of` converts its own; no attempt is recorded, as for an absent file | the pin requirement says refuse naming what to fetch and record no attempt; the evaluator converts at its own site | converting in `verified_paths`, which turns the evaluator's own conversion dead |
| [D3](#d3) | Both halves of the pin are planted wrong in one parametrized test, and the length tests carry a scenario of their own | the model half alone was ever planted; the length refusal is the symptom of a mismatched pair | a second copy of the test for the label index |
| [D4](#d4) | `prepare` turns a decode failure into a refusal naming the photograph, as the evaluator's face check does; the stale comment on what the gate installs is corrected in the same diff | a failure in either tagger shall not stop the other, and the product may not import `evaluation` | widening `tagging.py`'s catch, which needs Pillow's error class at module scope |
| [D5](#d5) | The tagger's runtime is held in a new file `tests/test_wd14_runtime.py`: the preparation by value, the opener over a stub runtime, and one tiny model through the real runtime, its bytes built from the standard library | `tests/test_wd14.py` forbids numpy, Pillow and the runtime; no package is added | a binary model in the tree; the `onnx` package |
| [D6](#d6) | The published digest is read offline by stubbing `urllib.request.build_opener` | the file's own pattern; no socket, no thread | a loopback server |
| [D7](#d7) | `post` and `probe` are driven by patching `ollama.OPENER`, in `tests/test_ollama.py` | the opener is the module's own seam; `0137-the-server` edits `tests/test_ui_jobs.py` | a test beside the one in `tests/test_ui_jobs.py` |
| [D8](#d8) | The pose crop is held by value on a scale-one crop with whole-pixel offsets | bilinear sampling lands on exact pixels there | a real model |
| [D9](#d9) | Scenarios are added under the requirements that demand them; other tests carry a key that stands | a patch adds a scenario under a requirement, never a requirement | `skip_specs`; a MODIFIED SHALL |
| [D10](#d10) | Phase 5 appends this change's mutants to `tests/mutants.json`, each naming its killing test file, and adds an entry for each fixed line | a mutant that must stay dead is a file | the audit's `covering`, which the replay refuses |

### D1

The tests extend the files that hold each subject, and the new file is `tests/test_wd14_runtime.py` of [D5](#d5). A mutant's test file is named in [mutants.json](mutants.json), and the replay runs that whole file. No test is deleted, so [Tests](#tests) holds no table of removals.

### D2

The pin requirement says the command refuses naming what to fetch, and no attempt is recorded. The tag stage already keeps the opener outside its `try`, so a refusal from it is reported and the hosted tagger still runs, with no error record. A digest mismatch is the same condition as an absent file: a fact about the build. `isekai/interface/wiring.py` after the change:

```python
def tagger_for() -> LocalTagger:
    """Open the local tagger and read its label index.

    (the paragraphs above stay)

    A file whose bytes disagree with its pin is a refusal naming the file and the
    fetch, so the verb reports it and the hosted tagger still runs.
    """
    try:
        return open_session()
    except DigestMismatch as swapped:
        raise Refusal(
            f"{swapped}; delete that file, run `{VOCABULARY_REMEDY}`, then this "
            "command again"
        ) from swapped
```

`VOCABULARY_REMEDY` is what `wd14.REMEDY` is, and `wiring.py` imports it already. The wording is the evaluator's own, in `evaluation/recall.py`. `verified_paths` is unchanged: it raises `DigestMismatch`, whose message names the file and both digests.

```
 verified_paths ──▶ DigestMismatch ──▶ tagger_for ──▶ Refusal ──▶ _once keeps it ──▶ hosted tagger runs
```

`_once` keeps the refusal, so the 467 MB hash is not run again for the next photograph. The brief's Q55 says the refusal is "recorded". It is read here as reported, as an absent file is: the pin scenario says no attempt is recorded, and the stage's own record is of a photograph's failure.

The tests:

| test | file | holds |
|---|---|---|
| a pin that does not match is a refusal and the hosted list is written | `tests/test_tagging.py` | `wiring.open_session` patched to raise `DigestMismatch`; `tag` over `_wired(tmp_path, tagger=wiring.tagger_for, hosted=hosted)` exits `1`, the hosted list is written, no `*.json` is in the local tagger's directory, and the error stream holds `MODEL_DEST` and `REMEDY` |
| `prepare` refuses when a pin does not match | `tests/test_pipeline_cli.py` | the same patch over `replace(_wiring(tmp_path), tagger=wiring.tagger_for)`; `prepare` of one assigned cell exits `1` and the error stream holds `REMEDY` |

Both carry `tagging:pin:the-label-index-and-the-model-are-verified-together`; the first also carries `tagging:order:a-local-failure-leaves-the-hosted-list-written`.

### D3

`test_a_half_whose_bytes_do_not_match_its_digest_stops_the_stage` is extended in place: `@pytest.mark.parametrize("dest", [LABELS_DEST, MODEL_DEST], ids=["the-label-index", "the-model"])`. It plants both files, overwrites `dest`'s bytes with `b"other bytes"`, and asserts `provision.DigestMismatch` and `dest in str(refused.value)`. Its comment says `verified_paths` leaves the mismatch a `DigestMismatch`, and the verb's wiring turns it into a refusal.

The longer-vector and shorter-vector tests carry the new key `tagging:pin:a-vector-that-disagrees-with-the-index-is-refused` in place of the pin key. The shorter-vector test asserts what the longer-vector test does: `"2 probabilities"`, `"3 neurons"` and `REMEDY` in the message.

### D4

`isekai/boundary/wd14.py` after the change, in `prepare`:

```python
    try:
        opened = Image.open(photo)
        opened.load()
    except (
        OSError,
        ValueError,
        EOFError,
        SyntaxError,
        Image.DecompressionBombError,
    ) as undecodable:
        raise Refusal(f"{photo} does not decode as an image") from undecodable
```

`Image` is the module `_require("PIL.Image")` returns, so the error class is reached at call time and the entry point's import graph keeps no third-party package. The sentence is the evaluator's own: `tests/test_recall.py` matches `1\.png does not decode` over an oversized PNG, and the refusal now comes from `prepare` with the same words.

`prepare`'s docstring gains one paragraph: a photograph that does not decode is a `Refusal` naming it, which the tag stage records as the photograph's permanent failure. `Session`'s docstring is corrected where it says the gate's environment does not install `numpy` and `Pillow`:

```
before:  `prepare` needs `numpy` and
         `Pillow`, which the environment the gate runs in deliberately does not
         install -- so a seam that began *after* preparation would leave the stage
         itself untestable and `tagging:seam:offline-double-satisfies-the-interface`
         unprovable.
after:   `prepare` needs `numpy` and
         `Pillow`, declared dependencies the gate's environment installs, and no
         stage test reaches them -- the double sits ahead of preparation, so a seam
         that began *after* it would put both inside every stage test and
         `tagging:seam:offline-double-satisfies-the-interface` would stop proving
         that the stage runs on a double alone.
```

The test, in `tests/test_tagging.py`, carries `tagging:order:a-photograph-that-will-not-decode-is-a-local-failure`. A class `_Preparing` has `run(self, photo)` call the real `prepare(photo, 8)` and return `[0.0, 0.0, 0.0]`. The photograph is `oversized_png()` from `tests/images.py`, written as `big.png`; the wiring is `_wired(tmp_path, tagger=Always(dataclasses.replace(fake_tagger(), session=_Preparing())), hosted=hosted)`. `tag` exits `1`; the hosted list `001.json` is written; the local tagger's directory holds `001.error.1.permanent.json` and no `001.json`; the error stream holds `does not decode as an image`.

### D5

`tests/test_wd14_runtime.py` imports `numpy` and `PIL`, and its docstring says why the file exists: `tests/test_wd14.py` holds the boundary with no wheel. It takes `_planted` from `tests.test_wd14`, as `tests/test_edit_session.py` takes from `tests.test_render`. Its tests:

| test | holds | carries |
|---|---|---|
| a photograph with a transparent pixel is composited on white, padded and handed over blue first | a 2 by 1 RGBA PNG, one pixel transparent and one `(255, 0, 0, 255)`; `prepare(photo, 2).tolist()` is `[[[[255, 255, 255], [0, 0, 255]], [[255, 255, 255], [255, 255, 255]]]]`, dtype `float32` | `tagging:seam:the-photograph-is-prepared-by-the-graphs-rule` |
| an opaque photograph is centred on white in blue, green, red | a 4 by 2 RGB PNG, its left half `(10, 20, 30)` and its right half `(40, 50, 60)`; `prepare(photo, 4)` is white in the first and last rows, and in the middle rows `[30, 20, 10]` twice then `[60, 50, 40]` twice | the same |
| a graph whose bytes differ from its pin is never opened | `_planted` with the model's bytes changed after the manifest, `provision.load_manifest` patched, `wd14._require` patched to a dispatcher returning a recording runtime for `"onnxruntime"` and `importlib.import_module` for the rest; `open_session(tmp_path)` raises `DigestMismatch` and the runtime opened nothing | `tagging:pin:the-graph-is-opened-only-after-both-digests-verify` |
| the session opens the verified path on the CPU | the same stub over matching bytes; the runtime opened `(str(tmp_path / MODEL_DEST), ["CPUExecutionProvider"])` alone, and the tagger holds the labels of `INDEX` and both digests | the same |
| a tiny graph run through the real runtime returns what `prepare` handed it | `OnnxSession` over `_tiny_graph(3)` written to `tiny.onnx`: `dimension` is `3`, and `run(photo)` over a 3 by 3 RGB PNG, its first pixel `(10, 20, 30)`, equals `numpy.asarray(prepare(photo, 3)).reshape(-1).tolist()` and starts `[30.0, 20.0, 10.0]` | `tagging:seam:the-photograph-is-prepared-by-the-graphs-rule` |

The stub-runtime tests and the real-runtime test set the telemetry switch as `tests/test_wd14.py`'s test does: `monkeypatch.setenv("ORT_DISABLE_TELEMETRY", "0")` then `monkeypatch.delenv("ORT_DISABLE_TELEMETRY")`, so `OnnxSession`'s write is undone.

The tiny graph is one `Flatten` node over an input `x` of shape `batch, edge, edge, 3`, so the session's output is the prepared array flattened. An ONNX model is plain protobuf, and the builder is the standard library's `bytes`:

```python
def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        low = value & 0x7F
        value >>= 7
        if value:
            out.append(low | 0x80)
        else:
            out.append(low)
            return bytes(out)


def _number(field: int, value: int) -> bytes:
    return _varint(field << 3) + _varint(value)


def _message(field: int, body: bytes) -> bytes:
    return _varint(field << 3 | 2) + _varint(len(body)) + body


def _text(field: int, value: str) -> bytes:
    return _message(field, value.encode())


def _dimension(size: int | str) -> bytes:
    return _message(1, _number(1, size) if isinstance(size, int) else _text(2, size))


def _tensor(name: str, shape: tuple[int | str, ...]) -> bytes:
    dims = b"".join(_dimension(size) for size in shape)
    kind = _message(1, _number(1, 1) + _message(2, dims))
    return _text(1, name) + _message(2, kind)


def _tiny_graph(edge: int) -> bytes:
    node = _text(1, "x") + _text(2, "y") + _text(3, "flatten") + _text(4, "Flatten")
    graph = (
        _message(1, node)
        + _text(2, "tiny")
        + _message(11, _tensor("x", ("batch", edge, edge, 3)))
        + _message(12, _tensor("y", ("batch", edge * edge * 3)))
    )
    return _number(1, 8) + _message(8, _number(2, 13)) + _message(7, graph)
```

The model is `ModelProto` with `ir_version` 8, opset 13 of the default domain and `graph`; `Flatten`'s axis defaults to 1 at that opset; element type 1 is `FLOAT`. A dimension is a number or a name, and `"batch"` is the symbolic axis `OnnxSession.dimension` skips.

### D6

`HuggingFaceFetcher.published_digest` calls `urllib.request.build_opener(_KeepRedirect)` and `opener.open(request, timeout=30)`. The tests in `tests/test_provision.py` patch `"urllib.request.build_opener"` by its string, as the file's test of the bad status line does, so no ratchet row is added. Each carries `model-provisioning:preflight:the-published-digest-is-read-from-the-sources-answer`:

| test | the stub opener | holds |
|---|---|---|
| a redirect that carries the digest is read | `open` raises `urllib.error.HTTPError(url, 302, "Found", headers, io.BytesIO(b""))`, `headers` an `email.message.Message` holding `x-linked-etag: "<64 hex>"` quoted | `published_digest(PRIMARY)` is the unquoted digest, and `build_opener` was handed `provision._KeepRedirect` |
| a response that carries the digest is read | `open` returns a context manager whose `headers` is such a `Message` | the same digest |
| a value that is no digest is none | a 40-hex value, and a redirect with no header | `published_digest(PRIMARY)` is `None` for each |
| the redirect is kept | `provision._KeepRedirect().redirect_request(request, None, 302, "Found", headers, "https://example.invalid/")` | `None` |

### D7

`post` returns an answered status and `probe` takes any status as up; both read the module's `OPENER` at call time. The tests in `tests/test_ollama.py` import `ollama` and patch `OPENER` with a stub whose `open(request, timeout)` raises or returns. `from isekai.boundary.ollama import ...` keeps its list, and the file gains `from isekai.boundary import ollama`.

| test | the stub | holds | carries |
|---|---|---|---|
| `post` returns an answered status with its body | raises `urllib.error.HTTPError(f"{HOST}{GENERATE}", 404, "Not Found", Message(), io.BytesIO(b'{"error": "model not found"}'))` | `post(GENERATE, b"{}") == (404, b'{"error": "model not found"}')` | `caption:reachability:absent-model-names-how-to-create-it` |
| `ask` over the real transport refuses a 404 naming the remedy | the same | `ask(BODY, remedy=REMEDY)` raises `Refusal` holding `REMEDY` and not `ollama.NOT_LISTENING` | the same |
| `probe` takes any answer as up | parametrized: raises the 404 `HTTPError`; returns a context-manager response | `ollama.probe()` returns `None` for each | `caption:reachability:a-host-that-answers-with-a-status-is-reachable` |

### D8

`crop_input(image, crop, size)` is an affine transform with bilinear sampling. With a crop whose width and height equal `size`'s, the scale is one, and with whole-pixel offsets each output pixel is one input pixel, which Pillow samples exactly.

The tests in `tests/test_pose.py` import `crop_input`, build `_normalised(colour)` as `[(value - mean) / deviation for value, mean, deviation in zip(colour, pose.MEAN, pose.DEVIATION, strict=True)]`, and compare each pixel with `pytest.approx(..., abs=1e-5)`. Each carries `placement-proposal:pose:the-estimator-reads-the-crops-pixels-normalised`.

| test | the image and crop | holds |
|---|---|---|
| the crop is cut from the image where the box is | a 6 by 4 image, columns 0 to 2 `(200, 100, 50)` and 3 to 5 `(10, 20, 30)`; crop `(2, 0, 6, 4)`, size `(4, 4)` | shape `(1, 3, 4, 4)`, dtype `float32`; column 0 is `_normalised((200, 100, 50))` and columns 1 to 3 are `_normalised((10, 20, 30))` |
| a crop that leaves the image is black there | a solid 6 by 4 image `(200, 100, 50)`; crop `(-2, -1, 2, 3)`, size `(4, 4)` | row 0 and columns 0 and 1 are `_normalised((0, 0, 0))`, and the pixel at row 1, column 2 is `_normalised((200, 100, 50))` |

### D9

| requirement | scenario added | key |
|---|---|---|
| `tagging` · *The model and its label index are verified together or not used* | a vector that disagrees with the index is refused | `tagging:pin:a-vector-that-disagrees-with-the-index-is-refused` |
| the same | the graph is opened only after both digests verify | `tagging:pin:the-graph-is-opened-only-after-both-digests-verify` |
| `tagging` · *The tagger is an injectable seam with an offline stand-in* | a photograph is prepared by the graph's rule | `tagging:seam:the-photograph-is-prepared-by-the-graphs-rule` |
| `tagging` · *Each tagger's failure is its own, and the local tagger runs first* | a photograph that will not decode is a local failure | `tagging:order:a-photograph-that-will-not-decode-is-a-local-failure` |
| `model-provisioning` · *A source is checked before a large transfer begins* | the published digest is read from the source's answer | `model-provisioning:preflight:the-published-digest-is-read-from-the-sources-answer` |
| `placement-proposal` · *A person's pose is read from one box and one crop* | the estimator reads the crop's pixels, normalised | `placement-proposal:pose:the-estimator-reads-the-crops-pixels-normalised` |
| `caption` · *A hosted model that is not running or not installed is refused before any attempt is spent* | a host that answers with a status is reachable | `caption:reachability:a-host-that-answers-with-a-status-is-reachable` |

Each requirement's text is the living one, unchanged; the delta is a MODIFIED block because it adds scenarios. The tests with no scenario of their own carry a key that stands:

| test | key it carries | because |
|---|---|---|
| each half of the pin planted wrong | `tagging:pin:the-label-index-and-the-model-are-verified-together` | the model file or the label index, either, is the scenario's own WHEN |
| `post` and `ask` over a 404 | `caption:reachability:absent-model-names-how-to-create-it` | the host reports that the model does not exist |

### D10

The change's mutants are in [mutants.json](mutants.json), each `tests` naming its file.

The audit's are `BD-1`, `BD-2a`, `BD-2b`, `BD-3a`, `BD-3b`, `BD-6`, `BD-10a` and `BD-10b`, their finds unchanged, because no phase edits those lines. The audit gave the replay `"covering"` for most; the replay refuses it, so each names its file.

This change adds `BD-1b` for the conversion of [D2](#d2), `BD-6b` for the probe's answered status, and `P6` for the refusal of [D4](#d4).

## Tests

Every case is a unit test: no browser, no end-to-end test is added, and none runs on an engine. The tests each file holds at the cut, by `git grep -c -E '^def test_' -- <file>`, and what it gains:

| file | tests at the cut | gains | phase |
|---|---|---|---|
| `tests/test_wd14.py` | 24 | the pin planted wrong on each half, in place; the length tests rebound | 1 |
| `tests/test_tagging.py` | 37 | a pin that does not match; a photograph that will not decode | 1, 2 |
| `tests/test_pipeline_cli.py` | 50 | `prepare` over a pin that does not match | 1 |
| `tests/test_wd14_runtime.py` | new | the preparation twice; the opener over a stub twice; one tiny graph through the real runtime | 3 |
| `tests/test_provision.py` | 38 | the published digest read from a redirect, from a response, refused as none, and the redirect kept | 4 |
| `tests/test_ollama.py` | 16 | `post` over a status; `ask` over a 404; `probe` over an answer | 4 |
| `tests/test_pose.py` | 15 | the crop by value, inside and past the image | 4 |

A new test that runs over five seconds carries the `slow` marker, which `make check` skips; none is expected, as no child process starts and the real runtime opens a tiny model.

The patch ratchet gains no row: the patched modules `isekai.interface.wiring`, `isekai.boundary.wd14`, `isekai.boundary.provision` and `isekai.boundary.ollama` are listed, and a string patch of `urllib.request.build_opener` names no module of the repository.

`tests/mutants.json` is not a test and is not in the gate; `make mutants` replays it. The mutants, and the test file that must kill each:

| mutant | where | killed by |
|---|---|---|
| `BD-1` | `isekai/boundary/wd14.py` `verified_paths`, the label index's digest | `tests/test_wd14.py` |
| `BD-1b` | `isekai/interface/wiring.py` `tagger_for`, the conversion | `tests/test_tagging.py` |
| `BD-2a` | `isekai/boundary/provision.py` `published_digest`, the quotes | `tests/test_provision.py` |
| `BD-2b` | `isekai/boundary/provision.py` `published_digest`, the redirect's header | `tests/test_provision.py` |
| `BD-3a` | `isekai/boundary/pose.py` `crop_input`, the mean | `tests/test_pose.py` |
| `BD-3b` | `isekai/boundary/pose.py` `crop_input`, the offset | `tests/test_pose.py` |
| `BD-6` | `isekai/boundary/ollama.py` `post`, the answered status | `tests/test_ollama.py` |
| `BD-6b` | `isekai/boundary/ollama.py` `probe`, the answered status | `tests/test_ollama.py` |
| `BD-10a` | `isekai/boundary/wd14.py` `prepare`, the blue-first flip | `tests/test_wd14_runtime.py` |
| `BD-10b` | `isekai/boundary/wd14.py` `open_session`, the order | `tests/test_wd14_runtime.py` |
| `P6` | `isekai/boundary/wd14.py` `prepare`, the refusal | `tests/test_tagging.py` |

No test is deleted or merged, so no row maps one test to another.

## Dependencies

None.

## Risks / Trade-offs

- **The tiny graph is hand-built.** Its bytes were not run against `onnxruntime` at the cut. The first run of its test is the proof; a runtime that refuses the bytes is a plan halt, and the builder's `ir_version` or opset is the place to look.
- **The first real-runtime test in CI.** It is the suite's first import of `onnxruntime` there: the wheel for `cp312` on `manylinux_2_28_x86_64` is locked, and the import costs about a second. `OnnxSession` silences the runtime's telemetry before the import, and each test undoes the switch.
- **A refusal keeps the opener's result.** `_once` keeps `tagger_for`'s refusal for the invocation, as it keeps an absent file's, so a swapped file is reported once for the batch.
- **`evaluation/recall.py` keeps a dead catch.** Its `UNDECODABLE` still covers a session double that raises the raw errors, and the real preparation now raises a `Refusal` its `read` lets through; `tests/test_recall.py` holds both.
- **A `find` that moves makes the replay refuse.** Phases 1 to 3 write each product line of [D2](#d2) and [D4](#d4) as quoted, so phase 5's finds stand; its first tasks check them.
- **Bilinear sampling at the crop's edge.** [D8](#d8)'s crops keep whole-pixel offsets at scale one, where Pillow reads exact pixels, and the tests look at no pixel on a seam.

## Verdict

Ready to build. Each phase ends on a green `make gate`, and phase 5 on a replay with no survivor. Nothing is irreversible: no format version, requirement text or decision moves, no image-frozen file is edited, and each product edit is a few lines under a requirement that stands.
