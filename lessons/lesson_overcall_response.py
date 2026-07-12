from lessons.base import BaseLesson
from engine.deal_constraints import deal_overcall_response
from engine.overcall import get_overcall, respond_overcall
from engine.opening import opening_bid as _opening_bid
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS
_S = SUIT_SYMBOLS
_SYM_TO_SUIT = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}
_RANK = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}

_MAX_STAGES = 4


def _is_game(bid):
    if bid in ('3NT', '4NT'):
        return True
    if len(bid) == 2 and bid[0] == '4' and bid[1] in ('♠', '♥'):
        return True
    if len(bid) == 2 and bid[0] == '5' and bid[1] in ('♣', '♦'):
        return True
    return False


def _is_new_suit(bid, oc_sym, op_sym):
    if not bid or bid in ('Pass', 'X') or 'NT' in bid:
        return False
    if len(bid) < 2 or not bid[0].isdigit():
        return False
    return bid[1] not in (oc_sym, op_sym)


def _n_auto_bid(n_hand, oc_bid, w_bid, s_bid):
    """N מכריז ריבאד אוטומטי אחרי הכרזת S"""
    h      = hcp(n_hand)
    d      = distribution(n_hand)
    oc_sym = oc_bid[1]
    oc_lvl = int(oc_bid[0])
    oc_suit = _SYM_TO_SUIT.get(oc_sym, '')

    if _is_new_suit(s_bid, oc_sym, w_bid[1]):
        s_suit = _SYM_TO_SUIT.get(s_bid[1], '')
        s_sym  = s_bid[1]
        s_lvl  = int(s_bid[0])
        s_r    = _RANK.get(s_sym, 5)
        oc_r   = _RANK.get(oc_sym, 5)

        if d.get(s_suit, 0) >= 3:
            return f'{s_lvl + 1}{s_sym}', f'{h} נקודות, תמיכה בצבע שלך'
        if h >= 14:
            # N חוזר לצבע שלו. חישוב רמה מינימלית
            n_lvl = s_lvl if oc_r > s_r else s_lvl + 1
            return f'{n_lvl}{oc_sym}', f'{h} נקודות, חוזר לצבע שלי'
        return 'Pass', f'{h} נקודות. מינימום'

    # S תמך בצבע N
    if len(s_bid) == 2 and s_bid[1] == oc_sym:
        s_lvl = int(s_bid[0])
        if s_lvl == oc_lvl + 2 and h >= 15:  # S הזמין. N מקבל
            if oc_suit in ('S', 'H'):
                return f'4{oc_sym}', f'{h} נקודות, מקבל הזמנה. משחק'
            return '3NT', f'{h} נקודות, מקבל הזמנה'
        return 'Pass', f'{h} נקודות. פס'

    return 'Pass', 'פס'


def _s_correct_bid(s_hand, oc_bid, w_bid, n_last_bid, s_prev_bid=None):
    """
    הכרזה נכונה לS:
      s_prev_bid=None → שלב 1: תגובה ישירה לאוברקול
      s_prev_bid set  → שלב 2+: תגובה לריבאד N
    """
    if s_prev_bid is None:
        return respond_overcall(s_hand, oc_bid, w_bid)

    h      = hcp(s_hand)
    d      = distribution(s_hand)
    oc_sym = oc_bid[1]
    oc_suit = _SYM_TO_SUIT.get(oc_sym, '')

    if n_last_bid == 'Pass':
        return 'Pass', 'שותף פס. מינימום'

    if _is_game(n_last_bid):
        return 'Pass', 'שותף הגיע למשחק. פס'

    n_sym  = n_last_bid[1] if len(n_last_bid) == 2 and 'N' not in n_last_bid else ''
    s_sym  = s_prev_bid[1] if len(s_prev_bid) == 2 else ''
    s_suit = _SYM_TO_SUIT.get(s_sym, '')
    n_suit = _SYM_TO_SUIT.get(n_sym, '')

    # N תמך בצבע S
    if n_sym and n_sym == s_sym:
        if h >= 15:
            if s_suit in ('S', 'H'):
                return f'4{s_sym}', f'{h} נקודות, יד חזקה. משחק'
            return '3NT', f'{h} נקודות, יד חזקה. 3NT'
        return 'Pass', f'{h} נקודות. הספקת'

    # N חזר לצבע שלו (אוברקול)
    if n_sym == oc_sym:
        if d.get(oc_suit, 0) >= 3 and h >= 13:
            if oc_suit in ('S', 'H'):
                return f'4{oc_sym}', f'{h} נקודות, 3+ קלפי {oc_sym}. משחק'
            return '3NT', f'{h} נקודות. 3NT'
        return 'Pass', f'{h} נקודות. פס'

    return 'Pass', 'פס'


