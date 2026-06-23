"""
צבע רביעי (Fourth Suit Forcing) — Acol
כאשר שלושה צבעים הוכרזו, הצבע הרביעי הוא כפוי ושואל לעוצר.
"""

from engine.scoring import hcp, distribution, has_stopper
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS
_RANK = {'C': 1, 'D': 2, 'H': 3, 'S': 4}
_SYM  = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}


def _suit_of(bid):
    for ch, s in _SYM.items():
        if ch in bid:
            return s
    return None


def compute_fourth_suit(bid1, bid2, bid3):
    """מחזיר (suit, sym, level) של הצבע הרביעי."""
    used = {_suit_of(b) for b in [bid1, bid2, bid3] if _suit_of(b)}
    lvl3 = int(bid3[0]) if bid3[0].isdigit() else 1
    s3   = _suit_of(bid3)
    for suit in ['S', 'H', 'D', 'C']:
        if suit not in used:
            lvl = lvl3 if _RANK.get(suit, 0) > _RANK.get(s3, 0) else lvl3 + 1
            return suit, _S[suit], lvl
    return None, None, None


def s_correct_bid(hand, bid1, bid2, bid3):
    """
    הכרזה נכונה ל-S אחרי שלושה צבעים.
    מחזיר (bid, explanation, is_fsf).
    """
    h  = hcp(hand)
    d  = distribution(hand)
    s3 = _suit_of(bid3)
    s2 = _suit_of(bid2)
    lvl3 = int(bid3[0]) if bid3[0].isdigit() else 1

    fs, fsym, flvl = compute_fourth_suit(bid1, bid2, bid3)

    # יד חלשה — פחות מ-12 נק׳: לא מכריזים צבע רביעי
    if h <= 11:
        return f'{lvl3}NT', f'{h} נק׳ — מינימום, עוצר', False

    # 4+ תמיכה בצבע הפתיחה (bid1) — מיגור
    s1 = _suit_of(bid1)
    if s1 and s1 in ('H', 'S') and d.get(s1, 0) >= 4:
        sym = _S[s1]
        return f'4{sym}', f'{h} נק׳, 4+ קלפי {sym} — תמיכה ישירה', False

    # 4+ תמיכה בצבע N השני
    if s3 and d.get(s3, 0) >= 4:
        sym = _S[s3]
        if h >= 13:
            return (f'4{sym}' if s3 in ('H', 'S') else '3NT'), f'{h} נק׳, 4+ קלפי {sym} — משחק', False
        return f'3{sym}', f'{h} נק׳, 4+ קלפי {sym} — הזמנה', False

    # 6+ בצבע S עצמו
    if s2 and d.get(s2, 0) >= 6:
        sym = _S[s2]
        return (f'4{sym}' if h >= 13 and s2 in ('H', 'S') else f'3{sym}'), f'{h} נק׳, 6+ קלפי {sym}', False

    # עוצר בצבע הרביעי → NT ישיר
    if fs and has_stopper(hand, fs):
        if h >= 13:
            return '3NT', f'{h} נק׳, יש עוצר ב-{fsym} — 3NT ישיר', False
        return f'{flvl - 1}NT', f'{h} נק׳, עוצר ב-{fsym} — NT הזמנה', False

    # FSF — הצבע הרביעי, שאלת עוצר
    # בדיקה: אם חסרים עוצרים ביותר מסדרה אחת לא מכוסה — FSF לא יעזור
    if fs and flvl:
        covered = {_suit_of(b) for b in [bid1, bid2, bid3] if _suit_of(b)}
        other_no_stopper = [
            s for s in ['S', 'H', 'D', 'C']
            if s not in covered and s != fs and not has_stopper(hand, s)
        ]
        if other_no_stopper:
            # חסרים עוצרים בשתי סדרות — הראה את הצבע הארוך של S
            if s2 and d.get(s2, 0) >= 5:
                sym2 = _S[s2]
                return f'3{sym2}', f'{h} נק׳ — חסרים עוצרים בשתי סדרות, מראה 5+ {sym2}', False
            return 'Pass', f'{h} נק׳ — חסרים עוצרים בשתי סדרות', False
        return f'{flvl}{fsym}', f'{h} נק׳ — צבע רביעי, שואל עוצר ב-{fsym}', True

    return 'Pass', f'{h} נק׳ — פס', False


