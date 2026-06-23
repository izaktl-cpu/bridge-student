from lessons.base import BaseLesson
from engine.deal_constraints import deal_student_opens_1nt
from engine.response import respond_1nt
from engine.rebid import opener_rebid
from engine.scoring import hcp, is_balanced
from utils.messages import msg_correct, msg_contract_wrong, msg_try_again_pts

_OPENING_BIDS = ['Pass', '1NT', '2NT', '3NT']


class LessonNTOpen(BaseLesson):
    """שיעור: תלמיד פותח 1NT, מחשב עונה, תלמיד ממשיך"""

    TITLE = 'שיעור 1. פתיחת 1NT'

    def start(self):
        if not self._replaying:
            self.hands = deal_student_opens_1nt()
        self._replaying = False
        self._stage = 'open'
        self._tries = 0

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('S')
        self.app.set_instruction('ספור את הנקודות שלך.\nיד מאוזנת?\nמה תפתח?')

    def on_student_bid(self, bid):
        if self._stage == 'open':
            self._handle_open(bid)
        elif self._stage == 'rebid':
            self._handle_rebid(bid)

    # ── שלב 1: תלמיד פותח ─────────────────────────────────────────────────

    def _handle_open(self, bid):
        h   = hcp(self.hands['S'])
        bal = is_balanced(self.hands['S'])

        if bid == '1NT':
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W

            north_bid, explanation = respond_1nt(self.hands['N'])
            self.app.auction_widget.add_bid(north_bid)             # N
            self.app.auction_widget.add_bid('Pass')                # E

            if north_bid == 'Pass':
                self.app.auction_widget.add_bid('Pass')            # S
                self.app.auction_widget.add_bid('Pass')            # W
                self._finish(f'פתחת 1NT. כל הכבוד!\nלצפון: {explanation}.\nחוזה סופי: 1NT.', ok=True)
            elif north_bid == '2NT':
                self._stage = 'rebid'
                self._tries = 0
                self.app.set_instruction(
                    f'צפון הזמין 2NT.\nלצפון: {explanation}.\n'
                    f'עם 15. פס.\n'
                    f'עם 16. 3NT אם יש סדרה טובה (5+ קלפים, 2 מ-A/K/Q), אחרת פס.\n'
                    f'עם 17. 3NT.')
                self.app.bidding_box.set_last_bid('2NT')
            else:  # 3NT
                self.app.auction_widget.add_bid('Pass')            # S
                self.app.auction_widget.add_bid('Pass')            # W
                self._finish(f'פתחת 1NT. כל הכבוד!\nלצפון: {explanation}.\nחוזה סופי: 3NT.', ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                self._finish(msg_contract_wrong(bid, '1NT'), ok=False)
                return
            self._tries += 1
            bal_txt = 'מאוזנת' if bal else 'לא מאוזנת'
            if self._tries < 3:
                self._last_wrong_bid = bid
                if bid == '2NT':
                    hint = f'פתיחת 2NT דורשת 20-21 נקודות.\nיש לך {h}. נסה שוב.'
                elif bid == '3NT':
                    hint = f'3NT הוא חוזה, לא פתיחה!\nיש לך {h} נקודות. נסה שוב.'
                else:
                    hint = f'יש לך {h} נקודות, יד {bal_txt}.\nנסה שוב.'
                self.app.bidding_box.reset()
                self.app.set_feedback(hint, ok=False)
            else:
                msg = (f'בחרת {bid}.\n'
                       f'יש לך {h} נקודות גבוהות, יד {bal_txt}.\n'
                       f'הפתיחה הנכונה: 1NT.')
                self.app.set_feedback(f'הנכון: 1NT.\n{msg}', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                self._finish(msg_contract_wrong(bid, '1NT'), ok=False)

    # ── שלב 2: תלמיד מגיב אחרי 2NT ────────────────────────────────────────

    def _handle_rebid(self, bid):
        h = hcp(self.hands['S'])
        correct, why = opener_rebid(self.hands['S'], '1NT', '2NT')

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W
            self.app.auction_widget.add_bid('Pass')                # N
            self.app.auction_widget.add_bid('Pass')                # E
            final = bid if bid != 'Pass' else '2NT'
            self._finish(msg_correct(why, final), ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                final = bid if bid != 'Pass' else '2NT'
                self._finish(msg_contract_wrong(final, correct), ok=False)
                return
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.bidding_box.reset()
                self.app.bidding_box.set_last_bid('2NT')
                self.app.set_feedback(msg_try_again_pts(h), ok=False)
            else:
                if bid == 'Pass' and correct == '3NT':
                    explanation = f'יש לך {h} נקודות גבוהות. עם 16 נקודות ומעלה, מקבלים את ההזמנה ומכריזים 3NT.'
                elif bid == '3NT' and correct == 'Pass':
                    explanation = f'יש לך {h} נקודות גבוהות. עם 15 נקודות. מינימום 1NT. דוחים את ההזמנה ומכריזים פס.'
                else:
                    explanation = f'יש לך {h} נקודות גבוהות.'
                msg = f'בחרת {bid}.\n{explanation}\nההכרזה הנכונה: {correct}.'
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                self._finish(msg, ok=False)

    # ── סיום ───────────────────────────────────────────────────────────────

    def _finish(self, message, ok):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.table.show_hands(self.hands, visible=('N', 'E', 'S', 'W'))
        self.app.show_new_deal_button()
