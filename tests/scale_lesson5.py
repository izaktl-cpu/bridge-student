"""
סקייל שיעור 5 — טרנספר אחרי 1NT.
N: 15-17 HCP מאוזן, לפחות J בכל סדרה.
S — שני סוגים:
  ~75% יד טרנספר: 0-14 HCP, 5+ קלפי מיגור עיקרי → 2♦/2♥.
  ~25% יד NT:     0-14 HCP מאוזן, בלי מיגור חמישייה. 0-7 → פס, 8-9 → 2NT, 10+ → 3NT.

כללי ההכרזה:
  S אחרי השלמת הטרנספר:
    0-7  נק' → Pass
    8-9  נק', 5 קל' → 2NT
    8-9  נק', 6+ קל' → 3M
    10+  נק', 5 קל' → 3NT
    10+  נק', 6+ קל' → 4M

  N אחרי 2NT (S=8-9, 5 קל'):
    15-16 נק'          → Pass  (חוזה 2NT)
    17    נק', 3+ קל'  → 4M
    17    נק', 2  קל'  → 3NT

  N אחרי 3M (S=8-9, 6+ קל'):
    15-16 נק'          → Pass  (חוזה 3M)
    17    נק', 2  קל'  → Pass  (חוזה 3M)
    17    נק', 3+ קל'  → 4M

  N אחרי 3NT (S=10+, 5 קל'):
    3+ קל' בסדרה       → 4M
    2  קל' בסדרה       → Pass  (חוזה 3NT)

  N אחרי 4M / Pass: Pass תמיד
"""
import sys, os
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_robot_opens_1nt_transfer
from engine.scoring import hcp, distribution, is_balanced

_SUITS = {'H': '♥', 'S': '♠'}


def _s_transfer(d_s):
    if d_s['H'] >= 5: return '2♦', 'H'
    if d_s['S'] >= 5: return '2♥', 'S'
    return None, None


def _s_cont(hs, suit_len, sym):
    if hs <= 7:
        return 'Pass'
    if hs <= 9:
        return '2NT' if suit_len == 5 else f'3{sym}'
    return '3NT' if suit_len == 5 else f'4{sym}'


def _n_response(s_cont, hn, north_fit, sym):
    if s_cont == 'Pass':
        return 'Pass'
    if s_cont == '2NT':
        if hn <= 16: return 'Pass'
        return f'4{sym}' if north_fit >= 3 else '3NT'
    if s_cont == f'3{sym}':
        if hn <= 16 or north_fit < 3: return 'Pass'
        return f'4{sym}'
    if s_cont == '3NT':
        return f'4{sym}' if north_fit >= 3 else 'Pass'
    return 'Pass'  # 4M או Pass


def _final_contract(s_cont, n_resp, sym):
    if n_resp != 'Pass':
        return n_resp
    if s_cont == 'Pass':
        return f'2{sym}'
    return s_cont


def _check(hands, idx, errors):
    """מחזיר (הכרזה_ראשונה, המשך_S_או_None, תגובת_N_או_None, חוזה_או_None, sym)."""
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    d_n, d_s = distribution(n), distribution(s)

    if not (15 <= hn <= 17):
        errors.append(f'#{idx}: N HCP={hn} מחוץ לטווח 15-17')
    if not is_balanced(n):
        errors.append(f'#{idx}: N לא מאוזן')

    t_bid, suit_key = _s_transfer(d_s)
    if t_bid is None:
        # יד NT: מאוזן 0-14 בלי מיגור חמישייה → פס/2NT/3NT
        if not (0 <= hs <= 14):
            errors.append(f'#{idx}: S יד-NT HCP={hs} מחוץ ל-0-14')
        if not is_balanced(s):
            errors.append(f'#{idx}: S יד-NT לא מאוזן')
        first = 'פס' if hs <= 7 else ('2NT' if hs <= 9 else '3NT')
        return first, None, None, None, None

    suit_len = d_s[suit_key]
    north_fit = d_n[suit_key]
    sym = _SUITS[suit_key]

    s_cont = _s_cont(hs, suit_len, sym)
    n_resp = _n_response(s_cont, hn, north_fit, sym)
    final  = _final_contract(s_cont, n_resp, sym)

    return t_bid, s_cont, n_resp, final, sym


def run(n=3000):
    errors   = []
    firsts   = Counter()
    s_conts  = Counter()
    n_resps  = Counter()
    finals   = Counter()
    by_scont = defaultdict(Counter)

    for i in range(n):
        try:
            hands = deal_robot_opens_1nt_transfer()
            first, s_cont, n_resp, final, sym = _check(hands, i, errors)
            if first:
                firsts[first] += 1
            if s_cont is not None:
                s_conts[s_cont] += 1
                n_resps[n_resp] += 1
                finals[final]   += 1
                by_scont[s_cont][n_resp] += 1
        except Exception as e:
            errors.append(f'#{i}: {e}')

    sep   = '─' * 55
    total = sum(s_conts.values()) or 1
    ftot  = sum(firsts.values()) or 1
    print(sep)
    print(f' שיעור 5 — טרנספר  |  {n} ידיות')
    print(sep)

    print('  הכרזה ראשונה של S:')
    for k, v in sorted(firsts.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/ftot:4.1f}%)')

    print()
    print('  המשך S (אחרי טרנספר):')
    for k, v in sorted(s_conts.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/total:4.1f}%)')

    print()
    print('  תגובת N לפי הכרזת S:')
    for sc in sorted(by_scont):
        sub       = by_scont[sc]
        sub_total = sum(sub.values())
        print(f'    S={sc}:')
        for nr, cnt in sorted(sub.items(), key=lambda x: -x[1]):
            print(f'      N={nr:<6} {cnt:>5}  ({100*cnt/sub_total:4.1f}%)')

    print()
    print('  חוזות סופיים:')
    for k, v in sorted(finals.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/total:4.1f}%)')

    print()
    if errors:
        print(f'  ✗ שגיאות: {len(errors)}')
        for e in errors[:10]:
            print(f'    • {e}')
    else:
        print('  ✓ אין שגיאות')
    print(sep)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    run(n)
