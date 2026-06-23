"""
סקייל בדיקה לשיעור 12 — אוברקול.
מריץ N ידיות ובודק עקביות בשני שלבים:
  שלב 1: הכרזת האוברקול של S
  שלב 2: ריבאד של S אחרי תגובת N

שימוש:
    python tests/scale_overcall.py          # ברירת מחדל: 2000 ידיות
    python tests/scale_overcall.py 500      # 500 ידיות
    python tests/scale_overcall.py 2000 -v  # מפורט (3 ידיות ראשונות)
"""

import sys, os, random
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_overcall
from engine.overcall import get_overcall, respond_overcall, _suit_quality
from engine.opening import opening_bid as _opening_bid
from engine.response import get_response
from engine.scoring import hcp, distribution, dist_fit_pts
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS
_SYM_TO_SUIT = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}
_BID_RANK = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}


# ─── עזר ────────────────────────────────────────────────────────────────────

def _bid_value(bid):
    if bid in ('Pass', 'X', 'XX'):
        return 0
    lvl = int(bid[0]) if bid[0].isdigit() else 0
    if 'NT' in bid:
        return lvl * 10 + 5
    return lvl * 10 + _BID_RANK.get(bid[1], 0)


def _is_game(bid):
    if bid in ('3NT', '4NT'):
        return True
    if len(bid) == 2 and bid[0] == '4' and bid[1] in ('♠', '♥'):
        return True
    if len(bid) == 2 and bid[0] == '5' and bid[1] in ('♣', '♦'):
        return True
    return False


def _s_rebid_correct(s_hand, s_bid1, n_last_bid):
    """מסונכרן עם lesson_overcall.py — הכרזה נכונה לS בשלב 2. ללא נק' חלוקה."""
    h = hcp(s_hand)
    d = distribution(s_hand)
    s_sym  = s_bid1[1] if len(s_bid1) == 2 else ''
    s_suit = _SYM_TO_SUIT.get(s_sym, '')
    s_lvl  = int(s_bid1[0]) if s_bid1[0].isdigit() else 1

    if n_last_bid == 'Pass':
        return 'Pass', 'שותף פס'

    n_sym  = n_last_bid[1] if len(n_last_bid) == 2 and 'N' not in n_last_bid else ''
    n_suit = _SYM_TO_SUIT.get(n_sym, '')
    n_lvl  = int(n_last_bid[0]) if n_last_bid[0].isdigit() else 0

    if n_sym == s_sym:
        diff = n_lvl - s_lvl
        if diff == 1:
            # N מינימום (7-10 נק') — בכל רמה
            if h >= 16:
                if s_suit in ('S', 'H'):
                    return f'3{s_sym}', 'ניסיון משחק'
            return 'Pass', 'מינימום'
        # N הזמין (diff>=2) — N=11-12 נק'
        if h >= 14:
            if s_suit in ('S', 'H'):
                return f'4{s_sym}', 'משחק'
            return '3NT', 'משחק NT'  # סקייל לא בודק עוצרים
        return 'Pass', 'לא מספיק'

    if n_sym and n_sym != s_sym:
        if d.get(n_suit, 0) >= 3:
            return f'{n_lvl + 1}{n_sym}', 'תמיכה'
        if h >= 13:
            return f'{s_lvl + 1}{s_sym}', 'חוזר לצבע'
        return 'Pass', 'פס'

    return 'Pass', 'פס'


# ─── בדיקה אחת ──────────────────────────────────────────────────────────────

