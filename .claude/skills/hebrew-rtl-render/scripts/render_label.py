#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
render_label.py — מרנדר טקסט של כפתור/תווית *בדיוק* כמו האפליקציה (CTkButton עם
fix()), מצלם ל-PNG, כדי שאפשר יהיה **לראות** את הסדר החזותי האמיתי במקום לנחש.

למה זה קיים
-----------
טקסט מעורב עברית+לטינית (למשל "סלם NT") מסודר על ידי אלגוריתם ה-BiDi של Tk
בצורה שקשה לנבא מהמחרוזת הלוגית לבדה. ניחוש = לופ אינסופי של "שמאל/ימין".
במקום זה: מרנדרים את כל המועמדים בבת אחת, כל אחד עם כיתוב של המחרוזת הלוגית
שלו, מסתכלים איזה נראה כמו הרצוי — ומעתיקים את המחרוזת הזו לקוד.

שימוש
-----
    # מועמד בודד:
    python render_label.py "שיעור 8\\nNT סלם ב"

    # כמה מועמדים זה מעל זה (מומלץ) — כל אחד עם כיתוב:
    python render_label.py "שיעור 8\\nסלם ב NT" "שיעור 8\\nNT סלם ב"

- כל ארגומנט חופשי = לייבל אחד (כמו הארגומנט הראשון ל-fix()). \\n = שורה חדשה.
- --out PATH   נתיב ה-PNG (ברירת מחדל: label_preview.png ליד הסקריפט).
- --flip       שומר גם עותק הפוך-אופקית (label_preview_flipped.png). שים לב:
               הפיכת פיקסלים הופכת גם את האותיות (הן נראות "הפוכות"), אז זו
               בדיקת-שפיות בלבד ולא תצוגה אמיתית.
- --size N     גודל פונט לרינדור גדול וקריא (ברירת מחדל 28).

מדפיס את נתיב/י ה-PNG. קרא/פתח כדי לראות מה באמת מוצג.
"""
import os
import sys
import time
import argparse

# מאפשר לייבא את utils של הפרויקט (fix, F) מכל מקום שממנו מריצים.
# הסקריפט יושב ב-<root>/.claude/skills/hebrew-rtl-render/scripts/
_SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SKILL_DIR, '..', '..', '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import customtkinter as ctk          # noqa: E402
from PIL import ImageGrab, ImageOps  # noqa: E402
from utils.rtl import fix            # noqa: E402


def render(labels, out_path, size=28, flip=False):
    """מרנדר כל לייבל בכפתור זהה לזה של app.py, ומצלם ל-PNG יחיד.
    מעל כל כפתור מופיע כיתוב עם המחרוזת הלוגית — כדי שתמיד יהיה ברור איזו
    מחרוזת יצרה איזו תצוגה."""
    ctk.set_appearance_mode('light')
    root = ctk.CTk()
    root.configure(fg_color='white')
    root.title('label_preview')
    frame = ctk.CTkFrame(root, fg_color='#e8edf8')
    frame.pack(padx=30, pady=30)

    for label in labels:
        ctk.CTkLabel(
            frame, text='logical: ' + label.replace('\n', ' / '),
            font=ctk.CTkFont(family='Gisha', size=13), text_color='#888',
        ).pack()
        ctk.CTkButton(
            frame, text=fix(label),
            width=max(240, size * 8), height=size * 3,
            font=ctk.CTkFont(family='Gisha', size=size),
            fg_color='#2a5a9b', hover_color='#1a3a6b',
        ).pack(padx=16, pady=(0, 14))

    root.update_idletasks()
    root.update()
    root.lift()
    root.focus_force()
    root.attributes('-topmost', True)
    root.update()
    time.sleep(0.4)          # נותן ל-Tk לסיים לצייר לפני הצילום
    root.update()

    x, y = root.winfo_rootx(), root.winfo_rooty()
    w, h = root.winfo_width(), root.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save(out_path)
    outputs = [out_path]

    if flip:
        flipped = os.path.splitext(out_path)[0] + '_flipped.png'
        ImageOps.mirror(img).save(flipped)
        outputs.append(flipped)

    root.destroy()
    return outputs


def main():
    ap = argparse.ArgumentParser(description='Render CTk button label(s) to PNG.')
    ap.add_argument('labels', nargs='+', help=r'One or more label strings (use \n for newline).')
    ap.add_argument('--out', default=os.path.join(_SKILL_DIR, 'label_preview.png'))
    ap.add_argument('--size', type=int, default=28)
    ap.add_argument('--flip', action='store_true')
    args = ap.parse_args()

    labels = [lbl.replace('\\n', '\n') for lbl in args.labels]
    for out in render(labels, args.out, size=args.size, flip=args.flip):
        print(out)


if __name__ == '__main__':
    main()
