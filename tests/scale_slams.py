"""
סקייל בדיקה לשיעורים 8 ו-9 — סלם NT וסלם בצבע.
מריץ N ידיים לכל שיעור ומדווח שגיאות וסטטיסטיקה.

שימוש:
    python tests/scale_slams.py          # ברירת מחדל: 2000 לכל שיעור
    python tests/scale_slams.py 500      # 500 לכל שיעור
    python tests/scale_slams.py 2000 8   # רק שיעור 8
    python tests/scale_slams.py 2000 9   # רק שיעור 9
"""

import sys, os, random
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import (
    deal_slam_nt_mode_a, deal_slam_nt_mode_b, deal_slam_nt_mode_c,
    deal_slam_major,
)
from engine.scoring import hcp, key_cards, distribution
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS

_MODE_C_SEQS = [('C','H'), ('C','S'), ('D','H'), ('D','S'), ('H','S')]

# תגובות בלאקווד: מספר מפתחות → הכרזה (זהה ל-lesson_slam_suit)
_BW_RESPONSE = {0: '5♣', 1: '5♦', 2: '5♥', 3: '5♠', 4: '5NT', 5: '5NT'}


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 8: סלם NT — חישוב עצמאי (תלמיד) וחישוב מחשב בנפרד
# ═══════════════════════════════════════════════════════════════════════════

def _lesson8_student_bid(mode, hs):
    """הכרזת התלמיד לפי מצב."""
    if mode == 'A':
        if hs <= 15: return '3NT'
        if hs <= 17: return '4NT'
        return '6NT'
    if mode == 'B':
        if hs <= 10: return '3NT'
        if hs <= 12: return '4NT'
        return '6NT'
    # C
    if hs <= 18: return '3NT'
    if hs <= 20: return '4NT'
    return '6NT'


def _lesson8_computer_bid(mode, hn, student_bid):
    """תגובת המחשב (N) לאחר 4NT — עצמאית מהכרזת התלמיד."""
    if student_bid != '4NT':
        return 'N/A'
    accept = {'A': 17, 'B': 22, 'C': 14}[mode]
    return '6NT' if hn >= accept else 'Pass'


def _lesson8_check(mode, hands, idx, errors):
    hn = hcp(hands['N'])
    hs = hcp(hands['S'])

    # — תלמיד —
    student_bid = _lesson8_student_bid(mode, hs)
    # — מחשב —
    computer_bid = _lesson8_computer_bid(mode, hn, student_bid)

    total = hn + hs

    # בדיקות טווח HCP — טווחי S הם איחוד כל התרחישים של המחלק
    # (r
    #  A: plain S=0-15, slam S=16-18, grand S=20-21
    #  B: plain S=5-12, slam S=13-15, grand S=17-18
    #  C: non-slam S=14-20, slam S=17-21 ; N=12-16)
    ranges = {'A': ((15,17),(0,21)), 'B': ((20,22),(5,18)), 'C': ((12,16),(14,21))}
    n_lo, n_hi = ranges[mode][0]
    s_lo, s_hi = ranges[mode][1]
    if not (n_lo <= hn <= n_hi):
        errors.append(f'Mode {mode} #{idx}: N HCP={hn} צריך להיות {n_lo}-{n_hi}')
    if not (s_lo <= hs <= s_hi):
        errors.append(f'Mode {mode} #{idx}: S HCP={hs} צריך להיות {s_lo}-{s_hi}')

    # עקביות: 6NT עם פחות מ-33 נקודות
    if student_bid == '6NT' and total < 33:
        errors.append(f'Mode {mode} #{idx}: תלמיד הכריז 6NT עם {total} נק\' ({hn}+{hs})')
    # 4NT נדחה אבל מספיק לסלם
    if student_bid == '4NT' and computer_bid == 'Pass' and total >= 34:
        errors.append(f'Mode {mode} #{idx}: 4NT נדחה אבל {total} נק\' ({hn}+{hs}) — אולי בעיה')
    # מחשב קיבל 4NT אבל אין מספיק
    if student_bid == '4NT' and computer_bid == '6NT' and total < 33:
        errors.append(f'Mode {mode} #{idx}: מחשב קיבל 4NT→6NT אבל {total} נק\' ({hn}+{hs})')

    return student_bid, computer_bid


