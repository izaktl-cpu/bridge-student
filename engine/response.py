"""
מענה Acol לכל פתיחה ראשונה.
מחזיר (bid, explanation).
"""

from engine.scoring import hcp, is_balanced, distribution, suit_len, dist_fit_pts, has_stopper
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


# ═══════════════════════════════════════════════════════════════════════════
#  מענה ל-1NT (15-17)
# ═══════════════════════════════════════════════════════════════════════════

def respond_1nt(hand):
    h = hcp(hand)
    if h <= 7:
        return 'Pass', '0-7 נקודות גבוהות, מכריזים פס'
    if h <= 9:
        return '2NT', '8-9 נקודות גבוהות, מזמינים למשחק'
    return '3NT', '10 נקודות גבוהות ומעלה, מכריזים חוזה משחק'


# ═══════════════════════════════════════════════════════════════════════════
#  מענה ל-1♥ / 1♠
# ═══════════════════════════════════════════════════════════════════════════

def respond_major(hand, opener_suit):
    """opener_suit: 'H' or 'S'"""
    h   = hcp(hand)
    d   = distribution(hand)
    bal = is_balanced(hand)
    sym = _S[opener_suit]
    fit = d[opener_suit]  # מספר קלפים אצל המשיב בצבע הפותח

    if h <= 5:
        return 'Pass', '0-5 נקודות גבוהות, מכריזים פס'

    # חוק ה-19: 5+ קלפים + 7+ נקג → 10 קלפים משותפים → 4M ישירות
    if fit >= 5 and h >= 7:
        return f'4{sym}', f'5 קלפי {sym} ו-{h} נקודות. 10 קלפים משותפים, קפיצה למשחק'

    # תמיכה בצבע הפותח. מוסיפים נקודות חלוקה
    if fit >= 3:
        dp  = dist_fit_pts(hand, trump=opener_suit)
        tot = h + dp
        dp_str = f'\nיש {dp} נקודות חוסר' if dp > 0 else ''
        if tot >= 13:
            return f'4{sym}', f'יש {h} נקודות גבוהות{dp_str}\nסה״כ {tot} עם תמיכה ב-{sym}, קופצים למשחק מלא'
        if tot >= 10:
            return f'3{sym}', f'יש {h} נקודות גבוהות{dp_str}\nסה״כ {tot} עם תמיכה ב-{sym}, הזמנה למשחק'
        return f'2{sym}', f'יש {h} נקודות גבוהות{dp_str}\nסה״כ {tot} עם תמיכה ב-{sym}'

    # ללא תמיכה. 1♠ אחרי 1♥: רמה 1, מספיק 4+ קלפים ו-6+ נקודות
    if opener_suit == 'H' and d['S'] >= 4 and h >= 6:
        return '1♠', '6 נקודות ומעלה, 4 קלפי ♠ ומעלה'

    # צבע חדש ברמה 2: חייב 11+ נקודות ו-5+ קלפים
    if h >= 11:
        best = _best_new_suit(d, exclude=opener_suit, min_len=5)
        if best:
            return f'2{_S[best]}', f'5+ קלפי {_S[best]}, 11+ נקודות. סדרה חדשה ברמה 2'

    # NT
    if h >= 13:
        return '3NT', '13 נקודות ומעלה, יד מאוזנת, קופצים למשחק'
    if h >= 11:
        return '2NT', '11-12 נקודות, יד מאוזנת, מזמינים למשחק'
    return '1NT', '6-10 נקודות ללא תמיכה בסדרת הפותח'


# ═══════════════════════════════════════════════════════════════════════════
#  מענה ל-1♣ / 1♦
# ═══════════════════════════════════════════════════════════════════════════

