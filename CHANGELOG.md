# Changelog

Notable changes, per [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0/).

A version's heading names its change: `## [0.25.0] - 2026-09-27 · 0035-the-flow-skills`. A bullet is one change
an operator notices, in 1–3 short lines — what changed and why — ending with its design id, `(0035 D2)`. It holds
no figure, file:line reference or pod id; a re-pinned flow's bullet names its new digest.

## [Unreleased]

- A render session's record plans each photograph's images per flow, and its page is a grid of flows over the
  photographs, waiting tiles for what is to come, moved by `h j k l` with `↵` opening the row (0076 D7).

- `c` on any large view picks another image of its cell in the viewer, any version or seed; Compare sets the older
  before and names when the seeds differ or the sheets are the same. The Render dialog closes when its page is left
  (0076 D2, D4).

- On macOS, `⌃H` `⌃L` move between Review's panes from a field. On Renders, `h l` step images as the arrows do,
  crossing cells and reaching the source, whose `↵` opens its photograph; `j k` keep the column (0076 D1, D6).

- The hub's source cell is a column — name and file level with the tick line, the thumbnail below — and long
  source and batch names wrap inside their columns. No screen draws a key bar; the app bar's `?` opens the key
  list (0076 D3, D5).

## [0.48.0] - 2026-10-24 · 0075-the-walkthrough

Gate: local 0m41s · CI 7m25s (build-image at 801ffec) · 0.47.0: local 0m42s · CI 7m25s

### Changed

- Home's batch row reads as one header line — name, sources, flow chips and last activity — with its thumbnails
  below at the full width (0075 D1).

- The hub's source cell is its grid's first column: `h` reaches it and `↵` opens the batch's photographs in the
  viewer (0075 D3).

- A rendered hub cell shows every image it holds, each marked with its version; a click or `↵` opens the viewer on
  the newest, whose `↵` opens its large view. Each version's outputs are listed once (0075 D5).

- The hub and Renders keep their focus for the open batch: `Esc` from a large view, the Back button and a tab switch
  come back to the cell or image left, else the first (0075 D4).

- An image's large view offers *Side by side* on `⇧C`: the image beside its run's photograph at equal height (0075 D2).

- Review's rail names each other flow holding unapproved sheets, with how many, and `⇧F` opens the next one's first;
  the design spec draws the walkthrough's screens and one job-strip dot (0075 D6, D7).

## [0.47.0] - 2026-10-24 · 0074-two-job-slots

Gate: local 0m42s · CI 7m25s (build-image at 801ffec) · 0.46.0: local 0m40s · CI 7m25s

### Changed

- The app's job runner holds a Prepare and a render side by side, each refused, stopped and waited for in its own
  slot; stopping the app interrupts both, and each line in a batch's log names its job (0074 D1–D3).

- The event stream's snapshot carries both slots as `jobs`, Stop is `POST /api/jobs/{kind}/stop`, and a running
  Prepare no longer holds Render back (0074 D4).

- Every screen reads its own slot: a hub's Prepare bar its batch's Prepare, the Render bar and the session page the
  render; the hub no longer holds Prepare while a render runs, another batch's Prepare disables it with its reason,
  and the job strip shows each running job (0074 D5).

- The design spec's rule 6 and §8, the READMEs and `docs/data-flow.md` state two job slots; the session outcome's
  comment names its lifetime lock, and the `render.py` row names every importer (0074 D6).

## [0.46.0] - 2026-10-24 · 0073-sessions

Gate: local 0m40s · CI 7m25s (build-image at 801ffec) · 0.45.0: local 0m39s · CI 7m25s

### Added

- `isekai render` keeps its session's record beside the batch's log, `sessions/<id>.json`, from the pod's ask to its
  end: its steps, each image as it lands, and how it ended. `--session ID` names it (0073 D1, D2).

- The app serves a batch's sessions and each one from its records, the running one first; the render job names its
  session, and a window opening that raises marks its step failed rather than running (0073 D3, D7).

- Each batch has a Sessions tab: its sessions listed from their records and a page per session, so a finished one is
  found again. A running render shows on every screen, and the billing alert's way out is `/billing` (0073 D4, D5).

- A session's finished images and the batch's photographs open in the viewer, drawn at the Renders tile size; the
  viewer follows its list as a live session adds to it (0073 D6).

### Changed

- The README, the design spec, Review's comment and the cancel's docstring say what a cancel does: `--from` copies the
  source's newest approval again, and a copy's cancel leaves the sheet on what the flow holds (0073 D7).

### Fixed

- Session ids refuse collisions without losing history; terminal renders stay live across the app, list refreshes
  preserve progress, the viewer keeps image identity, and Billing distinguishes open and unknown states (0073 D8–D11).

- A damaged session record refuses only its own batch, a failed running read is shown as unconfirmed and never hides
  the billing alert, and a sessions folder without hard links or locks refuses before the pod ask (0073 D8–D10).

## [0.45.0] - 2026-10-24 · 0072-cancel-approve

Gate: local 0m39s · CI 7m25s (build-image at 801ffec) · 0.44.1: local 0m38s · CI 7m25s

### Added

- The review stage can cancel an approval nothing was made from, writing back its draft; a prompt, a render group,
  a failure record or a copy in another flow refuses it, naming the way on (0072 D1, D2, D3).

- `isekai approve --cancel` takes each named run's approval back, each run answered on its own; beside
  `--from` it is refused before any run is read (0072 D4).

- Review's approve bar offers *Cancel approve* on an approved sheet, which opens it again, editable; disabled, it
  says why — something made from it, or a render running. A refused discard no longer outlives a reload (0072 D5, D6).

- A copy's cancel deletes it, and its source's refusal names that cancel, so the two no longer send the operator to
  each other; a cancel refused for what derives names a waiting draft rather than its discard (0072 D2, D3).

- A copy cancelled over a flow's own approval leaves that approval standing, and the CLI line and Review's approve
  bar name it, so a sheet still approved after a cancel says which approval it shows (0072 D3, D5).

## [0.44.1] - 2026-10-24 · 0071-the-review-patch

Gate: local 0m38s · CI 7m25s (build-image at 801ffec) · 0.44.0: local 0m40s · CI 7m25s

### Fixed

- The README and Review's comments say what Review does: Approve stays on the sheet, Revise opens its first draft
  with the others of its flow in the rail, and refusals land in the approve bar (0071 D2).

- A test opens a batch's Review address: it lands on its head's sheet, and a batch with none waiting says so
  (0071 D3).

## [0.44.0] - 2026-10-23 · 0070-review

Gate: local 0m40s · CI 7m25s (build-image at 801ffec) · 0.43.0: local 0m39s · CI 7m25s

### Changed

- A batch's Review has its own address, `/b/<batch>/review`, which opens its head; the Review tab counts the
  unapproved sheets, and the hub's *Review next* is gone. Each hub cell carries what its approval lacks (0070 D1, D2).

- Approve stays on the sheet, read-only, and Discard stays too; Review's rail, headed by its flow, lists every
  sheet not yet rendered. Revise opens its first draft, the rest in the rail. An approval waits for a save in
  flight (0070 D3, D4, D9).

- Review's old header is gone: the save and approval times sit in ③'s kicker, every refusal in the approve bar,
  and no file name shows. A revision's photograph and render share one header row at one height; Discard asks
  from the approve bar (0070 D5, D6, D9).

- ④ is one slot per image, a seed or random, in a panel right of the sheet rows; a typed seed sets its slot at
  once, and a seed listed twice is refused, by the slot and by approval (0070 D7).

- Review's photograph opens in the viewer, `←` `→` stepping the rail's photographs, and a revision's render opens
  there too; *Side by side* `⇧C` shows the pair at one height. The photo overlay is gone (0070 D8).

## [0.43.0] - 2026-10-23 · 0069-the-keys

Gate: local 0m39s · CI 7m25s (build-image at 801ffec) · 0.42.0: local 0m36s · CI 7m25s

### Changed

- Every key is declared once in a key store with one listener; none fires in a text field, `Esc` leaves
  the field first, and `?` lists the keys. The shell's keys are `⇧L` `⇧H` `⇧R` `⇧I` `⇧S` (0069 D1–D3, D6, D8).

- Home, the hub, Renders, the large view, Compare and the session declare their keys, each with a key bar:
  `h j k l` move, `⇧N` `⇧A` `⇧G` act, and `e` revises; Renders' `h l` step cells, its arrows images (0069 D4, D6).

