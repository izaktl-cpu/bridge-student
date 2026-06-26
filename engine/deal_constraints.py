"""
חלוקת ידיים מבוקרת לפי שיעור — כל שיעור מגדיר אילוצים מדויקים.
עיקרון: הסרת מורכבות לפי רמה כדי שהתלמיד יתמקד רק בחומר הנלמד.
"""

import random
from engine.cards import make_deck, SUITS, SUIT_SYMBOLS, card_rank, card_suit
from engine.scoring import hcp, is_balanced, distribution, suit_len, sure_tricks, key_cards, has_stopper
from engine.opening import opening_bid as _opening_bid

_MAX_TRIES = 80_000


def _deal_random():
    deck = make_deck()
    random.shuffle(deck)
    return {'N': deck[:13], 'E': deck[13:26], 'S': deck[26:39], 'W': deck[39:]}


def _quiet_opponent(hand):
    """ליריב: פחות מ-12 HCP + אין סדרה של 6+ קלפים."""
    if hcp(hand) >= 12:
        return False
    d = distribution(hand)
    return max(d.values()) <= 5


def _try(condition, tries=_MAX_TRIES):
    for _ in range(tries):
        hands = _deal_random()
        if condition(hands):
            return hands
    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו')


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 1 — תלמיד (S) פותח 1NT, שותף עונה
#  אילוץ: S=15-17 HCP מאוזן, N=0-15 HCP, ללא רביעיות במיגור (רמה בסיסית)
# ═══════════════════════════════════════════════════════════════════════════

def deal_student_opens_1nt(advanced=False):
    """
    S = 15-17 HCP מאוזן.
    N = 0-15 HCP.
    advanced=False → לN אין 4+ קלפי מיגור עיקרי (ללא Stayman/Transfer).
    """
    def ok(hands):
        s = hands['S']
        n = hands['N']
        if not (15 <= hcp(s) <= 17 and is_balanced(s)):
            return False
        hn = hcp(n)
        if not (0 <= hn <= 15):
            return False
        if not advanced:
            d = distribution(n)
            if d['S'] >= 4 or d['H'] >= 4:
                return False
        return True
    return _try(ok)


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 2 — תלמיד (S) פותח במיגור, שותף (N) יש לו תמיכה
#  אילוץ: S=12-19 HCP עם 5+ קלפי מיגור, N=6-12 עם 3+ תמיכה
# ═══════════════════════════════════════════════════════════════════════════

def deal_student_opens_major(major='H', advanced=False):
    """
    S = 12-19 HCP, 5+ קלפי major, והפתיחה הנכונה היא 1M.
    N = 6-12 HCP, 3+ תמיכה ב-major.
    סה״כ S+N <= 29 (ללא סלם).
    """
    from engine.cards import SUIT_SYMBOLS
    sym = SUIT_SYMBOLS[major]
    def ok(hands):
        s = hands['S']
        n = hands['N']
        hs = hcp(s)
        hn = hcp(n)
        if not (12 <= hs <= 19):
            return False
        if suit_len(s, major) < 5:
            return False
        if _opening_bid(s)[0] != f'1{sym}':
            return False
        if not (6 <= hn <= 12):
            return False
        if suit_len(n, major) < 3:
            return False
        if hs + hn > 29:
            return False
        return True
    return _try(ok)


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 3 — מחשב (N) פותח 1NT, תלמיד (S) עונה
#  אילוץ: N=15-17 מאוזן, S=0-15 HCP, (ללא רביעיות מיגור ברמה בסיסית)
# ═══════════════════════════════════════════════════════════════════════════

def deal_robot_opens_1nt(advanced=False):
    """
    N = 15-17 HCP מאוזן.
    S = 0-15 HCP.
    advanced=False → ל-S אין 4+ מיגור עיקרי.
    """
    def ok(hands):
        n = hands['N']
        s = hands['S']
        if not (15 <= hcp(n) <= 17 and is_balanced(n)):
            return False
        hs = hcp(s)
        if not (0 <= hs <= 15):
            return False
        if not advanced:
            if not is_balanced(s):
                return False
            d = distribution(s)
            if d['S'] >= 4 or d['H'] >= 4:
                return False
        return True
    return _try(ok)


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 4 — מחשב (N) פותח במיגור, תלמיד (S) עונה
# ═══════════════════════════════════════════════════════════════════════════

def deal_robot_opens_major(major='H', support_scenario=True):
    """
    N = 12-19 HCP, 5+ קלפי major, והפתיחה הנכונה היא 1M.
    support_scenario=True → S יש 3+ תמיכה (שיעור תמיכה).
    support_scenario=False → S אין תמיכה (שיעור תגובה ללא תמיכה).
    סה״כ N+S <= 29 (ללא סלם).
    """
    from engine.cards import SUIT_SYMBOLS
    sym = SUIT_SYMBOLS[major]
    def ok(hands):
        n = hands['N']
        s = hands['S']
        hn = hcp(n)
        hs = hcp(s)
        if not (12 <= hn <= 19):
            return False
        if suit_len(n, major) < 5:
            return False
        if _opening_bid(n)[0] != f'1{sym}':
            return False
        if support_scenario:
            if suit_len(s, major) < 3:
                return False
        else:
            if suit_len(s, major) >= 3:
                return False
        if hn + hs > 29:
            return False
        return True
    return _try(ok)


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 5 — אוברקול: N פותח, E עושה אוברקול, תלמיד (S) מגיב
# ═══════════════════════════════════════════════════════════════════════════

def deal_with_overcall(north_opening='1♥'):
    """
    N = יד המתאימה לפתיחה שנדרשת.
    E = יד עם אוברקול ריאלי (8-16 HCP, 5+ צבע).
    S = 6-14 HCP.
    """
    _suit_map = {'1♥': 'H', '1♠': 'S', '1♦': 'D', '1♣': 'C', '1NT': None}
    open_suit = _suit_map.get(north_opening)

    def ok(hands):
        n = hands['N']
        e = hands['E']
        s = hands['S']
        # N מתאים לפתיחה
        hn = hcp(n)
        if north_opening == '1NT':
            if not (15 <= hn <= 17 and is_balanced(n)):
                return False
        else:
            if not (12 <= hn <= 19):
                return False
            if open_suit and suit_len(n, open_suit) < 4:
                return False
        # E יכול לעשות אוברקול
        he = hcp(e)
        if not (8 <= he <= 16):
            return False
        has_5card = any(suit_len(e, s) >= 5
                        for s in ['S', 'H', 'D', 'C']
                        if s != open_suit)
        if not has_5card:
            return False
        # S בעל יד סבירה
        if not (6 <= hcp(s) <= 14):
            return False
        return True
    return _try(ok)


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור סטיימן — N פותח 1NT, ל-S יש 4 קלפי מיגור עיקרי בדיוק (ללא 5+)
# ═══════════════════════════════════════════════════════════════════════════

def deal_robot_opens_1nt_stayman():
    """
    N = 15-17 HCP מאוזן.
    S = 8-14 HCP, 2+ רביעיות, אחת לפחות במיגור עיקרי (בדיוק 4, לא 5+).
    """
    def ok(hands):
        n = hands['N']
        s = hands['S']
        if not (15 <= hcp(n) <= 17 and is_balanced(n)):
            return False
        hs = hcp(s)
        if not (8 <= hs <= 14):
            return False
        d = distribution(s)
        if d['H'] >= 5 or d['S'] >= 5:
            return False
        has_major_4 = d['H'] == 4 or d['S'] == 4
        if not has_major_4:
            return False
        four_count = sum([d['S'] == 4, d['H'] == 4, d['D'] >= 4, d['C'] >= 4])
        return four_count >= 2
    return _try(ok)


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור טרנספר — N פותח 1NT, ל-S יש 5+ קלפי מיגור עיקרי
# ═══════════════════════════════════════════════════════════════════════════

_HONORS = frozenset('AKQJ')

