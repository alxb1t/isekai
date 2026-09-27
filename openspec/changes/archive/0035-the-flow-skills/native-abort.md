# The tagger's native abort — before and after

Whether `tag` still exits 134 after writing everything, measured by the loop that reproduced it ([D5](design.md#d5)).

**The loop**, on the operator's machine, Ollama and WD14 local, one synthetic portrait
(`.data/inputs/synthetic/synthetic_portrait_00003_.png`), run once by path to open the run, then by id until the first
exit 134, at most twenty times:

```
uv run python -m isekai tag --new-version --flow summon-anime-wai \
  --runs .data/0035-native-abort/runs 0d4b7e6fb2a8_synthetic-portrait-00003
```

Before: 7 runs, 1 exited 134

The 7th run wrote both lists (`wd14 wrote 008.json`, `tags wrote 008.json`), then:
`libc++abi: terminating due to uncaught exception of type std::__1::system_error: recursive_mutex lock failed: Invalid argument`.

**The cause** was onnxruntime's telemetry client, not the session: see [D5](design.md#d5). **The fix** sets
`ORT_DISABLE_TELEMETRY=1` before onnxruntime is imported. The same loop, run 40 times rather than stopping at the
first abort, with each run's sockets sampled by `lsof` every 0.2 s:

After: 40 runs, 0 exited 134

Every run's only remote endpoint was `127.0.0.1:11434`, Ollama on loopback. The spike, for comparison: with the
`disable_telemetry_events()` API instead, 5 of 40 exited 134; `import onnxruntime` alone connected to a Microsoft
Corporation address on 3 of 3 runs, and on 0 of 4 with the switch set.
