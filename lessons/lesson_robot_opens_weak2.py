import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_weak_two
from engine.scoring import sure_tricks, suit_len, has_stopper
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_retry

_S = SUIT_SYMBOLS


class LessonRobotOpensWeak2(BaseLesson):
    """שיעור 10: מחשב (N) פותח Weak Two (2♥/2♠), תלמיד (S) עונה"""

    TITLE = 'שיעור 10. Weak Two'

    def start(self):
        if not self._replaying:
            self._major = random.choice(['H', 'S'])
            self.hands  = deal_weak_two(self._major)
        self._replaying = False
        self._tries     = 0
        self._stage     = 'respond'

        sym = _S[self._major]
        pos = self.hands.get('position', 1)
        pos_str = f'יד {pos}'
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid(f'2{sym}')  # N
        self.app.auction_widget.add_bid('Pass')      # E

        self.app.bidding_box.set_last_bid(f'2{sym}')
        other_sym = _S['H' if self._major == 'S' else 'S']
        self.app.set_instruction_table(
            f'מחשב פתח 2{sym} ({pos_str}). מה תכריז?',
            [
                ('Pass',         '0-2 לקיחות'),
                (f'3{sym}',      f'תמיכה ב-{sym}, 3 לקיחות'),
                (f'4{sym}',      f'תמיכה ב-{sym}, 4+ לקיחות'),
                (f'4{other_sym}', f'6+ קלפי {other_sym}, 4+ לקיחות'),
                ('3NT',          'עצור בכל הסדרות + קלף בסדרת שותף'),
            ]
        )

    def on_student_bid(self, bid):
        if self._stage == 'respond':
            self._handle_respond(bid)

    def _handle_respond(self, bid):
        correct = self._calc_response()
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            self.app.auction_widget.add_bid('Pass')               # N
            self.app.auction_widget.add_bid('Pass')               # E
            self._finish(self._ok_message(correct), ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')  # W
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(self._ok_message(bid), ok=False)
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
                self._finish(
                    f'הנכון: {correct}.\n{self._why(correct)}\n\n{self._ok_message(bid)}',
                    ok=False, correct_answer=correct)

    def _calc_response(self):
        s   = self.hands['S']
        sym = _S[self._major]
        st  = sure_tricks(s)
        fit = suit_len(s, self._major) >= 2
        other = [x for x in ['S', 'H', 'D', 'C'] if x != self._major]
        stops = all(has_stopper(s, suit) for suit in other)
        other_major = 'H' if self._major == 'S' else 'S'
        long_other  = suit_len(s, other_major) >= 6

        if st >= 4 and fit:
            return f'4{sym}'
        if st >= 4 and long_other:
            return f'4{_S[other_major]}'
        if st >= 4 and stops and suit_len(s, self._major) >= 1:
            return '3NT'
        if st == 3 and fit:
            return f'3{sym}'
        return 'Pass'

    def _ok_message(self, correct):
        s           = self.hands['S']
        sym         = _S[self._major]
        other_major = 'H' if self._major == 'S' else 'S'
        other_sym   = _S[other_major]
        st          = sure_tricks(s)
        fit         = suit_len(s, self._major)
        other_len   = suit_len(s, other_major)
        if correct == f'4{sym}':
            return f'✓ נכון! משחק מלא.\nיש {st} לקיחות גבוהות\nיש {fit} קלפי {sym}.'
        if correct == f'4{other_sym}':
            return f'✓ נכון! {other_len} קלפי {other_sym} + {st} לקיחות גבוהות → {correct}.'
        if correct == '3NT':
            return f'✓ נכון! 3NT.\nיש {st} לקיחות גבוהות + עוצרים בכל הסדרות.'
        if correct == f'3{sym}':
            return f'✓ נכון! הפרעה.\nיש 4 לקיחות גבוהות + {fit} קלפי {sym}.'
        return f'✓ נכון! פס.\nרק {st} לקיחות גבוהות. לא מספיק.'

    def _why(self, correct):
        s           = self.hands['S']
        sym         = _S[self._major]
        other_major = 'H' if self._major == 'S' else 'S'
        other_sym   = _S[other_major]
        st          = sure_tricks(s)
        fit         = suit_len(s, self._major)
        other_len   = suit_len(s, other_major)
        if correct == f'4{sym}':
            return f'יש {st} לקיחות גבוהות ו-{fit} קלפי {sym} → משחק מלא.'
        if correct == f'4{other_sym}':
            return f'יש {other_len} קלפי {other_sym} + {st} לקיחות → {correct}.'
        if correct == '3NT':
            return f'יש {st} לקיחות גבוהות + עוצרים → 3NT.'
        if correct == f'3{sym}':
            return f'יש 4 לקיחות גבוהות ו-{fit} קלפי {sym} → הפרעה ל-3.'
        return f'רק {st} לקיחות גבוהות. פס.'

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.show_all_hands()
        self.app.set_feedback(message, ok=ok, correct_answer=correct_answer)
        self.app.show_new_deal_button()
