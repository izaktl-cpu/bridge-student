import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_slam_nt_mode_a, deal_slam_nt_mode_b, deal_slam_nt_mode_c, deal_slam_nt_mode_d, deal_slam_nt_mode_e
from engine.scoring import hcp, suit_len, key_cards, rkcb_response
from engine.opening import opening_bid as _opening_bid
from utils.messages import msg_retry, msg_chose_wrong, msg_chose_wrong_why
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS

_RKCB_EXPLAIN = {
    f'5{_S["C"]}': '0 או 3 אסים',
    f'5{_S["D"]}': '1 או 4 אסים',
    f'5{_S["H"]}': '2 אסים, ללא Q♠',
    f'5{_S["S"]}': '2 אסים + Q♠',
}

_MODE_D_SEQS = [
    ('C', 'H', f'1{_S["C"]}', f'1{_S["H"]}'),
    ('C', 'S', f'1{_S["C"]}', f'1{_S["S"]}'),
    ('D', 'H', f'1{_S["D"]}', f'1{_S["H"]}'),
    ('D', 'S', f'1{_S["D"]}', f'1{_S["S"]}'),
]

_MODE_C_SEQS = [
    ('C', 'H', f'1{_S["C"]}', f'1{_S["H"]}'),
    ('C', 'S', f'1{_S["C"]}', f'1{_S["S"]}'),
    ('D', 'H', f'1{_S["D"]}', f'1{_S["H"]}'),
    ('D', 'S', f'1{_S["D"]}', f'1{_S["S"]}'),
]


