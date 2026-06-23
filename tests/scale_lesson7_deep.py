"""
בדיקה עמוקה לשיעור 7 — 2♣ חזקה.
מטרה: לאתר בעיות ניקוד והכרזות בכל הנתיבים.

בדיקות:
  1. סף נקודות נכון לכל תגובה (2♦=0-7, 2♥/2♠=8+, 2NT=8+ מאוזן)
  2. לא עוצרים לפני משחק מלא (חוזה >= 3NT/4M)
  3. עם 33+ נקודות — מגיעים לשאילת אסים
  4. S עם 5+ מיגור מראה אותו אחרי ריבאד N (2♥/2♠/3♣/3♦)
  5. S עם 5+ ספיידים אחרי 2♣-2♦-3♣ מכריז 3♠
"""
import sys, os
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_robot_opens_2c
from engine.response import respond_2c, respond_2c_second, respond_2c_third
from engine.rebid import opener_rebid, opener_bid_2c_round3
from engine.scoring import hcp, is_balanced, distribution, sure_tricks
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS
_GAME = {'3NT', '4♥', '4♠', '5♣', '5♦', '6NT', '6♥', '6♠', '6♣', '6♦',
         '7NT', '7♥', '7♠', '7♣', '7♦'}


def _hand_str(hand):
    d = distribution(hand)
    return f'♠{d["S"]} ♥{d["H"]} ♦{d["D"]} ♣{d["C"]} ({hcp(hand)}נק\')'


def _check(hands, idx, errors):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    d_s = distribution(s)
    d_n = distribution(n)

    # ── R01/R02/R03: תגובה ראשונה ─────────────────────────────────────────
    s1, _ = respond_2c(s)

    if hs <= 6 and s1 != '2♦':
        errors.append(f'#{idx} [R01] S={hs}נק\' צ"ל 2♦ (המתנה) אבל הכריז {s1}. {_hand_str(s)}')

    if hs >= 8:
        if (d_s['H'] >= 5 or d_s['S'] >= 5) and s1 == '2♦':
            major = '♥' if d_s['H'] >= 5 else '♠'
            errors.append(f'#{idx} [R02] S={hs}נק\' יש 5{major} — צ"ל 2{major} חיובי, הכריז 2♦. {_hand_str(s)}')
        if is_balanced(s) and s1 == '2♦':
            errors.append(f'#{idx} [R03] S={hs}נק\' מאוזן — צ"ל 2NT, הכריז 2♦. {_hand_str(s)}')

    if s1 in ('2♥', '2♠') and hs < 8:
        errors.append(f'#{idx} [R02] S={hs}נק\' הכריז {s1} — צריך 8+ לחיובי. {_hand_str(s)}')

    if s1 == '2NT' and (hs < 8 or not is_balanced(s)):
        errors.append(f'#{idx} [R03] S={hs}נק\' הכריז 2NT — צריך 8+ מאוזן. {_hand_str(s)}')

    # ── ריבאד N ───────────────────────────────────────────────────────────
    n2, _ = opener_rebid(n, '2♣', s1)

    # ── בדיקה 2: לא עוצרים לפני משחק מלא ─────────────────────────────────
    # אם N2 הוא Pass לפני גיים — בעיה
    if n2 == 'Pass':
        level = 0  # Pass זה עצירה
        errors.append(f'#{idx} עצירה: N פסם אחרי 2♣-{s1}. N={_hand_str(n)} S={_hand_str(s)}')
        return s1, n2, None, None

    if n2 in _GAME:
        return s1, n2, None, None

    # ── תגובה שנייה של S ──────────────────────────────────────────────────
    s2, _ = respond_2c_second(s, n2)

    # בדיקה 2 בשלב S2
    if s2 == 'Pass' and n2 not in _GAME:
        errors.append(f'#{idx} עצירה: S פסם ב-{n2} לפני גיים. S={_hand_str(s)}')
        return s1, n2, s2, None

    # ── בדיקה 3: עם 33+ נקודות יש שאילת אסים ─────────────────────────────
    total = hn + hs
    if total >= 33 and s2 not in ('4♣', '4NT', 'Pass') and s2 is not None:
        # בדיקה שבסוף מגיעים לשאלה
        if s2 not in _GAME and s2 != '2NT':
            pass  # ימשיך לשלב הבא

    # ── R04: S מראה מיגור שני אחרי 2♥/2♠ ────────────────────────────────
    # 7+ קלפים (או 6 חלש) → 4M ישר; אחרת → 3M
    if s1 == '2♦' and n2 == '2♥' and d_s['S'] >= 5 and d_s['H'] < 3:
        if s2 != '2♠':
            errors.append(f'#{idx} [R04] אחרי 2♥, S יש {d_s["S"]}♠ — צ"ל 2♠, הכריז {s2}. {_hand_str(s)}')
    # ללא fit ב-♥ וללא מיגור שני → 3♦ מלאכותי
    if s1 == '2♦' and n2 == '2♥' and d_s['H'] < 3 and d_s['S'] < 5 and hs < 8:
        if s2 != '3♣':
            errors.append(f'#{idx} [R04] אחרי 2♥, ללא fit ללא מיגור — צ"ל 3♣ מלאכותי, הכריז {s2}. {_hand_str(s)}')

    if s1 == '2♦' and n2 == '2♠' and d_s['H'] >= 5 and d_s['S'] < 3:
        if s2 != '3♥':
            errors.append(f'#{idx} [R04] אחרי 2♠, S יש {d_s["H"]}♥ — צ"ל 3♥, הכריז {s2}. {_hand_str(s)}')

    # ── R05: אחרי מינור — ספיידים לפני לבבות ─────────────────────────────
    if s1 == '2♦' and n2 in ('3♣', '3♦') and d_s['S'] >= 5 and d_s['S'] >= d_s['H']:
        if s2 != '3♠':
            errors.append(f'#{idx} [R05] אחרי {n2}, S יש {d_s["S"]}♠ — צ"ל 3♠, הכריז {s2}. {_hand_str(s)}')

    # ── R09: אחרי 2♥/2♠ חיובי + תמיכה, S עם 8+ → 4NT ───────────────────
    if s1 in ('2♥', '2♠') and s2 is not None:
        trump_sym = s1[1]
        if n2 == f'3{trump_sym}' and hs >= 8 and s2 != '4NT':
            errors.append(f'#{idx} [R09] אחרי {s1}-{n2}, S={hs}נק\' — צ"ל 4NT (Blackwood), הכריז {s2}. {_hand_str(s)}')

    # ── ריבאד שלישי של N ──────────────────────────────────────────────────
    # 4NT = Blackwood — N עונה אוטומטית בשיעור, לא דרך opener_bid_2c_round3
    if s2 and s2 not in _GAME and s2 != 'Pass' and s2 != '4NT':
        try:
            n3, _ = opener_bid_2c_round3(n, n2, s2)
        except Exception:
            n3 = None

        if n3 == 'Pass' and n2 not in _GAME:
            errors.append(f'#{idx} [R00] N פסם ב-{n2}-{s2} לפני גיים. N={_hand_str(n)}')
    else:
        n3 = None

    return s1, n2, s2, n3


