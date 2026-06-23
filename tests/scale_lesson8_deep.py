"""
scale_lesson8_deep.py — בדיקה עמוקה לשיעור 8 (סלם NT).

בדיקות:
  1. לוגיקת סף  — כל ערכי גבול לכל Mode (A/B/C/D)
  2. טקסטים     — כותרות instruction, שורות טבלה, ללא ערכים ישנים
  3. אילוצי deal — טווחי HCP, עקביות N/S, אין 4+ מיגור ב-S (A/B)
  4. עקביות     — 6NT רק עם ≥33, 3NT רק עם <33, 4NT מוביל לתוצאה הגיונית
  5. Mode D      — S=18-20, N=12-17, ללא 4+ מיגור ב-N

הרצה:
    python tests/scale_lesson8_deep.py
    python tests/scale_lesson8_deep.py 3000
"""
import sys, os, re, random
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import (
    deal_slam_nt_mode_a, deal_slam_nt_mode_b,
    deal_slam_nt_mode_c, deal_slam_nt_mode_d,
)
from engine.scoring import hcp, suit_len, distribution, is_balanced
from engine.opening import opening_bid as _opening_bid

_SUIT = {'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠'}
_MODE_C_SEQS = [('C', 'H'), ('C', 'S'), ('D', 'H'), ('D', 'S')]
_MODE_D_SEQS = [('C', 'H'), ('C', 'S'), ('D', 'H'), ('D', 'S')]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ═══════════════════════════════════════════════════════════════════════════
#  חישוב עצמאי של הכרזה נכונה — חייב להיות זהה ל-lesson_slam_nt.py
# ═══════════════════════════════════════════════════════════════════════════

def _correct_a(hs):
    """Mode A: N=1NT (15-17). S מחליט."""
    if hs <= 7:  return 'Pass'
    if hs <= 9:  return '2NT'
    if hs <= 15: return '3NT'
    return '4NT'


def _correct_b(hs):
    """Mode B: N=2NT (20-22). S מחליט."""
    if hs <= 10: return '3NT'
    if hs >= 13: return '6NT'
    return '4NT'


def _correct_c(hs):
    """Mode C: N ריבאד 1NT (12-16). S מחליט."""
    if hs <= 16: return '3NT'
    if hs >= 20: return '6NT'
    return '4NT'


def _computer_accept_4nt(hn, hs):
    """N מקבל 4NT אם combined ≥ 33."""
    return (hn + hs) >= 33


# ═══════════════════════════════════════════════════════════════════════════
#  [1] בדיקת לוגיקת סף — ערכי גבול
# ═══════════════════════════════════════════════════════════════════════════

def check_threshold_logic():
    issues = []

    # Mode A
    cases_a = [
        (0, 'Pass'), (7, 'Pass'),
        (8, '2NT'),  (9, '2NT'),
        (10, '3NT'), (15, '3NT'),
        (16, '4NT'), (20, '4NT'),
    ]
    for hs, expected in cases_a:
        got = _correct_a(hs)
        if got != expected:
            issues.append(f'Mode A: hs={hs} → {got} (צריך {expected})')

    # Mode B
    cases_b = [
        (5, '3NT'), (10, '3NT'),
        (11, '4NT'), (12, '4NT'),
        (13, '6NT'), (15, '6NT'),
    ]
    for hs, expected in cases_b:
        got = _correct_b(hs)
        if got != expected:
            issues.append(f'Mode B: hs={hs} → {got} (צריך {expected})')

    # Mode C
    cases_c = [
        (14, '3NT'), (16, '3NT'),
        (17, '4NT'), (19, '4NT'),
        (20, '6NT'), (21, '6NT'),
    ]
    for hs, expected in cases_c:
        got = _correct_c(hs)
        if got != expected:
            issues.append(f'Mode C: hs={hs} → {got} (צריך {expected})')

    return issues


# ═══════════════════════════════════════════════════════════════════════════
#  [2] בדיקת טקסטים בקובץ השיעור
# ═══════════════════════════════════════════════════════════════════════════

