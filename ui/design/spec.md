# isekai app — design spec

**The design the UI is built to**: rules, tokens, the shell, routes, the journeys, the states, keys and live state,
and which part each version of the UI arc builds — import and assign, render, revise. Drawn in Claude Design and
checked against the repo at `45babd9`. [§10](#10--which-version-builds-what) says which version builds what.

Vue 3 single-file components, plain CSS, no component library — the stack `ui/` already uses.

---

## 1 · Rules on every screen

1. **Text is state, a disabled action's reason, or a refusal's fix**. No helper text, legends or how-to
   sentences. Key hints inside buttons are allowed; the keys are listed once, in the key list the app bar's `?`
   opens. The one exception is the privacy line on first start.
2. **No file path on screen**, except inside a refusal's fix, written as the CLI prints it. Display names stay
   short (`00003`, `16_01`).
3. **One accent-outlined action per screen**: the next forward action, or none. Everything else is outlined
   grey.
4. **A disabled button has its reason beside it**, never in a tooltip, where the screen does not already show why.
   An action with nothing to do is absent, not disabled.
5. **A refusal** is a 7×7 accent square, the reason in `ink`, then the fix in `ink-2`. A command or an offered value
   inside the fix is mono, `accent-ink`.
6. **Two job slots, one Prepare and one render**; a job of either kind waits only for its own. While a job runs,
   only actions that would start another of its kind are disabled. An unresolved billing alert holds the render
   slot until gpunit confirms the pod or volume gone.
7. **No money after the Render quote**.
8. **The URL is real**. Overlays keep the URL of the page beneath. The Render dialog has no URL.
9. **A refusal's text is the CLI's, verbatim**. The UI invents no command.
10. **Count labels use the singular noun at one and the plural otherwise**: `1 source`, `0 sources`, `3 sources`.
11. **A dialog holds the focus** while open — on its first control, the page behind inert — and gives it back on close.

## 2 · Tokens

| token | value | use |
|---|---|---|
| `--ground` | `#161724` | app background |
| `--ground-deep` | `#11121c` | app bar, rail, job strip, fields |
| `--ground-media` | `#0e0f17` | large view, compare, the viewer |
| `--raised` | `#1a1b29` | dialogs, sheets |
| `--raised-2` | `#1d1e30` | Prepare bar, focused cell |
| `--line` | `#272939` | borders, column dividers |
| `--line-soft` | `#22243a` | row dividers |
| `--line-control` | `#33354a` | secondary button and field border |
| `--line-disabled` | `#2c2e42` | disabled button border, empty track segment |
| `--focus` | `#6b6d80` | focused cell and field ring — focus is not an action, so it is not accent |
| `--ink` · `--ink-1b` · `--ink-2` · `--ink-3` | `#e4e4ec` · `#c9cad6` · `#a3a5b8` · `#74768a` | text levels |
| `--ink-muted` | `#8a8ca0` | disabled reasons, secondary meta |
| `--ink-disabled` | `#5d5f73` | disabled button label |
| `--accent` | `#8d82e6` | the primary outline, assigned tick, running dot, refusal square, billing band |
| `--accent-dim` | `#5a5296` | the running segment of a stage track |
| `--accent-ink` | `#b3abf4` | commands, running words (`captioning…`) |
| `--tick-locked` | `#34364a` | a prepared, locked tick |
| `--chip-line` | `#2f3146` | a flow chip's border |
| placeholder | `repeating-linear-gradient(135deg,#1f2030 0 5px,#26273b 5px 10px)` | an image not yet decoded |
| scrim | `rgba(10,11,18,.4)` | behind sheets and dialogs |

**Type.** Sans: Helvetica Neue, Helvetica, Arial, for prose and buttons. Mono: JetBrains Mono 400/500/600, for names,
counts, keys, stage words and commands. Body 13px. Buttons 13px, 500 when primary. Section labels mono 11px `ink-3`,
uppercase, letter-spacing .04em. Mono meta 11–12px. Screen titles 14px/600; dialog titles 16–20px/600; the session
timer mono 40px/500.

**Shape.** Radius 4px for buttons and fields, 3px for thumbnails and checkboxes, 6–8px for bars and sheets. Buttons
30px tall in toolbars and 32px in dialogs, 14px horizontal padding, a 10px gap to their key hint. Floating bar shadow
`0 20px 50px rgba(0,0,0,.55)`; sheet shadow `0 30px 80px rgba(0,0,0,.5)`. No icons: every mark is CSS.

## 3 · The shell

```
┌ isekai  2026-09-17   Hub ⇧H  Review 3 ⇧R  Renders ⇧I    flow [all|summon|conjure] ⇧F         [ ? ] ┐ AppBar 40
├─ BillingBanner (only when something may be billing; filled accent, cannot be dismissed) ───────────┤
│                                                                                                     │
│                                   <the route's screen>                                              │
│                                                                                                     │
├─ ○ job · idle   last: render · 2026-09-17 · ended 15:38 · 1 image        volume open · until 19:38 ┤ JobStrip 28
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **AppBar**, `ground-deep`, bottom border `line`. The wordmark goes Home. The place is mono 12px `ink-2`: `library`
  on Home, else the batch name. Tabs only inside a batch; the active one has a 2px accent underline. The Review
  tab counts the batch's unapproved sheets in mono 11 `accent`, and opens the batch's Review. The flow
  switcher is a segmented control; Review drops `all`. The `?` button at its right end, after the running render,
  opens the key list, as `⌃/` does; no screen draws a key bar.
- **BillingBanner**, a filled accent band, text `#0f1018` at 600. Three variants: the volume past its window, a pod
  that may be billing, a volume that may be billing. esc never closes it.
- **JobStrip**, `ground-deep`, mono 11px: one dot, then one item per running job, each a label (`job · prepare`)
  and its totals (`1 of 3 cells done · 01:47`, `image 1 of 2 · 06:41 of ≤10:30`); with none running, each kind's
  last receipt. The dot: hollow idle, accent running, accent square unresolved. Prepare keeps the accepted-cell total fixed, counts cells completed at sheet and ticks
  elapsed time every second from its original start. On the right, while the volume is open, the quiet item
  `volume open · until 19:38 · close`.

## 4 · Routes

| route | screen | opens over it |
|---|---|---|
| `/` | Home | the New batch sheet |
| `/b/<batch>/hub` | Hub | the Add sources sheet, the Prepare bar, the Render dialog |
| `/b/<batch>/review` | Review's head, replaced by its sheet's URL | — |
| `/b/<batch>/review/<run>/<flow>` | Review | the cheatsheet, the viewer, *Side by side* |
| `/b/<batch>/renders` | Renders grid | the Revise confirm |
| `/b/<batch>/renders/<run>/<flow>/<version>/<seed>` | large view | the Revise confirm |
| `/b/<batch>/renders/<run>/<flow>/<version>/<seed>/compare` | before / after | — |
| `/b/<batch>/sessions` | the batch's render sessions | — |
| `/b/<batch>/sessions/<id>` | one render session | the viewer |
| `/billing` | the billing alert's way out | — |

- `<run>` is the run's **12-hex digest** (`0d4b7e6fb2a8`), unique by construction; the screen shows the short name
 .
- `<version>` is `v` + the approval's number (`v2` is `review/002.approved.json`, rendered into `outputs/002/`).
- `/b/<batch>/review` opens the first unapproved sheet of the first flow that has one, in the hub's order; else
  the first approved sheet short of its images, read-only; else *No sheet waits for review* and the way to the hub.
- `<id>` is the session's start in UTC, `20261024T091200Z`, and names its record `<batch>/sessions/<id>.json`. The
  list and the page read the records, so a finished session is found again and one started in the terminal shows.
- While a render runs, every screen shows `● render 06:41`, its clock, linking to its session's page.

## 5 · The journeys

Each row is one frame: the trigger that leads to it, and its URL. `…` is `localhost:7717`. J1–J4 run in order on a
new batch; J5–J6 on one already rendered.

### J1 · First batch

| frame | trigger | URL |
|---|---|---|
| J1·1 Home, first start | — | `…/` |
| J1·2 the browser's file dialog, filtered to images | ⇧N New batch | `…/` |
| J1·3 the sheet, `reading 3 of 6` | choose 6 files, Open | `…/` |
| J1·4 the sheet, every file read: 2 converted, 1 RAW refused | reading ends | `…/` |
| J1·5 the hub, every cell a bare checkbox | ⌘↵ Import | `…/b/2026-10-19/hub` |

```
J1·1  LIBRARY · EMPTY
      No batches yet.
      Sources are copied into ~/isekai/. A photograph leaves this Mac only to be rendered:
      metadata stripped, held only in the GPU pod's memory, and gone when the pod is.
      [ New batch ⇧N ]                                              ← the accent

J1·4  ┌ New batch   6 files chosen · 5 sources · 1 refused                 [ Add files… ] ┐
      │ SOURCES · 5 · 7.3 MB                                 │ NAME                       │
      │ [00003.png] [16_01.png] [IMG_0412.jpg]  [still_04.jpg] │ [ 2026-10-19            ]  │
      │                          HEIC → JPEG    WEBP → JPEG    │                            │
      │ REFUSED · 1                                            │                            │
      │ ■ DSC_2291.NEF  A RAW photo (Nikon NEF).               │                            │
      │                 Fix: export it as JPEG from Photos, then add it.                    │
      └──────────────────────────────────────────────── [ Cancel esc ] [ Import ⌘↵ ] ┘
```

- Tiles are 124×164 with × at the top right; a converted tile carries its badge (mono 10px) and its name and size
  after conversion.
- While reading, the header says `reading 3 of 6` in `accent-ink`, tiles show `converting…` or `waiting`, and Import
  is disabled with `Reading 3 of 6`.

### J2 · Assign and Prepare

| frame | trigger | URL |
|---|---|---|
| J2·1 one cell assigned; the bar `1 change · Prepare ⌘↵` | arrow to 00003 × conjure, space | `…/b/2026-10-19/hub` |
| J2·2 three rows selected, summon ticked for all; `4 changes` | ⇧↓ ⇧↓, space on the summon header | same |
| J2·3 Prepare running: progress in the cells, totals in the job strip | ⌘↵ Prepare | same |
| J2·4 done: no bar; the Review tab counts the new sheets | the last cell finishes | same |

```
6 sources × 2 flows                          [ Add sources… ⇧A ]
SOURCE                 │ summon-anime-wai                 │ conjure-anime-wai
00003                  │ ☑ ▰▰▰▰▰▰ rendered ×1      ↵ view │ ☑ ▰▰▰▰▰▱ approved
[▣]                    │ [v1▢][v2▢]                       │
cowboy_shot_2_of_a_ver │ ☑ ▰▰▰▱▱▱ captioning…            │ ☐
y_long_name            │                                  │
[▣]                    │                                  │

        ┌ IMG_0430 × summon · …                 [ Discard ]  [ 3 changes · Prepare ⌘↵ ] ┐   PrepareBar
        ┌ 2 images ready to render                                        [ Render ⇧G ] ┐   RenderBar
```

- **The hub header** leaves a 12 px gap between its items. Add sources keeps its right alignment.
- **A cell:** unassigned, a bare 14px checkbox and nothing else. Otherwise the checkbox, the stage track — six
  13×4 segments, gap 3: assigned · tag · caption · sheet · approved · rendered; done `accent`, running `accent-dim`,
  the rest `line-disabled`; a draft shares the sheet segment — and the stage word in mono 12: `assigned`,
  `tagging…`, `captioning…`, `sheet`, `draft`, `approved`, `rendered ×n`. Running words are `accent-ink`.
- **The tick:** accent fill is assigned and can be unticked; `tick-locked` is prepared and stays (`prepared ·
  the tick stays`).
- **Focus** is `raised-2` with an inset 1px `focus` ring, and the cell's one action shows only on focus (`↵ review`,
  `↵ view` or, on the source cell, `↵ view photo` at its top right, taking no line). The hub keeps its focus for the open batch: `Esc` from a large
  view, the Back button and a tab switch come back to the cell left, else the first row's source cell.
