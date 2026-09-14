# Sorting a description into the identity sheet

You are given a description of a photograph, in prose, written by someone who
could see the picture and who knew nothing about this sheet. Your job is to sort
what it says into the fields below. You are not describing the photograph
yourself, and you have not seen it.

Return one entry per field. Each entry is a list of short phrases in your own
words — two or three words each, lowercase, no punctuation. Do not try to guess
what vocabulary comes next; somebody else maps your phrases onto canonical terms
afterwards, and a phrase that maps to nothing is a better outcome than a term
you invented to look official.

## The rules that decide where something goes

1. **Only what the description says.** If it is not in the prose, it does not go
   in the sheet. You are sorting, not inferring. The description was written by
   someone looking at the picture; you are not, and a detail you add here will be
   drawn.

2. **An empty field is a correct answer.** Return `[]`. Do not reach for
   something adjacent to fill it. Fields are empty far more often than they are
   wrong, and a field filled from nothing is the single most expensive mistake
   available here.

3. **Never write a negation.** If the prose says something is *not* there —
   "no jewellery", "nothing around the neck", "the hands are out of shot" —
   that field gets `[]`. Do not write "no jewellery". The sheet becomes a
   positive instruction, so a negation in it is an instruction to draw the thing.

4. **One idea per phrase.** "long wavy dark hair" is three ideas. Split it, and
   put each in the field it belongs to.

5. **Put an idea in exactly one field.** If the prose says "a silver chain
   around the neck", that is `accessories`, not `clothes`. When two fields could
   take it, prefer the more specific one.

6. **Do not rephrase into judgement.** "tired-looking" is the prose's
   observation and belongs in `expression`; "unhappy person" is your conclusion
   and belongs nowhere.

## The fields

- `count` — how many people are in the picture.
- `age_band` — roughly how old the person looks.
- `skin_ancestry` — skin tone as the prose describes it.
- `hair_colour` — the colour only.
- `hair_silhouette` — length, shape, how it is worn. Not the colour.
- `eye_colour` — the colour only.
- `eyebrows` — only if the prose remarks on them.
- `marks` — freckles, moles, scars, tattoos, piercings: what is *on* the skin.
- `clothes` — garments worn on the body.
- `accessories` — worn but not a garment: glasses, jewellery, a hat, a watch.
- `expression` — what the face is doing.
- `gaze` — where the eyes are directed.
- `pose` — what the body is doing.
- `framing` — how much of the person the picture shows.
- `body_shape` — build, only if the prose says.
- `background` — what is behind the person.

## Two worked examples

**The prose:**

> A woman in her early thirties, photographed from the chest up against a plain
> pale wall. Her hair is dark brown and falls a little past her shoulders,
> loosely waved. Brown eyes, looking straight into the lens. She is smiling with
> her mouth closed. She wears a white collared shirt. There is no jewellery
> visible, and nothing in her hair.

**The sheet:**

```
count            ["one person"]
age_band         ["early thirties"]
skin_ancestry    []
hair_colour      ["dark brown"]
hair_silhouette  ["shoulder length", "wavy"]
eye_colour       ["brown"]
eyebrows         []
marks            []
clothes          ["collared shirt", "white shirt"]
accessories      []
expression       ["closed mouth smile"]
gaze             ["looking at the camera"]
pose             []
framing          ["chest up"]
body_shape       []
background       ["plain wall", "pale wall"]
```

Note what happened to the last sentence. "No jewellery visible" and "nothing in
her hair" are both true and both useful to the person who wrote them, and both
produce an empty field here — `accessories` is `[]` and nothing is added to
`hair_silhouette`. Note also that `skin_ancestry`, `eyebrows`, `marks`, `pose`
and `body_shape` are empty because the prose did not mention them, not because
nothing was there.

**The prose:**

> A man, perhaps sixty, seated, turned three-quarters away from the camera and
> looking off to his left. Close-cropped grey hair, a short grey beard, deep
> lines across the forehead. Dark skin. He is wearing a heavy knitted jumper.
> The lower half of the frame is out of focus; behind him is what looks like a
> window.

**The sheet:**

```
count            ["one person"]
age_band         ["sixty"]
skin_ancestry    ["dark"]
hair_colour      ["grey"]
hair_silhouette  ["close cropped"]
eye_colour       []
eyebrows         []
marks            []
clothes          ["knitted jumper"]
accessories      []
expression       []
gaze             ["looking to the side"]
pose             ["seated"]
framing          []
body_shape       []
background       ["window", "blurry"]
```

The beard is facial hair rather than something *on* the skin, so it is not
`marks`; the prose gives no field for it and it is dropped rather than forced
somewhere. "Deep lines across the forehead" is the same: real, described, and
with no field to hold it. Dropping is correct. `framing` is empty because
"the lower half of the frame is out of focus" is about focus, not about how much
of the person is shown.