_HEB = re.compile(r'[א-ת]')
_ADJACENT = re.compile(r'[א-ת][0-9A-Za-z♣♦♥♠]|[0-9A-Za-z♣♦♥♠][א-ת]')


def check_lesson_texts():
    issues = []
    fp = os.path.join(ROOT, 'lessons', 'lesson_slam_nt.py')
    if not os.path.exists(fp):
        return [('קובץ חסר', 0, 'lesson_slam_nt.py לא נמצא')]

    with open(fp, encoding='utf-8') as f:
        lines = f.readlines()
    text_full = ''.join(lines)

    # ── כותרות instruction שחייבות להופיע ──────────────────────────────────
    required = [
        ('1NT (15-17)', 'Mode A header'),
        ('2NT (20-22)', 'Mode B header'),
        ('1NT (12-16)', 'Mode C header'),
        ('1NT (12-17)', 'Mode D header'),
    ]
    for token, desc in required:
        if token not in text_full:
            issues.append(('כותרת חסרה', 0, f'{desc}: "{token}" לא נמצא'))

    # ── שורות טבלה Mode B ──────────────────────────────────────────────────
    for row in ['5-10', '11-12', '13+']:
        if row not in text_full:
            issues.append(('Mode B שורה חסרה', 0, f'"{row}"'))

    # ── שורות טבלה Mode C ──────────────────────────────────────────────────
    for row in ['עד 16', '17-19', '20+']:
        if row not in text_full:
            issues.append(('Mode C שורה חסרה', 0, f'"{row}"'))

    # ── ערכים ישנים שאסור שיופיעו ב-Mode C ─────────────────────────────────
    old_values = [
        ('12-14',  'טווח N ישן (היה 12-14, צריך 12-16)'),
        ('19-20',  'סף ישן 4NT Mode C (היה 19-20)'),
        ("'עד 18'", 'סף ישן 3NT Mode C (היה עד 18)'),
        ('"עד 18"', 'סף ישן 3NT Mode C (היה עד 18)'),
    ]
    for token, desc in old_values:
        if token in text_full:
            # מצא שורה
            for i, line in enumerate(lines, 1):
                if token in line:
                    issues.append(('ערך ישן', i, f'{desc}: "{token}" — {line.strip()[:70]}'))
                    break

    # ── עברית+LTR צמוד בתוך מחרוזות ──────────────────────────────────────
    # מחליף \\n, \\t ב-source לפני הבדיקה (כדי לא לזהות \n+עברית כשגיאה)
    for i, line in enumerate(lines, 1):
        for m in re.finditer(r"(['\"])(.*?)\1", line):
            txt = m.group(2)
            # מנקה escape sequences מ-source (\\n → רווח, \\t → רווח)
            clean = re.sub(r'\\[ntr]', ' ', txt)
            # מסיר תוכן של f-string expressions {…}
            clean = re.sub(r'\{[^}]*\}', ' ', clean)
            if _HEB.search(clean) and _ADJACENT.search(clean):
                issues.append(('עברית+LTR צמוד', i, txt[:70]))

    return issues


# ═══════════════════════════════════════════════════════════════════════════
#  [3] בדיקת Mode A
# ═══════════════════════════════════════════════════════════════════════════

def check_mode_a(hands, idx, errors):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    total = hn + hs

    # אילוצי deal
    if not (15 <= hn <= 17):
        errors.append(f'A#{idx}: N HCP={hn} מחוץ לטווח 15-17')
    if not is_balanced(n):
        errors.append(f'A#{idx}: N לא מאוזן')
    ds = distribution(s)
    if ds['H'] >= 4 or ds['S'] >= 4:
        errors.append(f'A#{idx}: S יש 4+ מיגור (יגרום לסטיימן). ♥={ds["H"]} ♠={ds["S"]}')

    bid = _correct_a(hs)

    # עקביות ביד
    if bid == 'Pass' and hs > 7:
        errors.append(f'A#{idx}: Pass עם {hs} נקודות (צריך ≤7)')
    if bid == '2NT' and not (8 <= hs <= 9):
        errors.append(f'A#{idx}: 2NT עם {hs} נקודות (צריך 8-9)')
    if bid == '3NT' and not (10 <= hs <= 15):
        errors.append(f'A#{idx}: 3NT עם {hs} נקודות (צריך 10-15)')
    if bid == '4NT' and hs < 16:
        errors.append(f'A#{idx}: 4NT עם {hs} נקודות (צריך 16+)')

    # אם N מקבל 4NT → combined ≥ 33
    if bid == '4NT' and _computer_accept_4nt(hn, hs) and total < 33:
        errors.append(f'A#{idx}: N קיבל 4NT→6NT אבל total={total}<33 (N={hn}, S={hs})')

    return bid, hn, hs, total


