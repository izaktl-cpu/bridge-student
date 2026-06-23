"""
תצוגה מקדימה של הודעות על פנל ירוק — לבדיקה ויזואלית.
הרץ: python tests/preview_messages.py
לחץ על כל כפתור לראות את ההודעה.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import customtkinter as ctk
from utils.rtl import fix

ctk.set_appearance_mode('light')

MESSAGES = [
    # ── גרבר ──────────────────────────────────────────────────────────────
    ('גרבר — 4 אסים (סלם)',
     'יש לנו 4 אסים מ-4.\nמחשב מכריז 6NT — סלם!\nחוזה סופי: 6NT.'),

    ('גרבר — 3 אסים (עצירה)',
     'יש לנו 3 אסים מ-4.\nחסר אס אחד.\nמחשב עוצר ב-5NT.\nחוזה סופי: 5NT.'),

    # ── Blackwood ──────────────────────────────────────────────────────────
    ('Blackwood — סלם ♥',
     'יש לנו 5 מפתחות מ-5.\nמחשב מכריז 6♥ — סלם!\nחוזה סופי: 6♥.'),

    ('Blackwood — עצירה',
     'יש לנו 4 מפתחות מ-5.\nחסרים מפתחות.\nמחשב עוצר ב-5♥.\nחוזה סופי: 5♥.'),

    # ── חוזה סופי ──────────────────────────────────────────────────────────
    ('נכון — 4♥',
     'נכון!\nיש 5 קלפי ♥ — N צריך 3 לתמיכה, מתקן ל-4♥.\nחוזה סופי: 4♥.'),

    ('נכון — 3NT',
     'נכון!\nללא התאמה ב-♠.\nחוזה סופי: 3NT.'),

    ('לא מיטבי',
     'לא מיטבי!\nהנכון: 3♥.\nיש לך 5 קלפי ♥ ו-3+ קלפי ♠.\nחוזה סופי: 4♠.'),
]


class PreviewApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('תצוגת הודעות')
        self.geometry('500x420')
        self.resizable(False, False)

        # פנל ירוק
        self._panel = ctk.CTkLabel(
            self, text='', fg_color='#1e5c1e',
            text_color='#90ee90', font=('Arial', 15),
            width=480, height=150,
            wraplength=460, justify='right', anchor='ne',
            corner_radius=8
        )
        self._panel.pack(padx=10, pady=(10, 6))

        # כפתורים
        frame = ctk.CTkScrollableFrame(self, width=480, height=220)
        frame.pack(padx=10, pady=4, fill='both', expand=True)

        for label, msg in MESSAGES:
            ctk.CTkButton(
                frame, text=label, width=460,
                command=lambda m=msg: self._show(m, ok=True),
                fg_color='#2a6496', hover_color='#1e4d72',
                font=('Arial', 13)
            ).pack(pady=3)

        ctk.CTkButton(
            frame, text='לא מיטבי (אדום)',
            width=460,
            command=lambda: self._show(MESSAGES[-1][1], ok=False),
            fg_color='#8b0000', hover_color='#600000',
            font=('Arial', 13)
        ).pack(pady=3)

    def _show(self, text, ok=True):
        color = '#90ee90' if ok else '#ffaaaa'
        self._panel.configure(
            text=fix(text.replace('\n\n', '\n')),
            text_color=color
        )


app = PreviewApp()
app.mainloop()
