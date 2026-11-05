## ADDED Requirements

### Requirement: The large view deletes its render after asking, and the Hub opens on its cell

The system SHALL offer *Delete* on a render's large view, on `⇧⌫`, after *Compare with…*, opening a modal dialog,
*Delete this render?*, whose *No* comes first and holds the focus; `h` `l` and `←` `→` SHALL move between *No* and
*Yes*, `↵` SHALL press the focused one, and `Esc` SHALL answer *No*. *Yes* SHALL discard the render through the render
stage, delete its thumbnails from the library's cache, and open the Hub focused on the render's cell, from whichever
screen opened the view. The server SHALL refuse the delete while a render session runs for the collection, deleting
nothing, and the dialog SHALL show the refusal.

A failed render is deleted where it is seen. *No* first makes a stray `↵` harmless, and a write beside a running
session is refused, as *Cancel approve* is. The cell is where the delete shows: one image fewer, or approved again.

```
large view ──⇧⌫──▶ Delete this render?  [No] [Yes]
                     │ Esc · No              │ Yes
                     ▼                       ▼
                 large view           discard ─▶ the Hub, focused on the cell
```

#### Scenario: the dialog opens on No
- **Key:** `ui:delete-render:the-dialog-opens-on-no`
- **Layers:** e2e
- **WHEN** `⇧⌫` is pressed on a large view, then `l`, `h` and `Esc`
- **THEN** *Delete this render?* opens with *No* focused, `l` focusing *Yes* and `h` *No*
- **AND** `Esc` closes it, the image still shown

#### Scenario: Yes deletes the render and opens the Hub on its cell
- **Key:** `ui:delete-render:yes-opens-the-hub-on-the-cell`
- **Layers:** e2e
- **WHEN** `⇧⌫`, `l` and `↵` are pressed on the large view of a cell's only image, opened at its address
- **THEN** the Hub opens focused on that cell, approved again
- **AND** the image is gone from the run

#### Scenario: the route deletes the render and its thumbnail
- **Key:** `ui:delete-render:the-route-deletes-the-render-and-its-thumbnail`
- **Layers:** unit
- **WHEN** a render whose thumbnail is cached is deleted at its address
- **THEN** its image, its record and its thumbnail are gone
- **AND** the other render and its thumbnail stay

#### Scenario: the delete is refused while a render runs
- **Key:** `ui:delete-render:refused-while-a-render-runs`
- **Layers:** unit
- **WHEN** a render is deleted while a render session runs for its collection
- **THEN** the delete is refused, saying a render session is running
- **AND** no file is deleted

## MODIFIED Requirements

### Requirement: Every command has one key, declared once, and none fires while typing

The system SHALL declare each keyboard command once, with its key and its label, on the screen or overlay that offers
it, and SHALL draw every key hint and the key list from those declarations, the list opening on `⌃/` on every screen
and on the app bar's `?` button; no screen SHALL carry a key bar. It SHALL match a key by the physical key, whatever
the keyboard layout, and SHALL treat Mod as `⌘` on macOS and `Ctrl` elsewhere. An open overlay SHALL take every key
before the screen beneath it, and the screen before the keys offered everywhere. While focus is in a text field, no
command SHALL fire but `Esc`, `Mod+↵`, `Mod+Z`, `⇧Mod+Z`, `Mod+K`, `⌃/` and `⌃;`, Review's `⌃P`, and on macOS Review's
`⌃H` and `⌃L`, which move between its panes, and `⌃J` and `⌃K`, which move between its fields as `↓` and `↑` do, and
in ④'s seed slots `j` `k` `↓` `↑`, which move between the slots; the field SHALL keep its own editing keys. On a grid,
a move between rows SHALL keep the column it is in, held at a shorter row's end. On the hub and in the session drawer,
a focused button or link SHALL keep `↵` and `Space`. An `Esc` that ends an input method's composition SHALL be the
input method's, closing nothing. `Esc` SHALL close an open suggestion list first, then leave the field, then close the
top overlay, then go back on the screen, and SHALL never close a billing alert. On macOS Review's panes SHALL move by
`⌃H` and `⌃L` alone, from a field or not, and `h` `l` and `←` `→` SHALL move within a pane; elsewhere `h` `l` and `←`
`→` SHALL move between the panes. A plain letter SHALL move the focus, and a command SHALL take `⇧` and a letter, but
for `⌫` on a chosen file, which removes it before anything is committed, and `⇧⌫` on a large view, which asks before
it deletes the render. No key SHALL spend money but the Render dialog's `Mod+↵`, which confirms the price it quotes.

A key typed into a field is text, never a command; a list drawn from the declarations cannot disagree with the keys.
Option is the window manager's on Linux and types characters on macOS, and a layout moves letters but not keys.
On Linux `Ctrl+J` is the browser's and `Ctrl+K` is `Mod+K`, so the field moves are macOS's alone. A shifted letter is
not pressed in passing, so it guards what writes.

```
keydown ─▶ in a text field? ─ yes ─▶ Esc · Mod+↵ · Mod+Z · ⇧Mod+Z · Mod+K · ⌃/ · ⌃;, Review's ⌃P,
               │                     on macOS Review's ⌃H ⌃L ⌃J ⌃K, else the field's own
               │ no
               ▼
           top overlay ─▶ screen ─▶ everywhere        the first that declares the key runs
```

#### Scenario: a key is matched by the physical key
- **Key:** `ui:keys:a-key-is-matched-by-the-physical-key`
- **Layers:** unit
- **WHEN** `⇧H` is pressed on a Cyrillic layout
- **THEN** the command declared for `⇧H` runs

#### Scenario: Mod is Command or Control
- **Key:** `ui:keys:mod-is-command-or-control`
- **Layers:** unit
- **WHEN** a command declared for `Mod+K` is offered
- **THEN** `⌘K` and `Ctrl+K` each run it

