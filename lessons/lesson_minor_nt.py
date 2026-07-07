import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_minor_nt
from engine.response import (respond_minor_nt, opener_rebid_after_3minor,
                              responder_stopper_reply, opener_after_stopper_denial)
from engine.scoring import hcp
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS
_BID_TO_SUIT = {'♥': 'H', '♠': 'S', '♣': 'C', '♦': 'D'}


class LessonMinorNT(BaseLesson):
    """N פותח 1♦, S מראה 5+ קלפי ♦ עם 11+ (3♦).
    N<14: לא בטוח ב-25+ משותפות, Pass. N>=14: שואל עוצר, S עונה."""

    TITLE = 'שיעור 15. NT במינור'
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonMinorNT
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def __init__(self, app):
        super().__init__(app)
        self._stage    = None
        self._ask_suit = None
        self._minor    = 'D'

    def start(self):
        if not self._replaying:
            self._minor = random.choice(['C', 'D'])
            self.hands = deal_minor_nt(self._minor)
        self._replaying = False
        self._stage    = 'respond'
        self._tries    = 0
        self._ask_suit = None

        sym = _S[self._minor]
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid(f'1{sym}')
        self.app.auction_widget.add_bid('Pass')

        self.app.bidding_box.set_last_bid(f'1{sym}')
        self._set_instruction()

    def _set_instruction(self):
        sym = _S[self._minor]
        self.app.set_instruction_table(
            'מה תכריז?',
            [
                (f'3{sym}', f'11+ נקודות, 5+ קלפי {sym}'),
            ]
        )

    def _set_ask_instruction(self, n_bid):
        ask_suit = next((su for ch, su in _BID_TO_SUIT.items() if ch in n_bid), None)
        ask_sym  = _S[ask_suit] if ask_suit else n_bid
        sym      = _S[self._minor]
        self.app.set_instruction_table(
            'מה תכריז?',
            [
                ('3NT',    f'יש לי עוצר ב-{ask_sym}'),
                (f'4{sym}', f'אין לי עוצר ב-{ask_sym}'),
            ]
        )

    def on_student_bid(self, bid):
        if self._stage == 'respond':
            self._handle_respond(bid)
        elif self._stage == 'ask':
            self._handle_ask(bid)

    def _handle_respond(self, bid):
        correct, _ = respond_minor_nt(self.hands['S'], self._minor)
        if bid != correct:
            self._tries += 1
            if self._tries >= 2:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(f'ההכרזה הנכונה\n{correct}', ok=False)
                return
            sym = _S[self._minor]
            self.app.bidding_box.reset()
            self.app.bidding_box.set_last_bid(f'1{sym}')
            self.app.set_feedback('נסה שוב', ok=False)
            return

        self.app.auction_widget.add_bid(bid, highlight=True)
        self.app.auction_widget.add_bid('Pass')

        # N שואל עוצר
        n_bid, _ = opener_rebid_after_3minor(self.hands['N'], self._minor)
        self.app.auction_widget.add_bid(n_bid)
        self.app.auction_widget.add_bid('Pass')

        if n_bid == '3NT':
            self._finish(f'{self._next_opener()}\nחוזה סופי\n3NT', ok=True)
            return

        if n_bid == 'Pass':
            self._finish(f'{self._next_opener()}\nחוזה סופי\n{bid}', ok=True)
            return

        # N שואל — שלב שני לתלמיד
        ask_suit = next((su for ch, su in _BID_TO_SUIT.items() if ch in n_bid), None)
        self._ask_suit = ask_suit
        self._stage    = 'ask'
        self._tries    = 0
        self.app.bidding_box.reset()
        self.app.bidding_box.set_last_bid(n_bid)
        self._set_ask_instruction(n_bid)

    def _handle_ask(self, bid):
        correct, _ = responder_stopper_reply(self.hands['S'], self._minor, self._ask_suit)
        if bid != correct:
            self._tries += 1
            if self._tries >= 2:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(f'ההכרזה הנכונה\n{correct}', ok=False)
                return
            self.app.bidding_box.reset()
            self.app.bidding_box.set_last_bid(
                next((f'3{_S[su]}' for su in [self._ask_suit]), '3NT'))
            self.app.set_feedback('נסה שוב', ok=False)
            return

        self.app.auction_widget.add_bid(bid, highlight=True)

        if bid == '3NT':
            self._finish(f'{self._next_opener()}\nיש לך עוצר\nחוזה סופי\n3NT', ok=True)
            return

        # bid == 4m (אין עוצר) — N מחליט אם מרים ל-5m לפי הנקודות שלו
        self.app.auction_widget.add_bid('Pass')  # W
        n_bid, _ = opener_after_stopper_denial(self.hands['N'], self._minor)
        self.app.auction_widget.add_bid(n_bid)
        final = n_bid if n_bid != 'Pass' else bid
        self._finish(f'{self._next_opener()}\nחוזה סופי\n{final}', ok=True)

    def _finish(self, message, ok):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