def deal_robot_opens_1nt_transfer():
    """
    N = 15-17 HCP מאוזן, לפחות J אחד בכל סדרה (אין סדרה עירומה).
    S = 0-14 HCP, בעל 5+ קלפי מיגור עיקרי (H או S).
    """
    def ok(hands):
        n = hands['N']
        s = hands['S']
        if not (15 <= hcp(n) <= 17 and is_balanced(n)):
            return False
        # אין סדרה עירומה ל-N — לפחות J בכל סדרה
        for suit in SUITS:
            ranks = [card_rank(c) for c in n if card_suit(c) == suit]
            if ranks and not any(r in _HONORS for r in ranks):
                return False
        hs = hcp(s)
        if not (0 <= hs <= 14):
            return False
        d = distribution(s)
        return d['H'] >= 5 or d['S'] >= 5
    return _try(ok)


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור מינורים — תלמיד (S) פותח 1♣/1♦
#  אילוץ: S=12-19 HCP, 4+ קלפי minor; N=6-12 HCP; basic: N ללא 4+ מיגור
# ═══════════════════════════════════════════════════════════════════════════

def _no_long_suits(hands, max_len=6):
    """אין סדרה ארוכה מ-max_len קלפים לאף שחקן."""
    for hand in hands.values():
        d = distribution(hand)
        if any(v > max_len for v in d.values()):
            return False
    return True


def deal_student_opens_minor(minor='C', advanced=False, scenario='free'):
    """
    S = 12-19 HCP, 3-6 קלפי minor, והפתיחה הנכונה היא 1m.
    N = 6-12 HCP.
    scenario='minor_partial' → N+S ≤ 24, N עם 4+ מינור, ללא 4+ מיגור.
    """
    from engine.cards import SUIT_SYMBOLS
    sym = SUIT_SYMBOLS[minor]
    def ok(hands):
        if not _no_long_suits(hands):
            return False
        s = hands['S']
        n = hands['N']
        hs = hcp(s)
        if not (12 <= hs <= 19):
            return False
        sm = suit_len(s, minor)
        if sm < 3 or sm > 6:
            return False
        if _opening_bid(s)[0] != f'1{sym}':
            return False
        hn = hcp(n)
        if not (6 <= hn <= 12):
            return False
        dn = distribution(n)
        if scenario == 'minor_partial':
            if hs + hn > 24:
                return False
            if dn['H'] >= 4 or dn['S'] >= 4:
                return False
            if suit_len(n, minor) < 5:
                return False
        else:
            # הימנעות ממצבי צבע רביעי: N עם מיגור ברור OR מאוזן
            has_major = dn['H'] >= 4 or dn['S'] >= 4
            if not (has_major or is_balanced(n)):
                return False
        return True
    return _try(ok)


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור מינורים — מחשב (N) פותח 1♣/1♦, תלמיד (S) עונה
#  אילוץ: N=12-19 HCP, 4+ קלפי minor; S=6-13 HCP; basic: S ללא 4+ מיגור
# ═══════════════════════════════════════════════════════════════════════════

def deal_robot_opens_minor(minor='C', advanced=False, scenario='free'):
    """
    N = 12-19 HCP, 3-6 קלפי minor, והפתיחה הנכונה היא 1m.
    S = 6-15 HCP — סה״כ N+S >= 22.
    מאפשר פתיחה עם 3 קלפים (מינור מאולץ).
    scenario='major_fit' → N וS חולקים 4+ באותו מיגור.
    scenario='nt'        → S מאוזן, ללא 4+ מיגורים.
    scenario='free'      → S עם מיגור OR מאוזן (ללא צבע רביעי).
    """
    from engine.cards import SUIT_SYMBOLS
    sym = SUIT_SYMBOLS[minor]

    def ok(hands):
        if not _no_long_suits(hands):
            return False
        n = hands['N']
        s = hands['S']
        hn = hcp(n)
        if not (12 <= hn <= 19):
            return False
        nm = suit_len(n, minor)
        if nm < 3 or nm > 6:
            return False
        if _opening_bid(n)[0] != f'1{sym}':
            return False
        hs = hcp(s)
        if not (6 <= hs <= 15):
            return False
        if hn + hs < 22:
            return False
        ds = distribution(s)
        dn = distribution(n)
        if scenario == 'major_fit':
            if not ((dn['H'] >= 4 and ds['H'] >= 4) or
                    (dn['S'] >= 4 and ds['S'] >= 4)):
                return False
        elif scenario == 'nt':
            if not is_balanced(s) or ds['H'] >= 4 or ds['S'] >= 4:
                return False
        elif scenario == 'minor_partial':
            # 20-24 נקודות משותפות, S עם 5+ מינור, ללא 4+ מיגור
            if hn + hs > 24:
                return False
            if ds['H'] >= 4 or ds['S'] >= 4:
                return False
            if suit_len(s, minor) < 5:
                return False
        else:  # free — הימנעות ממצבי צבע רביעי
            has_major = ds['H'] >= 4 or ds['S'] >= 4
            if not (has_major or is_balanced(s)):
                return False
        return True
    return _try(ok)


def deal_respond_nt_major(major='H'):
    """
    N = 12-19 HCP, 5+ קלפי major, פותח 1M.
    S = 6-14 HCP, התגובה הנכונה היא NT בלבד (ללא תמיכה, ללא מייג'ור שני, ללא 5+ מינור).
    """
    from engine.response import respond_major as _resp
    sym   = SUIT_SYMBOLS[major]
    other = 'S' if major == 'H' else 'H'

    def ok(hands):
        n, s = hands['N'], hands['S']
        hn = hcp(n)
        if not (12 <= hn <= 19):
            return False
        if suit_len(n, major) < 5:
            return False
        if _opening_bid(n)[0] != f'1{sym}':
            return False
        hs = hcp(s)
        if not (6 <= hs <= 14):
            return False
        if hn + hs > 29:
            return False
        bid, _ = _resp(s, major)
        return 'NT' in bid or bid == 'Pass'
    return _try(ok)


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 2NT — מחשב (N) פותח 2NT, תלמיד (S) עונה
#  2NT = 20-22 HCP מאוזן
# ═══════════════════════════════════════════════════════════════════════════

def deal_robot_opens_2nt_stayman():
    """
    N = 20-22 HCP מאוזן, חייב 4+ קלפי מיגור.
    S = 5-12 HCP, 2 רביעיות לפחות — אחת מהן מיגור (בדיוק 4, לא 5+).
    """
    def ok(hands):
        n = hands['N']
        s = hands['S']
        if not (20 <= hcp(n) <= 22 and is_balanced(n)):
            return False
        hs = hcp(s)
        if not (5 <= hs <= 12):
            return False
        ds = distribution(s)
        dn = distribution(n)
        if ds['H'] >= 5 or ds['S'] >= 5:
            return False
        has_major4 = ds['H'] == 4 or ds['S'] == 4
        has_second4 = sum(1 for v in ds.values() if v >= 4) >= 2
        if not (has_major4 and has_second4):
            return False
        return dn['H'] >= 4 or dn['S'] >= 4
    return _try(ok)


def deal_robot_opens_2nt_transfer():
    """
    N = 20-22 HCP מאוזן.
    S = 0-9 HCP, בעל 5+ קלפי מיגור עיקרי (H או S).
    """
    def ok(hands):
        n = hands['N']
        s = hands['S']
        if not (20 <= hcp(n) <= 22 and is_balanced(n)):
            return False
        hs = hcp(s)
        if not (0 <= hs <= 9):
            return False
        d = distribution(s)
        return d['H'] >= 5 or d['S'] >= 5
    return _try(ok)


# ═══════════════════════════════════════════════════════════════════════════
#  חלוקה חופשית (ידיים מתקדמות ללא אילוצים מיוחדים)
# ═══════════════════════════════════════════════════════════════════════════

def deal_free():
    """חלוקה אקראית לחלוטין."""
    return _deal_random()


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 8 — סלם ב-NT
# ═══════════════════════════════════════════════════════════════════════════

