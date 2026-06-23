import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_2nt_stayman, deal_robot_opens_2nt_transfer
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_retry, msg_chose_wrong, msg_correct_final, msg_contract_wrong

_S = SUIT_SYMBOLS


class LessonRobotOpens2NT(BaseLesson):
    """שיעור 6: סטיימן וטרנספר לאחר פתיחת 2NT של המחשב (20-22 HCP)"""

    TITLE = 'שיעור 6. 2NT'

    def start(self):
        if not self._replaying:
            self._mode = random.choice(['stayman', 'transfer'])
            if self._mode == 'stayman':
                self.hands = deal_robot_opens_2nt_stayman()
            else:
                self.hands = deal_robot_opens_2nt_transfer()
        self._replaying = False

        self._stage = 'respond'
        self._tries = 0
        self._awaiting_close = False

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid('2NT')
        self.app.auction_widget.add_bid('Pass')

        self.app.set_instruction_table(
            'מחשב פתח 2NT (20-22 נקודות). מה תכריז?',
            [
                ('3♣',  'סטיימן. 5+ נקודות, 2 רביעיות (אחת מיגור)'),
                ('3♦',  'טרנספר ל-♥. 5+ קלפי ♥'),
                ('3♥',  'טרנספר ל-♠. 5+ קלפי ♠'),
                ('3NT', '5+ נקודות, מאוזן'),
                ('Pass', '0-4 נקודות\nאין 5 קלפים במיגורים'),
            ]
        )
        self.app.bidding_box.set_last_bid('2NT')

    def on_student_bid(self, bid):
        if self._handle_close(bid): return
        if self._stage == 'respond':
            self._handle_respond(bid)
        elif self._stage == 'stayman_cont':
            self._handle_stayman_cont(bid)
        elif self._stage == 'transfer_cont':
            self._handle_transfer_cont(bid)

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
        if d['H'] >= 5:
            return '3♦', f'יש {h} נקודות, {d["H"]} קלפי ♥. טרנספר ל-♥'
        if d['S'] >= 5:
            return '3♥', f'יש {h} נקודות, {d["S"]} קלפי ♠. טרנספר ל-♠'
        if h >= 5 and (d['H'] == 4 or d['S'] == 4):
            return '3♣', f'יש {h} נקודות, 4 קלפי מיגור. סטיימן 3♣'
        if h <= 4:
            return 'Pass', f'יש {h} נקודות. מכריזים פס'
        return '3NT', f'יש {h} נקודות. מכריזים 3NT'

    def _execute_first_bid(self, bid, why):
        ok = not why.startswith('הנכון')
        prefix = '✓ ' if ok else ''
        if bid == 'Pass':
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(f'{prefix}{why}\nחוזה סופי: 2NT.', ok=ok)
        elif bid == '3NT':
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(f'{prefix}{why}\nחוזה סופי: 3NT.', ok=ok)
        elif bid == '3♣':
            self._do_stayman(why)
        elif bid == '3♦':
            self._do_transfer('♥', why)
        elif bid == '3♥':
            self._do_transfer('♠', why)
        else:
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(f'{why}\nחוזה סופי: {bid}.', ok=False)

    # ── סטיימן ────────────────────────────────────────────────────────────

    def _do_stayman(self, why):
        d_n = distribution(self.hands['N'])
        if d_n['H'] >= 4:
            self._stayman_reply = '3♥'
        elif d_n['S'] >= 4:
            self._stayman_reply = '3♠'
        else:
            self._stayman_reply = '3♦'

        self._stayman_why = why
        # S bid 3♣ and W Pass already added; now N replies
        self.app.auction_widget.add_bid(self._stayman_reply)  # N
        self.app.auction_widget.add_bid('Pass')               # E

        self._stage = 'stayman_cont'
        self._tries = 0

        r = self._stayman_reply
        reply_text = {'3♦': 'אין מיגור עיקרי', '3♥': 'יש לו ♥', '3♠': 'יש לו ♠, אין ♥'}[r]
        fit = self._has_fit()
        fit_suit = self._fit_suit()
        if fit:
            self.app.set_instruction_table(
                f'מחשב ענה {r} ({reply_text}). מה תכריז?',
                [
                    (f'4{fit_suit}', f'יש התאמה ב-{fit_suit}. משחק מלא'),
                ]
            )
        else:
            self.app.set_instruction_table(
                f'מחשב ענה {r} ({reply_text}). מה תכריז?',
                [
                    ('3NT', 'אין התאמה. יש 5+ נקודות, לך ל-3NT'),
                ]
            )
        self.app.bidding_box.set_last_bid(self._stayman_reply)

    def _has_fit(self):
        d = distribution(self.hands['S'])
        r = self._stayman_reply
        if r == '3♥' and d['H'] >= 4:
            return True
        if r == '3♠' and d['S'] >= 4:
            return True
        return False

    def _fit_suit(self):
        return '♥' if self._stayman_reply == '3♥' else '♠'

    def _stayman_cont_options(self):
        if self._has_fit():
            suit = self._fit_suit()
            return [f'4{suit}', '3NT']
        return ['3NT']

    def _handle_stayman_cont(self, bid):
        correct = self._calc_stayman_cont()
        h = hcp(self.hands['S'])
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            if correct.startswith('4'):
                self.app.auction_widget.add_bid('Pass')           # N
                self.app.auction_widget.add_bid('Pass')           # E
                self._finish(msg_correct_final(bid), ok=True)
            else:  # 3NT. check if N corrects to 4♠
                self._after_3nt_no_fit(was_correct=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                if bid.startswith('4'):
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(msg_contract_wrong(bid, correct), ok=False)
                else:
                    self._after_3nt_no_fit(was_correct=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
                self.app.bidding_box.set_last_bid(self._stayman_reply)
            else:
                self.app.set_feedback(f'הנכון: {correct}.', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                if bid.startswith('4'):
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(msg_contract_wrong(bid, correct), ok=False)
                else:
                    self._after_3nt_no_fit(was_correct=False)

    def _calc_stayman_cont(self):
        if self._has_fit():
            return f'4{self._fit_suit()}'
        return '3NT'

    def _after_3nt_no_fit(self, was_correct=True):
        # S=3NT and W=Pass already added; check if N corrects to 4♠
        prefix = '✓ נכון! ' if was_correct else ''
        if self._stayman_reply == '3♥':
            d_n = distribution(self.hands['N'])
            d_s = distribution(self.hands['S'])
            if d_n['S'] >= 4 and d_s['S'] >= 4:
                self.app.auction_widget.add_bid('4♠')   # N corrects
                self.app.auction_widget.add_bid('Pass')  # E
                self._start_closing(
                    f'{prefix}אין התאמה ב-♥, אבל יש התאמה ב-♠.\n'
                    f'מחשב מתקן ל-4♠. חוזה סופי: 4♠.', ok=was_correct)
                return
        self.app.auction_widget.add_bid('Pass')  # N
        self.app.auction_widget.add_bid('Pass')  # E
        self._finish(f'{prefix}חוזה סופי: 3NT.', ok=was_correct)

    # ── טרנספר ────────────────────────────────────────────────────────────

    def _do_transfer(self, target_sym, why):
        self._transfer_sym = target_sym
        response_bid = '3♥' if target_sym == '♥' else '3♠'

        # S transfer bid and W Pass already added; now N completes transfer
        self.app.auction_widget.add_bid(response_bid)  # N
        self.app.auction_widget.add_bid('Pass')        # E

        self._stage = 'transfer_cont'
        self._tries = 0

        h = hcp(self.hands['S'])
        d = distribution(self.hands['S'])
        suit_len = d['H'] if target_sym == '♥' else d['S']
        self.app.set_instruction_table(
            f'מחשב ענה {response_bid}. טרנספר הושלם.\nיש {suit_len} קלפי {target_sym} ו-{h} נקודות.',
            [
                ('Pass',            'עד 4 נקודות. עצור ב-3'),
                ('3NT',             f'5+ נקודות, 5 קלפי {target_sym} בדיוק. הפותח יבחר'),
                (f'4{target_sym}',  f'5+ נקודות, 6+ קלפי {target_sym}'),
            ]
        )
        self.app.bidding_box.set_last_bid(response_bid)

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
                self.app.auction_widget.add_bid('Pass')           # N
                self.app.auction_widget.add_bid('Pass')           # E
                self._finish(msg_correct_final(f'3{sym}'), ok=True)
            elif bid == '3NT':
                self._do_transfer_3nt()
            else:  # 4♥ or 4♠
                self.app.auction_widget.add_bid('Pass')           # N
                self.app.auction_widget.add_bid('Pass')           # E
                self._finish(f'✓ נכון!\nיש {suit_len} קלפי {sym}. יש משחק מלא.\nחוזה סופי: {bid}.', ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                if bid == '3NT':
                    self._do_transfer_3nt(was_correct=False)
                elif bid == 'Pass':
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(msg_contract_wrong(f'3{sym}', correct), ok=False)
                else:
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(msg_contract_wrong(bid, correct), ok=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.set_feedback(f'הנכון: {correct}.', ok=False)
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                if bid == '3NT':
                    self._do_transfer_3nt(was_correct=False)
                elif bid == 'Pass':
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(msg_contract_wrong(f'3{sym}', correct), ok=False)
                else:
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(msg_contract_wrong(bid, correct), ok=False)

    def _calc_transfer_cont(self):
        h = hcp(self.hands['S'])
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        suit_len = distribution(self.hands['S'])[key]
        if h <= 4:
            return 'Pass'
        if suit_len == 5:
            return '3NT'
        return f'4{sym}'

    def _do_transfer_3nt(self, was_correct=True):
        # S=3NT and W=Pass already added by _handle_transfer_cont
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        north_fit = distribution(self.hands['N'])[key]
        prefix = '✓ נכון! ' if was_correct else ''

        ok_tag = 'נכון! ✓\n' if was_correct else ''
        if north_fit >= 3:
            north_bid = f'4{sym}'
            self.app.auction_widget.add_bid(north_bid)  # N מתקן
            self.app.auction_widget.add_bid('Pass')      # E
            self._start_closing(
                f'{ok_tag}'
                f'יש 5 קלפי {sym}. הכרזת 3NT.\n'
                f'מחשב יש לו {north_fit} קלפי {sym}. מתקן ל-{north_bid}.\n'
                f'חוזה סופי: {north_bid}.', ok=was_correct)
        else:
            self.app.auction_widget.add_bid('Pass')  # N עובר
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(
                f'{ok_tag}'
                f'יש 5 קלפי {sym}. הכרזת 3NT.\n'
                f'מחשב יש לו {north_fit} קלפי {sym} בלבד. עובר.\n'
                f'חוזה סופי: 3NT.', ok=was_correct)

    # ── סיום ───────────────────────────────────────────────────────────────

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.table.show_hands(self.hands, visible=('N', 'E', 'S', 'W'))
        self.app.show_new_deal_button()
