"""
Rebid של הפותח. הכרזה שנייה לאחר מענה השותף.
מחזיר (bid, explanation).
"""

from engine.scoring import hcp, is_balanced, distribution, dist_fit_pts, has_stopper
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


def opener_rebid(hand, opening, partner_response):
    """
    הפותח מכריז שוב לאחר מענה השותף.
    opening: '1♥','1♠','1♣','1♦','1NT','2♣' וכד'.
    partner_response: '1NT','2♥','2NT','3NT','2♣' וכד'.
    """
    h   = hcp(hand)
    d   = distribution(hand)
    bal = is_balanced(hand)

    # ── לאחר 1NT (15-17) ────────────────────────────────────────────────────
    if opening == '1NT':
        return _rebid_after_1nt(h, partner_response, hand)

    # ── לאחר 2♣ חזקה ────────────────────────────────────────────────────────
    if opening == '2♣':
        return _rebid_after_2c(hand, h, d, bal, partner_response)

    # ── לאחר פתיחה בצבע ─────────────────────────────────────────────────────
    open_suit = _bid_to_suit(opening)
    return _rebid_after_suit(hand, h, d, bal, open_suit, partner_response)


# ───────────────────────────────────────────────────────────────────────────

def _has_good_5card_suit(hand):
    """האם ביד יש סדרה של 5+ קלפים עם לפחות 2 מתוך A/K/Q."""
    from engine.cards import card_suit, card_rank
    honors = {'A', 'K', 'Q'}
    suits = {}
    for card in hand:
        s = card_suit(card)
        r = card_rank(card)
        suits.setdefault(s, []).append(r)
    for s, ranks in suits.items():
        if len(ranks) >= 5 and sum(1 for r in ranks if r in honors) >= 2:
            return True
    return False


def _rebid_after_1nt(h, response, hand=None):
    if response == '2NT':
        if h <= 15:
            return 'Pass', '15 נקודות. מינימום 1NT, מכריזים פס'
        if h == 16:
            if hand and _has_good_5card_suit(hand):
                return '3NT', '16 נקודות עם סדרה טובה. מכריזים משחק'
            return 'Pass', '16 נקודות ללא סדרה טובה. נשארים ב-2NT'
        return '3NT', '17 נקודות. מקסימום 1NT, מכריזים משחק'
    if response == '5NT':  # כמותי — הזמנה לסלם גדול
        if h <= 15:
            return '6NT', '15 נקודות. מינימום 1NT, נשארים בסלם קטן'
        if h == 16:
            if hand and _has_good_5card_suit(hand):
                return '7NT', '16 נקודות עם סדרה טובה. מקבלים הזמנה לסלם גדול'
            return '6NT', '16 נקודות ללא סדרה טובה. נשארים בסלם קטן'
        return '7NT', '17 נקודות. מקסימום 1NT, סלם גדול'
    if response in ('3♥', '3♠'):  # הזמנה בשליט מוסכם (אחרי סטיימן)
        suit = response[1:]
        if h <= 15:
            return 'Pass', f'{h} נקודות. מינימום, נשארים ב-{response}'
        if h == 16:
            if hand and _has_good_5card_suit(hand):
                return f'4{suit}', f'16 נקודות עם סדרה טובה. מקבלים הזמנה'
            return 'Pass', f'16 נקודות ללא סדרה טובה. נשארים ב-{response}'
        return f'4{suit}', f'{h} נקודות. מקסימום, מקבלים הזמנה'
    if response == 'Pass':
        return 'Pass', 'השותף פסם'
    if response == '3NT':
        return 'Pass', 'חוזה סופי'
    return 'Pass', 'פס'