def deal_slam_major(major='H'):
    """
    שיעור 9 (1♣ פתיחה): N=12-19 HCP, 5+ שליט. S=8-17 HCP, 4+ תמיכה.
    תרחישים:
      game  — combined < 33 → 4M
      slam  — combined ≥ 33 + סה״כ מפתחות ≥ 4 → 4NT → 6M
      stop  — combined ≥ 33 + סה״כ מפתחות < 4 → 4NT → 5M
    """
    scenario = random.choices(['slam', 'stop', 'game'], weights=[5, 3, 2])[0]

    def _opens_1c(n, hn, dn):
        """בדיקה מהירה: N יפתח 1♣ (ללא קריאה ל-_opening_bid)."""
        if dn['S'] >= 5 or dn['H'] >= 5:
            return False
        if dn['D'] > dn['C']:
            return False
        if dn['D'] == dn['C'] and dn['D'] >= 5:
            return False
        if 15 <= hn <= 17 and is_balanced(n):
            return False
        return True

    s_min = 8  if scenario == 'game' else 14
    s_max = 14 if scenario == 'game' else 17
    # stop: combined ≥ 30 מספיק — dp של השיעור ישלים ל-33+
    combined_min = 0 if scenario == 'game' else (33 if scenario == 'slam' else 30)
    inner_tries = 150 if scenario in ('slam', 'stop') else 60

    for _outer in range(80_000):
        deck = make_deck()
        random.shuffle(deck)

        s = deck[:13]
        hs = hcp(s)
        if not (s_min <= hs <= s_max):
            continue
        if suit_len(s, major) < 4:
            continue
        # כש-trump=♥: S לא יכריז 1♠ לפני ♥ (ימנע רוורס בלתי-אפשרי)
        if major == 'H' and suit_len(s, 'S') >= suit_len(s, 'H'):
            continue
        s_kc = key_cards(s, major)
        s_trump = suit_len(s, major)

        remaining = deck[13:]
        for _inner in range(inner_tries):
            random.shuffle(remaining)
            n = remaining[:13]
            dn = distribution(n)
            if dn[major] < 4:
                continue
            if dn[major] + s_trump > 9:
                continue
            hn = hcp(n)
            if not (12 <= hn <= 19):
                continue
            if hs + hn < combined_min:
                continue
            if not _opens_1c(n, hn, dn):
                continue

            combined = hs + hn
            total_kc = s_kc + key_cards(n, major)

            if scenario == 'game':
                if not (22 <= combined <= 32):
                    continue
            elif scenario == 'slam':
                if total_kc < 4:
                    continue
            else:  # stop
                if total_kc >= 4:
                    continue

            e = remaining[13:26]
            w = remaining[26:]
            return {'N': n, 'E': e, 'S': s, 'W': w}

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו')


def deal_slam_nt_mode_a():
    """
    Mode A: N=15-17 HCP מאוזן (פותח 1NT).
    S=0-18 HCP מאוזן, ללא 5+ מיגור עיקרי.
    35% slam: S=16-18 ו-total>=33 (מוביל ל-6NT).
    """
    use_slam = random.random() < 0.35
    def ok(hands):
        n, s = hands['N'], hands['S']
        hn = hcp(n)
        if not (15 <= hn <= 17 and is_balanced(n)):
            return False
        hs = hcp(s)
        if use_slam:
            if not (16 <= hs <= 18):
                return False
            if hs + hn < 33:
                return False
        else:
            if not (0 <= hs <= 15):
                return False
        if not is_balanced(s):
            return False
        d = distribution(s)
        return d['H'] < 4 and d['S'] < 4
    return _try(ok)


def deal_slam_nt_mode_d(opening='C', response='S'):
    """
    Mode D: N=12-17 HCP, פותח 1♣/1♦, ללא 4♥/4♠ (מבטיח ריבאד 1NT).
    S מכריז 1♥ או 1♠ — אם response=S, S ללא 4♥.
    רגיל: S=18-20, ללא 5+ סדרה — חמישייה: S=20, בדיוק 4 בצבע-תגובה, 5+ מינור.
    """
    open_sym = SUIT_SYMBOLS[opening]
    use_five = random.random() < 0.4

    for _outer in range(_MAX_TRIES):
        deck = make_deck()
        random.shuffle(deck)
        s = deck[:13]
        hs = hcp(s)

        if suit_len(s, response) < 4:
            continue
        if response == 'S' and suit_len(s, 'H') >= 4:
            continue
        if response == 'H' and suit_len(s, 'S') > suit_len(s, 'H'):
            continue  # עם ♠ ארוך יותר מ-♥ — צריך לכריז 1♠, לא 1♥

        if use_five:
            if hs != 20:
                continue
            if suit_len(s, response) != 4:
                continue
            if not any(suit_len(s, su) >= 5 for su in ['D', 'C']):
                continue
        else:
            if not (18 <= hs <= 20):
                continue
            if suit_len(s, 'S') >= 5 or suit_len(s, 'H') >= 5:
                continue

        remaining = deck[13:]
        for _inner in range(60):
            random.shuffle(remaining)
            n = remaining[:13]
            hn = hcp(n)
            if not (12 <= hn <= 17):
                continue
            if _opening_bid(n)[0] != f'1{open_sym}':
                continue
            if suit_len(n, 'H') >= 4 or suit_len(n, 'S') >= 4:
                continue
            if not use_five and hn < 15 and hs > 18:
                continue
            e = remaining[13:26]
            w = remaining[26:]
            return {'N': n, 'E': e, 'S': s, 'W': w}

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו')


def deal_slam_nt_mode_e():
    """
    Mode E: N פותח 1♣/1♦, S=5♠+4♥, 18-21 HCP.
    N=11-17 HCP, בדיוק 3 קלפי ♠ (תמיכה ב-3♠), ללא 4♥/4♠ (מבטיח ריבאד 1NT).
    """
    for _outer in range(_MAX_TRIES):
        deck = make_deck()
        random.shuffle(deck)
        s = deck[:13]
        hs = hcp(s)

        if not (18 <= hs <= 21):
            continue
        if suit_len(s, 'S') < 5:
            continue
        if suit_len(s, 'H') < 4:
            continue

        remaining = deck[13:]
        for _inner in range(60):
            random.shuffle(remaining)
            n = remaining[:13]
            hn = hcp(n)
            if not (11 <= hn <= 17):
                continue
            if suit_len(n, 'H') >= 4 or suit_len(n, 'S') >= 4:
                continue
            if suit_len(n, 'S') != 3:
                continue
            open_bid, _ = _opening_bid(n)
            spade_sym = SUIT_SYMBOLS['S']
            club_sym  = SUIT_SYMBOLS['C']
            diamond_sym = SUIT_SYMBOLS['D']
            if open_bid not in (f'1{club_sym}', f'1{diamond_sym}'):
                continue
            e = remaining[13:26]
            w = remaining[26:]
            return {'N': n, 'E': e, 'S': s, 'W': w}

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו')


def deal_slam_nt_mode_b():
    """
    Mode B: N=20-22 HCP מאוזן (פותח 2NT).
    S=5-15 HCP מאוזן, ללא 4+ מיגור.
    35% slam: S=13-15 (combined תמיד ≥ 33).
    65% non-slam: S=5-12.
    """
    use_slam = random.random() < 0.35
    def ok(hands):
        n, s = hands['N'], hands['S']
        hn = hcp(n)
        if not (20 <= hn <= 22 and is_balanced(n)):
            return False
        hs = hcp(s)
        if use_slam:
            if not (13 <= hs <= 15):
                return False
        else:
            if not (5 <= hs <= 12):
                return False
        if not is_balanced(s):
            return False
        d = distribution(s)
        return d['H'] < 4 and d['S'] < 4
    return _try(ok)