- Review moves between the rail, the photograph, the sheet and ④ with `h` `l`, walks each with `j` `k`,
  and steps sheets with `⇧J` `⇧K`; the tag cheatsheet opens on `Mod+K`, which Linux does not take (0069 D4, D5).

- The import sheet, the Render dialog, the Revise confirm and the viewer take the keys over their screen; a
  commit in flight holds the import sheet, its Cancel and `Esc` with it (0069 D4, D7).

## [0.42.0] - 2026-10-23 · 0068-the-store

Gate: local 0m36s · CI 7m25s (build-image at 801ffec) · 0.41.0: local 0m37s · CI 7m25s

### Changed

- The page's job slot, billing and clock live in one Pinia store, `pinia` and `@vue/devtools-api` pinned
  exactly; stopping a job and checking billing are its actions (0068 D1, D2).

- A page holds one event stream, naming its batch and its open import, and opens it again when either
  changes; the hub and the import sheet no longer open their own (0068 D3).

- The open batch's hub, running cells, renders and Render offer live in one store, so Review and Renders
  follow Prepare as the hub does; an offer answered after a newer one is dropped (0068 D4, D5, D7).

- Each upload keeps its own state under the id its upload answers, so two files of one name are two
  tiles; Import seals the reader, so an upload after it is refused rather than dropped (0068 D6, D7).

## [0.41.0] - 2026-10-23 · 0067-hub-and-renders

Gate: local 0m37s · CI 7m25s (build-image at 801ffec) · 0.40.1: local 0m35s · CI 7m25s

### Added

- The hub shows each source's thumbnail, upright, and its size read from its own file, run or none; the
  thumbnail opens the source in a viewer dialog, fitted, a click for 1:1 (0067 D1, D2, D3).

- Home's row shows its first sources' thumbnails, then `+n`, and *New batch* sits in the library's header
  row, or under the privacy line on a first start (0067 D3, D10).

- A Render bar on the hub and Renders counts the images ready to render, the render stage's own count, and
  replaces the header's Render button; a hub opened after a failed Prepare shows its message (0067 D6, D10).

- A running Prepare or Render bar draws a sliding accent line and its running segment pulses; reduced motion
  stops both and the import bar's fill (0067 D9).

### Changed

- A hub cell does its one thing on a click or `↵`: tick, open Review, or open its newest image's large view,
  whose `Esc` returns to the hub; the double-click is gone (0067 D4, D5).

- The Renders grid reads oldest to newest, a row per cell with `vN` badges and a ready tile counting what the
  newest approval lacks; each version's heading moves to its large view (0067 D7, D8).

- A source's thumbnail on the hub and on Renders is a render tile's size, declared once; Home's are three times
  larger, wrapping in a narrow window (0067 D3).

### Fixed

- A damaged version's images stay drawn beside its striped tile, as the grid's focus moves across them; a hub read
  survives an oddly named or vanished render; a photograph is served as its bytes' image type, `nosniff` (0067 D8).

- A click ticks its own hub cell, a discarded Prepare failure stays dismissed, a refused count keeps the Render bar
  with its reason, a damaged large view says so, and a padded render name is no render (0067 D4, D6, D8, D10).

- A checkbox click ticks its own cell alone; Discard dismisses only its own batch's failure, in that page; one
  seed predicate names a render for the stage, `revise` and the app alike (0067 D4, D10).

## [0.40.1] - 2026-10-23 · 0066-the-quick-patch

Gate: local 0m35s · CI 7m25s (build-image at 801ffec) · 0.40.0: local 0m34s · CI 1m12s

### Fixed

- End event streams before the server’s shutdown wait and return quietly on Ctrl-C after cleanup;
  print the volume recovery command when a close fails after its worker ends (0066 D4, D5).

- Prepare shows sheet-completed cells against its accepted total and a ticking elapsed time in the
  strip and bar; reconnects preserve the counts and original start (0066 D3).

- Use singular count labels at one and leave a consistent gap between hub header controls so
  small batches read correctly and the controls stay spaced (0066 D7).

- Correct the UI child-process and shared-work descriptions, and state the Render quote’s image-total
  and limit boundary so its confirmation claim matches the check (0066 D2, D6).

## [0.40.0] - 2026-10-21 · 0065-revise

Gate: local 0m34s · CI 1m12s (ci at abf4e5e) · 0.39.1: local 0m29s · CI 0m55s

### Added

- `review.revise` copies the approval an image was rendered under into the next draft, its seed listed, and
  `review.discard` deletes a waiting draft; approval refuses a draft that would only re-render its approval's
  images (0065 D1, D3, D4).
- `isekai revise <image.png> …` checks every image first, then writes a revision for each or none, and
  `isekai review --discard` deletes a flow's waiting draft (0065 D2, D3).
- The app's API revises a selection of images all or none, discards a waiting draft, heads each version a
  revision or a re-roll of the one it came from, and compares a seed with its newest older version; an
  unedited revision of an image already rendered is refused (0065 D4, D5, D6, D7).
- The app revises from an image's large view and over a selection in Renders, opens Review on each draft with
  the render beside the photograph and a `was` line on every changed field, and Compare shows a seed's two
  versions side by side (0065 D7).
- The stream test closes its helper's broadcast in a `finally`, re-raises the helper's failure and uploads
  only after the snapshot is read; the e2e render test no longer re-proves a disabled Render; the README and
  the data flow describe `isekai revise`, `review --discard` and Compare (0065 D8).
- A revision reads every image's approval before writing any draft, so an unreadable one writes nothing; the
  app refuses an image of a flow this build does not track, and its Discard deletes only the draft the page
  last read (0065 D2, D7).
- Revise knows a run by its directory's identity, refuses a version or seed no run can hold, and ends each
  refusal with a command; the app's Discard asks before it deletes and lands a pending save first, and Ctrl+C
  on a large view no longer opens Compare (0065 D2, D7).

## [0.39.1] - 2026-10-21 · 0064-the-import-sheet

Gate: local 0m29s · CI 0m55s (ci at f76c6dc) · 0.39.0: local 0m30s · CI 1m5s

### Changed

- An upload is answered `202` once its bytes land; the import's reader reads its files one at a time and
  reports each on `/events?staging=<id>`, so a tile shows uploading, waiting, converting, then its result
  and the staged file's preview (0064 D1, D2, D3).
- Home's first start reads as the design draws it: the heading, the privacy line, then *New batch*; with a
  batch, *New batch* stays above the list (0064 D4).
- An approval against a stale draft is proved by its own test, and `tests/test_ui_api.py`'s docstring names
  what it proves and the gate's `uv run pytest` rather than counting (0064 D5).

## [0.39.0] - 2026-10-21 · 0063-render

Gate: local 0m30s · CI 1m5s (ci at 7a9a698) · 0.38.0: local 0m29s · CI 1m0s

### Added

- A draft and its approval carry `renders`, a count and seeds, edited in Review's ④; approval refuses a count
  below its seeds or a seed out of range; `render` takes the listed seeds first, and `generate` with no
  `--count` renders the approval's count (0063 D1).
- `isekai render <runs>` with no request renders what each approval lacks of its count; a run without the flow
  is skipped, and an unapproved flow is left out and named, so a draft holds up nothing (0063 D2).
- A session's limit is `--limit` or an estimate from recorded durations, at least the hold plus five minutes;
  gpunit stops the pod at it, and a render records its `duration`. `gpunit.toml` gains a ceiling long enough
  for a large batch, and an hourly maximum that bounds the price (0063 D3, D4).
- `isekai render --progress json` prints a JSON line per step: the pod, each image of the total, the teardown;
  the prose goes to stderr (0063 D5).
- The render job: `POST /api/b/{batch}/render/quote` quotes what renders and its price at most, and
  `POST …/render` opens the volume, runs `render --limit … --progress json` and closes it unless kept (0063 D6, D8).
- Billing is read from gpunit's `.gpunit/` records: the pod alert, the window's item, the band; `POST
  /api/billing/check` asks gpunit again (0063 D7).
- The hub's Render opens a dialog quoting what renders, the limit and the price at most; its confirmation
  opens `/session`, and the shell shows the billing band and the window's item (0063 D8).
- The Renders view lists each source's approvals newest first with their images, and the large view shows an
  image beside its sheet; thumbnails are made once into the library's `.cache/` (0063 D9).
