"""
סקייל בדיקה מקיפה — שיעור 14: נגטיב דאבל.
בודק את כל שרשרת ההכרזה: S (תלמיד/שלב 1) + N (תגובה/שלב 2).

פונקציות שנבדקות:
  s_response         — מה S מכריז (שלב 1)
  opener_rebid       — ריבאד N אחרי X (גם שלב 1 וגם שלב 2)
  opener_after_cue   — ריבאד N אחרי קיו ביט של S
  opener_after_natural — ריבאד N אחרי הכרזת מיגור/מינור טבעית

שימוש:
    python tests/scale_negative_double.py          # 2000 ידיות
    python tests/scale_negative_double.py 500 -v   # מפורט (8 ידיות ראשונות)
"""

import sys, os
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import _deal_random
from engine.scoring import hcp, distribution, has_stopper
from engine.opening import opening_bid as _opening_bid
from engine.negative_double import (
    s_response, opener_rebid,
    opener_after_cue, opener_after_natural,
)
from engine.cards import SUIT_SYMBOLS

_S    = SUIT_SYMBOLS
_RANK = {'C': 1, 'D': 2, 'H': 3, 'S': 4}
_SYM  = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}


def _bid_suit(bid):
    for ch, s in _SYM.items():
        if ch in bid:
            return s
    return None


def _bid_level(bid):
    return int(bid[0]) if bid and bid[0].isdigit() else 0


def _min_lvl(suit, e_suit, e_level):
    return e_level if _RANK[suit] > _RANK[e_suit] else e_level + 1


# ── יצירת ידיות ──────────────────────────────────────────────────────────────

def _find_hand():
    """N פותח 1m, E מכריז 1M (5+), W שקט (<10 נק')."""
    for _ in range(200_000):
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
        n_suit = _bid_suit(n_bid)
        if n_suit not in ('C', 'D'):
            continue

        de = distribution(e)
        e_cands = [m for m in ['H', 'S'] if de[m] >= 5 and m != n_suit]
        if len(e_cands) != 1:
            continue
        e_suit = e_cands[0]

        return hands, n_suit, e_suit
    raise RuntimeError('לא ניתן לחלק יד תקינה')


# ── ציפייה תיאורטית לתגובת S ─────────────────────────────────────────────────

def _expected_s(s_hand, n_suit, e_suit, e_level=1):
    """מחזיר (category, expected_bid) לפי טבלת הכללים."""
    h = hcp(s_hand)
    d = distribution(s_hand)
    um = [m for m in ['S', 'H'] if m not in (n_suit, e_suit)]
    mn = [m for m in ['D', 'C'] if m not in (n_suit, e_suit)]

    for major in um:
        if d[major] >= 5:
            lvl     = _min_lvl(major, e_suit, e_level)
            min_hcp = 6 if lvl == e_level else 11
            if h >= min_hcp:
                return 'major', f'{lvl}{_S[major]}'

    # עדיפות ראשונה למיגור: 4 קלפים במיגור לא-מוכרז → X נגטיב (לפני 2NT/תמיכה/מינור)
    min_x_hcp = 7 if e_level == 1 else 8
    if h >= min_x_hcp:
        for major in um:
            if d[major] >= 4:
                return 'X', 'X'

    if h >= 13:
        if has_stopper(s_hand, e_suit):
            return '3NT', '3NT'
        return 'cue', f'{e_level + 1}{_S[e_suit]}'

    if h >= 11 and has_stopper(s_hand, e_suit):
        return '2NT', '2NT'

    if d[n_suit] >= 4 and h >= 6:
        if h >= 11:
            return 'support', f'3{_S[n_suit]}'
        return 'support', f'2{_S[n_suit]}'

    for minor in mn:
        if d[minor] >= 6 and h >= 11:
            lvl = _min_lvl(minor, e_suit, e_level)
            return 'minor', f'{lvl}{_S[minor]}'

    for major in um:
        if d[major] >= 4 and h >= 7:
            return 'X', 'X'

    for minor in mn:
        if d[minor] >= 5 and h >= 11:
            lvl = _min_lvl(minor, e_suit, e_level)
            return 'minor', f'{lvl}{_S[minor]}'

    if h >= 7 and has_stopper(s_hand, e_suit):
        return '1NT', '1NT'

    return 'Pass', 'Pass'