#### Scenario: no command fires in a text field
- **Key:** `ui:keys:no-command-fires-in-a-text-field`
- **Layers:** unit
- **WHEN** a declared letter is pressed with focus in a text field
- **THEN** no command runs
- **AND** `Esc`, `Mod+↵`, `Mod+Z` and `Mod+K` still do

#### Scenario: a command waits until the field is left
- **Key:** `ui:keys:a-command-waits-until-the-field-is-left`
- **Layers:** e2e
- **WHEN** `⇧H` is typed into a tag field, then `Esc` and `⇧H` are pressed
- **THEN** the field holds the typed text and Review stays open
- **AND** the second `⇧H` opens the hub

#### Scenario: a focused control keeps Enter and Space
- **Key:** `ui:keys:a-focused-control-keeps-enter-and-space`
- **Layers:** unit
- **WHEN** `↵` or `Space` is pressed on the hub or in the session drawer with focus on a button or a link
- **THEN** the control answers it and the cell's command does not run

#### Scenario: an overlay takes the keys first
- **Key:** `ui:keys:an-overlay-takes-the-keys-first`
- **Layers:** unit
- **WHEN** an overlay and the screen beneath it both declare a key
- **THEN** only the overlay's command runs

#### Scenario: Esc closes the nearest thing first
- **Key:** `ui:keys:esc-closes-the-nearest-thing-first`
- **Layers:** unit
- **WHEN** `Esc` is pressed with a suggestion list open in a field inside an overlay
- **THEN** the list closes, and the next `Esc` leaves the field, and the next closes the overlay

#### Scenario: the key list and the hints come from the declarations
- **Key:** `ui:keys:hints-come-from-the-declarations`
- **Layers:** unit
- **WHEN** a screen declares its commands
- **THEN** its button hints and the key list name each command's key and label
- **AND** no key bar is drawn

#### Scenario: Renders moves by cell and by image
- **Key:** `ui:keys:renders-moves-by-cell-and-by-image`
- **Layers:** unit
- **WHEN** `l` and then `→` are pressed on a cell's last image of the Renders grid
- **THEN** each moves to the next image, crossing into the next cell, and `h` at a row's start reaches its source

#### Scenario: Review moves between its panes
- **Key:** `ui:keys:review-moves-between-its-panes`
- **Layers:** unit
- **WHEN** on macOS `⌃L` is pressed from the rail three times, then `l` once
- **THEN** focus moves through the source pane and the sheet to ④
- **AND** `l` moves within ④, and no pane changes

#### Scenario: a row move keeps the column
- **Key:** `ui:keys:a-row-move-keeps-the-column`
- **Layers:** unit
- **WHEN** `j` is pressed on the Renders grid's third image of a row whose next row holds two
- **THEN** the focus moves to that row's second image

#### Scenario: an Esc that ends a composition closes nothing
- **Key:** `ui:keys:an-esc-ending-a-composition-closes-nothing`
- **Layers:** unit
- **WHEN** `Esc` ends an input method's composition in a field inside an overlay
- **THEN** the field keeps the focus and the overlay stays open

#### Scenario: Review's panes move from a field on macOS
- **Key:** `ui:keys:review-panes-move-from-a-field-on-macos`
- **Layers:** unit
- **WHEN** `⌃L` is pressed with focus in a tag field, on macOS and then on Linux
- **THEN** on macOS the next pane takes the focus, and on Linux nothing moves

#### Scenario: the key list opens from a field
- **Key:** `ui:keys:the-key-list-opens-from-a-field`
- **Layers:** unit
- **WHEN** `?` and then `⌃/` are pressed with focus in a text field
- **THEN** `?` is typed into the field and `⌃/` opens the key list

#### Scenario: Review's fields move from a field on macOS
- **Key:** `ui:keys:review-fields-move-from-a-field-on-macos`
- **Layers:** unit
- **WHEN** Review's commands are declared on macOS and then on Linux
- **THEN** on macOS `⌃J` and `⌃K` move to the next and the previous field from a text field
- **AND** on Linux neither is declared

### Requirement: A dialog holds the focus while it is open

The system SHALL open every confirming dialog — Render, Revise, Delete, and New collection or Add sources — and the key
list as a modal dialog,
the page behind it inert, the focus on its first control and held inside it, and SHALL return the focus to where it
was when it closes. The Render dialog's first control SHALL be *Keep the volume open*, which `Space` toggles and
`↵` leaves alone; the Revise dialog's SHALL be its confirm button, and the Delete dialog's its *No*. The key list
SHALL stand centred over most of the window, its keys in columns by scope — everywhere, then the screen's — and `⌃/`,
`Esc` and the backdrop SHALL close it.

A key goes where the eye is. A dialog over a grid that leaves the focus on the grid sends `↵` and `Tab` to what it
covers; and only `Mod+↵` spends money, so `↵` on the checkbox never renders.

#### Scenario: the Render dialog opens on its checkbox
- **Key:** `ui:dialogs:the-render-dialog-opens-on-its-checkbox`
- **Layers:** e2e
- **WHEN** the Render dialog opens on the hub, then `Tab` is pressed until the focus has passed every control
- **THEN** *Keep the volume open* held the focus first, and the focus never left the dialog
- **AND** `Esc` returns the focus to the hub cell it left

#### Scenario: the key list is a dialog
- **Key:** `ui:dialogs:the-key-list-is-a-dialog`
- **Layers:** unit
- **WHEN** `⌃/` opens the key list on a screen
- **THEN** it is a modal dialog holding the focus, the everywhere keys in one column and the screen's in another
- **AND** `⌃/`, `Esc` and a click on the backdrop each close it