def deal_slam_nt_mode_c(opening='C', response='H'):
    """
    Mode C: N=12-16 HCP, פותח בצבע (ריבאד 1NT), ללא התאמה בצבע התגובה.
    S=14-21 HCP, בדיוק 4 קלפי בצבע התגובה.
    35% slam: S=17-21 ו-total>=33 (מוביל ל-4NT/6NT).
    65% non-slam: S=14-20, total<33 (תגובה 3NT או 4NT שנדחית).
    """
    open_sym = SUIT_SYMBOLS[opening]
    use_slam = random.random() < 0.35

    for _outer in range(80_000):
        deck = make_deck()
        random.shuffle(deck)

        s = deck[:13]
        hs = hcp(s)
        if use_slam:
            if not (17 <= hs <= 21):
                continue
        else:
            if not (14 <= hs <= 20):
                continue
        resp_len = suit_len(s, response)
        if resp_len != 4:
            continue
        if response == 'H' and suit_len(s, 'S') >= 4:
            continue
        if response == 'S' and suit_len(s, 'H') >= 4:
            continue

        remaining = deck[13:]
        for _inner in range(60):
            random.shuffle(remaining)
            n = remaining[:13]
            hn = hcp(n)
            if use_slam:
                if hs + hn < 33:
                    continue
            else:
                if hs + hn >= 33:
                    continue
            if not (12 <= hn <= 16):
                continue
            if _opening_bid(n)[0] != f'1{open_sym}':
                continue
            if suit_len(n, response) >= 4:
                continue
            e = remaining[13:26]
            w = remaining[26:]
            return {'N': n, 'E': e, 'S': s, 'W': w}

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו')


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 2♣ — מחשב (N) פותח 2♣, תלמיד (S) עונה
#  אילוץ: N=23+ HCP כל חלוקה, או 18-22 HCP עם 9+ לקיחות מידיות
#          S=0-10 HCP
# ═══════════════════════════════════════════════════════════════════════════

def deal_robot_opens_2c():
    """
    N = 23+ HCP (כל חלוקה), או 18-22 HCP עם 9+ לקיחות מידיות.
    S = ידיים ברורות בלבד:
        - 0-5 HCP  → 2♦ שלילי ברור
        - 8-10 HCP עם 5+ קלפי צבע, או מאוזן → תגובה חיובית ברורה
    נמנעים מטווח 6-7 HCP הגבולי.
    """
    import random as _r
    force_major = _r.random() < 0.60  # 60% מהידיות — N עם 5+ מיגור

    def ok(hands):
        n, s = hands['N'], hands['S']
        hn = hcp(n)
        st = sure_tricks(n)
        if not (hn >= 23 or (hn >= 18 and st >= 9)):
            return False
        d_n = distribution(n)
        if force_major:
            if not (d_n['H'] >= 5 or d_n['S'] >= 5):
                return False
        hs = hcp(s)
        if 4 <= hs <= 10:
            d_s = distribution(s)
            has_5major = d_s['H'] >= 5 or d_s['S'] >= 5
            has_5minor = d_s['C'] >= 5 or d_s['D'] >= 5
            if has_5minor and not has_5major:
                return False
            return True
        return False
    return _try(ok)


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 10 — Weak Two: מחשב (N) פותח 2♥/2♠, תלמיד (S) עונה
# ═══════════════════════════════════════════════════════════════════════════

def deal_weak_two(major='H'):
    """
    N: 6-9 HCP, בדיוק 6 קלפי major, פתיחה 2M.
    S: תרחישים:
      pass   — 0-3 לקיחות גבוהות
      raise3 — 4 לקיחות גבוהות + 2+ קלפי major
      game   — 5+ לקיחות גבוהות + 2+ קלפי major
      nt     — 5+ לקיחות גבוהות + עוצרים ב-3 הסדרות האחרות
    """
    sym = SUIT_SYMBOLS[major]
    scenario = random.choice(['pass', 'raise3', 'game', 'game', 'nt'])
    other = [s for s in ['S', 'H', 'D', 'C'] if s != major]

    for _outer in range(80_000):
        deck = make_deck()
        random.shuffle(deck)

        s = deck[:13]
        st  = sure_tricks(s)
        fit = suit_len(s, major) >= 2
        stops = all(has_stopper(s, suit) for suit in other)

        if scenario == 'pass':
            if st > 2:
                continue
        elif scenario == 'raise3':
            if st != 3 or not fit:
                continue
        elif scenario == 'game':
            if st < 4 or not fit:
                continue
        elif scenario == 'nt':
            if st < 4 or not stops:
                continue

        remaining = deck[13:]
        pos = random.choice([1, 2, 3])
        for _inner in range(300):
            random.shuffle(remaining)
            n = remaining[:13]
            if not (6 <= hcp(n) <= 9):
                continue
            if suit_len(n, major) != 6:
                continue
            if _opening_bid(n, position=pos)[0] != f'2{sym}':
                continue
            e = remaining[13:26]
            w = remaining[26:]
            if not (_quiet_opponent(e) and _quiet_opponent(w)):
                continue
            return {'N': n, 'E': e, 'S': s, 'W': w, 'position': pos}

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו')


def deal_student_weak2(major='H'):
    """
    שיעור 10 (תלמיד פותח): S פותח Weak Two (2♥/2♠).
    S: 6-9 HCP, בדיוק 6 קלפי major, פתיחה 2M.
    N: יד תגובה מגוונת (pass / raise3 / game / nt).
    """
    sym = SUIT_SYMBOLS[major]
    scenario = random.choice(['pass', 'raise3', 'game', 'game', 'nt'])
    other = [s for s in ['S', 'H', 'D', 'C'] if s != major]

    for _outer in range(80_000):
        deck = make_deck()
        random.shuffle(deck)

        pos = random.choice([1, 2, 3])
        s = deck[:13]
        if not (6 <= hcp(s) <= 9):
            continue
        if suit_len(s, major) != 6:
            continue
        honors = sum(1 for c in s if c[1] == major and c[0] in ('A', 'K', 'Q', 'J'))
        if honors < 2:
            continue
        if _opening_bid(s, position=pos)[0] != f'2{sym}':
            continue

        remaining = deck[13:]
        for _inner in range(60):
            random.shuffle(remaining)
            n = remaining[:13]
            st    = sure_tricks(n)
            fit   = suit_len(n, major) >= 2
            stops = all(has_stopper(n, suit) for suit in other)

            if scenario == 'pass'   and st > 2:
                continue
            if scenario == 'raise3' and (st != 3 or not fit):
                continue
            if scenario == 'game'   and (st < 4 or not fit):
                continue
            if scenario == 'nt'     and (st < 4 or not stops):
                continue

            e = remaining[13:26]
            w = remaining[26:]
            if not (_quiet_opponent(e) and _quiet_opponent(w)):
                continue
            return {'N': n, 'E': e, 'S': s, 'W': w, 'position': pos}

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו')


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 11 — Ogust: S פותח Weak Two, N שואל 2NT, S עונה אוגוסט
# ═══════════════════════════════════════════════════════════════════════════

def deal_overcall():
    """
    E: 12-19 HCP, פתיחה 1-בצבע (1♣/1♦/1♥/1♠).
    S: ~88% — אוברקול בצבע (get_overcall מחזיר הכרזה, לא X/1NT).
       ~12% — פס (אין אוברקול מתאים).
    N, W: אקראי.
    """
    from engine.overcall import get_overcall as _get_oc

    scenario   = random.choices(
        ['overcall', 'game', 'pass'], weights=[63, 25, 12])[0]
    # גיוון בפתיחות — רק לתרחישים קלים; 'game' מאפשר כל פתיחה כדי למנוע כישלון
    open_suit  = random.choice(['♣', '♦', '♥', '♠']) if scenario != 'game' else None
    _sym_to_suit = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        e = hands['E']
        s = hands['S']
        n = hands['N']

        he = hcp(e)
        if not (12 <= he <= 19):
            continue
        # כל השחקנים — מקסימום 6 קלפים בכל צבע
        if any(any(v > 6 for v in distribution(hands[p]).values()) for p in ('E', 'W', 'S', 'N')):
            continue
        e_bid_raw, _ = _opening_bid(e)
        # רק פתיחה 1-בצבע; לתרחישים שאינם game — גם בצבע הנבחר
        if not (len(e_bid_raw) == 2 and e_bid_raw[0] == '1' and e_bid_raw[1] in '♣♦♥♠'):
            continue
        if open_suit and e_bid_raw != f'1{open_suit}':
            continue

        oc_bid, _ = _get_oc(s, e_bid_raw)
        is_suit = len(oc_bid) == 2 and oc_bid[0].isdigit()

        if scenario == 'pass':
            # פס — S צריך לפחות 8 נק' (כדי שהחלטה לא תהיה טריוויאלית)
            if oc_bid != 'Pass' or not (8 <= hcp(s) <= 11):
                continue
            return hands
        elif not is_suit:
            # X או 1NT — לא מתאים לשום תרחיש בשיעור זה
            continue

        # כשS מכריז אוברקול — N חייב עם 3+ קלפים בצבע S
        oc_suit = _sym_to_suit.get(oc_bid[1], '')
        if distribution(n).get(oc_suit, 0) < 3:
            continue

        if scenario == 'game':
            # S חזק (14+) ו-N מזמין (לא מינימום) — כדי שהמכרז יגיע למשחק
            from engine.scoring import dist_fit_pts as _dfp
            oc_lvl_s = int(oc_bid[0])
            if hcp(s) < 14:
                continue
            n_ts = hcp(n) + _dfp(n, trump=oc_suit)
            # N חייב להזמין: 11+ לרמה 1, 13+ (כולל אורך) לרמה 2
            n_invite_min = 11 if oc_lvl_s == 1 else 13
            if n_ts < n_invite_min:
                continue

        return hands

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו')


