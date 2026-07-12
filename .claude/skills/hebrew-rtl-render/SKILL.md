---
name: hebrew-rtl-render
description: >-
  🔤 [תיקון עברית בכפתורים ולייבלים — סדר עברית+לטינית ב-RTL] —
  Use this WHENEVER you edit mixed Hebrew+Latin text on a tkinter/customtkinter
  widget in the bridge-student app — button labels, table cells, panel lines —
  where a bid (2♣, 1NT), a number, or a Latin word sits inside Hebrew. The
  on-screen left/right order of such text is decided by Tk's BiDi engine and is
  NOT predictable from the string you type; guessing it by eye burns entire
  sessions of "no, the other side" back-and-forth. This skill's rule is simple:
  never guess — render the candidate in the real widget, capture a PNG, and
  look. Trigger on any request like "the NT should be on the left", "fix the
  order on the שיעור button", "the bid flips on the button", "why is the number
  on the wrong side", or any edit to a `_BUTTONS` / label string that mixes
  Hebrew with Latin/numbers/bids. Also read this before touching the שיעור-8
  slam-NT button, whose correct string is recorded below.
---

# Rendering mixed Hebrew + Latin labels without guessing

## The trap

A label like `סלם NT` is stored as one logical string, but Tk reorders it with
the Unicode BiDi algorithm before drawing. Where the `NT` lands (left edge?
right edge? next to which Hebrew word?) is **not** obvious from the string, and
small mixed strings are genuinely easy to misread. Every time this was "solved"
by reasoning about left/right in chat, it flipped to the wrong side on the next
screenshot. Do not reason about it. Render it.

## Golden rule

**Never hand-guess the visual order of mixed Hebrew+Latin text. Render the real
widget to a PNG and look at it.**

## The tool

`scripts/render_label.py` renders any label string in a `CTkButton` that is
identical to the app's (same `fix()`, same font family), captures it to a PNG,
and captions each button with the exact logical string that produced it.

```bash
cd D:/bridge-student
# render several candidates at once — the recommended way:
python .claude/skills/hebrew-rtl-render/scripts/render_label.py \
    "שיעור 8\nסלם ב NT" \
    "שיעור 8\nNT סלם ב"
```

Then `Read` the printed PNG path. **Pick the button whose appearance matches the
desired layout, and copy its captioned logical string verbatim into the code.**
That's it — no direction math.

### How to work the loop

1. Write down the desired on-screen order as a token sequence, e.g. desired
   left→right = `NT` · `ב` · `סלם`. (Describe by token *content*, never by a bare
   "left"/"right" word — that phrasing is exactly what caused the confusion.)
2. Render 3–6 permutations of the tokens in one call, each captioned.
3. Read the PNG, find the button that matches the desired sequence, copy its
   logical string.
4. Paste it into the code (e.g. `_BUTTONS` in `app.py`), and — if the app is
   running — screenshot the *real* app once to confirm, since an isolated render
   can in rare cases differ from the live window.

If a human is available, the fastest ground truth is to show them the
multi-candidate PNG and let them point at the right one. Don't argue about
sides — let the picture decide.

## Confirmed answers (do not re-litigate)

These were verified on screen and confirmed by the user. Reuse them as-is;
re-deriving them wastes a session.

| Button | Desired on-screen (L→R) | Correct label string in code |
|--------|-------------------------|------------------------------|
| שיעור 8 — סלם ב-NT | `NT` · `ב` · `סלם` | `'שיעור 8\nNT סלם ב'` |

So in `app.py` `_BUTTONS`, the שיעור-8 entry is:

```python
('שיעור 8\nNT סלם ב',    10),
```

Note how un-intuitive this is: the *code* reads `NT סלם ב` but the *screen*
reads `NT ב סלם`. That gap is the whole reason this skill exists — you cannot
get it right from the string alone.

## The web side is different (and deterministic)

This skill is for the **tkinter/CTk desktop app**. For HTML output, the project
rule (see `CLAUDE.md`) is deterministic and needs no rendering: wrap every Latin
run / number / bid in `<bdi>` (or apply `unicode-bidi: isolate`), and add
`dir="auto"` to dynamic fields. Do that instead of rendering when the target is
a web page.

## Why this is worth the tooling

One three-token line (`NT` `ב` `סלם`) consumed an entire session of "it's on the
wrong side again". The render-and-look loop turns that into a single
deterministic step. Spend the 20 seconds to render; never trust a guess.