- **A click or ↵ follows the stage**: unassigned or assigned ticks and unticks; tagged or unreadable does nothing; a
  sheet or a draft opens Review (`↵ review`); an approval with no image opens its sheet read-only (`↵ review`); a
  cell holding images opens the viewer on its newest (`↵ view`), `← →` `h l` step its images and `↵` opens the
  shown one's large view. The checkbox's own click only ticks.
- **A cell's images** sit at its foot, level with the source's thumbnail, under its stage track and any refusal,
  every approved version's, oldest to newest, each a 96×128 tile
  with its `vN` badge, wrapping; a click on one opens the viewer on it.
- **A cell's refusal** sits inside the cell with its fix; the cell returns to assigned, so the next Prepare retries
  it.
- **The PrepareBar** floats centred, bottom 50, 940 wide, `raised-2`, 1px `line-control`, radius 8. Pending: the
  cells named in mono 11, Discard, primary `n changes · Prepare ⌘↵`. Running: `Prepare · 1 of 3 cells done · 01:47`,
  Stop. The accepted-cell total stays fixed; the sheet-completed count and ticking elapsed time match JobStrip,
  including across a reload. Finished cells stay done, the rest stay assigned. Refused: the CLI's refusal (J8a), on a
  hub opened after the failure too. Disabled while another batch's Prepare runs: its reason (`Prepare is running on 2026-10-19`). There is no done state: the
  receipt goes to the job strip, the count to the Review tab. Running, a 2 px `accent` line slides along the bar's top
  edge, as on a running RenderBar, and a running segment pulses `accent-dim` ↔ `accent`; under
  `prefers-reduced-motion` both stand still, as the import bar's fill does, and the clocks still tick.
