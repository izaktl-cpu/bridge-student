import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_ogust
from engine.scoring import hcp, sure_tricks, suit_len, rkcb_response, key_cards
from engine.cards import SUIT_SYMBOLS
from utils.messages import tricks
_S = SUIT_SYMBOLS

_FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

_EXPLAIN = {
    '3♣':  '6-7 נקודות מפוזרות',
    '3♦':  '6-7 נקודות בסדרה המוכרזת',
    '3♥':  '8-9 נקודות מפוזרות',
    '3♠':  '8-9 נקודות מרוכזות בסדרה',
    '3NT': 'AKQ בסדרה',
}

# דירוג הכרזות בגובה 3 — לבדיקה אם הרמה ל-3 בשליט חוקית מעל תשובת האוגוסט
_BID_RANK = {'3♣': 0, '3♦': 1, '3♥': 2, '3♠': 3, '3NT': 4}


def _partscore_bid(major, ogust_response):
    """הזמנת החלק-משחק של N: 3 בשליט אם זו הכרזה חוקית מעל תשובת הפותח,
    אחרת Pass (הפותח כבר בגובה 3 בשליט או מעל, כמו 3♥ בשליט לב)."""
    target = f'3{_S[major]}'
    if _BID_RANK[target] > _BID_RANK.get(ogust_response, -1):
        return target
    return 'Pass'


def _calc_ogust(hand, major):
    honors = sum(1 for c in hand if c[1] == major and c[0] in ('A', 'K', 'Q'))
    if honors == 3:
        return '3NT'
    h = hcp(hand)
    # מרוכז = אין שום מכובד (A/K/Q/J) מחוץ לשליט; מפוזר = יש מכובד כלשהו בחוץ, כולל J
    outside = sum(1 for c in hand if c[1] != major and c[0] in ('A', 'K', 'Q', 'J'))
    concentrated = outside == 0
    if h <= 7:
        return '3♦' if concentrated else '3♣'
    else:
        return '3♠' if concentrated else '3♥'


