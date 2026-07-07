"""
אוברקול Acol. E/W מגיבים לפתיחת N/S.
מחזיר (bid, explanation).
"""

from engine.scoring import hcp, is_balanced, distribution, suit_len
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


def get_overcall(hand, opening_bid, position='E'):
    """
    מחשב אוברקול לאחר פתיחה.
    opening_bid: '1♥', '1♠', '1NT' וכד'.
    position: 'E' or 'W'
    מחזיר (bid, explanation).
    """
    h   = hcp(hand)
    d   = distribution(hand)
    bal = is_balanced(hand)

    open_suit  = _bid_to_suit(opening_bid)
    open_level = int(opening_bid[0]) if opening_bid[0].isdigit() else 1

    # ── פס ──────────────────────────────────────────────────────────────────
    if h < 8:
        return 'Pass', f'{h} נק׳. פס'

    # ── 1NT אוברקול (15-18 HCP, מאוזן, כבלה בצבע הפותח) ───────────────────
    if 15 <= h <= 18 and bal and open_level == 1:
        if open_suit and d.get(open_suit, 0) >= 2:  # יש כבלה
            return '1NT', f'{h} נק׳, מאוזן. 1NT אוברקול'

    # ── טייקאאוט דאבל (12+ HCP, שורטאז' בצבע הפותח, תמיכה בשאר) ───────────
    if h >= 12 and open_suit:
        shortage   = d.get(open_suit, 0) <= 2
        other_fits = sum(1 for s in ['S', 'H', 'D', 'C']
                         if s != open_suit and d[s] >= 3)
        if shortage and other_fits >= 3:
            return 'X', f'{h} נק׳, {d.get(open_suit,0)} קלפי {_S.get(open_suit,"?")}. טייקאאוט דאבל'

    # ── אוברקול פשוט (5+ קלפים + 2 מכובדים) ────────────────────────────────
    for suit in ['S', 'H', 'D', 'C']:
        if suit == open_suit:
            continue
        length = d[suit]
        if length < 5:
            continue
        level = _min_level(open_bid=opening_bid, overcall_suit=suit)
        if not level:
            continue
        min_h = 9 if level == 1 else 12
        if h < min_h or h > 16:
            continue
        if _suit_quality(hand, suit) >= 2 and _suit_hcp(hand, suit) >= 4:
            return f'{level}{_S[suit]}', (
                f'{h} נק׳, {length} קלפי {_S[suit]}. אוברקול {level}{_S[suit]}'
            )

    return 'Pass', f'{h} נק׳. פס (אין אוברקול מתאים)'