def _rebid_after_2c(hand, h, d, bal, response):
    """פותח 2♣. הכרזה שנייה לאחר תגובת השותף."""
    if response == '2♦':  # המתנה. פותח מתאר ידו
        # מיגור 5 קלפי תמיד קודם לידה מאוזנת (גם 5-3-3-2)
        for suit in ['S', 'H']:
            if d[suit] >= 5:
                return f'2{_S[suit]}', f'5+ קלפי {_S[suit]}. מראה סדרה חזקה'
        if bal:
            if h <= 24:
                return '2NT', '23-24 נקודות מאוזן'
            return '3NT', '25+ נקודות מאוזן. משחק מלא'
        # יד עם עוצרים בכל הסדרות → 2NT, היד החזקה משחקת
        if all(has_stopper(hand, suit) for suit in ['S', 'H', 'D', 'C']):
            return '2NT', 'עוצרים בכל הסדרות. 2NT, היד החזקה משחקת'
        for suit in ['D', 'C']:
            if d[suit] >= 5:
                return f'3{_S[suit]}', f'5+ קלפי {_S[suit]}. מראה סדרה חזקה'
        return '2NT', 'יד חזקה ללא סדרה ארוכה'

    # תגובה חיובית. פותח ממשיך לפי ההתאמה
    _pos_map = {'2♥': 'H', '2♠': 'S', '3♣': 'C', '3♦': 'D'}
    resp_suit = _pos_map.get(response)

    if response == '2NT':  # מאוזן חיובי. מראים 5+ מיגור לפני 3NT
        if d['S'] >= 5:
            return '3♠', 'יש 5 קלפי ♠. מחפשים התאמה'
        if d['H'] >= 5:
            return '3♥', 'יש 5 קלפי ♥. מחפשים התאמה'
        return '3NT', 'שני הידיים מאוזנות. משחק 3NT'

    if resp_suit in ('H', 'S'):
        sym = _S[resp_suit]
        if d[resp_suit] >= 3:
            return f'3{sym}', f'התאמה ב-{sym}. תמיכה'
        return '3NT', f'ללא התאמה ב-{sym}. 3NT'

    if resp_suit in ('C', 'D'):
        sym = _S[resp_suit]
        if d[resp_suit] >= 4:
            return f'5{sym}', f'התאמה ב-{sym}. משחק מלא'
        return '3NT', f'ללא התאמה ב-{sym}. 3NT'

    return '3NT', 'מכוונים למשחק מלא'


def opener_bid_2c_round3(hand, n_second, s_second):
    """
    הכרזה שלישית של הפותח אחרי 2♣-2♦-2NT-Sxx.
    n_second: הכרזה שנייה של הפותח (2NT).
    s_second: הכרזה שנייה של המשיב (3♣/3♦/3♥).
    """
    d = distribution(hand)

    if n_second == '2NT':
        if s_second == '3♣':  # סטיימן
            if d['H'] >= 4 and d['H'] >= d['S']:
                return '3♥', '4 קלפי ♥. מגיב לסטיימן'
            if d['S'] >= 4:
                return '3♠', '4 קלפי ♠. מגיב לסטיימן'
            return '3♦', 'ללא 4 קלפי מיגור. מגיב לסטיימן'
        if s_second == '3♦':  # טרנספר ל-♥
            return '3♥', 'מקבל טרנספר. היד החזקה משחקת ♥'
        if s_second == '3♥':  # טרנספר ל-♠
            return '3♠', 'מקבל טרנספר. היד החזקה משחקת ♠'

    # אחרי 2♣-2♦-3♣/3♦. S הראה מיגור ב-3♥/3♠
    if n_second in ('3♣', '3♦') and s_second in ('3♥', '3♠'):
        s_sym  = s_second[1]
        s_suit = {'♥': 'H', '♠': 'S'}[s_sym]
        if d.get(s_suit, 0) >= 3:
            return f'4{s_sym}', f'תמיכה ב-{s_sym}. משחק מלא'
        return '3NT', 'ללא תמיכה. 3NT'

    # אחרי 2♣-2♦-2♥/2♠. S הראה מיגור שני
    if n_second in ('2♥', '2♠'):
        n_suit = {'♥': 'H', '♠': 'S'}[n_second[1]]
        n_sym  = n_second[1]
        s_suit = {'♥': 'H', '♠': 'S', '♣': 'C', '♦': 'D'}.get(s_second[1] if len(s_second)==2 else '')
        # 3♣ אחרי מיגור = שקר (ללא התאמה). לא תומכים — N מגלם 3NT
        if s_suit and s_suit != n_suit and s_second != '3♣' and d.get(s_suit, 0) >= 3:
            return f'4{_S[s_suit]}', f'תמיכה ב-{_S[s_suit]}. משחק מלא'
        n_sym = n_second[1]
        if s_second in ('2NT', '3♦', '3♣'):
            return '3NT', f'ללא התאמה ב-{n_sym}. N מגלם 3NT'
        s_sym = s_second[1] if len(s_second) == 2 else '?'
        return '3NT', 'אין התאמה. 3NT'

    return 'Pass', 'חוזה סופי'


