from lessons.base import BaseLesson
from engine.deal_constraints import deal_student_opens_1nt
from engine.response import respond_1nt
from engine.rebid import opener_rebid
from engine.scoring import hcp

_OPENING_BIDS = ['Pass', '1NT', '2NT', '3NT']


class LessonNTOpen(BaseLesson):
    """שיעור: תלמיד פותח 1NT, מחשב עונה, תלמיד ממשיך"""

    TITLE = 'שיעור 1. פתיחת 1NT'
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonNTOpen
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
            self.hands = deal_student_opens_1nt()
        self._replaying = False
        self._stage = 'open'
        self._tries = 0

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('S')
        self.app.set_instruction('ספור את הנקודות שלך\nיד מאוזנת\nמה תפתח')

    def on_student_bid(self, bid):
        if self._stage == 'open':
            self._handle_open(bid)
        elif self._stage == 'rebid':
            self._handle_rebid(bid)

    # ── שלב 1: תלמיד פותח ─────────────────────────────────────────────────

    def _handle_open(self, bid):
        if bid == '1NT':
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W

            north_bid, explanation = respond_1nt(self.hands['N'])
            self.app.auction_widget.add_bid(north_bid)             # N
            self.app.auction_widget.add_bid('Pass')                # E

            if north_bid == 'Pass':
                self.app.auction_widget.add_bid('Pass')            # S
                self.app.auction_widget.add_bid('Pass')            # W
                self._finish(self._correct_message('1NT'), ok=True)
            elif north_bid == '2NT':
                self._stage = 'rebid'
                self._tries = 0
                self.app.set_instruction_table(
                    'צפון הזמין 2NT. מה תכריז',
                    [
                        ('פס', '15 נקודות'),
                        ('3NT', '16-17 נקודות'),
                    ]
                )
                self.app.bidding_box.set_last_bid('2NT')
            else:  # 3NT
                self.app.auction_widget.add_bid('Pass')            # S
                self.app.auction_widget.add_bid('Pass')            # W
                self._finish(self._correct_message('3NT'), ok=True)
        else:
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.bidding_box.reset()
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                self._finish(f'{self._wrong_message("1NT")}', ok=False)

    # ── שלב 2: תלמיד מגיב אחרי 2NT ────────────────────────────────────────

    def _handle_rebid(self, bid):
        correct, why = opener_rebid(self.hands['S'], '1NT', '2NT')

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W
            self.app.auction_widget.add_bid('Pass')                # N
            self.app.auction_widget.add_bid('Pass')                # E
            final = bid if bid != 'Pass' else '2NT'
            self._finish(self._correct_message(final), ok=True)
        else:
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.bidding_box.reset()
                self.app.bidding_box.set_last_bid('2NT')
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                self._finish(f'{self._wrong_message(correct)}', ok=False)

    # ── סיום ───────────────────────────────────────────────────────────────

    def _finish(self, message, ok):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.table.show_hands(self.hands, visible=('N', 'E', 'S', 'W'))
        self.app.show_new_deal_button()
