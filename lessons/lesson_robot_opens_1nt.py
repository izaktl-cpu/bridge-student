from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_1nt
from engine.response import respond_1nt
from engine.rebid import opener_rebid
from engine.scoring import hcp
from utils.messages import msg_try_again_pts

_BIDS = ['Pass', '2NT', '3NT']


class LessonRobotOpens1NT(BaseLesson):
    """שיעור 2: מחשב (N) פותח 1NT, תלמיד (S) עונה"""

    TITLE = 'שיעור 2. מענה ל-1NT'
    _deal_count = 0

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
                'מחשב פתח 1NT. מה תענה?',
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
            self._after_correct_response(bid, why)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self._after_correct_response(bid, '')
                return
            self._tries += 1
            h = hcp(self.hands['S'])
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.bidding_box.reset()
                self.app.bidding_box.set_last_bid('1NT')
                self.app.set_feedback(msg_try_again_pts(h), ok=False)
            else:
                explanation = self._explain_wrong(bid, correct)
                self.app.set_feedback(f'הנכון: {correct}.\n{explanation}', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self._after_correct_response(bid, f'הנכון: {correct}.')

    def _after_correct_response(self, bid, why):
        ok = not why.startswith('הנכון')
        if bid == 'Pass':
            self.app.auction_widget.add_bid('Pass')   # N
            self.app.auction_widget.add_bid('Pass')   # E
            self._finish(f'{"נכון" if ok else why}\nחוזה סופי: 1NT.', ok=ok)
        elif bid == '3NT':
            self.app.auction_widget.add_bid('Pass')   # N
            self.app.auction_widget.add_bid('Pass')   # E
            self._finish(f'{"נכון" if ok else why}\nחוזה סופי: 3NT.', ok=ok)
        elif bid == '2NT':
            north_bid, n_why = opener_rebid(self.hands['N'], '1NT', '2NT')
            self.app.auction_widget.add_bid(north_bid)  # N
            self.app.auction_widget.add_bid('Pass')      # E
            final = '2NT' if north_bid == 'Pass' else north_bid
            msg = f'{"נכון" if ok else why}\nמחשב: {north_bid}. {n_why}.\nחוזה סופי: {final}.'
            if north_bid != 'Pass':
                self._start_closing(msg, ok=ok)
            else:
                self._finish(msg, ok=ok)
        else:
            # הכרזה לא צפויה. המחשב פס
            self.app.auction_widget.add_bid('Pass')   # N
            self.app.auction_widget.add_bid('Pass')   # E
            self._finish(f'{why}\nחוזה סופי: {bid}.', ok=False)

    def _explain_wrong(self, bid, correct):
        h = hcp(self.hands['S'])
        if bid == 'Pass' and correct == '2NT':
            return f'יש לך {h} נקודות גבוהות. עם 8-9 נקודות, מזמינים לחוזה 3NT על ידי הכרזת 2NT.'
        if bid == 'Pass' and correct == '3NT':
            return f'יש לך {h} נקודות גבוהות. עם 10 נקודות ומעלה, מכריזים 3NT ישירות.'
        if bid == '2NT' and correct == 'Pass':
            return f'יש לך {h} נקודות גבוהות. עם פחות מ-8 נקודות, אין מספיק למשחק. מכריזים פס.'
        if bid == '2NT' and correct == '3NT':
            return f'יש לך {h} נקודות גבוהות. עם 10 נקודות ומעלה, מכריזים 3NT ישירות ולא מזמינים.'
        if bid == '3NT' and correct == 'Pass':
            return f'יש לך {h} נקודות גבוהות. 3NT דורש לפחות 10 נקודות. עם פחות מ-8, מכריזים פס.'
        if bid == '3NT' and correct == '2NT':
            return f'יש לך {h} נקודות גבוהות. עם 8-9 נקודות, מזמינים ב-2NT ולא קופצים ישר ל-3NT.'
        return f'יש לך {h} נקודות גבוהות.'

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
