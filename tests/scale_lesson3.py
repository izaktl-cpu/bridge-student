"""
סקייל שיעור 3 — תלמיד (S) פותח מיגור עיקרי, מחשב (N) עונה.
S: 12-19 HCP, 5+ קלפי מיגור. N: 6-12 HCP, 3+ תמיכה.
S פותח 1M, N עונה respond_major, S עושה rebid.
"""
import sys, os, random
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_student_opens_major
from engine.response import respond_major
from engine.rebid import opener_rebid
from engine.scoring import hcp, suit_len, dist_fit_pts
from engine.cards import SUIT_SYMBOLS
from engine.opening import opening_bid as _opening_bid

_S = SUIT_SYMBOLS


def _check(hands, major, idx, errors):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    sym = _S[major]

    if not (12 <= hs <= 19):
        errors.append(f'#{idx} ({sym}): S HCP={hs} מחוץ לטווח 12-19')
    if suit_len(s, major) < 5:
        errors.append(f'#{idx} ({sym}): S יש {suit_len(s,major)} קלפי {sym} (מינ׳ 5)')
    if not (6 <= hn <= 12):
        errors.append(f'#{idx} ({sym}): N HCP={hn} מחוץ לטווח 6-12')
    if suit_len(n, major) < 3:
        errors.append(f'#{idx} ({sym}): N יש {suit_len(n,major)} קלפי {sym} (מינ׳ 3)')

    open_bid, _ = _opening_bid(s)
    if open_bid != f'1{sym}':
        errors.append(f'#{idx}: S אמור לפתוח 1{sym} אבל opening_bid={open_bid}')

    n_bid, _ = respond_major(n, major)
    rebid, _ = opener_rebid(s, f'1{sym}', n_bid)
    return n_bid, rebid


def run(n=2000):
    errors, n_bids, rebids, majors = [], Counter(), Counter(), Counter()
    for i in range(n):
        major = random.choice(['H', 'S'])
        try:
            hands = deal_student_opens_major(major)
            nb, rb = _check(hands, major, i, errors)
            n_bids[nb] += 1
            rebids[rb] += 1
            majors[_S[major]] += 1
        except Exception as e:
            errors.append(f'#{i}: {e}')

    sep = '─' * 50
    print(sep)
    print(f' שיעור 3 — תלמיד פותח מיגור  |  {n} ידיות')
    print(sep)
    total = sum(n_bids.values())
    print(f'  ♥={majors["♥"]}  ♠={majors["♠"]}')
    print('  תגובות N:')
    for k, v in sorted(n_bids.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/total:4.1f}%)')
    print('  ריבאד S:')
    for k, v in sorted(rebids.items(), key=lambda x: -x[1])[:6]:
        print(f'    {k:<6} {v:>5}  ({100*v/total:4.1f}%)')
    print()
    if errors:
        print(f'  ✗ שגיאות: {len(errors)}')
        for e in errors[:10]: print(f'    • {e}')
    else:
        print('  ✓ אין שגיאות')
    print(sep)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    run(n)