- Proved on a pod: two images rendered from the app inside their quoted limit, each recording its duration, and
  no pod or volume left after (0063 D11).

### Changed

- `CLAUDE.md`'s cost rule, D26 and D36 follow the quote: a session's limit and price, at most `gpunit.toml`'s
  `ceiling` and `max_hourly`; the README and data flow describe rendering from the app (0063 D10).

### Fixed

- From the proof: Render is disabled on the hub with its reason, the session's clock stops at its end and its
  tiles show the renders, Renders takes arrows and ↵, esc leaves the large view, and the log holds each line once (0063 D8, D9).
- From review: `render` logs `generate`'s lines again; a stopped app closes the window after the teardown, and
  Ctrl-C reaches no gpunit verb; a grown quote is refused; a thumbnail is named by its image (0063 D5, D8, D9).
- From the second review: a confirmation carries the images it quoted, a stopping app says it waits and names
  `gpunit volume down` if the wait runs out, a damaged approval costs Renders only its version, and a render job
  or session that fails mid-way reports it (0063 D5, D8, D9).

## [0.38.0] - 2026-10-21 · 0062-run-flow

Gate: local 0m29s · CI 1m0s (ci at ac379cf) · 0.37.0: local 0m22s · CI 0m35s

### Added

- `isekai import --batch <dir> <file…>` cleans photographs into a batch's `sources/`: no metadata but the
  orientation, colour in sRGB, HEIC and other formats converted; a RAW, multi-image or oversized file is refused
  by name, and each file is verified before it is committed (0062 D1, D2, D3).
- `isekai assign --flow F <source…> [--remove]` ticks a flow as its empty directory in the run, and the hub's
  `POST /api/b/{batch}/assign` runs the same function; an untick never deletes work (0062 D4).
- `tag`, `caption` and `sheet` take `--progress json`: a JSON line per item's start, end or refusal on stdout,
  the prose on stderr, so a job reads a format meant for it (0062 D6).
- Prepare runs as a job: `POST /api/b/{batch}/prepare` checks the model server answers, then runs `tag`,
  `caption` and `sheet` as CLI children per flow; Stop and a server stop interrupt it (0062 D7).
- `GET /events` streams a snapshot of the job slot and the batch's hub, then each change as a stage reports it;
  the server sweeps import's leftover staging at start (0062 D1, D8).
- New batch on Home and Add sources on the hub open the import sheet: files chosen in the dialog upload one
  request each with a bar each, show converted, refused or not cleaned, and Import waits for every file (0062 D9).
- The hub ticks: space or a click assigns a flow, ⇧↑↓ selects rows for a column, and the Prepare bar runs what
  changed, its cells moving live from `/events`; a prepared tick stays (0062 D10).
- The docs describe `import`, `assign`, `--progress json`, Prepare and `/events`; D4 now reads that the UI runs
  stages only as the CLI's children, and D43 records that a source holds pixels and orientation only (0062 D11).

### Changed

- The hub's columns and Home's counts are the flows `config/ui.json` offers, so `control-anime-wai` stays the
  CLI's; a source still carrying metadata is marked not cleaned (0062 D5, D10).
- A refusal that asks the operator to fix something and retry ends *"then try again"*, so the page can show it
  verbatim; D42 records that a new draft starts from the last approval (0062 D11).

## [0.37.0] - 2026-10-21 · 0061-ui-groundwork

Gate: local 0m22s · CI 0m35s (ci at 45babd9) · 0.36.0: none

### Added

- A browser test harness: vitest for the page's composables and Playwright from pytest for the page, both in
  the gate, with `make browsers` fetching Chromium; `ISEKAI_WIRING` serves the surface on the suite's doubles
  (0061 D6, D7).
- `isekai/interface/ui/library.py` reads the library: a folder holding `sources/` is a batch, each batch's row
  carries its counts per flow and its newest file, and each source × flow cell its stage, all from listings
  (0061 D1, D2, D4).

### Changed

- **BREAKING:** `isekai ui` takes no arguments and serves the library `ISEKAI_LIBRARY` names, `~/isekai` by
  default; the page is a shell with Home, each batch's hub and Review, every screen at a URL naming its batch
  and its run's digest, on `vue-router` (0061 D1, D3).
- The hub is a read-only grid of a batch's sources by its tracked flows: each cell's stage track and word, an
  unreadable cell's refusal, arrow-key focus, and ↵ to the cell's Review; ⌥0 and ⌥1 reach Home and the hub
  (0061 D4).
- Review is a queue: *Review next* opens the first flow's unapproved sheets in the hub's order, Approve moves to
  the next and to the hub after the last, and opening a sheet with no draft writes one through `review`
  (0061 D5).
- The design spec is `ui/design/spec.md`, replacing the imported design; D4, D18, D19 and D24 are restated
  for the library, D40 and D41 added, and the README, `CLAUDE.md`, `docs/` and `.env.example` moved onto
  `isekai ui` (0061 D10).

### Removed

- **BREAKING:** the `run-flows` and `compare-renders` skills, whose review step cannot follow the library; the
  verbs and `isekai ui` cover a batch (0061 D9).

### Fixed

- The review page's saving state holds a token per save, so an input switch can no longer silence it; the draft
  `PUT` is kept alive, so an edit pending as the tab closes is sent (0061 D8).
- A bundle build past its ceiling stops its whole process group; a request with no `Origin` is refused unless
  `Sec-Fetch-Site` says it came from the page; a missing caption's command names its runs root (0061 D8).
- A refusal reading the next state after an approval shows in the approve bar instead of being dropped
  (0061 D8).

## [0.36.0] - 2026-10-17 · 0060-the-working-window

### Changed

- gpunit is pinned at `v0.7.0`, and the image adds its `boot.sh` from that tag by checksum: `v0.7.0` makes the
  models volume a window and refuses an older boot script (0060 D1).
- `gpunit.toml` declares a working window's volume, 50 GB for up to 4 hours, in place of a kept one that no
  longer existed; a test holds the pair above the pod's floor, and README, D27 and the pins guide say so
  (0060 D2, D3).
- The pod reads `/dev/shm`'s type from the mount its memory directory's device is, says when it cannot read its
  swap table, and moves on at once from a source that answers 4xx; `provision()`'s stale citation goes (0060 D4).
- `run-flows` opens the window with `gpunit volume up` on the go, and asks *another batch?* before it runs
  `gpunit volume down`; `CLAUDE.md`'s GPU protocol names the volume, its teardown and its ceiling (0060 D5).
- The pod image is re-pinned to `v0.36-rc1`, `sha256:21b715d9…bd9a1d3f`, built from this branch with gpunit
  `v0.7.0`'s boot script and the pod's cards; its build record equals `config/image.json`'s `files` (0060 D6).
- A window on `v0.36-rc1` rendered both flows on a pod; the operator judged it by eye, with no evidence file kept
  and the volume left up for further work (0060 D7).

## [0.35.1] - 2026-10-11 · 0059-the-pod-in-python

### Changed

- `provision.py fetch` lands a manifest's files over `urllib`, walking each entry's sources under unit test; the
  vocabulary, reader and evaluator remedies name it in place of the shell driver (0059 D3).
- `isekai/boundary/pod_start.py` runs the pod's start as tested Python — the volume, the models link, `fetch`, the
  memory checks, then ComfyUI — and also holds on an unread `/dev/shm` type and reports swap (0059 D1, D2, D4, D6).
- The image runs `pod_start.py` beside `provision.py`, without `wget`; the build record refuses a `COPY` it cannot
  read; D35 names the host's swap, and the pins guide rebuilds before it re-records (0059 D1, D3, D7).
- The gate's browser typecheck is `tools/typecheck_ui.py`, its refusals unchanged and under test; no bash is
  tracked (0059 D5).
- The pod image is re-pinned to `v0.35.1-rc3`, `sha256:0f0a8e82…dbcf88ff`, carrying `fetch`'s retry; one
  `isekai render` session rendered both flows on it, the pod read showed memory-only ComfyUI with no metadata,
  and no pod was left (0059 D8, D9).

### Removed

- `start.sh`, `tools/download_models.sh`, `provision.py`'s `plan` and `land` verbs and the tests that read the
  scripts' text: `tests/test_pod_start.py` and `fetch`'s tests hold the same keys by behaviour (0059 D3, D6).
- `tools/typecheck_ui.sh`: `tools/typecheck_ui.py` replaces it (0059 D5).

