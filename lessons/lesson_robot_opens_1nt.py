from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_1nt
from engine.response import respond_1nt
from engine.rebid import opener_rebid
from engine.scoring import hcp

_BIDS = ['Pass', '2NT', '3NT']


class LessonRobotOpens1NT(BaseLesson):
    """שיעור 2: מחשב (N) פותח 1NT, תלמיד (S) עונה"""

    TITLE = 'שיעור 2. מענה ל-1NT'
    _deal_count = 0
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonRobotOpens1NT
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def _correct_message(self, final):
        h = hcp(self.hands['S'])
        return (f'{self._next_opener()}\n'
                f'יש לך {h} נקודות גבוהות\n'
                f'ההכרזה הנכונה\n'
                f'{final}')

    def _wrong_message(self, correct):
        h = hcp(self.hands['S'])
        return f'יש לך {h} נקודות גבוהות\nההכרזה הנכונה\n{correct}'

    def start(self):
        if not self._replaying:
            LessonRobotOpens1NT._deal_count += 1
            self.hands = deal_robot_opens_1nt()
        self._replaying = False
        self._stage = 'respond'
        self._tries = 0
        self._awaiting_close = False

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid('1NT')   # N
        self.app.auction_widget.add_bid('Pass')  # E

        self.app.bidding_box.set_last_bid('1NT')
        if LessonRobotOpens1NT._deal_count <= 3:
            self.app.set_instruction_table(
                'מחשב פתח 1NT. מה תענה',
                [
                    ('פס',  '0-7 נקודות גבוהות'),
                    ('2NT', '8-9 נקודות גבוהות'),
                    ('3NT', '10+ נקודות גבוהות'),
                ]
            )

    def on_student_bid(self, bid):
        if self._handle_close(bid): return
        if self._stage == 'respond':
            self._handle_respond(bid)
        elif self._stage == 'rebid':
            self._handle_rebid(bid)

    # ── שלב 1: תלמיד עונה ─────────────────────────────────────────────────

    def _handle_respond(self, bid):
        correct, why = respond_1nt(self.hands['S'])

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W
            self._after_correct_response(bid, self._correct_message(bid), ok=True)
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
            self.app.bidding_box.set_last_bid('1NT')
            self.app.set_feedback('נסה שוב', ok=False)

    def _after_correct_response(self, bid, message, ok=True):
        if bid == 'Pass':
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self._finish(message, ok=ok)
        elif bid == '3NT':
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self._finish(message, ok=ok)
        elif bid == '2NT':
            north_bid, _ = opener_rebid(self.hands['N'], '1NT', '2NT')
            self.app.auction_widget.add_bid(north_bid)
            self.app.auction_widget.add_bid('Pass')
            if north_bid != 'Pass':
                self._start_closing(message, ok=ok)
            else:
                self._finish(message, ok=ok)
        else:
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self._finish(message, ok=False)

    # ── שלב 2: חזרה אחרי 2NT (לא בשימוש בבסיסי. N מכריז לבד) ───────────

    def _handle_rebid(self, bid):
        pass

    # ── סיום ───────────────────────────────────────────────────────────────

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
