"""
auto_lesson_test.py — בדיקה אוטומטית של שיעורים
מריץ כל שיעור יד אחרי יד, מזין תמיד את התשובה הנכונה,
ובודק עקביות + נכונות לפי כללי ברידג'.

הרצה:  python tests/auto_lesson_test.py
"""

import sys, traceback
sys.path.insert(0, '.')

from engine.scoring import hcp, distribution
from engine.takeout_double import can_double, _count_stoppers

# ═══════════════════════════════════════════════════════
#  Mock UI
# ═══════════════════════════════════════════════════════

class _MockBiddingBox:
    def __init__(self):
        self.last_bid = None
        self.enabled  = True
    def set_last_bid(self, bid): self.last_bid = bid
    def disable(self):           self.enabled  = False


class _MockAuctionWidget:
    def __init__(self):         self.bids = []
    def reset(self):            self.bids = []
    def set_dealer(self, _):    pass
    def add_bid(self, bid, highlight=False): self.bids.append(bid)


class _MockTable:
    def show_hands(self, *a, **kw): pass


class MockApp:
    def __init__(self):
        self.table          = _MockTable()
        self.auction_widget = _MockAuctionWidget()
        self.bidding_box    = _MockBiddingBox()
        self._reset()

    def _reset(self):
        self.feedback_text = None
        self.feedback_ok   = None
        self.finished      = False
        self.auction_widget.reset()
        self.bidding_box.enabled = True

    def set_instruction_table(self, text, rows): pass
    def set_instruction(self, text):             pass
    def show_all_hands(self):                    pass

    def show_new_deal_button(self):
        self.finished = True   # סימן לסיום

    def set_feedback(self, text, ok=True, correct_answer=''):
        self.feedback_text = text
        self.feedback_ok   = ok


# ═══════════════════════════════════════════════════════
#  בדיקת נכונות — שיעור 14
# ═══════════════════════════════════════════════════════

def _suit_of(bid):
    _MAP = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}
    for ch, s in _MAP.items():
        if ch in bid:
            return s
    return None


_RANK = {'C': 1, 'D': 2, 'H': 3, 'S': 4}
_SYM  = {'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠'}


def _independent_best_suit(hand, opp_suit):
    """מוצא את הצבע הטוב ביותר לS — עצמאי מה-engine."""
    d    = distribution(hand)
    best = None
    best_len = -1
    for suit in ['S', 'H', 'D', 'C']:
        if suit == opp_suit:
            continue
        ln = d[suit]
        if ln > best_len:
            best_len, best = ln, suit
        elif ln == best_len:
            # מיגור עדיף על מינור
            if best in ('D', 'C') and suit in ('S', 'H'):
                best = suit
            # ♥ עדיף על ♠ כשאורך שווה
            elif best == 'S' and suit == 'H':
                best = suit
    return best


def _independent_response(hand, opp_suit, opp_level=1):
    """
    מחשב את ההכרזה הנכונה עצמאית — לא קורא ל-engine.
    מיגור:  0-8  רמה נמוכה / 9-12  קפיצה / 13+ קיו ביט
    מינור: 0-10 רמה נמוכה / 11-13 קפיצה / 14+ קיו ביט
    """
    h    = hcp(hand)
    suit = _independent_best_suit(hand, opp_suit)
    if not suit:
        return 'Pass'

    is_minor = suit in ('C', 'D')
    cue_thr  = 14 if is_minor else 13
    jump_thr = 11 if is_minor else 9

    # קיו ביט
    if h >= cue_thr:
        return f'{opp_level + 1}{_SYM[opp_suit]}'

    # גובה מינימלי
    min_lvl = opp_level
    if _RANK[suit] <= _RANK[opp_suit]:
        min_lvl = opp_level + 1

    # קפיצה
    if h >= jump_thr:
        return f'{min_lvl + 1}{_SYM[suit]}'

    # רמה נמוכה
    return f'{min_lvl}{_SYM[suit]}'


def validate_phase1_response(hand, opp_suit, actual_bid):
    """משווה: הכרזת engine מול לוגיקה עצמאית."""
    expected = _independent_response(hand, opp_suit)
    assert actual_bid == expected, (
        f'שלב 1: engine={actual_bid}, עצמאי={expected} '
        f'| {hcp(hand)} נק׳, צבע יריב={opp_suit}'
    )


