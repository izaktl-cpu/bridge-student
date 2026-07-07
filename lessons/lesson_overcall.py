from lessons.base import BaseLesson
from engine.deal_constraints import deal_overcall
from engine.overcall import get_overcall, respond_overcall, _suit_quality
from engine.opening import opening_bid as _opening_bid
from engine.response import get_response
from engine.scoring import hcp, distribution, dist_fit_pts, has_stopper
from engine.cards import SUIT_SYMBOLS, card_rank, card_suit
_S = SUIT_SYMBOLS
_SYM_TO_SUIT = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}
_BID_RANK = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}


def _hand_eval(hand, trump_suit=None):
    """מחזיר מחרוזת הערכת יד: HCP [+ חלוקה = סה״כ]"""
    h  = hcp(hand)
    dp = dist_fit_pts(hand, trump=trump_suit) if trump_suit else 0
    if dp:
        return f'{h} נקודות גבוהות ו-{dp} חלוקה, סך {h + dp}'
    return f'{h} נקודות גבוהות'


def _n_bid_meaning(n_bid, s_bid1):
    """פירוש הכרזת N לתצוגה"""
    if n_bid == 'Pass':
        return 'מינימום'
    if len(n_bid) < 2 or not n_bid[0].isdigit():
        return ''
    n_lvl = int(n_bid[0])
    n_sym = n_bid[1]
    s_sym = s_bid1[1] if len(s_bid1) == 2 else ''
    s_lvl = int(s_bid1[0]) if s_bid1 and s_bid1[0].isdigit() else 1
    if n_sym == s_sym:
        diff = n_lvl - s_lvl
        if diff == 1:
            return '6-9 נקודות. מינימום'
        if diff == 2:
            return '10-12 נקודות. הזמנה'
        if diff >= 3 or n_lvl == 4:
            return '13+ נקודות. משחק'
    return ''


def _shortage_pts(hand, trump_suit):
    """נקודות חוסר עם התאמה: void=3, singleton (לא מכובד)=2, doubleton=0"""
    d = distribution(hand)
    honors = {'A', 'K', 'Q', 'J'}
    pts = 0
    for suit, cnt in d.items():
        if suit == trump_suit:
            continue
        if cnt == 0:
            pts += 3
        elif cnt == 1:
            has_honor = any(card_rank(c) in honors for c in hand if card_suit(c) == suit)
            if not has_honor:
                pts += 2
    return pts


def _s_rebid_correct(s_hand, s_bid1, n_last_bid, op_bid='Pass'):
    """הכרזה נכונה לS בשלב 2+ לאחר ריבאד N."""
    h      = hcp(s_hand)
    d      = distribution(s_hand)
    s_sym  = s_bid1[1] if len(s_bid1) == 2 else ''
    s_suit = _SYM_TO_SUIT.get(s_sym, '')
    op_suit = _SYM_TO_SUIT.get(op_bid[1], '') if len(op_bid) >= 2 and op_bid[0].isdigit() else ''
    s_lvl  = int(s_bid1[0]) if s_bid1[0].isdigit() else 1

    if n_last_bid == 'Pass':
        return 'Pass', 'שותף פס. אין המשך'

    n_sym  = n_last_bid[1] if len(n_last_bid) == 2 and 'N' not in n_last_bid else ''
    n_suit = _SYM_TO_SUIT.get(n_sym, '')
    n_lvl  = int(n_last_bid[0]) if n_last_bid[0].isdigit() else 0

    # N תמך בצבע S
    if n_sym == s_sym:
        diff   = n_lvl - s_lvl
        op_suit = _SYM_TO_SUIT.get(op_bid[1], '') if len(op_bid) >= 2 and op_bid[0].isdigit() else ''

        if diff == 1:
            # N מינימום (7-10 נקודות) — בכל רמה
            if s_suit in ('S', 'H'):
                sp    = _shortage_pts(s_hand, s_suit)
                total = h + sp
                if total >= 18:
                    return f'4{s_sym}', f'{h}+{sp} נקודות חוסר, סה״כ {total}. משחק'
                if total >= 16:
                    return f'3{s_sym}', f'{h}+{sp} נקודות חוסר, סה״כ {total}. ניסיון משחק'
            return 'Pass', f'{h} נקודות. שותף מינימום, פס'

        # N הזמין (diff>=2) — N=11-12 נקודות
        if h >= 14:
            if s_suit in ('S', 'H'):
                return f'4{s_sym}', f'{h} נקודות, יד חזקה. משחק'
            # מינור: צריך עוצר בצבע הפותח
            if op_suit and has_stopper(s_hand, op_suit):
                return '3NT', f'{h} נקודות, עוצר. 3NT'
            return 'Pass', f'{h} נקודות. אין עוצר ב-{op_bid[1]}, פס'
        return 'Pass', f'{h} נקודות. לא מספיק למשחק, פס'

    # N הכריז צבע חדש
    if n_sym and n_sym != s_sym:
        if d.get(n_suit, 0) >= 3:
            return f'{n_lvl + 1}{n_sym}', f'{h} נקודות, {d[n_suit]} קלפי {n_sym}. תמיכה'
        if h >= 13:
            # חישוב רמה נכונה מעל הכרזת N
            s_r = _BID_RANK.get(s_sym, 0)
            n_r = _BID_RANK.get(n_sym, 0)
            rebid_lvl = n_lvl if s_r > n_r else n_lvl + 1
            return f'{rebid_lvl}{s_sym}', f'{h} נקודות. חוזר לצבע שלי'
        return 'Pass', f'{h} נקודות. פס'

    return 'Pass', 'פס'