- **The RenderBar** takes the PrepareBar's place, on the hub and on Renders, once no change waits: `n images ready
  to render`, the render stage's own count, and primary `Render ⇧G`, disabled with its reason. With nothing short it
  is absent; while a render runs it shows the job strip's totals, `image 1 of 2 · 06:41 of ≤10:30`, and
  `Session ⇧S`.
- **The grid:** columns `250px 1fr 1fr…`, full width, no sidebar. Rows at least 84px. The source cell is the grid's
  first column, `h` from the first flow cell, and a column itself: the file's stem in mono 13, its first line level
  with the cells' tick line, the size in the viewer's title, then a 96×128 thumbnail at the cell's foot, a
  render tile's size, upright; a row checkbox appears in selection mode. A long name breaks inside the column, as
  it does on Renders, Review's rail and Home, never spilling out. A click
  on the thumbnail or `↵` opens the viewer on its photograph, `← →` stepping the batch's sources; space does nothing
  there.
- **The viewer** is a dialog over the page, its URL unchanged: the image fitted, a click for 1:1 pixels, `Esc` or a
  click outside to close, titled with the name, the dimensions and `fit n%` or `1:1`.

### J3 · Review and approve

With two or more flows waiting, the Review tab is a chooser, a row per flow; ↵ opens its head, esc on Review returns.

| frame | trigger | URL |
|---|---|---|
| J3·1 the batch's head, the first sheet in summon | ⇧R Review | `…/b/2026-10-19/review/0d4b7e6fb2a8/summon-anime-wai` |
| J3·2 a field edited, the empties marked, Count 2 | edit · Mark 6 empty fields intentional · count + | same |
| J3·3 the same sheet, approved and read-only; its rail mark ● | ⌘↵ Approve | same |
| J3·4 the next sheet in the rail | ⇧J | `…/review/<16_01's run>/summon-anime-wai` |

