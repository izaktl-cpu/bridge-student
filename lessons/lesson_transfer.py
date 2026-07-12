from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_1nt_transfer
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


class LessonTransfer(BaseLesson):
    """שיעור 5: טרנספר לאחר פתיחת 1NT של המחשב"""

    TITLE = 'שיעור 5. טרנספר'
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonTransfer
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def _correct_message(self, final, extra_line=''):
        h = hcp(self.hands['S'])
        lines = [self._next_opener(), f'יש לך {h} נקודות']
        if extra_line:
            lines.append(extra_line)
        lines += ['ההכרזה הנכונה', final]
        return '\n'.join(lines)

    def _wrong_message(self, correct, extra_line=''):
        h = hcp(self.hands['S'])
        lines = [f'יש לך {h} נקודות']
        if extra_line:
            lines.append(extra_line)
        lines += ['ההכרזה הנכונה', correct]
        return '\n'.join(lines)

    def start(self):
        if not self._replaying:
            self.hands = deal_robot_opens_1nt_transfer()
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
            ('2♦',  '5+ קלפי ♥'),
            ('2♥',  '5+ קלפי ♠'),
            ('2NT', '8-9 נקודות בלי מייג׳ור חמישייה'),
            ('3NT', '10+ נקודות בלי מייג׳ור חמישייה'),
            ('פס',  '0-7 נקודות בלי מייג׳ור חמישייה'),
        ]
        self.app.set_instruction_table('מה תכריז', self._panel_rows)

    def on_student_bid(self, bid):
        if self._handle_close(bid): return
        if self._stage == 'respond':
            self._handle_respond(bid)
        elif self._stage == 'transfer_cont':
            self._handle_transfer_cont(bid)

    # ── שלב 1: טרנספר ─────────────────────────────────────────────────────

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
        if d['H'] >= 5:
            return '2♦'
        if d['S'] >= 5:
            return '2♥'
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
        elif bid == '2♦':
            self._do_transfer('♥')
        elif bid == '2♥':
            self._do_transfer('♠')
        else:
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(message, ok=False)

    # ── שלב 2: אחרי השלמת הטרנספר ────────────────────────────────────────

    def _do_transfer(self, target_sym):
        self._transfer_sym = target_sym
        response_bid = '2♥' if target_sym == '♥' else '2♠'

        self.app.auction_widget.add_bid(response_bid)  # N
        self.app.auction_widget.add_bid('Pass')        # E

        self._stage = 'transfer_cont'
        self._tries = 0

        h = hcp(self.hands['S'])
        key = 'H' if target_sym == '♥' else 'S'
        suit_len = distribution(self.hands['S'])[key]
        self._panel_rows = [
            ('פס',                '0-7 נקודות'),
            ('2NT',               f'8-9 נקודות 5 קלפי {target_sym} בדיוק'),
            (f'3{target_sym}',    f'8-9 נקודות 6+ קלפי {target_sym}'),
            ('3NT',               f'10+ נקודות 5 קלפי {target_sym} בדיוק'),
            (f'4{target_sym}',    f'10+ נקודות 6+ קלפי {target_sym}'),
        ]
        self.app.set_instruction_table(
            f'יש {suit_len} קלפי {target_sym} ו-{h} נקודות\nמה תכריז',
            self._panel_rows,
        )
        self.app.bidding_box.set_last_bid(response_bid)

    def _calc_transfer_cont(self):
        h = hcp(self.hands['S'])
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        suit_len = distribution(self.hands['S'])[key]
        if h <= 7:
            return 'Pass'
        if h <= 9:
            return '2NT' if suit_len == 5 else f'3{sym}'
        # 10+
        return '3NT' if suit_len == 5 else f'4{sym}'

    def _handle_transfer_cont(self, bid):
        correct = self._calc_transfer_cont()
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        suit_len = distribution(self.hands['S'])[key]

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            if bid == 'Pass':
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(self._correct_message(f'2{sym}'), ok=True)
            elif bid == f'4{sym}':
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(self._correct_message(f'4{sym}', extra_line=f'יש {suit_len} קלפי {sym}'), ok=True)
            elif bid == f'3{sym}':
                self._after_3m(correct, ok=True)
            elif bid == '2NT':
                self._after_2nt(correct, ok=True)
            elif bid == '3NT':
                self._after_3nt(correct, ok=True)
        else:
            self._tries += 1
            if self._tries < 3:
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self._finish(f'{self._wrong_message(correct)}', ok=False)

    # ── תגובות N ──────────────────────────────────────────────────────────

    def _after_2nt(self, correct, ok=True):
        """S הכריז 2NT. 8-9 נקודות, 5 קלפים."""
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        north_fit = distribution(self.hands['N'])[key]
        hn = hcp(self.hands['N'])
        fit_line = f'יש 5 קלפי {sym}'
        msg_fn = self._correct_message if ok else self._wrong_message
        if hn <= 16:
            self.app.auction_widget.add_bid('Pass')      # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._finish(msg_fn(correct if not ok else '2NT', extra_line=fit_line), ok=ok)
        elif north_fit >= 3:
            north_bid = f'4{sym}'
            self.app.auction_widget.add_bid(north_bid)  # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._start_closing(msg_fn(correct if not ok else north_bid, extra_line=fit_line), ok=ok)
        else:
            self.app.auction_widget.add_bid('3NT')       # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._start_closing(msg_fn(correct if not ok else '3NT', extra_line=fit_line), ok=ok)

    def _after_3m(self, correct, ok=True):
        """S הכריז 3M. 8-9 נקודות, 6+ קלפים."""
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        north_fit = distribution(self.hands['N'])[key]
        hn = hcp(self.hands['N'])
        suit_len = distribution(self.hands['S'])[key]
        fit_line = f'יש {suit_len} קלפי {sym}'
        msg_fn = self._correct_message if ok else self._wrong_message
        if hn >= 17 and north_fit >= 3:
            north_bid = f'4{sym}'
            self.app.auction_widget.add_bid(north_bid)  # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._start_closing(msg_fn(correct if not ok else north_bid, extra_line=fit_line), ok=ok)
        else:
            self.app.auction_widget.add_bid('Pass')      # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._finish(msg_fn(correct if not ok else f'3{sym}', extra_line=fit_line), ok=ok)

    def _after_3nt(self, correct, ok=True):
        """S הכריז 3NT. 10+ נקודות, 5 קלפים."""
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        north_fit = distribution(self.hands['N'])[key]
        fit_line = f'יש 5 קלפי {sym}'
        msg_fn = self._correct_message if ok else self._wrong_message
        if north_fit >= 3:
            north_bid = f'4{sym}'
            self.app.auction_widget.add_bid(north_bid)  # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._start_closing(msg_fn(correct if not ok else north_bid, extra_line=fit_line), ok=ok)
        else:
            self.app.auction_widget.add_bid('Pass')      # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._finish(msg_fn(correct if not ok else '3NT', extra_line=fit_line), ok=ok)

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
