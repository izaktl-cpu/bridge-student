import customtkinter as ctk
from engine.cards import SUITS, SUIT_SYMBOLS, SUIT_COLORS, hand_by_suit, fmt_suit_cards
from engine.scoring import hcp as _hcp
from utils.fonts import F, FB, FB_FEEDBACK
from utils.rtl import fix

TABLE_GREEN = '#1e5c1e'
PANEL_BG    = '#ffffff'


class PlayerPanel(ctk.CTkFrame):
    def __init__(self, parent, name, **kw):
        super().__init__(parent, fg_color=PANEL_BG, corner_radius=8,
                         border_width=1, border_color='#aaaaaa', **kw)

        ctk.CTkLabel(self, text=name,
                     font=FB(12),
                     text_color='#222222').pack(pady=(1, 0))

        self._hcp_label = ctk.CTkLabel(self, text='',
                                        font=F(10),
                                        text_color='#555555')
        self._hcp_label.pack(pady=0)

        self._suit_labels = {}
        for suit in SUITS:
            row = ctk.CTkFrame(self, fg_color=PANEL_BG)
            row.pack(fill='x', padx=3, pady=0)

            ctk.CTkLabel(row,
                         text=SUIT_SYMBOLS[suit],
                         font=F(20),
                         text_color=SUIT_COLORS[suit],
                         width=24,
                         anchor='w').pack(side='left')

            lbl = ctk.CTkLabel(row, text='',
                               font=FB(16),
                               text_color='#333333',
                               anchor='w')
            lbl.pack(side='left', fill='x', expand=True, padx=2)
            self._suit_labels[suit] = lbl

        ctk.CTkLabel(self, text='', height=0, fg_color=PANEL_BG).pack()

    def show_hand(self, hand):
        by_suit = hand_by_suit(hand)
        for suit in SUITS:
            text  = fmt_suit_cards(by_suit[suit])
            color = SUIT_COLORS[suit]
            self._suit_labels[suit].configure(text=text, text_color=color)
        self._hcp_label.configure(text=fix(f'{_hcp(hand)} נק׳'))

    def hide_hand(self):
        for suit in SUITS:
            self._suit_labels[suit].configure(text='■ ■ ■', text_color='#888888')
        self._hcp_label.configure(text='')


class BridgeTable(ctk.CTkFrame):
    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=TABLE_GREEN, corner_radius=12, **kw)

        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=0)

        self._panels = {}

        # North
        self._panels['N'] = PlayerPanel(self, 'North')
        self._panels['N'].grid(row=0, column=1, padx=(4, 8), pady=1, sticky='sew')

        # West
        self._panels['W'] = PlayerPanel(self, 'West')
        self._panels['W'].grid(row=1, column=0, padx=(4, 8), pady=1, sticky='ew')

        # East
        self._panels['E'] = PlayerPanel(self, 'East')
        self._panels['E'].grid(row=1, column=2, padx=(8, 4), pady=1, sticky='ew')

        # South
        self._panels['S'] = PlayerPanel(self, 'South ★')
        self._panels['S'].grid(row=2, column=1, padx=(4, 8), pady=1, sticky='new')

        # פינה ימין תחתונה — משוב קצר
        self._feedback_lbl = ctk.CTkLabel(
            self, text='',
            font=FB_FEEDBACK(18),
            text_color='white',
            fg_color='transparent',
            wraplength=180,
            justify='center',
            anchor='center')
        self._feedback_lbl.grid(row=2, column=2, padx=3, pady=3, sticky='nsew')

        # Compass
        compass = ctk.CTkFrame(self, fg_color=TABLE_GREEN)
        compass.grid(row=1, column=1, padx=4, pady=4)
        cf = FB(13)
        ctk.CTkLabel(compass, text='N', font=cf, text_color='white').grid(row=0, column=1, padx=4)
        ctk.CTkLabel(compass, text='W', font=cf, text_color='white').grid(row=1, column=0, padx=4)
        ctk.CTkLabel(compass, text='E', font=cf, text_color='white').grid(row=1, column=2, padx=4)
        ctk.CTkLabel(compass, text='S', font=cf, text_color='white').grid(row=2, column=1, padx=4)

    def set_feedback(self, text, ok=True):
        _BIDI = str.maketrans('', '', '‪‫‬‭‮‎‏')
        def clean(s):
            return '\n'.join(l.translate(_BIDI).rstrip(' .,-–—') for l in s.split('\n') if l.strip())
        if ok:
            label = 'נכון'
        else:
            body = clean(text) if text else ''
            # פידבק שגוי — להשאיר רק מ"ההכרזה הנכונה" והלאה, בלי שורות הסבר
            lines = body.split('\n')
            for i, ln in enumerate(lines):
                if 'ההכרזה הנכונה' in ln:
                    body = '\n'.join(lines[i:])
                    break
            label = 'לא נכון' + ('\n' + body if body else '')
        color = '#90ee90' if ok else '#ffaaaa'
        self._feedback_lbl.configure(text=label, text_color=color)

    def clear_feedback(self):
        self._feedback_lbl.configure(text='')

    def show_hands(self, hands, visible=('S',)):
        for player, panel in self._panels.items():
            if player in visible:
                panel.show_hand(hands[player])
            else:
                panel.hide_hand()