```
rail │ ① PHOTOGRAPH              │ ③ SHEET — DRAFT · saved 13:59      28 / 77 tokens │ ④ RENDERS
●    │ [photograph]              │ hair_colour   [blonde hair ×]                     │ images [−] 2 [+]
◐    │ ② CAPTION  231 words      │ eye_colour    [blue eyes ×]                       │ 1 [144     ]
○    │ one sentence a block …    │ …16 fields, 34px rows                             │ 2 [random  ]
     │                           │                                                   │ THE NEXT RENDER DRAWS
     │                           │                                                   │ 2 images · seed 144 + 1 random
     │                           │ [ Mark 7 empty fields intentional ]                       [ Approve sheet ⌘↵ ]
```

- The surface is today's review surface inside the shell: rail, ① source and ② caption, ③ sheet, approve bar. The
  sheet's kicker carries its receipt, never a path; there is no other header.
- **④ Renders**, a 230 px panel right of the sheet rows: one slot per image, its seed or `random`, and a stepper
  for how many — `−` drops the last random slot, else the last seed; never below one. A typed digit sets its slot
  at once; a seed already in another slot is refused in the slot. Listed seeds render first; the rest are drawn.
  Both are approved with the sheet. `Tab` walks `−`, `+` and the slots; `j` `k` move between the count and the
  slots. The line `THE NEXT RENDER DRAWS …` states the result.
- **The viewer**: the photograph opens in it, fitted, and `←` `→` step through the rail's photographs; a revision's
  render opens in it alone.
- **The rail**: the flow's name heads it, with a line under it for each other flow holding unapproved sheets,
  `summon-anime-wai · 1 waiting ⇧R`; ⇧R opens the chooser. It lists every sheet of the flow not yet rendered — unapproved, or
  approved and short of its images — and the one open, each marked ○ untouched, ◐ edited, ● approved, ◌ re-opened;
  its footer counts the approved among them. Revise opens the first draft it wrote; the rest wait in the rail.
  Approve stays on the sheet, read-only. ⇧J ⇧K step the rail. Approve still refuses an unmarked empty field.
- **Cancel approve**, grey-outlined beside the approved time, takes the approval back while nothing derives from it —
  no prompt, render group or copy — and the sheet is editable again; a copy's cancel deletes only the copy, and the
  sheet opens on the draft open above what lies beneath, else the approval beneath, read-only, the bar's note naming
  it as it names every approval shown. No key, no ask. Otherwise it is disabled, the review stage's reason beside it; while a render
  session runs for the batch, the reason says so.

### J4 · Render

| frame | trigger | URL |
|---|---|---|
| J4·1 the Render dialog: 4 images, 9 min, limit 13 min 30 s, about $0.06 | ⇧G Render | `…/b/2026-10-19/hub` — the dialog has none |
| J4·2 the session, image 2 of 4 | ⌘↵ Render · about $0.06 | `…/b/2026-10-19/sessions/20261019T152112Z` |
| J4·3 done: `Nothing is billing.` | the last image lands; teardown and volume down confirm | same |
| J4·4 Renders with the four new images | ⇧I View in Renders | `…/b/2026-10-19/renders` |