### Fixed

- `fetch` moves to the next source on a transfer that fails at the HTTP layer, and verifies after the download
  when its pre-flight HEAD does; the build record reads a `COPY` in any case or indent and refuses an `ADD` that
  is not a checksummed URL (0059 D3, D7).
- `fetch` tries a broken transfer again from the same source before moving on: an entry with one source had
  nowhere to fall. Bytes that do not verify still move on at once (0059 D9).
- The build record refuses a `COPY` wrapped straight after its name, and reads one below a comment ending in a
  backslash as Docker does, rather than leaving its file out of the record unseen (0059 D7).

## [0.35.0] - 2026-10-10 · 0058-gpunit-integration

### Added

- `gpunit.toml` declares the render session's GPU — the pinned image, the cards, the floors, the ceiling and the
  volume — and `gpunit` joins the runtime dependencies; `.env` keeps the API key alone (0058 D6).
- `isekai render <runs> <flow>=<count|source> …` runs a whole render session over `gpunit.session()`, with its
  ordering, pre-pod pass, ceiling watchdog and batch log under unit test; a render records the session's image
  (0058 D1–D5).
- `config/image.json` records the SHA-256 of the `Dockerfile` and every file it copies; `tools/image_record.py`
  prints it into `build-image.yml`'s summary, and a test turns red when the tree drifts from it (0058 D10).

### Changed

- The image boots gpunit's `boot.sh -- /start.sh`, added by checksum at gpunit's pin; `start.sh` drops its own
  stop, key and sshd, reads `GPUNIT_VOLUME_*`, ends a hold by exiting, and `exec`s ComfyUI (0058 D7).
- D27, D28, D35 and D36, the README's render path, `CLAUDE.md`'s metered protocol, the pins guide's recipes and
  the run-flows skill describe a session as `isekai render` over gpunit (0058 D9).
- The pod image is re-pinned to `v0.35-rc1`, `sha256:85f4c1c7…ac441f`, built from this tree; one `isekai render`
  session rendered both flows on a real pod through gpunit and left no pod behind (0058 D11).

### Removed

- `tools/stop_pod.sh` and its tests: gpunit's boot script stops the pod (0058 D7, D8).
- `infra/up.sh`, `down.sh`, `pods.sh` and `render.sh` and the tests that read them: `isekai render` and gpunit own
  the session; the remedies, principles and pins guide name `isekai render` and `gpunit.toml` (0058 D8, D9).

## [0.34.2] - 2026-10-09 · 0057-the-removed-key

### Fixed

- A `spec` marker may name a key the living spec holds while an open delta removes it, so a cut that removes a
  requirement leaves the gate green until its build deletes the tests (0057 D1, D2).

## [0.34.1] - 2026-10-03 · 0056-the-evaluation-paydown

### Changed

- `evaluation.json` and `recall.json` name a scored run by its digest prefix, and each table prints the same: a
  run's slug is its photograph's filename, which can be a person's name (0056 D1).
- The evaluation spec gives an empty latest render group its own scenario, and the test proving it is bound to it,
  so the behaviour no longer rides on the latest-group scenario (0056 D2).

## [0.34.0] - 2026-10-02 · 0055-attribute-recall

### Added

- `evaluation/recall.py` counts, per scored field, the approved sheet's tags a render reads back, names each miss, and
  prints a per-flow table from its record alone (0055 D1).
- Recall reads each render with the pipeline's WD14 tagger at its own floor, in the sheet's spelling, and refuses an image
  that does not decode by name (0055 D2).
- `python -m evaluation.recall <runs> [<run>...]` reads every render of every group and seed against its group's approval,
  writes `<batch>/recall.json` and prints the table; the record is refused where git can reach it, and that refusal now
  names the move and the command to run again (0055 D3).

### Changed

- The cohort evaluator ranks the first seed of each flow's latest render group, not the lowest one (0055 D4).
- D39 records that recall uses the sheet's tagger; `evaluation/README.md`, the evaluation spec's header and the
  boundary README name recall and its importers, and the README says every tracked flow names the same model
  (0055 D2, D5).

## [0.33.0] - 2026-10-02 · 0054-the-control-arm

### Added

- A third flow, `control-anime-wai`, is `summon-anime-wai`'s directory with its face dials at 0, held equal to it by a
  test; digest `f44b0f40647d0c51fa0eecab5a501c8f0318992fe8aac631c7a6cd0d81b61f7d` (0054 D1).
- `approve --flow <flow> --from <source> <run>` copies the source flow's latest approval under the flow, validated
  against its schema, and records the source and its version so the two flows share one sheet (0054 D2).
- `generate --seeds-from <flow>` renders each run on its source flow's latest seeds, refuses a run with none before any
  pod, and records the source on each render; `render.sh` takes `<flow>=<source>` beside `<flow>=<count>` (0054 D3).
- D38 records the control flow and the named-source crossing; `evaluation/README.md` gives the control batch's four
  commands, and the README and CLAUDE.md name the third flow (0054 D4).
- `approve --from` copies again once the source is approved again; `generate --seeds-from` refuses an out-of-step copy
  before any pod, and `--in-step-with` does when `render.sh` takes a source and its dependent in one session, source
  first (0054 D5, D6).
- A source with no render, or rendered from an older approval, is fixed by one session naming the flow beside it; a
  damaged approval record under `--seeds-from` is refused by name rather than crashing (0054 D3, D5).

## [0.32.0] - 2026-10-02 · 0053-the-evaluation-mechanism

### Added

- The evaluator ranks a cohort's photographs for each render and counts two hits, its own photograph and its
  own person with the source set aside, beside the hits chance gives; every render is a row (0053 D1, D2, D4).
- The evaluator finds and aligns a face with OpenCV's YuNet and embeds it with SFace, both pinned in its own
  manifest, so the count is not the generator's recognizer grading itself (0053 D3).
- `python -m evaluation <runs> --cohort <dir>` scores a current batch, writes `evaluation.json` beside the runs
  and prints the table; D37 and the measurement principles say why the count is shaped so (0053 D5, D7).
- A render that does not decode is an `unreadable` row and a run whose frame or flows refuse is listed as
  unreadable, so neither ends the batch; a cohort file that is not an image refuses naming it (0053 D1, D5).
- `evaluation.json` names its models and cohort photographs by digest and counts, never names, the runs it did
  not score; it is refused where git can reach it, and a retired flow costs a run only its own renders (0053 D4, D5).

### Removed

- The old evaluator — the canvas, the regions, the guard, the axes, the labels, the baseline and the `[eval]`
  extra — is deleted; the cohort count replaces it and the evaluator adds no package (0053 D6, D8).

## [0.31.4] - 2026-09-30 · 0052-the-paydown

### Changed

- The accepted risks of D6, D27, D35 and D36 are written in their decisions, and the patched module globals and
  `_once`'s transience rule as known breaks, so a reader of a topic finds its risk there (0052 D1, D2).
- `show` lists every failure record under its stage or render group, names each file or directory below a flow
  it does not read, and says when a file declares no kind, so a run is never shown as other than it is
  (0052 D3, D4, D5).
- The image's clone guard refuses an `ADD` from an ssh or scp address, which BuildKit clones as it does a git one
  (0052 D6).
- The review rail's run button reads `in the manifest`, which is what it counts, and the tag-list and tab-close
  comments no longer promise more than the code does (0052 D7).

## [0.31.3] - 2026-09-30 · 0051-the-terse-comments

### Changed

- The run directory's and the shared modules' comments carry no version, change id or design citation; a
  decision in force is named by its id, so a reader follows the reason to `docs/decisions.md` (0051 D1, D2).
- The boundary modules' comments and a tagger refusal carry no version or design citation; the Ollama, reader
  and vocabulary pins name D6, D7 and D23 (0051 D1, D2).
- The stages' comments carry no version or design citation; the untagged sheet, the permanent sheet failure and
  the tag verb's paired lists name D31, D21 and D1 (0051 D1, D2).
- The CLI's, the review UI's and the wiring's comments carry no version or design citation; the runs root, the
  seed and the tagger's declaration name D18, D13 and D31 (0051 D1, D2).
- The render scripts', the image's and the derivers' comments carry no version or design citation; the render
  session, the volume and the image pin name D36, D27 and D28 (0051 D1, D2).
- The suite's comments, docstrings and exemption reasons carry no version or design citation; a test's
  docstring keeps only what it proves (0051 D1, D2).
