import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_ogust
from engine.scoring import hcp, sure_tricks, suit_len
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_retry

_S = SUIT_SYMBOLS

_EXPLAIN = {
    '3♣':  '6–7 נקודות. מפוזרות',
    '3♦':  '6–7 נקודות. מרוכזות בסדרה',
    '3♥':  '8–9 נקודות. מפוזרות',
    '3♠':  '8–9 נקודות. מרוכזות בסדרה',
    '3NT': 'AKQ בסדרה',
}


def _calc_ogust(hand, major):
    h      = hcp(hand)
    honors = sum(1 for c in hand if c[1] == major and c[0] in ('A', 'K', 'Q'))
    if honors == 3:
        return '3NT'
    concentrated = honors >= 2
    if h <= 7:
        return '3♦' if concentrated else '3♣'
    else:
        return '3♠' if concentrated else '3♥'


class LessonOgust(BaseLesson):
    """שיעור 11: S פותח Weak Two, מחשב שואל 2NT, S עונה אוגוסט, N מסכם"""

    TITLE = 'שיעור 11. Ogust'

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
        self.app.set_instruction_table(
            f'יש לך 6 קלפי {sym} ו-{h} נקודות. פתח!',
            [
                (f'2{sym}', f'6 קלפים + 6–9 נקודות. Weak Two'),
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
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(f'הנכון: {correct}.', ok=False, correct_answer=correct)

    def _show_respond_instruction(self):
        sym = _S[self._major]
        self.app.set_instruction_table(
            f'פתחת 2{sym}\nמחשב שואל 2NT\nמה תענה?',
            [
                ('3♣',  "6-7 נק׳, מפוזרות"),
                ('3♦',  "6-7 נק׳, מרוכזות"),
                ('3♥',  "8-9 נק׳, מפוזרות"),
                ('3♠',  "8-9 נק׳, מרוכזות"),
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
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                # מקבל את הכרזת התלמיד, שומר שגיאה לסוף
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self._tries = 0
                self._ogust_bid     = bid
                self._ogust_wrong   = True
                self._ogust_correct = correct
                self._stage = 'north'
                self.app.table.show_hands(self.hands, visible=('S', 'N'))
                self.app.bidding_box.set_last_bid(bid)
                self._show_north_instruction(bid)

    # ─── stage 3: החלטת N ────────────────────────────────────────────────────

    def _show_north_instruction(self, ogust_bid):
        sym = _S[self._major]
        hn  = hcp(self.hands['N'])
        if ogust_bid == '3♣':
            decision_rows = [
                (f'3{sym}', 'פחות מ-7 לקיחות'),
                (f'4{sym}', '7+ לקיחות'),
            ]
        elif ogust_bid in ('3♦', '3♥'):
            decision_rows = [
                (f'3{sym}', 'פחות מ-5 לקיחות'),
                (f'4{sym}', '5+ לקיחות'),
            ]
        else:  # 3♠, 3NT
            decision_rows = [
                (f'3{sym}', 'פחות מ-4 לקיחות'),
                (f'4{sym}', '4–5 לקיחות'),
                (f'6{sym}', '6+ לקיחות'),
            ]
        self.app.set_instruction_table(
            f'יש לך {hn} נקודות. מה תכריז?',
            decision_rows
        )
        self.app.add_immediate_table([
            ('3♣',  '6-7 נק׳, מפוזרות'),
            ('3♦',  '6-7 נק׳, מרוכזות'),
            ('3♥',  '8-9 נק׳, מפוזרות'),
            ('3♠',  '8-9 נק׳, מרוכזות'),
            ('3NT', 'AKQ בסדרה'),
        ])

    def _handle_north(self, bid):
        correct = self._north_final(self._ogust_bid)
        sym     = _S[self._major]
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # N
            self.app.auction_widget.add_bid('Pass')               # E
            self.app.auction_widget.add_bid('Pass')               # S
            self.app.auction_widget.add_bid('Pass')               # W
            et = self._effective_tricks(self._ogust_bid)
            self._finish(
                f'✓ נכון! {bid}.\n'
                f'שותף ענה {self._ogust_bid} — {_EXPLAIN[self._ogust_bid]}\n'
                f'יש לך {et} לקיחות.'
                + self._ogust_note(),
                ok=True
            )
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                et = self._effective_tricks(self._ogust_bid)
                self._finish(
                    f'הנכון: {correct}.\n'
                    f'שותף ענה {self._ogust_bid} — {_EXPLAIN[self._ogust_bid]}\n'
                    f'יש לך {et} לקיחות.'
                    + self._ogust_note(),
                    ok=False
                )
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                et = self._effective_tricks(self._ogust_bid)
                self._finish(
                    f'הנכון: {correct}.\n'
                    f'שותף ענה {self._ogust_bid} — {_EXPLAIN[self._ogust_bid]}\n'
                    f'יש לך {et} לקיחות.'
                    + self._ogust_note(),
                    ok=False, correct_answer=correct
                )

    def _ogust_note(self):
        if not self._ogust_wrong:
            return ''
        return f'\nגם באוגוסט טעית — הנכון: {self._ogust_correct}.'

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

    def _effective_tricks(self, ogust_response):
        """לקיחות אפקטיביות: בסדרת הפותח כל AKQJ=1; בשאר — רצף עליון בלבד."""
        n = self.hands['N']
        total = sum(1 for c in n if c[1] == self._major and c[0] in ('A', 'K', 'Q', 'J'))
        for suit in ['S', 'H', 'D', 'C']:
            if suit != self._major:
                total += self._suit_tricks(n, suit)
        return total

    @staticmethod
    def _suit_tricks(hand, suit):
        """רצף עליון: AKQ=3, KQJ=2, AQ=1, KQ=1 וכו'."""
        order = ['A', 'K', 'Q', 'J']
        top_idx = None
        for i, r in enumerate(order):
            if any(c[0] == r and c[1] == suit for c in hand):
                top_idx = i
                break
        if top_idx is None:
            return 0
        seq = 0
        for r in order[top_idx:]:
            if any(c[0] == r and c[1] == suit for c in hand):
                seq += 1
            else:
                break
        return max(0, seq - top_idx)

    def _north_final(self, ogust_response):
        n   = self.hands['N']
        sym = _S[self._major]
        et  = self._effective_tricks(ogust_response)
        fit = suit_len(n, self._major) >= 2 or self._strong_suits(n) >= 2

        if not fit:
            return f'3{sym}'
        if ogust_response == '3♣':
            return f'4{sym}' if et >= 7 else f'3{sym}'
        elif ogust_response == '3♦':
            return f'4{sym}' if et >= 5 else f'3{sym}'
        elif ogust_response == '3♥':
            return f'4{sym}' if et >= 5 else f'3{sym}'
        else:  # 3♠, 3NT
            if et >= 6:
                return f'6{sym}'
            elif et >= 4:
                return f'4{sym}'
            else:
                return f'3{sym}'

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.show_all_hands()
        self.app.set_feedback(message, ok=ok, correct_answer=correct_answer)
        self.app.show_new_deal_button()
