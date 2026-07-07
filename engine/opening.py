"""
פתיחות Acol — כל פתיחות ראשונות
מחזיר (bid, explanation) לפי כללי Acol סטנדרטי.
"""

from engine.scoring import hcp, is_balanced, distribution
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS  # קיצור


def _longest_suit(dist):
    return max(dist, key=dist.get)


def _suit_sym(s):
    return _S[s]


def opening_bid(hand, position=1):
    """
    מחשב את הפתיחה הנכונה לפי Acol.
    position: 1/2 = קפדני, 3 = מקל (Weak Two).
    מחזיר (bid_str, explanation_str).
    """
    h   = hcp(hand)
    bal = is_balanced(hand)
    d   = distribution(hand)

    # ── פרי-אמפטים ─────────────────────────────────────────────────────────
    for suit in ['S', 'H', 'D', 'C']:
        if d[suit] >= 7 and h <= 12:
            return f'3{_S[suit]}', (
                f'{h} נקודות גבוהות, {d[suit]} קלפי {_S[suit]}, פרי-אמפט'
            )

    # ── 2 חלש ────────────────────────────────────────────────────────────────
    if 6 <= h <= 9:
        for suit in ['S', 'H', 'D']:  # קלאבס לא פותחים 2 חלש
            if d[suit] == 6:
                honors = sum(1 for c in hand if c[1] == suit and c[0] in ('A', 'K', 'Q', 'J'))
                has_top = any(c[1] == suit and c[0] in ('A', 'K') for c in hand)
                if honors >= 2 and has_top:
                    if position <= 2:
                        other_major = 'H' if suit == 'S' else 'S'
                        aces = sum(1 for c in hand if c[0] == 'A')
                        if aces >= 2 or d[other_major] >= 4:
                            continue
                    return f'2{_S[suit]}', (
                        f'{h} נקודות גבוהות, 6 קלפי {_S[suit]}, פתיחה חלשה'
                    )

    # ── פס ──────────────────────────────────────────────────────────────────
    if h < 12:
        return 'Pass', f'{h} נקודות גבוהות, לא מספיק לפתיחה'

    # ── 2♣ חזקה ─────────────────────────────────────────────────────────────
    if h >= 20:
        return '2♣', f'{h} נקודות גבוהות, 2♣ כפוי'

    # ── 1NT ─────────────────────────────────────────────────────────────────
    if 15 <= h <= 17 and bal:
        return '1NT', f'{h} נקודות גבוהות, יד מאוזנת, 1NT'

    # ── 1 בצבע (12-19 HCP) ──────────────────────────────────────────────────
    return _best_suit_opening(h, d)


def _best_suit_opening(h, d):
    """בחר את הפתיחה הטובה ביותר בצבע לפי Acol."""

    # 5+ קלפי מיגור עיקרי — פתח בגבוה ביותר
    if d['S'] >= 5 and d['S'] >= d['H']:
        return '1♠', f'{h} נקודות גבוהות, {d["S"]} קלפי ♠'
    if d['H'] >= 5:
        return '1♥', f'{h} נקודות גבוהות, {d["H"]} קלפי ♥'
    if d['S'] >= 5:
        return '1♠', f'{h} נקודות גבוהות, {d["S"]} קלפי ♠'

    # מינורים — כלל: ארוך יותר; שוויון: 4-4/5-5 → גבוה (♦), 3-3 → נמוך (♣)
    dc, dd = d['C'], d['D']
    if dd > dc:
        return '1♦', f'{h} נקודות גבוהות, {dd} קלפי ♦'
    if dc > dd:
        return '1♣', f'{h} נקודות גבוהות, {dc} קלפי ♣'
    # שוויון
    if dd >= 4:
        return '1♦', f'{h} נקודות גבוהות, {dd} קלפי ♦ ו-{dc} קלפי ♣ — פותח בגבוה'
    return '1♣', f'{h} נקודות גבוהות, {dd} קלפי ♦ ו-{dc} קלפי ♣ — פותח בנמוך'
