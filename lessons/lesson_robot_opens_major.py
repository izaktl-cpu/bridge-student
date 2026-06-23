import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_major
from engine.response import respond_major
from engine.rebid import opener_rebid
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_contract_wrong, msg_try_again_pts

_S = SUIT_SYMBOLS


class LessonRobotOpensMajor(BaseLesson):
    """מחשב (N) פותח מיגור עיקרי, תלמיד (S) עונה"""

    _deal_count = 0

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
                    ('פס',       '0-5 נקודות'),
                    (f'2{sym}',  f'6-9 נקודות, 3-4 קלפי {sym}'),
                    (f'3{sym}',  f'10-11 נקודות, 3-4 קלפי {sym}'),
                    (f'4{sym}',  f'12+ נקודות, 3+ קלפי {sym}'),
                    (f'4{sym}',  f'חוק 19: 7+ נקודות, 5 קלפי {sym}'),
                ]
            )

    def on_student_bid(self, bid):
        if self._handle_close(bid): return
        if self._stage == 'respond':
            self._handle_respond(bid)

    def _handle_respond(self, bid):
        h   = hcp(self.hands['S'])
        d   = distribution(self.hands['S'])
        sym = _S[self._major]
        correct, why = respond_major(self.hands['S'], self._major)

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W

            opening = f'1{sym}'
            n_rebid, n_why = opener_rebid(self.hands['N'], opening, bid)

            if n_rebid == 'Pass':
                self.app.auction_widget.add_bid('Pass')            # N
                self.app.auction_widget.add_bid('Pass')            # E
                self._finish(f'נכון!\n{why}.\n\nחוזה סופי: {bid}.', ok=True)
            else:
                self.app.auction_widget.add_bid(n_rebid)           # N
                self.app.auction_widget.add_bid('Pass')            # E
                self._start_closing(
                    f'נכון!\n{why}.\n\n'
                    f'מחשב העלה ל-{n_rebid}: {n_why}.\n\n'
                    f'חוזה סופי: {n_rebid}.', ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                opening = f'1{sym}'
                n_rebid, n_why = opener_rebid(self.hands['N'], opening, bid)
                if n_rebid == 'Pass':
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(msg_contract_wrong(bid, correct), ok=False)
                else:
                    self.app.auction_widget.add_bid(n_rebid)  # N
                    self.app.auction_widget.add_bid('Pass')   # E
                    self._start_closing(f'מחשב: {n_rebid}.\nחוזה סופי: {n_rebid}. הנכון: {correct}.', ok=False)
                return
            self._tries += 1
            h = hcp(self.hands['S'])
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.bidding_box.reset()
                self.app.bidding_box.set_last_bid(f'1{sym}')
                self.app.set_feedback(msg_try_again_pts(h), ok=False)
            else:
                explanation = self._explain_wrong(bid, correct)
                self.app.set_feedback(f'הנכון: {correct}.\n{explanation}', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                opening = f'1{sym}'
                n_rebid, n_why = opener_rebid(self.hands['N'], opening, bid)
                if n_rebid == 'Pass':
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(msg_contract_wrong(bid, correct), ok=False)
                else:
                    self.app.auction_widget.add_bid(n_rebid)  # N
                    self.app.auction_widget.add_bid('Pass')   # E
                    self._start_closing(
                        f'הנכון: {correct}.\nמחשב: {n_rebid}.\nחוזה סופי: {n_rebid}.', ok=False)

    def _explain_wrong(self, bid, correct):
        h   = hcp(self.hands['S'])
        d   = distribution(self.hands['S'])
        sym = _S[self._major]
        fit = d[self._major]

        if bid == 'Pass':
            return (f'יש לך {h} נקודות גבוהות ו-{fit} קלפי {sym}. '
                    f'עם תמיכה ו-6 נקודות לפחות, יש לתמוך בסדרת הפותח.')

        bid_level    = int(bid[0]) if bid[0].isdigit() else 0
        correct_level = int(correct[0]) if correct[0].isdigit() else 0

        if bid_level < correct_level:
            if correct == f'3{sym}':
                return (f'יש לך {h} נקודות גבוהות ו-{fit} קלפי {sym}. '
                        f'עם 10-11 נקודות ותמיכה, מכריזים {correct} כהזמנה למשחק.')
            if correct == f'4{sym}':
                if fit >= 5:
                    return (f'יש לך {h} נקודות גבוהות ו-{fit} קלפי {sym}. '
                            f'חוק ה-19: עם 5 קלפים ו-7+ נקודות, '
                            f'יש לנו 10 קלפים ביחד. קופצים ישר ל-{correct}.')
                return (f'יש לך {h} נקודות גבוהות ו-{fit} קלפי {sym}. '
                        f'עם 12 נקודות ומעלה ותמיכה, קופצים ישר לחוזה המשחק {correct}.')

        if bid_level > correct_level:
            if correct == f'2{sym}':
                return (f'יש לך {h} נקודות גבוהות. '
                        f'עם 6-9 נקודות, מכריזים {correct} בלבד. אין מספיק לרמה גבוהה יותר.')
            if correct == f'3{sym}':
                return (f'יש לך {h} נקודות גבוהות. '
                        f'עם 10-11 נקודות, מכריזים {correct} כהזמנה. לא קופצים ישר ל-4.')

        return f'יש לך {h} נקודות גבוהות ו-{fit} קלפי {sym}.'

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