def deal_overcall_response():
    """
    W: 12-19 HCP, פתיחה 1-בצבע.
    N: יד אוברקול בצבע (get_overcall מחזיר 1X או 2X).
    S תרחישים:
      support  60% — 3+ תמיכה, 8-15 HCP (חלוקה פנימית לפי נקודות)
      nt       20% — מאוזן + עצור, 8-12 HCP
      pass     20% — פחות מ-7 HCP
    """
    from engine.overcall import get_overcall as _get_oc, respond_overcall as _resp_oc

    _sym_to_suit = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}

    scenario  = random.choices(
        ['support', 'new_suit', 'nt', 'pass'],
        weights=[55, 20, 13, 12]
    )[0]
    open_suit = random.choice(['♣', '♦', '♥', '♠'])   # גיוון בפתיחות

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        w = hands['W']
        n = hands['N']
        s = hands['S']

        # יריבים — מקסימום 6 קלפים בכל צבע
        if any(v > 6 for v in distribution(w).values()):
            continue
        if any(v > 6 for v in distribution(hands['E']).values()):
            continue
        # W פותח 1-בצבע בצבע שנבחר אקראית
        if not (12 <= hcp(w) <= 19):
            continue
        w_bid_raw, _ = _opening_bid(w)
        if w_bid_raw != f'1{open_suit}':
            continue
        op_suit = _sym_to_suit[open_suit]

        # N מכריז אוברקול בצבע
        n_bid, _ = _get_oc(n, w_bid_raw)
        if not (len(n_bid) == 2 and n_bid[0].isdigit()):
            continue
        oc_suit = _sym_to_suit.get(n_bid[1], '')

        hs = hcp(s)
        ds = distribution(s)
        sup = ds.get(oc_suit, 0)

        # דחה יד S עם 6+ קלפים בצבע ללא אף מכובד (A/K/Q/J)
        _honors = {'A', 'K', 'Q', 'J'}
        if any(
            ds[suit] >= 6 and
            not any(c[0] in _honors for c in s if c[1] == suit)
            for suit in ['S', 'H', 'D', 'C']
        ):
            continue

        # אילוצי תרחיש על יד S
        if scenario == 'support':
            oc_lvl_n = int(n_bid[0])
            # מינור או אוברקול ברמה 2+: נדרש 10+ נקודות
            min_pts = 10 if (oc_suit in ('C', 'D') or oc_lvl_n >= 2) else 8
            if not (min_pts <= hs <= 15 and sup >= 3):
                continue
        elif scenario == 'nt':
            if not (8 <= hs <= 12 and is_balanced(s) and
                    op_suit and has_stopper(s, op_suit) and sup < 3):
                continue
        elif scenario == 'new_suit':
            # 11+ HCP, 5+ קלפים בצבע חדש (לא oc_suit, לא op_suit), פחות מ-3 תמיכה
            has_new = any(
                ds[suit] >= 5
                for suit in ['S', 'H', 'D', 'C']
                if suit not in (oc_suit, op_suit)
            )
            if not (hs >= 11 and has_new and sup < 3):
                continue
        elif scenario == 'pass':
            if hs >= 8:
                continue

        # בדוק שהתגובה המחושבת סבירה (אין 5m/4m-מינור הזמנה)
        s_bid, _ = _resp_oc(s, n_bid, w_bid_raw)
        is_minor_invite = (
            len(s_bid) == 2 and s_bid[0] == '4' and
            s_bid[1] in ('♣', '♦') and oc_suit in ('C', 'D')
        )
        if s_bid == '5NT' or is_minor_invite:
            continue

        return hands

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו')


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 13 — צבע רביעי (FSF)
#  מסלול: 1♣ (N) — 1♥ (S) — 1♠ (N) — 2♦? (S, תלמיד)
# ═══════════════════════════════════════════════════════════════════════════

def deal_fourth_suit():
    """
    N: 12-17 HCP, פותח 1♣, ריבאד 1♠ (4+ ♠).
    S: 11-15 HCP, 4-5♥, ללא 4+♠, ללא 6+♥, ללא עוצר ב-♦.
    תרחישים:
      'stopper'    (2/4) — N יש עוצר ♦ → יענה 2NT/3NT אחרי FSF
      'support'    (1/4) — N יש 3♥, אין עוצר ♦ → יענה 2♥ אחרי FSF
      'minor_back' (1/4) — N אין עוצר ♦, אין 3♥ → יענה 3♣ (חזרה למינור)
    """
    from engine.response import respond_minor as _resp_minor
    from engine.rebid import opener_rebid as _rebid

    scenario = random.choices(['stopper', 'support', 'minor_back'], weights=[2, 1, 1])[0]

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        n = hands['N']
        s = hands['S']

        hn = hcp(n)
        hs = hcp(s)
        dn = distribution(n)
        ds = distribution(s)

        # N: 12-16 HCP, opens 1♣ — 4+♣, ♣ ארוך לפחות כמו ♦
        if not (12 <= hn <= 16):
            continue
        if dn['C'] < 4:
            continue
        if dn['D'] > dn['C']:
            continue
        if dn['H'] >= 5 or dn['S'] >= 5:
            continue

        # N: 4+ ♠ לריבאד
        if dn['S'] < 4:
            continue

        # S: 12-15 HCP, 4-5♥
        if not (12 <= hs <= 15):
            continue
        if not (4 <= ds['H'] <= 5):
            continue

        # S: <4♠, <6♥ (אין הכרזה טבעית)
        if ds['S'] >= 4 or ds['H'] >= 6:
            continue

        # ידיים חצי-מאוזנות: ללא void וללא סינגלטון
        if min(dn.values()) < 2 or min(ds.values()) < 2:
            continue

        # S: ללא עוצר ♦ (כדי שיצטרך FSF)
        if has_stopper(s, 'D'):
            continue

        # וידוא שS מכריז 1♥ ו-N מכריז 1♠
        s_resp, _ = _resp_minor(s, 'C')
        if s_resp != '1♥':
            continue
        n_rebid, _ = _rebid(n, '1♣', '1♥')
        if n_rebid != '1♠':
            continue

        # אילוצי תרחיש על N — בדיקה ישירה דרך engine
        from engine.fourth_suit import n_respond_fsf as _n_fsf
        n_resp, _ = _n_fsf(n, 'D', 'C', 'H')
        if scenario == 'stopper':
            if 'NT' not in n_resp:
                continue
        elif scenario == 'support':
            if '♥' not in n_resp:
                continue
        else:  # minor_back — N חוזר ל-♣ (אין עוצר, אין תמיכה)
            if '♣' not in n_resp:
                continue

        return hands

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו — deal_fourth_suit')


