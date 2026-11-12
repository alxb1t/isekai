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
| `--accent` | `#8d82e6` | the primary outline, pending (assigned or tagged) tick, running dot, refusal square, billing band |
| `--accent-dim` | `#5a5296` | the running segment of a stage track |
| `--accent-ink` | `#b3abf4` | commands, running words (`captioning…`) |
| `--tick-locked` | `#34364a` | a prepared, locked tick |
| `--chip-line` | `#2f3146` | an import row's badge border |
| `--chain-ground` | `#1f2036` | the ground of the shown row of a render's chain |
| `--chain-ring` | `#8d82e6` | the frame of the shown row of a render's chain |
| placeholder | `repeating-linear-gradient(135deg,#1f2030 0 5px,#26273b 5px 10px)` | an image not yet decoded |
| scrim | `rgba(10,11,18,.4)` | behind sheets and dialogs |
| `--band` | `#0f1018` | text on the billing band |
| `--scrim-drawer` | `color-mix(in srgb, var(--ground) 80%, transparent)` | behind the session drawer |
| `--overlay` | `color-mix(in srgb, var(--color-bg) 72%, black)` | the tag cheatsheet's ground |

**Themes.** These are Nocturne's values, the default. Catppuccin's Latte, Frappé, Macchiato and Mocha set every token
in `ui/src/themes.css`, mapped by role, and `⇧T` chooses one
([D48](../../docs/decisions.md#d48--a-theme-is-a-token-set-chosen-in-the-browser)).

**Type.** Sans: Helvetica Neue, Helvetica, Arial, for prose and buttons. Mono: JetBrains Mono 400/500/600, for names,
counts, keys, stage words and commands. Body 13px. Buttons 13px, 500 when primary. Section labels mono 11px `ink-3`,
uppercase, letter-spacing .04em. Mono meta 11–12px. Screen titles 14px/600; dialog titles 16–20px/600; the session
timer mono 40px/500.

**Shape.** Radius 4px for buttons and fields, 3px for thumbnails and checkboxes, 6–8px for bars and sheets. Buttons
30px tall in toolbars and 32px in dialogs, 14px horizontal padding, a 10px gap to their key hint. Floating bar shadow
`0 20px 50px rgba(0,0,0,.55)`; sheet shadow `0 30px 80px rgba(0,0,0,.5)`. No icons: every mark is CSS.

## 3 · The shell

```
┌ isekai  2026-09-17   Hub ⇧H  Review 3 ⇧R                flow [all|summon|conjure] ⇧F         [ ? ] ┐ AppBar 40
├─ BillingBanner (only when something may be billing; filled accent, cannot be dismissed) ───────────┤
│                                                                                                     │
│                                   <the route's screen>                                              │
│                                                                                                     │
├─ ○ job · idle   last: render · 2026-09-17 · ended 15:38 · 1 image        volume open · until 19:38 ┤ JobStrip 28
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **AppBar**, `ground-deep`, bottom border `line`. The wordmark goes Home. The place is mono 12px `ink-2`: `library`
  on Home, else the collection name. Tabs only inside a collection; the active one has a 2px accent underline. The Review
  tab counts the collection's unapproved sheets in mono 11 `accent-ink`, and opens the collection's Review. The flow
  switcher is a segmented control; Review drops `all`. The `?` button at its right end, after the running render,
  opens the key list, as `⌃/` does; no screen draws a key bar. The key list is a modal dialog, centred over most of
  the window, a column per scope — everywhere's, then the screen's; `⌃/`, `esc` and the backdrop close it.
- **BillingBanner**, a filled accent band, text `band` at 600. Three variants: the volume past its window, a pod
  that may be billing, a volume that may be billing. esc never closes it.
- **JobStrip**, `ground-deep`, mono 11px: one dot, then one item per running job, each a label (`job · prepare`)
  and its totals (`tag 6 of 6 · caption 3 of 6 · sheet 0 of 6 · 00:35`, `image 1 of 2 · 06:41 of ≤10:30`); with none
  running, each kind's last receipt. The dot: hollow idle, accent running, accent square unresolved. Prepare keeps each
  stage's total fixed, counts each cell once as it completes that stage, and ticks elapsed time every second from its
  original start. On the right, while the volume is open, the quiet item
  `volume open · until 19:38 · close`.

## 4 · Routes

| route | screen | opens over it |
|---|---|---|
| `/` | Home | the New collection sheet |
| `/c/<collection>/hub` | Hub | the Add sources sheet, the Prepare bar, the Render dialog |
| `/c/<collection>/review` | Review's head, replaced by its sheet's URL | — |
| `/c/<collection>/review/<run>/<flow>` | Review | the cheatsheet, the viewer, *Side by side* |
| `/c/<collection>/renders/<run>/<flow>/<version>/<seed>` | large view | *Draft from this*, *Compare with…* |
| `/c/<collection>/renders/<run>/<flow>/<version>/<seed>/place/<step>` and `…/place/outline/<tattoo>` | the placement screen, its steps `tattoo`, `outline`, `photo`, `render` and `review` | the Leave dialog |
| `/c/<collection>/renders/<run>/<flow>/<version>/<seed>/edit/:k` | large view of a bake | — |
| `/c/<collection>/renders/<run>/<flow>/<version>/<seed>/compare/<flow>/<version>/<seed>` and `…/compare/photo` | Compare | — |
| `/billing` | the billing alert's way out | — |

- `<run>` is the run's **12-hex digest** (`0d4b7e6fb2a8`), unique by construction; the screen shows the short name
 .
- `<version>` is `v` + the approval's number (`v2` is `review/002.approved.json`, rendered into `outputs/002/`).
- `:k` is the number of an edit of that seed (`edit/1`); an address whose `k` is no edit of the seed shows the server's
  refusal. The Hub tab stays lit on it, as on the large view.
- `/c/<collection>/review` opens the first unapproved sheet of the first flow that has one, in the hub's order; else
  the first approved sheet short of its images, read-only; else *No sheet waits for review* and the way to the hub.
- `<step>` is `tattoo`, `outline`, `photo`, `render` or `review`; any other step redirects to `tattoo` of the same
  render, and a step the tattoo's mode skips redirects to the step the mode takes in its place: `photo` of a cut or of
  a tattoo not on this photo goes to `render`. A step or tattoo change keeps the placement screen mounted.
- While a render runs, every screen shows `● render 06:41`, its clock, opening the render drawer, which holds no URL.

## 5 · The journeys

Each row is one frame: the trigger that leads to it, and its URL. `…` is `localhost:7717`. J1–J4 run in order on a
new collection; J5–J6 on one already rendered.

### J1 · First collection

| frame | trigger | URL |
|---|---|---|
| J1·1 Home, first start | — | `…/` |
| J1·2 the browser's file dialog, filtered to images | ⇧N New collection | `…/` |
| J1·3 the sheet, `reading 3 of 6` | choose 6 files, Open | `…/` |
| J1·4 the sheet, every file read: 2 converted, 1 RAW refused | reading ends | `…/` |
| J1·5 the hub, every cell a bare checkbox | ⌘↵ Import | `…/c/2026-10-19/hub` |

```
J1·1  LIBRARY · EMPTY
      No collections yet.
      Sources are copied into ~/isekai/. A photograph leaves this Mac only to be rendered:
      metadata stripped, held only in the GPU pod's memory, and gone when the pod is.
      [ New collection ⇧N ]                                         ← the accent

J1·4  ┌ New collection   6 files chosen · 5 sources · 1 refused         [ Add files… ⇧A ] ┐
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
- The tiles are a grid. Once every file is read the first tile takes the focus, unless the name field holds it; `h j k
  l` and the arrows move it, `⌫` removes the focused file as × does, unasked, and `↵` opens it full size in the
  viewer. A tile still on its way offers no ×.
- While reading, the header says `reading 3 of 6` in `accent-ink`, tiles show `converting…` or `waiting`, and Import
  is disabled with `Reading 3 of 6`.

### J2 · Assign and Prepare

| frame | trigger | URL |
|---|---|---|
| J2·1 one cell assigned; the bar `1 change · Prepare ⌘↵` | arrow to 00003 × conjure, space | `…/c/2026-10-19/hub` |
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

        ┌ 2 photographs to prepare in 2026-10-19  [ Discard ]  [ 3 changes · Prepare ⌘↵ ] ┐   PrepareBar
        ┌ 2 images ready to render                                        [ Render ⇧G ] ┐   RenderBar
```

- **The hub header** leaves a 12 px gap between its items. Add sources keeps its right alignment.
- **A cell:** unassigned, a bare 14px checkbox and nothing else. Otherwise the checkbox, the stage track — six
  13×4 segments, gap 3: assigned · tag · caption · sheet · approved · rendered; done `accent`, running `accent-dim`,
  the rest `line-disabled`; a draft shares the sheet segment — and the stage word in mono 12: `assigned`,
  `tagging…`, `captioning…`, `sheet`, `draft`, `approved`, `rendered ×n`. Running words are `accent-ink`.
- **The tick:** accent fill is pending — assigned or tagged — and can be unticked; `tick-locked` is prepared and
  stays, with no word saying so.
- **Focus** is `raised-2` with an inset 1px `focus` ring, and the cell's one action shows only on focus (`↵ review`,
  `↵ view` or, on the source cell, `↵ view photo`), at the cell's top right, taking no line. The hub keeps its focus
  for the open collection: the Back button and a tab switch come back to the cell left,
  and `Esc` from a large view to the cell of the image it closed, else the first row's source cell.
- **A click or ↵ follows the stage**: unassigned, assigned or tagged ticks and unticks; unreadable does nothing; a
  sheet or a draft opens Review (`↵ review`); an approval with no image opens its sheet read-only (`↵ review`); a
  cell holding images opens the cell modal on its newest (`↵ view`). The checkbox's own click only ticks.
- **The cell modal** is a dialog holding the focus, its head one line, `ada.jpg · summon-anime-wai · v2 · seed 7`,
  naming the focused image.
  One grid of every image of the cell, versions oldest first, seeds in numeric order, at most three to a row, rows balanced — 4 is 2 and 2, 5 is 3 and 2, 7 is 3, 3 and 1; each tile twice 96×128, scaled down so up to three rows show whole, a fourth scrolling, its `vN` badge on the image, `seed N` under it, then `⇄` where the seed was rendered under another version too. `h j k l` and `←↓↑→` move, a row move keeping the column, held at a shorter row's last tile, `l` at a row's end going on to the next row's first and `h` at a row's start back to the previous row's last; `↵` or a click opens the focused image's large view; `Esc` closes it, the hub's focus kept.
- **The viewer** opens an image fitted; a click or `↵` toggles full size, where `j k` `↓ ↑` scroll it by 120 px, and
  `h l` `← →` step to the next image, fitted. On a pair `↵` does nothing.
- **A cell's images** sit at its foot, level with the source's thumbnail, under its stage track and any refusal,
  every approved version's, versions oldest first, seeds in numeric order, each a 96×128 tile
  with its `vN` badge, wrapping, and last the ready tile, `ready · n images`;
  a click on one opens the cell modal on it.
- **A cell's refusal** sits inside the cell with its fix; the cell returns to assigned, so the next Prepare retries
  it.
- **The PrepareBar** floats centred, bottom 50, 940 wide, `raised-2`, 1px `line-control`, radius 8. Pending:
  `<n> photographs to prepare in <collection>` in mono 11, each photograph counted once whatever its flows, Discard,
  primary `n changes · Prepare ⌘↵`. Running: `Prepare · tag 6 of 6 · caption 3 of 6 · sheet 0 of 6 · 00:35`, Stop.
  Each stage's total stays fixed; its count and the ticking elapsed time match JobStrip, including across a reload. Finished cells stay done, the rest stay assigned. Refused: the CLI's refusal (J8a), on a
  hub opened after the failure too. Disabled while another collection's Prepare runs: its reason (`Prepare is running on 2026-10-19`). There is no done state: the
  receipt goes to the job strip, the count to the Review tab. Running, a 2 px `accent` line along the bar's top edge
  is as wide as the stages' cells done over those asked, `progress` in `bars.ts` sizing it as it sizes the RenderBar's
  and the drawer's; with nothing to size it, the line slides. A running segment pulses `accent-dim` ↔ `accent`; under
  `prefers-reduced-motion` both stand still, as the import bar's fill does, and the clocks still tick.
- **The RenderBar** takes the PrepareBar's place on the hub once no change waits: `n images ready to render`, the
  render stage's own count, and primary `Render ⇧G`, disabled with its reason. With nothing short it
  is absent. While a render runs it shows the session's totals, `image 2 of 4 · 06:41 of ≤10:30`, the images
  short outside its plan, `1 image waits` or `n images wait for the next session`, and `Session ⌃;`, in place of the
  count and Render. Its line, and the drawer's bar, are as wide as the images done over those asked; the drawer keeps
  `06:41 of 13:30 at most` as text.
- **The grid:** columns `250px 1fr 1fr…`, full width, no sidebar. Rows at least 84px. The source cell is the grid's
  first column, `h` from the first flow cell, and a column itself: the file's stem in mono 13, its first line level
  with the cells' tick line, the size in the viewer's title, then a 96×128 thumbnail at the cell's foot, a
  render tile's size, upright; a row checkbox appears in selection mode. A long name breaks inside the column, as
  it does on Review's rail and Home, never spilling out. A click
  on the thumbnail or `↵` opens the viewer on its photograph, `← →` stepping the collection's sources; space does nothing
  there.
- **The viewer** is a dialog over the page, its URL unchanged: the image fitted, a click for 1:1 pixels, `Esc` or a
  click outside to close, titled with the name, the dimensions and `fit n%` or `1:1`. The title is one line, cut by
  an ellipsis, so no name widens the dialog; the frame is the window less 64 × 96 px whatever is loading, the image
  centred in it.

### J3 · Review and approve

With two or more flows waiting, the Review tab is a chooser, a row per flow; ↵ opens its head, esc on Review returns.

| frame | trigger | URL |
|---|---|---|
| J3·1 the collection's head, the first sheet in summon | ⇧R Review | `…/c/2026-10-19/review/0d4b7e6fb2a8/summon-anime-wai` |
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
  its footer counts the approved among them. *Draft from this* opens the first draft it wrote; the rest wait in the rail.
  Approve stays on the sheet, read-only. ⇧J ⇧K step the rail. Approve still refuses an unmarked empty field.
- **Cancel approve**, grey-outlined beside the approved time, takes the approval back while nothing derives from it —
  no prompt, render group or copy — and the sheet is editable again; a copy's cancel deletes only the copy, and the
  sheet opens on the draft open above what lies beneath, else the approval beneath, read-only, the bar's note naming
  it as it names every approval shown. No key, no ask. Otherwise it is disabled, the review stage's reason beside it; while a render
  session runs for the collection, the reason says so, and it follows the render as it starts and ends.

### J4 · Render

| frame | trigger | URL |
|---|---|---|
| J4·1 the Render dialog: 4 images and 1 bake, 10 min, limit 15 min, about $0.07 | ⇧G Render | `…/c/2026-10-19/hub` — the dialog has none |
| J4·2 the session, image 2 of 4 | ⌘↵ Render · about $0.07 | the drawer over the hub |
| J4·3 done: `Nothing is billing.` | the last image lands; teardown and volume down confirm | same |
| J4·4 the hub with the four new images | ⇧H View in Hub | `…/c/2026-10-19/hub` |

```
J4·1  RENDER · ON A RENTED GPU                           Render 4 images · 1 bake
      ☑ 2026-10-19 3 images · 1 bake                                 a row per collection
          summon-anime-wai 2 images                                  96×128 thumbnails, 15 then +n
          [▒▒×]×2                                                    × takes the photograph out · ×n above one
          conjure-anime-wai 1 image
          [▒▒×]
          bakes 1 bake                                               the bakes of the collection, a row each
          [▒] 00003 · v1 · 1840266731 · edit 1 [×]                   × takes its flow out with its bakes
      ☑ 2026-10-20 1 image                                           the rows scroll in a max height
          summon-anime-wai 1 image
          [▒▒×]
      ☐ 2026-10-21 all removed                                       every photograph out: no tick
      ESTIMATE  boot 3:00 · 4 images · 1 bake · teardown 2:00          10 min
                limit 1.5× the estimate                              15 min
                gpunit.toml's ceiling                                3 h
      PRICE     pod 10 min at about $0.40/h                         about $0.07
                volume attached for the session                 under $0.01
                                     at the limit about $0.10
      ☐ Keep the volume open for 4 hours after the session        about $0.02
                                           [ Cancel esc ]  [ Render · about $0.07 ⌘↵ ]

J4·2  RENDER SESSION · STARTED 15:21:12 · 4 SHEETS
      06:41 of 15:00 at most      [▰▰▰▰▰▰▱▱▱▱▱▱]  images done over asked
      ● volume up         gpunit-isekai · attached                 0:21
      ● pod boot          gpunit-isekai                            2:04
      ◐ rendering         image 2 of 4 · 00003 · conjure-anime-wai · 4:16
      ○ teardown
      ○ volume down
      2026-10-19                                                             a grid per collection
      summon-anime-wai    [done]                                             a column per photograph
                          [▨]                                                a cell's images stack
      conjure-anime-wai   [done]
      PHOTOGRAPHS         [00003]                                            the photographs' row last
      2026-10-20                                                             j from the row above
      summon-anime-wai    [▨]
      PHOTOGRAPHS         [16_01]
                                                               [ Stop session now ]
```

- **What renders**: a row per collection short of images or holding a bake, in the Library's order, each ticked; in
  each, every approved source × flow whose newest version holds fewer images than its Count, grouped by flow, then
  the collection's bakes, a row each. The row's count line reads `<n> images · <m> bakes`, the bakes left out for zero; the images stay, even at zero.
  Unticking a row quotes the rest again; one session renders every ticked collection on one pod, its bakes after its
  images. The bar counts its own collection's images and bakes, and `+n in other collections` counts both.
- **Taking out**: a tile's `×`, or `⌫` on a focused tile, takes the photograph's flow out of the session; a bake
  row's `×` takes its flow out with its bakes, since `render --without` names a flow of a run. The rest is quoted
  again; a row with none left reads *all removed* and cannot be ticked. The confirmation carries what was taken out.
- **The title and the button**: the title is *Render 2 images*, *Render 2 images · 1 bake* or *Bake 1*, as what the
  session does; the button reads *Render*, and *Bake* when no image is short. A session of bakes alone opens from the
  bar, which shows with bakes alone, as `⇧G` does.
- **The estimate**: boot + images × time per image + bakes × time per bake + teardown; boot 8:00 and teardown 2:00,
  each image at its recorded median or 1:35, whichever is higher, each bake at the edit's configured time; one boot
  and one teardown for every ticked collection. The estimate line names each of images and bakes, none for zero.
  The limit is 1.5× the estimate, under the configured
  maximum, and teardown starts by itself at the limit; an estimate past the ceiling disables Render — *untick a
  collection*. The price comes from the estimate: the pod at `pod_rate` (about $0.40/h), the volume at about
  $0.005/h.
- **The drawer** stands at the right, as wide as its widest grid: at least half the window and 480 px, at most the
  window less 100 px, a wider grid scrolling inside it; its long text, a refusal's above all, never widens it.
- **The session** shows elapsed time against its limit, five steps always, and a grid per collection it renders,
  stacked in its order, each headed by its name — no diffusion steps and no spend. A column per photograph the record
  plans, a row per flow, the photographs' row at the foot; a cell holds that flow's images of that photograph and a
  striped tile per image still to come, stacked, so a column stays one tile wide. A record that plans nothing places
  what landed. The first render takes the focus on opening and is the grids' tab stop; `h l` move between
  photographs, `j k` between rows and from a grid's photographs' row into the next grid's first row, the column kept,
  and `↵` opens the viewer over the row, each image named `summon-anime-wai · v1`. `⇧H` opens the focused image's collection's hub. Stop goes straight to
  teardown; finished images are kept.
- **Done** is the step list all confirmed, the count and the duration, and `Nothing is billing.` only when both
  teardown steps are confirmed.

### J5 · Revise one image

| frame | trigger | URL |
|---|---|---|
| J5·1 the hub's cell modal, before the revision | ↵ on the cell | `…/c/2026-09-17/hub` — the modal has none |
| J5·2 the large view, no Compare yet | ↵ | `…/renders/0d4b7e6fb2a8/summon-anime-wai/v1/1840266731` |
| J5·3 *Draft from this* over it, its own flow focused | ⇧D Draft from this | same |
| J5·4 Review of the revision: the render beside the photograph, the seed prefilled | ↵ on *revise* | `…/c/2026-09-17/review/0d4b7e6fb2a8/summon-anime-wai` |
| J5·5 eye_colour edited | × `light` in eye_colour | same |
| J5·6 the revision approved, read-only; the hub's Render bar, `1 image ready to render` | ⌘↵ Approve · ⇧H | `…/c/2026-09-17/hub` |
| (J4·1–J4·3 for 1 image, 6 min, about $0.04) | ⇧G · ⌘↵ | the drawer over the hub |
| J5·7 the hub's cell modal: v2 after v1, both marked `⇄` | ⇧H View in Hub · ↵ on the cell | `…/c/2026-09-17/hub` |
| J5·8 the large view of v2, with `Compare with…  ⇧C` | ↵ on v2 | `…/v2/1840266731` |
| J5·9 Compare | ⇧C, ↵ on v1 in the pick | `…/v2/1840266731/compare/summon-anime-wai/v1/1840266731` |

```
J5·4  ① PHOTOGRAPH · 1073×1406   RENDER BEING REVISED · seed 1840266731   [ Side by side ⌃P ]
      [photograph]               [render, accent hairline]       one height, top-aligned
      ② CAPTION  collapsed on a revision
      ③ SHEET — REVISION OF RENDER 1840266731 · saved 15:52
      eye_colour  • [blue eyes ×]      was light · blue eyes   │ ④ RENDERS  images [−] 1 [+]
                                                              │ 1 [1840266731]  prefilled, one slot per image
                                                              │ THE NEXT RENDER DRAWS 1 image · seed 1840266731
                                        [ Discard draft ]  [ Approve sheet ⌘↵ ]

J5·9  SUMMON-ANIME-WAI · V1 · SEED 1840266731     SUMMON-ANIME-WAI · V2 · SEED 1840266731
      [the image picked, one height, top-aligned]  [the image compare started from]
      the pair centred, as tall as the window less the app bar and the heads; nothing under it
      the photograph picked:  the photograph left, the image right
```

- **↵ always opens the large view**: the image on `ground-media`, the sheet it was rendered from beside it
  (filled fields only, read-only). Its actions stand under the heading, above the fields: a column of full-width buttons, label left
  and key right, in groups 12 px apart — the writes, the comparisons, the way back. `Esc` and its back button go
  back to the hub, on the cell of the image it closed, whatever opened it. `h` `l` and `←` `→` walk the
  photograph's row wherever it was opened — its flows in the hub's column order, versions oldest first, seeds in
  numeric order — held at either end, the head naming the step,
  `summon-anime-wai · v2 · seed 1840266731 · 2 of 5`.
  `Compare with…  ⇧C` opens a pick of the source's images: the photograph's row on top, then a row per flow
  holding images, headed by its name, tiles at a thumbnail's size oldest first, `vN` under each, the image
  compare started from marked, the pick's head naming the focused tile on two lines, each cut at its end —
  `Compare summon-anime-wai v2 · seed 1840266731` over `with summon-anime-wai v1 · seed 1840266731`. The pick is as
  wide as its longest row, whatever is focused: at least 480 px, at most the window less 96 px, its rows and its
  tiles 20 px apart. Its rows stand no taller than the window less 96 px, scrolling inside. It opens on the newest older version of this seed, else the image before this one,
  else the photograph; `h j k l` and the arrows move, keeping the column, held at a shorter row's end; `↵` or a
  click compares, `Esc` closes.
- **The photograph** shows on the large view's sheet at its thumbnail size, above the actions. It has no link and no
  key: a key belongs to the placement screen.
- **The chain** stands under the actions, above the fields, when the render has bakes: the render first, then each bake of its seed
  by number, one level further in for each bake it descends through, so a bake placed on another is drawn under it.
  The shown row is framed with `--chain-ring` on `--chain-ground`. A baked row (`edit 1 · baked 15:40:12`) opens that
  bake's view; a queued row (`edit 2 · queued, waits for the next session`) and a damaged row (`edit 3 · damaged`,
  with its reason) open none, and one damaged record costs only its own row.
- **A bake's view** (`…/<seed>/edit/:k`) is the large view with the bake's image, or for a queued bake the image it
  was placed on, under the line `queued · the image it was placed on, until the next session bakes it`. The sheet
  keeps its head and fields, and adds the bake's record rows: *placed on* (`the render` or `edit 1`), *edit* and
  *baked*. It offers no write — no *Draft from this*, *Compare with…* or *Delete*, and none of their keys — since a
  delete there would take the render and every bake; the way back is *Back to Hub* and the chain's rows.
- **Compare** sets the image picked on the left and the image compare started from on the right, at one height,
  each headed by its flow, version and seed and nothing else: the pair centred, as tall as the window less the app
  bar and the heads, on the app's 12 px padding.
  *Draft from this* `⇧D` heads the writes.
- **Draft from this** (the verb `isekai draft --flow`), on the large view: a dialog headed
  `Draft from this · summon-anime-wai v1 · seed 1840266731`, with a row per offered flow, assigned or not — the
  image's own first, named *revise*, and focused. `j` `k` move, `↵` drafts the focused flow and opens Review on the
  first draft, the rest in the rail, `Esc` closes. Its own flow is a revision; another is drafted from the image's approval, its own fields from its sheet, and Review shows the image
  beside the photograph, marks the draft against that flow's sheet and heads it *the image it was drafted from*. It
  drafts the one image the large view shows: a refusal names why that image cannot be drafted, and writes nothing. A
  target's waiting draft with edits of its own opens Review on that draft, writing nothing; one equal to its sheet is
  replaced. The endpoint takes a list of images and refuses all or nothing; that list is the API's, and the page
  sends one image.
- **The revision's sheet** marks changed rows with an accent gutter dot and a `was` line against the rendered sheet,
  and keeps them once approved; the image it revises stays, whatever its seeds become.
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
| (the large view of 00003 · conjure v1, as J5·2; *Draft from this*, as J5·3) | ↵ · ⇧D · ↵ | `…/renders/0d4b7e6fb2a8/conjure-anime-wai/v1/2216093514` |
| J6·1 Review: the seed cleared, Count 3, the tags untouched | × the seed · count + + | `…/review/0d4b7e6fb2a8/conjure-anime-wai` |
| (J4 for 3 images, 8 min, about $0.05) | ⌘↵ Approve · ⇧G · ⌘↵ | the drawer over the hub |
| J6·2 the hub's cell modal: three new images after v1, no pair | ⇧H View in Hub · ↵ on the cell | `…/c/2026-09-17/hub` |

Changes in ④ are marked like changed fields: the gutter dot and `was 1 in v1`, `was 1840266731 · cleared`.

### J7 · Add sources to a collection

| frame | trigger | URL |
|---|---|---|
| J7·1 Home, the library | — | `…/` |
| J7·2 its hub | ↵ on 2026-09-17 | `…/c/2026-09-17/hub` |
| (the file dialog, as J1·2) | ⇧A Add sources… | same |
| J7·3 the sheet without a name: one `already here`, one copied as `16_01-2.png`, one HEIC converted | Open; reading ends | same |
| J7·4 two new rows, bare checkboxes | ⌘↵ Import 2 | same |

```
J7·1  LIBRARY · 4 collections · newest activity first                     [ New collection ⇧N ]
      2026-09-17  6 sources  1 source without a flow                 today 15:31 · render · open ↵
      ▢▢▢▢▢▢▢ +5
      old exports      ▨ Not a collection: no sources/ folder inside. Move it out of ~/isekai/ in Finder
                         to clear this row.                                                  can't be opened
```

- **Home's row**: a header line — the name, `n sources`, `n sources without a flow`, no chip per flow (the API keeps
  each flow's counts), and at the right last activity, the time and kind of the newest
  file written in the collection, then `open ↵` — over up to fifteen 84×114 thumbnails then `+n`, at the full width,
  wrapping in a narrow window. Sorted by last activity; a folder without `sources/`
  sorts last, striped and inert; dot-folders, `.staging` among them, are not listed.
- **A running render's row** has an accent left edge (`inset 2px 0 0`), background `#1b1c2c`,
  `● render running · 06:41` and `image 1 of 2`.
- **`already here`** is the same bytes as a source in the collection: dimmed, skipped. A different file with a taken name
  is copied as `<stem>-2` and says `chosen as 16_01.png`.

### J8 · When it goes wrong

- **J8a, Prepare refused** — from J2·2, ⌘↵. The bar shows the CLI's refusal; nothing ran, the cells stay assigned.
  Start Ollama outside the app, then ⌘↵ again → J2·3. URL `…/c/2026-10-19/hub`.
- **J8b, teardown unconfirmed** — from J4·2, teardown gets no answer. The band shows on every screen; *Resolve*
  opens the alert at `…/billing`. Ways out, each ending in **Check again**, which asks gpunit: Check again itself;
  `uv run --env-file .env gpunit down`, then Check again; stop it in RunPod's console, then Check again. It clears
  only when gpunit confirms the pod gone → the band goes, the receipt stays.
- **J8c, the volume past its window** — Home with the quiet job-strip item; at the window's end the band:
  `Volume gpunit-isekai is still open past its window and is billing.`, `window ended 19:38`,
  `or uv run --env-file .env gpunit volume down`, **Close volume** (the same command). gpunit confirms → J7·1.
- **A volume that may be billing** after a session is J8b's shape with `uv run --env-file .env gpunit volume down`.

### J9 · Place a tattoo

| frame | trigger | URL |
|---|---|---|
| J9·1 the picker, nothing kept: `none kept yet`, the upload form, the cut form | ⇧P Place a tattoo, on J5·2's large view | `…/renders/0d4b7e6fb2a8/summon-anime-wai/v1/1840266731/place/tattoo` |
| J9·2 a file chosen: its name `IMG_5521`, `reading…`, then `converted`; Keep waits `reading the file` | Upload a tattoo…, choose `IMG_5521.heic` | same |
| J9·3 the outline step on it, the outline open: the ink view, the white point and the tone read `outline open` | Keep | `…/place/outline/IMG_5521` |
| J9·4 the outline closed: the ink view, the white point `auto` with its grey, the tone, `saved` | click the first point again | same |
| J9·5 the picker: the card `IMG_5521`, `outlined` | ① tattoo | `…/place/tattoo` |
| J9·6 a cut: the photograph dimmed outside the outline, the source line `from photograph 0d4b7e6fb2a8 · ink 412×301 on the photograph`, neutral on, depth 1.6 | name `bow`, Cut from this photo, close its outline | `…/place/outline/bow` |
| J9·7 the picker: `instead of bow, which stays kept`, the name starting `bow_closeup` | Upload a tattoo instead | `…/place/tattoo?instead=bow` |
| J9·8 ③ tattoo ↔ photograph: the ink view and the photograph, the waiting image in the accent; forward waits `6 pairs needed · 2 placed`, then `point 7 has no match` | Next: ③ tattoo ↔ photograph, on J9·4 | `…/place/photo` |
| J9·9 the preview: the ink multiplied over the photograph, `Hide the preview` and its opacity; the last answer at half opacity while the next is asked | the third complete pair, then a second without a change | same |
| J9·10 ④ photograph ↔ render: the photograph and the render, the preview over the render, the rows `limb · 9 points · keeps` and `exclusion 1 · 8 points · removes` with *Edit*; the pairs wait while one is drawn, `drawing · 3 points`, `click on the render adds a point · the first point closes · the pairs wait` | Next: ④ photograph ↔ render, then Draw limb, Draw exclusion | `…/place/render` |
| J9·11 ③ tattoo ↔ render, for a tattoo `not on this photo`: its ink view and the render; no ③ photograph and no stage-1 pairs asked | the card's *not on this photo*, then Next | `…/place/render` |
| J9·12 ⑤ review: the render with the tattoo over it, its crop `before` and `after`, the summary, `Back to ③ …` and `Back to ④ …`, *Bake*; waiting with `stage 2 · 8 pairs needed · 5 placed`, then `queued · edit 3 · next render session` | Next: review, then Bake | `…/place/review` |
| J9·13 Leave this stage?: `Point 8 has no match on the photograph`, `7 pairs stand · saved 14:05`, *Stay* and *Leave* | ① tattoo, or a step, or Back to the render, with a lone point | the step asked for |
| J9·14 ④ photograph ↔ render opened with no pair held: `Proposing pairs…` under the list while the clicks work; then the proposed pairs numbered after the held ones, each point ringed dashed and its row marked, *Accept* and *Accept all*, forward waiting `4 proposed · accept or delete them`; after a refusal its words with their fix, after an empty answer `Nothing proposed — place the pairs by clicking` | Next: ④ photograph ↔ render, on a two-stage tattoo or a cut, then Accept all | `…/place/render` |

```
J9·4  place a tattoo · summon-anime-wai · v1 · seed 1840266731      ① tattoo   ② outline   [ Back to the render ]
      ┌──────────────────────────────────┐   IMG_5521 · outlined
      │  the tattoo, its outline closed, │   kept 2026-11-12
      │  a numbered ring on each vertex  │   [ Undo ] [ Clear ]                           saved
      │                                  │   ink view          crop at 120,80 · 310×420
      │                   Fit · 1:1 100% │   white point · auto   [ 212 ] [ Auto ]
      └──────────────────────────────────┘   tone   ☐ neutral   depth [ 1.0 ]
```

- **The panel** zooms at the pointer, pans by a drag, and has *Fit*, *1:1* and the zoom as a percentage. A click adds
  a vertex, the first vertex closes the outline, a drag moves one, ⇧-click inserts on an edge and a double click
  removes one. It reads no key.
- **The outline and the tone** are saved as they change: `saving…`, then `saved`. The ink view asks again after each
  save, `drawing the ink…` until it lands. The white point waits `reading the ink` until the first ink view has read
  the automatic grey. *Reset* shows only while the tone differs from its kind's default: neutral off and depth 1.0
  for an upload, neutral on and depth 1.6 for a cut.
- **A card** shows the image, the name, `outlined` or `not outlined`, and `kept 2026-11-12`, with
  `· downscaled from 6000×4000` when it was scaled, or `from photograph 0d4b7e6fb2a8` for a cut.
- **Keep and Cut wait with their reason**: `reading the file`, `the file is refused`, `name the tattoo`, `name the cut`,
  `keeping`.
- **Refusals**, each with its fix: a taken name, `bow is kept; choose another name`, beside the name; a file that is
  not an image or still carries metadata, on the file; an outline the server refuses, as the ink view's refusal under
  the ink view; an unknown render or tattoo, a full-page refusal with `Back to the library ⇧L`.
- **A cut of another photograph** stays listed, disabled, reading `from photograph 5c19e0a47d3b, not this render's`.
- **The stages** pair the images by clicks, either image first; the image that waits for a match takes the accent, a
  click near a point selects its pair, a drag moves a point, and the list has *Undo*, *Delete* and *Clear*. Forward
  waits with `6 pairs needed · 2 placed` or `point 7 has no match`. The steps of a mode keep their numbers (§4): a cut
  has no ③, and a tattoo `not on this photo` pairs the tattoo with the render at ③ `render`.
- **The preview** is asked the declared time after the last change once the preview's floor of complete pairs stand;
  only the newest answer is drawn. A refusal clears the answer and shows its fix under the pairs.
- **The proposed pairs** are asked once, when ④ opens with no pair for a two-stage tattoo or a cut; the direct stage
  asks nothing. The line under the list reads `Proposing pairs…`, then the refusal's words, or `Nothing proposed —
  place the pairs by clicking` after an empty answer, and the clicks keep working. A proposed pair is dashed on both
  images and in its row; *Accept* makes the selected one ordinary, *Accept all* makes every one, and a drag of either
  point accepts that pair. Forward waits `4 proposed · accept or delete them` before any other reason, and *Undo*
  leaves the proposal in place.
- **The limb and the exclusions** are drawn on the render with *Draw limb* and *Draw exclusion*, each a row with *Edit*
  and no way to remove one; a second *Draw limb* edits the first. A refusal names the region that has too few points.
- **The review** waits with the stage that lacks pairs; *Bake* then reads `baking…` and `queued · edit 3 · next render
  session`, or shows the server's refusal beside it and stays enabled. A bake spends nothing.
- **The Leave dialog** opens on a step change or a way out of the screen while a stage holds a lone point. *Stay* and
  `esc` close it and keep the stage; *Leave* drops the lone point and keeps the pairs. A stage with no lone point is
  left without asking. The stage-1 line reads `saved 14:05`, and the stages of ④ read no time.

## 6 · States no journey draws

| screen | state | what shows |
|---|---|---|
| Home | loading | rows paint with folder names; counts and thumbnails fill per row |
| Home | the library cannot be created | a full-page refusal naming the permission problem |
| New collection | name taken | the refusal with a free name offered, `use 2026-10-19 2 ⇧↵`; Import disabled `Choose a name that isn't taken` |
| New collection | name unusable | `A name can't contain /, start with a dot, or be empty.` |
| New collection | nothing usable | Import disabled `None of the chosen files could be read.` |
| New collection | cancel | the staging folder is deleted; the library is unchanged |
| Hub | loading | placeholder rows, `reading 2 of 6` |
| Hub | a damaged run | the cell reads `unreadable`, with the CLI's refusal (path, line and column) and its fix; the rest of the grid works |
| Hub | a render running | the session's totals, `image 2 of 4 · 06:41 of ≤10:30`, and `Session ⌃;`; no Render |
| Hub | Prepare disabled | the bar keeps its cells, reason `Prepare is running on 2026-10-19` |
| Hub | Add sources, nothing new | Import disabled `Nothing new to add` |
| Hub | the collection is gone | a full-page refusal, `Back to the library ⇧L` |
| Render | refused before billing | the CLI's refusal: no GPU free, no key in `.env`; `nothing billed` when true |
| Render | disabled | `A pod may still be billing.` |
| large view | a missing image, its record kept | `its record is there, its image is gone`, the path in the fix |
| large view | a deleted render | `no render is here, its record and its image are gone` |

## 7 · Keys

Matched on `event.code`, the physical key, with the typed character suppressed, and declared once in
the key store ([D25](../../docs/decisions.md#d25--shortcuts-match-the-physical-key)); `⌃/` lists them. ⌘
is Ctrl off macOS. Inside a text field only esc, ⌘↵, ⌘Z, ⇧⌘Z, ⌘K, ⌃/ and ⌃; run, Review's ⌃P, and on macOS Review's
⌃H ⌃L ⌃J ⌃K.

| where | keys |
|---|---|
| everywhere | ⇧L the library · ⇧H Hub · ⇧R Review's head · ⇧T the theme dialog · ⌃; the render drawer, from a field too · ⌃/ the key list, from a field too · ⌘↵ the outlined action · esc leaves a field, then closes an overlay, never a billing alert |
| Home | ⇧N New collection · j k or ↓↑ ↵ the library |
| Hub | h j k l or ←↓↑→ cells, the source column first · space tick / untick, or a column for the selected rows · ⇧J ⇧K or ⇧↓↑ select rows · ↵ the cell's action, on the source the viewer · in the viewer, ← → h l step, ↵ full size, j k or ↓↑ scroll it · in the cell modal, h j k l or ←↓↑→ move, l and h going on across rows, ↵ the large view, esc closes · ⌘↵ Prepare · ⇧A Add sources · ⇧G Render · esc clears the selection |
| Review | the panes: the rail, the photograph, the sheet, ④ — on macOS ⌃H ⌃L alone, from a field or not, elsewhere h l or ←→ · ⌃J ⌃K the fields from a field on macOS · j k or ↓↑ in each: the input, a scroll, the rows, ④'s grid of − + and its slots, from a slot too · h l or ←→ across − + on macOS · ⇧J ⇧K or ⇧↓↑ the rail, the sheet scrolled to its centre · ⌃P the photograph, on a revision or a draft from an image Side by side, from a field too, ← → its photographs · ⌘↵ Approve · ⌘Z ⇧⌘Z · ⌘K the tag cheatsheet · autocomplete ↑↓ ↵ esc · ⌘↓ walk refusals, when built · ⇧↵ take every suggested spelling · the collapsed caption, its key named when built |
| Large view | h l or ←→ the photograph's row · ⇧D Draft from this · ⇧C Compare with… · ⇧P Place a tattoo · esc back to the hub · in its pick, h j k l or the arrows, ↵ compare, esc close · in compare, `\` swap, esc back |
| Placement | none of its own: the mouse draws and the everywhere keys stay |
| Drawer | h l or ←→ photographs · j k or ↓↑ rows, held at the photographs' row · ↵ the viewer over the row · ⇧H its collection's hub · ⌃; or esc close |
| dialogs | ⌘↵ confirm · ⇧↵ the secondary confirm · esc cancel, held while an import commits · ⇧A Add files…, in the import sheet |

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
  open collection's cells, the open import's files, billing state — then only changes. The stream names the page's
  collection and its open import, and opens again when either changes. Actions are HTTP POSTs.
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
| **ui groundwork** | the shell — AppBar, JobStrip, BillingBanner's slot; tokens; routes with the collection (§4); `isekai ui` with no arguments over `ISEKAI_LIBRARY`; Home and the library (J7·1, Home's states); the hub grid as a listing, focus, keys (§7), the cheatsheet; Review inside the shell with its queue; vitest and Playwright, the fakes behind `ISEKAI_WIRING=<module>:<factory>` |
| **run flow** | New collection and Add sources (J1, J7) — the upload, staging, `isekai import` and conversion; `isekai assign`; ticking, multi-select, the PrepareBar and Prepare as a job (J2, J8a); `--progress json` on the stage verbs; the job slot; SSE `/events` with the snapshot |
| **render** | the Render dialog, the session, done (J4); ④ editable, Count and Seeds through approve; `render <runs>` rendering what is short; the scaled limit and recorded durations; Renders, the large view; the billing alerts and the volume item (J8b, J8c); `--progress json` on `render` |
| **revise** | `isekai draft --flow`, *Draft from this* and its refusal; Review of a revision (J5·4–J5·6); `review --discard`; compare (J5·8, J5·9); re-roll (J6) |
| **the placement core** | *Place a tattoo* `⇧P` on a render's large view; the placement screen's route (§4) and its first two steps, ① the tattoo and ② the outline with its ink view (J9); the tattoo library `.tattoos/` ([D52](../../docs/decisions.md#d52--the-tattoo-library-is-library-wide-kept-whole-and-never-deleted)); the panel's zoom, pan and outline; `--outline-fill` and `--point-ring` in each theme. The stages, the live warp and the bake are the next version's |
| **the placement** | the placement screen's steps ③ `photo`, ④ `render` and ⑤ `review` (§4, J9·8–J9·13): the pairs on two images, the live preview, the limb and exclusions, the review and *Bake*, which queues an edit request, and the Leave dialog; a tattoo's stage-1 pairs kept per photograph; the placement record beside its edit ([D53](../../docs/decisions.md#d53--a-placement-is-recorded-beside-its-edit)); `--limb-fill` and `--exclusion-fill` in each theme |
| **automatic placement** | stage ④'s proposed pairs (J9·14): asked once when it opens with no pair, a spinner or a refusal, dashed points and rows, *Accept* and *Accept all*, and forward's wait for them; the pose and the segmenter run on the operator's machine ([D54](../../docs/decisions.md#d54--automatic-pairs-run-on-the-operators-machine-and-are-kept-nowhere)) |
| **bakes** | the bake's route `…/<seed>/edit/:k` and its view; the chain and the photograph's thumbnail on the large view; bakes in the Render bar and the dialog, their `×`, the titles and the confirmation that carries them (J4·1, J5) |
