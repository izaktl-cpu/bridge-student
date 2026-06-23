"""
סקייל שיעור 4 — סטיימן אחרי 1NT.
N: 15-17 HCP מאוזן. S: 8-14 HCP, 2 רביעיות, מיגור אחד בדיוק 4 (לא 5+).
S מכריז 2♣, N עונה, S מסיים.
"""
import sys, os
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_robot_opens_1nt_stayman
from engine.scoring import hcp, is_balanced, distribution
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


def _north_stayman_reply(n, d_n):
    if d_n['H'] >= 4: return '2♥'
    if d_n['S'] >= 4: return '2♠'
    return '2♦'


def _calc_cont(hs, has_fit):
    if has_fit:
        return '4M' if hs >= 10 else '3M'
    return '3NT' if hs >= 10 else '2NT'


def _check(hands, idx, errors):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    d_n, d_s = distribution(n), distribution(s)

    if not (15 <= hn <= 17):
        errors.append(f'#{idx}: N HCP={hn} מחוץ לטווח 15-17')
    if not is_balanced(n):
        errors.append(f'#{idx}: N לא מאוזן')
    if not (8 <= hs <= 14):
        errors.append(f'#{idx}: S HCP={hs} מחוץ לטווח 8-14')
    if d_s['H'] >= 5 or d_s['S'] >= 5:
        errors.append(f'#{idx}: S יש 5+ קלפי מיגור (צ"ל 4 בדיוק)')
    if not (d_s['H'] == 4 or d_s['S'] == 4):
        errors.append(f'#{idx}: S אין 4 קלפי מיגור')

    reply = _north_stayman_reply(n, d_n)
    has_fit = (reply == '2♥' and d_s['H'] >= 4) or (reply == '2♠' and d_s['S'] >= 4)
    cont = _calc_cont(hs, has_fit)
    return reply, cont


def run(n=2000):
    errors, replies, conts = [], Counter(), Counter()
    for i in range(n):
        try:
            hands = deal_robot_opens_1nt_stayman()
            r, c = _check(hands, i, errors)
            replies[r] += 1
            conts[c] += 1
        except Exception as e:
            errors.append(f'#{i}: {e}')

    sep = '─' * 50
    print(sep)
    print(f' שיעור 4 — סטיימן  |  {n} ידיות')
    print(sep)
    total = sum(replies.values())
    print('  תגובות N לסטיימן:')
    for k, v in sorted(replies.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/total:4.1f}%)')
    print('  המשך S:')
    for k, v in sorted(conts.items(), key=lambda x: -x[1]):
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
