import random
from lessons.base import BaseLesson
from engine.deal_constraints import (deal_robot_opens_2nt_stayman,
                                      deal_robot_opens_2nt_transfer,
                                      deal_robot_opens_2nt_nt)
from engine.scoring import hcp, distribution, key_cards
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


def _gerber_bid(aces):
    """תשובת גרבר לשאלת 4♣ (אסים בלבד): 0/4→4♦, 1→4♥, 2→4♠, 3→4NT."""
    return {0: '4♦', 1: '4♥', 2: '4♠', 3: '4NT', 4: '4♦'}[aces]


class LessonRobotOpens2NT(BaseLesson):
    """שיעור 6: סטיימן וטרנספר לאחר פתיחת 2NT של המחשב (20-22 HCP)"""

    TITLE = 'שיעור 6. 2NT'
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonRobotOpens2NT
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
            r = random.random()
            if r < 0.25:
                self._mode = 'nt'
                self.hands = deal_robot_opens_2nt_nt()
            elif r < 0.625:
                self._mode = 'stayman'
                self.hands = deal_robot_opens_2nt_stayman()
            else:
                self._mode = 'transfer'
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

        self._panel_rows = [
            ('3♦',  '5+ קלפי ♥'),
            ('3♥',  '5+ קלפי ♠'),
            ('3♣',  '5+ נקודות עם רביעייה במייג׳ור'),
            ('3NT', '5-10 נקודות מאוזן'),
            ('4♣',  '11-12 נקודות מאוזן שאלת אסים'),
            ('פס',  '0-4 נקודות'),
        ]
        self.app.set_instruction_table('מה תכריז', self._panel_rows)
        self.app.bidding_box.set_last_bid('2NT')

    def on_student_bid(self, bid):
        if self._handle_close(bid): return
        if self._stage == 'respond':
            self._handle_respond(bid)
        elif self._stage == 'stayman_cont':
            self._handle_stayman_cont(bid)
        elif self._stage == 'transfer_cont':
            self._handle_transfer_cont(bid)
        elif self._stage == 'gerber':
            self._handle_gerber(bid)

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
        if d['H'] >= 5:
            return '3♦'
        if d['S'] >= 5:
            return '3♥'
        if h >= 5 and (d['H'] == 4 or d['S'] == 4):
            return '3♣'
        if h <= 4:
            return 'Pass'
        if h >= 11:
            return '4♣'    # 11-12 מאוזן בלי מייג׳ור — גרבר, שאלת אסים
        return '3NT'       # 5-10

    def _execute_first_bid(self, bid, message):
        if bid == 'Pass':
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(message, ok=True)
        elif bid == '3NT':
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(message, ok=True)
        elif bid == '4♣':
            # S ו-W (Pass) כבר נוספו ב-_handle_respond
            self._do_gerber_4c()
        elif bid == '3♣':
            self._do_stayman()
        elif bid == '3♦':
            self._do_transfer('♥')
        elif bid == '3♥':
            self._do_transfer('♠')
        else:
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(message, ok=False)

    # ── סטיימן ────────────────────────────────────────────────────────────

    def _do_stayman(self):
        d_n = distribution(self.hands['N'])
        if d_n['H'] >= 4:
            self._stayman_reply = '3♥'
        elif d_n['S'] >= 4:
            self._stayman_reply = '3♠'
        else:
            self._stayman_reply = '3♦'

        # S bid 3♣ and W Pass already added; now N replies
        self.app.auction_widget.add_bid(self._stayman_reply)  # N
        self.app.auction_widget.add_bid('Pass')               # E

        self._stage = 'stayman_cont'
        self._tries = 0

        r = self._stayman_reply
        reply_text = {'3♦': 'אין מיגור עיקרי', '3♥': 'יש לו 4 קלפי ♥', '3♠': 'יש לו 4 קלפי ♠ אין 4 קלפי ♥'}[r]
        fit = self._has_fit()
        fit_suit = self._fit_suit()
        if fit:
            self._panel_rows = [
                (f'4{fit_suit}', '5-10 נקודות משחק מלא'),
                ('4♣',           '11-12 נקודות שאלת אסים'),
            ]
        else:
            self._panel_rows = [
                ('3NT', '5-10 נקודות'),
                ('4♣',  '11-12 נקודות שאלת אסים'),
            ]
        self.app.set_instruction_table(f'{reply_text}\nמה תכריז', self._panel_rows)
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
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            if correct == '4♣':
                self._do_gerber_4c()
            elif correct.startswith('4'):  # 4M התאמה
                self.app.auction_widget.add_bid('Pass')           # N
                self.app.auction_widget.add_bid('Pass')           # E
                self._finish(self._correct_message(bid), ok=True)
            else:  # 3NT. check if N corrects to 4♠
                self._after_3nt_no_fit(correct, ok=True)
        else:
            self._tries += 1
            if self._tries < 3:
                self.app.set_feedback('נסה שוב', ok=False)
                self.app.bidding_box.set_last_bid(self._stayman_reply)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self._finish(f'{self._wrong_message(correct)}', ok=False)

    def _calc_stayman_cont(self):
        h = hcp(self.hands['S'])
        if self._has_fit():
            return '4♣' if h >= 11 else f'4{self._fit_suit()}'
        return '4♣' if h >= 11 else '3NT'

    def _do_gerber_4c(self):
        """S הכריז 4♣ גרבר שאלת אסים. N עונה כמה אסים בגובה 4.
        (S ו-W Pass כבר נוספו למכרז לפני הקריאה.)"""
        # trump=None → key_cards סופר אסים בלבד. 0/4→4♦, 1→4♥, 2→4♠, 3→4NT.
        n_aces = key_cards(self.hands['N'], None)
        self._n_ace_response    = _gerber_bid(n_aces)
        self._gerber_total_aces = n_aces + key_cards(self.hands['S'], None)

        self.app.auction_widget.add_bid(self._n_ace_response)  # N עונה אסים
        self.app.auction_widget.add_bid('Pass')                # E

        self._stage = 'gerber'
        self._tries = 0
        explain = {'4♦': '0 או 4 אסים', '4♥': '1 אס',
                   '4♠': '2 אסים', '4NT': '3 אסים'}[self._n_ace_response]
        # סגירה נמוכה. אם N ענה 4NT (3 אסים) — 4NT כבר תפוס, סוגרים בפס.
        low = 'פס' if self._n_ace_response == '4NT' else '4NT'
        self._panel_rows = [
            ('6NT', '4 אסים ו-32+ נקודות משותפות'),
            (low,   'חסר אס או פחות מ-32 נקודות'),
        ]
        self.app.set_instruction_table(
            f'N ענה {self._n_ace_response}\n{explain}\nמה תכריז', self._panel_rows)
        self.app.bidding_box.set_last_bid(self._n_ace_response)

    def _handle_gerber(self, bid):
        total    = self._gerber_total_aces
        combined = hcp(self.hands['N']) + hcp(self.hands['S'])
        if total >= 4 and combined >= 32:
            correct = '6NT'
        else:
            # חסר אס או מעט נקודות — סוגרים נמוך. אם N ענה 4NT סוגרים בפס.
            correct = 'Pass' if self._n_ace_response == '4NT' else '4NT'
        extra   = f'{total} אסים {combined} נקודות משותפות'
        display = '4NT' if correct == 'Pass' else correct
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            if bid != 'Pass':
                self.app.auction_widget.add_bid('Pass')           # N
                self.app.auction_widget.add_bid('Pass')           # E
            self._finish(self._correct_message(display, extra_line=extra), ok=True)
        else:
            self._tries += 1
            if self._tries < 3:
                self.app.set_feedback('נסה שוב', ok=False)
                self.app.bidding_box.set_last_bid(self._n_ace_response)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self._finish(self._wrong_message(display, extra_line=extra), ok=False)

    def _after_3nt_no_fit(self, correct, ok=True):
        # S=3NT and W=Pass already added; check if N corrects to 4♠
        msg_fn = self._correct_message if ok else self._wrong_message
        if self._stayman_reply == '3♥':
            d_n = distribution(self.hands['N'])
            d_s = distribution(self.hands['S'])
            if d_n['S'] >= 4 and d_s['S'] >= 4:
                self.app.auction_widget.add_bid('4♠')   # N corrects
                self.app.auction_widget.add_bid('Pass')  # E
                self._start_closing(
                    msg_fn(correct if not ok else '4♠',
                           extra_line='אין התאמה ב-♥, יש התאמה ב-♠'), ok=ok)
                return
        self.app.auction_widget.add_bid('Pass')  # N
        self.app.auction_widget.add_bid('Pass')  # E
        self._finish(msg_fn(correct if not ok else '3NT'), ok=ok)

    # ── טרנספר ────────────────────────────────────────────────────────────

    def _do_transfer(self, target_sym):
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
        self._panel_rows = [
            ('פס',              '0-4 נקודות'),
            ('3NT',             f'5+ נקודות 5 קלפי {target_sym} בדיוק'),
            (f'4{target_sym}',  f'5+ נקודות 6+ קלפי {target_sym}'),
        ]
        self.app.set_instruction_table(
            f'יש {suit_len} קלפי {target_sym} ו-{h} נקודות\nמה תכריז',
            self._panel_rows,
        )
        self.app.bidding_box.set_last_bid(response_bid)

    def _handle_transfer_cont(self, bid):
        correct = self._calc_transfer_cont()
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        suit_len = distribution(self.hands['S'])[key]

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            if bid == 'Pass':
                self.app.auction_widget.add_bid('Pass')           # N
                self.app.auction_widget.add_bid('Pass')           # E
                self._finish(self._correct_message(f'3{sym}'), ok=True)
            elif bid == '3NT':
                self._do_transfer_3nt(correct, ok=True)
            else:  # 4♥ or 4♠
                self.app.auction_widget.add_bid('Pass')           # N
                self.app.auction_widget.add_bid('Pass')           # E
                self._finish(self._correct_message(bid, extra_line=f'יש {suit_len} קלפי {sym}'), ok=True)
        else:
            self._tries += 1
            if self._tries < 3:
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self._finish(f'{self._wrong_message(correct)}', ok=False)

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

    def _do_transfer_3nt(self, correct, ok=True):
        # S=3NT and W=Pass already added by _handle_transfer_cont
        sym = self._transfer_sym
        key = 'H' if sym == '♥' else 'S'
        north_fit = distribution(self.hands['N'])[key]
        msg_fn = self._correct_message if ok else self._wrong_message
        fit_line = f'יש 5 קלפי {sym}'
        if north_fit >= 3:
            north_bid = f'4{sym}'
            self.app.auction_widget.add_bid(north_bid)  # N מתקן
            self.app.auction_widget.add_bid('Pass')      # E
            self._start_closing(msg_fn(correct if not ok else north_bid, extra_line=fit_line), ok=ok)
        else:
            self.app.auction_widget.add_bid('Pass')  # N עובר
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(msg_fn(correct if not ok else '3NT', extra_line=fit_line), ok=ok)

    # ── סיום ───────────────────────────────────────────────────────────────

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        # בסוף כל יד — מציגים את טבלת האפשרויות הרלוונטית (נכון וגם טעות)
        rows = getattr(self, '_panel_rows', None)
        if rows:
            self.app.add_immediate_table(rows)
        self.app.set_feedback(message, ok=ok)
        self.app.table.show_hands(self.hands, visible=('N', 'E', 'S', 'W'))
        self.app.show_new_deal_button()