```
J4·1  RENDER · 2026-10-19 · ON A RENTED GPU                      Render 4 images
      summon-anime-wai 3 images · 00003 v1 count 2 · 16_01 v1 count 1
      conjure-anime-wai 1 image  · 00003 v1 count 1
      Not included: cowboy_shot_2 · summon is a draft.
      ESTIMATE  boot 3:00 · 4 images × 1:00 · teardown 2:00             9 min
                limit 1.5× the estimate                              13 min 30 s
      PRICE     pod 9 min at about $0.40/h                          about $0.06
                volume attached for the session                 under $0.01
                                     at the limit about $0.09
      ☐ Keep the volume open for 4 hours after the session        about $0.02
                                           [ Cancel esc ]  [ Render · about $0.06 ⌘↵ ]

J4·2  RENDER SESSION · STARTED 15:21:12 · 4 SHEETS
      06:41 of 13:30 at most      [▰▰▰▰▰▰▰▱▱▱▱▱▱]  the bar's width is the limit
      ● volume up         gpunit-isekai · attached                 0:21
      ● pod boot          gpunit-isekai                            2:04
      ◐ rendering         image 2 of 4 · 00003 · conjure-anime-wai · 4:16
      ○ teardown
      ○ volume down
      summon-anime-wai    [done]        [▨]                                  a column per photograph
                          [▨]                                                a cell's images stack
      conjure-anime-wai   [done]
      PHOTOGRAPHS         [00003]       [16_01]                              the photographs' row last
                                                               [ Stop session now ]
```

- **What renders**: every approved source × flow whose newest version holds fewer images than its Count,
  grouped by flow; a large batch collapses each flow to one line, the full list one click away. What is left out is
  named.
- **The estimate**: boot + images × time per image + teardown; until durations are recorded, 3:00, 1:00 and
  2:00. The limit is 1.5× the estimate, under the configured maximum, and teardown starts by itself at the limit. The
  price comes from the estimate: the pod at `pod_rate` (about $0.40/h), the volume at about $0.005/h.
- **The session** shows elapsed time against its limit, five steps always, and a grid of its images — no
  diffusion steps and no spend. A column per photograph the record plans, a row per flow, the photographs' row at
  the foot; a cell holds that flow's images of that photograph and a striped tile per image still to come, stacked,
  so a column stays one tile wide. A record that plans nothing places what landed. The first render takes the focus
  on opening and is the grid's tab stop; `h l` move between photographs, `j k` between rows, held at the
  photographs' row, and `↵` opens the viewer over the row. Stop goes straight to teardown; finished images are kept.
- **Done** is the step list all confirmed, the count and the duration, and `Nothing is billing.` only when both
  teardown steps are confirmed.

### J5 · Revise one image

| frame | trigger | URL |
|---|---|---|
| J5·1 Renders, before the revision | — | `…/b/2026-09-17/renders` |
| J5·2 the large view, no Compare yet | ↵ | `…/renders/0d4b7e6fb2a8/summon-anime-wai/v1/1840266731` |
| J5·3 the Revise confirm over it | ⇧E Revise this image | same |
| J5·4 Review of the revision: the render beside the photograph, the seed prefilled | ⌘↵ Write 1 draft and review | `…/b/2026-09-17/review/0d4b7e6fb2a8/summon-anime-wai` |
| J5·5 eye_colour edited | × `light` in eye_colour | same |
| J5·6 the revision approved, read-only; the hub's Render bar, `1 image ready to render` | ⌘↵ Approve · ⇧H | `…/b/2026-09-17/hub` |
| (J4·1–J4·3 for 1 image, 6 min, about $0.04) | ⇧G · ⌘↵ | `…/b/2026-09-17/sessions/<id>` |
| J5·7 Renders: v2 after v1, both marked `⇄` | ⇧I View in Renders | `…/b/2026-09-17/renders` |
| J5·8 the large view of v2, with `Compare with…  c` | ↵ on v2 | `…/v2/1840266731` |
| J5·9 before / after | c, ↵ on v1 in the tile picker | `…/v2/1840266731/compare/v1/1840266731` |

```
J5·4  ① PHOTOGRAPH · 1073×1406   RENDER BEING REVISED · seed 1840266731   [ Side by side ⌃P ]
      [photograph]               [render, accent hairline]       one height, top-aligned
      ② CAPTION  collapsed on a revision
      ③ SHEET — REVISION OF RENDER 1840266731 · saved 15:52
      eye_colour  • [blue eyes ×]      was light · blue eyes   │ ④ RENDERS  images [−] 1 [+]
                                                              │ 1 [1840266731]  prefilled, one slot per image
                                                              │ THE NEXT RENDER DRAWS 1 image · seed 1840266731
                                        [ Discard draft ]  [ Approve sheet ⌘↵ ]

J5·9  BEFORE · v1 · approved 14:12:40        AFTER · v2 · approved 15:52:10
      [render, equal size, top-aligned]      [render]
      same seed · 1840266731     1 FIELD CHANGED  eye_colour  light blue eyes → blue eyes
      another seed picked:  different seeds · 2216093514 → 1840266731 · same sheet when no field changed
```