def respond_overcall(hand, overcall_bid, opening_bid, competition_bid='Pass'):
    """
    תגובה לאוברקול של שותף.
    competition_bid: הכרזת המתנגד (W) אחרי האוברקול. משפיע על תחרות.
    מחזיר (bid, explanation).
    overcall_bid: e.g. '1♠', '2♦'
    opening_bid:  e.g. '1♥', '1♣'
    """
    from engine.scoring import hcp, is_balanced, distribution, has_stopper, suit_len, dist_fit_pts

    h      = hcp(hand)
    d      = distribution(hand)
    oc_sym = overcall_bid[1]
    oc_suit = _bid_to_suit(overcall_bid)
    op_suit = _bid_to_suit(opening_bid)
    oc_lvl  = int(overcall_bid[0])
    support = d.get(oc_suit, 0)

    # נקודות אורך בלבד (לשימוש מחוץ לתמיכה)
    length_pts = sum(max(0, cnt - 4) for cnt in d.values())
    t      = h + length_pts

    # ── תמיכה בצבע האוברקול (3+ קלפים) ────────────────────────────────────────
    comp_lvl = int(competition_bid[0]) if competition_bid and competition_bid not in ('Pass', 'X', 'XX') and competition_bid[0].isdigit() else 0
    is_minor_oc = oc_suit in ('C', 'D')

    # תחרות (מיגור רמה 1): המתנגד ברמה 2 → עולים עם 3+ תמיכה גם עם יד חלשה (3-6 נק')
    if support >= 3 and not is_minor_oc and oc_lvl == 1 and h <= 6 and comp_lvl >= 2:
        return f'{oc_lvl + 1}{oc_sym}', f'{h} נק׳, {support} קלפי {oc_sym}. תחרות'

    if support >= 3:
        if is_minor_oc:
            # מינור: נדרש 10+ נקודות להעלאה (28+ נק' משותפות למשחק)
            if h < 10:
                return 'Pass', f'{h} נק׳, מינור. פס'
            return f'{oc_lvl + 1}{oc_sym}', f'{h} נק׳, {support} קלפי {oc_sym}. תמיכה'
        elif oc_lvl == 1:
            # מיגור רמה 1: 7-10→+1, 11-12→הזמנה, 13+ (כולל אורך) →משחק
            if h < 7:
                return 'Pass', f'{h} נק׳. פס'
            if t >= 13:
                return f'4{oc_sym}', f'{h} נק׳ ({t} סה״כ), {support} קלפי {oc_sym}. משחק'
            if h <= 10:
                return f'{oc_lvl + 1}{oc_sym}', f'{h} נק׳, {support} קלפי {oc_sym}. תמיכה'
            else:
                return f'{oc_lvl + 2}{oc_sym}', f'{h} נק׳, {support} קלפי {oc_sym}. הזמנה'
        else:
            # מיגור רמה 2+: נדרש 10+ (כבר ברמה 3 עם תמיכה)
            if h < 10:
                return 'Pass', f'{h} נק׳. פס'
            if t >= 13:
                return f'4{oc_sym}', f'{h} נק׳ ({t} סה״כ), {support} קלפי {oc_sym}. משחק'
            if h <= 12:
                return f'{oc_lvl + 1}{oc_sym}', f'{h} נק׳, {support} קלפי {oc_sym}. הזמנה'
            else:
                return f'4{oc_sym}', f'{h} נק׳, {support} קלפי {oc_sym}. משחק'

    # ── פס. יד חלשה מדי לכל הכרזה אחרת ──────────────────────────────────────
    if t < 8:
        return 'Pass', f'{h} נק׳. פס (יד חלשה)'

    # ── צבע חדש 11+ נקודות ───────────────────────────────────────────────────
    if t >= 11:
        for suit in ['S', 'H', 'D', 'C']:
            if suit in (oc_suit, op_suit):
                continue
            if d[suit] < 5:
                continue
            if _suit_hcp(hand, suit) == 0:   # חייב לפחות J. לא מכריזים צבע ללא מכובדים
                continue
            sym  = _S[suit]
            rank = {'C': 1, 'D': 2, 'H': 3, 'S': 4}
            lvl  = oc_lvl if rank[suit] > rank[oc_suit] else oc_lvl + 1
            if lvl <= 4:
                return f'{lvl}{sym}', f'{h} נק׳, {d[suit]} קלפי {sym}. צבע חדש'

    # ── 1NT / 2NT ────────────────────────────────────────────────────────────
    if is_balanced(hand) and op_suit and has_stopper(hand, op_suit):
        nt_lvl = oc_lvl if oc_lvl == 1 else oc_lvl
        min_nt = 8 if oc_lvl == 1 else 11
        if min_nt <= t <= 11:
            return f'{nt_lvl}NT', f'{h} נק׳, מאוזן, עצור. {nt_lvl}NT'
        if t >= 12:
            return f'{nt_lvl + 1}NT', f'{h} נק׳, מאוזן, עצור. {nt_lvl + 1}NT'

    # ── פס ───────────────────────────────────────────────────────────────────
    return 'Pass', f'{h} נק׳. פס'


def _suit_hcp(hand, suit):
    _hcp = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
    ranks = {c[0] for c in hand if c[1] == suit}
    return sum(_hcp.get(r, 0) for r in ranks)


def _suit_quality(hand, suit):
    """
    ספור יחידות כבוד בצבע:
      A, K, Q. כל אחד 1 יחידה
      JT      . J וגם T בצבע = 1 יחידה
      T98     . T וגם 9 וגם 8 בצבע = 1 יחידה
    """
    ranks = {c[0] for c in hand if c[1] == suit}
    count = sum(1 for r in ('A', 'K', 'Q') if r in ranks)
    if 'J' in ranks and 'T' in ranks:
        count += 1
    if 'T' in ranks and '9' in ranks and '8' in ranks:
        count += 1
    return count


def _min_level(open_bid, overcall_suit):
    """מחשב את הרמה המינימלית לאוברקול בצבע נתון."""
    _rank = {'C': 1, 'D': 2, 'H': 3, 'S': 4, 'N': 5}
    open_level = int(open_bid[0]) if open_bid[0].isdigit() else 1
    open_suit  = _bid_to_suit(open_bid)
    oc_rank    = _rank.get(overcall_suit, 0)
    op_rank    = _rank.get(open_suit, 0) if open_suit else 0

    if open_level == 1:
        return 1 if oc_rank > op_rank else 2
    return open_level + 1 if oc_rank <= op_rank else open_level


def _bid_to_suit(bid):
    _map = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
    for ch, suit in _map.items():
        if ch in bid:
            return suit
    return None
