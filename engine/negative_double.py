"""
נגטיב דאבל — Acol
N פותח 1 מינור, E מכריז אוברקול מיגור, S מכריז נגטיב דאבל.
"""

from engine.scoring import hcp, distribution, has_stopper
from engine.cards import SUIT_SYMBOLS

_S    = SUIT_SYMBOLS
_RANK = {'C': 1, 'D': 2, 'H': 3, 'S': 4}


def _unbid(n_suit, e_suit):
    return [s for s in ['S', 'H', 'D', 'C'] if s not in (n_suit, e_suit)]


def _min_lvl(suit, blocker_suit, blocker_level):
    return blocker_level if _RANK[suit] > _RANK[blocker_suit] else blocker_level + 1


def can_negative_double(s_hand, n_suit, e_suit, e_level=1):
    """
    האם S יכול לכריז נגטיב דאבל?
    - רמה 1: 7–12 HCP | רמה 2: 8–12 HCP
    - 4+ במיגור שלא הוכרז
    - 3+ בכל מינור שלא הוכרז
    - לא 5+ קלפי מיגור (עדיף הכרזה ישירה)
    """
    h = hcp(s_hand)
    d = distribution(s_hand)

    if not (8 <= h <= 12):
        return False

    unbid_majors = [s for s in ['S', 'H'] if s not in (n_suit, e_suit)]
    unbid_minors = [s for s in ['D', 'C'] if s not in (n_suit, e_suit)]

    for m in unbid_majors:
        if d[m] >= 5:
            return False

    if unbid_majors and not any(d[m] >= 4 for m in unbid_majors):
        return False

    for mn in unbid_minors:
        if d[mn] < 3:
            return False

    return True


def s_response(s_hand, n_suit, e_suit, e_level=1):
    """
    תגובת S אחרי N-1m, E-1M.
    עדיפויות: מיגור → 3NT/קיו(13+) → 2NT → מינור → X נגטיב → 1NT → פס
    """
    h = hcp(s_hand)
    d = distribution(s_hand)

    unbid_majors = [s for s in ['S', 'H'] if s not in (n_suit, e_suit)]
    unbid_minors = [s for s in ['D', 'C'] if s not in (n_suit, e_suit)]

    # 1. 5+ מיגור פנוי
    for major in unbid_majors:
        if d[major] >= 5:
            lvl     = _min_lvl(major, e_suit, e_level)
            min_hcp = 6 if lvl == e_level else 11
            if h >= min_hcp:
                sym = _S[major]
                return f'{lvl}{sym}', f'{h} נק׳, {d[major]} קלפי {sym}'

    # 2. 13+ → 3NT עם עוצר, קיו ביט ללא עוצר
    if h >= 13:
        if has_stopper(s_hand, e_suit):
            return '3NT', f'{h} נק׳, עוצר ב{_S[e_suit]} — 3NT'
        sym = _S[e_suit]
        return f'{e_level + 1}{sym}', f'{h} נק׳ — קיו ביט'

    # 3. 11-12 עם עוצר → 2NT
    if h >= 11 and has_stopper(s_hand, e_suit):
        return '2NT', f'{h} נק׳, עוצר ב{_S[e_suit]} — 2NT'

    # 4. 5+ מינור, 11+ נק'
    for minor in unbid_minors:
        if d[minor] >= 5 and h >= 11:
            sym = _S[minor]
            lvl = _min_lvl(minor, e_suit, e_level)
            return f'{lvl}{sym}', f'{h} נק׳, {d[minor]} קלפי {sym}'

    # 5. X נגטיב: 8+ נק', 4+ מיגור פנוי
    for major in unbid_majors:
        if d[major] >= 4 and h >= 8:
            return 'X', f'{h} נק׳, 4 קלפי {_S[major]} — נגטיב דאבל'

    # 6. 1NT: 7-10 נק', עוצר
    if h >= 7 and has_stopper(s_hand, e_suit):
        return '1NT', f'{h} נק׳, עוצר ב{_S[e_suit]} — 1NT'

    # 7. פס
    return 'Pass', f'{h} נק׳ — אין מספיק'


def opener_after_cue(n_hand, n_suit, e_suit):
    """
    ריבאד N אחרי קיו ביט של S (S הראה 13+ נק', מבקש עוצר בצבע E).
    עדיפות: מיגור 4 קלפים → 3NT עם עוצר → חזרה למינור.
    """
    d = distribution(n_hand)
    unbid_major = next((m for m in ['S', 'H'] if m not in (n_suit, e_suit)), None)
    if unbid_major and d[unbid_major] >= 4:
        sym = _S[unbid_major]
        lvl = _min_lvl(unbid_major, e_suit, 2)   # קיו ביט היה ברמה 2
        return f'{lvl}{sym}', f'{d[unbid_major]} קלפי {sym}'
    if has_stopper(n_hand, e_suit):
        return '3NT', f'עוצר ב{_S[e_suit]} — 3NT'
    sym = _S[n_suit]
    return f'3{sym}', f'אין עוצר ב{_S[e_suit]} — חוזר ל{sym}'


def opener_after_natural(n_hand, s_suit):
    """
    ריבאד N אחרי הכרזה ישירה של S במיגור (5+ קלפים, 7-12 נק').
    מחזיר (bid, explanation).
    """
    h = hcp(n_hand)
    d = distribution(n_hand)
    sym = _S[s_suit]
    support = d[s_suit]

    if support >= 3:
        if h >= 16:
            return f'4{sym}', f'תמיכה ב{sym} + {h} נק׳ — משחק'
        if h >= 14:
            return f'3{sym}', f'תמיכה ב{sym} + {h} נק׳ — הזמנה'
        return 'Pass', f'תמיכה ב{sym} אבל {h} נק׳ — לא מספיק להזמנה'

    return 'Pass', f'אין 3+ תמיכה ב{sym} — פס'


def opener_rebid(n_hand, n_suit, e_suit, e_level=1):
    """
    ריבאד N אחרי נגטיב דאבל של S.
    מחזיר (bid, explanation).
    """
    h = hcp(n_hand)
    d = distribution(n_hand)

    unbid_majors = [s for s in ['S', 'H'] if s not in (n_suit, e_suit)]
    unbid_minors = [s for s in ['D', 'C'] if s not in (n_suit, e_suit)]

    for major in unbid_majors:
        if d[major] >= 3:
            sym = _S[major]
            lvl = _min_lvl(major, e_suit, e_level)
            return f'{lvl}{sym}', f'{d[major]} קלפי {sym}'

    if h >= 12 and has_stopper(n_hand, e_suit):
        return f'{e_level}NT', f'{h} נק׳, עוצר ב{_S[e_suit]}'

    for minor in unbid_minors:
        if d[minor] >= 4:
            sym = _S[minor]
            lvl = _min_lvl(minor, e_suit, e_level)
            return f'{lvl}{sym}', f'{d[minor]} קלפי {sym}'

    sym = _S[n_suit]
    lvl = _min_lvl(n_suit, e_suit, e_level)
    return f'{lvl}{sym}', f'חוזר על {sym}'