def deal_fourth_suit_heart():
    """
    מסלול: 1♥ (N) — 1♠ (S) — 2♣ (N) — 2♦ (S, FSF)
    N: 12-16 HCP, 5+ ♥, 4+ ♣, ללא 4+♠, ללא 4+♦.
    S: 12-15 HCP, 4+♠, ללא עוצר ♦, חצי-מאוזן.
    """
    from engine.response import respond_major as _resp_major
    from engine.rebid import opener_rebid as _rebid

    scenario = random.choices(['stopper', 'support', 'minor_back'], weights=[2, 1, 1])[0]

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        n = hands['N']
        s = hands['S']
        hn = hcp(n)
        hs = hcp(s)
        dn = distribution(n)
        ds = distribution(s)

        # N: 12-16 HCP, 5+♥, 4+♣, ללא 4+♠, ללא 4+♦
        if not (12 <= hn <= 16):
            continue
        if dn['H'] < 5 or dn['C'] < 4:
            continue
        if dn['S'] >= 4 or dn['D'] >= 4:
            continue

        # S: 12-15 HCP, 4+♠, ללא עוצר ♦, ללא void
        if not (12 <= hs <= 15):
            continue
        if ds['S'] < 4:
            continue
        if has_stopper(s, 'D'):
            continue
        if min(ds.values()) < 1:
            continue

        # N: ללא void
        if min(dn.values()) < 1:
            continue

        return hands

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו — deal_fourth_suit_heart')


def deal_fourth_suit_diamond():
    """
    מסלול: 1♦ (N) — 1♥ (S) — 1♠ (N) — 2♣? (S, תלמיד, FSF בגובה 2)
    N: 12-17 HCP, פותח 1♦, 4+ ♠ לריבאד, ללא ♦>4 (כדי שלא ייתמך ב-♦).
    S: 11-14 HCP, 4-5♥, ללא 4+♠, ללא 6+♥, ללא עוצר ב-♣.
    תרחישים:
      'stopper'    (2/4) — N יש עוצר ♣ → יענה 2NT/3NT
      'support'    (1/4) — N יש 3♥, אין עוצר ♣ → יענה 2♥
      'minor_back' (1/4) — N אין עוצר ♣, אין 3♥ → יענה 2♦ (חזרה לפתיחה)
    """
    from engine.response import respond_minor as _resp_minor
    from engine.rebid import opener_rebid as _rebid

    scenario = random.choices(['stopper', 'support', 'minor_back'], weights=[2, 1, 1])[0]

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        n = hands['N']
        s = hands['S']

        hn = hcp(n)
        hs = hcp(s)
        dn = distribution(n)
        ds = distribution(s)

        # N: 12-16 HCP, פותח 1♦ — 4+♦, ♦ ארוך לפחות כמו ♣, ללא 5+ מייג'ור
        if not (12 <= hn <= 16):
            continue
        if dn['D'] < 4:
            continue
        if dn['C'] > dn['D']:
            continue
        if dn['H'] >= 5 or dn['S'] >= 5:
            continue
        if dn['S'] < 4:
            continue

        # S: 12-14 HCP, 4-5♥, ללא 4+♠, ללא 6+♥, ללא עוצר ♣
        if not (12 <= hs <= 14):
            continue
        if not (4 <= ds['H'] <= 5):
            continue
        if ds['S'] >= 4 or ds['H'] >= 6:
            continue
        if has_stopper(s, 'C'):
            continue

        # ידיים חצי-מאוזנות: ללא void וללא סינגלטון
        if min(dn.values()) < 2 or min(ds.values()) < 2:
            continue

        return hands

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו — deal_fourth_suit_diamond')


def deal_stopper_ask():
    """
    מסלול: 1♦ (N) — 2♦ (S, תמיכה חלשה) — 3♥ (N, שאלת עוצר) — ? (S)
    N: 15-17 HCP, פותח 1♦, אין עוצר ♥, מחפש 3NT.
    S: 6-10 HCP, 5+ ♦, ללא 4+ מיגור עיקרי.
    תרחישים:
      'has_heart' (2/4) — S יש עוצר ♥ → 3NT
      'has_spade' (1/4) — S אין ♥, יש עוצר ♠ → 3♠
      'no_stop'   (1/4) — S אין עוצרים → 4♦
    """
    scenario = random.choices(['has_heart', 'has_spade', 'no_stop'], weights=[3, 2, 1])[0]

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        n = hands['N']
        s = hands['S']

        hn = hcp(n)
        hs = hcp(s)
        dn = distribution(n)
        ds = distribution(s)

        # N: 18-19 HCP, 4+ ♦, אין עוצר ♥ (N שואל כי הוא עצמו חסר)
        if not (18 <= hn <= 19):
            continue
        if dn['D'] < 4:
            continue
        if dn['H'] >= 4 or dn['S'] >= 4:
            continue
        if has_stopper(n, 'H'):
            continue

        # ידיים חצי-מאוזנות: N ללא void, S ללא void וללא סינגלטון
        if min(dn.values()) < 1 or min(ds.values()) < 2:
            continue

        # S: 7-10 HCP, 5+ ♦, ללא 4+ מיגור עיקרי
        if not (7 <= hs <= 10):
            continue
        if ds['D'] < 5:
            continue
        if ds['H'] >= 4 or ds['S'] >= 4:
            continue

        # בדיקת תרחיש
        if scenario == 'has_heart':
            if not has_stopper(s, 'H'):
                continue
        elif scenario == 'has_spade':
            if has_stopper(s, 'H') or not has_stopper(s, 'S'):
                continue
        else:  # no_stop
            if has_stopper(s, 'H') or has_stopper(s, 'S'):
                continue

        return hands

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו — deal_stopper_ask')


def deal_stopper_ask_generic(opener_minor, ask_suit):
    """
    גנרי: N פותח מינור, S תומך, N שואל עוצר בסדרה שרצה.
    opener_minor: 'C' | 'D'
    ask_suit:     'H' | 'S' | 'D' (עבור פתיחה ♣) | 'C' (עבור פתיחה ♦)
    תרחישים:
      'has_asked' (2/4) — יש לS עוצר בסדרה הנשאלת  → 3NT
      'has_other' (1/4) — אין עוצר נשאל, יש עוצר אחר → מראה
      'no_stop'   (1/4) — אין עוצרים → חוזר למינור
    """
    min_sym  = {'C': '♣', 'D': '♦'}[opener_minor]
    opening  = f'1{min_sym}'
    other_suits = [s for s in ['S', 'H', 'D', 'C']
                   if s != opener_minor and s != ask_suit]
    scenario = random.choices(['has_asked', 'has_other', 'no_stop'],
                              weights=[3, 2, 1])[0]

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        n = hands['N']
        s = hands['S']
        hn = hcp(n)
        hs = hcp(s)
        dn = distribution(n)
        ds = distribution(s)

        if not (15 <= hn <= 17):
            continue
        if _opening_bid(n)[0] != opening:
            continue
        if has_stopper(n, ask_suit):
            continue

        if not (12 <= hs <= 14):
            continue
        if ds[opener_minor] < 5:
            continue
        if ds['H'] >= 4 or ds['S'] >= 4:
            continue

        if scenario == 'has_asked':
            if not has_stopper(s, ask_suit):
                continue
        elif scenario == 'has_other':
            if has_stopper(s, ask_suit):
                continue
            if not any(has_stopper(s, os) for os in other_suits):
                continue
        else:  # no_stop
            if has_stopper(s, ask_suit):
                continue
            if any(has_stopper(s, os) for os in other_suits):
                continue

        return hands

    raise RuntimeError(
        f'לא ניתן לחלק יד — deal_stopper_ask_generic({opener_minor}, {ask_suit})')