- CLAUDE.md states the comment rule, and a guard fails on a version, a change id or a design citation in a
  comment, a docstring or an exemption reason; the package READMEs name every importer (0051 D3, D4, D5).

## [0.31.2] - 2026-09-30 · 0050-the-colour-profile

### Changed

- A photograph's upload no longer carries its colour profile or colour hints: they can name the device and hold
  free text, and the endpoint decodes the same pixels without them (0050 D1).

### Fixed

- Each way the upload's strip refuses a photograph it cannot walk is now reached by a test, so none can regress into
  a crash or a whole upload unnoticed (0050 D2).

## [0.31.1] - 2026-09-30 · 0049-pins-guarded

### Fixed

- The image's clone check counts every `git clone`, whatever its flags or host; a bumped source-only package
  fails until its build tools are recorded again, and pins.md names what a backend adds while it builds
  (0049 D1, D2).
- A runtime report in a shape this build does not read is refused, permanent, as the transport refuses any
  such answer, and is not asked again in the session; the caption and tags goldens hold a pinned producer
  (0049 D3, D4).
- The models root resolves from any working directory, anchored like every other root; `up.sh`'s missing-volume
  refusal no longer states a stale download size (0049 D5, D6).
- The clone check also counts a clone behind git's own options and refuses a git `ADD`; a render reads the
  runtime report before it uploads, so a refused report sends no photograph; CI keeps no checkout token
  (0049 D1, D4).

### Added

- `make drift` re-runs the fetching derivers and fails on a diff, and `drift.yml` runs it weekly, so a moved
  source turns something red; `make derive` fails on a diff too (0049 D7).

## [0.31.0] - 2026-09-29 · 0048-the-run-files

### Added

- `sheet` warns when it keeps a sheet filled from a tag list older than the flow's latest, naming both and the
  `--new-version` command: after `tag --new-version`, "already complete" alone hid it (0048 D5).

### Changed

- A run file whose schema names another kind is refused, naming both, before its version is checked: a file
  copied into the wrong place is no longer read as whatever its place implies. A damaged approval is restored by
  hand, never deleted, since no command rewrites it (0048 D1, D2).
- A render's record is `<seed>.render.json`, and a version listing reads only the `draft` and `approved` labels:
  a three-digit seed's record no longer reads as a version (0048 D3).
- `sheet` records a damaged tag list and a tag outside the vocabulary as permanent failures, so its budget
  binds and the refusal names the record and `tag --new-version`, as no sheet exists to edit; an absent tag list
  still records nothing (0048 D4).
- A stage's refusal for a failed later version names its rerun with `--new-version`: the bare command reported
  the version before it as already complete (0048 D4).

## [0.30.4] - 2026-09-29 · 0047-the-refusals

### Fixed

- One flow's refusal no longer drops an input's other flows; `tag` given only untagged flows names `sheet`; a
  render session refuses a batch with a named flow unapproved on any run; a test is demanded only of a living key,
  so a cut adding a scenario stays green (0047 D1, D2, D3, D8).
- `show` marks a frame it cannot read and lists the rest; the Ollama refusals name the pinned files' fetch before
  the build; an artifact the vocabulary manifest does not declare is a refusal, not a traceback (0047 D4, D5, D6).
- The host-key check reads the container log's last lines, keeping the last key line alone; a `since` read follows
  when downloads pushed it out, as reading by `since` first stalled on a live boot (0047 D7).

## [0.30.3] - 2026-09-29 · 0046-the-terse-specs

### Changed

- `CLAUDE.md` states how a spec reads. `agent-skills`, `comfy-transport` and `pod-image` read to it, and the pod
  listing's no-image failure names a live pod, as the listing already drops a terminated one (0046 D1, D2, D3, D4).
- `image-generation` reads to the rule: each requirement one SHALL and one *why*, with its decisions linked and
  diagrams for the render target and a flow's layout (0046 D2, D3).
- `cli` reads to the rule, its Purpose two sentences; a history of the per-flow seam and the render surface gives
  way to the reason each holds (0046 D2, D3).
- `sheet` and `tagging` read to the rule: measured figures and the story of the move from prose to a tag list go,
  and the sheet's fill gains a diagram (0046 D2, D3).
- `caption` and `review` read to the rule: measured scores and costs go, and the review's copy-then-approve layout
  gains a diagram (0046 D2, D3).
- `model-provisioning` reads to the rule, its stray closing tag gone; each rule's reason leaves its SHALL paragraph
  and its scenarios, and the provisioning hold gains a diagram (0046 D2, D3).
- `run-directory` and `field-map` read to the rule, and the gate holds it: a spec naming a version, a change id or a
  commit, or with a line past 120 characters but a title, fails the suite (0046 D2, D3, D5).

## [0.30.2] - 2026-09-29 · 0045-the-spec-bound

### Fixed

- The prefix-collision scenario has its test, and a scan no one answers has its own scenario and tests;
  the hold's test checks that the hold ends in the pod's stop (0045 D3, D4, D5).
- The gate checks every spec↔test binding: each scenario key has a test, each marker names a key, and each
  test carries one marker, counting an active change's deltas; `CLAUDE.md` names the check (0045 D1, D2, D6).

## [0.30.1] - 2026-09-29 · 0044-the-session-proved

### Fixed

- The pod listing fails on a repeated cursor or an `isekai` pod with no image, and lists only this image; a
  session `up.sh` refused leaves a listed pod, sweeping only after a lost create (0044 D1, D2).
- `README.md` names the pod check, the catalogue, the sweep and the stop timer. `0.30.0` gains its `### Security`
  heading, an exception to append-only, and a bullet outside a section is refused (0044 D3, D4).
- Image `v0.30-rc2` is proved on a pod: both flows render, and the pod stops itself with its own key, whose scope
  is its own pod. The live read of the pod's log and a refused key's endless retry are carded (0044 D5).

## [0.30.0] - 2026-09-29 · 0043-the-session

### Security

- `up.sh` places a pod only on a host that can render, and refuses beside a recorded or listed `isekai` pod;
  `down.sh` removes every `isekai` pod, so none bills unseen (0043 D1, D2, D3).
- A pod stops itself 45 minutes after it boots, and every hold ends in that stop, so a pod bills bounded with
  the laptop gone. ComfyUI starts without RunPod's key (0043 D4, D5, D6).
- `docs/decisions.md` records `render.sh` as the render session and the bounds that hold it; `CLAUDE.md`'s
  teardown rule names `down.sh`'s sweep and the pod's own stop (0043 D7).
- A pod boots image `v0.30-rc2`, built on request from this version's tree, so it carries the stop. It replaces
  `v0.30-rc1`, built before the boot's end and the stop's retry changed in `start.sh` and `tools/stop_pod.sh` (0043 D8).
- The live acceptance of `v0.30-rc1`, a render boot and a stop boot, is deferred to the next version: RunPod had
  no capacity. One boot placed a host within the floors but got no SSH address (0043 D9).
- A boot that ends, ComfyUI exiting included, stops the pod rather than restarting with a fresh ceiling; the stop
  retries until it succeeds; and a session whose create was lost still sweeps with `down.sh` (0043 D3, D4, D6).

## [0.29.1] - 2026-09-29 · 0042-the-rebuild

### Security

- An upload spools to memory, and a pod holds on a `/dev/shm` that is not a tmpfs or not read. The image, now on
  plain Ubuntu with CPU onnxruntime, carries the telemetry switches; its build tools are checked by hash
  (0042 D1, D2, D3, D4, D5).

### Changed

- `docs/pins.md` holds the build tools by hash, the privacy principle names its new tests, and 0.26.1 names its
  append-only exception (0042 D5, D6).
- A pod boots image `v0.29.1-rc1`, built on request from this version's tree, so it carries the rebuild (0042 D7).
- One session on `v0.29.1-rc1` rendered both flows from memory. DWPose's box detector now runs on OpenCV, not
  onnxruntime, as the CPU package lists no GPU provider; accepted until an evaluation on more photographs says
  otherwise (0042 D4, D8).

## [0.29.0] - 2026-09-28 · 0041-the-right-machine

### Security

- A pod is created only beside a models volume large enough for the manifest, and with its libraries' telemetry
  and update checks off, so the machine rendering a likeness reports to no one (0041 D3, D4).