def _bid_value(bid):
    if bid in ('Pass', 'X', 'XX'):
        return 0
    lvl = int(bid[0]) if bid[0].isdigit() else 0
    if 'NT' in bid:
        return lvl * 10 + 5
    return lvl * 10 + _BID_RANK.get(bid[1], 0)


def _is_game(bid):
    if bid in ('3NT', '4NT'):
        return True
    if len(bid) == 2 and bid[0] == '4' and bid[1] in ('♠', '♥'):
        return True
    if len(bid) == 2 and bid[0] == '5' and bid[1] in ('♣', '♦'):
        return True
    return False


def _w_competitive_bid(w_hand, e_bid, s_bid, last_rank):
    """W הכרזה תחרותית לאחר אוברקול — תמיכה בE או צבע חדש ברמה הנכונה"""
    h = hcp(w_hand)
    d = distribution(w_hand)

    e_sym  = e_bid[1] if len(e_bid) == 2 else ''
    e_suit = _SYM_TO_SUIT.get(e_sym, '')
    s_suit = _SYM_TO_SUIT.get(s_bid[1], '') if len(s_bid) == 2 else ''

    # תמיכה בצבע E (3+ קלפים, 6+ נקודות)
    if e_suit and d.get(e_suit, 0) >= 3 and h >= 6:
        for lvl in range(1, 5):
            candidate = f'{lvl}{e_sym}'
            if _bid_value(candidate) > last_rank:
                if lvl >= 3 and h < 8:
                    break
                return candidate

    # צבע חדש (5+ קלפים, 10+ נקודות)
    if h >= 10:
        for suit in ['C', 'D', 'H', 'S']:
            if suit in (e_suit, s_suit):
                continue
            if d.get(suit, 0) < 5:
                continue
            sym = _S[suit]
            for lvl in range(1, 5):
                candidate = f'{lvl}{sym}'
                if _bid_value(candidate) > last_rank:
                    return candidate

    return 'Pass'


def _e_rebid(e_hand, e_bid, last_rank):
    """E ריבאד אחרי אוברקול — 6+ קלפים בצבע הפתיחה, או דו-סדרתית (5-5)"""
    if not (len(e_bid) == 2 and e_bid[0].isdigit()):
        return 'Pass'
    e_sym  = e_bid[1]
    e_suit = _SYM_TO_SUIT.get(e_sym, '')
    d      = distribution(e_hand)

    # 6+ קלפים בצבע הפתיחה → ריבאד
    if d.get(e_suit, 0) >= 6:
        lvl = int(e_bid[0]) + 1
        if lvl <= 4:
            bid = f'{lvl}{e_sym}'
            if _bid_value(bid) > last_rank:
                return bid

    # דו-סדרתית: 5+ קלפי פתיחה + 5+ בצבע שני → הראה צבע שני
    if d.get(e_suit, 0) >= 5:
        for suit in ['C', 'D', 'H', 'S']:
            if suit == e_suit:
                continue
            if d.get(suit, 0) < 5:
                continue
            sym = _S[suit]
            for lvl in range(1, 5):
                candidate = f'{lvl}{sym}'
                if _bid_value(candidate) > last_rank:
                    return candidate

    return 'Pass'


