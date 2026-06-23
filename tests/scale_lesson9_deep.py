"""
scale_lesson9_deep.py — בדיקה עמוקה לשיעור 9 (סלם בצבע).

כללים:
  שלב 1 (S מחליט):
    4NT  — 18+ HCP, או 17 עם קצר/ווייד
    4M   — עד 17 ללא קצר
  שלב 2 (אחרי RKCB):
    6M   — total_kc >= 5  AND combined >= 33
    stop — אחרת (5M אם גבוה מהתגובה, אחרת Pass)
  RKCB (5 מפתחות: 4 אסים + K שליט):
    5♣ = 0 או 3  |  5♦ = 1 או 4  |  5♥ = 2 ללא Q שליט  |  5♠ = 2 + Q שליט

הרצה:
    python tests/scale_lesson9_deep.py
    python tests/scale_lesson9_deep.py 3000
"""
import sys, os, random
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_slam_major
from engine.scoring import hcp, key_cards, rkcb_response, distribution, suit_len
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS
_SUIT_RANK = {'♣': 0, '♦': 1, '♥': 2, '♠': 3, 'NT': 4}


def _bid_rank(bid):
    if not bid or bid in ('Pass', 'X', 'XX'):
        return -1
    return int(bid[0]) * 5 + _SUIT_RANK.get(bid[1:], 4)


# ═══════════════════════════════════════════════════════════════════════════
#  לוגיקה עצמאית — חייבת להיות זהה ל-lesson_slam_suit.py
# ═══════════════════════════════════════════════════════════════════════════

def _calc_shortage(hand, trump):
    """None אם אין קצר, אחרת הסדרה עם ≤1 קלפים."""
    d = distribution(hand)
    for suit in ['S', 'H', 'D', 'C']:
        if suit != trump and d[suit] <= 1:
            return suit
    return None


def _correct_first(hs, shortage, trump_sym):
    """שלב 1: מה מכריז S?"""
    if hs >= 18 or (hs == 17 and shortage is not None):
        return '4NT'
    return '3NT' if trump_sym in ('♣', '♦') else f'4{trump_sym}'


def _stop_bid(trump_sym, response):
    """עצור: 5M אם גבוה מהתגובה, אחרת Pass."""
    game5 = f'5{trump_sym}'
    return game5 if _bid_rank(game5) > _bid_rank(response) else 'Pass'


def _dist_points(hand, trump):
    """נקודות חלוקה עם התאמה בשליט: ווייד=5, סינגלטון=3."""
    d = distribution(hand)
    for suit in ['S', 'H', 'D', 'C']:
        if suit != trump and d[suit] <= 1:
            return 3 if d[suit] == 0 else 2
    return 0


def _correct_second(n_kc, s_kc, hn, hs, trump_sym, n_response, hand_s=None, trump=None):
    """שלב 2: אחרי RKCB — 6M או עצור."""
    total = n_kc + s_kc
    dp = _dist_points(hand_s, trump) if hand_s is not None else 0
    combined = hn + hs + dp
    if total >= 5 and combined >= 33:
        return f'6{trump_sym}'
    return _stop_bid(trump_sym, n_response)


# ═══════════════════════════════════════════════════════════════════════════
#  [1] בדיקת לוגיקת סף — ערכי גבול
# ═══════════════════════════════════════════════════════════════════════════

