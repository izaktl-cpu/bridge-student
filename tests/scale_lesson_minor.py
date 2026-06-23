"""
סקייל שיעור מינור — תלמיד (S) פותח מינור, מחשב (N) עונה.
S: 12-19 HCP, 3-6 קלפי מינור. N: 6-12 HCP.
S פותח 1♣/1♦ (או 1NT עם 15-17 מאוזן), N עונה, S עושה ריבאד.
"""
import sys, os, random
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_student_opens_minor
from engine.response import respond_minor
from engine.rebid import opener_rebid
from engine.scoring import hcp, suit_len, is_balanced
from engine.cards import SUIT_SYMBOLS
from engine.opening import opening_bid as _opening_bid

_S = SUIT_SYMBOLS


def _check(hands, minor, idx, errors):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    sym = _S[minor]

    # בדיקות בסיסיות
    if not (12 <= hs <= 19):
        errors.append(f'#{idx} ({sym}): S HCP={hs} מחוץ לטווח 12-19')
    if not (6 <= hn <= 12):
        errors.append(f'#{idx} ({sym}): N HCP={hn} מחוץ לטווח 6-12')

    # הכרזת S
    open_bid, _ = _opening_bid(s)
    expected_minor = f'1{sym}'
    if open_bid == '1NT':
        # 15-17 מאוזן — תקין
        pass
    elif open_bid != expected_minor and open_bid not in ('1♣', '1♦'):
        errors.append(f'#{idx}: S פתח {open_bid} במקום מינור')

    if open_bid == '1NT':
        # אין ריבאד — חוזה ישיר
        return open_bid, 'חוזה ישיר', 'N/A'

    # תגובת N
    minor_key = 'C' if '♣' in open_bid else 'D'
    n_bid, _ = respond_minor(n, minor_key)

    # ריבאד S
    rebid, _ = opener_rebid(s, open_bid, n_bid)

    return open_bid, n_bid, rebid


def run(n=2000):
    errors   = []
    opens    = Counter()
    n_bids   = Counter()
    rebids   = Counter()
    minors   = Counter()

    for i in range(n):
        minor = random.choice(['C', 'D'])
        try:
            hands = deal_student_opens_minor(minor)
            ob, nb, rb = _check(hands, minor, i, errors)
            opens[ob]  += 1
            n_bids[nb] += 1
            rebids[rb] += 1
            minors[_S[minor]] += 1
        except Exception as e:
            errors.append(f'#{i}: {e}')

    sep   = '─' * 52
    total = sum(opens.values())
    print(sep)
    print(f' שיעור מינור — תלמיד פותח מינור  |  {n} ידיות')
    print(sep)
    print(f'  ♣={minors["♣"]}  ♦={minors["♦"]}')
    print('  פתיחות S:')
    for k, v in sorted(opens.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/total:4.1f}%)')
    print('  תגובות N:')
    for k, v in sorted(n_bids.items(), key=lambda x: -x[1])[:8]:
        print(f'    {k:<6} {v:>5}  ({100*v/total:4.1f}%)')
    print('  ריבאד S:')
    for k, v in sorted(rebids.items(), key=lambda x: -x[1])[:8]:
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
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    run(n)
