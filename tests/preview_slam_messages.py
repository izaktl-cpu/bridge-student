"""
תצוגה מקדימה של תבניות הסלם — לבדיקה ויזואלית.
הרץ: python tests/preview_slam_messages.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import customtkinter as ctk
from utils.rtl import fix
from utils.messages import (
    msg_slam_correct, msg_slam_stop, msg_slam_wrong,
    msg_no_slam, msg_calc_game,
)

ctk.set_appearance_mode('light')

MESSAGES = [
    ('סלם הצליח — 6♠',       True,  msg_slam_correct('6♠', 5, 33)),
    ('עצרנו — 5♠',           True,  msg_slam_stop('5♠', 4, 31)),
    ('שגוי — הנכון 6♥',      False, msg_slam_wrong('5♥', '6♥', 5, 34)),
    ('אין סלם — 4♠',         False, msg_no_slam(29, '4♠')),
    ('אין משחק מלא — 4♥',    False, msg_calc_game('4♥')),
]


class PreviewApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('תצוגת תבניות סלם')
        self.geometry('500x380')
        self.resizable(False, False)

        self._panel = ctk.CTkLabel(
            self, text='לחץ על כפתור', fg_color='#1e5c1e',
            text_color='#90ee90', font=('Arial', 15),
            width=480, height=140,
            wraplength=0, justify='right', anchor='ne',
            corner_radius=8
        )
        self._panel.pack(padx=10, pady=(10, 6))

        frame = ctk.CTkScrollableFrame(self, width=480, height=190)
        frame.pack(padx=10, pady=4, fill='both', expand=True)

        for label, ok, msg in MESSAGES:
            color = '#2a6496' if ok else '#8b0000'
            hover = '#1e4d72' if ok else '#600000'
            ctk.CTkButton(
                frame, text=label, width=460,
                command=lambda m=msg, o=ok: self._show(m, o),
                fg_color=color, hover_color=hover,
                font=('Arial', 13)
            ).pack(pady=3)

    def _show(self, text, ok):
        color = '#90ee90' if ok else '#ffaaaa'
        self._panel.configure(text=fix(text), text_color=color)


app = PreviewApp()
app.mainloop()
