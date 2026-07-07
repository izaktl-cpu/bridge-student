import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_1nt_stayman, deal_robot_opens_1nt_transfer
from engine.rebid import opener_rebid
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_retry, msg_correct_final

_S = SUIT_SYMBOLS


class LessonStaymanTransfer(BaseLesson):
    """שיעור 5: סטיימן וטרנספר לאחר פתיחת 1NT של המחשב"""

    TITLE = 'שיעור 5. סטיימן וטרנספר'

    def start(self):
        # חלק אקראי: סטיימן או טרנספר
        self._mode = random.choice(['stayman', 'transfer'])
        if self._mode == 'stayman':
            self.hands = deal_robot_opens_1nt_stayman()
        else:
            self.hands = deal_robot_opens_1nt_transfer()

        self._stage = 'respond'
        self._tries = 0

        self.app.table.show_hands(self.hands, visible=('N', 'E', 'S', 'W'))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid('1NT')
        self.app.auction_widget.add_bid('Pass')

        self.app.bidding_box.set_last_bid('1NT')

    def on_student_bid(self, bid):
        if self._stage == 'respond':
            self._handle_respond(bid)
        elif self._stage == 'stayman_cont':
            self._handle_stayman_cont(bid)
        elif self._stage == 'transfer_cont':
            self._handle_transfer_cont(bid)

    # ── שלב 1: תגובה ראשונית ──────────────────────────────────────────────

    def _handle_respond(self, bid):
        correct, why = self._calc_correct_first_bid()

        if bid == correct:
            self.app.auction_widget.add_bid('Pass')    # W
            self.app.auction_widget.add_bid(bid, highlight=True)
            self._execute_first_bid(bid, why)
        else:
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(f'ההכרזה הנכונה\n{correct}', ok=False)

    def _calc_correct_first_bid(self):
        h = hcp(self.hands['S'])
        d = distribution(self.hands['S'])

        # טרנספר: 5+ מיגור עיקרי (כל ניקוד)
        if d['H'] >= 5:
            return '2♦', f'יש {h} נקודות גבוהות, {d["H"]} קלפי ♥, טרנספר ל-♥'
        if d['S'] >= 5:
            return '2♥', f'יש {h} נקודות גבוהות, {d["S"]} קלפי ♠, טרנספר ל-♠'

        # סטיימן: 2 רביעיות (אחת לפחות מיגור) + 8+ נקודות
        has_major_4 = d['H'] == 4 or d['S'] == 4
        four_count = sum([d['S'] == 4, d['H'] == 4, d['D'] >= 4, d['C'] >= 4])
        if h >= 8 and has_major_4 and four_count >= 2:
            return '2♣', f'יש {h} נקודות גבוהות, 2 רביעיות עם מיגור, סטיימן 2♣'

        # בסיסי
        if h <= 7:
            return 'Pass', f'יש {h} נקודות גבוהות, מכריזים פס'
        if h <= 9:
            return '2NT', f'יש {h} נקודות גבוהות, מזמינים ל-3NT'
        return '3NT', f'יש {h} נקודות גבוהות, מכריזים משחק מלא'

    def _execute_first_bid(self, bid, why):
        if bid == 'Pass':
            self._finish('חוזה סופי\n1NT', ok=True)
        elif bid == '2NT':
            north_bid, n_why = opener_rebid(self.hands['N'], '1NT', '2NT')
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid(north_bid)
            self._finish(f'מחשב ענה {north_bid}. {n_why}\nחוזה סופי\n{north_bid}', ok=True)
        elif bid == '3NT':
            self.app.auction_widget.add_bid('Pass')
            self._finish('חוזה סופי\n3NT', ok=True)
        elif bid == '2♣':
            self._do_stayman(why)
        elif bid == '2♦':
            self._do_transfer_heart(why)
        elif bid == '2♥':
            self._do_transfer_spade(why)

    # ── סטיימן ────────────────────────────────────────────────────────────

    def _do_stayman(self, why):
        d_n = distribution(self.hands['N'])
        if d_n['S'] >= 4 and d_n['H'] >= 4:
            self._stayman_reply = '2♥'          # ♥ קודם כשיש שניהם
        elif d_n['H'] >= 4:
            self._stayman_reply = '2♥'
        elif d_n['S'] >= 4:
            self._stayman_reply = '2♠'
        else:
            self._stayman_reply = '2♦'          # אין מיגור עיקרי

        self._stayman_why = why
        self.app.auction_widget.add_bid('Pass')
        self.app.auction_widget.add_bid(self._stayman_reply)
        self.app.auction_widget.add_bid('Pass')

        self._stage = 'stayman_cont'
        self._tries = 0
        bids = self._stayman_cont_options()
        h = hcp(self.hands['S'])
        d = distribution(self.hands['S'])
        r = self._stayman_reply
        reply_text = {
            '2♦': 'אין מיגור עיקרי',
            '2♥': 'יש לו ♥ (לא שולל ♠)',
            '2♠': 'יש לו ♠, אין ♥',
        }[r]
        fit = self._has_fit()
        fit_suit = self._fit_suit()
        if fit:
            hint = f'יש התאמה ב-{fit_suit}.\n8-9 נקודות → 3{fit_suit}  |  10+ נקודות → 4{fit_suit}'
        else:
            hint = f'אין התאמה במיגור.\n8-9 נקודות → 2NT  |  10+ נקודות → 3NT'
        self.app.set_instruction(
            f'מחשב ענה {r} ({reply_text}).\n{hint}')
        self.app.bidding_box.set_last_bid(self._stayman_reply)

    def _has_fit(self):
        d = distribution(self.hands['S'])
        r = self._stayman_reply
        if r == '2♥' and d['H'] >= 4:
            return True
        if r == '2♠' and d['S'] >= 4:
            return True
        return False

    def _fit_suit(self):
        r = self._stayman_reply
        return '♥' if r == '2♥' else '♠'

    def _stayman_cont_options(self):
        h = hcp(self.hands['S'])
        r = self._stayman_reply

        if self._has_fit():
            suit = self._fit_suit()
            return [f'3{suit}', f'4{suit}']
        return ['2NT', '3NT']

    def _handle_stayman_cont(self, bid):
        correct = self._calc_stayman_cont()
        h = hcp(self.hands['S'])
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self._finish(f'חוזה סופי\n{bid}', ok=True)
        else:
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(f'ההכרזה הנכונה\n{correct}', ok=False)

    def _calc_stayman_cont(self):
        h = hcp(self.hands['S'])
        if self._has_fit():
            suit = self._fit_suit()
            return f'4{suit}' if h >= 10 else f'3{suit}'
        return '3NT' if h >= 10 else '2NT'

    # ── טרנספר ────────────────────────────────────────────────────────────

    def _do_transfer_heart(self, why):
        """2♦ → מחשב כופה 2♥"""
        self._transfer_sym = '♥'
        self._transfer_why = why
        self.app.auction_widget.add_bid('Pass')
        self.app.auction_widget.add_bid('2♥')       # מחשב מסיים טרנספר
        self.app.auction_widget.add_bid('Pass')

        self._stage = 'transfer_cont'
        self._tries = 0
        bids = self._transfer_cont_options()
        h = hcp(self.hands['S'])
        d = distribution(self.hands['S'])
        self.app.set_instruction(
            f'מחשב ענה 2♥. טרנספר הושלם. '
            f'ל-S יש {d["H"]} קלפי ♥ ו-{h} נקודות. מה תכריז?')
        self.app.bidding_box.set_last_bid('2♥')

    def _do_transfer_spade(self, why):
        """2♥ → מחשב כופה 2♠"""
        self._transfer_sym = '♠'
        self._transfer_why = why
        self.app.auction_widget.add_bid('Pass')
        self.app.auction_widget.add_bid('2♠')       # מחשב מסיים טרנספר
        self.app.auction_widget.add_bid('Pass')

        self._stage = 'transfer_cont'
        self._tries = 0
        bids = self._transfer_cont_options()
        h = hcp(self.hands['S'])
        d = distribution(self.hands['S'])
        self.app.set_instruction(
            f'מחשב ענה 2♠. טרנספר הושלם. '
            f'ל-S יש {d["S"]} קלפי ♠ ו-{h} נקודות. מה תכריז?')
        self.app.bidding_box.set_last_bid('2♠')

    def _transfer_cont_options(self):
        h = hcp(self.hands['S'])
        sym = self._transfer_sym
        if h <= 7:
            return ['Pass']
        if h <= 9:
            return [f'3{sym}', 'Pass']
        return [f'4{sym}', '3NT']

    def _handle_transfer_cont(self, bid):
        correct = self._calc_transfer_cont()
        h = hcp(self.hands['S'])
        sym = self._transfer_sym

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            final_contract = f'2{self._transfer_sym}' if bid == 'Pass' else bid
            self._finish(f'חוזה סופי\n{final_contract}', ok=True)
        else:
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(f'ההכרזה הנכונה\n{correct}', ok=False)

    def _calc_transfer_cont(self):
        h = hcp(self.hands['S'])
        sym = self._transfer_sym
        if h <= 7:
            return 'Pass'
        if h <= 9:
            return f'3{sym}'
        return f'4{sym}'

    # ── סיום ───────────────────────────────────────────────────────────────

    def _finish(self, message, ok):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_new_deal_button()