def respond_minor(hand, opener_suit):
    """opener_suit: 'C' or 'D'"""
    h   = hcp(hand)
    d   = distribution(hand)
    bal = is_balanced(hand)
    sym = _S[opener_suit]
    fit = d[opener_suit]
    dp  = dist_fit_pts(hand, trump=opener_suit)  # נקודות חלוקה עם התאמה
    tot = h + dp                                  # סה״כ עם חוסר

    if h <= 5:
        return 'Pass', '0-5 נקודות גבוהות, מכריזים פס'

    if h >= 6:
        # סדרה חדשה (4+ קלפים): הסדרה הארוכה ביותר קודמת.
        # שוויון ב-5+: הגבוהה קודמת. שוויון בדיוק ב-4: עולים בסולם (הזולה קודמת).
        hs, hh = d['S'], d['H']
        _rank = {'D': 0, 'H': 1, 'S': 2}
        candidates = []
        if opener_suit == 'C' and d['D'] >= 4:
            candidates.append((d['D'], _rank['D'], '1♦', 'קלפי ♦'))
        if hh >= 4:
            candidates.append((hh, _rank['H'], '1♥', 'קלפי ♥'))
        if hs >= 4:
            candidates.append((hs, _rank['S'], '1♠', 'קלפי ♠'))

        if candidates:
            max_len = max(c[0] for c in candidates)
            tied = [c for c in candidates if c[0] == max_len]
            chosen = (max(tied, key=lambda c: c[1]) if max_len >= 5
                      else min(tied, key=lambda c: c[1]))
            _, _, bid, desc = chosen
            return bid, f'{max_len}+ {desc}. הסדרה הארוכה ביותר'

    if opener_suit == 'C' and fit >= 5:
        dp_note = f' (+{dp} חוסר)' if dp else ''
        if h <= 10:
            return '2♣', f'קלפי ♣ 5+, נקודות {h}{dp_note}. תמיכה, מסיים את המכרז'
        if not bal:
            if h >= 13:
                return '3NT', f'נקודות {h}{dp_note}. קופץ למשחק'
            return '3♣', f'קלפי ♣ 5+, נקודות {h}{dp_note}. תמיכה חזקה, מזמין למשחק'
        # מאוזן 11+ נופל לבלוק ה-NT למטה (2NT/3NT)
    if opener_suit == 'D' and fit >= 4:
        dp_note = f' (+{dp} חוסר)' if dp else ''
        all_stopped = (has_stopper(hand, 'H') and has_stopper(hand, 'S')
                       and has_stopper(hand, 'C'))
        if h >= 13:
            if not bal:
                return f'3{sym}', f'5+ קלפי {sym}, {h}{dp_note} נקודות לא מאוזן. כפוי למשחק'
            # מאוזן 13+ נופל ל-3NT למטה
        elif h >= 11:
            if not bal or not all_stopped:
                return f'3{sym}', f'תמיכה ב-{sym}, {h}{dp_note} נקודות. תמיכה חזקה, מזמין'
            # מאוזן עם עוצרים נופל ל-2NT למטה
        else:  # 6-10 נקודות
            if fit >= 5 or not bal:
                return f'2{sym}', f'תמיכה ב-{sym}, נקודות {h}{dp_note}. מסיים את המכרז'
            # 4 קלפי מאוזן חלש נופל ל-1NT למטה

    if bal:
        if h >= 13:
            return '3NT', '13+ נקודות מאוזן. קופץ למשחק'
        if h >= 11:
            return '2NT', '11-12 נקודות מאוזן. מזמין לחוזה 3NT'
        return '1NT', '6-10 נקודות מאוזן. אין סדרה 4-קלפית'

    if opener_suit == 'D' and d['C'] >= 5 and h >= 11:
        return '2♣', '5+ קלפי ♣, 11+ נקודות. סדרה חדשה ברמה 2'

    return '1NT', '6-10 נקודות. אין סדרה 4-קלפית, עוצר את המכרז'


# ═══════════════════════════════════════════════════════════════════════════
#  מענה ל-1♦/1♣ עם 5+ מינור, 11+ (שיעור 15 — NT במינור)
# ═══════════════════════════════════════════════════════════════════════════

def respond_minor_nt(hand, minor):
    """S: 5+ קלפי מינור, 11-13 HCP. קפיצה ישירה ל-3 במינור."""
    sym = _S[minor]
    return f'3{sym}', f'5+ קלפי {sym}, 11-13 נקודות. קפיצה ישירה'


