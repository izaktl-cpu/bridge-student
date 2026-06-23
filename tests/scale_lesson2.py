"""
סקייל שיעור 2 — מחשב (N) פותח מיגור עיקרי, תלמיד (S) עונה.
N: 12-19 HCP, 5+ קלפי מיגור. S: 3+ תמיכה.
תגובה: 2M (6-9) / 3M (10-11) / 4M (12+) / חוק 19.
"""
import sys, os, random
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_robot_opens_major
from engine.response import respond_major
from engine.scoring import hcp, suit_len, distribution, dist_fit_pts
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


def _check(hands, major, idx, errors):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    sym = _S[major]

    if not (12 <= hn <= 19):
        errors.append(f'#{idx} ({sym}): N HCP={hn} מחוץ לטווח 12-19')
    if suit_len(n, major) < 5:
        errors.append(f'#{idx} ({sym}): N יש {suit_len(n,major)} קלפי {sym} (מינ׳ 5)')
    if suit_len(s, major) < 3:
        errors.append(f'#{idx} ({sym}): S יש {suit_len(s,major)} קלפי {sym} (מינ׳ 3)')

    bid, _ = respond_major(s, major)
    fit = suit_len(s, major)
    dp  = dist_fit_pts(s, trump=major) if fit >= 3 else 0
    tot = hs + dp

    if bid == f'2{sym}':
        if fit < 3:
            errors.append(f'#{idx}: 2{sym} ללא תמיכה')
        if tot < 6 or tot > 9:
            errors.append(f'#{idx}: 2{sym} עם {tot} נקודות (צ"ל 6-9)')
    elif bid == f'3{sym}':
        if fit < 3:
            errors.append(f'#{idx}: 3{sym} ללא תמיכה')
        if tot < 10 or tot > 12:
            errors.append(f'#{idx}: 3{sym} עם {tot} נקודות (צ"ל 10-12)')
    elif bid == f'4{sym}':
        if fit >= 5 and hs >= 7:
            pass  # חוק 19
        elif fit >= 3 and tot < 13:
            errors.append(f'#{idx}: 4{sym} עם {tot} נקודות (צ"ל 13+)')
    return bid


def run(n=2000):
    errors, bids, majors = [], Counter(), Counter()
    for i in range(n):
        major = random.choice(['H', 'S'])
        try:
            hands = deal_robot_opens_major(major, support_scenario=True)
            bids[_check(hands, major, i, errors)] += 1
            majors[_S[major]] += 1
        except Exception as e:
            errors.append(f'#{i}: {e}')

    sep = '─' * 50
    print(sep)
    print(f' שיעור 2 — מחשב פותח מיגור  |  {n} ידיות')
    print(sep)
    total = sum(bids.values())
    print(f'  ♥={majors["♥"]}  ♠={majors["♠"]}')
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
