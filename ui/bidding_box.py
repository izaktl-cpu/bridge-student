import customtkinter as ctk
from utils.fonts import F, FB


class BiddingBox(ctk.CTkFrame):
    """כפתורי הכרזה לתלמיד"""

    def __init__(self, parent, on_bid, **kw):
        super().__init__(parent, fg_color='#e8edf8', corner_radius=10,
                         border_width=1, border_color='#b0c0e0', **kw)
        self._on_bid  = on_bid
        self._buttons = []

        self._title = ctk.CTkLabel(
            self, text='בבקשה הכרז',
            font=FB(14),
            text_color='#1a3a6b',
            justify='right')
        self._title.pack(pady=(6, 3))

        self._btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        self._btn_frame.pack(pady=(0, 6), padx=10)

    def set_bids(self, bids):
        for b in self._buttons:
            b.destroy()
        self._buttons = []

        for bid in bids:
            is_pass = bid == 'Pass'
            btn = ctk.CTkButton(
                self._btn_frame,
                text=bid,
                width=62,
                height=34,
                font=FB(14),
                fg_color='#4a7a4a' if is_pass else '#2a5fa5',
                hover_color='#3a6a3a' if is_pass else '#1e4a8a',
                command=lambda b=bid: self._on_bid(b)
            )
            btn.pack(side='left', padx=3)
            self._buttons.append(btn)

    def disable(self):
        for b in self._buttons:
            b.configure(state='disabled')

    def enable(self):
        for b in self._buttons:
            b.configure(state='normal')

    def clear(self):
        for b in self._buttons:
            b.destroy()
        self._buttons = []