def opener_rebid_after_3minor(hand, minor):
    """N: לאחר קפיצת S ל-3 במינור (11-13). שואל עוצר רק אם בטוח ב-25+ נק' משותפות
    (S מובטח 11+, אז צריך N בעצמו 14+). אחרת נשאר הכי נמוך שאפשר — Pass."""
    if hcp(hand) < 14:
        return 'Pass', 'לא בטוח ב-25+ נקודות משותפות. נשארים ב-3 במינור'
    other = [su for su in ['H', 'S', 'C', 'D'] if su != minor]
    missing = [su for su in other if not has_stopper(hand, su)]
    if not missing:
        return '3NT', 'עוצרים בכל הסדרות. 3NT'
    _suit_rank = {'C': 0, 'D': 1, 'H': 2, 'S': 3}
    ask = missing[0]
    if _suit_rank[ask] <= _suit_rank[minor]:
        return '3NT', f'3{_S[ask]} לא חוקי מעל 3{_S[minor]} (סדרה נמוכה יותר). 3NT ישיר'
    return f'3{_S[ask]}', f'שואל עוצר ב-{_S[ask]}'


def responder_stopper_reply(hand, minor, ask_suit):
    """S: עונה לשאלת העוצר של N. יש עוצר → 3NT.
    אין עוצר → חוזר לרמה הכי נמוכה האפשרית במינור (4m, לא קופצים ל-5m —
    N כבר יודע ש-S מובטח 11-13 ויחליט בעצמו אם להרים ל-5m)."""
    sym = _S[minor]
    if has_stopper(hand, ask_suit):
        return '3NT', f'יש עוצר ב-{_S[ask_suit]}. 3NT'
    return f'4{sym}', f'אין עוצר ב-{_S[ask_suit]}. חוזרים ל-4{sym} (הרמה הכי נמוכה)'


def opener_after_stopper_denial(hand, minor):
    """N: לאחר ש-S חזר ל-4m (אין עוצר). N מחליט אם להרים ל-5m או להישאר.
    S מובטח 11-13; כדי להעריך 28+ נק' משותפות (סף משחק במינור) N צריך בעצמו 17+."""
    h   = hcp(hand)
    sym = _S[minor]
    if h >= 17:
        return f'5{sym}', f'{h} נקודות. מספיק ל-28+ נקודות משותפות, מקבלים למשחק'
    return 'Pass', f'{h} נקודות. לא בטוח ב-28+ משותפות, נשארים ב-4{sym}'


# ═══════════════════════════════════════════════════════════════════════════
#  מענה ל-2 חלש (2♥/2♠/2♦)
# ═══════════════════════════════════════════════════════════════════════════

def respond_weak2(hand, opener_suit):
    h   = hcp(hand)
    d   = distribution(hand)
    sym = _S[opener_suit]
    fit = d[opener_suit]

    if h <= 14 and fit <= 2:
        return 'Pass', 'ללא תמיכה מספקת. מכריזים פס'

    # עם תמיכה ואינטרס משחק מלא
    if fit >= 3 and h >= 15:
        return f'4{sym}', f'15+ נקודות עם 3+ קלפי {sym}. משחק מלא'
    if fit >= 3 and h >= 12:
        return f'3{sym}', f'12-14 נקודות עם 3+ קלפי {sym}. הרמת לחץ'

    # NT חזק עם כבלה בצבע הפותח
    if is_balanced(hand) and h >= 15:
        return '2NT', '15+ נקודות מאוזן. שאילת Ogust'

    if fit >= 2:
        return f'3{sym}', f'הרמת לחץ תחרותית ב-{sym}'

    return 'Pass', 'מכריזים פס'


# ═══════════════════════════════════════════════════════════════════════════
#  ממשק ראשי
# ═══════════════════════════════════════════════════════════════════════════