def scale_lesson8(n=2000, verbose=False):
    """שיעור 8: מריץ n ידיים (חלוקה: ~n/3 לכל מצב)."""
    errors = []
    bid_counts = Counter()
    mode_counts = Counter()

    per = n // 3
    chunks = [('A', per), ('B', per), ('C', n - 2*per)]

    for mode, count in chunks:
        for i in range(count):
            try:
                if mode == 'A':
                    hands = deal_slam_nt_mode_a()
                elif mode == 'B':
                    hands = deal_slam_nt_mode_b()
                else:
                    opening, response = random.choice(_MODE_C_SEQS)
                    hands = deal_slam_nt_mode_c(opening, response)

                sb, cb = _lesson8_check(mode, hands, i, errors)
                bid_counts[f'תלמיד:{sb}'] += 1
                if cb != 'N/A':
                    bid_counts[f'מחשב:{cb}'] += 1
                mode_counts[mode] += 1

                if verbose and i < 3:
                    hn, hs = hcp(hands['N']), hcp(hands['S'])
                    print(f'  Mode {mode} #{i}: N={hn} S={hs} → תלמיד={sb} מחשב={cb}')
            except Exception as e:
                errors.append(f'Mode {mode} #{i}: חריגה — {e}')

    return errors, bid_counts, mode_counts


# ═══════════════════════════════════════════════════════════════════════════
#  שיעור 9: סלם בצבע — חישוב עצמאי (תלמיד) וחישוב מחשב בנפרד
# ═══════════════════════════════════════════════════════════════════════════

def _has_shortage(hand, trump):
    """סינגלטון/ווייד בסדרה שאינה שליט."""
    from engine.scoring import distribution as _dist
    d = _dist(hand)
    return any(d[s] <= 1 for s in ['S', 'H', 'D', 'C'] if s != trump)


def _lesson9_student_bid1(hs, trump_sym, shortage):
    """שלב 1: 4NT אם 18+ נק', או 17 עם קצר/ווייד. אחרת 4M."""
    if hs >= 18 or (hs == 17 and shortage):
        return '4NT'
    return f'4{trump_sym}'


def _lesson9_computer_bw(n_kc):
    """תגובת בלאקווד של המחשב (N)."""
    return _BW_RESPONSE[n_kc]


def _lesson9_student_bid2(n_kc, s_kc, trump_sym):
    """שלב 2: סלם אם 4+ מפתחות, אחרת עצור."""
    total = n_kc + s_kc
    return f'6{trump_sym}' if total >= 4 else f'5{trump_sym}'


def _lesson9_check(trump, hands, idx, errors):
    trump_sym = _S[trump]
    hn  = hcp(hands['N'])
    hs  = hcp(hands['S'])
    n_kc     = key_cards(hands['N'], trump)
    s_kc     = key_cards(hands['S'], trump)
    total_kc = n_kc + s_kc
    shortage = _has_shortage(hands['S'], trump)

    # — שלב 1: תלמיד —
    sb1 = _lesson9_student_bid1(hs, trump_sym, shortage)

    # — שלב 2 (רק אם 4NT) —
    sb2 = cb_bw = None
    if sb1 == '4NT':
        cb_bw = _lesson9_computer_bw(n_kc)
        sb2   = _lesson9_student_bid2(n_kc, s_kc, trump_sym)

    # בדיקות טווח — N: 12-19, S: 8-17 (game S=8-14, slam/stop S=14-17)
    if not (12 <= hn <= 19):
        errors.append(f'#{idx} ({trump}): N HCP={hn} מחוץ לטווח 12-19')
    if not (8 <= hs <= 17):
        errors.append(f'#{idx} ({trump}): S HCP={hs} מחוץ לטווח 8-17')
    if not (0 <= n_kc <= 5):
        errors.append(f'#{idx} ({trump}): N key_cards={n_kc} בלתי-חוקי')
    if not (0 <= s_kc <= 5):
        errors.append(f'#{idx} ({trump}): S key_cards={s_kc} בלתי-חוקי')
    if total_kc > 5:
        errors.append(f'#{idx} ({trump}): סה״כ מפתחות={total_kc} > 5')

    # עקביות שלב 1
    if sb1 == '4NT' and hs <= 16:
        errors.append(f'#{idx} ({trump}): תלמיד הכריז 4NT עם {hs} נקודות ללא קצר')
    if sb1 == f'4{trump_sym}' and hs >= 18:
        errors.append(f'#{idx} ({trump}): תלמיד הכריז 4{trump_sym} עם {hs} נקודות (צ"ל 4NT)')

    # עקביות שלב 2
    if sb2 == f'6{trump_sym}' and total_kc < 4:
        errors.append(f'#{idx} ({trump}): סלם עם {total_kc} מפתחות בלבד')
    if sb2 == f'5{trump_sym}' and total_kc >= 4:
        errors.append(f'#{idx} ({trump}): עצר ב-5{trump_sym} עם {total_kc} מפתחות (צ"ל סלם)')

    return sb1, cb_bw, sb2


