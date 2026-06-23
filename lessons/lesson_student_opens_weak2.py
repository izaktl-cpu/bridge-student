import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_student_weak2
from engine.scoring import sure_tricks, suit_len, has_stopper, hcp
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_retry, msg_chose_wrong

_S = SUIT_SYMBOLS


def _n_response(n_hand, major):
    """מחשב את תגובת N לפתיחת Weak Two של S."""
    sym         = _S[major]
    st          = sure_tricks(n_hand)
    fit         = suit_len(n_hand, major) >= 2
    other       = [x for x in ['S', 'H', 'D', 'C'] if x != major]
    stops       = all(has_stopper(n_hand, suit) for suit in other)
    other_major = 'H' if major == 'S' else 'S'
    long_other  = suit_len(n_hand, other_major) >= 6

    if st >= 4 and fit:
        return f'4{sym}'
    if st >= 4 and long_other:
        return f'4{_S[other_major]}'
    if st >= 4 and stops and suit_len(n_hand, major) >= 1:
        return '3NT'
    if st == 4 and fit:
        return f'3{sym}'
    return 'Pass'


class LessonStudentOpensWeak2(BaseLesson):
    """שיעור 10: תלמיד (S) פותח Weak Two (2♥/2♠), מחשב (N) עונה"""

    TITLE = 'שיעור 10. Weak Two (אני פותח)'

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
            f'יש לך 6 קלפי {sym} ו-{hcp(self.hands["S"])} נקודות ({pos_str}). פתח!',
            [
                (f'2{sym}', '6 קלפים + 6–9 נקודות. Weak Two'),
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
            pos_note = f'\n(יד {pos} — כללים מקלים)' if pos == 3 else f'\n(יד {pos})'
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')  # W
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(msg_chose_wrong(bid, correct) + pos_note, ok=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')  # W
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(msg_chose_wrong(bid, correct) + pos_note, ok=False, correct_answer=correct)

    def _result_message(self, n_bid):
        n           = self.hands['N']
        sym         = _S[self._major]
        other_major = 'H' if self._major == 'S' else 'S'
        other_sym   = _S[other_major]
        st          = sure_tricks(n)
        fit         = suit_len(n, self._major)
        other_len   = suit_len(n, other_major)

        if n_bid == f'4{sym}':
            return f'✓ מחשב קפץ ל-{n_bid}!\nיש {st} לקיחות גבוהות\nיש {fit} קלפי {sym}.'
        if n_bid == f'4{other_sym}':
            return f'✓ מחשב הכריז {n_bid}.\nיש {other_len} קלפי {other_sym} + {st} לקיחות גבוהות.'
        if n_bid == '3NT':
            return f'✓ מחשב הכריז 3NT.\nיש {st} לקיחות גבוהות + עוצרים בכל הסדרות.'
        if n_bid == f'3{sym}':
            return f'✓ מחשב הפריע ל-3{sym}.\nיש 4 לקיחות גבוהות + {fit} קלפי {sym}.'
        return f'✓ מחשב פס.\nרק {st} לקיחות גבוהות. לא מספיק להמשך.'

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.show_all_hands()
        self.app.set_feedback(message, ok=ok, correct_answer=correct_answer)
        self.app.show_new_deal_button()
