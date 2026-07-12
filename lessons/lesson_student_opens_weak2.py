import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_student_weak2
from engine.scoring import sure_tricks, suit_len, has_stopper, hcp
from engine.cards import SUIT_SYMBOLS
from utils.messages import high_tricks, cards_of

_S = SUIT_SYMBOLS


def _n_response(n_hand, major):
    """מחשב את תגובת N לפתיחת Weak Two של S."""
    sym         = _S[major]
    st          = sure_tricks(n_hand)
    fit         = suit_len(n_hand, major) >= 2
    other       = [x for x in ['S', 'H', 'D', 'C'] if x != major]
    stops       = all(has_stopper(n_hand, suit) for suit in other)

    if fit and st >= 5:
        return f'4{sym}'
    if fit and st == 4:
        return f'3{sym}'          # הזמנה
    if st >= 4 and stops and suit_len(n_hand, major) >= 1:
        return '3NT'
    return 'Pass'


class LessonStudentOpensWeak2(BaseLesson):
    """שיעור 10: תלמיד (S) פותח Weak Two (2♥/2♠), מחשב (N) עונה"""

    TITLE = 'שיעור 10. Weak Two (אני פותח)'
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonStudentOpensWeak2
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def _wrong_message(self, correct):
        return f'ההכרזה הנכונה\n{correct}'

    def start(self):
        if not self._replaying:
            self._major = random.choice(['H', 'S'])
            self.hands  = deal_student_weak2(self._major)
        self._replaying = False
        self._tries     = 0
        self._stage     = 'open'

        sym = _S[self._major]
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('S')

        pos = self.hands.get('position', 1)
        pos_str = f'יד {pos}'
        self.app.bidding_box.set_last_bid(None)
        self.app.set_instruction_table(
            f'יש לך 6 קלפי {sym} ו-{hcp(self.hands["S"])} נקודות. {pos_str}. פתח',
            [
                (f'2{sym}', '6 קלפים + 6-9 נקודות. Weak Two'),
            ]
        )

    def on_student_bid(self, bid):
        if self._stage == 'open':
            self._handle_open(bid)

    def _handle_open(self, bid):
        sym     = _S[self._major]
        correct = f'2{sym}'
        pos     = self.hands.get('position', 1)

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            n_bid = _n_response(self.hands['N'], self._major)
            self.app.auction_widget.add_bid(n_bid)                # N
            self.app.auction_widget.add_bid('Pass')               # E
            self.app.auction_widget.add_bid('Pass')               # S
            self.app.auction_widget.add_bid('Pass')               # W
            self._finish(self._result_message(n_bid), ok=True)
        else:
            pos_note = f'\nיד {pos}, כללים מקלים' if pos == 3 else f'\nיד {pos}'
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')  # W
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(f'{self._wrong_message(correct)}{pos_note}', ok=False, correct_answer=correct)

    def _result_message(self, n_bid):
        n           = self.hands['N']
        sym         = _S[self._major]
        st          = sure_tricks(n)
        fit         = suit_len(n, self._major)

        opener = self._next_opener()
        if n_bid == f'4{sym}':
            return f'{opener}\nמחשב קפץ ל-{n_bid}\nיש {high_tricks(st)}\nיש {cards_of(fit, sym)}'
        if n_bid == '3NT':
            return f'{opener}\nמחשב הכריז 3NT\nיש {high_tricks(st)} + עוצרים בכל הסדרות'
        if n_bid == f'3{sym}':
            return f'{opener}\nמחשב הפריע ל-3{sym}\nיש 4 לקיחות גבוהות + {cards_of(fit, sym)}'
        return f'{opener}\nמחשב פס\nרק {high_tricks(st)}'

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.show_all_hands()
        self.app.set_feedback(message, ok=ok, correct_answer=correct_answer)
        self.app.show_new_deal_button()