def scale_lesson9(n=2000, verbose=False):
    """שיעור 9: מריץ n ידיים (חלוקה שווה ♥/♠)."""
    errors = []
    bid1_counts = Counter()
    bid2_counts = Counter()
    bw_counts   = Counter()
    trump_counts = Counter()

    for i in range(n):
        trump = random.choice(['H', 'S'])
        trump_sym = _S[trump]
        try:
            hands = deal_slam_major(trump)
            sb1, cb_bw, sb2 = _lesson9_check(trump, hands, i, errors)

            bid1_counts[sb1] += 1
            trump_counts[trump_sym] += 1
            if cb_bw:
                bw_counts[cb_bw] += 1
            if sb2:
                bid2_counts[sb2] += 1

            if verbose and i < 3:
                hn, hs = hcp(hands['N']), hcp(hands['S'])
                n_kc = key_cards(hands['N'], trump)
                s_kc = key_cards(hands['S'], trump)
                print(f'  #{i} ({trump_sym}): N={hn}/{n_kc}mc S={hs}/{s_kc}mc '
                      f'→ שלב1={sb1}  BW={cb_bw}  שלב2={sb2}')
        except Exception as e:
            errors.append(f'#{i} ({trump}): חריגה — {e}')

    return errors, bid1_counts, bw_counts, bid2_counts, trump_counts


# ═══════════════════════════════════════════════════════════════════════════
#  הרצה ראשית
# ═══════════════════════════════════════════════════════════════════════════

def _bar(label, counts, total):
    lines = []
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        pct = 100 * v / total if total else 0
        lines.append(f'    {k:<20} {v:>5}  ({pct:4.1f}%)')
    return '\n'.join(lines)


def run(n=2000, lesson=None):
    sep = '─' * 56

    if lesson in (None, 8, '8'):
        print(sep)
        print(f' שיעור 8 — סלם NT  |  {n} ידיים')
        print(sep)
        errors, bids, modes = scale_lesson8(n, verbose=False)
        total = sum(modes.values())
        print(f'  ידיים שהורצו: {total}')
        print(f'  מצבים: ' + '  '.join(f'{m}={c}' for m,c in sorted(modes.items())))
        print()
        print('  הכרזות תלמיד:')
        student = {k: v for k,v in bids.items() if k.startswith('תלמיד:')}
        print(_bar('', {k[6:]: v for k,v in student.items()}, total))
        print()
        print('  תגובות מחשב (אחרי 4NT):')
        computer = {k: v for k,v in bids.items() if k.startswith('מחשב:')}
        n4nt = sum(v for k,v in bids.items() if '4NT' in k)
        print(_bar('', {k[6:]: v for k,v in computer.items()}, n4nt or 1))
        print()
        if errors:
            print(f'  ✗ שגיאות: {len(errors)}')
            for e in errors[:20]:
                print(f'    • {e}')
            if len(errors) > 20:
                print(f'    ... ועוד {len(errors)-20}')
        else:
            print('  ✓ אין שגיאות')

    if lesson in (None, 9, '9'):
        print()
        print(sep)
        print(f' שיעור 9 — סלם בצבע  |  {n} ידיים')
        print(sep)
        errors, bid1, bw, bid2, trumps = scale_lesson9(n, verbose=False)
        total = sum(trumps.values())
        print(f'  ידיים שהורצו: {total}')
        print(f'  שיט: ' + '  '.join(f'{t}={c}' for t,c in sorted(trumps.items())))
        print()
        print('  שלב 1 (תלמיד):')
        print(_bar('', bid1, total))
        n4nt = bid1.get('4NT', 0)
        if n4nt:
            print()
            print(f'  תגובות בלאקווד (מחשב) — מתוך {n4nt} ידיים עם 4NT:')
            print(_bar('', bw, n4nt))
            print()
            print(f'  שלב 2 (תלמיד) — מתוך {n4nt}:')
            print(_bar('', bid2, n4nt))
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
    args = sys.argv[1:]
    n       = int(args[0]) if len(args) >= 1 else 2000
    lesson  = int(args[1]) if len(args) >= 2 else None
    run(n, lesson)