def get_response(hand, opening):
    """
    מחשב מענה לכל פתיחה.
    opening: מחרוזת כגון '1NT', '1♥', '1♣', '2♣', '2♥' וכד'.
    """
    if opening == '1NT':
        return respond_1nt(hand)
    if opening in ('1♥', '1♠'):
        suit = 'H' if opening == '1♥' else 'S'
        return respond_major(hand, suit)
    if opening in ('1♣', '1♦'):
        suit = 'C' if opening == '1♣' else 'D'
        return respond_minor(hand, suit)
    if opening == '2♣':
        return respond_2c(hand)
    if opening in ('2♥', '2♠', '2♦'):
        suit = {'2♥': 'H', '2♠': 'S', '2♦': 'D'}[opening]
        return respond_weak2(hand, suit)
    return 'Pass', 'לא זוהתה פתיחה. פס'


# ═══════════════════════════════════════════════════════════════════════════
#  עזרים פנימיים
# ═══════════════════════════════════════════════════════════════════════════

def responder_continuation(hand, n_rebid):
    """
    S מכריז בשלב המשך לאחר שN הכריז מחדש.
    n_rebid: ההכרזה האחרונה של N (למשל '2♦', '2NT', '3♣').
    """
    h = hcp(hand)

    if n_rebid in ('3NT', '4♥', '4♠', '5♣', '5♦'):
        return 'Pass', 'חוזה סופי'

    if n_rebid == '2NT':
        if h >= 8:
            return '3NT', '8+ נקודות. מקבל הזמנה'
        return 'Pass', '0-7 נקודות. דוחה הזמנה'

    if n_rebid and n_rebid[0] == '3':
        if h >= 9:
            return '3NT', '9+ נקודות. מכריז משחק מלא'
        return 'Pass', '0-8 נקודות. מינימום'

    # הכרזה ברמה 1 או 2 (מכרז פתוח)
    if h >= 11:
        return '3NT', '11+ נקודות. מכריז משחק מלא'
    if h >= 9:
        return '2NT', '9-10 נקודות. מזמין למשחק'
    return 'Pass', '0-8 נקודות. מינימום'