- `up.sh` checks a pod's host key against the fingerprint the pod printed, and keeps it for the strict tunnel; a
  mismatch, or no fingerprint in time, refuses and tears the pod down, so only the pod gets a photograph
  (0041 D1, D2).
- The privacy principles enter `docs/principles.md`, and `docs/decisions.md` records that renders stay on a pod
  and that the pod's operator is a trust boundary, accepted knowingly (0041 D5).
- One session rendered both flows through the checked host key and the strict tunnel, on a pod created with
  its telemetry switches set (0041 D6).

## [0.28.0] - 2026-09-28 · 0040-the-pod-image

### Security

- The image ships no SSH host key: each boot makes an Ed25519 key, serves with it alone and prints its fingerprint.
  ComfyUI writes only to memory and saves no metadata, and holds on too little memory; the environment now installs
  before the node clones (0040 D1, D2, D3, D4).

### Changed

- A pod boots image `v0.28-rc1`, built on request from this version's tree, so it carries the key and memory
  changes (0040 D5).
- One session on `v0.28-rc1` rendered both flows, a rotated photograph upright among them: the pod made its own
  host key, ComfyUI wrote to memory, and no render carried a text chunk (0040 D6).

## [0.27.0] - 2026-09-28 · 0039-the-photo-metadata

### Security

- A photograph can be stripped to the blocks that decode its pixels, colour profile and orientation, by a byte
  walk that never re-encodes; one it cannot walk to its end is refused (0039 D1, D2, D5).
- The render uploads the stripped photograph under its name, and the run's copy keeps its bytes; the transport
  takes a name and bytes (0039 D3, D4).
- A JFIF or Adobe header is cut to its fixed fields, so a thumbnail never leaves, and assembly walks the photograph,
  even under a prompt already on disk, so one the strip refuses is refused before any pod boots (0039 D1, D5).

## [0.26.1] - 2026-09-28 · 0038-the-changelog

### Changed

- Every version rewritten terse, the one stated exception to append-only: Keep a Changelog sections only, each
  heading from `0.7.0` naming its change, and the preamble holding the rules only (0038 D1, D2, D3, D5, D6).
- `CLAUDE.md` states the changelog's rules, no code, doc or README cites it, and `tests/test_changelog.py` holds
  both (0038 D6, D7, D8).

## [0.26.0] - 2026-09-28 · 0037-the-boundaries

### Security

- The ComfyUI transport ignores an exported proxy and bounds every wait; a malformed prompt id is refused
  (0037 D1, D2, D3).
- An upload's boundary is random and its names escaped, and an endpoint's error text keeps printable characters
  only (0037 D4, D5).
- The review surface refuses a damaged draft, sheet, caption or tag list by name, with a shell-quoted fix that
  works under any runs root, and refuses a malformed draft update (0037 D6).
- A run's frame names its photograph by one plain filename and carries its digest, and the photograph may not be
  a symbolic link (0037 D7).
- A render session's watchdog ends with it, its tunnel keeps its own host keys, and its checks bypass any proxy
  (0037 D8, D9, D11).

## [0.25.1] - 2026-09-27 · 0036-the-prose

### Changed

- No intimate tag, rating term or per-tag count from the operator's sheets stays in tracked prose; the archive and
  this file are edited, a stated exception (0036 D1).
- `docs/decisions.md` D33 records that isekai restricts no content; the operator answers for what renders
  (0036 D4).
- `docs/pins.md` stops overstating the reader's and the image's pins (0036 D5).
- The teardown and port messages name the right fix (0036 D6).
- `summon-anime-wai`'s graph placeholder is `photo.jpeg`, re-pinned in place; no submitted graph moves.
  `summon-anime-wai` → `96c605821e68a8ac2f1c7a60807cfcfb4c3658ae4112cc84d21a00bf39f3e698` (0036 D7).

## [0.25.0] - 2026-09-27 · 0035-the-flow-skills

### Added

- `compare` verb: writes `compare.html`, each photograph beside its flows' renders, and prints its path (0035 D2).
- `infra/render.sh`: one render session that assembles first, rents, renders each flow, halts at the pod ceiling,
  and tears down on every exit (0035 D3).
- The `run-flows` and `compare-renders` skills: an agent runs a batch to the comparison page, stopping for the
  approval and the go, and never reports a pod id (0035 D1, D4, D6).

### Fixed

- onnxruntime's telemetry is disabled, so `tag` no longer connects out or aborts at exit (0035 D5).

## [0.24.1] - 2026-09-27 · 0034-runpod-rest-v2

### Changed

- `up.sh` creates and `down.sh` deletes on RunPod's REST v2, trying each GPU type in order (0034 D1, D2, D3).
- Only a 204 tears down; a 404 keeps the record files and asks for the RunPod MCP's confirmation (0034 D5).
- Every RunPod call is bounded and reads its key from a file descriptor, never `argv` (0034).
- A create whose outcome is unknown says a pod may exist, and names the check (0034 D4).

## [0.24.0] - 2026-09-27 · 0033-pin-and-record

### Added

- `docs/pins.md`: what each pin buys, where it is declared and checked, and how it moves (0033 D10).

### Changed

- CI and the toolchain are pinned: actions by commit, the runner, Node and uv (0033 D1).
- The image is built on request from pinned inputs into a locked environment, and reports its digest (0033 D2).
- BREAKING: a pod boots only the digest `config/image.json` pins; `RUNPOD_IMAGE` goes (0033 D3).
- `caption` and `tag` refuse a reader model that no entry in `config/reader.json` pins (0033 D4).
- Every artifact records what shaped it: sampling options, floor, flow digest, sheet, image and runtime
  (0033 D5, D6).
- A boot prints when each step begins (0033).

## [0.23.0] - 2026-09-26 · 0032-the-tag-verb

### Changed

- BREAKING: a flow's manifest declares `"tagger": true | false`, and `MANIFEST_VERSION` moves to 4 (0032 D1).
- Both flows re-pinned in place, format only. `conjure-anime-wai` →
  `f2bd3202079b1288068aed7ccf57e2b6b0e3b9a1db037973b4be99f83bf22a1f` (0032 D1).
- BREAKING: `caption` writes the prose only, and a new `tag` verb writes both tag lists (0032 D2).
- A flow that declares no tagger gets a sheet with every field empty (0032 D3).
- The review surface shows a missing caption with the command that writes it (0032 D4).

## [0.22.9] - 2026-09-26 · 0031-the-backlog

### Changed

- The retry rule is stated once, in `run._spent`, and the drifted documentation is corrected (0031 D2, D3).

### Fixed

- An endpoint answer in the wrong shape is refused permanent, and a history that is not an object no longer polls
  forever (0031 D1).
- A key the `review`, `approve` or `sheet` stage reads from a run file is refused by name when missing or mistyped
  (0031 D1).
- Approval takes the draft lock, and never guesses a draft unedited from a missing or damaged source (0031 D1).
- A damaged `run.json` names a remedy that works (0031 D1).

## [0.22.8] - 2026-09-26 · 0030-the-defects

### Fixed

- An unreadable run file is refused by name, with a remedy that deletes it, and `show` marks it (0030 D1, D5).
- A failure record's attempt is the highest recorded plus one, so a deleted record is never overwritten (0030 D2).
- One definition of the current draft: a stale draft neither re-opens an input nor is approved (0030 D1, D4).
- The transport's failure carries its kind: a 4xx is permanent, a 5xx or a closed tunnel transient (0030 D3, D6).
- Every printed stage command names its run, so a pasted remedy acts (0030 D1, D2).

## [0.22.7] - 2026-09-26 · 0029-the-tree

### Changed

- The files the pipeline reads move to `config/`, and the derivers and operator scripts to `tools/`
  (0029 D1, D3, D4).
- The evaluator is a top-level `evaluation/`, run as `python -m evaluation` (0029 D1, D2).
- `make derive` re-runs every deriver in dependency order (0029 D6).
- The image's paths are checked statically (0029 D5).

### Removed

- The licence record `scripts/eval_licences.md` and its requirement; the AGPL guards stay (0029 D10).
- `probe/`, the loader probe (0029 D9).

## [0.22.6] - 2026-09-26 · 0028-the-file-shapes

### Changed

- `isekai/foundation/artifacts.py` is the run directory's contract: each file kind's shape, name and version, with
  one typed `read` and `write` (0028 D1, D2, D3, D4).
- Every run file is read and written through the contract, and golden files pin each kind's bytes
  (0028 D5, D8, D9).