def _check_one(hands, idx, errors):
    """
    מריץ יד אחת:
    שלב 1 → אוברקול
    שלב 2 → ריבאד S (אם הכרזה ולא פס)
    מחזיר dict עם נתוני הסטטיסטיקה.
    """
    e = hands['E']
    s = hands['S']
    n = hands['N']
    w = hands['W']

    he = hcp(e)
    hs = hcp(s)

    # ─ בדיקת תקינות E ──────────────────────────────────────────────────────
    if not (12 <= he <= 19):
        errors.append(f'#{idx}: E HCP={he} מחוץ לטווח 12-19')

    e_bid, _ = _opening_bid(e)
    if not (len(e_bid) == 2 and e_bid[0] == '1'):
        errors.append(f'#{idx}: E לא פתח 1-בצבע (פתח {e_bid})')
        return {'s_bid': '?', 'n_bid': '?', 's_rebid': '?'}

    # ─ שלב 1: אוברקול ──────────────────────────────────────────────────────
    s_bid, s_expl = get_overcall(s, e_bid)
    is_suit_oc = len(s_bid) == 2 and s_bid[0].isdigit()

    # עקביות: אוברקול בצבע → חייב 5+ קלפים + 2 מכובדים
    if is_suit_oc:
        oc_suit = _SYM_TO_SUIT.get(s_bid[1], '')
        d_s = distribution(s)
        length = d_s.get(oc_suit, 0)
        quality = _suit_quality(s, oc_suit)
        if length < 5:
            errors.append(
                f'#{idx}: S הכריז {s_bid} אבל יש לו רק {length} קלפי {s_bid[1]}')
        if quality < 2:
            errors.append(
                f'#{idx}: S הכריז {s_bid} אבל איכות צבע = {quality} (צ"ל 2+)')
        if hs < 8:
            errors.append(
                f'#{idx}: S הכריז {s_bid} עם {hs} נק׳ בלבד (מינ׳ 8)')
        if hs > 16:
            errors.append(
                f'#{idx}: S הכריז {s_bid} עם {hs} נק׳ (מקס׳ 16 לאוברקול פשוט)')

        # N חייב לפחות 3 קלפי תמיכה (כך מוגדר deal_overcall)
        n_support = distribution(n).get(oc_suit, 0)
        if n_support < 3:
            errors.append(
                f'#{idx}: N יש לו {n_support} קלפי {s_bid[1]} (צ"ל 3+)')

    # פס: עקביות — אם פס, HCP < 8 או אין צבע מתאים
    # ידיות 20+ HCP: ה-engine אינו מגדיר אוברקול חזק — פס לגיטימי בשיעור זה

    # ─ שלב 2: תגובת N + ריבאד S ────────────────────────────────────────────
    n_bid = 'N/A'
    s_rebid = 'N/A'

    if is_suit_oc:
        # W מגיב לE, N מגיב לS
        w_bid, _ = get_response(w, e_bid)
        n_bid, _ = respond_overcall(n, s_bid, e_bid)

        # עקביות הכרזת N
        if n_bid != 'Pass':
            if _bid_value(n_bid) <= _bid_value(s_bid):
                errors.append(
                    f'#{idx}: N הכריז {n_bid} אבל S הכריז {s_bid} — רמה לא חוקית')

        # S מכריז שוב רק אם N לא פס ולא game
        if n_bid != 'Pass' and not _is_game(n_bid):
            s_rebid, _ = _s_rebid_correct(s, s_bid, n_bid)

            # עקביות ריבאד: game עם מינמום HCP
            if _is_game(s_rebid) and hs < 12:
                errors.append(
                    f'#{idx}: S ריבאד {s_rebid} עם {hs} נק׳ — חלש מדי למשחק')
            # Pass עם יד חזקה (17+ בלתי אפשרי לאוברקול פשוט → רק bug אמיתי)
            if s_rebid == 'Pass' and hs >= 17:
                errors.append(
                    f'#{idx}: S ריבאד Pass עם {hs} נק׳ (N הכריז {n_bid}) — חשוד')

    return {'s_bid': s_bid, 'n_bid': n_bid, 's_rebid': s_rebid}


# ─── הרצה ראשית ─────────────────────────────────────────────────────────────

