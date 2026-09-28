# Tasks — 0037 the boundaries

The transport first, then the review surface, the run frame and the render session, each with its scenarios; one
metered session proves them together, per [design](design.md).

## Progress

- [x] 1 — The transport
- [x] 2 — The review surface
- [x] 3 — The run frame
- [ ] 4 — The render session
- [ ] 5 — 🛑 **HUMAN · METERED** — one render session with a dead `http_proxy` exported

Line numbers are `fcb5e3b`'s; find each site by the text [design](design.md) names. Every new test carries
`@pytest.mark.spec` with the key its task names, and every text-check test has a twin.

## 1 — The transport

- [x] 1.1 **HALT CHECK** — the client calls `request.urlopen` directly, with no proxy handler and no timeout.
  Verify: `grep -c 'request.urlopen(' isekai/boundary/comfy/client.py` prints `5`, and `grep -c -e 'ProxyHandler' -e 'timeout' isekai/boundary/comfy/client.py` prints `0`.
- [x] 1.2 Add `OPENER` and `TIMEOUT = 60` to `isekai/boundary/comfy/client.py`, send every call through `OPENER.open(…, timeout=TIMEOUT)`, and give a timeout its own transient refusal, per [D1](design.md#d1) and [D2](design.md#d2).
  Verify: `grep -c 'request.urlopen(' isekai/boundary/comfy/client.py` prints `0`, `grep -c 'OPENER.open(' isekai/boundary/comfy/client.py` prints `5`, and `grep -c 'did not answer within' isekai/boundary/comfy/client.py` prints `1`.
- [x] 1.3 Add `stub_comfy` to `tests/fakes.py` and move the `urllib.request.urlopen` stubs in `tests/test_generate.py` and `tests/test_resume.py` onto it; make the guards in `tests/test_sheet_stage.py` and `tests/test_pipeline_cli.py` stub it too, per [D1](design.md#d1).
  Verify: `cat tests/test_generate.py tests/test_resume.py | grep -cF 'setattr(urllib.request, "urlopen"'` prints `0`, and `grep -l stub_comfy tests/test_sheet_stage.py tests/test_pipeline_cli.py | grep -c .` prints `2`.
- [x] 1.4 Add `test_no_proxy_in_the_environment_reaches_the_rendering_endpoint` (`comfy-transport:proxy:an-exported-proxy-is-ignored`) and `test_an_unanswered_request_is_refused_transient` (`comfy-transport:timeout:an-unanswered-request-is-transient`) to `tests/test_generate.py`, per [D1](design.md#d1) and [D2](design.md#d2).
  Verify: `grep -c -e '^def test_no_proxy_in_the_environment_reaches_the_rendering_endpoint' -e '^def test_an_unanswered_request_is_refused_transient' tests/test_generate.py` prints `2`.
- [x] 1.5 Add D6's sentence on the ComfyUI transport to `docs/decisions.md`, with `0037` in its *Made by*, per [D1](design.md#d1).
  Verify: `grep -c "The ComfyUI transport ignores the environment's proxy the same way" docs/decisions.md` prints `1`.
- [x] 1.6 Add `RENDER_DEADLINE = 600` and the `deadline` parameter to `isekai/pipeline/generate.py`, refuse a non-string prompt id in `submit`, and quote the id in `history`, per [D3](design.md#d3); add `test_an_unfinished_prompt_is_refused_at_the_deadline` and `test_a_prompt_id_that_is_not_a_string_is_refused` to `tests/test_generate.py`.
  Verify: `grep -c '^RENDER_DEADLINE = 600' isekai/pipeline/generate.py` prints `1`, and `grep -c -e '^def test_an_unfinished_prompt_is_refused_at_the_deadline' -e '^def test_a_prompt_id_that_is_not_a_string_is_refused' tests/test_generate.py` prints `2`.
- [x] 1.7 Draw the multipart boundary and escape names in `isekai/boundary/comfy/multipart.py`, per [D4](design.md#d4); add `test_the_boundary_appears_in_no_part` and `test_names_are_escaped` to `tests/test_multipart.py`.
  Verify: `grep -c 'convertpyBoundary' isekai/boundary/comfy/multipart.py` prints `0`, and `grep -c -e '^def test_the_boundary_appears_in_no_part' -e '^def test_names_are_escaped' tests/test_multipart.py` prints `2`.
- [x] 1.8 Keep printable characters only in `_error_body`, per [D5](design.md#d5); add `test_an_error_body_loses_its_control_characters` (`comfy-transport:error-text:control-characters-are-dropped`) to `tests/test_generate.py`.
  Verify: `grep -c 'isprintable' isekai/boundary/comfy/client.py` prints `1`, and `grep -c '^def test_an_error_body_loses_its_control_characters' tests/test_generate.py` prints `1`.

## 2 — The review surface

- [x] 2.1 Check every read in `read_input`, `_wd14` and `_tags` in `isekai/interface/ui/app.py` and refuse with the remedies [D6](design.md#d6) lists; add `test_a_damaged_file_is_refused_by_name` (`ui:damage:a-damaged-file-is-refused-by-name`) to `tests/test_ui_api.py`, over the draft, the approved sheet, the caption and both tag lists.
  Verify: `grep -cF 'read(approved, APPROVED_FILE)["fields"]' isekai/interface/ui/app.py` prints `0`, and `grep -c '^def test_a_damaged_file_is_refused_by_name' tests/test_ui_api.py` prints `1`.
- [x] 2.2 Check `put_draft`'s body before the lock, per [D6](design.md#d6); add `test_a_malformed_update_is_refused_naming_the_field` (`ui:damage:a-malformed-update-is-refused-naming-the-field`) to `tests/test_ui_api.py`, with a tag list sent as a string among its cases.
  Verify: `grep -cF '[str(tag) for tag in tags]' isekai/interface/ui/app.py` prints `0`, and `grep -c '^def test_a_malformed_update_is_refused_naming_the_field' tests/test_ui_api.py` prints `1`.

## 3 — The run frame

- [x] 3.1 Check the frame in `Run.photo` and `_run_for` in `isekai/foundation/run.py`, per [D7](design.md#d7); add `test_a_name_that_leaves_the_run_is_refused` (`run-directory:frame:a-name-that-leaves-the-run-is-refused`) and `test_a_frame_without_its_photograph_is_refused` (`run-directory:frame:a-frame-without-its-photograph-is-refused`) to `tests/test_run_directory.py`.
  Verify: `grep -cF 'self.path / str(self.frame["photo"]["name"])' isekai/foundation/run.py` prints `0`, and `grep -c -e '^def test_a_name_that_leaves_the_run_is_refused' -e '^def test_a_frame_without_its_photograph_is_refused' tests/test_run_directory.py` prints `2`.

## 4 — The render session

- [ ] 4.1 **HALT CHECK** — the watchdog sleeps once, the tunnel uses the operator's known hosts, and the checks follow a proxy.
  Verify: `grep -cF 'sleep "$CEILING"' infra/render.sh` prints `1`, and `grep -c -e 'UserKnownHostsFile' -e 'noproxy' infra/render.sh` prints `0`.
- [ ] 4.2 Make the watchdog in `infra/render.sh` poll per [D8](design.md#d8); in `tests/test_infra.py`, make `unbounded_session` look for `end=$((SECONDS + CEILING))`, and add `test_the_watchdog_ends_with_its_session` (`pod-image:session:the-watchdog-ends-with-its-session`).
  Verify: `grep -cF 'sleep "$CEILING"' infra/render.sh` prints `0`, `grep -cF 'kill -0 $$ 2>/dev/null || exit 0' infra/render.sh` prints `2`, and `grep -c '^def test_the_watchdog_ends_with_its_session' tests/test_infra.py` prints `1`.
- [ ] 4.3 Give each session its own known-hosts file in `infra/render.sh` per [D9](design.md#d9); add `test_a_sessions_host_keys_are_its_own` (`pod-image:session:host-keys-are-the-sessions-own`) to `tests/test_infra.py`.
  Verify: `grep -cF 'UserKnownHostsFile="$known_hosts"' infra/render.sh` prints `1`, `grep -cF 'rm -f "$up_out" "$known_hosts"' infra/render.sh` prints `1`, and `grep -c '^def test_a_sessions_host_keys_are_its_own' tests/test_infra.py` prints `1`.
- [ ] 4.4 Pass `--noproxy '*'` to every `curl` in `infra/render.sh` that names `$SERVER`, per [D11](design.md#d11); add `test_the_session_reaches_its_tunnel_without_a_proxy` (`pod-image:session:the-tunnel-is-reached-directly`) to `tests/test_infra.py`.
  Verify: `grep -F '"$SERVER' infra/render.sh | grep -F 'curl' | grep -vcF -- "--noproxy '*'"` prints `0`, and `grep -c '^def test_the_session_reaches_its_tunnel_without_a_proxy' tests/test_infra.py` prints `1`.

## 5 — 🛑 **HUMAN · METERED** — one render session with a dead `http_proxy` exported

**Ceiling: 45 minutes and ~$0.30; planned at about 15 minutes and ~$0.10.** The pod goes up and down only through
`infra/render.sh`, which runs `infra/up.sh` and `infra/down.sh`; the RunPod MCP confirms it gone. A synthetic
portrait only, per [D10](design.md#d10).

- [ ] 5.1 The operator puts one synthetic portrait in `.data/v0.26/photos/`, exports `http_proxy=http://127.0.0.1:9` with `https_proxy` unset, and runs the `run-flows` skill over both flows: approves the sheets, then says go.
  Verify: `ls .data/v0.26/runs/*/summon-anime-wai/outputs/*.png .data/v0.26/runs/*/conjure-anime-wai/outputs/*.png` lists a render for each flow, and `grep -c '^refused' .data/v0.26/log.txt` prints `0`.
- [ ] 5.2 Record the session in `openspec/changes/0037-the-boundaries/acceptance.md`: the command, the renders, the exported proxy, and the RunPod MCP's answer that no pod is left.
  Verify: `grep -c -e 'http_proxy=http://127.0.0.1:9' -e 'pods: \[\]' openspec/changes/0037-the-boundaries/acceptance.md` prints `2`.