### Removed

- `SCHEMA_VERSION`, `envelope` and `read_artifact` (0028 D7).

## [0.22.5] - 2026-09-25 · 0027-the-seams

### Changed

- The `Makefile` is the gate's one declaration; `.minions/minions.toml` goes (0027 D1).
- The review UI reads the encoder window from the server's token budget (0027 D2).
- `tests/test_layers.py` holds that imports point down, and `foundation` imports nothing above it (0027 D3, D6).
- Pin verification belongs to `boundary/provision.py`, and the ComfyUI transport is `boundary/comfy/`
  (0027 D7, D9).
- The approval state moves from the review UI into `pipeline/review.py` (0027 D11).

## [0.22.4] - 2026-09-25 · 0026-architecture-in-the-repo

### Changed

- Code, tests and spec preambles say what the code does; no behaviour changes (0026 D1).
- `docs/` holds the architecture: `principles.md`, `decisions.md` and `modules.md`, with `docs/arc/` flattened in
  (0026).
- `CLAUDE.md` keeps only process, and imports `docs/principles.md` (0026 D8).
- `README.md` stops restating the architecture and links `docs/` (0026 D10).

## [0.22.3] - 2026-09-23 · 0025-running-the-flow

### Changed

- The negative prompt is quality-only and lives in the flow alone; each graph's negative node is emptied, and both
  flows are re-pinned (0025 D1, D2).
- `dependencies = []` retires: the tagger's and the UI's stacks are declared, so the gate stops removing them
  (0025 D3).
- The `-S` guard is narrowed, and falsified against a declared dependency (0025 D4).
- `## Quickstart` is rewritten as `## Running a flow` (0025 D5).

### Fixed

- The re-pin record test can fail for a re-pin (0025 D2).
- The tagger's refusal names `uv sync`, not a removed extra (0025 D3).

## [0.22.2] - 2026-09-22 · 0024-the-documents

### Added

- `docs/arc/`, where the architecture is drawn: the module graph and the data flow (0024 D3, D4).
- Scenarios for the behaviour `0.22.1` shipped unbound, repaying its `spec_exempt` markers (0024 D7).

### Changed

- Every claim the repository makes about itself is checked against the tree, and quantities leave the docs
  (0024 D1, D2, D6).
- `CLAUDE.md` holds agent instructions only; how the system works moves to `docs/arc/` (0024 D3).
- An input re-opened with `review --new-version` is editable on the surface again (0024 D5).

### Removed

- `isekai/README.md`'s edge table: `docs/arc/` owns the module graph (0024 D4).

## [0.22.1] - 2026-09-22 · 0023-backlog-paydown

### Changed

- `num_ctx` is pinned in both hosted option maps (0023 D8).

### Removed

- The `vite` dev-server proxy, which the `Host` guard turned into a trap (0023 D3).

### Fixed

- A manifest missing a dial its roles read, or naming a node its graph lacks, is refused at load (0023 D4).
- An unreachable endpoint is recorded `transient`; rendering's budget stays one (0023 D11).
- One flow's malformed sheet, or one unreadable photograph, no longer costs the rest of the batch (0023 D1).
- An overlapping draft `PUT` answers `409`, and approve stops when the write it waits for was refused (0023 D6).
- Every command a refusal prints is one the parser accepts (0023 D1).
- The UI bundle is rebuilt when anything it is built from changes, and the build is bounded in time (0023 D1).
- The hosted tag panel shows each tag once (0023 D7).

### Security

- The review surface validates `Host` and `Origin` on every request (0023 D3).

## [0.22.0] - 2026-09-22 · 0022-one-arm

### Changed

- BREAKING: `summon-anime-wai` and `conjure-anime-wai` replace the three flows; a flow's name carries its base
  (0022 D5, D6).
- BREAKING: the `hosted` block goes; a required top-level `model` replaces it, and `MANIFEST_VERSION` moves to 3
  (0022 D1, D2, D4).
- `CliFailure` becomes `StageFailure`, and the shared run names move to `foundation/run.py` (0022 D12, D13).

### Removed

- The `claude` arm: `isekai/boundary/claude_cli.py`, both reader registries and `tests/test_isolation.py`
  (0022 D16, D18).
- `sheet.briefing.md`, from every flow (0022 D9).

## [0.21.0] - 2026-09-21 · 0021-sheet-from-the-tagger

### Added

- `field-map`: one authored table giving each tag one primary field, checked at load (0021 D4, D9, D19).
- `scripts/derive_field_map.py`, an offline authoring aid for the table (0021 D15).
- A read-only field cheatsheet on `Option+Space`, served by `GET /api/fields`, and `Option+F` for the photograph
  (0021 D11, D13, D14).

### Changed

- The sheet comes from the local tagger's list through the field map; an absent `wd14/` refuses naming `caption`
  (0021 D5, D21, D24).

### Removed

- Both sorters, the free-text mapping cascade and their scenarios (0021 D20, D23).

## [0.20.0] - 2026-09-21 · 0020-readable-caption

### Added

- `caption` also writes a local WD14 tag list and a hosted JoyCaption one, beside the prose (0020 D1, D7, D8).
- `isekai/boundary/wd14.py`, the local tagger behind a `tagging` extra, verifying its pinned digests first
  (0020 D9, D17, D19).
- The review surface shows the caption a sentence to a block, with both tag lists beneath (0020 D2, D10, D13).
- The gate type-checks the browser half, and CI restores its toolchain (0020 D22).

### Changed

- The hosted tag list is filtered to the vocabulary before it reaches the page (0020 D29).

### Fixed

- `isekai ui` rebuilds a stale bundle (0020 D28).

## [0.19.0] - 2026-09-20 · 0019-open-models

### Added

- `isekai/boundary/ollama.py`: open models behind a local Ollama read and sort, with no `claude` needed and no
  proxy in between (0019 D1, D4, D5).
- A flow may declare the models its first two stages call, and `flows/summon-open-v1/` does (0019 D2, D3).
- An unreachable host or an absent model refuses without spending an attempt (0019 D9).
- A manifest key this build does not read is refused by name (0019 D12).

## [0.18.0] - 2026-09-19 · 0018-review-ui

### Added

- `isekai ui <ids…> --flow F`: stage ③ in a browser, a Vue app served by FastAPI beside the CLI (0018 D1, D2, D8).
- Editing with autosave, undo, a keyboard model, tag autocomplete and a token budget per field (0018 D4).
- Approval is terminal in the browser, and a run manifest sums up the batch (0018 D5).
- The bundle is built on demand, and a `ui` extra pins the server stack (0018 D12).

### Changed

- Each living spec gains `## Purpose` (0018 D9).

### Fixed

- The run-root containment guard compares directories, not path text (0018 D10).

## [0.17.0] - 2026-09-18 · 0017-conjure

### Added

- `flows/conjure-v1/`: a render from the sheet alone, no photograph, added without code (0017 D1, D2, D3).
- Its schema is chosen by vocabulary depth, and its dials are `summon`'s less the identity ones (0017 D4, D6).

## [0.16.0] - 2026-09-17 · 0016-flow-registry

### Added

- `--flow` is required and repeatable on every stage verb, resolved against `flows/` before a run opens (0016 D6).

### Changed

- BREAKING: a flow is flat files with an eight-key `flow.json` that pins its models by digest (0016 D1, D3, D4).
- BREAKING: the run layout is input above flow, and the sheet stage writes one sheet per flow (0016 D5, D6).
- BREAKING: the run id's separator is an underscore (0016 D10).
- `validate` moves to `shared/fields.py`, and no stage imports another (0016 D8).

### Fixed

- A manifest declaring the photograph on one side only is refused at load (0016 D9).
- Resume no longer assumes a render is a PNG (0016 D11).

## [0.15.0] - 2026-09-17 · 0015-arc-alignment

### Changed

- The package becomes group directories, each with a `README.md`; the CLI moves to `interface/cli.py`, and
  `provision.py`, which the image follows, to `boundary/` (0015 D2, D3, D11).
- `show.py` becomes `run_view.py`, `photo.py` becomes `image.py`, and `write_atomically` is its own module
  (0015 D4, D6).
- The repository-root anchors are pinned by a test before anything moves (0015 D7).

## [0.14.0] - 2026-09-15 · 0014-delete-the-old-path

### Added