def responder_continuation_after_minor(hand, s_bid, n_rebid):
    """
    S מכריז בפעם השנייה אחרי שN הכריז מחדש בפתיחת מינור.
    מחזיר (bid, explanation) או ('Pass', ...) אם המכרז נגמר.
    """
    h   = hcp(hand)
    d   = distribution(hand)

    _map = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
    s_suit = next((suit for ch, suit in _map.items() if ch in s_bid), None)
    s_sym  = _S[s_suit] if s_suit else ''
    s_len  = d.get(s_suit, 0) if s_suit else 0

    # חוזה סופי
    if n_rebid in ('3NT', '4♥', '4♠', '5♣', '5♦'):
        return 'Pass', 'חוזה סופי'

    # אחרי תמיכה ב-2M (פותח חלש, 12-14)
    _suit_map = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
    n_suit = next((s for ch, s in _suit_map.items() if ch in n_rebid), None)
    if n_rebid.startswith('2') and n_suit in ('H', 'S'):
        n_sym = _S[n_suit]
        dp = dist_fit_pts(hand, trump=n_suit)
        tot = h + dp
        if tot >= 13:
            return f'4{n_sym}', f'13+ נקודות עם תמיכה ב-{n_sym}. משחק מלא'
        if tot >= 10:
            return f'3{n_sym}', f'10-12 נקודות עם תמיכה ב-{n_sym}. הזמנה למשחק'
        return 'Pass', f'6-9 נקודות. חלש, מכריזים פס'

    # אחרי הזמנה ב-3M (פותח בינוני, 15-17)
    if n_rebid.startswith('3') and n_suit in ('H', 'S'):
        n_sym = _S[n_suit]
        dp = dist_fit_pts(hand, trump=n_suit)
        tot = h + dp
        if tot >= 9:
            return f'4{n_sym}', f'9+ נקודות. מקבל הזמנה, משחק מלא'
        return 'Pass', '0-8 נקודות. דוחה הזמנה'

    # 5♠+4♥. אחרי 1♠, הראה ♥ (דורש 9+ נקודות; 13+ = קפיצה כפוי למשחק)
    if s_suit == 'S' and s_len >= 5 and d.get('H', 0) >= 4:
        if n_suit not in ('H', 'S') and not n_rebid.startswith('4'):
            if h >= 13:
                return '3♥', '5+ קלפי ♠ ו-4+ קלפי ♥, 13+ נקודות. כפוי למשחק'
            if h >= 9:
                return '2♥', '5+ קלפי ♠ ו-4+ קלפי ♥, 9-12 נקודות. מראה את הסדרה השנייה'
            return '2♠', '6-8 נקודות. חוזר לסדרת ♠'

    # 5♥+4♠. אחרי 1♥, מכריזים 1♠ ברמה 1 (ללא דרישת נקודות)
    if s_suit == 'H' and s_len >= 5 and d.get('S', 0) >= 4:
        if n_rebid == '1NT':
            return '1♠', '5+ קלפי ♥ ו-4+ קלפי ♠. מראה ♠ ברמה 1'

    # אחרי 1NT (12-14 מאוזן)
    if n_rebid == '1NT':
        if s_suit in ('H', 'S') and s_len >= 6:
            dp  = dist_fit_pts(hand, trump=s_suit)
            tot = h + dp
            if tot >= 13:
                return f'4{s_sym}', f'6+ קלפי {s_sym}, 13+ נקודות. קופץ למשחק'
            if tot >= 11:
                return f'3{s_sym}', f'6+ קלפי {s_sym}, 11-12 נקודות. מזמין למשחק'
            return f'2{s_sym}', f'6+ קלפי {s_sym}, 6-10 נקודות. חוזר לסדרה'
        if h >= 13:
            return '3NT', '13+ נקודות. קופץ למשחק'
        if h >= 11:
            return '2NT', '11-12 נקודות. מזמין למשחק'
        return 'Pass', '6-10 נקודות. מינימום, מכריזים פס'

    # אחרי 2♣/2♦ (שותף לא תמך. צריך יותר נקודות לקפוץ למשחק)
    if n_rebid in ('2♣', '2♦'):
        if s_suit in ('H', 'S') and s_len >= 6:
            dp  = dist_fit_pts(hand, trump=s_suit)
            tot = h + dp
            if tot >= 15:
                return f'4{s_sym}', f'6+ קלפי {s_sym}, 15+ נקודות. קופץ למשחק'
            if tot >= 11:
                return f'3{s_sym}', f'6+ קלפי {s_sym}, 11-14 נקודות. מזמין'
            return f'2{s_sym}', f'6+ קלפי {s_sym}, 6-10 נקודות. חוזר לסדרה'
        if h >= 13:
            return '3NT', '13+ נקודות. חוזה משחק'
        if h >= 11:
            return '2NT', '11-12 נקודות. מזמין'
        return 'Pass', '6-10 נקודות. מכריזים פס'

    # אחרי 3♣/3♦ (מזמין, 15+). בדוק עוצרים לצורך 3NT
    if n_rebid in ('3♣', '3♦'):
        if h >= 9:
            has_h = has_stopper(hand, 'H')
            has_s = has_stopper(hand, 'S')
            if has_h and has_s:
                return '3NT', '9+ נקודות, עוצרים בכל הצבעים. מכריז משחק'
            if not has_h:
                return '3♥', '9+ נקודות, מחפש עוצר בלב. שאילת עוצרים'
            return '3♠', '9+ נקודות, מחפש עוצר בספייד. שאילת עוצרים'
        return 'Pass', '0-8 נקודות. דוחה הזמנה'

    # אחרי 2NT
    if n_rebid == '2NT':
        # אחרי תגובת מיגור: N הראה 15-17 → קבל עם 9+
        # אחרי תגובת מינור: N הראה 18-19 → קבל עם 7+
        threshold = 9 if s_suit in ('H', 'S') else 7
        if h >= threshold:
            return '3NT', f'{threshold}+ נקודות. מקבל הזמנה'
        return 'Pass', f'0-{threshold-1} נקודות. מכריזים פס'

    # אחרי 1♠ (פותח הראה 4 ספיידים אחרי תגובת מינור)
    if n_rebid == '1♠':
        fit = d.get('S', 0)
        if fit >= 4:
            lp  = fit - 3  # נק' אורך: כל קלף מעל 3 בשליט
            tot = h + lp
            if tot >= 13:
                return '4♠', '4+ קלפי ♠, 13+ נקודות. משחק מלא'
            if tot >= 10:
                return '3♠', '4+ קלפי ♠, 10-12 נקודות. הזמנה'
            return '2♠', '4+ קלפי ♠, 6-9 נקודות. תמיכה'
        if d.get('H', 0) >= 5 and h >= 10:
            return '3♥', '5+ קלפי ♥, 10+ נקודות. יד חזקה עם לב'
        if d.get('H', 0) >= 4 and h >= 13:
            return '3NT', '4+ קלפי ♥, 13+ נקודות. חוזה משחק'
        if d.get('H', 0) >= 4 and h >= 9:
            return '2♥', '4+ קלפי ♥, 9-12 נקודות. מראה סדרה שנייה'
        if h >= 13:
            return '3NT', '13+ נקודות, ללא תמיכה ב-♠. חוזה משחק'
        if h >= 11:
            return '2NT', '11-12 נקודות. מזמין'
        # העדפה לחזור למינור עם 5+ קלפים
        if d.get('C', 0) >= 5 and s_bid and '♣' in s_bid:
            return '2♣', '5+ קלפי ♣. העדפה לחזור לסדרת הפתיחה'
        if d.get('C', 0) >= 5:
            return '2♣', '5+ קלפי ♣. חוזר לסדרת הפתיחה'
        if d.get('D', 0) >= 5:
            return '2♦', '5+ קלפי ♦. חוזר לסדרת הפתיחה'
        return 'Pass', '6-10 נקודות. מינימום'

    # אחרי 1♥ (פותח הראה 4 לבבות אחרי תגובת מינור)
    if n_rebid == '1♥':
        fit = d.get('H', 0)
        if fit >= 4:
            dp  = dist_fit_pts(hand, trump='H')
            tot = h + dp
            if tot >= 13:
                return '4♥', '4+ קלפי ♥, 13+ נקודות. משחק מלא'
            if tot >= 9:
                return '3♥', '4+ קלפי ♥, 9-12 נקודות. הזמנה'
            return '2♥', '4+ קלפי ♥, 6-8 נקודות. תמיכה'
        if d.get('S', 0) >= 4:
            return '1♠', '4+ קלפי ♠. מראה סדרה ברמה 1'
        if h >= 13:
            return '3NT', '13+ נקודות, ללא תמיכה ב-♥. חוזה משחק'
        if h >= 11:
            return '2NT', '11-12 נקודות. מזמין'
        # העדפה לחזור למינור עם 5+ קלפים
        if d.get('C', 0) >= 5:
            return '2♣', '5+ קלפי ♣. חוזר לסדרת הפתיחה'
        if d.get('D', 0) >= 5:
            return '2♦', '5+ קלפי ♦. חוזר לסדרת הפתיחה'
        return 'Pass', '6-10 נקודות. מינימום'

    return 'Pass', 'מכריזים פס'