class LessonOgust(BaseLesson):
    """שיעור 11: S פותח Weak Two, מחשב שואל 2NT, S עונה אוגוסט, N מסכם"""

    TITLE = 'שיעור 11. Ogust'
    _opener_idx = 0

    def _next_opener(self):
        cls = LessonOgust
        word = _FEEDBACK_OPENERS[cls._opener_idx % len(_FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def _table(self, header, rows):
        """שומר את שורות הטבלה (לתצוגה בסיום) ומציג את הכותרת."""
        self._panel_rows = rows
        self.app.set_instruction_table(header, rows)

    # ─── start ───────────────────────────────────────────────────────────────

    def start(self):
        if not self._replaying:
            self._major = random.choice(['H', 'S'])
            self.hands  = deal_ogust(self._major)
        self._replaying      = False
        self._tries          = 0
        self._stage          = 'open'
        self._ogust_wrong    = False
        self._ogust_correct  = None

        sym = _S[self._major]
        h   = hcp(self.hands['S'])
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('S')

        self.app.bidding_box.set_last_bid(None)
        self._table(
            'מה תכריז',
            [
                (f'2{sym}', f'6 קלפים + 6-9 נקודות'),
            ]
        )

    # ─── routing ─────────────────────────────────────────────────────────────

    def on_student_bid(self, bid):
        if self._stage == 'open':
            self._handle_open(bid)
        elif self._stage == 'respond':
            self._handle_respond(bid)
        elif self._stage == 'north':
            self._handle_north(bid)
        elif self._stage == 'blackwood':
            self._handle_blackwood(bid)

    # ─── stage 1: פתיחה ──────────────────────────────────────────────────────

    def _handle_open(self, bid):
        sym     = _S[self._major]
        correct = f'2{sym}'
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            self.app.auction_widget.add_bid('2NT')                # N שואל
            self.app.auction_widget.add_bid('Pass')               # E
            self.app.bidding_box.set_last_bid('2NT')
            self._tries = 0
            self._stage = 'respond'
            self._show_respond_instruction()
        else:
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(f'ההכרזה הנכונה\n{correct}', ok=False, correct_answer=correct)

    def _show_respond_instruction(self):
        sym = _S[self._major]
        self._table(
            'מה תכריז',
            [
                ('3♣',  "6-7 נקודות מפוזרות"),
                ('3♦',  "6-7 נקודות בסדרה המוכרזת"),
                ('3♥',  "8-9 נקודות מפוזרות"),
                ('3♠',  "8-9 נקודות מרוכזות בסדרה"),
                ('3NT', 'AKQ בסדרה'),
            ]
        )

    # ─── stage 2: תגובת אוגוסט ───────────────────────────────────────────────

    def _handle_respond(self, bid):
        correct = _calc_ogust(self.hands['S'], self._major)
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            self._tries = 0
            self._ogust_bid = correct
            self._stage = 'north'
            self.app.table.show_hands(self.hands, visible=('S', 'N'))
            self.app.bidding_box.set_last_bid(bid)
            self._show_north_instruction(correct)
        else:
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(f'ההכרזה הנכונה\n{correct}', ok=False)

    # ─── stage 3: החלטת N ────────────────────────────────────────────────────

    def _show_north_instruction(self, ogust_bid):
        sym = _S[self._major]
        invite = _partscore_bid(self._major, ogust_bid)   # 3 בשליט או Pass
        decision_rows = [
            (invite,    '4 לקיחות גבוהות הזמנה'),
            (f'4{sym}', '5 לקיחות גבוהות'),
            ('4NT',     '6+ לקיחות גבוהות'),
        ]
        self._table(
            'מה תכריז',
            decision_rows
        )
        self.app.add_immediate_table([
            ('3♣',  '6-7 נקודות מפוזרות'),
            ('3♦',  '6-7 נקודות בסדרה המוכרזת'),
            ('3♥',  '8-9 נקודות מפוזרות'),
            ('3♠',  '8-9 נקודות מרוכזות בסדרה'),
            ('3NT', 'AKQ בסדרה'),
        ])

    def _handle_north(self, bid):
        correct = self._north_final(self._ogust_bid)
        sym     = _S[self._major]
        if bid == correct:
            if correct == '4NT':
                self._do_ace_ask()
                return
            self.app.auction_widget.add_bid(bid, highlight=True)  # N
            self.app.auction_widget.add_bid('Pass')               # E
            self.app.auction_widget.add_bid('Pass')               # S
            self.app.auction_widget.add_bid('Pass')               # W
            et = sure_tricks(self.hands['N'])
            self._finish(
                f'{self._next_opener()}\n'
                f'שותף ענה {self._ogust_bid}. {_EXPLAIN[self._ogust_bid]}\n'
                f'יש לך {tricks(et)}\n'
                f'ההכרזה הנכונה\n{bid}'
                + self._ogust_note(),
                ok=not self._ogust_wrong
            )
        else:
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                et = sure_tricks(self.hands['N'])
                self._finish(
                    f'שותף ענה {self._ogust_bid}. {_EXPLAIN[self._ogust_bid]}\n'
                    f'יש לך {tricks(et)}\n'
                    f'ההכרזה הנכונה\n{correct}'
                    + self._ogust_note(),
                    ok=False, correct_answer=correct
                )

    # ─── stage 4: שאלת אסים RKCB → סלם ───────────────────────────────────────

    def _do_ace_ask(self):
        """N הכריז 4NT. S (הפותח) עונה מפתחות RKCB בשליט, N יחליט 6M/5M."""
        sym = _S[self._major]
        self.app.auction_widget.add_bid('4NT', highlight=True)  # N
        self.app.auction_widget.add_bid('Pass')                 # E
        resp, s_kc, _ = rkcb_response(self.hands['S'], self._major)
        self._s_ace_response = resp
        self._total_kc = s_kc + key_cards(self.hands['N'], self._major)
        self.app.auction_widget.add_bid(resp)                   # S עונה מפתחות
        self.app.auction_widget.add_bid('Pass')                 # W
        self._stage = 'blackwood'
        self._tries = 0
        self._table(
            'מה תכריז',
            [
                (f'6{sym}', 'לא חסרים 2 מפתחות'),
                (f'5{sym}', 'חסרים 2 מפתחות'),
            ]
        )
        self.app.bidding_box.set_last_bid(resp)

    def _handle_blackwood(self, bid):
        sym     = _S[self._major]
        correct = f'6{sym}' if self._total_kc >= 4 else f'5{sym}'
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # N
            self.app.auction_widget.add_bid('Pass')               # E
            self.app.auction_widget.add_bid('Pass')               # S
            self.app.auction_widget.add_bid('Pass')               # W
            self._finish(
                f'{self._next_opener()}\n'
                f'שותף ענה {self._s_ace_response}\n'
                f'{self._total_kc} מפתחות משותפים\n'
                f'ההכרזה הנכונה\n{bid}'
                + self._ogust_note(),
                ok=not self._ogust_wrong
            )
        else:
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(
                    f'שותף ענה {self._s_ace_response}\n'
                    f'{self._total_kc} מפתחות משותפים\n'
                    f'ההכרזה הנכונה\n{correct}'
                    + self._ogust_note(),
                    ok=False, correct_answer=correct
                )

    def _ogust_note(self):
        if not self._ogust_wrong:
            return ''
        return f'\nגם באוגוסט טעית\nההכרזה הנכונה שם\n{self._ogust_correct}'

    # ─── helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _strong_suits(hand):
        """מונה סדרות עם 4+ קלפים ו-2+ מכובדים (A/K/Q)."""
        count = 0
        for suit in ['S', 'H', 'D', 'C']:
            if suit_len(hand, suit) >= 4:
                top = sum(1 for c in hand if c[1] == suit and c[0] in ('A', 'K', 'Q'))
                if top >= 2:
                    count += 1
        return count

    def _north_final(self, ogust_response):
        n   = self.hands['N']
        sym = _S[self._major]
        # המחלק מבטיח 2+ קלפים במיגור, אבל נשארים הגנתיים
        if suit_len(n, self._major) < 2:
            return f'3{sym}'
        # הכל לפי לקיחות גבוהות (sure_tricks): 4=הזמנה, 5=משחק, 6+=שאלת אסים
        st = sure_tricks(n)
        if st >= 6:
            return '4NT'
        if st >= 5:
            return f'4{sym}'
        # 4 לקיחות גבוהות → הזמנה: 3 בשליט, או Pass אם הפותח כבר שם
        return _partscore_bid(self._major, ogust_response)

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        rows = getattr(self, '_panel_rows', None)
        if rows:
            self.app.add_immediate_table(rows)
        self.app.show_all_hands()
        self.app.set_feedback(message, ok=ok, correct_answer=correct_answer)
        self.app.show_new_deal_button()