- The target ceiling is restored to the surviving render path (0014 D4).
- `--runs` refuses a root inside the working tree (0014 D7).
- `infra/up.sh`'s readiness wait is bounded, and tears the pod down on timeout (0014 D10).

### Changed

- `.data/` is the one root anything is generated into; `outputs/` is gone (0014 D7).
- `isekai/workflow.py` becomes `isekai/photo.py`, without injection (0014 D3).

### Removed

- BREAKING: the old render path, `convert.py` and its CLI; `python -m isekai` is the one entry point (0014 D1).
- The model artifacts only the old graph used, from the manifest (0014).

## [0.13.0] - 2026-09-15 · 0013-walking-skeleton

### Added

- `python -m isekai`, a second entry point with the verbs `caption`, `sheet`, `review`, `approve`, `generate` and
  `show`; `convert.py` is untouched (0013 D1, D2).
- The run directory, `.data/runs/<photo-id>/`: the photograph copied in, artifacts numbered and never overwritten,
  and a failure recorded beside its artifact with its kind (0013 D4, D5, D14).
- `caption` reads a photograph into prose, and `sheet` sorts the prose into a versioned schema mapped onto the tag
  vocabulary, both through a locked-down `claude -p` (0013 D6, D8).
- `review` copies a sheet into a draft, and `approve` validates the draft and renames it, recording whether a human
  edited it (0013 D3).
- `generate` renders an approved sheet through a flow under `flows/`, declared and pinned by equality; the prompt is
  assembled locally before any endpoint (0013 D12, D13).
- The tag vocabulary is provisioned from its own pinned manifest, and one module derives every manifest (0013 D9,
  D10).

### Removed

- The absent-models preflight: no endpoint lists a volume, so it could only give a false guarantee (0013 D15).

### Fixed

- `outputs/` and `.inputs/` are gitignored again, held by a test (0013 D14).
- `generate` assembles the whole batch before renting, renders only with `--server`, and refuses a run approved for
  nothing (0013).
- The sorting briefing's examples use the vocabulary's spellings, so `count` and `gaze` map to tags (0013).
- `infra/up.sh` sends the GPU preference as a list, not one enum value (0013).

## [0.12.0] - 2026-09-07 · 0012-identity-evaluator

### Added

- `evaluate.py`, a second entry point off `convert.py`'s import graph: face, pose and hair-colour axes and a
  face-location guard, which rank and never grade (0012 D1, D5, D12).
- `run.json` records the photograph's digest, the base, the working resolution, the pod image, the ComfyUI
  commit, and each variation's seed, graph digest and dials (0012 D4, D14).
- `--fixed-dials` renders at the graph's own dials, and `--cn-strength` sets the identity node's keypoint dial
  (0012 D3, D6).
- The evaluator's models are pinned in `scripts/eval_models.json`, a sibling of the graph's manifest, with every
  licence recorded (0012 D16, D18).
- The guard ships box IoU as its authoritative method, chosen by measuring both (0012 D9).

### Changed

- The anime-face detector is `deepghs/anime_face_detection`, MIT: the AGPL one named publishes no ONNX (0012 D19).

## [0.11.0] - 2026-09-06 · 0011-converge-paydown

### Added

- `infra/up.sh` refuses a pod with no network volume named, and the pod checks its volume's capacity (0011 D5).
- A provisioning abort holds the pod for a bounded time and leaves a failure marker on container disk (0011 D6).
- Measuring a photo refuses past stated ceilings on the target, a header dimension and the header walk (0011 D8).
- `provision.py` refuses an escaping destination, an unpinned source and an empty entry before any byte moves
  (0011 D7).
- The base checkpoint's digest is derived from Civitai's record, not transcribed (0011 D13).
- CI refuses a manual image tag that is `latest` or malformed (0011).

### Changed

- ComfyUI's core is pinned to the commit the release-candidate image ran (0011 D3, D4).
- The graph↔manifest binding keys on a census of node classes, not a name suffix (0011).

### Fixed

- A rotated PNG is measured as the loader transposes it, as a JPEG already was (0011 D11, D12).
- The pose-grid sentence is corrected: `DWPreprocessor` works at its own resolution (0011 D9).

## [0.10.0] - 2026-09-05 · 0010-illustrious-base

### Added

- An `ImageScale` node sizes the photo to a working resolution derived from its own header (0010 D2).
- A release-candidate image tag for metered phases; `:latest` stays the released one (0010 D8).

### Changed

- BREAKING: the base is WAI-illustrious-SDXL v17.0, fetched from mirrors and trusted by the digest Civitai
  publishes, with its publisher's prompts (0010 D1, D4).
- The graph stops CLIP at the second-to-last layer, as the publisher's samples do (0010 D6).
- The probe's dials and every ControlNet are kept, and the dials are pinned by the suite (0010 D7, D9).

### Removed

- `1girl` leaves the positive prompt; gender comes from the identity node's face embedding (0010 D5).
- Animagine XL 4.0 leaves the manifest once the swap is proven (0010 D3).

### Fixed

- A rotated JPEG is measured as the loader transposes it, and a deep frame header is read, not refused (0010 D2).

## [0.9.0] - 2026-09-05 · 0009-pinned-provisioning

### Added

- `scripts/models.json`, a pinned and checksummed manifest of every model the graph needs, derived by
  `scripts/derive_manifest.py` (0009 D5, D15).
- `isekai/provision.py` decides skip, fetch or abort per entry, hashes a file already present, and lands a transfer
  only once verified (0009 D4, D14).
- A test binds the graph to the manifest, including the files preprocessors fetch for themselves (0009 D6).

### Changed

- `scripts/download_models.sh` is a `wget` driver over the manifest, walking its fallback sources; the `hf` CLI goes
  (0009 D2, D3, D16).
- The volume mounts at `/runpod-volume`, and the models directory is one symlink into this project's namespace
  (0009 D8, D9).
- The annotator checkpoints move onto the volume, and a provisioning abort holds the pod open (0009 D7, D17).

## [0.8.0] - 2026-09-04 · 0008-one-path

### Changed

- BREAKING: one path, renamed to nothing: `workflows/pipeline.json`; `--model`, `--workflow` and `--prompt` go
  (0008 D1).
- BREAKING: `-o` names a directory; each run writes a timestamped one with its renders and a `run.json` (0008 D4).
- BREAKING: every variation's seed is derived from `--seed`, variation 0 included (0008 D5).
- The positive prompt is pinned by equality in the suite, and `arms crossed` leaves it (0008 D6, D7).
- `CLAUDE.md`'s metered-work rule names who creates, tears down and confirms, and when a human go is back (0008 D10).

### Removed

- The `qwen`, `animagine` and `animagine-i2i` paths, the registry, the fixtures and every idle seam (0008 D2, D3, D9).

## [0.7.0] - 2026-09-01 · 0001-mf-standard

### Added

- The OpenSpec tree, and `spec` and `spec_exempt` markers binding every test to a scenario (0001).
- A root `Makefile` with a `gate` target that CI runs, `.python-version`, and this file (0001).

### Changed

- The gate config moves to `.minions/minions.toml`, and `CLAUDE.md` and `README.md` are rewritten (0001).

### Fixed

- `--variations` no longer bills identical renders on a model with no mutation, and zero is refused (0001).
- `--seed` and `--denoise 0.0` are no longer discarded, and `mutate` refuses a linked dial by name (0001).

## [0.6.0] - 2026-08-15

### Added

- `--denoise`, `--cfg` and `--ip-weight`, range-checked and applied before the jitter.

### Changed

- The jitter is relative to each dial's base value.

## [0.4.0] - 2026-08-04

### Added

- `--seed` and `--variations`, through a mutation seam with an injected `random.Random`.
- The `animagine-i2i-cn` model: `animagine-i2i` with a tile, OpenPose and lineart ControlNet stack.

## [0.3.0] - 2026-07-31

### Added

- The `animagine-i2i` model: img2img from the photo, with `denoise` as the identity-versus-style dial.

## [0.2.0] - 2026-07-31

### Added

- `--model {qwen,animagine}`, the `animagine` model with InstantID, and a fake transport for an offline suite.

## [0.1.0] - 2026-07-28

### Added

- `convert.py`, a stdlib-only CLI that drives a ComfyUI workflow, and the container image CI publishes.
- Pods created and deleted by `infra/up.sh` and `infra/down.sh`, with models downloaded on boot.

### Fixed

- Blackwell GPUs run the image: PyTorch is pinned to a cu128 build.