# ═══════════════════════════════════════════════════════════════════════════
#  מענה ל-2♣ חזקה
# ═══════════════════════════════════════════════════════════════════════════

def respond_2c(hand):
    """
    2♦ = ממתין: 0-6 HCP (כל חלוקה), או 7-10 HCP ללא 5+ קלפי צבע וללא מאוזן
    2♥ = חיובי, 5+ ♥, 7+ HCP
    2♠ = חיובי, 5+ ♠, 7+ HCP
    2NT = חיובי, מאוזן, 8+ HCP (ללא 5+ מיגור)
    3♣ = חיובי, 5+ ♣, 7+ HCP
    3♦ = חיובי, 5+ ♦, 7+ HCP
    """
    h   = hcp(hand)
    d   = distribution(hand)
    bal = is_balanced(hand)

    if h <= 6:
        return '2♦', '0-6 נקודות. תגובת המתנה'

    # 7+ HCP. בדוק אם יש תגובה חיובית ברורה
    if d['H'] >= 5 and d['H'] >= d['S'] and h >= 8:
        return '2♥', f'8+ נקודות, 5 קלפי ♥. תגובה חיובית'
    if d['S'] >= 5 and h >= 8:
        return '2♠', f'8+ נקודות, 5 קלפי ♠. תגובה חיובית'
    if d['H'] >= 5 and h >= 8:
        return '2♥', f'8+ נקודות, 5 קלפי ♥. תגובה חיובית'
    if bal and h >= 8:
        return '2NT', '8+ נקודות, יד מאוזנת. תגובה חיובית'
    if d['C'] >= 5 and d['C'] >= d['D'] and h >= 8:
        return '3♣', f'8+ נקודות, 5 קלפי ♣. תגובה חיובית'
    if d['D'] >= 5 and h >= 8:
        return '3♦', f'8+ נקודות, 5 קלפי ♦. תגובה חיובית'
    if d['C'] >= 5 and h >= 8:
        return '3♣', f'8+ נקודות, 5 קלפי ♣. תגובה חיובית'
    # 7-10 HCP ללא 5 קלפי צבע וללא מאוזן. 2♦ ממתין
    return '2♦', f'{h} נקודות, אין 5 קלפי צבע ולא מאוזן. 2♦ ממתין'