class LessonSlamNT(BaseLesson):
    """שיעור 8: סלם ב-NT. הכרזה כמותית 4NT ו-6NT"""

    TITLE = 'שיעור 8. סלם NT'

    def start(self):
        if not self._replaying:
            self._mode = random.choice(['A', 'B', 'C', 'D'])
        self._tries = 0
        self._awaiting_close = False
        _deal = not self._replaying
        self._replaying = False

        if self._mode == 'A':
            self._stage = 'decide'
            self._setup_mode_a(_deal)
        elif self._mode == 'B':
            self._stage = 'decide'
            self._setup_mode_b(_deal)
        elif self._mode == 'C':
            self._setup_mode_c(_deal)
        elif self._mode == 'D':
            self._setup_mode_d(_deal)
        elif self._mode == 'E':
            self._setup_mode_e(_deal)

    # ── הכנה ──────────────────────────────────────────────────────────────

    def _setup_mode_a(self, deal=True):
        if deal:
            self.hands = deal_slam_nt_mode_a()
        self._hn = hcp(self.hands['N'])

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid('1NT')
        self.app.auction_widget.add_bid('Pass')

        self.app.set_instruction_table(
            'מחשב פתח 1NT (15-17). מה תכריז?',
            [
                ('Pass', '0-7 נקודות'),
                ('2NT', '8-9. הזמנה ל-3NT'),
                ('3NT', '10-15 נקודות'),
                ('4NT', '16+. הזמנה לסלם\nל-6NT: 33 נק\' משותפות'),
            ]
        )
        self.app.bidding_box.set_last_bid('1NT')

    def _setup_mode_b(self, deal=True):
        if deal:
            self.hands = deal_slam_nt_mode_b()
        self._accept_hcp = 22
        self._hn = hcp(self.hands['N'])

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid('2NT')
        self.app.auction_widget.add_bid('Pass')

        self.app.set_instruction_table(
            'מחשב פתח 2NT (20-22). מה תכריז?',
            [
                ('3NT', '5-10 נקודות'),
                ('4NT', '11-12. הזמנה לסלם'),
                ('6NT', '13+ נקודות. סלם ישיר'),
            ]
        )
        self.app.bidding_box.set_last_bid('2NT')

    def _setup_mode_c(self, deal=True):
        if deal:
            opening, response, open_bid, resp_bid = random.choice(_MODE_C_SEQS)
            self._mode_c_seq = (opening, response, open_bid, resp_bid)
            self.hands = deal_slam_nt_mode_c(opening, response)
        opening, response, open_bid, resp_bid = self._mode_c_seq
        self._accept_hcp = 16
        self._hn = hcp(self.hands['N'])

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid(open_bid)
        self.app.auction_widget.add_bid('Pass')

        self._stage = 'respond_c'
        self._tries = 0

        open_sym = open_bid[1]
        rows = []
        if opening in ('C', 'D'):
            rows = [
                ('1♥', '4+ קלפי ♥, אין 5 ♠'),
                ('1♠', '4+ קלפי ♠\nעם 5♠+4♥ — ♠ קודם'),
            ]
        else:  # opening == 'H'
            rows = [('1♠', '4+ קלפי ♠')]
        self.app.set_instruction_table(
            f'מחשב פתח {open_bid}. מה תכריז?', rows)
        self.app.bidding_box.set_last_bid(open_bid)

    def _setup_mode_d(self, deal=True):
        if deal:
            opening, response, open_bid, resp_bid = random.choice(_MODE_D_SEQS)
            self._mode_d_seq = (opening, response, open_bid, resp_bid)
            self.hands = deal_slam_nt_mode_d(opening, response)
        opening, response, open_bid, resp_bid = self._mode_d_seq
        self._hn = hcp(self.hands['N'])

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid(open_bid)
        self.app.auction_widget.add_bid('Pass')

        self._stage = 'respond_d'
        self._tries = 0

        resp_sym = _S[response]
        self.app.set_instruction_table(
            f'מחשב פתח {open_bid}. מה תכריז?',
            [(resp_bid, f'4+ קלפי {resp_sym}, 18+ נק\'')]
        )
        self.app.bidding_box.set_last_bid(open_bid)

    def _handle_respond_d(self, bid):
        _, _, open_bid, resp_bid = self._mode_d_seq
        correct = resp_bid
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            self.app.auction_widget.add_bid('1NT')                # N
            self.app.auction_widget.add_bid('Pass')               # E
            self._stage = 'decide_d'
            self._tries = 0
            hs = hcp(self.hands['S'])
            has_five = any(suit_len(self.hands['S'], su) >= 5 for su in ['S', 'H', 'D', 'C'])
            if has_five and hs == 20:
                rows = [('6NT', '20 נק\' + סדרה. סלם ישיר')]
            else:
                rows = [('4NT', 'שואל מינימום/מקסימום\nל-6NT: 33 נק\' משותפות')]
            self.app.set_instruction_table('מחשב חזר 1NT (12-17). מה תכריז?', rows)
            self.app.bidding_box.set_last_bid('1NT')
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                self.app.auction_widget.add_bid('1NT')                # N
                self.app.auction_widget.add_bid('Pass')               # E
                self._stage = 'decide_d'
                self._tries = 0
                self.app.set_instruction_table('מחשב חזר 1NT. מה תכריז?',
                    [('4NT', 'שואל מינימום/מקסימום\nל-6NT: 33 נק\' משותפות')])
                self.app.bidding_box.set_last_bid(bid if bid[0] >= '2' else '1NT')
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.set_feedback(f'הנכון: {resp_bid}.', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                self.app.auction_widget.add_bid('1NT')                # N
                self.app.auction_widget.add_bid('Pass')               # E
                self._stage = 'decide_d'
                self._tries = 0
                self.app.set_instruction_table('מחשב חזר 1NT. מה תכריז?',
                    [('4NT', 'שואל מינימום/מקסימום\nל-6NT: 33 נק\' משותפות')])
                self.app.bidding_box.set_last_bid(bid if bid[0] >= '2' else '1NT')

    def _handle_decide_d(self, bid):
        hs = hcp(self.hands['S'])
        has_five = any(suit_len(self.hands['S'], su) >= 5 for su in ['S', 'H', 'D', 'C'])
        correct = '6NT' if (has_five and hs == 20) else '4NT'
        total = hs + self._hn

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            if correct == '6NT':
                self.app.auction_widget.add_bid('Pass')  # W
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(
                    f'✓ סלם ישיר!\nיש {hs} נקודות + סדרה.\nחוזה: 6NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                    ok=True)
            else:  # 4NT
                self.app.auction_widget.add_bid('Pass')  # W
                if self._hn + hs >= 33:
                    self.app.auction_widget.add_bid('6NT')   # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._start_closing(
                        f'✓ נכון! מחשב יש לו {self._hn}. מכריז 6NT.\nחוזה: 6NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                        ok=True)
                else:
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(
                        f'✓ נכון! מחשב יש לו {self._hn}. פס.\nחוזה: 4NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                        ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(msg_chose_wrong_why(bid, correct, f'יש {hs} נקודות.'), ok=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(msg_chose_wrong_why(bid, correct, f'יש {hs} נקודות.'), ok=False)

    def _handle_respond_c(self, bid):
        _, _, open_bid, resp_bid = self._mode_c_seq
        # עם 5♠+4♥ — הכרז ♠ קודם
        if resp_bid == f'1{_S["H"]}' and suit_len(self.hands['S'], 'S') >= 5:
            resp_bid = f'1{_S["S"]}'
        if bid == resp_bid:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            self.app.auction_widget.add_bid('1NT')                # N
            self.app.auction_widget.add_bid('Pass')               # E
            self._stage = 'decide'
            self._tries = 0
            self.app.set_instruction_table(
                'מחשב חזר 1NT (12-16). מה תכריז?',
                [
                    ('3NT', 'עד 16 נקודות'),
                    ('4NT', '17-19. הזמנה לסלם'),
                    ('6NT', '20+. סלם ישיר'),
                ]
            )
            self.app.bidding_box.set_last_bid('1NT')
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                self.app.auction_widget.add_bid('1NT')                # N
                self.app.auction_widget.add_bid('Pass')               # E
                self._stage = 'decide'
                self._tries = 0
                self.app.set_instruction_table('מחשב חזר 1NT (12-16). מה תכריז?',
                    [('3NT','עד 16'),('4NT','17-19'),('6NT','20+')])
                self.app.bidding_box.set_last_bid(bid if bid[0] >= '2' else '1NT')
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.set_feedback(f'הנכון: {resp_bid}.', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                self.app.auction_widget.add_bid('1NT')                # N
                self.app.auction_widget.add_bid('Pass')               # E
                self._stage = 'decide'
                self._tries = 0
                self.app.set_instruction_table('מחשב חזר 1NT (12-16). מה תכריז?',
                    [('3NT','עד 16'),('4NT','17-19'),('6NT','20+')])
                self.app.bidding_box.set_last_bid(bid if bid[0] >= '2' else '1NT')

    # ── לוגיקת תגובה ──────────────────────────────────────────────────────

    def on_student_bid(self, bid):
        if self._handle_close(bid): return
        if self._stage == 'respond_c':
            self._handle_respond_c(bid)
        elif self._stage == 'respond_d':
            self._handle_respond_d(bid)
        elif self._stage == 'decide_d':
            self._handle_decide_d(bid)
        elif self._stage == 'decide':
            self._handle_decide(bid)
        elif self._stage == 'e_bid1':
            self._handle_e_bid1(bid)
        elif self._stage == 'e_bid2':
            self._handle_e_bid2(bid)
        elif self._stage == 'e_bid3':
            self._handle_e_bid3(bid)
        elif self._stage == 'e_bid4':
            self._handle_e_bid4(bid)

    def _handle_decide(self, bid):
        correct = self._calc_correct()
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self._execute_bid(bid)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                hs = hcp(self.hands['S'])
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(msg_chose_wrong_why(bid, correct, f'יש {hs} נקודות.'), ok=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                hs = hcp(self.hands['S'])
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(msg_chose_wrong_why(bid, correct, f'יש {hs} נקודות.'), ok=False)

    def _calc_correct(self):
        hs = hcp(self.hands['S'])
        if self._mode == 'A':
            if hs <= 7:  return 'Pass'
            if hs <= 9:  return '2NT'
            if hs <= 15: return '3NT'
            return '4NT'
        elif self._mode == 'B':
            if hs <= 10: return '3NT'   # 5-10: משחק
            if hs >= 13: return '6NT'   # 13+: סלם ישיר (combined ≥ 33)
            return '4NT'                # 11-12: הזמנה
        else:  # C
            if hs <= 16: return '3NT'   # combined עד 32
            if hs >= 20: return '6NT'   # סלם ישיר
            return '4NT'                # 17-19: הזמנה

    def _execute_bid(self, bid):
        hs = hcp(self.hands['S'])
        total = hs + self._hn
        if bid == 'Pass':
            self.app.auction_widget.add_bid('Pass')  # W
            self._finish(f'✓ נכון! יש {hs} נקודות. חוזה: 1NT.', ok=True)
        elif bid == '2NT':
            self.app.auction_widget.add_bid('Pass')  # W
            self._handle_2nt_computer_response(hs, total)
        elif bid == '3NT':
            self.app.auction_widget.add_bid('Pass')  # W
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(
                f'✓ נכון! חוזה: 3NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                ok=True)
        elif bid == '6NT':
            self.app.auction_widget.add_bid('Pass')  # W
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(
                f'✓ סלם! חוזה: 6NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                ok=True)
        elif bid == '4NT':
            self._handle_4nt(hs, total)

    def _handle_2nt_computer_response(self, hs, total):
        if self._hn >= 17:
            self.app.auction_widget.add_bid('3NT')   # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._start_closing(
                f'✓ נכון! מחשב יש לו {self._hn}. מכריז 3NT.\nחוזה: 3NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                ok=True)
        elif self._hn == 16:
            has_5 = any(suit_len(self.hands['N'], s) >= 5 for s in ['S', 'H', 'D', 'C'])
            if has_5:
                self.app.auction_widget.add_bid('3NT')   # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._start_closing(
                    f'✓ נכון! מחשב יש לו {self._hn} + סדרה. מכריז 3NT.\nחוזה: 3NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                    ok=True)
            else:
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(
                    f'✓ נכון! מחשב יש לו {self._hn}, אין סדרה. פס.\nחוזה: 2NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                    ok=True)
        else:  # 15
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(
                f'✓ נכון! מחשב יש לו {self._hn}. פס.\nחוזה: 2NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                ok=True)

    def _handle_4nt(self, hs, total):
        self.app.auction_widget.add_bid('Pass')  # W
        if total >= 33:
            self.app.auction_widget.add_bid('6NT')   # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._start_closing(
                f'✓ נכון! מחשב יש לו {self._hn}. מכריז 6NT.\nחוזה: 6NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                ok=True)
        elif total == 32:
            has_5 = any(suit_len(self.hands['N'], s) >= 5 for s in ['S', 'H', 'D', 'C'])
            if has_5:
                self.app.auction_widget.add_bid('6NT')   # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._start_closing(
                    f'✓ נכון! מחשב יש לו {self._hn} + סדרה. מכריז 6NT.\nחוזה: 6NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                    ok=True)
            else:
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(
                    f'✓ נכון! מחשב יש לו {self._hn}, רק {total} נק\'. פס.\nחוזה: 4NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                    ok=True)
        else:
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(
                f'✓ נכון! מחשב יש לו {self._hn}, רק {total} נק\'. פס.\nחוזה: 4NT.\nסה״כ {hs}+{self._hn}={total} נקודות.',
                ok=True)

    # ── Mode E — RKCB ─────────────────────────────────────────────────────

    def _setup_mode_e(self, deal=True):
        if deal:
            self.hands = deal_slam_nt_mode_e()
        open_bid, _ = _opening_bid(self.hands['N'])
        self._e_open_bid = open_bid

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid(open_bid)
        self.app.auction_widget.add_bid('Pass')

        self._stage = 'e_bid1'
        self._tries = 0

        self.app.set_instruction_table(
            f'מחשב פתח {open_bid}. מה תכריז?',
            [(f'1{_S["S"]}', f'5+ קלפי {_S["S"]}, 4+ {_S["H"]}, יד חזקה')]
        )
        self.app.bidding_box.set_last_bid(open_bid)

    def _handle_e_bid1(self, bid):
        correct = f'1{_S["S"]}'
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            self.app.auction_widget.add_bid('1NT')                # N
            self.app.auction_widget.add_bid('Pass')               # E
            self._stage = 'e_bid2'
            self._tries = 0
            self.app.set_instruction_table(
                f'מחשב חזר 1NT. מה תכריז?',
                [(f'3{_S["H"]}', f'4 קלפי {_S["H"]}, יד חזקה')]
            )
            self.app.bidding_box.set_last_bid('1NT')
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('1NT')
                self.app.auction_widget.add_bid('Pass')
                self._stage = 'e_bid2'
                self._tries = 0
                self.app.set_instruction_table(
                    f'מחשב חזר 1NT. מה תכריז?',
                    [(f'3{_S["H"]}', f'4 קלפי {_S["H"]}, יד חזקה')]
                )
                self.app.bidding_box.set_last_bid('1NT')
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.set_feedback(f'הנכון: {correct}.', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('1NT')
                self.app.auction_widget.add_bid('Pass')
                self._stage = 'e_bid2'
                self._tries = 0
                self.app.set_instruction_table(
                    f'מחשב חזר 1NT. מה תכריז?',
                    [(f'3{_S["H"]}', f'4 קלפי {_S["H"]}, יד חזקה')]
                )
                self.app.bidding_box.set_last_bid('1NT')

    def _handle_e_bid2(self, bid):
        correct = f'3{_S["H"]}'
        n_bid = f'3{_S["S"]}'
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            self.app.auction_widget.add_bid(n_bid)                # N
            self.app.auction_widget.add_bid('Pass')               # E
            self._stage = 'e_bid3'
            self._tries = 0
            self.app.set_instruction_table(
                f'מחשב תמך {n_bid}. מה תכריז?',
                [('4NT', f'RKCB — שאלת אסים בשליט {_S["S"]}')]
            )
            self.app.bidding_box.set_last_bid(n_bid)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid(n_bid)
                self.app.auction_widget.add_bid('Pass')
                self._stage = 'e_bid3'
                self._tries = 0
                self.app.set_instruction_table(
                    f'מחשב תמך {n_bid}. מה תכריז?',
                    [('4NT', f'RKCB — שאלת אסים בשליט {_S["S"]}')]
                )
                self.app.bidding_box.set_last_bid(n_bid)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.set_feedback(f'הנכון: {correct}.', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid(n_bid)
                self.app.auction_widget.add_bid('Pass')
                self._stage = 'e_bid3'
                self._tries = 0
                self.app.set_instruction_table(
                    f'מחשב תמך {n_bid}. מה תכריז?',
                    [('4NT', f'RKCB — שאלת אסים בשליט {_S["S"]}')]
                )
                self.app.bidding_box.set_last_bid(n_bid)

    def _handle_e_bid3(self, bid):
        correct = '4NT'
        n_rkcb, n_kc, _ = rkcb_response(self.hands['N'], 'S')
        s_kc = key_cards(self.hands['S'], 'S')
        total_kc = n_kc + s_kc
        total_hcp = hcp(self.hands['N']) + hcp(self.hands['S'])
        self._e_total_kc = total_kc
        self._e_total_hcp = total_hcp
        self._e_n_rkcb = n_rkcb
        explain = _RKCB_EXPLAIN.get(n_rkcb, '')

        def _go_next():
            self.app.auction_widget.add_bid('Pass')      # W
            self.app.auction_widget.add_bid(n_rkcb)      # N
            self.app.auction_widget.add_bid('Pass')       # E
            self._stage = 'e_bid4'
            self._tries = 0
            rows = [
                (f'6{_S["S"]}', f'5 אסים, או 4+33 נק\''),
                (f'5{_S["S"]}', '4 אסים ופחות מ-33, או פחות מ-4'),
            ]
            self.app.set_instruction_table(
                f'מחשב ענה {n_rkcb} ({explain}). מה תכריז?', rows)
            self.app.bidding_box.set_last_bid(n_rkcb)

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            _go_next()
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                _go_next()
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.set_feedback(f'הנכון: {correct}.', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)
                _go_next()

    def _handle_e_bid4(self, bid):
        total_kc = self._e_total_kc
        total_hcp = self._e_total_hcp
        if total_kc >= 5 or (total_kc == 4 and total_hcp >= 33):
            correct = f'6{_S["S"]}'
        else:
            correct = f'5{_S["S"]}'

        def _go_next(ok):
            self.app.auction_widget.add_bid('Pass')  # W
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            if correct == f'6{_S["S"]}':
                if total_kc >= 5:
                    reason = f'{total_kc} אסים'
                else:
                    reason = f'4 אסים + {total_hcp} נק\''
                msg = (f'✓ נכון! {reason}. חוזה: {correct}.' if ok
                       else f'הנכון: {correct}. {reason}. חוזה: {correct}.')
            else:
                if total_kc < 4:
                    reason = f'רק {total_kc} אסים'
                else:
                    reason = f'4 אסים, רק {total_hcp} נק\''
                msg = (f'✓ נכון! {reason} — עוצרים ב-{correct}.' if ok
                       else f'הנכון: {correct}. {reason}. חוזה: {correct}.')
            self._finish(msg, ok=ok)

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            _go_next(ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                _go_next(ok=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.set_feedback(f'הנכון: {correct}.', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)
                _go_next(ok=False)

    # ── סיום ──────────────────────────────────────────────────────────────

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
