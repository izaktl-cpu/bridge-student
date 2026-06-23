"""
סקייל שיעור 1 — מחשב (N) פותח 1NT, תלמיד (S) עונה.
N: 15-17 HCP מאוזן. S: 0-15 HCP, ללא 4+ מיגור עיקרי.
תגובה: Pass (0-7) / 2NT (8-9) / 3NT (10+).
"""
import sys, os, random
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_robot_opens_1nt
from engine.response import respond_1nt
from engine.scoring import hcp, is_balanced, distribution


def _check(hands, idx, errors):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)

    if not (15 <= hn <= 17):
        errors.append(f'#{idx}: N HCP={hn} מחוץ לטווח 15-17')
    if not is_balanced(n):
        errors.append(f'#{idx}: N לא מאוזן')
    if not (0 <= hs <= 15):
        errors.append(f'#{idx}: S HCP={hs} מחוץ לטווח 0-15')
    d = distribution(s)
    if d['H'] >= 4 or d['S'] >= 4:
        errors.append(f'#{idx}: S יש 4+ קלפי מיגור (צ"ל ללא)')

    bid, _ = respond_1nt(s)
    if bid == 'Pass'  and hs > 7:
        errors.append(f'#{idx}: פס עם {hs} נקודות')
    if bid == '2NT'   and not (8 <= hs <= 9):
        errors.append(f'#{idx}: 2NT עם {hs} נקודות (צ"ל 8-9)')
    if bid == '3NT'   and hs < 10:
        errors.append(f'#{idx}: 3NT עם {hs} נקודות (צ"ל 10+)')
    return bid


def run(n=2000):
    errors, bids = [], Counter()
    for i in range(n):
        try:
            hands = deal_robot_opens_1nt()
            bids[_check(hands, i, errors)] += 1
        except Exception as e:
            errors.append(f'#{i}: {e}')

    sep = '─' * 50
    print(sep)
    print(f' שיעור 1 — 1NT  |  {n} ידיות')
    print(sep)
    total = sum(bids.values())
    for k, v in sorted(bids.items(), key=lambda x: -x[1]):
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
