import random
from lessons.base import BaseLesson
from engine.deal_constraints import (
    deal_fourth_suit, deal_fourth_suit_diamond,
    deal_fourth_suit_heart, deal_stopper_ask,
)
from engine.fourth_suit import (
    compute_fourth_suit, s_correct_bid, n_respond_fsf, s_final_bid
)
from engine.scoring import hcp, has_stopper
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_retry

_S = SUIT_SYMBOLS
_SYM = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}
_CODE = {'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠'}

# ── תצורות מסלול ─────────────────────────────────────────────────────────
_AUCTION_CONFIGS = [
    # 1♣ (N). 1♥ (S). 1♠ (N). 2♦ (S, FSF)
    {'type': 'fsf',
     'deal_fn': deal_fourth_suit,
     'n_bid': '1♣', 'n_rebid': '1♠', 's_response': '1♥',
     's_suit': 'H', 'opener_suit': 'C'},
    # 1♦ (N). 1♥ (S). 1♠ (N). 2♣ (S, FSF)
    {'type': 'fsf',
     'deal_fn': deal_fourth_suit_diamond,
     'n_bid': '1♦', 'n_rebid': '1♠', 's_response': '1♥',
     's_suit': 'H', 'opener_suit': 'D'},
    # 1♥ (N). 1♠ (S). 2♣ (N). 2♦ (S, FSF)
    {'type': 'fsf',
     'deal_fn': deal_fourth_suit_heart,
     'n_bid': '1♥', 'n_rebid': '2♣', 's_response': '1♠',
     's_suit': 'S', 'opener_suit': 'H'},
    # 1♦ (N). 2♦ (S, תמיכה חלשה). 3♥ (N, שאלת עוצר). ? (S)
    {'type': 'stopper_ask',
     'deal_fn': deal_stopper_ask,
     'n_bid': '1♦', 's_raise': '2♦', 'n_ask': '3♥',
     'ask_sym': '♥'},
]


def _suit_of(bid):
    for ch, s in _SYM.items():
        if ch in bid:
            return s
    return None


def _hand_eval(hand):
    h = hcp(hand)
    return f'{h} נק׳ גבוהות'


def _stopper_reply(hand):
    """תגובה נכונה של S לשאלת עוצר 3♥ (S הכריז 2♦, N שאל 3♥)."""
    if has_stopper(hand, 'H'):
        return '3NT', 'יש עוצר ♥. 3NT'
    else:
        return '4♦', 'אין עוצר ♥. חוזרים ל-♦'


