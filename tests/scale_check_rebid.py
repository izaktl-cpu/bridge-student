"""
scale_check_rebid.py — בדיקה עצמאית של opener_rebid לפתיחה במינורים.
משווה ה-engine מול כללים עצמאיים. מדפיס תיקונים נדרשים — לא מחיל אוטומטית.

הרצה: python tests/scale_check_rebid.py [n]
"""
import sys, os, random
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_student_opens_minor
from engine.response import respond_minor
from engine.rebid import opener_rebid
from engine.scoring import hcp, distribution, has_stopper
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


# ── לוגיקה עצמאית לפי הטבלה ────────────────────────────────────────────────

def _all_stopped(hand, exclude):
    """עוצרים בכל הסדרות מלבד הסדרה שמוחרגת."""
    return all(has_stopper(hand, s) for s in ['H', 'S', 'C', 'D'] if s != exclude)


def _independent_rebid(hand, open_suit, north_bid):
    """
    מחשב עצמאית את ריבאד הפותח לפי הטבלה המאושרת.
    מחזיר (bid, rule).
    """
    h   = hcp(hand)
    d   = distribution(hand)
    sym = _S[open_suit]
    nb  = north_bid

    # ── אחרי 1NT ──────────────────────────────────────────────────────────────
    if nb == '1NT':
        if h >= 19: return '3NT', '19+ → 3NT'
        if h >= 17: return '2NT', '17-18 → 2NT'
        return 'Pass', '12-16 → Pass'

    # ── אחרי 2NT ──────────────────────────────────────────────────────────────
    if nb == '2NT':
        if h >= 17: return '3NT', '17+ → 3NT'
        return 'Pass', '12-16 → Pass'

    # ── אחרי תמיכה 3♣/3♦ (לימיט ריס) ────────────────────────────────────────
    if nb in ('3♣', '3♦'):
        if h >= 14 and _all_stopped(hand, open_suit):
            return '3NT', '14+ עם עוצרים → 3NT'
        return 'Pass', '12-13 או ללא עוצרים → Pass'

    # ── אחרי תמיכה 2♣/2♦ ─────────────────────────────────────────────────────
    if nb in ('2♣', '2♦'):
        if h >= 19 and _all_stopped(hand, open_suit):
            return '3NT', '19+ עם עוצרים → 3NT'
        if h >= 17 and _all_stopped(hand, open_suit):
            return '2NT', '17-18 עם עוצרים → 2NT'
        return 'Pass', '12-16 → Pass'

    # ── אחרי 1♥ / 1♠ ──────────────────────────────────────────────────────────
    if nb in ('1♥', '1♠'):
        resp_suit = 'H' if nb == '1♥' else 'S'
        resp_sym  = _S[resp_suit]
        fit = d.get(resp_suit, 0)
        if fit >= 4:
            if h >= 18: return f'4{resp_sym}', f'18+ עם 4+ {resp_sym} → 4{resp_sym}'
            if h >= 15: return f'3{resp_sym}', f'15-17 עם 4+ {resp_sym} → 3{resp_sym}'
            return f'2{resp_sym}', f'12-14 עם 4+ {resp_sym} → 2{resp_sym}'
        # ללא התאמה — הכרזה הכי נמוכה
        # אחרי 1♥ — אפשר להראות 4♠ ברמה 1 (up-the-line)
        if resp_suit == 'H' and d.get('S', 0) >= 4:
            return '1♠', '4+ ♠ אחרי 1♥ → 1♠ up-the-line'
        if d.get(open_suit, 0) >= 5:
            return f'2{_S[open_suit]}', f'5+ קלפי {_S[open_suit]} → 2{_S[open_suit]}'
        return '1NT', 'ללא התאמה, מאוזן → 1NT'

    # ── אחרי 1♦ (תגובה ל-1♣) ───────────────────────────────────────────────
    if nb == '1♦' and open_suit == 'C':
        if d.get('H', 0) >= 4:
            return '1♥', '4+ ♥ → 1♥'
        if d.get('S', 0) >= 4:
            return '1♠', '4+ ♠ → 1♠'
        if d.get('C', 0) >= 5:
            return '2♣', '5+ ♣ → 2♣'
        return '1NT', 'מאוזן → 1NT'

    # ── חוזה סופי ────────────────────────────────────────────────────────────
    if nb == '3NT':
        return 'Pass', 'חוזה סופי → Pass'

    # ── שאר המקרים — לא מכוסים בטבלה ──────────────────────────────────────────
    return None, 'לא מכוסה בטבלה'


# ── Runner ────────────────────────────────────────────────────────────────────

def run(n=1000):
    errors   = []
    skipped  = 0
    checked  = 0

    for i in range(n):
        minor = random.choice(['C', 'D'])
        try:
            hands = deal_student_opens_minor(minor)
            s     = hands['S']
            h     = hcp(s)
            sym   = _S[minor]

            north_bid, _ = respond_minor(hands['N'], minor)
            engine_bid, _ = opener_rebid(s, f'1{sym}', north_bid)

            expected, rule = _independent_rebid(s, minor, north_bid)
            if expected is None:
                skipped += 1
                continue

            checked += 1
            if engine_bid != expected:
                errors.append({
                    'i':        i + 1,
                    'minor':    sym,
                    'hcp':      h,
                    'north':    north_bid,
                    'engine':   engine_bid,
                    'expected': expected,
                    'rule':     rule,
                })
        except Exception as e:
            errors.append({'i': i + 1, 'err': str(e)})

    sep = '─' * 55
    status = '✓' if not errors else '✗'
    print(sep)
    print(f' scale_check_rebid  |  {n} ידיות  {status}')
    print(sep)
    print(f'  נבדקו: {checked}  |  דולגו (לא בטבלה): {skipped}')

    if not errors:
        print('  ✓ אין שגיאות')
    else:
        print(f'  ✗ שגיאות: {len(errors)}')
        print()
        seen = set()
        for e in errors:
            if 'err' in e:
                print(f'  יד {e["i"]:4d}: חריגה — {e["err"]}')
                continue
            key = (e['north'], e['engine'], e['expected'])
            if key in seen:
                continue
            seen.add(key)
            print(f'  פתיחה 1{e["minor"]}  |  N ענה {e["north"]}  |  HCP={e["hcp"]}')
            print(f'    engine החזיר: {e["engine"]}')
            print(f'    צריך להיות:  {e["expected"]}  ({e["rule"]})')
            print(f'    >>> תיקון נדרש ב-engine/rebid.py: לשנות את הענף "{e["north"]}" כך ש-{e["rule"]}')
            print()

    print(sep)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    run(n)