def _oc_is_game(bid):
    """האם ההכרזה היא משחק מלא?"""
    if not bid or bid in ('Pass', 'X', 'XX'):
        return False
    if 'NT' in bid and bid[0] in '34567':
        return True
    if len(bid) == 2 and bid[0] == '4' and bid[1] in ('♠', '♥'):
        return True
    if len(bid) == 2 and bid[0] == '5' and bid[1] in ('♣', '♦'):
        return True
    return False


def _opener_rebid(e_hand, e_bid, w_response, last_rank):
    """E rebid אחרי תגובת W — כללים פשוטים"""
    h     = hcp(e_hand)
    d     = distribution(e_hand)
    e_sym = e_bid[1] if len(e_bid) == 2 else ''
    e_suit = _SYM_TO_SUIT.get(e_sym, '')

    if len(w_response) < 2 or not w_response[0].isdigit():
        return 'Pass'

    w_sym  = w_response[1] if 'N' not in w_response else ''
    w_suit = _SYM_TO_SUIT.get(w_sym, '')
    w_lvl  = int(w_response[0])

    # W הרים E's suit
    if w_sym == e_sym:
        if h >= 17 and e_suit in ('S', 'H'):
            bid = f'4{e_sym}'
            if _bid_value(bid) > last_rank:
                return bid
        if h >= 19 and e_suit in ('C', 'D'):
            if _bid_value('3NT') > last_rank:
                return '3NT'
        return 'Pass'

    # W הכריז NT
    if 'NT' in w_response:
        if h >= 17:
            lvl = w_lvl + 1
            bid = f'{lvl}NT'
            if _bid_value(bid) > last_rank:
                return bid
        return 'Pass'

    # W הכריז צבע חדש
    if w_suit:
        if d.get(w_suit, 0) >= 3:
            if h >= 17 and w_suit in ('S', 'H'):
                bid = f'4{w_sym}'
            else:
                bid = f'{w_lvl + 1}{w_sym}'
            if _bid_value(bid) > last_rank:
                return bid
        if d.get(e_suit, 0) >= 6:
            bid = f'{w_lvl}{e_sym}'
            if _bid_value(bid) > last_rank:
                return bid
        if h >= 18:
            bid = '2NT'
            if _bid_value(bid) > last_rank:
                return bid

    return 'Pass'


def _responder_continue(w_hand, w_bid, e_rebid, last_rank):
    """W ממשיך אחרי E rebid — כללים פשוטים"""
    h     = hcp(w_hand)
    d     = distribution(w_hand)

    if len(e_rebid) < 2 or not e_rebid[0].isdigit():
        return 'Pass'

    e_sym  = e_rebid[1] if 'N' not in e_rebid else ''
    e_suit = _SYM_TO_SUIT.get(e_sym, '')
    e_lvl  = int(e_rebid[0])

    # E חוזר לצבעו → W עם תמיכה 3+ ונקודות מספיק → משחק
    if e_suit and d.get(e_suit, 0) >= 3:
        if h >= 11 and e_suit in ('S', 'H'):
            bid = f'4{e_sym}'
            if _bid_value(bid) > last_rank:
                return bid
        if h >= 11 and e_suit in ('C', 'D'):
            if _bid_value('3NT') > last_rank:
                return '3NT'

    # E bid NT → W raises
    if 'NT' in e_rebid and h >= 10:
        bid = f'{e_lvl + 1}NT'
        if _bid_value(bid) > last_rank:
            return bid

    return 'Pass'


def _auto_bids(hands, e_bid, s_bid, last_rank, w_done, n_done, e_done=False):
    """
    מחשב הכרזות אוטומטיות של W, N, E אחרי הכרזת S.
    מחזיר (רשימת הכרזות, last_rank_חדש, w_done_חדש, n_done_חדש, e_done_חדש, passes_רצופים).
    """
    result = []
    consecutive = 0

    w_bid = 'Pass'
    for player in ['W', 'N', 'E']:
        if player == 'W' and not w_done:
            bid = _w_competitive_bid(hands['W'], e_bid, s_bid, last_rank)
            w_bid = bid
            w_done = True
        elif player == 'N' and not n_done:
            bid, _ = respond_overcall(hands['N'], s_bid, e_bid, competition_bid=w_bid)
            n_done = True
        elif player == 'E' and not e_done:
            bid = _e_rebid(hands['E'], e_bid, last_rank)
            e_done = True
        else:
            bid = 'Pass'

        if bid != 'Pass' and _bid_value(bid) <= last_rank:
            bid = 'Pass'

        result.append(bid)
        if bid != 'Pass':
            last_rank = _bid_value(bid)
            consecutive = 0
        else:
            consecutive += 1

    return result, last_rank, w_done, n_done, e_done, consecutive