# ── ציפייה תיאורטית לריבאד N אחרי X ─────────────────────────────────────────

def _expected_rebid(n_hand, n_suit, e_suit, e_level=1):
    from engine.scoring import is_balanced
    h   = hcp(n_hand)
    d   = distribution(n_hand)
    bal = is_balanced(n_hand)
    um = next((m for m in ['S', 'H'] if m not in (n_suit, e_suit)), None)
    mn = next((m for m in ['D', 'C'] if m not in (n_suit, e_suit)), None)

    # תמיכה (3+) בסדרה שהראה ה-X — קודמת לכל השאר
    if um and d[um] >= 3:
        min_lvl = _min_lvl(um, e_suit, e_level)
        lvl = min_lvl if h <= 14 else min_lvl + 1
        return f'{lvl}{_S[um]}'

    # ללא תמיכה: קיו ביט (18-21, לא מאוזן-18-19)
    if 18 <= h <= 21 and not (bal and 18 <= h <= 19):
        return f'{e_level + 1}{_S[e_suit]}'

    if 18 <= h <= 19 and bal and has_stopper(n_hand, e_suit):
        return f'{e_level + 1}NT'

    if 12 <= h <= 14 and bal and has_stopper(n_hand, e_suit):
        return f'{e_level}NT'

    if mn and d[mn] >= 4:
        lvl = _min_lvl(mn, e_suit, e_level)
        return f'{lvl}{_S[mn]}'

    lvl = _min_lvl(n_suit, e_suit, e_level)
    if h >= 15:
        lvl = max(lvl, 3)
    return f'{lvl}{_S[n_suit]}'


# ── ציפייה תיאורטית לריבאד N אחרי קיו ביט ───────────────────────────────────

def _expected_cue(n_hand, n_suit, e_suit):
    d = distribution(n_hand)
    um = next((m for m in ['S', 'H'] if m not in (n_suit, e_suit)), None)

    if has_stopper(n_hand, e_suit):
        return '3NT'
    if um and d[um] >= 4:
        lvl = _min_lvl(um, e_suit, 2)
        return f'{lvl}{_S[um]}'
    return f'3{_S[n_suit]}'


# ── ציפייה תיאורטית לריבאד N אחרי מיגור טבעי של S ──────────────────────────

def _expected_natural(n_hand, s_suit, n_suit=None, e_suit=None):
    h = hcp(n_hand)
    d = distribution(n_hand)
    sym = _S[s_suit]

    # שורה 1: תמיכה 3+
    if d[s_suit] >= 3:
        if s_suit == n_suit:
            if h >= 15 and e_suit and has_stopper(n_hand, e_suit):
                return '3NT'
            if h >= 15:
                return f'5{sym}'
            return 'Pass'
        s_level = _min_lvl(s_suit, e_suit, 1) if e_suit else 1
        min_raise = s_level + 1
        if h >= 18:
            return f'{max(min_raise, 4)}{sym}'
        if h >= 15:
            return f'{max(min_raise, 3)}{sym}'
        return f'{min_raise}{sym}'

    # שורה 2: עוצר ב-E → 2NT
    if e_suit and has_stopper(n_hand, e_suit):
        return '2NT'

    # שורה 3: סדרה שנייה 4+ (לא n_suit, לא s_suit, לא e_suit)
    excluded = {n_suit, s_suit}
    if e_suit:
        excluded.add(e_suit)
    for suit in ['C', 'D', 'H', 'S']:
        if suit not in excluded and d[suit] >= 4:
            is_reverse = n_suit and _RANK[suit] > _RANK[n_suit]
            if is_reverse and h < 18:
                continue
            return f'2{_S[suit]}'

    # שורה 4: ריבאד בסדרת N עצמה 5+
    if n_suit and d[n_suit] >= 5:
        lvl = 3 if h >= 15 else 2
        return f'{lvl}{_S[n_suit]}'

    # שורה 5: פס
    return 'Pass'