def respond_2c_second(hand, opener_second):
    """
    תגובה שנייה של המשיב אחרי 2♣-2♦-Xxx.
    opener_second: הכרזה שנייה של הפותח (2NT, 2♥, 2♠, 3♣, 3♦, 3NT).
    """
    h   = hcp(hand)
    d   = distribution(hand)
    bal = is_balanced(hand)

    _suit_map = {'2♥': 'H', '2♠': 'S', '3♥': 'H', '3♠': 'S', '3♣': 'C', '3♦': 'D'}
    opener_suit = _suit_map.get(opener_second)

    # ── 2NT (23-24). המקרה היחיד שאפשר לעצור ──────────────────────────────
    if opener_second == '2NT':
        if h <= 3:
            return 'Pass', '0-3 נקודות. מכריזים פס'
        if d['H'] >= 5:
            return '3♦', f'5 קלפי ♥. טרנספר ל-♥'
        if d['S'] >= 5:
            return '3♥', f'5 קלפי ♠. טרנספר ל-♠'
        if d['H'] >= 4 or d['S'] >= 4:
            return '3♣', '4+ קלפי מיגור. סטיימן'
        if h >= 10:
            return '4♣', '10+ נקודות מאוזן. גרבר, שואל אסים'
        if h == 9:
            return '4NT', '9 נקודות מאוזן. כמותי'
        return '3NT', f'{h} נקודות, מאוזן. משחק מלא'

    # ── 3NT (25+ מאוזן). עם 8+ נקודות שואלים אסים ג׳רבר ──────────────────
    if opener_second == '3NT':
        if h >= 8:
            return '4♣', 'שואל אסים. ג׳רבר (23+ ל-N + 8+ ל-S = סיכוי לסלם)'
        return 'Pass', 'חוזה סופי'

    # ── מיגור עיקרי (כפוי למשחק) ─────────────────────────────────────────────
    if opener_suit in ('H', 'S'):
        sym = _S[opener_suit]
        other_suit = 'S' if opener_suit == 'H' else 'H'
        other_sym  = _S[other_suit]
        if d[opener_suit] >= 3:
            if h >= 8:
                return '4NT', f'{h} נקודות, 3+ קלפי {sym}. Blackwood לחקור סלם'
            return f'4{sym}', f'3+ קלפי {sym}. תמיכה, משחק מלא'
        # ללא התאמה. מראים מיגור שני אם יש 5+
        if d[other_suit] >= 5:
            other_len = d[other_suit]
            # הולכים לאט. ברמה הנמוכה ביותר מעל הכרזת הפותח
            _suits_order = ['♣', '♦', '♥', '♠']
            opener_level = int(opener_second[0])
            opener_sym   = opener_second[1]
            # בדוק אם 2+other_sym חוקי (מעל opener_second)
            if opener_level < 2 or (opener_level == 2 and _suits_order.index(other_sym) > _suits_order.index(opener_sym)):
                level = '2'
            else:
                level = '3'
            return f'{level}{other_sym}', f'יש {other_len} קלפי {other_sym}, ללא התאמה ב-{sym}'
        if h >= 8:
            return '4NT', f'{h} נקודות, ללא התאמה. Blackwood לחקור 6NT'
        # 3♦ מלאכותי. כדי שהפותח יגלם 3NT (לא S)
        return '3♣', f'ללא התאמה ב-{sym}.\nשקר! 3♣ לא מראה תלתנים.\nN יכריז 3NT ויגלם'

    # ── מינור (כפוי למשחק). עדיפות: 4M → 8+ נק' שואל אסים → 3NT ─────────
    if opener_suit in ('C', 'D'):
        sym = _S[opener_suit]
        # עדיפות 1: מיגור עיקרי
        if d['S'] >= 5 and d['S'] >= d['H']:
            return '3♠', '5+ קלפי ♠. מראה מיגור'
        if d['H'] >= 5:
            return '3♥', '5+ קלפי ♥. מראה מיגור'
        if d['S'] >= 5:
            return '3♠', '5+ קלפי ♠. מראה מיגור'
        # עדיפות 2: 8+ נקודות. Blackwood לחקור סלם
        if h >= 8:
            return '4NT', f'{h} נקודות, ללא מיגור עיקרי. Blackwood לחקור 6NT'
        # עדיפות 3: 3NT. הפותח החזק מכסה את העוצרים
        return '3NT', 'ללא 5 קלפי מיגור. 3NT (עדיף על 5 במינור)'

    return '3NT', 'ממשיך למשחק'