# ═══════════════════════════════════════════════════════════════════════════
#  [4] בדיקת Mode B
# ═══════════════════════════════════════════════════════════════════════════

def check_mode_b(hands, idx, errors):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    total = hn + hs

    if not (20 <= hn <= 22):
        errors.append(f'B#{idx}: N HCP={hn} מחוץ לטווח 20-22')
    if not is_balanced(n):
        errors.append(f'B#{idx}: N לא מאוזן')
    ds = distribution(s)
    if ds['H'] >= 4 or ds['S'] >= 4:
        errors.append(f'B#{idx}: S יש 4+ מיגור. ♥={ds["H"]} ♠={ds["S"]}')
    if not (5 <= hs <= 15):
        errors.append(f'B#{idx}: S HCP={hs} מחוץ לטווח 5-15')

    bid = _correct_b(hs)

    if bid == '3NT' and hs > 10:
        errors.append(f'B#{idx}: 3NT עם {hs} נקודות (צריך ≤10)')
    if bid == '3NT' and total >= 33:
        errors.append(f'B#{idx}: 3NT אבל total={total}≥33 (N={hn}, S={hs}) — אולי 6NT נכון?')
    if bid == '4NT' and not (11 <= hs <= 12):
        errors.append(f'B#{idx}: 4NT עם {hs} נקודות (צריך 11-12)')
    if bid == '6NT':
        if hs < 13:
            errors.append(f'B#{idx}: 6NT עם {hs} נקודות (צריך 13+)')
        if total < 33:
            errors.append(f'B#{idx}: 6NT ישיר עם total={total}<33 (N={hn}, S={hs})')

    if bid == '4NT' and _computer_accept_4nt(hn, hs) and total < 33:
        errors.append(f'B#{idx}: N קיבל 4NT→6NT אבל total={total}<33')

    return bid, hn, hs, total


# ═══════════════════════════════════════════════════════════════════════════
#  [5] בדיקת Mode C
# ═══════════════════════════════════════════════════════════════════════════

def check_mode_c(hands, idx, errors, opening, response):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    total = hn + hs
    open_sym = _SUIT[opening]

    # אילוצי deal — N
    if not (12 <= hn <= 16):
        errors.append(f'C#{idx}: N HCP={hn} מחוץ לטווח 12-16')

    # N פותח בצבע הנכון
    op_bid, _ = _opening_bid(n)
    if op_bid != f'1{open_sym}':
        errors.append(f'C#{idx}: N פותח {op_bid} במקום 1{open_sym}')

    # N אין התאמה בצבע התגובה
    n_resp_len = suit_len(n, response)
    if n_resp_len >= 4:
        errors.append(f'C#{idx}: N יש {n_resp_len} קלפי {_SUIT[response]} (אסור ≥4)')

    # S
    if not (14 <= hs <= 21):
        errors.append(f'C#{idx}: S HCP={hs} מחוץ לטווח 14-21')

    s_resp_len = suit_len(s, response)
    if s_resp_len != 4:
        errors.append(f'C#{idx}: S יש {s_resp_len} קלפי {_SUIT[response]} (צריך בדיוק 4)')

    # S אין מיגור שני (response=H → ללא 4+ ♠, response=S → ללא 4+ ♥)
    other = 'S' if response == 'H' else 'H'
    if suit_len(s, other) >= 4:
        errors.append(f'C#{idx}: S יש 4+ {_SUIT[other]} בנוסף ל-{_SUIT[response]}')

    bid = _correct_c(hs)

    if bid == '3NT':
        if hs > 16:
            errors.append(f'C#{idx}: 3NT עם {hs} נקודות (צריך ≤16)')
        if total >= 33:
            errors.append(f'C#{idx}: 3NT אבל total={total}≥33 (N={hn}, S={hs})')
    elif bid == '4NT':
        if not (17 <= hs <= 19):
            errors.append(f'C#{idx}: 4NT עם {hs} נקודות (צריך 17-19)')
        if _computer_accept_4nt(hn, hs) and total < 33:
            errors.append(f'C#{idx}: N קיבל 4NT→6NT אבל total={total}<33')
    elif bid == '6NT':
        if hs < 20:
            errors.append(f'C#{idx}: 6NT עם {hs} נקודות (צריך 20+)')

    return bid, hn, hs, total