def check_threshold_logic():
    issues = []
    t = '♥'

    # ── שלב 1: 4NT לעומת 4M ─────────────────────────────────────────────
    cases1 = [
        (16, None, f'4{t}'),   # 16 ללא קצר → 4M
        (16, 'C',  f'4{t}'),   # 16 עם קצר → 4M (עדיין 16)
        (17, None, f'4{t}'),   # 17 ללא קצר → 4M
        (17, 'D',  '4NT'),     # 17 עם קצר → 4NT
        (18, None, '4NT'),     # 18 ללא קצר → 4NT
        (18, 'C',  '4NT'),     # 18 עם קצר → 4NT
        (19, None, '4NT'),     # 19 → 4NT
    ]
    for hs, shortage, expected in cases1:
        got = _correct_first(hs, shortage, t)
        if got != expected:
            issues.append(f'שלב1: hs={hs}, קצר={shortage} → {got} (צריך {expected})')

    # ── שלב 2: 6M רק עם ≥33 נקודות ─────────────────────────────────────
    #  תגובה 5♣ — תמיד מתחת ל-5M, כך stop=5M
    cases2 = [
        (3, 2, 21, 12, f'6{t}'),  # 5 kc + 33 נק → סלם
        (3, 2, 20, 13, f'6{t}'),  # 5 kc + 33 נק → סלם
        (4, 1, 21, 12, f'6{t}'),  # 5 kc + 33 → סלם
        (5, 0, 21, 12, f'6{t}'),  # 5 kc + 33 → סלם
        (3, 2, 20, 12, f'5{t}'),  # 5 kc אבל 32 נק → עצור
        (2, 3, 20, 12, f'5{t}'),  # 5 kc אבל 32 נק → עצור
        (2, 2, 21, 12, f'5{t}'),  # 4 kc + 33 → עצור (kc חסר)
        (3, 1, 21, 18, f'5{t}'),  # 4 kc + 39 → עצור (kc חסר)
    ]
    for n_kc, s_kc, hn, hs, expected in cases2:
        got = _correct_second(n_kc, s_kc, hn, hs, t, '5♣')
        if got != expected:
            issues.append(
                f'שלב2: n_kc={n_kc}, s_kc={s_kc}, combined={hn+hs} → {got} (צריך {expected})'
            )

    # ── stop_bid: 5M לעומת Pass ──────────────────────────────────────────
    stop_cases = [
        ('♥', '5♣', '5♥'),   # 5♥ > 5♣
        ('♥', '5♦', '5♥'),   # 5♥ > 5♦
        ('♥', '5♥', 'Pass'),  # 5♥ = 5♥ → Pass
        ('♥', '5♠', 'Pass'),  # 5♥ < 5♠ → Pass
        ('♠', '5♣', '5♠'),   # 5♠ > 5♣
        ('♠', '5♦', '5♠'),   # 5♠ > 5♦
        ('♠', '5♥', '5♠'),   # 5♠ > 5♥
        ('♠', '5♠', 'Pass'),  # 5♠ = 5♠ → Pass
    ]
    for trump_sym, response, expected in stop_cases:
        got = _stop_bid(trump_sym, response)
        if got != expected:
            issues.append(f'stop_bid: {trump_sym}, תגובה={response} → {got} (צריך {expected})')

    return issues


# ═══════════════════════════════════════════════════════════════════════════
#  [2] בדיקת יד בודדת
# ═══════════════════════════════════════════════════════════════════════════

def check_hand(hands, trump, idx, errors):
    n, s = hands['N'], hands['S']
    hn = hcp(n)
    hs = hcp(s)
    t = _S[trump]
    shortage = _calc_shortage(s, trump)
    n_kc = key_cards(n, trump)
    s_kc = key_cards(s, trump)
    combined = hn + hs

    # ── אילוצי deal ──────────────────────────────────────────────────────
    if not (12 <= hn <= 19):
        errors.append(f'#{idx}: N HCP={hn} מחוץ לטווח 12-19')
    if suit_len(n, trump) < 5:
        errors.append(f'#{idx}: N יש {suit_len(n, trump)} קלפי {t} (צריך 5+)')
    if suit_len(s, trump) < 4:
        errors.append(f'#{idx}: S יש {suit_len(s, trump)} קלפי {t} (צריך 4+)')

    # ── שלב 1 ────────────────────────────────────────────────────────────
    first = _correct_first(hs, shortage, t)

    if first != f'4{t}':
        # ── בדיקת RKCB ───────────────────────────────────────────────────
        n_response, n_kc_check, _ = rkcb_response(n, trump)
        if n_kc_check != n_kc:
            errors.append(f'#{idx}: rkcb_response נתן kc={n_kc_check} אבל key_cards={n_kc}')

        # ── שלב 2 ────────────────────────────────────────────────────────
        second = _correct_second(n_kc, s_kc, hn, hs, t, n_response, s, trump)
        dp = _dist_points(s, trump)
        combined_adj = combined + dp

        # כלל הזהב: 6M רק עם ≥33 נקודות (כולל חלוקה)
        if second.startswith('6') and combined_adj < 33:
            errors.append(
                f'#{idx}: 6{t} עם combined_adj={combined_adj}<33 (N={hn}, S={hs}+{dp}, kc={n_kc+s_kc})'
            )
        # כלל ההפוך: אם יש 5+ kc ו-≥33 נק — חייב 6M
        if second != f'6{t}' and n_kc + s_kc >= 5 and combined_adj >= 33:
            errors.append(
                f'#{idx}: עצרנו ב-{second} אבל kc={n_kc+s_kc}≥5 ו-combined_adj={combined_adj}≥33'
            )

    return first, hn, hs, combined, n_kc + s_kc


# ═══════════════════════════════════════════════════════════════════════════
#  עזרים להדפסה
# ═══════════════════════════════════════════════════════════════════════════

def _bar(counts, total):
    lines = []
    for k, v in sorted(counts.items()):
        pct = 100 * v / total if total else 0
        lines.append(f'    {k:<8} {v:>5}  ({pct:5.1f}%)')
    return '\n'.join(lines)