class LessonOvercall(BaseLesson):
    """שיעור 12: תלמיד מכריז אוברקול, ממשיך להכריז בשלבים הבאים"""

    TITLE = 'שיעור 12. אוברקול'
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonOvercall
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def _wrong_message(self, correct):
        return f'ההכרזה הנכונה\n{correct}'

    def start(self):
        if not self._replaying:
            self.hands     = deal_overcall()
            self._e_bid, _ = _opening_bid(self.hands['E'])
        self._replaying = False
        self._tries     = 0
        self._stage     = 'bid1'
        self._last_rank = _bid_value(self._e_bid)
        self._w_done      = False
        self._n_done      = False
        self._e_done      = False
        self._s_bid1      = None
        self._n_last_bid  = None
        self._e_last_bid  = None

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('E')
        self.app.auction_widget.add_bid(self._e_bid)
        self.app.bidding_box.set_last_bid(self._e_bid)
        eval_txt = _hand_eval(self.hands['S'])
        self.app.set_instruction_table(
            f'{eval_txt}\nמה תכריז',
            [
                ('בגובה 1', '9-16 נקודות גבוהות\n5 קלפים, 2 מכובדים'),
                ('בגובה 2', '12-16 נקודות גבוהות\n5 קלפים, 2 מכובדים'),
                ('פס',      'אין אוברקול מתאים'),
            ]
        )

    def on_student_bid(self, bid):
        if self._stage == 'bid1':
            self._handle_bid1(bid)
        elif self._stage == 'play':
            self._handle_play(bid)

    # ── שלב 1: אוברקול (נבדק) ───────────────────────────────────────────────

    def _handle_bid1(self, bid):
        correct, explanation = get_overcall(self.hands['S'], self._e_bid)
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self._s_bid1    = bid
            self._last_rank = _bid_value(bid)
            if bid == 'Pass':
                self._add_pass_continuation()
                self._finish(self._ok_message(bid), ok=True)
            else:
                self._run_auto_then_continue()
        else:
            self._tries += 1
            if self._tries < 2:
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')  # W
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(self._wrong_message(correct), ok=False, correct_answer=correct)

    # ── שלבים הבאים: S מכריז עם בדיקה ─────────────────────────────────────

    def _handle_play(self, bid):
        correct, explanation = _s_rebid_correct(
            self.hands['S'], self._s_bid1, self._n_last_bid, op_bid=self._e_bid)

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self._last_rank = _bid_value(bid)
            if bid == 'Pass' or _is_game(bid):
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(f'{self._next_opener()}\n{explanation}', ok=True)
            else:
                self._run_auto_then_continue()
        else:
            self._tries += 1
            if self._tries < 2:
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')  # W
                self.app.auction_widget.add_bid('Pass')  # N
                self.app.auction_widget.add_bid('Pass')  # E
                self._finish(self._wrong_message(correct), ok=False, correct_answer=correct)

    # ── המשך מכרז אחרי פס של S ──────────────────────────────────────────────

    def _add_pass_continuation(self):
        """S פס — E ו-W ממשיכים את המכרז שלהם עד משחק או 3 פסים"""
        e_rank = _bid_value(self._e_bid)
        last_rank = e_rank

        # שלב 1: W מגיב לפתיחת E
        w_bid, _ = get_response(self.hands['W'], self._e_bid)
        if _bid_value(w_bid) <= last_rank:
            w_bid = 'Pass'
        self.app.auction_widget.add_bid(w_bid)   # W
        self.app.auction_widget.add_bid('Pass')  # N

        if w_bid == 'Pass':
            self.app.auction_widget.add_bid('Pass')  # E
            self.app.auction_widget.add_bid('Pass')  # S
            return

        last_rank = _bid_value(w_bid)
        if _oc_is_game(w_bid):
            self.app.auction_widget.add_bid('Pass')  # E
            self.app.auction_widget.add_bid('Pass')  # S
            return

        # שלב 2: E rebid
        e_rebid = _opener_rebid(self.hands['E'], self._e_bid, w_bid, last_rank)
        self.app.auction_widget.add_bid(e_rebid)  # E
        self.app.auction_widget.add_bid('Pass')   # S

        if e_rebid == 'Pass':
            self.app.auction_widget.add_bid('Pass')  # W
            self.app.auction_widget.add_bid('Pass')  # N
            return

        last_rank = _bid_value(e_rebid)
        if _oc_is_game(e_rebid):
            self.app.auction_widget.add_bid('Pass')  # W
            self.app.auction_widget.add_bid('Pass')  # N
            return

        # שלב 3: W ממשיך
        w_bid2 = _responder_continue(
            self.hands['W'], w_bid, e_rebid, last_rank)
        self.app.auction_widget.add_bid(w_bid2)  # W
        self.app.auction_widget.add_bid('Pass')  # N

        if w_bid2 == 'Pass':
            self.app.auction_widget.add_bid('Pass')  # E
            self.app.auction_widget.add_bid('Pass')  # S
            return

        last_rank = _bid_value(w_bid2)
        if _oc_is_game(w_bid2):
            self.app.auction_widget.add_bid('Pass')  # E
            self.app.auction_widget.add_bid('Pass')  # S
            return

        # שלב 4: E rebid שני → סגור
        e_rebid2 = _opener_rebid(self.hands['E'], e_rebid, w_bid2, last_rank)
        self.app.auction_widget.add_bid(e_rebid2)  # E
        self.app.auction_widget.add_bid('Pass')    # S
        self.app.auction_widget.add_bid('Pass')    # W
        self.app.auction_widget.add_bid('Pass')    # N

    # ── הפעלת הכרזות אוטומטיות ואחר כך המתנה לS ────────────────────────────

    def _run_auto_then_continue(self):
        auto, new_rank, w_done, n_done, e_done, passes = _auto_bids(
            self.hands, self._e_bid, self._s_bid1,
            self._last_rank, self._w_done, self._n_done, self._e_done)

        self._w_done    = w_done
        self._n_done    = n_done
        self._e_done    = e_done
        self._last_rank = new_rank

        # שמור את הכרזת N האחרונה (W, N, E)
        n_bid_in_round = auto[1] if len(auto) > 1 else 'Pass'
        if n_bid_in_round != 'Pass':
            self._n_last_bid = n_bid_in_round
        elif self._n_last_bid is None:
            self._n_last_bid = 'Pass'

        # שמור הכרזת E (ריבאד)
        e_bid_in_round = auto[2] if len(auto) > 2 else 'Pass'
        if e_bid_in_round != 'Pass':
            self._e_last_bid = e_bid_in_round

        for b in auto:
            self.app.auction_widget.add_bid(b)

        # בדוק אם המכרז נסגר (3 פסים: W+N+E כולם פסו)
        if passes == 3 or _is_game(auto[-2] if len(auto) >= 2 else 'Pass'):
            self._finish('מכרז הסתיים', ok=True)
            return

        # S מכריז שוב
        last_auto_bid = next((b for b in reversed(auto) if b != 'Pass'), None)
        set_bid = last_auto_bid if last_auto_bid else self._s_bid1
        self.app.bidding_box.set_last_bid(set_bid)
        eval_txt = _hand_eval(self.hands['S'])
        n_info = self._n_last_bid if self._n_last_bid else ''
        n_meaning = _n_bid_meaning(n_info, self._s_bid1 or '')
        self.app.set_instruction_table(
            f'{eval_txt}\n{n_meaning}\nמה תכריז',
            [('4M / 3NT', 'יד חזקה. משחק'),
             ('Pass',     'מינימום. פס')]
        )
        self._stage = 'play'

    # ── הודעות ─────────────────────────────────────────────────────────────

    def _ok_message(self, bid):
        s = self.hands['S']
        h = hcp(s)
        d = distribution(s)
        opener = self._next_opener()
        if bid == 'Pass':
            return f'{opener}\nיש לך {h} נקודות גבוהות\nאין אוברקול מתאים\nההכרזה הנכונה\nPass'
        sym     = bid[1]
        suit    = _SYM_TO_SUIT.get(sym, '')
        length  = d.get(suit, 0)
        quality = _suit_quality(s, suit)
        return (
            f'{opener}\n'
            f'יש לך {h} נקודות גבוהות\n'
            f'יש לך {length} קלפי {sym} עם {quality} מכובדים\n'
            f'ההכרזה הנכונה\n{bid}'
        )

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.show_all_hands()
        self.app.set_feedback(message, ok=ok, correct_answer=correct_answer)
        self.app.show_new_deal_button()
