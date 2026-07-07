import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_minor
from engine.response import respond_minor, responder_continuation_after_minor
from engine.rebid import opener_rebid, opener_later_bid
from engine.scoring import hcp
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS

_GAME  = {'3NT', '4♥', '4♠', '5♣', '5♦'}


def _is_final_contract(bid):
    return bid in _GAME


def _consecutive_passes(bids, n=3):
    """האם n הפסים האחרונים ברצף (כולל E/W)."""
    return len(bids) >= n and all(b == 'Pass' for b in bids[-n:])


class LessonRobotOpensMinor(BaseLesson):
    """מחשב (N) פותח מינור, תלמיד (S) עונה. עד 4 סביבים או 3 פסים"""

    _deal_count = 0
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonRobotOpensMinor
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def _correct_message(self, final):
        h = hcp(self.hands['S'])
        return (f'{self._next_opener()}\n'
                f'יש לך {h} נקודות\n'
                f'ההכרזה הנכונה\n'
                f'{final}')

    def start(self):
        if not self._replaying:
            LessonRobotOpensMinor._deal_count += 1
            self._minor = random.choice(['C', 'D'])
            r = random.random()
            if r < 0.40:
                scenario = 'major_fit'
            elif r < 0.65:
                scenario = 'nt'
            elif r < 0.75:
                scenario = 'free'
            else:
                scenario = 'minor_partial'
            self.hands  = deal_robot_opens_minor(self._minor, scenario=scenario)
        self._replaying = False
        self._stage  = 'respond'
        self._tries  = 0
        self._round  = 1          # סביב נוכחי (1-4)
        self._history_n = []      # הכרזות N (אחרי הפתיחה)
        self._history_s = []      # הכרזות S
        self._all_bids  = []      # כל ההכרזות לפי סדר (לבדיקת 3 פסים)

        sym = _S[self._minor]
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid(f'1{sym}')  # N
        self.app.auction_widget.add_bid('Pass')      # E

        self._all_bids.append(f'1{sym}')
        self._all_bids.append('Pass')

        self.app.bidding_box.set_last_bid(f'1{sym}')
        self._set_respond_instruction()

    # ── הוראות ────────────────────────────────────────────────────────────

    def _set_respond_instruction(self):
        sym = _S[self._minor]
        self.app.set_instruction_table(
            'מה תכריז?',
            [
                (f'2{sym}', '6-10 נקודות'),
                (f'3{sym}', '11-12 נקודות'),
            ]
        )

    def _set_continue_instruction(self, n_bid):
        self.app.set_instruction('מה תכריז?')

    # ── ניתוב הכרזות ──────────────────────────────────────────────────────

    def on_student_bid(self, bid):
        self._handle_student_bid(bid)

    # ── לוגיקה מרכזית ─────────────────────────────────────────────────────

    def _handle_student_bid(self, bid):
        sym = _S[self._minor]

        # חישוב התשובה הנכונה לפי שלב
        if self._stage == 'respond':
            correct, _ = respond_minor(self.hands['S'], self._minor)
        else:
            s_prev = self._history_s[-1]
            n_prev = self._history_n[-1]
            correct, _ = responder_continuation_after_minor(
                self.hands['S'], s_prev, n_prev)

        if bid != correct:
            self._tries += 1
            if self._tries < 2:
                last_bid = self._history_n[-1] if self._history_n else f'1{sym}'
                self.app.bidding_box.reset()
                self.app.bidding_box.set_last_bid(last_bid)
                self.app.set_feedback('נסה שוב', ok=False)
                return
            # טעות שנייה — מציגים הודעה ברורה ואת ההכרזה הנכונה, מסיימים
            self.app.auction_widget.add_bid(bid, highlight=True)
            self._finish(f'טעית בפעם השנייה.\nההכרזה הנכונה\n{correct}', ok=False)
            return

        # תשובה נכונה
        self.app.auction_widget.add_bid(bid, highlight=True)
        self.app.auction_widget.add_bid('Pass')   # W
        self._history_s.append(bid)
        self._all_bids += [bid, 'Pass']
        self._tries = 0

        # בדיקת עצירה אחרי הכרזת S
        if _is_final_contract(bid) or _consecutive_passes(self._all_bids) or self._round >= 4:
            final = bid if bid != 'Pass' else (self._history_n[-1] if self._history_n else f'1{sym}')
            self._finish(self._correct_message(final), ok=True)
            return

        # N מכריז שוב
        opening = f'1{sym}'
        if self._round == 1:
            n_bid, _ = opener_rebid(self.hands['N'], opening, bid)
        else:
            # agreed_minor רק אם S תמך במינור במפורש (2m/3m בסיבוב ראשון)
            s_first = self._history_s[0] if self._history_s else ''
            _agreed = self._minor if (f'2{sym}' in s_first or f'3{sym}' in s_first) else None
            # S הראה 6 לבבות אם: פתח ב-1♥ ועכשיו קופץ ל-3♥
            _6h = (s_first == '1♥' and bid == '3♥')
            n_bid, _ = opener_later_bid(self.hands['N'], bid, agreed_minor=_agreed, s_showed_6h=_6h)

        self.app.auction_widget.add_bid(n_bid)
        self.app.auction_widget.add_bid('Pass')   # E
        self._history_n.append(n_bid)
        self._all_bids += [n_bid, 'Pass']
        self._round += 1

        # בדיקת עצירה אחרי הכרזת N
        if _is_final_contract(n_bid) or _consecutive_passes(self._all_bids):
            final = n_bid if n_bid != 'Pass' else bid
            self._finish(self._correct_message(final), ok=True)
            return

        # המשך. שלב הבא
        self._stage  = 'continue'
        self._tries  = 0
        self.app.bidding_box.reset()
        self.app.bidding_box.set_last_bid(n_bid)
        self._set_continue_instruction(n_bid)

    def _finish(self, message, ok):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