def _rebid_after_suit(hand, h, d, bal, open_suit, response):
    sym = _S[open_suit] if open_suit else '?'
    resp_suit = _bid_to_suit(response)
    is_minor = open_suit in ('C', 'D')

    # שותף פסם. המכרז נגמר
    if response == 'Pass':
        return 'Pass', 'השותף פסם'

    # שותף הרים מיד למשחק מלא
    if response in ('3NT', f'4{_S.get(open_suit, "")}', '4♥', '4♠'):
        return 'Pass', 'חוזה סופי'

    # לאחר 1NT מהשותף (ללא תמיכה)
    if response == '1NT':
        if is_minor:
            if h >= 18:
                return '3NT', 'יד חזקה. קופץ ל-3NT'
            if h >= 15:
                return '2NT', 'יד בינונית. מזמין לחוזה 3NT'
            return 'Pass', 'יד מינימום. מכריזים פס'
        if h >= 18:
            return '3NT', 'יד חזקה. קופץ ל-3NT'
        if h >= 15:
            return '2NT', 'יד בינונית. מזמין לחוזה 3NT'
        return 'Pass', 'יד מינימום. מכריזים פס'

    # לאחר 2NT מהשותף
    if response == '2NT':
        if is_minor:
            if h >= 13:
                return '3NT', 'מקבל הזמנה. קופץ למשחק'
            return 'Pass', 'יד מינימום. דוחה הזמנה'
        if h >= 14:
            return '3NT', 'מקבל הזמנה. קופץ למשחק'
        return 'Pass', 'יד מינימום. דוחה הזמנה'

    # לאחר לימיט ריס (3M / 3m). חייב לבוא לפני תמיכה פשוטה
    if response.startswith('3') and resp_suit == open_suit:
        if is_minor:
            if h >= 14:
                return '3NT', 'מקבל הזמנה. קופץ למשחק'
            return 'Pass', 'יד מינימום. דוחה הזמנה'
        if h >= 15:
            return f'4{sym}', 'מקבל הזמנה. קופץ למשחק'
        return 'Pass', 'יד מינימום. דוחה הזמנה'

    # לאחר תמיכה פשוטה (2M / 2m)
    if resp_suit == open_suit:
        if is_minor:
            if h >= 18:
                return '3NT', 'יד חזקה. קופץ ל-3NT'
            if h >= 15:
                return f'3{sym}', 'יד בינונית. מזמין למשחק'
            return 'Pass', 'יד מינימום. מכריזים פס'
        dp = dist_fit_pts(hand, trump=open_suit, opener=True)
        tot = h + dp
        dp_str = f'\nיש {dp} נקודות חוסר\nסה״כ {tot}' if dp > 0 else ''
        if tot >= 18:
            return f'4{sym}', f'יש {h} נקודות גבוהות{dp_str}. קופצים למשחק מלא'
        if tot >= 15:
            return f'3{sym}', f'יש {h} נקודות גבוהות{dp_str}. מזמינים למשחק'
        return 'Pass', f'יש {h} נקודות גבוהות{dp_str}. מינימום, פס'

    # תמיכה במיגור השותף
    if resp_suit in ('H', 'S'):
        resp_sym = _S[resp_suit]
        fit = d.get(resp_suit, 0)
        if fit >= 4:
            if h >= 18:
                return f'4{resp_sym}', f'תמיכה חזקה ב-{resp_sym}. קופץ למשחק'
            if h >= 15:
                return f'3{resp_sym}', f'תמיכה בינונית ב-{resp_sym}. מזמין למשחק'
            return f'2{resp_sym}', f'תמיכה חלשה ב-{resp_sym}. מוצא התאמה'
        # ללא התאמה (פחות מ-4). הכרזה הכי נמוכה
        # אחרי 1♥. אפשר להראות 4♠ ברמה 1
        if resp_suit == 'H' and d.get('S', 0) >= 4:
            return '1♠', 'מראה 4 קלפי ♠. up-the-line'
        # 5+ קלפי מינור. חוזרים לסדרה ברמה 2
        if is_minor and d.get(open_suit, 0) >= 5:
            return f'2{sym}', f'5+ קלפי {sym}. חוזר לסדרת הפתיחה'
        # אחרת. 1NT (הכי נמוך)
        return '1NT', f'ללא התאמה ב-{resp_sym}. 1NT'

    # אחרי 1♣ → 1♦. up-the-line: 1♥ / 1♠ / 2♣ / 1NT
    resp_level = int(response[0]) if response and response[0].isdigit() else 1
    if open_suit == 'C' and resp_suit == 'D':
        if d.get('H', 0) >= 4:
            return '1♥', 'מראה 4+ קלפי ♥. up-the-line'
        if d.get('S', 0) >= 4:
            return '1♠', 'מראה 4+ קלפי ♠. up-the-line'
        if d.get('D', 0) >= 4:
            return '2♦', 'תמיכה ב-4+ קלפי ♦'
        if d.get('C', 0) >= 5:
            return '2♣', '5+ קלפי ♣. חוזר לסדרת הפתיחה'
        if h >= 18:
            return '2NT', '18-19 נקודות מאוזן. מזמין ל-3NT'
        return '1NT', 'מאוזן. 1NT'

    # אחרי תגובת מינור ברמה 1. הראה מיגור (up-the-line)
    if resp_level == 1 and resp_suit in ('D', 'C'):
        if d.get('H', 0) >= 4:
            return '1♥', 'מראה 4+ קלפי ♥. up-the-line'
        if d.get('S', 0) >= 4:
            return '1♠', 'מראה 4+ קלפי ♠. up-the-line'

    # לאחר צבע חדש ברמה 2
    if resp_level >= 2 and is_minor and d.get(open_suit, 0) >= 4:
        return f'2{sym}', f'4+ קלפי {sym}. חוזר לסדרת הפתיחה'
    # צבע מינור חדש ברמה 2 = כפוי (11+). פותח ללא תמיכה מראה NT לפי עוצמה
    if resp_level >= 2 and resp_suit in ('C', 'D'):
        if h >= 19:
            return '3NT', 'יד חזקה. קופץ ל-3NT'
        return '2NT', 'ללא תמיכה בסדרת השותף. 2NT'
    if d.get(open_suit, 0) >= 5:
        return f'2{sym}', f'5+ קלפי {sym}. חוזר לסדרת הפתיחה'
    return '1NT', 'ללא התאמה. 1NT'


