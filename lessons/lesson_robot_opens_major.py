import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_major
from engine.response import respond_major
from engine.rebid import opener_rebid
from engine.scoring import hcp
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


class LessonRobotOpensMajor(BaseLesson):
    """מחשב (N) פותח מיגור עיקרי, תלמיד (S) עונה"""

    _deal_count = 0
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonRobotOpensMajor
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def _correct_message(self, final):
        h = hcp(self.hands['S'])
        return (f'{self._next_opener()}\n'
                f'יש לך {h} נקודות\n'
                f'ההכרזה הנכונה\n'
                f'{final}')

    def _wrong_message(self, correct):
        h = hcp(self.hands['S'])
        return f'יש לך {h} נקודות\nההכרזה הנכונה\n{correct}'

    def start(self):
        if not self._replaying:
            LessonRobotOpensMajor._deal_count += 1
            self._major = random.choice(['H', 'S'])
            self.hands  = deal_robot_opens_major(self._major, support_scenario=True)
        self._replaying = False
        self._stage = 'respond'
        self._tries = 0
        self._awaiting_close = False

        sym = _S[self._major]
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid(f'1{sym}')  # N
        self.app.auction_widget.add_bid('Pass')      # E

        self.app.bidding_box.set_last_bid(f'1{sym}')

        if LessonRobotOpensMajor._deal_count <= 3:
            self.app.set_instruction_table(
                f'מחשב פתח 1{sym}.',
                [
                    ('0-5',   '',            'פס'),
                    ('6-9',   f'3+ קלפי{sym}', f'2{sym}'),
                    ('10-11', f'3+ קלפי{sym}', f'3{sym}'),
                    ('12+',   f'3+ קלפי{sym}', f'4{sym}'),
                ]
            )

    def on_student_bid(self, bid):
        if self._handle_close(bid): return
        if self._stage == 'respond':
            self._handle_respond(bid)

    def _handle_respond(self, bid):
        sym = _S[self._major]
        correct, why = respond_major(self.hands['S'], self._major)

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W

            opening = f'1{sym}'
            n_rebid, n_why = opener_rebid(self.hands['N'], opening, bid)

            message = self._correct_message(bid)
            if n_rebid == 'Pass':
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(message, ok=True)
            else:
                self.app.auction_widget.add_bid(n_rebid)
                self.app.auction_widget.add_bid('Pass')
                self._start_closing(message, ok=True)
        else:
            if self._tries >= 1:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(f'{self._wrong_message(correct)}', ok=False)
                return
            self._tries += 1
            self._last_wrong_bid = bid
            self.app.bidding_box.reset()
            self.app.bidding_box.set_last_bid(f'1{sym}')
            self.app.set_feedback('נסה שוב', ok=False)

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
