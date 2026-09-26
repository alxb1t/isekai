Go: 2026-09-26

# Acceptance — 0032 the tag verb

Phase 6, run on the operator's machine: Ollama and WD14 local, no pod. One synthetic portrait,
`.data/v0.23/photos/00_00_warm_lamplit_interior_portrait.png`. Runs root `.data/v0.23/runs`, and
`.data/v0.23/runs-fresh` for the sheet-before-tag check.

Run id: `682398a521c1_00-00-warm-lamplit-interior-port`.

## 6.2 — both flows: `tag`, `caption`, `sheet`, `ui`

```
$ python -m isekai tag --flow summon-anime-wai --flow conjure-anime-wai --runs .data/v0.23/runs .data/v0.23/photos/00_00_warm_lamplit_interior_portrait.png
682398a521c1_00-00-warm-lamplit-interior-port: wd14 wrote 001.json
682398a521c1_00-00-warm-lamplit-interior-port: tags wrote 001.json
682398a521c1_00-00-warm-lamplit-interior-port: wd14 wrote 001.json
682398a521c1_00-00-warm-lamplit-interior-port: tags wrote 001.json
exit 0

$ python -m isekai caption --flow summon-anime-wai --flow conjure-anime-wai --runs .data/v0.23/runs .data/v0.23/photos/00_00_warm_lamplit_interior_portrait.png
682398a521c1_00-00-warm-lamplit-interior-port: caption wrote 001.json
682398a521c1_00-00-warm-lamplit-interior-port: caption wrote 001.json
exit 0

$ python -m isekai sheet --flow summon-anime-wai --flow conjure-anime-wai --runs .data/v0.23/runs .data/v0.23/photos/00_00_warm_lamplit_interior_portrait.png
682398a521c1_00-00-warm-lamplit-interior-port: sheet wrote 001.json
682398a521c1_00-00-warm-lamplit-interior-port: sheet wrote 001.json
exit 0
```

`ui`, once per flow, each queried at `GET /api/inputs/<run>` and then stopped:

| command | `caption` | `caption_command` | WD14 chips | offered chips | filled fields |
|---|---|---|---|---|---|
| `python -m isekai ui --flow summon-anime-wai --runs .data/v0.23/runs 682398a521c1_00-00-warm-lamplit-interior-port` | the prose | `null` | 39 | 5 | 11 |
| `python -m isekai ui --flow conjure-anime-wai --runs .data/v0.23/runs 682398a521c1_00-00-warm-lamplit-interior-port` | the prose | `null` | 39 | 5 | 13 |

## 6.3 — Ollama stopped; sheet before tag

A first attempt to quit the Ollama app was cancelled, so Ollama stayed up; the `tag --new-version`
run that followed wrote `002.json` for both lists of both flows, with Ollama answering. It is not
evidence for this check.

**Ollama stopped** — the operator quit it from the menu bar, and nothing answered at
`127.0.0.1:11434`. WD14 is written for both flows; only the JoyCaption lists are refused, and no
error record is written under `tags/`, so no attempt was spent:

```
$ python -m isekai tag --flow summon-anime-wai --flow conjure-anime-wai --new-version --runs .data/v0.23/runs 682398a521c1_00-00-warm-lamplit-interior-port
refused: nothing is listening at http://127.0.0.1:11434, and the reader and the JoyCaption tagger need it; start the runtime (`ollama serve`), then run this command again
refused: nothing is listening at http://127.0.0.1:11434, and the reader and the JoyCaption tagger need it; start the runtime (`ollama serve`), then run this command again
682398a521c1_00-00-warm-lamplit-interior-port: wd14 wrote 003.json
682398a521c1_00-00-warm-lamplit-interior-port: wd14 wrote 003.json
exit 1
```

After it: each flow's `wd14/` holds `001.json 002.json 003.json`, and each `tags/` holds
`001.json 002.json`. The refusals print first because they go to stderr unbuffered.

`caption`, with Ollama still stopped, refuses and writes nothing:

```
$ python -m isekai caption --flow summon-anime-wai --new-version --runs .data/v0.23/runs 682398a521c1_00-00-warm-lamplit-interior-port
refused: nothing is listening at http://127.0.0.1:11434, and the reader and the JoyCaption tagger need it; start the runtime (`ollama serve`), then run this command again
exit 1
```

Sheet before tag, on a fresh run — refused, naming `tag`:

```
$ python -m isekai sheet --flow summon-anime-wai --flow conjure-anime-wai --runs .data/v0.23/runs-fresh .data/v0.23/photos/00_00_warm_lamplit_interior_portrait.png
refused: 682398a521c1_00-00-warm-lamplit-interior-port: there is no tag list to fill a sheet for summon-anime-wai from; run `python -m isekai tag --flow summon-anime-wai 682398a521c1_00-00-warm-lamplit-interior-port` first, which writes summon-anime-wai/wd14/
exit 1
```

Then `tag` and `sheet` on that run, and `ui` on a run never captioned:

```
$ python -m isekai tag --flow summon-anime-wai --runs .data/v0.23/runs-fresh .data/v0.23/photos/00_00_warm_lamplit_interior_portrait.png
682398a521c1_00-00-warm-lamplit-interior-port: wd14 wrote 001.json
682398a521c1_00-00-warm-lamplit-interior-port: tags wrote 001.json
libc++abi: terminating due to uncaught exception of type std::__1::system_error: recursive_mutex lock failed: Invalid argument
exit 134

$ python -m isekai sheet --flow summon-anime-wai --runs .data/v0.23/runs-fresh .data/v0.23/photos/00_00_warm_lamplit_interior_portrait.png
682398a521c1_00-00-warm-lamplit-interior-port: sheet wrote 001.json
exit 0
```

`python -m isekai ui --flow summon-anime-wai --runs .data/v0.23/runs-fresh 682398a521c1_00-00-warm-lamplit-interior-port`
served the input with `caption: null` and `caption_command:
"python -m isekai caption --flow summon-anime-wai 682398a521c1_00-00-warm-lamplit-interior-port"`.

## Findings

- **The native abort at exit kills the process.** The `CHANGELOG.md` 0.22.x entry left open whether
  it aborted; it does: exit 134, after every artifact was written. Seen on 2 of about 11 `tag`
  invocations here. Not introduced by this change; not fixed by it.
- **A refusal on a multi-flow `sheet` names only the first flow.** `across` collects per input, so
  `conjure-anime-wai`'s refusal was never reached. The remedy printed is still correct for the flow it
  names.
- **Printed commands name the run but not `--runs`.** Pasted as printed for a run under a non-default
  runs root, they look for the run under `.data/runs` and are refused. True of every refusal remedy
  and of `caption_command`.
