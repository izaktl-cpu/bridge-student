import customtkinter as ctk
from utils.fonts import FB

_SUITS  = ['♣', '♦', '♥', '♠', 'NT']
_LEVELS = list(range(1, 8))

_COLORS = {
    '♣':  ('#7a4a1a', '#5a3210'),
    '♦':  ('#e06000', '#b84e00'),
    '♥':  ('#cc1111', '#991100'),
    '♠':  ('#222222', '#000000'),
    'NT': ('#1a3a8b', '#0f2560'),
}
_PASS_CLR  = ('#666666', '#444444')
_X_CLR     = ('#cc1111', '#991100')
_XX_CLR    = ('#880000', '#550000')
_DISABLED  = ('#c0c0c0', '#c0c0c0')


def _rank(bid):
    if not bid or bid in ('Pass', 'X', 'XX'):
        return -1
    order = {'♣': 0, '♦': 1, '♥': 2, '♠': 3, 'NT': 4}
    return int(bid[0]) * 5 + order[bid[1:]]


class BiddingPanel(ctk.CTkFrame):
    """פנל הכרזה מלא: Pass / X / XX ו-1♣ עד 7NT."""

    def __init__(self, parent, on_bid, **kw):
        super().__init__(parent, fg_color='#eef2f8', corner_radius=10,
                         border_width=1, border_color='#b0c0d8', **kw)
        self._on_bid   = on_bid
        self._btns     = {}
        self._allowed  = None   # None = לפי חוקיות בלבד
        self._last_bid = None   # ההכרזה האחרונה שאינה Pass/X/XX
        self._locked   = False
        self._no_pass  = False
        self._build()

    # ── בנייה ──────────────────────────────────────────────────────────────

    def _build(self):
        self._colors = {}   # bid → (fg, hover)

        _W  = 48   # רוחב כפתור הכרזה
        _H  = 28   # גובה
        _FS = 15   # גודל גופן

        # שורה 1: Pass / X / XX
        top = ctk.CTkFrame(self, fg_color='transparent')
        top.pack(pady=(3, 1), padx=4)
        for text, clr in [('Pass', _PASS_CLR), ('X', _X_CLR), ('XX', _XX_CLR)]:
            fg, hv = clr
            self._colors[text] = clr
            b = ctk.CTkButton(top, text=text, width=_W, height=_H,
                              font=FB(_FS),
                              fg_color=fg, hover_color=hv,
                              command=lambda t=text: self._click(t))
            b.pack(side='left', padx=1)
            self._btns[text] = b

        # שורות 1–7
        for lvl in range(1, 8):
            row = ctk.CTkFrame(self, fg_color='transparent')
            row.pack(pady=1, padx=4)
            for suit in _SUITS:
                bid = f'{lvl}{suit}'
                clr = _COLORS[suit]
                fg, hv = clr
                self._colors[bid] = clr
                b = ctk.CTkButton(row, text=bid, width=_W, height=_H,
                                  font=FB(_FS),
                                  fg_color=fg, hover_color=hv,
                                  command=lambda t=bid: self._click(t))
                b.pack(side='left', padx=1)
                self._btns[bid] = b

        self._refresh()

    # ── API ────────────────────────────────────────────────────────────────

    def set_bids(self, bids):
        """הגבל לרשימה פדגוגית (None = ללא הגבלה מעבר לחוקיות)."""
        self._allowed = set(bids) if bids is not None else None
        self._refresh()

    def set_last_bid(self, bid, no_pass=False):
        """עדכן את ההכרזה האחרונה (לחוקיות). no_pass=True מסתיר Pass."""
        if bid not in ('Pass', 'X', 'XX'):
            self._last_bid = bid
        self._no_pass = no_pass
        self._refresh()

    def reset(self):
        self._last_bid = None
        self._allowed  = None
        self._locked   = False
        self._no_pass  = False
        self._refresh()

    def disable(self):
        self._locked = True
        for b in self._btns.values():
            b.configure(state='disabled', fg_color=_DISABLED[0], text_color='#888888')

    def enable(self):
        self._locked = False
        self._refresh()

    def clear(self):
        self.set_bids(None)

    # ── פנימי ──────────────────────────────────────────────────────────────

    def _click(self, bid):
        if not self._locked:
            self._on_bid(bid)

    def _legal(self, bid):
        if bid == 'Pass':
            return not self._no_pass
        if bid in ('X', 'XX'):
            return True
        return _rank(bid) > _rank(self._last_bid)

    def _refresh(self):
        if self._locked:
            return
        for bid, btn in self._btns.items():
            if self._allowed is not None:
                ok = bid in self._allowed
            else:
                ok = self._legal(bid)
            if ok:
                fg, hv = self._colors[bid]
                btn.configure(state='normal', fg_color=fg, hover_color=hv,
                              text_color='white')
            else:
                btn.configure(state='disabled', fg_color=_DISABLED[0],
                              hover_color=_DISABLED[1], text_color='#888888')