# ── בדיקות ───────────────────────────────────────────────────────────────────

def _err(errors, msg):
    errors.append(msg)


def _check_legal_level(bid, e_suit, e_level, label, idx, errors):
    suit = _bid_suit(bid)
    lvl  = _bid_level(bid)
    if suit and lvl:
        min_l = _min_lvl(suit, e_suit, e_level)
        if lvl < min_l:
            _err(errors, f'#{idx} [{label}] {bid}: גובה {lvl} < מינימום {min_l}')


def check_s_response(hands, n_suit, e_suit, idx, errors):
    """בדיקת s_response."""
    s       = hands['S']
    h       = hcp(s)
    e_level = 1

    actual, _ = s_response(s, n_suit, e_suit, e_level)
    cat, exp  = _expected_s(s, n_suit, e_suit, e_level)

    if actual != exp:
        _err(errors,
             f'#{idx} s_response={actual} ציפינו={exp} [{cat}] '
             f'HCP={h} N={n_suit} E={e_suit}')

    _check_legal_level(actual, e_suit, e_level, 's_response', idx, errors)

    if actual == 'Pass' and h >= 13:
        _err(errors, f'#{idx} S={h}נק׳ → פס — 13+ לא יכול לפס')

    return cat, actual


def check_opener_rebid(hands, n_suit, e_suit, idx, errors, label='after_X'):
    """בדיקת opener_rebid אחרי X של S."""
    n       = hands['N']
    h       = hcp(n)
    d       = distribution(n)
    e_level = 1

    actual, _ = opener_rebid(n, n_suit, e_suit, e_level)
    exp       = _expected_rebid(n, n_suit, e_suit, e_level)

    if actual != exp:
        _err(errors,
             f'#{idx} [{label}] opener_rebid={actual} ציפינו={exp} '
             f'HCP={h} N={n_suit} E={e_suit}')

    if actual == 'Pass':
        _err(errors, f'#{idx} [{label}] N הכריז פס — אסור אחרי נגטיב דאבל')

    if 'NT' in actual and not has_stopper(n, e_suit):
        _err(errors, f'#{idx} [{label}] NT בלי עוצר ב{_S[e_suit]}')

    _check_legal_level(actual, e_suit, e_level, label, idx, errors)
    return actual


def check_after_cue(hands, n_suit, e_suit, idx, errors):
    """בדיקת opener_after_cue אחרי קיו ביט של S."""
    n      = hands['N']
    h      = hcp(n)
    actual, _ = opener_after_cue(n, n_suit, e_suit)
    exp    = _expected_cue(n, n_suit, e_suit)

    if actual != exp:
        _err(errors,
             f'#{idx} [after_cue] opener_after_cue={actual} ציפינו={exp} '
             f'HCP={h} N={n_suit} E={e_suit}')

    # בדיקת גובה חוקי ביחס לקיו ביט (שהיה e_level+1 בצבע e_suit)
    cue_level = 2   # e_level=1 → cue = 2{e_suit}
    suit = _bid_suit(actual)
    lvl  = _bid_level(actual)
    if suit and lvl:
        min_l = _min_lvl(suit, e_suit, cue_level)
        if lvl < min_l:
            _err(errors, f'#{idx} [after_cue] {actual}: גובה {lvl} < מינימום {min_l} (אחרי קיו {cue_level}{_S[e_suit]})')

    return actual


def check_after_natural(hands, n_suit, e_suit, s_bid, idx, errors):
    """בדיקת opener_after_natural אחרי הכרזת מיגור/מינור של S."""
    n      = hands['N']
    h      = hcp(n)
    s_suit = _bid_suit(s_bid)
    if not s_suit:
        return '—'

    actual, _ = opener_after_natural(n, n_suit, s_suit, e_suit)
    exp       = _expected_natural(n, s_suit, n_suit, e_suit)

    if actual != exp:
        _err(errors,
             f'#{idx} [after_natural({s_bid})] '
             f'opener_after_natural={actual} ציפינו={exp} '
             f'HCP={h} תמיכה={distribution(n)[s_suit]}')

    return actual


