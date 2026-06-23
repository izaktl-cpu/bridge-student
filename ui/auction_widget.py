import customtkinter as ctk
from utils.fonts import F, FB

_PLAYERS  = ['N', 'E', 'S', 'W']
_PRE_ROWS = 4

_SUIT_COLORS = {
    '♣': '#7a4a1a',
    '♦': '#e06000',
    '♥': '#cc1111',
    '♠': '#222222',
    'NT': '#1a3a8b',
    'Pass': '#666666',
    'X':    '#cc1111',
    'XX':   '#880000',
}

def _bid_color(bid):
    for key, color in _SUIT_COLORS.items():
        if key in bid:
            return color
    return '#444444'


class AuctionWidget(ctk.CTkFrame):
    """טבלת מכרז: ריבוע כחלחל — עמודות N E S W שוות רוחב"""

    def __init__(self, parent, **kw):
        super().__init__(parent,
                         fg_color='#e8edf8',
                         border_width=1,
                         border_color='#b0bcd8',
                         corner_radius=6,
                         **kw)

        for col in range(4):
            self.grid_columnconfigure(col, weight=1, uniform='col')

        for col, p in enumerate(_PLAYERS):
            ctk.CTkLabel(self, text=p, font=FB(15),
                         text_color='#1a3a6b', anchor='center'
                         ).grid(row=0, column=col, padx=2, pady=(6, 3), sticky='ew')

        self._pre_cells: dict[tuple, ctk.CTkLabel] = {}
        for r in range(1, _PRE_ROWS + 1):
            for c in range(4):
                lbl = ctk.CTkLabel(self, text='',
                                   font=F(15),
                                   text_color='#222222',
                                   fg_color='transparent',
                                   anchor='center')
                lbl.grid(row=r, column=c, padx=2, pady=2, sticky='ew')
                self._pre_cells[(r, c)] = lbl

        self._row = 1
        self._col = 0
        self._bids: list[str] = []

    def set_dealer(self, player):
        self._col = _PLAYERS.index(player)

    def add_bid(self, bid_text, highlight=False):
        color = _bid_color(bid_text)
        font  = FB(15) if highlight else F(15)

        cell = self._pre_cells.get((self._row, self._col))
        if cell:
            cell.configure(text=bid_text, text_color=color, font=font)
        else:
            lbl = ctk.CTkLabel(self, text=bid_text, font=font,
                               text_color=color, fg_color='transparent',
                               anchor='center')
            lbl.grid(row=self._row, column=self._col, padx=2, pady=2, sticky='ew')

        self._bids.append(bid_text)
        self._col += 1
        if self._col >= 4:
            self._col = 0
            self._row += 1

    def seal(self):
        """סגור את המכרז: הוסף פסים עד שיש 3 פסים רצופים בסוף."""
        passes = 0
        for b in reversed(self._bids):
            if b == 'Pass':
                passes += 1
            else:
                break
        for _ in range(max(0, 3 - passes)):
            self.add_bid('Pass')

    def reset(self):
        for lbl in self._pre_cells.values():
            lbl.configure(text='', text_color='#222222', font=F(15))
        for w in self.grid_slaves():
            if int(w.grid_info()['row']) > _PRE_ROWS:
                w.destroy()
        self._row = 1
        self._col = 0
        self._bids = []