- **Renders** is a grid of sources × flows, each source its upright thumbnail, opening the viewer. A
  cell is one wrapped row of thumbnails, versions oldest to newest, each with a `vN` badge and `⇄` in `accent-ink` when its
  seed is shared across versions. A damaged version is a striped tile before its images, its refusal under the
  cell. Last comes the ready tile, `ready · n images`, while the newest version lacks images of its Count, the render
  stage's own count. The Render bar offers them. The version's heading — `revision of v1` or `re-roll of v1`, the
  approval time, the Count and the seeds — is in the large view.
- **↵ always opens the large view**: the image on `ground-media`, the sheet it was rendered from beside it
  (filled fields only, read-only), and *Side by side* `⇧C`: the image beside its run's photograph, at one height,
  in one dialog. Its actions stand under the heading, above the fields: a column of full-width buttons, label left
  and key right, in groups 12 px apart — the writes, the comparisons, the way back. `Esc` and its back button go
  back to where it was opened, the hub or else Renders, focused on the cell or the image left.
  `Compare with…  c` appears when its cell holds another image, and with one other compares at once. Else it
  opens a dialog of the cell's other images as tiles at Renders' size, every version's and seed's, oldest first,
  `vN · seed` under each, focused on the newest older version of this seed, else the image before this one;
  `h j k l` and the arrows move, `↵` or a click compares, the older of the two before. The same-seed address, `…/compare`, still compares with the newest
  older version of the seed. Each flow of the batch drafted from a sheet alone is offered as *Conjure from this*,
  the first on `⇧F`: it drafts that flow from this image's approval and opens Review, which marks its draft
  against that flow's sheet, names the approval in the kicker and offers *Discard draft*; a refusal shows under
  the actions.
- **Revise** (the verb `isekai revise`): the confirm lists each image — source × flow × seed, the version it copies,
  the seed it prefills. All or nothing: a refusal lists every selected image, those that could be revised
  too, and offers `Deselect those 2 and revise 1 ⇧↵`; it has no primary button.
  An image whose flow holds a waiting draft opens Review on that draft, writing nothing. In a selection it is left
  out, the rest written, and the confirm names it `already waiting`, then offers `Review ⌘↵`.
- **The revision's sheet** marks changed rows with an accent gutter dot and a `was` line against the rendered sheet,
  and keeps them once approved.
- **Approve refuses an unchanged revision** — neither fields nor ④ changed — naming the image it would reproduce
 . *Discard draft*, 12 px left of Approve, asks, then deletes this unapproved draft, through `review --discard`;
  the sheet stays open.
- **One header row** names the photograph and its size, and the render and its seed, over the pair, with *Side by
  side* `⌃P` at its right: one dialog, the pair at one height, fit only, `Esc` to close. No how-to text. A click on
  either image opens it in the viewer. Every receipt sits in ③'s kicker, `· saved 15:52` or `APPROVED 14:12:40`, and every refusal in the
  approve bar.

### J6 · Re-roll

| frame | trigger | URL |
|---|---|---|
| (the large view of 00003 · conjure v1, as J5·2; the confirm, as J5·3) | ↵ · ⇧E · ⌘↵ | `…/renders/0d4b7e6fb2a8/conjure-anime-wai/v1/2216093514` |
| J6·1 Review: the seed cleared, Count 3, the tags untouched | × the seed · count + + | `…/review/0d4b7e6fb2a8/conjure-anime-wai` |
| (J4 for 3 images, 8 min, about $0.05) | ⌘↵ Approve · ⇧G · ⌘↵ | `…/b/2026-09-17/sessions/<id>` |
| J6·2 Renders: three new images after v1, no pair | ⇧I | `…/b/2026-09-17/renders` |

Changes in ④ are marked like changed fields: the gutter dot and `was 1 in v1`, `was 1840266731 · cleared`.

### J7 · Add sources to a batch

| frame | trigger | URL |
|---|---|---|
| J7·1 Home, the library | — | `…/` |
| J7·2 its hub | ↵ on 2026-09-17 | `…/b/2026-09-17/hub` |
| (the file dialog, as J1·2) | ⇧A Add sources… | same |
| J7·3 the sheet without a name: one `already here`, one copied as `16_01-2.png`, one HEIC converted | Open; reading ends | same |
| J7·4 two new rows, bare checkboxes | ⌘↵ Import 2 | same |

```
J7·1  LIBRARY · 4 batches · newest activity first                              [ New batch ⇧N ]
      2026-09-17  6 sources  [summon-anime-wai 2/5 approved · 1/5 rendered]
                             [conjure-anime-wai 1/2 approved · 0/2 rendered]  today 15:31 · render · open ↵
      ▢▢▢▢▢▢▢ +5
      old exports      ▨ Not a batch: no sources/ folder inside. Move it out of ~/isekai/ in Finder
                         to clear this row.                                                  can't be opened
```