class LessonFourthSuit(BaseLesson):
    """שיעור 13: צבע רביעי ושאלות לעוצר"""

    TITLE = 'שיעור 13. צבע רביעי'

    def start(self):
        if not self._replaying:
            for _ in range(10):
                cfg = random.choice(_AUCTION_CONFIGS)
                try:
                    self.hands = cfg['deal_fn']()
                    self._cfg = cfg
                    break
                except RuntimeError:
                    continue
            else:
                cfg = _AUCTION_CONFIGS[0]
                self._cfg = cfg
                self.hands = cfg['deal_fn']()
        self._replaying = False
        self._tries = 0

        cfg = self._cfg
        self._n_bid = cfg['n_bid']

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid(self._n_bid)   # N: פתיחה
        self.app.auction_widget.add_bid('Pass')          # E
        self.app.bidding_box.set_last_bid(self._n_bid)

        if cfg['type'] == 'fsf':
            self._n_rebid     = cfg['n_rebid']
            self._s_expected  = cfg['s_response']
            self._opener_suit = cfg['opener_suit']
            self._s_suit      = cfg['s_suit']
            self._stage = 'response'
            s_sym    = _CODE[cfg['s_suit']]
            eval_txt = _hand_eval(self.hands['S'])
            self.app.set_instruction_table(
                f'{eval_txt}\nמה תכריז?',
                [(cfg['s_response'], f'4+ קלפי {s_sym}. כריזת צבע חדש')]
            )

        else:  # stopper_ask
            self._s_raise = cfg['s_raise']
            self._n_ask   = cfg['n_ask']
            self._ask_sym = cfg['ask_sym']
            self._stage = 'response'
            eval_txt = _hand_eval(self.hands['S'])
            self.app.set_instruction_table(
                f'{eval_txt}\nמה תכריז?',
                [('2♦', '6-10 נק׳, 5+ קלפי ♦. תמיכה חלשה')]
            )

    # ── ניתוב ─────────────────────────────────────────────────────────────

    def on_student_bid(self, bid):
        if self._stage == 'response':
            if self._cfg['type'] == 'fsf':
                self._handle_response_fsf(bid)
            else:
                self._handle_response_stopper_ask(bid)
        elif self._stage == 'fsf':
            self._handle_fsf(bid)
        elif self._stage == 'final':
            self._handle_final(bid)
        elif self._stage == 'stopper_reply':
            self._handle_stopper_reply(bid)

    # ── FSF שלב 0: תגובה ראשונה ──────────────────────────────────────────

    def _handle_response_fsf(self, bid):
        correct = self._s_expected
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self._s_bid1 = bid

            self.app.auction_widget.add_bid('Pass')           # W
            self.app.auction_widget.add_bid(self._n_rebid)    # N: ריבאד
            self.app.auction_widget.add_bid('Pass')            # E

            self._correct_fsf, self._fsf_expl, _ = s_correct_bid(
                self.hands['S'], self._n_bid, self._s_bid1, self._n_rebid)

            self.app.bidding_box.set_last_bid(self._n_rebid)
            self._tries = 0
            self._stage = 'fsf'

            _, fsym, _ = compute_fourth_suit(
                self._n_bid, self._s_bid1, self._n_rebid)
            eval_txt = _hand_eval(self.hands['S'])
            self.app.set_instruction_table(
                f'{eval_txt}\nמה תכריז?',
                [
                    (f'{self._correct_fsf}',
                     f'11+ נק׳, שואל עוצר ב-{fsym}\n(צבע רביעי. לא טבעי!)'),
                    ('3NT', '13+ נק׳, יש לי עוצר. ישיר'),
                    ('2NT', '11-12 נק׳, יש עוצר. הזמנה'),
                ]
            )
        else:
            s_sym = _CODE[self._s_suit]
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.set_feedback(f'נסה שוב. רמז: יש לך 4+ קלפי {s_sym}.', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(
                    f'טעית בפעם השנייה.\nבחרת {bid}\nהנכון: {correct}. יש לך 4+ קלפי {s_sym}',
                    ok=False, correct_answer=correct)

    # ── FSF שלב 1: הכרזת FSF ─────────────────────────────────────────────

    def _handle_fsf(self, bid):
        correct = self._correct_fsf

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self._s_fsf_bid = bid

            fs = _suit_of(bid)
            n_resp, n_why = n_respond_fsf(
                self.hands['N'], fs, self._opener_suit, self._s_suit)
            self._n_fsf_resp = n_resp
            self._n_fsf_why  = n_why

            self.app.auction_widget.add_bid('Pass')   # W
            self.app.auction_widget.add_bid(n_resp)    # N
            self.app.auction_widget.add_bid('Pass')    # E

            _, fsym, _ = compute_fourth_suit(
                self._n_bid, self._s_bid1, self._n_rebid)

            if n_resp == '3NT':
                self.app.auction_widget.add_bid('Pass')  # E
                self.app.auction_widget.add_bid('Pass')  # S
                self.app.auction_widget.add_bid('Pass')  # W
                self._finish(
                    f'נכון. הכרזת {bid}\n'
                    f'צבע רביעי. שואל עוצר ב-{fsym}, לא טבעי\n'
                    f'שותף {n_resp}. {n_why}\nמשחק מלא',
                    ok=True)
                return

            self._tries = 0
            self._stage = 'final'
            correct_final, _ = s_final_bid(self.hands['S'], n_resp, self._s_suit, self._opener_suit)
            self._correct_final = correct_final

            self.app.bidding_box.set_last_bid(n_resp)
            self._show_final_instruction(n_resp, fsym)

        else:
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                _, fsym, _ = compute_fourth_suit(
                    self._n_bid, self._s_bid1, self._n_rebid)
                self.app.set_feedback(
                    f'נסה שוב. רמז: הצבע הרביעי שלא הוכרז הוא {fsym}.', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                _, fsym, _ = compute_fourth_suit(
                    self._n_bid, self._s_bid1, self._n_rebid)
                self._finish(
                    f'טעית בפעם השנייה.\nבחרת {bid}\n'
                    f'הנכון: {correct}. צבע רביעי, שואל עוצר ב-{fsym}\n'
                    f'{self._fsf_expl}',
                    ok=False, correct_answer=correct)

    # ── FSF שלב 2: הכרזה אחרי תגובת N ───────────────────────────────────

    def _handle_final(self, bid):
        correct = self._correct_final
        n_resp  = self._n_fsf_resp

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            n_why   = self._n_fsf_why
            fsf_bid = self._s_fsf_bid
            _, fsym, _ = compute_fourth_suit(
                self._n_bid, self._s_bid1, self._n_rebid)
            self._finish(
                f'נכון! הכרזת {fsf_bid}\n'
                f'צבע רביעי. שואל עוצר ב-{fsym}, לא טבעי\n'
                f'שותף: {n_resp}. {n_why}\n'
                f'הכרזתך: {bid}',
                ok=True)
        else:
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.set_feedback(msg_retry(), ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                _, expl = s_final_bid(self.hands['S'], n_resp, self._s_suit, self._opener_suit)
                self._finish(
                    f'טעית בפעם השנייה.\nבחרת {bid}\nהנכון: {correct}. {expl}',
                    ok=False, correct_answer=correct)

    # ── Stopper Ask שלב 0: תמיכה 2♦ ─────────────────────────────────────

    def _handle_response_stopper_ask(self, bid):
        correct = self._s_raise
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)

            self.app.auction_widget.add_bid('Pass')        # W
            self.app.auction_widget.add_bid(self._n_ask)   # N: שאלת עוצר
            self.app.auction_widget.add_bid('Pass')         # E

            self._stopper_correct, self._stopper_expl = _stopper_reply(self.hands['S'])
            self._tries = 0
            self._stage = 'stopper_reply'

            self.app.bidding_box.set_last_bid(self._n_ask)
            eval_txt = _hand_eval(self.hands['S'])
            self.app.set_instruction_table(
                f'{eval_txt}\n'
                f'שאלת עוצר ב-{self._ask_sym}\nמה תכריז?',
                [
                    ('3NT', 'יש עוצר ♥. 3NT'),
                    ('4♦',  'אין עוצר ♥. חוזרים ל-♦'),
                ]
            )
        else:
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.set_feedback(
                    f'נסה שוב. רמז: עם 6-10 נק׳ ו-5+ קלפי ♦. תמיכה חלשה.',
                    ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(
                    f'טעית בפעם השנייה.\nבחרת {bid}\nהנכון: {correct}. 6-10 נק׳, 5+ קלפי ♦',
                    ok=False, correct_answer=correct)

    # ── Stopper Ask שלב 1: תגובה לשאלת עוצר ─────────────────────────────

    def _handle_stopper_reply(self, bid):
        correct = self._stopper_correct
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self.app.auction_widget.add_bid('Pass')   # W

            if bid == '3NT':
                # יש עוצר. S מכריז 3NT ישיר
                self.app.auction_widget.add_bid('Pass')  # E
                self.app.auction_widget.add_bid('Pass')  # S
                self.app.auction_widget.add_bid('Pass')  # W
                self._finish(
                    f'נכון!\n'
                    f'{self._n_bid}-{self._s_raise}-{self._n_ask}-3NT\n'
                    f'יש עוצר ♥. 3NT',
                    ok=True)
            else:  # 4♦. אין עוצר
                hn = hcp(self.hands['N'])
                hs = hcp(self.hands['S'])
                if hn + hs >= 28:
                    n_final = '5♦'
                    expl = f'{hn}+{hs}={hn+hs} נק׳. 5♦'
                else:
                    n_final = 'Pass'
                    expl = f'{hn}+{hs}={hn+hs} נק׳. פס'
                self.app.auction_widget.add_bid(n_final)   # N
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(
                    f'נכון!\n'
                    f'{self._n_bid}-{self._s_raise}-{self._n_ask}-4♦\n'
                    f'אין עוצר ♥. שותף מכריז {n_final} ({expl})',
                    ok=True)
        else:
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.set_feedback(
                    f'נסה שוב. רמז: יש לך עוצר ב-{self._ask_sym}? אם לא. חזור ל-♦.',
                    ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(
                    f'טעית בפעם השנייה.\nבחרת {bid}\nהנכון: {correct}. {self._stopper_expl}',
                    ok=False, correct_answer=correct)

    # ── FSF עזרים ────────────────────────────────────────────────────────

    def _show_final_instruction(self, n_resp, fsym):
        n_why = self._n_fsf_why

        if 'NT' in n_resp:
            h = hcp(self.hands['S'])
            if n_resp == '2NT' and h <= 12:
                self.app.set_instruction_table(
                    f'שותף הכריז {n_resp}. {n_why}\nמה תכריז?',
                    [('Pass', f'{h} נק׳, שותף מינימום. נשאר ב-2NT')]
                )
            else:
                self.app.set_instruction_table(
                    f'שותף הכריז {n_resp}. {n_why}\nמה תכריז?',
                    [('3NT', 'שותף יש עוצר. משחק')]
                )
        elif _suit_of(n_resp) == 'H':
            self.app.set_instruction_table(
                f'שותף הכריז {n_resp}. {n_why}\nמה תכריז?',
                [('4♥', 'שותף תמך ב-♥. משחק')]
            )
        elif _suit_of(n_resp) == self._opener_suit:
            correct = self._correct_final
            h = hcp(self.hands['S'])
            if correct == 'Pass':
                hint = f'{h} נק׳. אין מספיק נקודות למשחק, פס'
            elif correct.startswith('5'):
                hint = f'{h} נק׳. 5+ בצבע שותף, אין עוצרים. {correct}'
            else:
                hint = 'מנסה 3NT'
            self.app.set_instruction_table(
                f'שותף הכריז {n_resp}. {n_why}\n'
                f'אין עוצר ב-{fsym}, אין תמיכה ב-♥\nמה תכריז?',
                [(correct, hint)]
            )
        else:
            correct = self._correct_final
            self.app.set_instruction_table(
                f'שותף הכריז {n_resp}. {n_why}\nמה תכריז?',
                [(correct, 'מנסה 3NT')]
            )

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.show_all_hands()
        self.app.set_feedback(message, ok=ok, correct_answer=correct_answer)
        self.app.show_new_deal_button()