def respond_2c_third(hand, s_second, n_third):
    """
    תגובה שלישית של המשיב אחרי 2♣-2♦-2NT-Sxx-Nxx.
    s_second: הכרזה שנייה של המשיב (3♣/3♦/3♥).
    n_third:  הכרזה שלישית של הפותח (תגובה לסטיימן/טרנספר).
    """
    d = distribution(hand)

    if s_second == '3♣':  # סטיימן. פותח ענה
        if n_third == '3♥':
            if d['H'] >= 4:
                return '4♥', 'התאמה ב-♥. משחק מלא'
            return '3NT', 'ללא התאמה ב-♥'
        if n_third == '3♠':
            if d['S'] >= 4:
                return '4♠', 'התאמה ב-♠. משחק מלא'
            return '3NT', 'ללא התאמה ב-♠'
        if n_third == '3♦':  # ללא מיגור (סטיימן)
            h = hcp(hand)
            if h >= 8:
                return '4♣', 'ללא התאמה. גרבר לחקור 6NT'
            return '3NT', 'ללא התאמה במיגור'
        if n_third == '3NT':  # 3♣ שקר. N מגלם 3NT
            h = hcp(hand)
            if h >= 8:
                return '4♣', '8+ נקודות. שואל אסים גרבר'
            return 'Pass', 'חוזה סופי 3NT'

    if s_second == '3♦':  # טרנספר ל-♥, פותח ענה 3♥
        if d['H'] >= 6:
            return '4♥', 'יש 6 קלפי ♥. משחק מלא ישיר'
        return '3NT', 'יש 5 קלפי ♥. מזמין, הפותח יבחר'

    if s_second == '3♥':  # טרנספר ל-♠, פותח ענה 3♠
        if d['S'] >= 6:
            return '4♠', 'יש 6 קלפי ♠. משחק מלא ישיר'
        return '3NT', 'יש 5 קלפי ♠. מזמין, הפותח יבחר'

    # S הראה מיגור שני (3♥/3♠) אחרי N מראה מיגור, N ענה 3NT
    if s_second in ('3♥', '3♠') and n_third == '3NT':
        sym = s_second[1]
        return f'4{sym}', f'יש 6 קלפי {sym}. משחק מלא'

    return 'Pass', 'חוזה סופי'


def _best_new_suit(d, exclude, min_len=4):
    """מוצא את הצבע הטוב ביותר (ארוך ביותר) מלבד הצבע שמוחרג."""
    candidates = [(suit, d[suit]) for suit in ['S', 'H', 'D', 'C']
                  if suit != exclude and d[suit] >= min_len]
    if not candidates:
        return None
    return max(candidates, key=lambda x: x[1])[0]
