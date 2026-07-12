"""
סקייל שיעור 4 — סטיימן אחרי 1NT.
N: 15-17 HCP מאוזן.
S — שני סוגים:
  ~75% יד סטיימן: 0-14 HCP, מיגור בדיוק 4 (לא 5+), 2+ רביעיות. 8+ → 2♣, אחרת פס.
  ~25% יד NT:     8-14 HCP מאוזן, בלי מיגור רביעייה. 8-9 → 2NT, 10+ → 3NT.
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
    """מאמת יד ומחזיר (הכרזה_ראשונה, תגובת_N_או_None, המשך_S_או_None)."""
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    d_n, d_s = distribution(n), distribution(s)

    if not (15 <= hn <= 17):
        errors.append(f'#{idx}: N HCP={hn} מחוץ לטווח 15-17')
    if not is_balanced(n):
        errors.append(f'#{idx}: N לא מאוזן')
    if d_s['H'] >= 5 or d_s['S'] >= 5:
        errors.append(f'#{idx}: S יש 5+ קלפי מיגור עיקרי')
        return None, None, None

    has_major_4 = d_s['H'] == 4 or d_s['S'] == 4
    four_count = sum([d_s['S'] == 4, d_s['H'] == 4, d_s['D'] >= 4, d_s['C'] >= 4])

    if has_major_4:
        # יד סטיימן: 0-14, 2+ רביעיות. 8+ → 2♣, אחרת פס
        if not (0 <= hs <= 14):
            errors.append(f'#{idx}: S סטיימן HCP={hs} מחוץ ל-0-14')
        if four_count < 2:
            errors.append(f'#{idx}: S סטיימן פחות מ-2 רביעיות')
        if hs < 8:
            return 'פס', None, None
        reply = _north_stayman_reply(n, d_n)
        has_fit = (reply == '2♥' and d_s['H'] >= 4) or (reply == '2♠' and d_s['S'] >= 4)
        return '2♣', reply, _calc_cont(hs, has_fit)

    # יד NT: מאוזן 8-14 בלי מיגור רביעייה. 10+ → 3NT, אחרת 2NT
    if not (8 <= hs <= 14):
        errors.append(f'#{idx}: S יד-NT HCP={hs} מחוץ ל-8-14')
    if not is_balanced(s):
        errors.append(f'#{idx}: S יד-NT לא מאוזן')
    return ('3NT' if hs >= 10 else '2NT'), None, None


def run(n=2000):
    errors = []
    firsts, replies, conts = Counter(), Counter(), Counter()
    for i in range(n):
        try:
            hands = deal_robot_opens_1nt_stayman()
            f, r, c = _check(hands, i, errors)
            if f: firsts[f] += 1
            if r: replies[r] += 1
            if c: conts[c] += 1
        except Exception as e:
            errors.append(f'#{i}: {e}')

    sep = '─' * 50
    print(sep)
    print(f' שיעור 4 — סטיימן  |  {n} ידיות')
    print(sep)
    total = sum(firsts.values()) or 1
    print('  הכרזה ראשונה של S:')
    for k, v in sorted(firsts.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/total:4.1f}%)')
    if replies:
        rt = sum(replies.values())
        print('  תגובות N לסטיימן:')
        for k, v in sorted(replies.items(), key=lambda x: -x[1]):
            print(f'    {k:<6} {v:>5}  ({100*v/rt:4.1f}%)')
        print('  המשך S אחרי סטיימן:')
        for k, v in sorted(conts.items(), key=lambda x: -x[1]):
            print(f'    {k:<6} {v:>5}  ({100*v/rt:4.1f}%)')
    print()
    if errors:
        print(f'  ✗ שגיאות: {len(errors)}')
        for e in errors[:10]: print(f'    • {e}')
    else:
        print('  ✓ אין שגיאות')
    print(sep)
    return len(errors)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    run(n)
