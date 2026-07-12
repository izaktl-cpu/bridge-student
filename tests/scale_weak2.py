"""
סקייל בדיקה לשיעור 10 — Weak Two.

שני מצבים:
  A — מחשב (N) פותח Weak Two, תלמיד (S) עונה  (deal_weak_two)
  B — תלמיד (S) פותח Weak Two, מחשב (N) עונה  (deal_student_weak2)

לכל מצב:
  1. self-play  — שני הצדדים מכריזים אוטומטית, מציג סטטיסטיקה
  2. validation — בודק עקביות הידיות וההכרזות, מדווח שגיאות

שימוש:
    python tests/scale_weak2.py          # 2000 לכל מצב
    python tests/scale_weak2.py 500
    python tests/scale_weak2.py 2000 A   # רק מצב A
    python tests/scale_weak2.py 2000 B   # רק מצב B
"""

import sys, os, random
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_weak_two, deal_student_weak2
from engine.scoring import hcp, sure_tricks, suit_len, has_stopper
from engine.opening import opening_bid as _opening_bid
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


# ─── לוגיקת תגובה (זהה לשני השיעורים) ──────────────────────────────────────

def _calc_response(hand, major):
    """מחזיר את ההכרזה הנכונה לתגובה על Weak Two."""
    sym         = _S[major]
    st          = sure_tricks(hand)
    fit         = suit_len(hand, major) >= 2
    other       = [x for x in ['S', 'H', 'D', 'C'] if x != major]
    stops       = all(has_stopper(hand, suit) for suit in other)

    if fit and st >= 5:
        return f'4{sym}'
    if fit and st == 4:
        return f'3{sym}'          # הזמנה
    if st >= 4 and stops and suit_len(hand, major) >= 1:
        return '3NT'
    return 'Pass'


def _validate_opener(hand, major, idx, errors, position=1, label='N'):
    """בדיקת תקינות יד הפותח (6-9 HCP, 6 קלפים, 2+ מכובדים, פותח 2M)."""
    sym    = _S[major]
    h      = hcp(hand)
    length = suit_len(hand, major)
    honors = sum(1 for c in hand if c[1] == major and c[0] in ('A', 'K', 'Q', 'J'))
    bid, _ = _opening_bid(hand, position=position)

    if not (6 <= h <= 9):
        errors.append(f'#{idx}: {label} HCP={h} מחוץ לטווח 6-9')
    if length != 6:
        errors.append(f'#{idx}: {label} יש לו {length} קלפי {sym} (צ"ל 6)')
    if honors < 2:
        errors.append(f'#{idx}: {label} יש לו {honors} מכובדים בלבד בצבע {sym} (מינ׳ 2)')
    if bid != f'2{sym}':
        errors.append(f'#{idx}: {label} אמור לפתוח 2{sym} אבל opening_bid החזיר {bid}')


def _validate_response(resp_hand, major, response, idx, errors, label='S'):
    """בדיקת עקביות בין יד המגיב לתגובה שחושבה."""
    sym         = _S[major]
    st          = sure_tricks(resp_hand)
    fit         = suit_len(resp_hand, major) >= 2
    other       = [x for x in ['S', 'H', 'D', 'C'] if x != major]
    stops       = all(has_stopper(resp_hand, suit) for suit in other)

    if response == f'4{sym}':
        if st < 5:
            errors.append(f'#{idx}: {label} הכריז 4{sym} עם {st} לקיחות בלבד (מינ׳ 5)')
        if not fit:
            errors.append(f'#{idx}: {label} הכריז 4{sym} ללא 2+ קלפי {sym}')

    elif response == '3NT':
        if st < 4:
            errors.append(f'#{idx}: {label} הכריז 3NT עם {st} לקיחות (מינ׳ 4)')
        if not stops:
            errors.append(f'#{idx}: {label} הכריז 3NT ללא עוצרים בכל הסדרות')

    elif response == f'3{sym}':
        if st != 4:
            errors.append(f'#{idx}: {label} הכריז 3{sym} עם {st} לקיחות (צ"ל 4)')
        if not fit:
            errors.append(f'#{idx}: {label} הכריז 3{sym} ללא 2+ קלפי {sym}')

    elif response == 'Pass':
        has_major_card = suit_len(resp_hand, major) >= 1
        if fit and st >= 4:
            errors.append(
                f'#{idx}: {label} פס עם {st} לקיחות + תמיכה '
                f'(צ"ל 3{sym} לפחות)')
        elif stops and has_major_card and st >= 4:
            errors.append(f'#{idx}: {label} פס עם {st} לקיחות + עוצרים (צ"ל 3NT)')