# ───────────────────────────────────────────────────────────────────────────

def opener_later_bid(hand, s_last, agreed_minor=None, s_showed_6h=False):
    """
    N's bid in round 3+ after: 1m - s1 - n1 - s2 - ???
    s_last: S's most recent bid.
    agreed_minor: 'C' or 'D' if a minor suit was agreed, enables stopper ask detection.
    """
    h = hcp(hand)
    d = distribution(hand)

    if s_last == 'Pass':
        return 'Pass', 'השותף פסם'

    _final = {'3NT', '4♥', '4♠', '5♣', '5♦'}
    if s_last in _final:
        return 'Pass', 'חוזה סופי'

    # S הזמין ב-2NT → קבל/דחה
    if s_last == '2NT':
        if h >= 14:
            return '3NT', '14+ נקודות. מקבל הזמנה'
        return 'Pass', 'מינימום (12-13 נקודות). דוחה הזמנה'

    resp_suit = _bid_to_suit(s_last)

    # S הראה 4 ספיידים ברמה 1 (אחרי 1♥ של N). up-the-line
    if s_last == '1♠':
        fit = d.get('S', 0)
        if fit >= 3:
            if h >= 15:
                return '4♠', '3+ קלפי ♠, 15+ נקודות. משחק מלא'
            return '3♠', '3+ קלפי ♠, 12-14 נקודות. מזמין'
        if h >= 15:
            return '3NT', '15+ נקודות, ללא תמיכה ב-♠. 3NT'
        return 'Pass', 'מינימום (12-14 נקודות)'

    # S הכריז מיגור ברמה 2. תמיכה או סדרה חדשה (9-12 נקודות)
    if s_last.startswith('2') and resp_suit in ('H', 'S'):
        fit = d.get(resp_suit, 0)
        resp_sym = _S[resp_suit]
        if fit >= 3:
            if h >= 14:
                return f'4{resp_sym}', f'3+ קלפי {resp_sym}, 14+ נקודות. משחק מלא'
            return f'3{resp_sym}', f'3+ קלפי {resp_sym}, 12-13 נקודות. מזמין'
        if h >= 14:
            return '3NT', f'14+ נקודות, ללא תמיכה ב-{resp_sym}. 3NT'
        return 'Pass', 'מינימום (12-13 נקודות)'

    # Stopper ask. 3♥/3♠ אחרי הסכמת מינור מפורשת
    if agreed_minor and s_last.startswith('3') and resp_suit in ('H', 'S'):
        asked_sym = _S[resp_suit]
        minor_sym = _S[agreed_minor]
        if has_stopper(hand, resp_suit):
            return '3NT', f'יש עוצר ב-{asked_sym}. מכריזים 3NT'
        return f'5{minor_sym}', f'אין עוצר ב-{asked_sym}. ממשיכים ב-{minor_sym}'

    # 3♥ טבעי. S הראה 6 קלפי ♥ (1♥→3♥) או 5♠+4♥ כפוי למשחק
    if not agreed_minor and s_last == '3♥' and resp_suit == 'H':
        fit_h = d.get('H', 0)
        if s_showed_6h:
            # S הראה 6 לבבות. 6+2=8, מספיק למשחק מלא
            if fit_h >= 2:
                return '4♥', 'דרום הראה 6+ קלפי ♥. התאמה, משחק מלא'
            return '3NT', 'ללא תמיכה בלב. מכריזים 3NT'
        # S הראה 4 לבבות (5♠+4♥)
        if fit_h >= 4:
            return '4♥', '4+ קלפי ♥. התאמה, משחק מלא'
        if fit_h >= 3:
            return '3NT', '3 קלפי ♥ בלבד. ללא התאמה מלאה, מכריזים 3NT'
        # ללא התאמה בלב. בדוק תמיכה ב-♠
        fit_s = d.get('S', 0)
        if fit_s >= 3:
            if h >= 15:
                return '4♠', '3+ קלפי ♠, 15+ נקודות. תמיכה ב-♠ למשחק מלא'
            return '3♠', '3+ קלפי ♠. תמיכה ב-♠, מזמין'
        return '3NT', 'ללא התאמה בלב או ספייד. מכריזים 3NT'

    # S הכריז 3M ללא הסכמת מינור (הזמנה למיגור)
    if s_last.startswith('3') and resp_suit in ('H', 'S'):
        fit = d.get(resp_suit, 0)
        if h >= 14 or (h >= 13 and fit >= 4):
            sym = _S[resp_suit]
            return f'4{sym}', '14+ נקודות. מקבל הזמנה'
        return 'Pass', 'מינימום (12-13 נקודות). דוחה הזמנה'

    # S הכריז 3m (הזמנה למינור)
    if s_last.startswith('3') and resp_suit in ('C', 'D'):
        if h >= 15:
            return '3NT', '15+ נקודות. מקבל הזמנה'
        return 'Pass', 'מינימום (12-14 נקודות). דוחה הזמנה'

    return 'Pass', 'מכריזים פס'


# ───────────────────────────────────────────────────────────────────────────
# עזרים

def _bid_to_suit(bid):
    """מחלץ צבע מהכרזה כגון '1♠' → 'S'"""
    _map = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
    for ch, suit in _map.items():
        if ch in bid:
            return suit
    return None