def n_respond_fsf(hand, fsf_suit, opener_suit, responder_suit):
    """
    N מגיב לצבע רביעי של S.
    מחזיר (bid, explanation).
    """
    h    = hcp(hand)
    d    = distribution(hand)
    fsym = _S.get(fsf_suit, '')
    fsr  = _RANK.get(fsf_suit, 0)

    # עוצר בצבע הרביעי → NT
    if has_stopper(hand, fsf_suit):
        if h >= 15:
            return '3NT', f'יש עוצר ב-{fsym}, יד חזקה — 3NT'
        return '2NT', f'יש עוצר ב-{fsym} — 2NT'

    # 3+ קלפים בצבע S → תמיכה
    if responder_suit and d.get(responder_suit, 0) >= 3:
        rsym = _S[responder_suit]
        lvl  = 2 if _RANK.get(responder_suit, 0) > fsr else 3
        return f'{lvl}{rsym}', f'אין עוצר ב-{fsym}, 3+ קלפי {rsym} — תמיכה'

    # אין עוצר ואין תמיכה — חפש הכי הרבה שליטים
    # N יכול להציע: צבע הפתיחה (5+) או צבע הריבאד (4+)
    # S הראה: responder_suit (4+)
    # בחר את הצבע שN הכי ארוך בו
    best_suit = opener_suit
    best_len  = d.get(opener_suit, 0) if opener_suit else 0

    for s in ['S', 'H', 'D', 'C']:
        if s == fsf_suit:
            continue
        if s == responder_suit:
            continue
        if d.get(s, 0) > best_len:
            best_len  = d[s]
            best_suit = s

    opsym = _S.get(best_suit, '') if best_suit else ''
    lvl   = 2 if _RANK.get(best_suit, 0) > fsr else 3
    return f'{lvl}{opsym}', f'אין עוצר ב-{fsym} — חוזר ל-{opsym} ({best_len} קלפים)'


def s_final_bid(hand, n_response, responder_suit, opener_suit=None):
    """
    S מכריז אחרי תגובת N ל-FSF.
    מחזיר (bid, explanation).
    opener_suit: הצבע שN הכריז כריבאד (מיגור בד"כ).
    """
    h     = hcp(hand)
    d     = distribution(hand)
    nsym  = _suit_of(n_response)
    s2sym = _S.get(responder_suit, '') if responder_suit else ''

    # N הראה עוצר (ענה NT)
    if 'NT' in n_response:
        if n_response == '2NT' and h <= 12:
            return 'Pass', f'{h} נק׳ — שותף מינימום, נשאר ב-2NT'
        return '3NT', f'{h} נק׳ — שותף יש עוצר, 3NT'

    # N תמך בצבע S — יש התאמה → משחק
    if nsym == responder_suit:
        if responder_suit in ('H', 'S'):
            return f'4{s2sym}', f'{h} נק׳ — שותף תמך, יש התאמה — 4{s2sym}'
        return '3NT', f'{h} נק׳ — 3NT'

    # N חזר למינור (אין עוצר, אין תמיכה) — חפש הכי הרבה שליטים
    n_suit = nsym  # המינור שN חזר אליו (5+)
    if n_suit in ('C', 'D'):
        # חשב התאמות אפשריות
        # מיגור: N הראה 4+ ב-opener_suit
        major_fit = 0
        major_suit = None
        if opener_suit and opener_suit in ('H', 'S'):
            major_fit = d.get(opener_suit, 0) + 4
            major_suit = opener_suit

        # מינור: N חזר = 5+
        minor_fit = d.get(n_suit, 0) + 5
        minor_sym = _S[n_suit]

        # בחר הכי טוב (עדיפות למיגור בשוויון)
        if major_suit and major_fit >= minor_fit and major_fit >= 7:
            msym = _S[major_suit]
            return f'4{msym}', f'{h} נק׳ — {d.get(major_suit,0)}+4={major_fit} שליטים ב-{msym} — 4{msym}'

        if minor_fit >= 8 and h >= 16:
            return f'5{minor_sym}', f'{h} נק׳ — {d.get(n_suit,0)}+5={minor_fit} שליטים ב-{minor_sym} — 5{minor_sym}'

        if major_suit and major_fit >= 7:
            msym = _S[major_suit]
            return f'4{msym}', f'{h} נק׳ — {d.get(major_suit,0)}+4={major_fit} שליטים ב-{msym} — 4{msym}'

    return 'Pass', f'{h} נק׳ — אין עוצר ואין התאמה טובה, פס'
