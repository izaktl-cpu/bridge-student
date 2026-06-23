from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_1nt_transfer
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_retry, msg_chose_wrong

_S = SUIT_SYMBOLS


class LessonTransfer(BaseLesson):
    """שיעור 5: טרנספר לאחר פתיחת 1NT של המחשב"""

    TITLE = 'שיעור 5. טרנספר'

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

        self.app.set_instruction('מחשב פתח 1NT. מה תכריז?')
        self.app.bidding_box.set_last_bid('1NT')

    def on_student_bid(self, bid):
        if self._handle_close(bid): return
        if self._stage == 'respond':
            self._handle_respond(bid)
        elif self._stage == 'transfer_cont':
            self._handle_transfer_cont(bid)

    # ── שלב 1: טרנספר ─────────────────────────────────────────────────────

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
        if d['H'] >= 5:
            return '2♦', f'יש {h} נקודות, {d["H"]} קלפי ♥. טרנספר ל-♥'
        if d['S'] >= 5:
            return '2♥', f'יש {h} נקודות, {d["S"]} קלפי ♠. טרנספר ל-♠'
        if h <= 7:
            return 'Pass', f'יש {h} נקודות. מכריזים פס'
        if h <= 9:
            return '2NT', f'יש {h} נקודות. מזמינים ל-3NT'
        return '3NT', f'יש {h} נקודות. מכריזים משחק מלא'

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
        elif bid == '2♦':
            self._do_transfer('♥', why)
        elif bid == '2♥':
            self._do_transfer('♠', why)
        else:
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(f'{why}\nחוזה סופי: {bid}.', ok=False)

    # ── שלב 2: אחרי השלמת הטרנספר ────────────────────────────────────────

    def _do_transfer(self, target_sym, why):
        self._transfer_sym = target_sym
        response_bid = '2♥' if target_sym == '♥' else '2♠'

        self.app.auction_widget.add_bid(response_bid)  # N
        self.app.auction_widget.add_bid('Pass')        # E

        self._stage = 'transfer_cont'
        self._tries = 0

        h = hcp(self.hands['S'])
        key = 'H' if target_sym == '♥' else 'S'
        suit_len = distribution(self.hands['S'])[key]
        self.app.set_instruction_table(
            f'מחשב ענה {response_bid}. טרנספר הושלם.\nיש {suit_len} קלפי {target_sym} ו-{h} נקודות. מה תכריז?',
            [
                ('Pass',              '0-7 נקודות'),
                ('2NT',               f'8-9 נקודות, 5 קלפי {target_sym} בדיוק'),
                (f'3{target_sym}',    f'8-9 נקודות, 6+ קלפי {target_sym}'),
                ('3NT',               f'10+ נקודות, 5 קלפי {target_sym} בדיוק'),
                (f'4{target_sym}',    f'10+ נקודות, 6+ קלפי {target_sym}'),
            ]
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
        h = hcp(self.hands['S'])
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        suit_len = distribution(self.hands['S'])[key]

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            if bid == 'Pass':
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(f'✓ נכון!\nיש {h} נקודות. פס.\nחוזה סופי: 2{sym}.', ok=True)
            elif bid == f'4{sym}':
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(f'✓ נכון!\nיש {h} נקודות\nיש {suit_len} קלפי {sym}. יש משחק מלא.\nחוזה סופי: 4{sym}.', ok=True)
            elif bid == f'3{sym}':
                self._after_3m()
            elif bid == '2NT':
                self._after_2nt()
            elif bid == '3NT':
                self._after_3nt()
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                if bid == f'3{sym}':
                    self._after_3m(ok=False, prefix=f'בחרת {bid}.')
                elif bid == '2NT':
                    self._after_2nt(ok=False, prefix=f'בחרת {bid}.')
                elif bid == '3NT':
                    self._after_3nt(ok=False, prefix=f'בחרת {bid}.')
                else:
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(msg_chose_wrong(bid, correct), ok=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                expl = self._explain_wrong(bid, correct, h, suit_len, sym)
                if bid == f'3{sym}':
                    self._after_3m(ok=False, prefix=expl)
                elif bid == '2NT':
                    self._after_2nt(ok=False, prefix=expl)
                elif bid == '3NT':
                    self._after_3nt(ok=False, prefix=expl)
                else:
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(expl, ok=False)

    # ── תגובות N ──────────────────────────────────────────────────────────

    def _after_2nt(self, ok=True, prefix=''):
        """S הכריז 2NT. 8-9 נקודות, 5 קלפים."""
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        north_fit = distribution(self.hands['N'])[key]
        h = hcp(self.hands['S'])
        hn = hcp(self.hands['N'])
        base = prefix or f'✓ נכון!\nיש {h} נקודות\nיש 5 קלפי {sym}.'
        if hn <= 16:
            # 15-16. מסרב
            self.app.auction_widget.add_bid('Pass')      # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._finish(f'{base}\nמחשב יש לו {hn} נקודות. מסרב.\nחוזה סופי: 2NT.', ok=ok)
        elif north_fit >= 3:
            north_bid = f'4{sym}'
            self.app.auction_widget.add_bid(north_bid)  # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._start_closing(f'{base}\nמחשב יש לו {north_fit} קלפי {sym}. מקבל: {north_bid}.\nחוזה סופי: {north_bid}.', ok=ok)
        else:
            self.app.auction_widget.add_bid('3NT')       # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._start_closing(f'{base}\nמחשב יש לו {hn} נקודות. מקבל: 3NT.\nחוזה סופי: 3NT.', ok=ok)

    def _after_3m(self, ok=True, prefix=''):
        """S הכריז 3M. 8-9 נקודות, 6+ קלפים."""
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        north_fit = distribution(self.hands['N'])[key]
        h = hcp(self.hands['S'])
        hn = hcp(self.hands['N'])
        suit_len = distribution(self.hands['S'])[key]
        base = prefix or f'✓ נכון!\nיש {h} נקודות\nיש {suit_len} קלפי {sym}.'
        if hn >= 17 and north_fit >= 3:
            north_bid = f'4{sym}'
            self.app.auction_widget.add_bid(north_bid)  # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._start_closing(f'{base}\nמחשב יש לו {north_fit} קלפי {sym}. מקבל: {north_bid}.\nחוזה סופי: {north_bid}.', ok=ok)
        else:
            self.app.auction_widget.add_bid('Pass')      # N
            self.app.auction_widget.add_bid('Pass')      # E
            reason = f'יש לו {hn} נקודות' if hn <= 16 else f'יש לו {north_fit} קלפי {sym} בלבד'
            self._finish(f'{base}\nמחשב {reason}. מסרב.\nחוזה סופי: 3{sym}.', ok=ok)

    def _after_3nt(self, ok=True, prefix=''):
        """S הכריז 3NT. 10+ נקודות, 5 קלפים."""
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        north_fit = distribution(self.hands['N'])[key]
        h = hcp(self.hands['S'])
        base = prefix or f'✓ נכון!\nיש {h} נקודות\nיש 5 קלפי {sym}.'
        if north_fit >= 3:
            north_bid = f'4{sym}'
            self.app.auction_widget.add_bid(north_bid)  # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._start_closing(f'{base}\nמחשב יש לו {north_fit} קלפי {sym}. מתקן ל-{north_bid}.\nחוזה סופי: {north_bid}.', ok=ok)
        else:
            self.app.auction_widget.add_bid('Pass')      # N
            self.app.auction_widget.add_bid('Pass')      # E
            self._finish(f'{base}\nמחשב יש לו {north_fit} קלפי {sym} בלבד. עובר.\nחוזה סופי: 3NT.', ok=ok)

    def _explain_wrong(self, bid, correct, h, suit_len, sym):
        if correct == 'Pass':
            return f'✗ בחרת {bid}.\nיש {h} נקודות. מכריזים פס.\nהנכון: Pass.'
        if correct == '2NT':
            return f'✗ בחרת {bid}.\nיש {h} נקודות, יש 5 קלפי {sym}. מזמינים 2NT.\nהנכון: 2NT.'
        if correct == f'3{sym}':
            return f'✗ בחרת {bid}.\nיש {h} נקודות, יש {suit_len} קלפי {sym}. מכריזים 3{sym}.\nהנכון: 3{sym}.'
        if correct == '3NT':
            return f'✗ בחרת {bid}.\nיש {h} נקודות, יש 5 קלפי {sym}. מכריזים 3NT.\nהנכון: 3NT.'
        if correct == f'4{sym}':
            return f'✗ בחרת {bid}.\nיש {h} נקודות, יש {suit_len} קלפי {sym}. יש משחק מלא.\nהנכון: {correct}.'
        return f'✗ בחרת {bid}. הנכון: {correct}.'

    # ── סיום ───────────────────────────────────────────────────────────────

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
