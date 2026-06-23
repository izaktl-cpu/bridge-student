from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_1nt_stayman
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_retry, msg_chose_wrong, msg_correct_final

_S = SUIT_SYMBOLS


class LessonStayman(BaseLesson):
    """שיעור 4א: סטיימן לאחר פתיחת 1NT של המחשב"""

    TITLE = 'שיעור 4. סטיימן'

    def start(self):
        if not self._replaying:
            self.hands = deal_robot_opens_1nt_stayman()
        self._replaying = False
        self._stage = 'respond'
        self._tries = 0
        self._awaiting_close = False

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid('1NT')
        self.app.auction_widget.add_bid('Pass')

        self.app.set_instruction('מחשב פתח 1NT. מה תכריז?')
        self.app.bidding_box.set_last_bid('1NT')

    def on_student_bid(self, bid):
        if self._handle_close(bid): return
        if self._stage == 'respond':
            self._handle_respond(bid)
        elif self._stage == 'stayman_cont':
            self._handle_stayman_cont(bid)

    # ── שלב 1: תגובה ראשונית ──────────────────────────────────────────────

    def _handle_respond(self, bid):
        correct, why = self._calc_correct_first_bid()
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            self._execute_first_bid(bid, why)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                self._execute_first_bid(bid, '')
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.set_feedback(f'הנכון: {correct}.', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                self._execute_first_bid(bid, f'הנכון: {correct}.')

    def _calc_correct_first_bid(self):
        h = hcp(self.hands['S'])
        d = distribution(self.hands['S'])
        has_major_4 = d['H'] == 4 or d['S'] == 4
        four_count = sum([d['S'] == 4, d['H'] == 4, d['D'] >= 4, d['C'] >= 4])
        if h >= 8 and has_major_4 and four_count >= 2:
            return '2♣', f'{h} נקודות, 2 רביעיות עם מיגור. סטיימן 2♣'
        if h <= 7:
            return 'Pass', f'{h} נקודות. מכריזים פס'
        if h <= 9:
            return '2NT', f'{h} נקודות. מזמינים ל-3NT'
        return '3NT', f'{h} נקודות. מכריזים משחק מלא'

    def _execute_first_bid(self, bid, why):
        ok = not why.startswith('הנכון')
        prefix = '✓ ' if ok else ''
        if bid == 'Pass':
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(f'{prefix}{why}\nחוזה סופי: 1NT.', ok=ok)
        elif bid == '2NT':
            from engine.rebid import opener_rebid
            north_bid, n_why = opener_rebid(self.hands['N'], '1NT', '2NT')
            self.app.auction_widget.add_bid(north_bid)  # N
            self.app.auction_widget.add_bid('Pass')     # E
            final = '2NT' if north_bid == 'Pass' else north_bid
            msg = f'{prefix}{why}\nמחשב: {north_bid}.\nחוזה סופי: {final}.'
            if north_bid != 'Pass':
                self._start_closing(msg, ok=ok)
            else:
                self._finish(msg, ok=ok)
        elif bid == '3NT':
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(f'{prefix}{why}\nחוזה סופי: 3NT.', ok=ok)
        elif bid == '2♣':
            self._do_stayman(why)
        else:
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(f'{why}\nחוזה סופי: {bid}.', ok=False)

    # ── סטיימן ────────────────────────────────────────────────────────────

    def _do_stayman(self, why):
        d_n = distribution(self.hands['N'])
        if d_n['H'] >= 4:
            self._stayman_reply = '2♥'
        elif d_n['S'] >= 4:
            self._stayman_reply = '2♠'
        else:
            self._stayman_reply = '2♦'

        self._stayman_why = why
        # S bid 2♣ and W Pass already added; N replies
        self.app.auction_widget.add_bid(self._stayman_reply)  # N
        self.app.auction_widget.add_bid('Pass')               # E

        self._stage = 'stayman_cont'
        self._tries = 0

        h = hcp(self.hands['S'])
        r = self._stayman_reply
        reply_text = {'2♦': 'אין מיגור עיקרי', '2♥': 'יש לו ♥', '2♠': 'יש לו ♠, אין ♥'}[r]
        fit = self._has_fit()
        fit_suit = self._fit_suit()
        if fit:
            shortage = self._shortage_pts()
            total = h + shortage
            if shortage > 0:
                pts_str = f'יש {h} נקודות גבוהות\nיש {shortage} נקודות חוסר\nסה״כ {total}'
            else:
                pts_str = f'יש {h} נקודות'
            hint = f'יש התאמה ב-{fit_suit}.\n{pts_str}\n8-9 סה״כ → 3{fit_suit}  |  10+ סה״כ → 4{fit_suit}'
        else:
            hint = f'אין התאמה במיגור.\nיש {h} נקודות\n8-9 → 2NT  |  10+ → 3NT'
        self.app.set_instruction(f'מחשב ענה {r} ({reply_text}).\n{hint}')
        self.app.bidding_box.set_last_bid(self._stayman_reply)

    def _has_fit(self):
        d = distribution(self.hands['S'])
        r = self._stayman_reply
        if r == '2♥' and d['H'] >= 4:
            return True
        if r == '2♠' and d['S'] >= 4:
            return True
        return False

    def _fit_suit(self):
        return '♥' if self._stayman_reply == '2♥' else '♠'

    def _stayman_cont_options(self):
        if self._has_fit():
            suit = self._fit_suit()
            return [f'3{suit}', f'4{suit}']
        return ['2NT', '3NT']

    def _shortage_pts(self):
        sym = self._fit_suit()
        trump_key = 'H' if sym == '♥' else 'S'
        d = distribution(self.hands['S'])
        pts = 0
        for suit, length in d.items():
            if suit == trump_key:
                continue
            if length == 0:
                pts += 3
            elif length == 1:
                pts += 2
        return pts

    def _handle_stayman_cont(self, bid):
        correct = self._calc_stayman_cont()
        h = hcp(self.hands['S'])
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            self.app.auction_widget.add_bid('Pass')               # N
            self.app.auction_widget.add_bid('Pass')               # E
            self._finish(msg_correct_final(bid), ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                self.app.auction_widget.add_bid('Pass')               # N
                self.app.auction_widget.add_bid('Pass')               # E
                self._finish(msg_chose_wrong(bid, correct), ok=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                self.app.auction_widget.add_bid('Pass')               # N
                self.app.auction_widget.add_bid('Pass')               # E
                if self._has_fit():
                    shortage = self._shortage_pts()
                    total = h + shortage
                    self._finish(
                        f'✗ בחרת {bid}.\nיש {h} נקודות גבוהות\nיש {shortage} נקודות חוסר\nסה״כ {total}.\nהנכון: {correct}.', ok=False)
                else:
                    self._finish(f'✗ בחרת {bid}.\nיש {h} נקודות.\nהנכון: {correct}.', ok=False)

    def _calc_stayman_cont(self):
        h = hcp(self.hands['S'])
        if self._has_fit():
            suit = self._fit_suit()
            total = h + self._shortage_pts()
            return f'4{suit}' if total >= 10 else f'3{suit}'
        return '3NT' if h >= 10 else '2NT'

    # ── סיום ───────────────────────────────────────────────────────────────

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