- **Home's row**: a header line — the name, `n sources`, one chip per flow present (its denominator the sources that
  have it; chips wrap), `n sources without a flow`, and at the right last activity, the time and kind of the newest
  file written in the batch, then `open ↵` — over up to fifteen 84×114 thumbnails then `+n`, at the full width,
  wrapping in a narrow window. Sorted by last activity; a folder without `sources/`
  sorts last, striped and inert; dot-folders, `.staging` among them, are not listed.
- **A running render's row** has an accent left edge (`inset 2px 0 0`), background `#1b1c2c`,
  `● render running · 06:41` and `image 1 of 2`.
- **`already here`** is the same bytes as a source in the batch: dimmed, skipped. A different file with a taken name
  is copied as `<stem>-2` and says `chosen as 16_01.png`.

### J8 · When it goes wrong

- **J8a, Prepare refused** — from J2·2, ⌘↵. The bar shows the CLI's refusal; nothing ran, the cells stay assigned.
  Start Ollama outside the app, then ⌘↵ again → J2·3. URL `…/b/2026-10-19/hub`.
- **J8b, teardown unconfirmed** — from J4·2, teardown gets no answer. The band shows on every screen; *Resolve*
  opens the alert at `…/billing`. Ways out, each ending in **Check again**, which asks gpunit: Check again itself;
  `uv run --env-file .env gpunit down`, then Check again; stop it in RunPod's console, then Check again. It clears
  only when gpunit confirms the pod gone → the band goes, the receipt stays.
- **J8c, the volume past its window** — Home with the quiet job-strip item; at the window's end the band:
  `Volume gpunit-isekai is still open past its window and is billing.`, `window ended 19:38`,
  `or uv run --env-file .env gpunit volume down`, **Close volume** (the same command). gpunit confirms → J7·1.
- **A volume that may be billing** after a session is J8b's shape with `uv run --env-file .env gpunit volume down`.

## 6 · States no journey draws

| screen | state | what shows |
|---|---|---|
| Home | loading | rows paint with folder names; counts and thumbnails fill per row |
| Home | the library cannot be created | a full-page refusal naming the permission problem |
| New batch | name taken | the refusal with a free name offered, `use 2026-10-19 2 ⇧↵`; Import disabled `Choose a name that isn't taken` |
| New batch | name unusable | `A name can't contain /, start with a dot, or be empty.` |
| New batch | nothing usable | Import disabled `None of the chosen files could be read.` |
| New batch | cancel | the staging folder is deleted; the library is unchanged |
| Hub | loading | placeholder rows, `reading 2 of 6` |
| Hub | a damaged run | the cell reads `unreadable`, with the CLI's refusal (path, line and column) and its fix; the rest of the grid works |
| Hub | a render running | Render disabled `A render session is running · 06:41 of ≤10:30` |
| Hub | Prepare disabled | the bar keeps its cells, reason `Prepare is running on 2026-10-19` |
| Hub | Add sources, nothing new | Import disabled `Nothing new to add` |
| Hub | the batch is gone | a full-page refusal, `Back to the library ⇧L` |
| Render | refused before billing | the CLI's refusal: no GPU free, no key in `.env`; `nothing billed` when true |
| Render | disabled | `A pod may still be billing.` |
| Renders | empty | each short cell's ready tile and the Render bar; with nothing approved, the Review tab's count |
| Renders | a missing image | `its record is there, its image is gone`, the path in the fix |
| Renders | Revise disabled | `No image selected` |

## 7 · Keys

