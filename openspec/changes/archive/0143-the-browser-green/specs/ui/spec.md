## MODIFIED Requirements

### Requirement: The large view deletes its render after asking, and the Hub opens on its cell

The system SHALL offer *Delete* on a render's large view, on `⇧⌫`, after *Compare with…*, opening a modal dialog,
*Delete this render?*, whose *No* comes first and holds the focus; `h` `l` and `←` `→` SHALL move between *No* and
*Yes*, `↵` SHALL press the focused one, and `Esc` SHALL answer *No*. *Yes* SHALL delete the render's own thumbnails from
the library's cache, discard the render through the render stage — its approval going with its last render, and a flow
left with no approval keeping only its assignment — and open the Hub focused on the render's cell, from whichever screen
opened the view. The server SHALL refuse the delete while a render session runs for the collection, deleting nothing,
and the dialog SHALL show the refusal.

A failed render is deleted where it is seen. *No* first makes a stray `↵` harmless, and a write beside a running session
is refused, as *Cancel approve* is. The cell is where the delete shows: one image fewer, an older approval's images once
the newest's last image goes, or *tagged* once the flow's last approval goes, with nothing to review. A thumbnail is
told from another collection's of the same photograph and seed by its image's digest, so only the render's own goes.

```
large view ──⇧⌫──▶ Delete this render?  [No] [Yes]
                     │ Esc · No              │ Yes
                     ▼                       ▼
                 large view           thumbnails ─▶ discard ─▶ its approval, if emptied ─▶ the Hub on the cell
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
- **THEN** the Hub opens focused on that cell, reading *tagged*
- **AND** the image, its approval's prompt and the flow's sheet are gone from the run

#### Scenario: the Hub opens without the deleted render
- **Key:** `ui:delete-render:the-hub-opens-without-the-deleted-render`
- **Layers:** e2e
- **WHEN** `⇧⌫`, `l` and `↵` are pressed on the large view of a cell's only image
- **THEN** the Hub is read again before it opens, and no thumbnail of the deleted render is asked for

#### Scenario: the route deletes the render and its thumbnail
- **Key:** `ui:delete-render:the-route-deletes-the-render-and-its-thumbnail`
- **Layers:** unit
- **WHEN** a render whose thumbnail is cached is deleted at its address
- **THEN** its image, its record and its thumbnail are gone
- **AND** the other render and its thumbnail stay, and so does another collection's thumbnail of the same photograph
  and seed

#### Scenario: the delete is refused while a render runs
- **Key:** `ui:delete-render:refused-while-a-render-runs`
- **Layers:** unit
- **WHEN** a render is deleted while a render session runs for its collection
- **THEN** the delete is refused, saying a render session is running
- **AND** no file is deleted
