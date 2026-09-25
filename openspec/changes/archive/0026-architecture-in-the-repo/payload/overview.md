# isekai — architecture

A photograph of a person goes in, and an anime image of that same person comes out (`summon`); or a
character is drawn from a corrected sheet alone (`conjure`). Self-hosted, on open models only (D0).

```
 operator — one verb at a time
     │
 ┌───▼─ interface ──────────────────────────────────────┐
 │  CLI  python -m isekai        review UI  isekai ui   │
 │  the CLI builds them through wiring.py for both      │
 └───┬────────────────────────────────┬─────────────────┘
     ▼                                ▼ stage ③ only
 ┌─ pipeline ───────────────────────────────────────────┐
 │  ① caption   ② sheet   ③ review · approve  ④ generate │
 └───┬──────────────────────────────────────────────┬───┘
     │ each stage reads and writes only              │
     ▼                                               │
 ┌─ the run directory — the only channel ─────┐      │
 │  runs/<input>/<flow>/<stage>/              │      │
 └────────────────────────────────────────────┘      │
 ┌─ boundary — every way out ───────────────────────▼───┐
 │  Ollama: JoyCaption   WD14: local ONNX   ComfyUI: pod │
 └───────────────────────────────────────────────────────┘
```

| file | answers |
|---|---|
| [principles](principles.md) | the rules every component follows |
| [decisions](decisions.md) | the choices in force, and why |
| [modules](modules.md) | the layers, and which module imports which |
| [data-flow](data-flow.md) | the verbs, the stages, the run directory |

Evaluation, a separate sub-system, is not covered here yet.