# ─── מצב A: מחשב פותח, תלמיד עונה ─────────────────────────────────────────

def scale_mode_a(n=2000, verbose=False):
    errors      = []
    resp_counts = Counter()
    major_counts = Counter()

    for i in range(n):
        major = random.choice(['H', 'S'])
        try:
            hands = deal_weak_two(major)
            sym   = _S[major]

            # self-play: N פותח 2M, S מכריז תגובה אוטומטית
            response = _calc_response(hands['S'], major)

            # validation
            _validate_opener(hands['N'], major, i, errors, position=hands.get('position', 1), label='N')
            _validate_response(hands['S'], major, response, i, errors, label='S')

            resp_counts[response] += 1
            major_counts[sym] += 1

            if verbose and i < 3:
                hn = hcp(hands['N'])
                st = sure_tricks(hands['S'])
                fit = suit_len(hands['S'], major)
                print(f'  #{i} ({sym}): N={hn}נק׳ פתח 2{sym} | '
                      f'S: {st} לק׳ fit={fit} → {response}')

        except Exception as e:
            errors.append(f'#{i}: חריגה — {e}')

    return errors, resp_counts, major_counts


# ─── מצב B: תלמיד פותח, מחשב עונה ──────────────────────────────────────────

def scale_mode_b(n=2000, verbose=False):
    errors      = []
    resp_counts = Counter()
    major_counts = Counter()

    for i in range(n):
        major = random.choice(['H', 'S'])
        try:
            hands = deal_student_weak2(major)
            sym   = _S[major]

            # self-play: S פותח 2M, N מכריז תגובה אוטומטית
            n_response = _calc_response(hands['N'], major)

            # validation
            _validate_opener(hands['S'], major, i, errors, position=hands.get('position', 1), label='S')
            _validate_response(hands['N'], major, n_response, i, errors, label='N')

            resp_counts[n_response] += 1
            major_counts[sym] += 1

            if verbose and i < 3:
                hs = hcp(hands['S'])
                st = sure_tricks(hands['N'])
                fit = suit_len(hands['N'], major)
                print(f'  #{i} ({sym}): S={hs}נק׳ פתח 2{sym} | '
                      f'N: {st} לק׳ fit={fit} → {n_response}')

        except Exception as e:
            errors.append(f'#{i}: חריגה — {e}')

    return errors, resp_counts, major_counts


# ─── הדפסה ───────────────────────────────────────────────────────────────────

def _bar(counts, total):
    lines = []
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        pct = 100 * v / total if total else 0
        lines.append(f'    {k:<10} {v:>5}  ({pct:4.1f}%)')
    return '\n'.join(lines)


def run(n=2000, mode=None, verbose=False):
    sep = '─' * 56

    if mode in (None, 'A', 'a'):
        print(sep)
        print(f' מצב A — מחשב (N) פותח Weak Two  |  {n} ידיות')
        print(sep)
        errors, resps, majors = scale_mode_a(n, verbose)
        total = sum(majors.values())
        print(f'  ידיות: {total}   ♥={majors.get("♥",0)}  ♠={majors.get("♠",0)}')
        print()
        print('  self-play — תגובות S:')
        print(_bar(resps, total))
        print()
        if errors:
            print(f'  ✗ שגיאות: {len(errors)}')
            for e in errors[:20]:
                print(f'    • {e}')
            if len(errors) > 20:
                print(f'    ... ועוד {len(errors)-20}')
        else:
            print('  ✓ אין שגיאות')

    if mode in (None, 'B', 'b'):
        print()
        print(sep)
        print(f' מצב B — תלמיד (S) פותח Weak Two  |  {n} ידיות')
        print(sep)
        errors, resps, majors = scale_mode_b(n, verbose)
        total = sum(majors.values())
        print(f'  ידיות: {total}   ♥={majors.get("♥",0)}  ♠={majors.get("♠",0)}')
        print()
        print('  self-play — תגובות N:')
        print(_bar(resps, total))
        print()
        if errors:
            print(f'  ✗ שגיאות: {len(errors)}')
            for e in errors[:20]:
                print(f'    • {e}')
            if len(errors) > 20:
                print(f'    ... ועוד {len(errors)-20}')
        else:
            print('  ✓ אין שגיאות')

    print(sep)


if __name__ == '__main__':
    args   = sys.argv[1:]
    n      = int(args[0]) if args and args[0].isdigit() else 2000
    mode   = args[1].upper() if len(args) >= 2 and args[1].upper() in ('A','B') else None
    verbose = '-v' in args
    run(n, mode, verbose)
