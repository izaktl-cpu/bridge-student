"""
נגטיב דאבל. Acol
N פותח 1 מינור, E מכריז אוברקול מיגור, S מכריז נגטיב דאבל.
"""

from engine.scoring import hcp, distribution, has_stopper, is_balanced
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
    - רמה 1: 7+ HCP | רמה 2: 8+ HCP (אין תקרה עליונה)
    - 4+ במיגור שלא הוכרז
    - 3+ בכל מינור שלא הוכרז
    - לא 5+ קלפי מיגור (עדיף הכרזה ישירה)
    """
    h = hcp(s_hand)
    d = distribution(s_hand)

    min_hcp = 7 if e_level == 1 else 8
    if h < min_hcp:
        return False

    unbid_majors = [s for s in ['S', 'H'] if s not in (n_suit, e_suit)]
    unbid_minors = [s for s in ['D', 'C'] if s not in (n_suit, e_suit)]

    for m in unbid_majors:
        if d[m] >= 5:
            return False

    if unbid_majors:
        if not any(d[m] >= 4 for m in unbid_majors):
            return False
        for mn in unbid_minors:
            if d[mn] < 3:
                return False
    elif len(unbid_minors) == 2:
        # אין מיגור פנוי (שני המיגורים כבר הוכרזו). 4+ במינור אחד, 3+ בשני (בלי סדר קבוע)
        lens = sorted((d[mn] for mn in unbid_minors), reverse=True)
        if not (lens[0] >= 4 and lens[1] >= 3):
            return False
    else:
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

    # 2. 13+ → X עם 4 מיגור פנוי, 3NT עם עוצר, קיו ביט ללא עוצר ובלי מיגור
    if h >= 13:
        for major in unbid_majors:
            if d[major] >= 4:
                return 'X', f'{h} נק׳, 4 קלפי {_S[major]}. נגטיב דאבל'
        if has_stopper(s_hand, e_suit):
            return '3NT', f'{h} נק׳, עוצר ב{_S[e_suit]}. 3NT'
        sym = _S[e_suit]
        return f'{e_level + 1}{sym}', f'{h} נק׳. קיו ביט'

    # 3. 11-12 עם עוצר → 2NT (לפני תמיכה. NT עדיף על מינור)
    if h >= 11 and has_stopper(s_hand, e_suit):
        return '2NT', f'{h} נק׳, עוצר ב{_S[e_suit]}. 2NT'

    # 3b. 4+ תמיכה לצבע N, 6+ נק'
    if d[n_suit] >= 4 and h >= 6:
        sym = _S[n_suit]
        if h >= 11:
            return f'3{sym}', f'{h} נק׳, {d[n_suit]} קלפי {sym}. הזמנה'
        return f'2{sym}', f'{h} נק׳, {d[n_suit]} קלפי {sym}. תמיכה'

    # 4. מינור ארוך (6+) עם 11+ נק'. עדיפות על X
    for minor in unbid_minors:
        if d[minor] >= 6 and h >= 11:
            sym = _S[minor]
            lvl = _min_lvl(minor, e_suit, e_level)
            return f'{lvl}{sym}', f'{h} נק׳, {d[minor]} קלפי {sym}'

    # 5. X נגטיב: 7+ נק' (רמה 1) / 8+ (רמה 2)
    min_x_hcp = 7 if e_level == 1 else 8
    if h >= min_x_hcp:
        if unbid_majors:
            for major in unbid_majors:
                if d[major] >= 4:
                    return 'X', f'{h} נק׳, 4 קלפי {_S[major]}. נגטיב דאבל'
        elif len(unbid_minors) == 2:
            # אין מיגור פנוי (שני המיגורים כבר הוכרזו). 4+ במינור אחד, 3+ בשני
            long_mn, short_mn = sorted(unbid_minors, key=lambda mn: -d[mn])
            if d[long_mn] >= 4 and d[short_mn] >= 3:
                return 'X', (f'{h} נק׳, {d[long_mn]}+{d[short_mn]} קלפים '
                              f'ב{_S[long_mn]}/{_S[short_mn]}. נגטיב דאבל')

    # 6. מינור 5 קלפים, 11+ נק'
    for minor in unbid_minors:
        if d[minor] >= 5 and h >= 11:
            sym = _S[minor]
            lvl = _min_lvl(minor, e_suit, e_level)
            return f'{lvl}{sym}', f'{h} נק׳, {d[minor]} קלפי {sym}'

    # 6. 1NT: 7-10 נק', עוצר
    if h >= 7 and has_stopper(s_hand, e_suit):
        return '1NT', f'{h} נק׳, עוצר ב{_S[e_suit]}. 1NT'

    # 7. פס
    return 'Pass', f'{h} נק׳. אין מספיק'


def opener_after_cue(n_hand, n_suit, e_suit):
    """
    ריבאד N אחרי קיו ביט של S (S הראה 13+ נק', מבקש עוצר בצבע E).
    עדיפות: עוצר → 3NT | מיגור פנוי 4+ → מיגור | חזרה למינור.
    """
    d = distribution(n_hand)
    if has_stopper(n_hand, e_suit):
        return '3NT', f'עוצר ב{_S[e_suit]}. 3NT'
    unbid_major = next((m for m in ['S', 'H'] if m not in (n_suit, e_suit)), None)
    if unbid_major and d[unbid_major] >= 4:
        sym = _S[unbid_major]
        lvl = _min_lvl(unbid_major, e_suit, 2)   # קיו ביט היה ברמה 2
        return f'{lvl}{sym}', f'{d[unbid_major]} קלפי {sym}'
    sym = _S[n_suit]
    return f'3{sym}', f'אין עוצר ב{_S[e_suit]}. חוזר ל{sym}'


def opener_after_natural(n_hand, n_suit, s_suit, e_suit=None):
    """
    ריבאד N אחרי הכרזה ישירה של S במיגור (5+ קלפים, 7-12 נק').
    מחזיר (bid, explanation).
    """
    h = hcp(n_hand)
    d = distribution(n_hand)
    sym = _S[s_suit]
    support = d[s_suit]

    if support >= 3:
        if s_suit == n_suit:
            # S הרים את סדרת N (לימיט ריס) → Pass מינימום, 3NT חזק
            if h >= 15 and e_suit and has_stopper(n_hand, e_suit):
                return '3NT', f'{h} נק׳, עוצר ב{_S[e_suit]}. 3NT'
            if h >= 15:
                return f'5{_S[n_suit]}', f'{h} נק׳. משחק במינור'
            return 'Pass', f'{h} נק׳. מינימום, פס'
        s_level = _min_lvl(s_suit, e_suit, 1) if e_suit else 1
        min_raise = s_level + 1
        if h >= 18:
            return f'{max(min_raise, 4)}{sym}', f'תמיכה ב{sym} + {h} נק׳. משחק'
        if h >= 15:
            return f'{max(min_raise, 3)}{sym}', f'תמיכה ב{sym} + {h} נק׳. הזמנה'
        return f'{min_raise}{sym}', f'תמיכה ב{sym} + {h} נק׳. מינימום'

    # אין תמיכה. עוצר ב-E → 2NT
    if e_suit and has_stopper(n_hand, e_suit):
        return '2NT', f'עוצר ב{_S[e_suit]}. 2NT'

    # סדרה שנייה (לא n_suit, לא s_suit, לא e_suit)
    excluded = {n_suit, s_suit}
    if e_suit:
        excluded.add(e_suit)
    for suit in ['C', 'D', 'H', 'S']:
        if suit not in excluded and d[suit] >= 4:
            # רברס = סדרה שנייה גבוהה יותר מ-n_suit ברמה גבוהה → דורש 18+
            is_reverse = _RANK[suit] > _RANK[n_suit]
            if is_reverse and h < 18:
                continue
            return f'2{_S[suit]}', f'{d[suit]} קלפי {_S[suit]}. סדרה שנייה'

    # ריבאד בסדרת N עצמה (5+ קלפים)
    if d[n_suit] >= 5:
        lvl = 3 if h >= 15 else 2
        return f'{lvl}{_S[n_suit]}', f'{d[n_suit]} קלפי {_S[n_suit]}. ריבאד'

    return 'Pass', f'אין תמיכה ואין סדרה. פס'


def opener_rebid(n_hand, n_suit, e_suit, e_level=1):
    """
    ריבאד N אחרי נגטיב דאבל של S.
    עדיפות: תמיכה (3+) בסדרה שהראה ה-X > קיו ביט (18-21, לא מאוזן-18-19) >
             2NT (18-19 מאוזן+עוצר) > NT מינימלי (12-14 מאוזן+עוצר) > חזרה למינור/לסדרה.
    מחזיר (bid, explanation).
    """
    h   = hcp(n_hand)
    d   = distribution(n_hand)
    bal = is_balanced(n_hand)

    unbid_majors = [s for s in ['S', 'H'] if s not in (n_suit, e_suit)]
    unbid_minors = [s for s in ['D', 'C'] if s not in (n_suit, e_suit)]

    # תמיכה (3+) בסדרה שהראה ה-X. קודמת לכל השאר
    for major in unbid_majors:
        if d[major] >= 3:
            sym     = _S[major]
            min_lvl = _min_lvl(major, e_suit, e_level)
            lvl     = min_lvl if h <= 14 else min_lvl + 1
            note    = 'מינימום' if h <= 14 else 'קפיצה'
            return f'{lvl}{sym}', f'{d[major]} קלפי {sym}, {h} נק׳. {note}'

    # ללא תמיכה: קיו ביט (18-21, לא מאוזן-18-19)
    if 18 <= h <= 21 and not (bal and 18 <= h <= 19):
        cue_lvl = e_level + 1
        return f'{cue_lvl}{_S[e_suit]}', f'{h} נק׳. קיו ביט'

    # 18-19 מאוזן + עוצר → קפיצה ל-NT
    if 18 <= h <= 19 and bal and has_stopper(n_hand, e_suit):
        return f'{e_level + 1}NT', f'{h} נק׳, מאוזן, עוצר ב{_S[e_suit]}'

    # 12-14 מאוזן + עוצר → NT מינימלי
    if 12 <= h <= 14 and bal and has_stopper(n_hand, e_suit):
        return f'{e_level}NT', f'{h} נק׳, מאוזן, עוצר ב{_S[e_suit]}'

    for minor in unbid_minors:
        if d[minor] >= 4:
            sym = _S[minor]
            lvl = _min_lvl(minor, e_suit, e_level)
            return f'{lvl}{sym}', f'{d[minor]} קלפי {sym}'

    sym = _S[n_suit]
    lvl = _min_lvl(n_suit, e_suit, e_level)
    if h >= 15:
        lvl = max(lvl, 3)  # קפיצה = חזק 15-17
    return f'{lvl}{sym}', f'חוזר על {sym}'
