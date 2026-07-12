from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_1nt_stayman
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS, card_rank, card_suit

_S = SUIT_SYMBOLS


class LessonStayman(BaseLesson):
    """שיעור 4א: סטיימן לאחר פתיחת 1NT של המחשב"""

    TITLE = 'שיעור 4. סטיימן'
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonStayman
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def _correct_message(self, final, extra_pts=0):
        h = hcp(self.hands['S']) + extra_pts
        return (f'{self._next_opener()}\n'
                f'יש לך {h} נקודות\n'
                f'ההכרזה הנכונה\n'
                f'{final}')

    def _wrong_message(self, correct, extra_pts=0):
        h = hcp(self.hands['S']) + extra_pts
        return f'יש לך {h} נקודות\nההכרזה הנכונה\n{correct}'

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

        self._set_respond_instruction()
        self.app.bidding_box.set_last_bid('1NT')

    def _set_respond_instruction(self):
        self._panel_rows = [
            ('2♣',  '8+ נקודות עם רביעייה במייג׳ור'),
            ('2NT', '8-9 נקודות בלי מייג׳ור רביעייה'),
            ('3NT', '10+ נקודות בלי מייג׳ור רביעייה'),
            ('פס',  '0-7 נקודות'),
        ]
        self.app.set_instruction_table('מה תכריז', self._panel_rows)

    def on_student_bid(self, bid):
        if self._handle_close(bid): return
        if self._stage == 'respond':
            self._handle_respond(bid)
        elif self._stage == 'stayman_cont':
            self._handle_stayman_cont(bid)

    # ── שלב 1: תגובה ראשונית ──────────────────────────────────────────────

    def _handle_respond(self, bid):
        correct = self._calc_correct_first_bid()
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            self._execute_first_bid(bid, self._correct_message(bid))
        else:
            self._tries += 1
            if self._tries < 3:
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self._finish(f'{self._wrong_message(correct)}', ok=False)

    def _calc_correct_first_bid(self):
        h = hcp(self.hands['S'])
        d = distribution(self.hands['S'])
        has_major_4 = d['H'] == 4 or d['S'] == 4
        four_count = sum([d['S'] == 4, d['H'] == 4, d['D'] >= 4, d['C'] >= 4])
        if h >= 8 and has_major_4 and four_count >= 2:
            return '2♣'
        if h <= 7:
            return 'Pass'
        if h <= 9:
            return '2NT'
        return '3NT'

    def _execute_first_bid(self, bid, message):
        if bid == 'Pass':
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(message, ok=True)
        elif bid == '2NT':
            from engine.rebid import opener_rebid
            north_bid, n_why = opener_rebid(self.hands['N'], '1NT', '2NT')
            self.app.auction_widget.add_bid(north_bid)  # N
            self.app.auction_widget.add_bid('Pass')     # E
            if north_bid != 'Pass':
                self._start_closing(message, ok=True)
            else:
                self._finish(message, ok=True)
        elif bid == '3NT':
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(message, ok=True)
        elif bid == '2♣':
            self._do_stayman()
        else:
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(message, ok=False)

    # ── סטיימן ────────────────────────────────────────────────────────────

    def _do_stayman(self):
        d_n = distribution(self.hands['N'])
        if d_n['H'] >= 4:
            self._stayman_reply = '2♥'
        elif d_n['S'] >= 4:
            self._stayman_reply = '2♠'
        else:
            self._stayman_reply = '2♦'

        # S bid 2♣ and W Pass already added; N replies
        self.app.auction_widget.add_bid(self._stayman_reply)  # N
        self.app.auction_widget.add_bid('Pass')               # E

        self._stage = 'stayman_cont'
        self._tries = 0

        r = self._stayman_reply
        reply_text = {'2♦': 'אין מיגור עיקרי', '2♥': 'יש לו 4 קלפי ♥', '2♠': 'יש לו 4 קלפי ♠ אין 4 קלפי ♥'}[r]
        fit = self._has_fit()
        fit_suit = self._fit_suit()
        if fit:
            self._panel_rows = [
                (f'3{fit_suit}', '8-9 נקודות'),
                (f'4{fit_suit}', '10+ נקודות'),
            ]
        else:
            self._panel_rows = [
                ('2NT', '8-9 נקודות'),
                ('3NT', '10+ נקודות'),
            ]
        self.app.set_instruction_table(f'{reply_text}\nמה תכריז', self._panel_rows)
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
        hand = self.hands['S']
        d = distribution(hand)
        honors = {'A', 'K', 'Q', 'J'}
        pts = 0
        for suit, length in d.items():
            if suit == trump_key:
                continue
            if length == 0:
                pts += 3
            elif length == 1:
                has_honor = any(card_rank(c) in honors for c in hand if card_suit(c) == suit)
                if not has_honor:
                    pts += 2
        return pts

    def _handle_stayman_cont(self, bid):
        correct = self._calc_stayman_cont()
        extra = self._shortage_pts() if self._has_fit() else 0
        if bid == correct:
            self._close_stayman_cont(bid, self._correct_message(bid, extra_pts=extra), ok=True)
        else:
            self._tries += 1
            if self._tries < 3:
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(f'{self._wrong_message(correct, extra_pts=extra)}', ok=False)

    def _close_stayman_cont(self, bid, message, ok):
        self.app.auction_widget.add_bid(bid, highlight=True)  # S
        self.app.auction_widget.add_bid('Pass')               # W
        if bid in ('2NT', '3♥', '3♠'):
            from engine.rebid import opener_rebid
            north_bid, _ = opener_rebid(self.hands['N'], '1NT', bid)
            self.app.auction_widget.add_bid(north_bid)  # N
            self.app.auction_widget.add_bid('Pass')     # E
            if north_bid != 'Pass':
                self._start_closing(message, ok=ok)
                return
        else:
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
        self._finish(message, ok=ok)

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
        # בסוף כל יד — מציגים את טבלת האפשרויות הרלוונטית (נכונה וגם טעות)
        rows = getattr(self, '_panel_rows', None)
        if rows:
            self.app.add_immediate_table(rows)
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