Matched on `event.code`, the physical key, with the typed character suppressed, and declared once in
the key store ([D25](../../docs/decisions.md#d25--shortcuts-match-the-physical-key)); `⌃/` lists them. ⌘
is Ctrl off macOS. Inside a text field only esc, ⌘↵, ⌘Z, ⇧⌘Z, ⌘K and ⌃/ run, Review's ⌃P, and on macOS Review's
⌃H ⌃L ⌃J ⌃K.

| where | keys |
|---|---|
| everywhere | ⇧L the library · ⇧H Hub · ⇧R Review's head · ⇧I Renders · ⇧S the running session, else the batch's sessions · ⌃/ the key list, from a field too · ⌘↵ the outlined action · esc leaves a field, then closes an overlay, never a billing alert |
| Home | ⇧N New batch · j k or ↓↑ ↵ the library |
| Hub | h j k l or ←↓↑→ cells, the source column first · space tick / untick, or a column for the selected rows · ⇧J ⇧K or ⇧↓↑ select rows · ↵ the cell's action, on the source the viewer · in the viewer, ← → h l step, ↵ the large view · ⌘↵ Prepare · ⇧A Add sources · ⇧G Render · esc clears the selection |
| Review | h l or ←→ the panes: the rail, the photograph, the sheet, ④, and ⌃H ⌃L from a field on macOS · ⌃J ⌃K the fields from a field on macOS · j k or ↓↑ in each: the input, a scroll, the rows · ⇧J ⇧K or ⇧↓↑ the rail · ⌃E ⌃Y scroll the photograph · ⌃P the photograph, on a revision Side by side, from a field too, ← → its photographs · ⌘↵ Approve · ⌘Z ⇧⌘Z · ⌘K the tag cheatsheet · autocomplete ↑↓ ↵ esc · ⇧E revise and ⌘↓ walk refusals, when built · ⇧↵ take every suggested spelling · the collapsed caption, its key named when built |
| Renders | h l or ←→ images, across cells, into the source at a row's start · j k or ↓↑ sources, keeping the column · space select · ↵ the large view, on the source the viewer · ⇧E Revise · ⇧G Render · in the large view, ⇧E Revise, ⇧F Conjure from this, c Compare with…, ⇧C *Side by side*, esc back · in compare, `\` swap, esc back |
| Session | h l or ←→ photographs · j k or ↓↑ rows, held at the photographs' row · ↵ the viewer over the row |
| dialogs | ⌘↵ confirm · ⇧↵ the secondary confirm · esc cancel, held while an import commits |

No key spends money but the Render dialog's ⌘↵, which confirms the price it quotes: ⇧G only opens the dialog.

## 8 · The job lifecycle and live state

**Each slot, Prepare's and the render's, runs this lifecycle on its own**; neither waits on the other.

```
idle ──confirm──▶ running ──▶ (render) teardown ──▶ done ──▶ idle
                    ├─ refused before start ───────────────▶ idle      nothing written, nothing billed
                    ├─ stopped ─────────────▶ teardown or done        finished work kept
                    └─ teardown or volume unconfirmed ─▶ unresolved ──gpunit confirms gone──▶ idle
```

- **A job is the CLI**: the server runs `python -m isekai …` as a child process; Import and reading files are
  not jobs. A job outlives the tab; stopping the server sends each running job SIGINT at once, so `render` tears
  down.
- **Progress is the CLI's**: stage verbs and `render` take `--progress json` and print one JSON line per step
  (`{"cell": …, "step": "caption", "state": "running"}`, `{"image": 2, "of": 4}`,
  `{"step": "teardown", "state": "confirmed"}`). The server reads the child's stdout; the human output still goes to
  `log.txt`, each line naming its job — `[prepare] …`, `[render] …` — and the UI never parses it.
- **The page is told over SSE**: one stream, `/events`, a full snapshot on every connect — both job slots, the
  open batch's cells, the open import's files, billing state — then only changes. The stream names the page's
  batch and its open import, and opens again when either changes. Actions are HTTP POSTs.
- **The hub's cells** are a listing of `runs/`, read again on each progress event.
- **gpunit is asked** every ~30 s while a session runs or an alert is unresolved, on Check again, and once at
  server start. The volume item and its band run on a timer from the window's end gpunit recorded locally. Idle, the
  app reaches nothing.
- **Ollama is probed** only when Prepare starts.

## 9 · Copy from the CLI

The UI shows a refusal as the CLI prints it. **Where the design's wording differs from today's CLI, the CLI's
text ships**, and the version that builds that screen decides whether to reword the CLI so it reads on both surfaces.
The known case:

| the design wrote | the CLI says today, at `45babd9` |
|---|---|
| `Ollama isn't answering on 127.0.0.1:11434.` / `Start Ollama, then press Prepare again.` | `nothing is listening at http://127.0.0.1:11434, and the reader and the JoyCaption tagger need it; start the runtime (`ollama serve`), then run this command again` (`isekai/boundary/ollama.py:234`) |

*"then run this command again"* does not read on a button — a reason for run flow's change to reword the CLI's
endings once, for both surfaces. The key is `RUNPOD_API_KEY` in `.env` (`.env.example:6`).

## 10 · Which version builds what

| version | builds |
|---|---|
| **ui groundwork** | the shell — AppBar, JobStrip, BillingBanner's slot; tokens; routes with the batch (§4); `isekai ui` with no arguments over `ISEKAI_LIBRARY`; Home and the library (J7·1, Home's states); the hub grid as a listing, focus, keys (§7), the cheatsheet; Review inside the shell with its queue; vitest and Playwright, the fakes behind `ISEKAI_WIRING=<module>:<factory>` |
| **run flow** | New batch and Add sources (J1, J7) — the upload, staging, `isekai import` and conversion; `isekai assign`; ticking, multi-select, the PrepareBar and Prepare as a job (J2, J8a); `--progress json` on the stage verbs; the job slot; SSE `/events` with the snapshot |
| **render** | the Render dialog, the session, done (J4); ④ editable, Count and Seeds through approve; `render <runs>` rendering what is short; the scaled limit and recorded durations; Renders, the large view; the billing alerts and the volume item (J8b, J8c); `--progress json` on `render` |
| **revise** | `isekai revise`, the confirm and its refusal; Review of a revision (J5·4–J5·6); `review --discard`; compare (J5·8, J5·9); re-roll (J6) |