# ═══════════════════════════════════════════════════════════════════════════
#  [6] בדיקת Mode D
# ═══════════════════════════════════════════════════════════════════════════

def check_mode_d(hands, idx, errors, opening, response):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    open_sym = _SUIT[opening]

    # N
    if not (12 <= hn <= 17):
        errors.append(f'D#{idx}: N HCP={hn} מחוץ לטווח 12-17')

    # N פותח בצבע הנכון
    op_bid, _ = _opening_bid(n)
    if op_bid != f'1{open_sym}':
        errors.append(f'D#{idx}: N פותח {op_bid} במקום 1{open_sym}')

    # N ללא 4+ מיגור (כדי לריבאד 1NT)
    if suit_len(n, 'H') >= 4 or suit_len(n, 'S') >= 4:
        dn = distribution(n)
        errors.append(f'D#{idx}: N יש 4+ מיגור. ♥={dn["H"]} ♠={dn["S"]} (יריבאד מיגור, לא 1NT)')

    # S
    if not (18 <= hs <= 20):
        errors.append(f'D#{idx}: S HCP={hs} מחוץ לטווח 18-20')

    # S יש 4+ בצבע התגובה
    if suit_len(s, response) < 4:
        errors.append(f'D#{idx}: S יש {suit_len(s, response)} קלפי {_SUIT[response]} (צריך 4+)')

    # הכרזה נכונה לפי כלל השיעור
    has_five = any(suit_len(s, su) >= 5 for su in ['S', 'H', 'D', 'C'])
    correct = '6NT' if (has_five and hs == 20) else '4NT'

    total = hn + hs
    if correct == '4NT' and _computer_accept_4nt(hn, hs) and total < 33:
        errors.append(f'D#{idx}: N קיבל 4NT→6NT אבל total={total}<33')

    return correct, hn, hs, total


# ═══════════════════════════════════════════════════════════════════════════
#  הרצה ראשית
# ═══════════════════════════════════════════════════════════════════════════

def _bar(counts, total, indent='    '):
    if not counts:
        return f'{indent}(ריק)'
    lines = []
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        pct = 100 * v / total if total else 0
        lines.append(f'{indent}{k:<8} {v:>5}  ({pct:5.1f}%)')
    return '\n'.join(lines)


def _section(title):
    print(f'\n{"─"*60}')
    print(f'  {title}')
    print('─' * 60)


