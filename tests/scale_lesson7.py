"""
סקייל שיעור 7 — מחשב (N) פותח 2♣ חזקה, תלמיד (S) עונה.
N: 23+ HCP כל חלוקה, או 18-22 HCP עם 9+ לקיחות.
S: 4-10 HCP (ממוקד). 2♦ = ממתין (0-6), תגובות חיוביות (7+).
"""
import sys, os
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_robot_opens_2c
from engine.response import respond_2c, respond_2c_second
from engine.rebid import opener_rebid
from engine.scoring import hcp, is_balanced, distribution, sure_tricks


def _check(hands, idx, errors):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    d_s = distribution(s)
    st_n = sure_tricks(n)

    # אימות תנאי הדילוג
    if not (hn >= 23 or (hn >= 18 and st_n >= 9)):
        errors.append(f'#{idx}: N HCP={hn} sure={st_n} לא עומד בתנאי פתיחת 2♣')
    if not (4 <= hs <= 10):
        errors.append(f'#{idx}: S HCP={hs} מחוץ לטווח 4-10')

    # הכרזה ראשונה של S
    s1, _ = respond_2c(s)

    # אימות עקביות
    if hs <= 6 and s1 != '2♦':
        errors.append(f'#{idx}: S HCP={hs} צ"ל 2♦ (ממתין) אבל הכריז {s1}')
    if hs >= 8 and s1 == '2♦':
        # 2♦ ממתין עם 8+ HCP — שגוי רק אם יש 5+ מיגור או מאוזן
        has_5major = d_s['H'] >= 5 or d_s['S'] >= 5
        bal = is_balanced(s)
        if has_5major:
            errors.append(f'#{idx}: S HCP={hs} עם 5+ מיגור צ"ל תגובה חיובית אבל הכריז 2♦')
        elif bal:
            errors.append(f'#{idx}: S HCP={hs} מאוזן צ"ל 2NT אבל הכריז 2♦')

    # הכרזה שנייה של N (ריבאד)
    n2, _ = opener_rebid(n, '2♣', s1)

    # הכרזה שנייה של S (אם N2 לא סופי)
    _FINAL = {'3NT', '4♥', '4♠', '5♣', '5♦', '6NT', '6♥', '6♠'}
    if n2 not in _FINAL:
        s2, _ = respond_2c_second(s, n2)
    else:
        s2 = None

    return s1, n2, s2


def run(n=2000):
    errors = []
    s1_ctr, n2_ctr, s2_ctr = Counter(), Counter(), Counter()

    for i in range(n):
        try:
            hands = deal_robot_opens_2c()
            s1, n2, s2 = _check(hands, i, errors)
            s1_ctr[s1] += 1
            n2_ctr[n2] += 1
            if s2:
                s2_ctr[s2] += 1
        except Exception as e:
            errors.append(f'#{i}: {e}')

    sep = '─' * 50
    print(sep)
    print(f' שיעור 7 — 2♣ חזקה  |  {n} ידיות')
    print(sep)
    total = sum(s1_ctr.values())
    print('  תגובה ראשונה S:')
    for k, v in sorted(s1_ctr.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/total:4.1f}%)')
    print('  ריבאד N:')
    for k, v in sorted(n2_ctr.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/total:4.1f}%)')
    if s2_ctr:
        print('  תגובה שנייה S:')
        for k, v in sorted(s2_ctr.items(), key=lambda x: -x[1]):
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