def deal_fourth_suit_minor():
    """
    מסלול: 1♣ (N) — 1♦ (S) — 2♣ (N) — 2♠? (S, תלמיד, FSF בגובה 2)
    N: 12-17 HCP, פותח 1♣, 6+ ♣ (ריבאד 2♣), ללא 4+ מיגור עיקרי.
    S: 11-14 HCP, 4-5♦, ללא 4+ מיגור עיקרי, ללא עוצר ב-♠.
    תרחישים:
      'stopper' (2/3) — N יש עוצר ♠ → יענה 2NT/3NT אחרי FSF
      'support' (1/3) — N יש 3+♦, אין עוצר ♠ → יענה 3♦ (תמיכה במינור)
    """
    from engine.response import respond_minor as _resp_minor
    from engine.rebid import opener_rebid as _rebid

    scenario = random.choices(['stopper', 'support'], weights=[2, 1])[0]

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        n = hands['N']
        s = hands['S']

        hn = hcp(n)
        hs = hcp(s)
        dn = distribution(n)
        ds = distribution(s)

        # N: 12-17 HCP, פותח 1♣, ללא 4+ מיגור עיקרי
        if not (12 <= hn <= 17):
            continue
        if _opening_bid(n)[0] != '1♣':
            continue
        if dn['H'] >= 4 or dn['S'] >= 4:
            continue

        # S: 12-14 HCP, 4-5♦, ללא 4+ מיגור עיקרי, ללא עוצר ♠
        if not (12 <= hs <= 14):
            continue
        if not (4 <= ds['D'] <= 5):
            continue
        if ds['H'] >= 4 or ds['S'] >= 4:
            continue
        if has_stopper(s, 'S'):
            continue

        # וידוא מסלול: S מכריז 1♦, N מכריז 2♣
        s_resp, _ = _resp_minor(s, 'C')
        if s_resp != '1♦':
            continue
        n_rebid, _ = _rebid(n, '1♣', '1♦')
        if n_rebid != '2♣':
            continue

        # אילוצי תרחיש על N
        if scenario == 'stopper':
            if not has_stopper(n, 'S'):
                continue
        else:  # support
            if dn['D'] < 3 or has_stopper(n, 'S'):
                continue

        return hands

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו — deal_fourth_suit_minor')


def deal_ogust(major='H'):
    """
    S: 6-9 HCP, 6 קלפי major, כשיר לפתיחה 2M (2+ מתוך A/K/Q/J בסדרה).
    N: 15+ HCP.
    תרחישים: clubs/diamonds/hearts/spades/nt לפי תגובת S באוגוסט.
    """
    sym = SUIT_SYMBOLS[major]
    scenario = random.choices(
        ['clubs', 'diamonds', 'hearts', 'spades', 'nt'],
        weights=[25, 25, 25, 20, 5]
    )[0]

    for _outer in range(80_000):
        deck = make_deck()
        random.shuffle(deck)

        s = deck[:13]
        hs = hcp(s)
        if suit_len(s, major) != 6:
            continue
        honors_open = sum(1 for c in s if c[1] == major and c[0] in ('A', 'K', 'Q', 'J'))
        has_top_open = any(c[1] == major and c[0] in ('A', 'K') for c in s)
        if honors_open < 2 or not has_top_open:
            continue
        other_major = 'S' if major == 'H' else 'H'
        if suit_len(s, other_major) >= 4:
            continue
        honors = sum(1 for c in s if c[1] == major and c[0] in ('A', 'K', 'Q'))

        if scenario == 'clubs':      # 6-7 נק', מפוזרות (honors < 2)
            if not (6 <= hs <= 7) or honors >= 2:
                continue
        elif scenario == 'diamonds': # 6-7 נק', מרוכזות (honors >= 2)
            if not (6 <= hs <= 7) or honors < 2:
                continue
        elif scenario == 'hearts':   # 8-9 נק', מפוזרות (honors < 2)
            if not (8 <= hs <= 9) or honors >= 2:
                continue
        elif scenario == 'spades':   # 8-9 נק', מרוכזות (honors >= 2, לא 3)
            if not (8 <= hs <= 9) or honors < 2 or honors == 3:
                continue
        elif scenario == 'nt':       # AKQ בסדרה (honors == 3), 9 נק' בדיוק
            if honors != 3 or hs != 9:
                continue

        remaining = deck[13:]
        for _inner in range(60):
            random.shuffle(remaining)
            n = remaining[:13]
            if hcp(n) < 15:
                continue
            if sure_tricks(n) < 4:
                continue
            has_fit = suit_len(n, major) >= 2
            strong_suits = sum(
                1 for s in ['S', 'H', 'D', 'C']
                if suit_len(n, s) >= 4
                and sum(1 for c in n if c[1] == s and c[0] in ('A', 'K', 'Q')) >= 2
            )
            if not has_fit and strong_suits < 2:
                continue
            e = remaining[13:26]
            w = remaining[26:]
            return {'N': n, 'E': e, 'S': s, 'W': w}

    raise RuntimeError('לא ניתן לחלק יד עם האילוצים שנדרשו')


def deal_takeout_double():
    """
    E פותח 1 במיגור/מינור, N מכריז דבל להוצאה.
    E: 12-15 HCP, פותח 1 בצבע
    N: 9-16 HCP, 3+ קלפים בכל צבע חוץ מצבע E
    S: ידיים שונות (חלש 0-8 / בינוני 9-12 / חזק 13+)
    """
    from engine.takeout_double import can_double

    _SYM_MAP = {chr(0x2663): "C", chr(0x2666): "D", chr(0x2665): "H", chr(0x2660): "S"}
    scenario = random.choices(["weak", "medium", "strong"], weights=[3, 2, 1])[0]

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        w = hands["W"]
        n = hands["N"]
        s = hands["S"]

        hw = hcp(w)
        hn = hcp(n)
        hs = hcp(s)
        dn = distribution(n)
        ds = distribution(s)

        # W: 12-15 HCP, פותח 1 בצבע (לא NT)
        if not (12 <= hw <= 15):
            continue
        w_bid, _ = _opening_bid(w)
        if not w_bid or w_bid[0] != "1" or "NT" in w_bid:
            continue
        w_suit = next((v for k, v in _SYM_MAP.items() if k in w_bid), None)
        if not w_suit:
            continue

        # N: 9-16 HCP, דבל להוצאה, ללא 5+ בצבע אחר
        if not (9 <= hn <= 16):
            continue
        if not can_double(n, w_suit, level=1):
            continue
        if any(dn[suit] >= 5 for suit in ["S", "H", "D", "C"] if suit != w_suit):
            continue

        if scenario == "weak"   and not (0  <= hs <= 8):
            continue
        if scenario == "medium" and not (9  <= hs <= 12):
            continue
        if scenario == "strong" and not (13 <= hs <= 17):
            continue

        if min(dn.values()) < 1 or min(ds.values()) < 1:
            continue

        return hands

    raise RuntimeError("deal_takeout_double: לא ניתן לחלק יד")


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 14 שלב 1 — W פותח, N מדבל (12-16), S עונה
# ═══════════════════════════════════════════════════════════════════════════

def deal_takeout_double_phase1():
    """
    W: 12-15 HCP, פותח 1 בצבע (לא NT).
    N: 12-16 HCP, עומד בתנאי דבל להוצאה.
    S: חלש/בינוני/חזק (לתרגול תגובות).
    """
    from engine.takeout_double import can_double

    _SYM_MAP = {chr(0x2663): 'C', chr(0x2666): 'D', chr(0x2665): 'H', chr(0x2660): 'S'}
    scenario = random.choices(['weak', 'medium', 'strong'], weights=[2, 2, 2])[0]

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        w, n, s = hands['W'], hands['N'], hands['S']

        hw, hn, hs = hcp(w), hcp(n), hcp(s)
        dn, ds = distribution(n), distribution(s)

        if not (12 <= hw <= 15):
            continue
        if hcp(hands['E']) > 8:
            continue
        w_bid, _ = _opening_bid(w)
        if not w_bid or w_bid[0] != '1' or 'NT' in w_bid:
            continue
        w_suit = next((v for k, v in _SYM_MAP.items() if k in w_bid), None)
        if not w_suit:
            continue
        # ~80% פתיחות מינור (♣/♦) כדי שS יכריז מיגור ברמה 1
        if w_suit in ('H', 'S') and random.random() < 0.8:
            continue
        # S ללא 4+ בצבע הפותח — מונע פס קנס
        if distribution(s).get(w_suit, 0) >= 4:
            continue

        if not (12 <= hn <= 16):
            continue
        if not can_double(n, w_suit, level=1):
            continue
        # עם 5+ קלפים בצבע אחר — עדיף אוברקול, לא דבל
        if any(dn[suit] >= 5 for suit in ['S', 'H', 'D', 'C'] if suit != w_suit):
            continue

        if scenario == 'weak'   and not (0  <= hs <= 8):
            continue
        if scenario == 'medium' and not (9  <= hs <= 12):
            continue
        if scenario == 'strong' and not (13 <= hs <= 17):
            continue

        if min(ds.values()) < 1:
            continue

        # N+S צריכים לפחות כמו W+E
        if hn + hs < hw + hcp(hands['E']):
            continue

        # ידיים חזקות: לוודא שיש תשובה חד-משמעית
        if scenario == 'strong':
            from engine.takeout_double import _count_stoppers
            # בדיקת עוצרים משותפים
            stops = _count_stoppers(s, w_suit) + _count_stoppers(n, w_suit)
            # בדיקת התאמה במיגור
            major_fit = any(
                ds[m] >= 4 and dn[m] >= 4
                for m in ['H', 'S'] if m != w_suit
            ) or any(
                ds[m] >= 5 and dn[m] >= 3
                for m in ['H', 'S'] if m != w_suit
            )
            # בדיקת נקודות ל-5 מינור
            minor_pts = (hs + hn >= 28)
            if not (stops >= 2 or major_fit or minor_pts):
                continue

        return hands

    raise RuntimeError('deal_takeout_double_phase1: לא ניתן לחלק יד')


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 14 שלב 2 — E פותח, S מחליט X/Pass
#  ~50% ידיים שS יכול לדבל, ~50% שלא
# ═══════════════════════════════════════════════════════════════════════════