def run(n=2000):
    sep = '═' * 60
    print(sep)
    print(f'  scale_lesson8_deep — שיעור 8 סלם NT | {n} ידיים')
    print(sep)

    all_errors = []

    # ── [1] לוגיקת סף ────────────────────────────────────────────────────────
    _section('[1] לוגיקת סף — ערכי גבול A/B/C')
    thresh = check_threshold_logic()
    if thresh:
        all_errors.extend(thresh)
        for t in thresh:
            print(f'  ✗ {t}')
    else:
        print('  ✓ כל הספים נכונים')
        print('    Mode A: Pass≤7, 2NT=8-9, 3NT=10-15, 4NT=16+')
        print('    Mode B: 3NT≤10, 4NT=11-12, 6NT=13+')
        print('    Mode C: 3NT≤16, 4NT=17-19, 6NT=20+')

    # ── [2] טקסטים ────────────────────────────────────────────────────────────
    _section('[2] טקסטים בקובץ השיעור')
    text_iss = check_lesson_texts()
    if text_iss:
        for kind, lineno, txt in text_iss:
            loc = f'שורה {lineno}' if lineno else 'קובץ'
            print(f'  ✗ {kind} ({loc}): {txt}')
            all_errors.append(f'טקסט [{kind}]: {txt[:50]}')
    else:
        print('  ✓ כותרות, שורות טבלה, ואין ערכים ישנים')

    per = n // 4
    chunks = [('A', per), ('B', per), ('C', per), ('D', n - 3 * per)]

    for mode, count in chunks:
        bid_counts = Counter()
        mode_errors = []
        deal_failures = 0
        total_by_bid = Counter()  # total points per bid

        for i in range(count):
            try:
                if mode == 'A':
                    hands = deal_slam_nt_mode_a()
                    bid, hn, hs, total = check_mode_a(hands, i, mode_errors)
                elif mode == 'B':
                    hands = deal_slam_nt_mode_b()
                    bid, hn, hs, total = check_mode_b(hands, i, mode_errors)
                elif mode == 'C':
                    opening, response = random.choice(_MODE_C_SEQS)
                    hands = deal_slam_nt_mode_c(opening, response)
                    bid, hn, hs, total = check_mode_c(hands, i, mode_errors, opening, response)
                else:
                    opening, response = random.choice(_MODE_D_SEQS)
                    hands = deal_slam_nt_mode_d(opening, response)
                    bid, hn, hs, total = check_mode_d(hands, i, mode_errors, opening, response)

                bid_counts[bid] += 1
                total_by_bid[bid] += total

            except RuntimeError:
                # כשל deal (האילוצים קשים מדי) — נורמלי לפעמים
                deal_failures += 1
            except Exception as e:
                mode_errors.append(f'Mode {mode}#{i}: חריגה בלתי-צפויה — {e}')

        n_mode = sum(bid_counts.values())

        # תיאורי Mode
        desc = {
            'A': 'N=1NT (15-17). S: Pass/2NT/3NT/4NT',
            'B': 'N=2NT (20-22). S: 3NT/4NT/6NT',
            'C': 'N ריבאד 1NT (12-16). S: 3NT/4NT/6NT',
            'D': 'N ריבאד 1NT (12-17). S: 4NT/6NT ישיר',
        }[mode]

        _section(f'[{3 + ord(mode) - ord("A")}] Mode {mode} — {count} ידיים: {desc}')
        print(_bar(bid_counts, n_mode))

        # ממוצע נקודות לכל הכרזה
        if n_mode:
            avg_parts = []
            for bid in sorted(bid_counts.keys()):
                cnt = bid_counts[bid]
                avg = total_by_bid[bid] / cnt if cnt else 0
                avg_parts.append(f'{bid}={avg:.1f}נק\'')
            print(f'    ממוצע combined: {", ".join(avg_parts)}')

        if deal_failures:
            pct = 100 * deal_failures / count
            warn = '⚠' if pct < 5 else '✗'
            print(f'  {warn} כשלי deal: {deal_failures}/{count} ({pct:.1f}%)'
                  + (' — תקין (<5%)' if pct < 5 else ' — יותר מדי!'))
            if pct >= 5:
                all_errors.append(f'Mode {mode}: {deal_failures} כשלי deal ({pct:.1f}%)')

        if mode_errors:
            uniq = sorted(set(mode_errors))
            print(f'  ✗ {len(mode_errors)} שגיאות ({len(uniq)} ייחודיות):')
            for e in uniq[:12]:
                print(f'    • {e}')
            if len(uniq) > 12:
                print(f'    ... ועוד {len(uniq) - 12}')
            all_errors.extend(mode_errors)
        else:
            print(f'  ✓ אין שגיאות לוגיות')

    # ── סיכום ────────────────────────────────────────────────────────────────
    print()
    print(sep)
    total_e = len(all_errors)
    if total_e == 0:
        print(f'  ✓ עבר הכל — 0 שגיאות')
    else:
        print(f'  ✗ {total_e} שגיאות סה"כ')
    print(sep)

    return total_e


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    sys.exit(0 if run(n) == 0 else 1)