class LessonOvercallResponse(BaseLesson):
    """שיעור 12 (גרסה ב): תלמיד עונה לאוברקול שותפו. עד 4 סיבובים"""

    TITLE = 'שיעור 12. תגובה לאוברקול'
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonOvercallResponse
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def start(self):
        if not self._replaying:
            self.hands     = deal_overcall_response()
            self._w_bid, _ = _opening_bid(self.hands['W'])
            self._n_bid, _ = get_overcall(self.hands['N'], self._w_bid)
        self._replaying = False
        self._tries     = 0
        self._stage     = 1
        self._s_bids    = []   # הכרזות S עד כה
        self._n_rebids  = []   # ריבאדים של N (bid, why)

        oc_sym  = self._n_bid[1]
        oc_lvl  = int(self._n_bid[0])
        is_minor = oc_sym in ('♣', '♦')

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('W')
        self.app.auction_widget.add_bid(self._w_bid)
        self.app.auction_widget.add_bid(self._n_bid)
        self.app.auction_widget.add_bid('Pass')  # E
        self.app.bidding_box.set_last_bid(self._n_bid)
        if is_minor:
            table = [
                (f'{oc_lvl + 1}{oc_sym}', f'3+ קלפי {oc_sym}, 10+ נקודות'),
                ('צבע חדש',               '5+ קלפים, 11+ נקודות'),
                ('Pass',                  'פחות מ-10 נקודות'),
            ]
        else:
            table = [
                (f'{oc_lvl + 1}{oc_sym}', f'3+ קלפי {oc_sym}, 7-10 נקודות'),
                (f'{oc_lvl + 2}{oc_sym}', f'3+ קלפי {oc_sym}, 11-12 נקודות. הזמנה'),
                ('צבע חדש',               '5+ קלפים, 11+ נקודות'),
                ('Pass',                  'יד חלשה'),
            ]
        self.app.set_instruction_table(
            'מה תענה',
            table
        )

    def on_student_bid(self, bid):
        if self._stage > _MAX_STAGES:
            return

        s_prev  = self._s_bids[-1] if self._s_bids else None
        n_last  = self._n_rebids[-1][0] if self._n_rebids else self._n_bid

        correct, explanation = _s_correct_bid(
            self.hands['S'], self._n_bid, self._w_bid, n_last, s_prev)

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self._s_bids.append(bid)

            # תנאי סיום
            if bid == 'Pass' or _is_game(bid) or self._stage >= _MAX_STAGES:
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(f'{self._next_opener()}\n{explanation}\nההכרזה הנכונה\n{bid}', ok=True)
                return

            # N מכריז ריבאד אוטומטי
            nr_bid, nr_why = _n_auto_bid(
                self.hands['N'], self._n_bid, self._w_bid, bid)
            self._n_rebids.append((nr_bid, nr_why))
            self.app.auction_widget.add_bid('Pass')   # W
            self.app.auction_widget.add_bid(nr_bid)   # N
            self.app.auction_widget.add_bid('Pass')   # E

            # N סיים את המכרז
            # כשN פס: W+N+E כבר 3 פסים רצופים ✓
            # כשN הכריז משחק: E כבר פס, צריך עוד S+W
            if nr_bid == 'Pass' or _is_game(nr_bid):
                if _is_game(nr_bid):
                    self.app.auction_widget.add_bid('Pass')  # S
                    self.app.auction_widget.add_bid('Pass')  # W
                    self.app.auction_widget.add_bid('Pass')  # N
                self._finish(
                    f'{self._next_opener()}\n{explanation}\nשותף הכריז {nr_bid}. {nr_why}\nההכרזה הנכונה\n{bid}',
                    ok=True)
                return

            # עלייה לשלב הבא
            self._stage += 1
            self._tries = 0
            self.app.bidding_box.set_last_bid(nr_bid)
            self.app.set_instruction_table(
                f'שותף הכריז {nr_bid} ({nr_why}). מה תכריז',
                [
                    ('4M / 3NT', 'יד חזקה. משחק'),
                    ('Pass',     'מינימום. פס'),
                ]
            )

        else:
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')  # W
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(
                    f'{explanation}\nההכרזה הנכונה\n{correct}',
                    ok=False, correct_answer=correct)

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 99
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.show_all_hands()
        self.app.set_feedback(message, ok=ok, correct_answer=correct_answer)
        self.app.show_new_deal_button()
