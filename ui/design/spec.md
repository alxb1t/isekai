# isekai app — design spec

**The design the UI is built to**: rules, tokens, the shell, routes, the journeys, the states, keys and live state,
and which part each version of the UI arc builds — import and assign, render, revise. Drawn in Claude Design and
checked against the repo at `45babd9`. [§10](#10--which-version-builds-what) says which version builds what.

Vue 3 single-file components, plain CSS, no component library — the stack `ui/` already uses.

---

## 1 · Rules on every screen

1. **Text is state, a disabled action's reason, or a refusal's fix**. No helper text, legends or how-to
   sentences. Key hints inside buttons and the bottom key bar are allowed. The one exception is the privacy line on
   first start.
2. **No file path on screen**, except inside a refusal's fix, written as the CLI prints it. Display names stay
   short (`00003`, `16_01`).
3. **One accent-outlined action per screen**: the next forward action, or none. Everything else is outlined
   grey.
4. **A disabled button has its reason beside it**, never in a tooltip.
5. **A refusal** is a 7×7 accent square, the reason in `ink`, then the fix in `ink-2`. A command or an offered value
   inside the fix is mono, `accent-ink`.
6. **One job slot**, Prepare or Render. While a job runs, only actions that would start another job are
   disabled. An unresolved billing alert holds the slot until gpunit confirms the pod or volume gone.
7. **No money after the Render quote**.
8. **The URL is real**. Overlays keep the URL of the page beneath. The Render dialog has no URL.
9. **A refusal's text is the CLI's, verbatim**. The UI invents no command.
10. **Count labels use the singular noun at one and the plural otherwise**: `1 source`, `0 sources`, `3 sources`.

## 2 · Tokens

| token | value | use |
|---|---|---|
| `--ground` | `#161724` | app background |
| `--ground-deep` | `#11121c` | app bar, rail, job strip, fields |
| `--ground-media` | `#0e0f17` | large view, compare, photo overlay |
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
┌ isekai  2026-09-17   Hub ⌥1  Review ⌥2  Renders ⌥3      flow [all|summon|conjure] ⌥←→  ⌥Space keys ┐ AppBar 40
├─ BillingBanner (only when something may be billing; filled accent, cannot be dismissed) ───────────┤
│                                                                                                     │
│                                   <the route's screen>                                              │
│                                                                                                     │
├─ ○ job · idle   last: render · 2026-09-17 · ended 15:38 · 1 image        volume open · until 19:38 ┤ JobStrip 28
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **AppBar**, `ground-deep`, bottom border `line`. The wordmark goes Home. The place is mono 12px `ink-2`: `library`
  on Home, else the batch name. Tabs only inside a batch; the active one has a 2px accent underline. The flow
  switcher is a segmented control; Review drops `all`.
- **BillingBanner**, a filled accent band, text `#0f1018` at 600. Three variants: the volume past its window, a pod
  that may be billing, a volume that may be billing. esc never closes it.
- **JobStrip**, `ground-deep`, mono 11px. Its dot: hollow idle, accent running, accent square unresolved. Then a label
  (`job · prepare`) and totals (`1 of 3 cells done · 01:47`, `image 1 of 2 · 06:41 of ≤10:30`), or the last
  job's receipt. Prepare keeps the accepted-cell total fixed, counts cells completed at sheet and ticks
  elapsed time every second from its original start. On the right, while the volume is open, the quiet item
  `volume open · until 19:38 · close`.

## 4 · Routes

| route | screen | opens over it |
|---|---|---|
| `/` | Home | the New batch sheet |
| `/b/<batch>/hub` | Hub | the Add sources sheet, the Prepare bar, the Render dialog |
| `/b/<batch>/review/<run>/<flow>` | Review | the cheatsheet, the photo overlay |
| `/b/<batch>/renders` | Renders grid | the Revise confirm |
| `/b/<batch>/renders/<run>/<flow>/<version>/<seed>` | large view | the Revise confirm |
| `/b/<batch>/renders/<run>/<flow>/<version>/<seed>/compare` | before / after | — |
| `/session` | the render session | — |

- `<run>` is the run's **12-hex digest** (`0d4b7e6fb2a8`), unique by construction; the screen shows the short name
 .
- `<version>` is `v` + the approval's number (`v2` is `review/002.approved.json`, rendered into `outputs/002/`).
- `/session` exists only while a session runs or an alert is unresolved; otherwise it redirects to Home.

## 5 · The journeys

Each row is one frame: the trigger that leads to it, and its URL. `…` is `localhost:7717`. J1–J4 run in order on a
new batch; J5–J6 on one already rendered.

### J1 · First batch

| frame | trigger | URL |
|---|---|---|
| J1·1 Home, first start | — | `…/` |
| J1·2 the browser's file dialog, filtered to images | ⌥N New batch | `…/` |
| J1·3 the sheet, `reading 3 of 6` | choose 6 files, Open | `…/` |
| J1·4 the sheet, every file read: 2 converted, 1 RAW refused | reading ends | `…/` |
| J1·5 the hub, every cell a bare checkbox | ⌘↵ Import | `…/b/2026-10-19/hub` |

```
J1·1  LIBRARY · EMPTY
      No batches yet.
      Sources are copied into ~/isekai/. A photograph leaves this Mac only to be rendered:
      metadata stripped, held only in the GPU pod's memory, and gone when the pod is.
      [ New batch ⌥N ]                                              ← the accent

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
| J2·4 done: no bar, the accent on Review next | the last cell finishes | same |

```
6 sources × 2 flows         [ Add sources… ⌥A ]  [ Review next · 16_01 conjure ⌥2 ]  [ Render 2 ⌥R ]
SOURCE                 │ summon-anime-wai                 │ conjure-anime-wai
[▣] 00003              │ ☑ ▰▰▰▰▰▰ rendered ×1      ↵ view │ ☑ ▰▰▰▰▰▱ approved
    00003.png · 832×1216│                                  │
[▣] cowboy_shot_2      │ ☑ ▰▰▰▱▱▱ captioning…            │ ☐
[▣] IMG_0430           │ ☑ ▰▱▱▱▱▱ assigned                │ ☐
↑↓←→ move · space tick / untick · ⇧↑↓ select rows · ↵ the cell's action · ⌥A add sources · ⌥R render

        ┌ IMG_0430 × summon · …                 [ Discard ]  [ 3 changes · Prepare ⌘↵ ] ┐   PrepareBar
```

- **The hub header** leaves a 12 px gap between its items. Add sources keeps its right alignment.
- **A cell:** unassigned, a bare 14px checkbox and nothing else. Otherwise the checkbox, the stage track — six
  13×4 segments, gap 3: assigned · tag · caption · sheet · approved · rendered; done `accent`, running `accent-dim`,
  the rest `line-disabled`; a draft shares the sheet segment — and the stage word in mono 12: `assigned`,
  `tagging…`, `captioning…`, `sheet`, `draft`, `approved`, `rendered ×n`. Running words are `accent-ink`.
- **The tick:** accent fill is assigned and can be unticked; `tick-locked` is prepared and stays (`prepared ·
  the tick stays`).
- **Focus** is `raised-2` with an inset 1px `focus` ring, and the cell's one action shows only on focus (`↵ review`).
- **A cell's refusal** sits inside the cell with its fix; the cell returns to assigned, so the next Prepare retries
  it.
- **The PrepareBar** floats centred, bottom 50, 940 wide, `raised-2`, 1px `line-control`, radius 8. Pending: the
  cells named in mono 11, Discard, primary `n changes · Prepare ⌘↵`. Running: `Prepare · 1 of 3 cells done · 01:47`,
  Stop. The accepted-cell total stays fixed; the sheet-completed count and ticking elapsed time match JobStrip,
  including across a reload. Finished cells stay done, the rest stay assigned. Refused: the CLI's refusal (J8a). Disabled: its reason (`A render is running ·
  06:41`). There is no done state: the receipt goes to the job strip, the accent to Review next.
- **The grid:** columns `250px 1fr 1fr…`, full width, no sidebar. Rows at least 84px. The source cell is a
  44×60 thumbnail, upright, that opens the viewer, the file's stem in mono 13 and mono 11 `file · dims`, the size
  read from the file; a row checkbox appears in selection mode.
- **The viewer** is a dialog over the page, its URL unchanged: the image fitted, a click for 1:1 pixels, `Esc` or a
  click outside to close, titled with the name, the dimensions and `fit n%` or `1:1`.

### J3 · Review and approve

| frame | trigger | URL |
|---|---|---|
| J3·1 the first sheet in summon's queue | ⌥2 Review next | `…/b/2026-10-19/review/0d4b7e6fb2a8/summon-anime-wai` |
| J3·2 a field edited, the empties marked, Count 2 | edit · Mark 6 empty fields intentional · count + | same |
| J3·3 the next unapproved sheet in summon | ⌘↵ Approve | `…/review/<16_01's run>/summon-anime-wai` |
| J3·4 the hub, `Render 3` takes the accent | ⌘↵ Approve on the last one | `…/b/2026-10-19/hub` |

```
rail │ ① SOURCE                  │ ③ SHEET — DRAFT  9 filled · 7 empty · drafted 13:59:30    28 / 77 tokens
●    │ [photograph]              │ hair_colour   [blonde hair ×]
◐    │ ② CAPTION  231 words      │ eye_colour    [blue eyes ×]
○    │ one sentence a block …    │ …16 fields, 34px rows
     │                           │ ④ RENDERS   count [− 1 +]   seeds [ + seed ]
     │                           │   THE NEXT RENDER DRAWS 1 image · random seed
     │                           │ [ Mark 7 empty fields intentional ]            [ Approve sheet ⌘↵ ]
```

- The surface is today's review surface inside the shell: rail, ① source and ② caption, ③ sheet, approve bar. The
  sheet header carries counts and a time, never a path.
- **④ Renders**: Count (a stepper, default 1, never below the number of seeds listed) and Seeds (a list,
  default empty). Listed seeds render first; the rest of Count are drawn. Both are approved with the sheet. The line
  `THE NEXT RENDER DRAWS …` states the result.
- **The queue**: Review next opens the unapproved sheets of the first flow that has any, in grid order;
  Revise opens the drafts it wrote. Approve moves to the next; after the last, the hub. ⌥↑↓ steps without approving.
  Approve still refuses an unmarked empty field.

### J4 · Render

| frame | trigger | URL |
|---|---|---|
| J4·1 the Render dialog: 4 images, 9 min, limit 13 min 30 s, about $0.06 | ⌥R Render 3 | `…/b/2026-10-19/hub` — the dialog has none |
| J4·2 the session, image 2 of 4 | ⌘↵ Render · about $0.06 | `…/session` |
| J4·3 done: `Nothing is billing.` | the last image lands; teardown and volume down confirm | `…/session` |
| J4·4 Renders with the four new images | ⌥3 View in Renders | `…/b/2026-10-19/renders` |

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
      IMAGES  [done] [striped until finished] …                [ Stop session now ]
```

- **What renders**: every approved source × flow whose newest version holds fewer images than its Count,
  grouped by flow; a large batch collapses each flow to one line, the full list one click away. What is left out is
  named.
- **The estimate**: boot + images × time per image + teardown; until durations are recorded, 3:00, 1:00 and
  2:00. The limit is 1.5× the estimate, under the configured maximum, and teardown starts by itself at the limit. The
  price comes from the estimate: the pod at `pod_rate` (about $0.40/h), the volume at about $0.005/h.
- **The session** shows elapsed time against its limit, five steps always, and tiles striped until each image is
  finished — no diffusion steps and no spend. Stop goes straight to teardown; finished images are kept.
- **Done** is the step list all confirmed, the count and the duration, and `Nothing is billing.` only when both
  teardown steps are confirmed.

### J5 · Revise one image

| frame | trigger | URL |
|---|---|---|
| J5·1 Renders, before the revision | — | `…/b/2026-09-17/renders` |
| J5·2 the large view, no Compare yet | ↵ | `…/renders/0d4b7e6fb2a8/summon-anime-wai/v1/1840266731` |
| J5·3 the Revise confirm over it | ⌥E Revise this image | same |
| J5·4 Review of the revision: the render beside the photograph, the seed prefilled | ⌘↵ Write 1 draft and review | `…/b/2026-09-17/review/0d4b7e6fb2a8/summon-anime-wai` |
| J5·5 eye_colour edited | × `light` in eye_colour | same |
| J5·6 the hub, `Render 1` takes the accent | ⌘↵ Approve — Revise's queue ends | `…/b/2026-09-17/hub` |
| (J4·1–J4·3 for 1 image, 6 min, about $0.04) | ⌥R · ⌘↵ | `…/session` |
| J5·7 Renders: v2 above v1, both labelled `⇄ 1840266731` | ⌥3 View in Renders | `…/b/2026-09-17/renders` |
| J5·8 the large view of v2, with `Compare with v1  C` | ↵ on v2 | `…/v2/1840266731` |
| J5·9 before / after | C | `…/v2/1840266731/compare` |

```
J5·4  ① SOURCE  [photograph] │ RENDER BEING REVISED [render, accent hairline]
      ② CAPTION  collapsed on a revision · ⌥↓
      ③ SHEET — REVISION OF RENDER 1840266731   1 field changed · saved 15:52:04
      eye_colour  • [blue eyes ×]      was light · blue eyes
      ④ RENDERS  count [− 1 +]   seeds prefilled [1840266731 ×] [ + seed ]
                 THE NEXT RENDER DRAWS 1 image · seed 1840266731

J5·9  BEFORE · v1 · approved 14:12:40        AFTER · v2 · approved 15:52:10
      [render, equal size, top-aligned]      [render]
      same seed · 1840266731     1 FIELD CHANGED  eye_colour  light blue eyes → blue eyes
      \ swap in place · ← → next revised image · esc back                  [ Revise again ⌥E ]
```

- **Renders** is a grid of sources × flows. In each cell, versions newest first; the header line gives the version,
  `revision of v1` or `re-roll of v1`, the approval time, the Count and the seeds. A seed shared across versions is
  labelled `⇄ seed` in `accent-ink`.
- **↵ always opens the large view**: the image on `ground-media`, the sheet it was rendered from beside it
  (filled fields only, read-only), the photograph a key away (⌥C). `Compare with v1  C` appears when another version
  of the same source × flow shares the seed; with several, it compares with the newest older one.
- **Revise** (the verb `isekai revise`): the confirm lists each image — source × flow × seed, the version it copies,
  the seed it prefills. All or nothing: a refusal lists every selected image, those that could be revised
  too, and offers `Deselect those 2 and revise 1 ⌥↵`; it has no primary button.
- **The revision's sheet** marks changed rows with an accent gutter dot and a `was` line against the rendered sheet.
- **Approve refuses an unchanged revision** — neither fields nor ④ changed — naming the image it would reproduce
 . *Discard revision* deletes this unapproved draft, through `review --discard`.

### J6 · Re-roll

| frame | trigger | URL |
|---|---|---|
| (the large view of 00003 · conjure v1, as J5·2; the confirm, as J5·3) | ↵ · ⌥E · ⌘↵ | `…/renders/0d4b7e6fb2a8/conjure-anime-wai/v1/2216093514` |
| J6·1 Review: the seed cleared, Count 3, the tags untouched | × the seed · count + + | `…/review/0d4b7e6fb2a8/conjure-anime-wai` |
| (J4 for 3 images, 8 min, about $0.05) | ⌘↵ Approve · ⌥R · ⌘↵ | `…/session` |
| J6·2 Renders: three new images above v1, no pair | ⌥3 | `…/b/2026-09-17/renders` |

Changes in ④ are marked like changed fields: the gutter dot and `was 1 in v1`, `was 1840266731 · cleared`.

### J7 · Add sources to a batch

| frame | trigger | URL |
|---|---|---|
| J7·1 Home, the library | — | `…/` |
| J7·2 its hub | ↵ on 2026-09-17 | `…/b/2026-09-17/hub` |
| (the file dialog, as J1·2) | ⌥A Add sources… | same |
| J7·3 the sheet without a name: one `already here`, one copied as `16_01-2.png`, one HEIC converted | Open; reading ends | same |
| J7·4 two new rows, bare checkboxes | ⌘↵ Import 2 | same |

```
J7·1  LIBRARY · 4 batches · newest activity first                              [ New batch ⌥N ]
      BATCH            SOURCES  ▢▢▢▢▢▢▢+5  FLOWS                                         LAST ACTIVITY ↓
      2026-09-17       6 sources [thumbs]  [summon-anime-wai 2/5 approved · 1/5 rendered]
                                           [conjure-anime-wai 1/2 approved · 0/2 rendered]  today 15:31
                                           1 source without a flow                          render · 1 image   open ↵
      old exports      ▨ Not a batch: no sources/ folder inside. Move it out of ~/isekai/ in Finder
                         to clear this row.                                                  can't be opened
```

- **Home's row**: the name, `n sources`, up to seven 28×38 thumbnails then `+n`, one chip per flow present
  (its denominator the sources that have it; chips wrap), `n sources without a flow`, and last activity — the time
  and kind of the newest file written in the batch. Sorted by last activity; a folder without `sources/`
  sorts last, striped and inert; dot-folders, `.staging` among them, are not listed.
- **A running render's row** has an accent left edge (`inset 2px 0 0`), background `#1b1c2c`,
  `● render running · 06:41` and `image 1 of 2`.
- **`already here`** is the same bytes as a source in the batch: dimmed, skipped. A different file with a taken name
  is copied as `<stem>-2` and says `chosen as 16_01.png`.

### J8 · When it goes wrong

- **J8a, Prepare refused** — from J2·2, ⌘↵. The bar shows the CLI's refusal; nothing ran, the cells stay assigned.
  Start Ollama outside the app, then ⌘↵ again → J2·3. URL `…/b/2026-10-19/hub`.
- **J8b, teardown unconfirmed** — from J4·2, teardown gets no answer. The band shows on every screen; *Resolve* or ⌥4
  opens the alert at `…/session`. Ways out, each ending in **Check again**, which asks gpunit: Check again itself;
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
| New batch | name taken | the refusal with a free name offered, `use 2026-10-19 2 ⌥↵`; Import disabled `Choose a name that isn't taken` |
| New batch | name unusable | `A name can't contain /, start with a dot, or be empty.` |
| New batch | nothing usable | Import disabled `None of the chosen files could be read.` |
| New batch | cancel | the staging folder is deleted; the library is unchanged |
| Hub | loading | placeholder rows, `reading 2 of 6` |
| Hub | a damaged run | the cell reads `unreadable`, with the CLI's refusal (path, line and column) and its fix; the rest of the grid works |
| Hub | a render running | Render disabled `A render session is running · 06:41 of ≤10:30`; the accent on Review next |
| Hub | Prepare disabled | the bar keeps its cells, reason `A render is running · 06:41` |
| Hub | Add sources, nothing new | Import disabled `Nothing new to add` |
| Hub | the batch is gone | a full-page refusal, `Back to the library ⌥0` |
| Render | refused before billing | the CLI's refusal: no GPU free, no key in `.env`; `nothing billed` when true |
| Render | disabled | `Every approved source × flow already has its Count of images.` · `Prepare is running · 01:42` · `A pod may still be billing.` |
| Renders | empty | the count of approvals short of their Count, with Render; with nothing approved, Review next |
| Renders | a missing image | `its record is there, its image is gone`, the path in the fix |
| Renders | Revise disabled | `No image selected` · `Prepare is running · 01:42` |

## 7 · Keys

Matched on `event.code`, the physical key, with the typed character suppressed; ⌥0–⌥4 fire inside text
fields, ⌥R and ⌥E do not fire inside a chip input.

| where | keys |
|---|---|
| everywhere | ⌥0 Home · ⌥1 Hub · ⌥2 Review · ⌥3 Renders · ⌥4 the session · ⌥← → flow · ⌥Space the cheatsheet · ⌘↵ the outlined action · esc closes an overlay, never a billing alert |
| Home | ⌥N New batch · ↑↓ ↵ the library |
| Hub | ↑↓←→ cells · space tick / untick, or a column for the selected rows · ⇧↑↓ select rows · ↵ the cell's action · ⌥A Add sources · ⌥R Render |
| Review | ⌘Z ⇧⌘Z · ⌥↑↓ the queue · ⌘↵ Approve · autocomplete ↑↓ ↵ esc · ⌃↓ walk refusals · ⌥↵ take every suggested spelling · ⌥C photo and render, on a revision · ⌥↓ the collapsed caption |
| Renders | ↑↓←→ images · space select · ↵ the large view · C compare, in the large view · `\` swap, in compare · ⌥E Revise |
| dialogs | ⌘↵ confirm · esc cancel |

No key spends money: ⌥R opens the dialog, and only its ⌘↵ starts billing.

## 8 · The job lifecycle and live state

```
idle ──confirm──▶ running ──▶ (render) teardown ──▶ done ──▶ idle
                    ├─ refused before start ───────────────▶ idle      nothing written, nothing billed
                    ├─ stopped ─────────────▶ teardown or done        finished work kept
                    └─ teardown or volume unconfirmed ─▶ unresolved ──gpunit confirms gone──▶ idle
```

- **A job is the CLI**: the server runs `python -m isekai …` as a child process; Import and reading files are
  not jobs. A job outlives the tab; stopping the server sends it SIGINT, so `render` tears down.
- **Progress is the CLI's**: stage verbs and `render` take `--progress json` and print one JSON line per step
  (`{"cell": …, "step": "caption", "state": "running"}`, `{"image": 2, "of": 4}`,
  `{"step": "teardown", "state": "confirmed"}`). The server reads the child's stdout; the human output still goes to
  `log.txt`, which the UI never parses.
- **The page is told over SSE**: one stream, `/events`, a full snapshot on every connect — the job slot, the
  open batch's cells, billing state — then only changes. Actions are HTTP POSTs.
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