def _section(title):
    print(f'\n{"─"*60}')
    print(f'  {title}')
    print('─' * 60)


# ═══════════════════════════════════════════════════════════════════════════
#  הרצה ראשית
# ═══════════════════════════════════════════════════════════════════════════

def run(n=2000):
    sep = '═' * 60
    print(sep)
    print(f'  scale_lesson9_deep — שיעור 9 סלם בצבע | {n} ידיים')
    print(sep)

    all_errors = []

    # ── [1] לוגיקת סף ────────────────────────────────────────────────────
    _section('[1] לוגיקת סף — ערכי גבול')
    thresh = check_threshold_logic()
    if thresh:
        all_errors.extend(thresh)
        for t in thresh:
            print(f'  ✗ {t}')
    else:
        print('  ✓ כל הספים נכונים')
        print('    שלב1: 4NT אם 18+ / 17+קצר, אחרת 4M')
        print('    שלב2: 6M רק אם kc≥5 AND combined≥33')
        print('    stop_bid: 5M אם גבוה מתגובה, אחרת Pass')

    per = n // 4
    suits = [('H', '♥'), ('S', '♠'), ('D', '♦'), ('C', '♣')]
    for i, (trump, sym) in enumerate(suits, 2):
        count = per if i < 5 else n - 3 * per
        _section(f'[{i}] {count} ידיים — שליט {sym}')
        _run_trump(trump, count, all_errors)

    # ── סיכום ────────────────────────────────────────────────────────────
    print()
    print(sep)
    total_e = len(all_errors)
    if total_e == 0:
        print('  ✓ עבר הכל — 0 שגיאות')
    else:
        print(f'  ✗ {total_e} שגיאות סה"כ')
    print(sep)

    return total_e


def _run_trump(trump, count, all_errors):
    t = _S[trump]
    first_counts = Counter()
    second_counts = Counter()
    errors = []
    deal_failures = 0

    # מעקב combined לפי תוצאה
    slam_combined = []
    stop_combined = []
    game_combined = []

    for i in range(count):
        try:
            hands = deal_slam_major(trump)
        except RuntimeError:
            deal_failures += 1
            continue

        try:
            first, hn, hs, combined, total_kc = check_hand(hands, trump, i, errors)
            first_counts[first] += 1

            if first == '4NT':
                n = hands['N']
                n_response, _, _ = rkcb_response(n, trump)
                n_kc = key_cards(n, trump)
                s_kc = key_cards(hands['S'], trump)
                dp = _dist_points(hands['S'], trump)
                second = _correct_second(n_kc, s_kc, hn, hs, t, n_response, hands['S'], trump)
                second_counts[second] += 1
                combined_adj = combined + dp
                if second.startswith('6'):
                    slam_combined.append(combined_adj)
                else:
                    stop_combined.append(combined_adj)
            else:
                game_combined.append(combined)
        except Exception as e:
            errors.append(f'#{i}: חריגה — {e}')

    ok = sum(first_counts.values())
    print(f'  ידיים תקינות: {ok}/{count}')
    if deal_failures:
        pct = 100 * deal_failures / count
        w = '⚠' if pct < 5 else '✗'
        print(f'  {w} כשלי deal: {deal_failures} ({pct:.1f}%)')

    print(f'\n  שלב 1 — הכרזה ראשונה:')
    if first_counts:
        print(_bar(first_counts, ok))

    asked = first_counts.get('4NT', 0)
    if asked:
        print(f'\n  שלב 2 — אחרי 4NT ({asked} ידיים):')
        print(_bar(second_counts, asked))

    # סטטיסטיקות combined
    def _avg(lst):
        return f'{sum(lst)/len(lst):.1f}' if lst else '-'

    print(f'\n  ממוצע combined:')
    print(f'    4M   (game): {_avg(game_combined)}  ({len(game_combined)} ידיים)')
    print(f'    4NT→6M:      {_avg(slam_combined)}  ({len(slam_combined)} ידיים)')
    print(f'    4NT→עצור:   {_avg(stop_combined)}  ({len(stop_combined)} ידיים)')

    # בדיקת כלל 33
    bad33 = [c for c in slam_combined if c < 33]
    if bad33:
        errors.append(f'6{t} עם פחות מ-33 נק: {len(bad33)} מקרים (min={min(bad33)})')

    if errors:
        uniq = sorted(set(errors))
        print(f'\n  ✗ {len(errors)} שגיאות ({len(uniq)} ייחודיות):')
        for e in uniq[:10]:
            print(f'    • {e}')
        if len(uniq) > 10:
            print(f'    ... ועוד {len(uniq) - 10}')
        all_errors.extend(errors)
    else:
        print(f'\n  ✓ אין שגיאות לוגיות')


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    sys.exit(0 if run(n) == 0 else 1)