# ── הרצה ראשית ───────────────────────────────────────────────────────────────

def scale(n=2000, verbose=False):
    errors     = []
    s_cats     = Counter()
    s_bids     = Counter()
    n_after_x  = Counter()
    n_after_cue= Counter()
    n_after_nat= Counter()

    for i in range(1, n + 1):
        try:
            hands, n_suit, e_suit = _find_hand()
        except RuntimeError as exc:
            _err(errors, f'#{i}: {exc}')
            continue

        # ── שלב 1: בדיקת S ────────────────────────────────────────────────
        cat, s_bid = check_s_response(hands, n_suit, e_suit, i, errors)
        s_cats[cat]   += 1
        s_bids[s_bid] += 1

        # ── שלב 1: בדיקת תגובת N לפי מה ש-S הכריז ───────────────────────
        if s_bid == 'X':
            rb = check_opener_rebid(hands, n_suit, e_suit, i, errors, 'after_X')
            n_after_x[rb] += 1

        elif cat == 'cue':
            rb = check_after_cue(hands, n_suit, e_suit, i, errors)
            n_after_cue[rb] += 1

        elif cat in ('major', 'minor', 'support'):
            rb = check_after_natural(hands, n_suit, e_suit, s_bid, i, errors)
            n_after_nat[rb] += 1

        # ── שלב 2 (N תלמיד): בדיקת opener_rebid ─────────────────────────
        # מדמים שS תמיד הכריז X ובודקים את ריבאד N
        check_opener_rebid(hands, n_suit, e_suit, i, errors, 'phase2')

        if verbose and i <= 8:
            n_bid, _ = _opening_bid(hands['N'])
            de = distribution(hands['E'])
            e_m = next(m for m in ['H', 'S'] if de[m] >= 5)
            hs = hcp(hands['S'])
            rb2 = opener_rebid(hands['N'], n_suit, e_suit, 1)[0]
            print(f'  #{i}: N={n_bid} E=1{_S[e_m]} '
                  f'S={hs}נק׳→{s_bid} [{cat}]  N→{rb2}')

    return errors, s_cats, s_bids, n_after_x, n_after_cue, n_after_nat


def _bar(counts, total):
    lines = []
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        pct = 100 * v / total if total else 0
        lines.append(f'    {k:<28} {v:>5}  ({pct:4.1f}%)')
    return '\n'.join(lines)


def run(n=2000, verbose=False):
    sep = '─' * 62
    print(sep)
    print(f' שיעור 14 — נגטיב דאבל (בדיקה מקיפה)  |  {n} ידיות')
    print(sep)

    errors, s_cats, s_bids, n_x, n_cue, n_nat = scale(n, verbose=verbose)
    total = sum(s_cats.values())

    print(f'  ידיות שהורצו: {total}')
    print()
    print('  התפלגות קטגוריות S (s_response):')
    print(_bar(s_cats, total))
    print()
    print('  התפלגות הכרזות S:')
    print(_bar(s_bids, total))

    if n_x:
        print()
        print(f'  ריבאד N אחרי X (after_X / phase2):')
        print(_bar(n_x, sum(n_x.values())))

    if n_cue:
        print()
        print(f'  ריבאד N אחרי קיו ביט ({sum(n_cue.values())} ידיות):')
        print(_bar(n_cue, sum(n_cue.values())))

    if n_nat:
        print()
        print(f'  ריבאד N אחרי הכרזה טבעית ({sum(n_nat.values())} ידיות):')
        print(_bar(n_nat, sum(n_nat.values())))

    print()
    if errors:
        print(f'  ✗ שגיאות: {len(errors)}')
        for e in errors[:30]:
            print(f'    • {e}')
        if len(errors) > 30:
            print(f'    ... ועוד {len(errors) - 30}')
    else:
        print('  ✓ אין שגיאות')
    print(sep)


if __name__ == '__main__':
    args    = sys.argv[1:]
    n       = int(args[0]) if args and args[0].lstrip('-').isdigit() else 2000
    verbose = '-v' in args
    run(n, verbose=verbose)