def scale_overcall(n=2000, verbose=False):
    errors = []
    s_bid_counts   = Counter()
    n_bid_types    = Counter()
    s_rebid_counts = Counter()
    pass_count = 0

    for i in range(n):
        try:
            hands = deal_overcall()
            result = _check_one(hands, i, errors)

            s_bid = result['s_bid']
            n_bid = result['n_bid']
            s_rebid = result['s_rebid']

            # סיווג הכרזת S
            if s_bid == 'Pass':
                s_bid_counts['Pass'] += 1
                pass_count += 1
            elif s_bid == 'X':
                s_bid_counts['X (טייקאאוט)'] += 1
            elif s_bid == '1NT':
                s_bid_counts['1NT'] += 1
            elif s_bid[0] == '1':
                s_bid_counts['1-בצבע'] += 1
            elif s_bid[0] == '2':
                s_bid_counts['2-בצבע'] += 1
            else:
                s_bid_counts[s_bid] += 1

            # סיווג תגובת N
            if n_bid == 'N/A':
                n_bid_types['N/A (S פס)'] += 1
            elif n_bid == 'Pass':
                n_bid_types['Pass'] += 1
            elif 'NT' in n_bid:
                n_bid_types['NT'] += 1
            elif n_bid[0] in '34' and n_bid[1] in ('♠', '♥', '♣', '♦'):
                n_bid_types[f'תמיכה {n_bid}'] += 1
            else:
                n_bid_types['תמיכה/צבע חדש'] += 1

            # סיווג ריבאד S
            if s_rebid == 'N/A':
                s_rebid_counts['N/A'] += 1
            elif _is_game(s_rebid):
                s_rebid_counts['משחק'] += 1
            elif s_rebid == 'Pass':
                s_rebid_counts['Pass'] += 1
            else:
                s_rebid_counts['תחרות'] += 1

            if verbose and i < 3:
                e_bid, _ = _opening_bid(hands['E'])
                he = hcp(hands['E'])
                hs = hcp(hands['S'])
                hn = hcp(hands['N'])
                print(f'  #{i}: E={he}נק׳ פתח {e_bid} | '
                      f'S={hs}נק׳ → {s_bid} | '
                      f'N={hn}נק׳ → {n_bid} | '
                      f'S ריבאד → {s_rebid}')

        except Exception as e:
            errors.append(f'#{i}: חריגה — {e}')

    return errors, s_bid_counts, n_bid_types, s_rebid_counts


def _bar(counts, total):
    lines = []
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        pct = 100 * v / total if total else 0
        lines.append(f'    {k:<25} {v:>5}  ({pct:4.1f}%)')
    return '\n'.join(lines)


def run(n=2000, verbose=False):
    sep = '─' * 60
    print(sep)
    print(f' שיעור 12 — אוברקול  |  {n} ידיות')
    print(sep)

    errors, s_bids, n_bids, s_rebids = scale_overcall(n, verbose=verbose)
    total = sum(s_bids.values())

    print(f'  ידיות שהורצו: {total}')
    print()
    print('  שלב 1 — הכרזת S (אוברקול):')
    print(_bar(s_bids, total))

    n_oc = total - s_bids.get('Pass', 0)
    if n_oc:
        print()
        print(f'  שלב 1b — תגובת N (מתוך {n_oc} ידיות עם אוברקול):')
        n_bids_filtered = {k: v for k, v in n_bids.items() if k != 'N/A (S פס)'}
        print(_bar(n_bids_filtered, n_oc))

        n_rebid = sum(v for k, v in s_rebids.items()
                      if k not in ('N/A', 'Pass') or k == 'Pass')
        rebid_total = sum(v for k, v in s_rebids.items() if k != 'N/A')
        if rebid_total:
            print()
            print(f'  שלב 2 — ריבאד S (מתוך {rebid_total} ידיות שהגיעו לשלב זה):')
            print(_bar({k: v for k, v in s_rebids.items() if k != 'N/A'}, rebid_total))

    print()
    if errors:
        print(f'  ✗ שגיאות: {len(errors)}')
        for e in errors[:20]:
            print(f'    • {e}')
        if len(errors) > 20:
            print(f'    ... ועוד {len(errors) - 20}')
    else:
        print('  ✓ אין שגיאות')
    print(sep)


if __name__ == '__main__':
    args = sys.argv[1:]
    n       = int(args[0]) if args and args[0].lstrip('-').isdigit() else 2000
    verbose = '-v' in args
    run(n, verbose=verbose)
