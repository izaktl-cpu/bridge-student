import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_student_opens_major
from engine.response import respond_major
from engine.rebid import opener_rebid
from engine.scoring import hcp, distribution, dist_fit_pts
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


class LessonStudentOpensMajor(BaseLesson):
    """תלמיד (S) פותח מיגור עיקרי, מחשב (N) עונה"""

    TITLE = 'שיעור 3. פתיחת מיגור עיקרי'
    _deal_count = 0
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonStudentOpensMajor
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def _correct_message(self, final):
        h = hcp(self.hands['S'])
        return (f'{self._next_opener()}\n'
                f'יש לך {h} נקודות\n'
                f'ההכרזה הנכונה\n'
                f'{final}')

    def _explain_open_wrong(self, correct):
        h = hcp(self.hands['S'])
        return f'יש לך {h} נקודות\nההכרזה הנכונה\n{correct}'

    def start(self):
        if not self._replaying:
            LessonStudentOpensMajor._deal_count += 1
            self._major = random.choice(['H', 'S'])
            self.hands  = deal_student_opens_major(self._major)
        self._replaying = False
        self._stage = 'open'
        self._tries = 0

        sym = _S[self._major]
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('S')
        self.app.bidding_box.reset()

        if LessonStudentOpensMajor._deal_count <= 3:
            h = hcp(self.hands['S'])
            d = distribution(self.hands['S'])
            self.app.set_instruction(
                f'יש לך {h} נקודות גבוהות ו-{d[self._major]} קלפי {sym}.\n\n'
                f'עם 5+ קלפי {sym} ו-12-19 נקודות\n'
                f'פתח 1{sym}.')

    def on_student_bid(self, bid):
        if self._stage == 'open':
            self._handle_open(bid)
        elif self._stage == 'rebid':
            self._handle_rebid(bid)

    # ── שלב 1: תלמיד פותח ─────────────────────────────────────────────────

    def _handle_open(self, bid):
        sym = _S[self._major]
        correct = f'1{sym}'

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W

            north_bid, n_why = respond_major(self.hands['N'], self._major)
            self._north_bid = north_bid
            self.app.auction_widget.add_bid(north_bid)             # N
            self.app.auction_widget.add_bid('Pass')                # E

            if north_bid in (f'4{sym}', '3NT'):
                self._finish(self._correct_message(north_bid), ok=True)
            else:
                self._stage = 'rebid'
                self._tries = 0
                h_s     = hcp(self.hands['S'])
                is_raise = north_bid in (f'2{sym}', f'3{sym}', f'4{sym}')
                dp      = dist_fit_pts(self.hands['S'], trump=self._major, opener=True) if is_raise else 0
                tot     = h_s + dp
                self._rebid_pts = (h_s, dp, tot)
                dp_str = f'\nיש {h_s} נקודות גבוהות\nיש {dp} נקודות חוסר\nסה״כ {tot}' if dp > 0 else f'\nיש {h_s} נקודות גבוהות'
                self.app.bidding_box.set_last_bid(north_bid)
                self.app.set_instruction(f'{dp_str.lstrip(chr(10))}\n\nמה תכריז?')
        else:
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.bidding_box.reset()
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                self._finish(f'טעית בפעם השנייה.\n{self._explain_open_wrong(correct)}', ok=False)

    # ── שלב 2: תלמיד עושה חזרה ─────────────────────────────────────────────

    def _handle_rebid(self, bid):
        opening = f'1{_S[self._major]}'
        correct, why = opener_rebid(self.hands['S'], opening, self._north_bid)

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W
            self.app.auction_widget.add_bid('Pass')                # N
            self.app.auction_widget.add_bid('Pass')                # E
            final_contract = self._north_bid if bid == 'Pass' else bid
            self._finish(self._correct_message(final_contract), ok=True)
        else:
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.bidding_box.set_last_bid(self._north_bid)
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                self._finish(f'טעית בפעם השנייה.\n{self._explain_rebid_wrong(correct)}', ok=False)

    def _explain_rebid_wrong(self, correct):
        h_s, dp, tot = self._rebid_pts
        h = h_s + dp if dp > 0 else h_s
        return f'יש לך {h} נקודות\nההכרזה הנכונה\n{correct}'

    # ── סיום ───────────────────────────────────────────────────────────────

    def _finish(self, message, ok):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
