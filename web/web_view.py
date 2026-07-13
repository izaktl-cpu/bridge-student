"""
מתאם View מנותק (headless) — מחקה את ממשק ה-tkinter שהשיעורים מכירים,
אבל במקום לצייר פיקסלים הוא רושם את המצב לאובייקט JSON.

השיעורים וה-engine רצים ללא שינוי. מחליפים רק את אובייקט ה-app.
"""
from engine.cards import SUITS, SUIT_SYMBOLS, hand_by_suit, fmt_rank
from engine.scoring import hcp as _hcp

_PLAYERS = ['N', 'E', 'S', 'W']
_SUIT_ORDER = {'♣': 0, '♦': 1, '♥': 2, '♠': 3, 'NT': 4}


def _bid_rank(bid):
    """דירוג הכרזה לצורך חוקיות — זהה ל-BiddingPanel._rank."""
    if not bid or bid in ('Pass', 'X', 'XX'):
        return -1
    return int(bid[0]) * 5 + _SUIT_ORDER[bid[1:]]


# ── מכרז ────────────────────────────────────────────────────────────────────

class RecordingAuction:
    """מחקה את AuctionWidget — רושם רצף הכרזות עם המושב של כל אחת."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._dealer = 'N'
        self._seat_idx = 0
        self.bids = []          # [{'seat', 'bid', 'highlight'}]

    def set_dealer(self, player):
        self._dealer = player
        self._seat_idx = _PLAYERS.index(player)

    def add_bid(self, bid_text, highlight=False):
        seat = _PLAYERS[self._seat_idx % 4]
        self.bids.append({'seat': seat, 'bid': bid_text, 'highlight': bool(highlight)})
        self._seat_idx += 1

    def seal(self):
        """הוסף פסים עד 3 פסים רצופים בסוף."""
        passes = 0
        for b in reversed(self.bids):
            if b['bid'] == 'Pass':
                passes += 1
            else:
                break
        for _ in range(max(0, 3 - passes)):
            self.add_bid('Pass')

    def snapshot(self):
        return {'dealer': self._dealer, 'bids': list(self.bids)}


# ── תיבת הכרזה ──────────────────────────────────────────────────────────────

class RecordingBiddingBox:
    """מחקה את BiddingPanel — מחשב אילו הכרזות חוקיות/מותרות."""

    _ALL_BIDS = ['Pass', 'X', 'XX'] + [
        f'{lvl}{suit}' for lvl in range(1, 8) for suit in ['♣', '♦', '♥', '♠', 'NT']
    ]

    def __init__(self):
        self.reset()

    def reset(self):
        self._last_bid = None
        self._allowed = None    # None = לפי חוקיות בלבד
        self._locked = False
        self._no_pass = False

    def set_bids(self, bids):
        self._allowed = set(bids) if bids is not None else None

    def set_last_bid(self, bid, no_pass=False):
        if bid not in ('Pass', 'X', 'XX'):
            self._last_bid = bid
        self._no_pass = no_pass

    def disable(self):
        self._locked = True

    def enable(self):
        self._locked = False

    def clear(self):
        self.set_bids(None)

    def _legal(self, bid):
        if bid == 'Pass':
            return not self._no_pass
        if bid in ('X', 'XX'):
            return True
        return _bid_rank(bid) > _bid_rank(self._last_bid)

    def enabled_bids(self):
        if self._locked:
            return []
        out = []
        for bid in self._ALL_BIDS:
            ok = (bid in self._allowed) if self._allowed is not None else self._legal(bid)
            if ok:
                out.append(bid)
        return out

    def snapshot(self):
        return {'enabled': self.enabled_bids(), 'locked': self._locked}


# ── שולחן ───────────────────────────────────────────────────────────────────

class RecordingTable:
    """מחקה את BridgeTable — עוקב אחרי ידיים גלויות ומשוב."""

    def __init__(self):
        self.hands = {}
        self.visible = ('S',)
        self._fb_text = ''
        self._fb_ok = True
        self._fb_shown = False

    def show_hands(self, hands, visible=('S',)):
        self.hands = hands
        self.visible = visible

    def set_feedback(self, text, ok=True):
        self._fb_text = text
        self._fb_ok = ok
        self._fb_shown = bool(text) or ok

    def clear_feedback(self):
        self._fb_text = ''
        self._fb_shown = False

    def showing_wrong(self):
        return self._fb_shown and not self._fb_ok

    def hands_snapshot(self):
        out = {}
        for seat in _PLAYERS:
            hand = self.hands.get(seat)
            if hand is None:
                continue
            vis = seat in self.visible
            by_suit = hand_by_suit(hand)
            out[seat] = {
                'visible': vis,
                'hcp': _hcp(hand) if vis else None,
                'suits': {s: [fmt_rank(r) for r in by_suit[s]] for s in SUITS} if vis else None,
            }
        return out


# ── ה-app עצמו ──────────────────────────────────────────────────────────────

class WebApp:
    """חזית ה-app שהשיעורים מכירים, בגרסה חסרת-ממשק."""

    def __init__(self):
        self.table = RecordingTable()
        self.auction_widget = RecordingAuction()
        self.bidding_box = RecordingBiddingBox()
        self._lesson = None
        self._reset_panel()

    def _reset_panel(self):
        self._panel_header = ''
        self._panel_text = ''
        self._pending_table = None
        self._tables = []       # טבלאות מוצגות: כל אחת רשימת שורות
        self._feedback = {'text': '', 'ok': True, 'shown': False}

    # ── API לשיעורים ────────────────────────────────────────────────────────

    def set_instruction(self, text):
        if text and self.table.showing_wrong():
            self.table.set_feedback('', ok=True)
        self._pending_table = None
        self._panel_text = text or ''
        if text:
            self._panel_header = ''

    def set_instruction_table(self, header, rows):
        if self.table.showing_wrong():
            self.table.set_feedback('', ok=True)
        else:
            self.table.clear_feedback()
        self._pending_table = rows
        self._panel_header = header or ''
        self._panel_text = ''

    def add_immediate_table(self, rows):
        self._tables.append([list(r) for r in rows])

    def reveal_instruction_table(self):
        rows = self._pending_table
        if not rows:
            return
        self._pending_table = None
        self._tables.append([list(r) for r in rows])

    def set_feedback(self, text, ok=True, correct_answer=''):
        self.reveal_instruction_table()
        self.table.set_feedback(text, ok)
        self._feedback = {'text': text, 'ok': ok, 'shown': True}

    def show_all_hands(self):
        if self._lesson:
            self.table.show_hands(self._lesson.hands, visible=('N', 'E', 'S', 'W'))

    def show_new_deal_button(self):
        pass  # תמיד גלוי ב-web

    def after(self, ms, fn):
        # tkinter scheduling — ב-web מריצים מיד (השימושים הם after(0, ...))
        fn()

    # ── ניהול שיעור ──────────────────────────────────────────────────────────

    def load_lesson(self, lesson_cls):
        self._reset_panel()
        self.table = RecordingTable()
        self.auction_widget = RecordingAuction()
        self.bidding_box = RecordingBiddingBox()
        self._lesson = lesson_cls(self)
        return self._lesson

    def new_turn(self):
        """איפוס המצב הרך לפני הכרזת תלמיד — משאיר ידיים ומכרז."""
        pass

    # ── תמונת מצב ל-frontend ──────────────────────────────────────────────────

    def snapshot(self):
        return {
            'title': getattr(self._lesson, 'TITLE', ''),
            'hands': self.table.hands_snapshot(),
            'auction': self.auction_widget.snapshot(),
            'bidding_box': self.bidding_box.snapshot(),
            'panel': {
                'header': self._panel_header,
                'text': self._panel_text,
                'tables': self._tables,
            },
            'feedback': dict(self._feedback),
            'done': self.bidding_box._locked,
        }
