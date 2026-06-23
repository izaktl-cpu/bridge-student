import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_student_opens_major
from engine.response import respond_major
from engine.rebid import opener_rebid
from engine.scoring import hcp, distribution, dist_fit_pts
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_contract_wrong

_S = SUIT_SYMBOLS


class LessonStudentOpensMajor(BaseLesson):
    """תלמיד (S) פותח מיגור עיקרי, מחשב (N) עונה"""

    TITLE = 'שיעור 3. פתיחת מיגור עיקרי'
    _deal_count = 0

    def start(self):
        if not self._replaying:
            LessonStudentOpensMajor._deal_count += 1
            self._major = random.choice(['H', 'S'])
            self.hands  = deal_student_opens_major(self._major)
        self._replaying = False
        self._stage = 'open'
        self._tries = 0

        sym = _S[self._major]
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('S')
        self.app.bidding_box.reset()

        if LessonStudentOpensMajor._deal_count <= 3:
            h = hcp(self.hands['S'])
            d = distribution(self.hands['S'])
            self.app.set_instruction(
                f'יש לך {h} נקודות גבוהות ו-{d[self._major]} קלפי {sym}.\n\n'
                f'עם 5+ קלפי {sym} ו-12-19 נקודות:\n'
                f'פתח 1{sym}.')

    def on_student_bid(self, bid):
        if self._stage == 'open':
            self._handle_open(bid)
        elif self._stage == 'rebid':
            self._handle_rebid(bid)

    # ── שלב 1: תלמיד פותח ─────────────────────────────────────────────────

    def _handle_open(self, bid):
        h   = hcp(self.hands['S'])
        d   = distribution(self.hands['S'])
        sym = _S[self._major]
        correct = f'1{sym}'

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W

            north_bid, n_why = respond_major(self.hands['N'], self._major)
            self._north_bid = north_bid
            self.app.auction_widget.add_bid(north_bid)             # N
            self.app.auction_widget.add_bid('Pass')                # E

            if north_bid in (f'4{sym}', '3NT'):
                self._finish(
                    f'נכון!\n\n'
                    f'פתחת 1{sym}.\n'
                    f'מחשב ענה {north_bid}: {n_why}.\n\n'
                    f'חוזה סופי: {north_bid}.',
                    ok=True)
            else:
                self._stage = 'rebid'
                self._tries = 0
                h_s     = hcp(self.hands['S'])
                is_raise = north_bid in (f'2{sym}', f'3{sym}', f'4{sym}')
                dp      = dist_fit_pts(self.hands['S'], trump=self._major) if is_raise else 0
                tot     = h_s + dp
                self._rebid_pts = (h_s, dp, tot)
                dp_str = f'\nיש {h_s} נקודות גבוהות\nיש {dp} נקודות חוסר\nסה״כ {tot}' if dp > 0 else f'\nיש {h_s} נקודות גבוהות'
                self.app.bidding_box.set_last_bid(north_bid)
                self.app.set_instruction(
                    f'מחשב ענה {north_bid}.\n{n_why}.{dp_str}\n\nמה תכריז עכשיו?')
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                self._finish(msg_contract_wrong(bid, correct), ok=False)
                return
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.bidding_box.reset()
                self.app.set_feedback(
                    f'יש לך {h} נקודות גבוהות ו-{d[self._major]} קלפי {sym}.\nנסה שוב.', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                self._finish(
                    f'בחרת {bid}.\n'
                    f'יש לך {h} נקודות גבוהות ו-{d[self._major]} קלפי {sym}.\n'
                    f'ההכרזה הנכונה: {correct}.',
                    ok=False)

    # ── שלב 2: תלמיד עושה חזרה ─────────────────────────────────────────────

    def _handle_rebid(self, bid):
        opening = f'1{_S[self._major]}'
        correct, why = opener_rebid(self.hands['S'], opening, self._north_bid)
        sym = _S[self._major]

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W
            self.app.auction_widget.add_bid('Pass')                # N
            self.app.auction_widget.add_bid('Pass')                # E
            final_contract = self._north_bid if bid == 'Pass' else bid
            self._finish(f'נכון!\n\n{why}.\n\nחוזה סופי: {final_contract}.', ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                final_contract = self._north_bid if bid == 'Pass' else bid
                self._finish(msg_contract_wrong(final_contract, correct), ok=False)
                return
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.bidding_box.set_last_bid(self._north_bid)
                h_s, dp, tot = self._rebid_pts
                if dp > 0:
                    hint = f'יש לך {h_s} נקודות גבוהות + {dp} נקודות חלוקה = {tot} סה״כ.\nנסה שוב.'
                else:
                    hint = f'יש לך {h_s} נקודות גבוהות.\nנסה שוב.'
                self.app.set_feedback(hint, ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')                # W
                self.app.auction_widget.add_bid('Pass')                # N
                self.app.auction_widget.add_bid('Pass')                # E
                explanation = self._explain_rebid_wrong(bid, correct)
                self._finish(
                    f'בחרת {bid}.\n{explanation}\nההכרזה הנכונה: {correct}.', ok=False)

    def _explain_rebid_wrong(self, bid, correct):
        h_s, dp, tot = self._rebid_pts
        d   = distribution(self.hands['S'])
        sym = _S[self._major]
        nb  = self._north_bid
        pts = f'יש {h_s} נקודות גבוהות\nיש {dp} נקודות חוסר\nסה״כ {tot}' if dp > 0 else f'יש {h_s} נקודות גבוהות'

        # אחרי 1NT (שותף 6-9, ללא תמיכה)
        if nb == '1NT':
            if correct == 'Pass':
                return (f'יש לך {pts}. השותף ענה 1NT (6-9 נקודות, ללא תמיכה). '
                        f'עם 12-14 נקודות. מינימום. מכריזים פס.')
            if correct == f'2{sym}':
                return (f'יש לך {pts} ו-{d[self._major]} קלפי {sym}. '
                        f'עם 15 נקודות ומעלה ו-5+ קלפים. מכריזים {correct} להדגיש את הסדרה.')
            if correct == '2NT':
                return (f'יש לך {pts}. '
                        f'עם 18-19 נקודות. מכריזים 2NT כהזמנה למשחק.')

        # אחרי תמיכה פשוטה 2{sym} (שותף 6-9, 3+ קלפים)
        if nb == f'2{sym}':
            if correct == 'Pass':
                return (f'יש לך {pts}. השותף תמך ב-2{sym} (6-9 נקודות). '
                        f'עם 12-14 נקודות כולל חלוקה. מינימום. מכריזים פס.')
            if correct == f'3{sym}':
                return (f'יש לך {pts}. השותף תמך ב-2{sym} (6-9 נקודות). '
                        f'עם 15-16 נקודות כולל חלוקה. מזמינים ב-{correct} למשחק.')
            if correct == f'4{sym}':
                return (f'יש לך {pts}. השותף תמך ב-2{sym} (6-9 נקודות). '
                        f'עם 17 נקודות ומעלה כולל חלוקה. קופצים ישר ל-{correct}.')

        # אחרי הזמנה 3{sym} (שותף 10-11, 3+ קלפים)
        if nb == f'3{sym}':
            if correct == f'4{sym}':
                return (f'יש לך {pts}. השותף הזמין {nb} (10-11 נקודות). '
                        f'עם 15 נקודות ומעלה כולל חלוקה. מקבלים ומכריזים {correct}.')
            if correct == 'Pass':
                return (f'יש לך {pts}. השותף הזמין {nb} (10-11 נקודות). '
                        f'עם 12-14 נקודות כולל חלוקה. מינימום. מכריזים פס.')

        # אחרי 2NT (שותף 10-12, מאוזן)
        if nb == '2NT':
            if correct == '3NT':
                return (f'יש לך {pts}. השותף הזמין 2NT (10-12 נקודות). '
                        f'עם 15 נקודות ומעלה. מקבלים ומכריזים 3NT.')
            if correct == 'Pass':
                return (f'יש לך {pts}. השותף הזמין 2NT (10-12 נקודות). '
                        f'עם 12-14 נקודות. מינימום. דוחים ומכריזים פס.')

        # אחרי צבע חדש של השותף
        lvl_b = int(bid[0]) if bid and bid[0].isdigit() else 0
        lvl_c = int(correct[0]) if correct and correct[0].isdigit() else 0
        if lvl_b < lvl_c:
            return (f'יש לך {pts}. '
                    f'הכרזת {bid} חלשה מדי. עם {tot} נקודות ההכרזה הנכונה היא {correct}.')
        if lvl_b > lvl_c:
            return (f'יש לך {pts}. '
                    f'הכרזת {bid} חזקה מדי. עם {tot} נקודות ההכרזה הנכונה היא {correct}.')

        return f'יש לך {pts}. ההכרזה הנכונה היא {correct}.'

    # ── סיום ───────────────────────────────────────────────────────────────

    def _finish(self, message, ok):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