def _independent_cue_response(s_hand, n_hand, n_suit, opp_suit):
    """
    מחשב עצמאית את תגובת S אחרי שN הראה סדרה.
    עדיפויות:
      1. 5+ מיגור (לא צבע יריב) → 3M (אם N לא הראה) או 4M (אם N הראה)
      2. 4+ בסדרת N כשהיא מיגור → 4M
      3. עוצר בצבע יריב → 3NT
      4. 28+ נק' + 4+ מינור משותף → 5m
      5. אחרת → 3NT
    """
    ds = distribution(s_hand)
    hs = hcp(s_hand)
    hn = hcp(n_hand) if n_hand else 0

    # 1. 5+ מיגור
    for major in ['H', 'S']:
        if major == opp_suit:
            continue
        if ds[major] >= 5:
            sym = _SYM[major]
            if n_suit == major:
                return f'4{sym}'
            else:
                return f'3{sym}'

    # 2. 4+ בסדרת N (מיגור)
    if n_suit and n_suit in ('H', 'S') and ds.get(n_suit, 0) >= 4:
        return f'4{_SYM[n_suit]}'

    # 3. עוצר בצבע יריב
    if opp_suit and _count_stoppers(s_hand, opp_suit):
        return '3NT'

    # 4. 28+ עם מינור
    if n_suit and n_suit in ('C', 'D') and ds.get(n_suit, 0) >= 4:
        if hs + hn >= 28:
            return f'5{_SYM[n_suit]}'

    return '3NT'


def _independent_can_double(hand, opp_suit):
    """מחשב עצמאית האם S יכול לדבל (4-4-3-2 קלאסי)."""
    h = hcp(hand)
    d = distribution(hand)
    if not (12 <= h <= 16):
        return False
    if d.get(opp_suit, 0) > 2:
        return False
    other = [s for s in ['S', 'H', 'D', 'C'] if s != opp_suit]
    for suit in other:
        if d[suit] < 3:
            return False
    if sum(1 for s in other if d[s] >= 4) < 2:
        return False
    return True


def validate_cue_response(s_hand, n_hand, n_suit, opp_suit, bid):
    """משווה תגובת קיו ביט: engine מול לוגיקה עצמאית."""
    expected = _independent_cue_response(s_hand, n_hand, n_suit, opp_suit)
    assert bid == expected, (
        f'קיו ביט: engine={bid}, עצמאי={expected} '
        f'| {hcp(s_hand)} נק׳ S, N הראה {n_suit}, יריב={opp_suit}'
    )


def validate_phase2(hand, e_suit, bid):
    """משווה שלב 2: engine מול לוגיקה עצמאית."""
    expected = 'X' if _independent_can_double(hand, e_suit) else 'Pass'
    assert bid == expected, (
        f'שלב 2: engine={bid}, עצמאי={expected} '
        f'| {hcp(hand)} נק׳, צבע יריב={e_suit}, '
        f'חלוקה={distribution(hand)}'
    )


# ═══════════════════════════════════════════════════════
#  Runner — שיעור 14
# ═══════════════════════════════════════════════════════

def run_lesson14(n_deals=30):
    from lessons.lesson_takeout_double import LessonTakeoutDouble

    app    = MockApp()
    lesson = LessonTakeoutDouble(app)
    lesson._next_phase = 1

    passed = 0
    failed = 0
    errors = []

    for deal_num in range(1, n_deals + 1):
        app._reset()
        try:
            lesson.start()
            phase = lesson._phase

            # ── שלב 1 ──
            if phase == 1:
                correct = lesson._correct
                hands   = lesson.hands

                # אימות נכונות — תגובה לדבל
                validate_phase1_response(hands['S'], lesson._w_suit, correct)

                app.finished = False
                lesson.on_student_bid(correct)

                # אם נכנסנו לדיאלוג קיו ביט
                if not app.finished and hasattr(lesson, '_cue_correct'):
                    cue = lesson._cue_correct
                    validate_cue_response(
                        hands['S'], hands['N'],
                        _suit_of(lesson._n_rebid),
                        lesson._w_suit,
                        cue
                    )
                    lesson.on_student_bid(cue)

                assert app.finished,   'השיעור לא הסתיים'
                assert app.feedback_ok, f'ok=False: {app.feedback_text}'

            # ── שלב 2 ──
            else:
                correct = lesson._correct
                hands   = lesson.hands
                validate_phase2(hands['S'], lesson._e_suit, correct)

                lesson.on_student_bid(correct)

                assert app.finished,   'השיעור לא הסתיים'
                assert app.feedback_ok, f'ok=False: {app.feedback_text}'

            passed += 1

        except Exception as exc:
            failed += 1
            errors.append((deal_num, phase if 'phase' in dir() else '?', str(exc)))

    return passed, failed, errors


# ═══════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════

def main():
    N = 40
    print(f'\n=== בדיקה אוטומטית — שיעור 14 ({N} ידיים) ===\n')

    passed, failed, errors = run_lesson14(N)
    total = passed + failed
    status = '✓' if failed == 0 else '✗'

    print(f'שיעור 14 — דבל להוצאה:  {passed}/{total} {status}')

    if errors:
        print(f'\n  שגיאות ({len(errors)}):')
        for deal_num, phase, msg in errors:
            print(f'   יד {deal_num:2d} (שלב {phase}): {msg}')

    print()


if __name__ == '__main__':
    main()