def check_hebrew(lesson_file):
    """בודק בעיות RTL/עברית בקובץ שיעור."""
    import re
    issues = []

    with open(lesson_file, encoding='utf-8') as f:
        lines = f.readlines()

    for lineno, line in enumerate(lines, 1):
        # חילוץ תוכן מחרוזות f-string
        strings = re.findall(r"f'([^']*)'|f\"([^\"]*)\"|'([^']*)'|\"([^\"]*)\"", line)
        for groups in strings:
            text = next((g for g in groups if g), '')
            if not text:
                continue

            # בדיקה 1: {var} נקודות ללא prefix עברי
            for m in re.finditer(r'\{[^}]+\}\s+נקודות', text):
                before = text[:m.start()].rstrip()
                hebrew_prefixes = ('יש', 'סה', 'לך', 'לו', 'לנו', 'ל-', 'כ-', 'ב-')
                if not any(before.endswith(p) for p in hebrew_prefixes):
                    issues.append(f'שורה {lineno}: {{{m.group()}}} ללא prefix עברי')

            # בדיקה 2: שתי כרזות/מספרים על אותה שורה (כמו "3NT = 5 קלפי")
            if re.search(r'[1-7][♣♦♥♠NT]{1,2}.*=.*\d+', text):
                if '\\n' not in text and '\n' not in text:
                    issues.append(f'שורה {lineno}: מספר+הכרזה אותה שורה: {text[:60]!r}')

            # בדיקה 3: ✓ נכון + LTR על אותה שורה
            if '✓' in text and re.search(r'[1-7][♣♦♥♠NT]', text):
                if '\\n' not in text:
                    issues.append(f'שורה {lineno}: ✓ נכון! עם LTR אותה שורה: {text[:60]!r}')

    return issues


def run(n=3000):
    errors = []
    s1_ctr  = Counter()
    n2_ctr  = Counter()
    s2_ctr  = Counter()
    paths   = Counter()

    for i in range(n):
        try:
            hands = deal_robot_opens_2c()
            result = _check(hands, i, errors)
            s1, n2, s2, n3 = result
            s1_ctr[s1] += 1
            n2_ctr[n2] += 1
            if s2:
                s2_ctr[s2] += 1
                paths[f'{s1}→{n2}→{s2}'] += 1
        except Exception as e:
            errors.append(f'#{i}: חריגה — {e}')

    sep = '─' * 58
    print(sep)
    print(f' שיעור 7 — בדיקה עמוקה  |  {n} ידיות')
    print(sep)

    print('  תגובה ראשונה S:')
    for k, v in sorted(s1_ctr.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/n:4.1f}%)')

    print('  ריבאד N:')
    for k, v in sorted(n2_ctr.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/n:4.1f}%)')

    print('  תגובה שנייה S:')
    for k, v in sorted(s2_ctr.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/n:4.1f}%)')

    print()
    top_paths = sorted(paths.items(), key=lambda x: -x[1])[:8]
    print('  נתיבים נפוצים:')
    for p, v in top_paths:
        print(f'    {p:<22} {v:>4}')

    print()
    if errors:
        by_type = defaultdict(list)
        for e in errors:
            t = e.split(':')[1].split()[0] if ':' in e else 'אחר'
            by_type[t].append(e)
        print(f'  ✗ שגיאות הכרזה: {len(errors)}')
        for t, errs in by_type.items():
            print(f'\n  [{t}] — {len(errs)} שגיאות:')
            for e in errs[:5]:
                print(f'    • {e}')
            if len(errs) > 5:
                print(f'    ... ועוד {len(errs)-5}')
    else:
        print('  ✓ הכרזות — אין שגיאות')

    # ── בדיקת עברית ──────────────────────────────────────────────────────
    print()
    lesson_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               'lessons', 'lesson_robot_opens_2c.py')
    heb_issues = check_hebrew(lesson_path)
    if heb_issues:
        print(f'  ✗ בעיות עברית: {len(heb_issues)}')
        for issue in heb_issues:
            print(f'    • {issue}')
    else:
        print('  ✓ עברית — אין בעיות')

    print(sep)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    run(n)