def deal_takeout_double_phase2():
    """
    E: 12-15 HCP, פותח 1 בצבע (לא NT).
    S: לפעמים 12-16 עם תבנית מתאימה (יכול לדבל),
       לפעמים לא עומד בתנאים (נקודות / קוצר / חלוקה).
    """
    from engine.takeout_double import can_double

    _SYM_MAP = {chr(0x2663): 'C', chr(0x2666): 'D', chr(0x2665): 'H', chr(0x2660): 'S'}
    can_double_target = random.choice([True, False])

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        e, s = hands['E'], hands['S']

        he, hs = hcp(e), hcp(s)

        if not (12 <= he <= 15):
            continue
        if hcp(hands['N']) > 8:
            continue
        if hcp(hands['W']) > 8:
            continue
        e_bid, _ = _opening_bid(e)
        if not e_bid or e_bid[0] != '1' or 'NT' in e_bid:
            continue
        e_suit = next((v for k, v in _SYM_MAP.items() if k in e_bid), None)
        if not e_suit:
            continue
        # ~80% פתיחות מינור
        if e_suit in ('H', 'S') and random.random() < 0.8:
            continue
        # S ללא 4+ בצבע הפותח — מונע פס קנס
        if distribution(s).get(e_suit, 0) >= 4:
            continue

        s_can = can_double(s, e_suit, level=1)
        if s_can != can_double_target:
            continue

        # N+S צריכים לפחות כמו E+W (ריאליסטי בהוראה)
        if hcp(s) + hcp(hands['N']) < he + hcp(hands['W']):
            continue

        if min(distribution(s).values()) < 1:
            continue

        return hands

    raise RuntimeError('deal_takeout_double_phase2: לא ניתן לחלק יד')


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 14 — נגטיב דאבל
#  N פותח 1 מינור, E מכריז 1 מיגור, S מחליט / N מכריז ריבאד
# ═══════════════════════════════════════════════════════════════════════════

_ND_RANK = {'C': 1, 'D': 2, 'H': 3, 'S': 4}
_ND_SYM  = {chr(0x2663): 'C', chr(0x2666): 'D', chr(0x2665): 'H', chr(0x2660): 'S'}


def deal_negative_double_phase1():
    """
    N: 12–15 HCP, פותח 1♣ או 1♦.
    E: 8–14 HCP, מכריז 1♥ או 1♠ (5+ קלפים).
    S: תרחישים מגוונים (נגטיב דאבל / טבעי / קיו / פס).
    W: שקט (< 10 HCP).
    """
    from engine.negative_double import s_response as _sr

    scenario = random.choices(
        ['neg_double', 'major', 'cue', '3NT', '2NT', 'minor', '1NT', 'pass'],
        weights=[6, 2, 1, 1, 1, 3, 1, 1])[0]

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        n, e, s, w = hands['N'], hands['E'], hands['S'], hands['W']

        if hcp(w) >= 10:
            continue

        hn = hcp(n)
        if not (12 <= hn <= 15):
            continue
        n_bid, _ = _opening_bid(n)
        if not n_bid or n_bid[0] != '1' or 'NT' in n_bid:
            continue
        n_suit = next((v for k, v in _ND_SYM.items() if k in n_bid), None)
        if not n_suit or n_suit not in ('C', 'D'):
            continue

        he = hcp(e)
        if not (8 <= he <= 14):
            continue
        de = distribution(e)
        e_candidates = [m for m in ['H', 'S'] if de[m] >= 5]
        if len(e_candidates) != 1:
            continue
        e_suit = e_candidates[0]
        e_level = 1

        ds = distribution(s)
        if min(ds.values()) < 2:  # חצי מאוזן — אין בודד לS
            continue
        bid, _ = _sr(s, n_suit, e_suit, e_level)
        s_suit = next((v for k, v in _ND_SYM.items() if k in bid), None)

        if scenario == 'neg_double':
            if bid != 'X':
                continue
        elif scenario == 'major':
            if not s_suit or s_suit not in ('H', 'S') or s_suit == e_suit:
                continue
        elif scenario == 'cue':
            if not s_suit or s_suit != e_suit:
                continue
        elif scenario == '3NT':
            if bid != '3NT':
                continue
        elif scenario == '2NT':
            if bid != '2NT':
                continue
        elif scenario == 'minor':
            if not s_suit or s_suit not in ('D', 'C'):
                continue
            if ds.get(s_suit, 0) < 5 or hcp(s) < 11:
                continue
        elif scenario == '1NT':
            if bid != '1NT':
                continue
        else:  # pass
            if bid != 'Pass':
                continue

        if min(ds.values()) < 1:
            continue

        return hands

    raise RuntimeError('deal_negative_double_phase1: לא ניתן לחלק יד')


def deal_negative_double_phase2():
    """
    N: 12–18 HCP, פותח 1♣ או 1♦, מראה ריבאד אחרי נגטיב דאבל.
    E: 8–14 HCP, מכריז 1♥ או 1♠.
    S: יכול לכריז נגטיב דאבל (7–12 HCP, 4+ מיגור, 3+ מינור).
    """
    scenario = random.choices(
        ['major', 'nt', 'minor'],
        weights=[5, 2, 3])[0]

    for _ in range(_MAX_TRIES):
        hands = _deal_random()
        n, e, s, w = hands['N'], hands['E'], hands['S'], hands['W']

        if hcp(w) >= 10:
            continue

        hn = hcp(n)
        if not (12 <= hn <= 18):
            continue
        n_bid, _ = _opening_bid(n)
        if not n_bid or n_bid[0] != '1' or 'NT' in n_bid:
            continue
        n_suit = next((v for k, v in _ND_SYM.items() if k in n_bid), None)
        if not n_suit or n_suit not in ('C', 'D'):
            continue

        he = hcp(e)
        if not (8 <= he <= 14):
            continue
        de = distribution(e)
        e_candidates = [m for m in ['H', 'S'] if de[m] >= 5]
        if len(e_candidates) != 1:
            continue
        e_suit = e_candidates[0]

        from engine.negative_double import can_negative_double
        if not can_negative_double(s, n_suit, e_suit, e_level=1):
            continue

        dn = distribution(n)
        unbid_major = next((m for m in ['S', 'H'] if m not in (n_suit, e_suit)), None)
        unbid_minor = next((m for m in ['D', 'C'] if m not in (n_suit, e_suit)), None)

        if scenario == 'major':
            if not unbid_major or dn[unbid_major] < 3:
                continue
        elif scenario == 'nt':
            if hn < 12:
                continue
            if not has_stopper(n, e_suit):
                continue
            if unbid_major and dn[unbid_major] >= 3:
                continue
        else:  # minor
            if unbid_major and dn[unbid_major] >= 3:
                continue
            if not unbid_minor or dn[unbid_minor] < 4:
                continue
            if hn >= 12 and has_stopper(n, e_suit):
                continue

        if min(distribution(s).values()) < 1:
            continue

        return hands

    raise RuntimeError('deal_negative_double_phase2: לא ניתן לחלק יד')
