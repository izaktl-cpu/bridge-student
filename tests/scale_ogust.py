"""
סקייל בדיקה לשיעור 11 — Ogust.

בודק:
  1. אילוצי ה-deal (S, N, יריבים)
  2. חישוב _calc_ogust
  3. חישוב _effective_tricks
  4. החלטת N (_north_final)
  5. עקביות כללית

שימוש:
    python tests/scale_ogust.py          # 2000 ידיות
    python tests/scale_ogust.py 500
    python tests/scale_ogust.py 2000 -v  # מפורט (5 ידיות ראשונות)
"""

import sys, os, random
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_ogust
from engine.scoring import hcp, suit_len, sure_tricks
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS

_EXPLAIN = {
    '3♣':  '6–7 נק׳ מפוזרות',
    '3♦':  '6–7 נק׳ מרוכזות',
    '3♥':  '8–9 נק׳ מפוזרות',
    '3♠':  '8–9 נק׳ מרוכזות',
    '3NT': 'AKQ בסדרה',
}


# ─── לוגיקה (מועתקת מ-lesson_ogust.py) ─────────────────────────────────────

def _calc_ogust(hand, major):
    h      = hcp(hand)
    honors = sum(1 for c in hand if c[1] == major and c[0] in ('A', 'K', 'Q'))
    if honors == 3:
        return '3NT'
    concentrated = honors >= 2
    if h <= 7:
        return '3♦' if concentrated else '3♣'
    else:
        return '3♠' if concentrated else '3♥'


def _suit_tricks(hand, suit):
    order = ['A', 'K', 'Q', 'J']
    top_idx = None
    for i, r in enumerate(order):
        if any(c[0] == r and c[1] == suit for c in hand):
            top_idx = i
            break
    if top_idx is None:
        return 0
    seq = 0
    for r in order[top_idx:]:
        if any(c[0] == r and c[1] == suit for c in hand):
            seq += 1
        else:
            break
    return max(0, seq - top_idx)


def _effective_tricks(n, major):
    total = sum(1 for c in n if c[1] == major and c[0] in ('A', 'K', 'Q', 'J'))
    for suit in ['S', 'H', 'D', 'C']:
        if suit != major:
            total += _suit_tricks(n, suit)
    return total


def _strong_suits(hand):
    count = 0
    for suit in ['S', 'H', 'D', 'C']:
        if suit_len(hand, suit) >= 4:
            top = sum(1 for c in hand if c[1] == suit and c[0] in ('A', 'K', 'Q'))
            if top >= 2:
                count += 1
    return count


def _north_final(ogust_response, n, major):
    sym = _S[major]
    et  = _effective_tricks(n, major)
    fit = suit_len(n, major) >= 2 or _strong_suits(n) >= 2
    if not fit:
        return f'3{sym}'
    if ogust_response == '3♣':
        return f'4{sym}' if et >= 7 else f'3{sym}'
    elif ogust_response == '3♦':
        return f'4{sym}' if et >= 5 else f'3{sym}'
    elif ogust_response == '3♥':
        return f'4{sym}' if et >= 5 else f'3{sym}'
    else:  # 3♠, 3NT
        if et >= 6:
            return f'6{sym}'
        elif et >= 4:
            return f'4{sym}'
        else:
            return f'3{sym}'


# ─── בדיקה ──────────────────────────────────────────────────────────────────

def _check_one(hands, major, idx, errors):
    s   = hands['S']
    n   = hands['N']
    sym = _S[major]
    other_major = 'S' if major == 'H' else 'H'

    hs = hcp(s)
    hn = hcp(n)
    s_len        = suit_len(s, major)
    s_other_len  = suit_len(s, other_major)
    honors_akqj  = sum(1 for c in s if c[1] == major and c[0] in ('A', 'K', 'Q', 'J'))
    honors_akq   = sum(1 for c in s if c[1] == major and c[0] in ('A', 'K', 'Q'))
    n_st         = sure_tricks(n)
    n_fit        = suit_len(n, major) >= 2
    n_strong     = _strong_suits(n) >= 2

    # ── אילוצי S ──────────────────────────────────────────────────────────────
    if not (6 <= hs <= 9):
        errors.append(f'#{idx}: S HCP={hs} מחוץ לטווח 6-9')
    if s_len != 6:
        errors.append(f'#{idx}: S יש לו {s_len} קלפי {sym} (צ"ל 6)')
    if honors_akqj < 2:
        errors.append(f'#{idx}: S יש {honors_akqj} מכובדים AKQJ (מינ׳ 2)')
    if s_other_len >= 4:
        errors.append(f'#{idx}: S יש {s_other_len} קלפי {_S[other_major]} (אסור 4+)')

    # ── אילוצי N ──────────────────────────────────────────────────────────────
    if hn < 15:
        errors.append(f'#{idx}: N HCP={hn} פחות מ-15')
    if n_st < 4:
        errors.append(f'#{idx}: N sure_tricks={n_st} פחות מ-4')
    if not n_fit and not n_strong:
        errors.append(f'#{idx}: N אין fit ואין 2 סדרות חזקות')

    # ── עקביות אוגוסט ─────────────────────────────────────────────────────────
    ogust = _calc_ogust(s, major)
    if ogust == '3♣':
        if not (6 <= hs <= 7) or honors_akq >= 2:
            errors.append(f'#{idx}: 3♣ שגוי — HCP={hs} AKQ={honors_akq}')
    elif ogust == '3♦':
        if not (6 <= hs <= 7) or honors_akq < 2:
            errors.append(f'#{idx}: 3♦ שגוי — HCP={hs} AKQ={honors_akq}')
    elif ogust == '3♥':
        if not (8 <= hs <= 9) or honors_akq >= 2:
            errors.append(f'#{idx}: 3♥ שגוי — HCP={hs} AKQ={honors_akq}')
    elif ogust == '3♠':
        if not (8 <= hs <= 9) or honors_akq < 2 or honors_akq == 3:
            errors.append(f'#{idx}: 3♠ שגוי — HCP={hs} AKQ={honors_akq}')
    elif ogust == '3NT':
        if honors_akq != 3:
            errors.append(f'#{idx}: 3NT שגוי — AKQ={honors_akq} (צ"ל 3)')

    # ── עקביות _effective_tricks ──────────────────────────────────────────────
    et = _effective_tricks(n, major)
    if et < 0:
        errors.append(f'#{idx}: et={et} שלילי')
    if et > 13:
        errors.append(f'#{idx}: et={et} גבוה מדי')

    # בדיקת רכיב major: כל AKQJ = 1
    expected_major = sum(1 for c in n if c[1] == major and c[0] in ('A', 'K', 'Q', 'J'))
    got_major      = sum(1 for c in n if c[1] == major and c[0] in ('A', 'K', 'Q', 'J'))
    if expected_major != got_major:
        errors.append(f'#{idx}: חישוב major טעוי')

    # בדיקת רצף: כל סדרה אחרת ≤ 4
    for suit in ['S', 'H', 'D', 'C']:
        if suit != major:
            t = _suit_tricks(n, suit)
            if t < 0 or t > 4:
                errors.append(f'#{idx}: _suit_tricks({suit})={t} חריג')

    # ── החלטת N ───────────────────────────────────────────────────────────────
    n_bid = _north_final(ogust, n, major)
    valid = {f'3{sym}', f'4{sym}', f'6{sym}'}
    if n_bid not in valid:
        errors.append(f'#{idx}: N הכריז {n_bid} שאינו ב-{valid}')

    # אחרי 3NT — לפחות 4M (לא 3M)
    if ogust == '3NT' and n_bit_rank(n_bid) < n_bit_rank(f'4{sym}'):
        errors.append(f'#{idx}: אחרי 3NT N הכריז {n_bid} (צ"ל לפחות 4{sym})')

    return ogust, n_bid, et


def n_bit_rank(bid):
    order = {'3♣':0,'3♦':1,'3♥':2,'3♠':3,'3NT':4,
             '4♣':5,'4♦':6,'4♥':7,'4♠':8,'4NT':9,
             '5♣':10,'5♦':11,'5♥':12,'5♠':13,
             '6♣':14,'6♦':15,'6♥':16,'6♠':17,'6NT':18}
    return order.get(bid, -1)


# ─── הרצה ────────────────────────────────────────────────────────────────────

def run(n=2000, verbose=False):
    sep = '─' * 62
    errors     = []
    ogust_cnt  = Counter()
    nbid_cnt   = Counter()
    major_cnt  = Counter()
    et_sum     = 0
    done       = 0

    for i in range(n):
        major = random.choice(['H', 'S'])
        try:
            hands = deal_ogust(major)
            ogust, n_bid, et = _check_one(hands, major, i, errors)
            ogust_cnt[ogust] += 1
            nbid_cnt[n_bid]  += 1
            major_cnt[_S[major]] += 1
            et_sum += et
            done   += 1

            if verbose and i < 5:
                hs  = hcp(hands['S'])
                hn  = hcp(hands['N'])
                akq = sum(1 for c in hands['S'] if c[1] == major and c[0] in ('A','K','Q'))
                sym = _S[major]
                print(f'  #{i} ({sym}): S={hs}נק׳ AKQ={akq} → {ogust} ({_EXPLAIN[ogust]}) | '
                      f'N={hn}נק׳ et={et} → {n_bid}')
        except Exception as e:
            errors.append(f'#{i}: חריגה — {e}')

    print(sep)
    print(f' שיעור 11 — Ogust  |  {done}/{n} ידיות')
    print(sep)
    print(f'  ♥={major_cnt.get("♥",0)}  ♠={major_cnt.get("♠",0)}   '
          f'ממוצע et={et_sum/done:.1f}' if done else '')

    print()
    print('  תגובות S (אוגוסט):')
    for k in ['3♣','3♦','3♥','3♠','3NT']:
        v = ogust_cnt.get(k, 0)
        pct = 100*v/done if done else 0
        print(f'    {k:<6} {_EXPLAIN.get(k,""):<26} {v:>5}  ({pct:4.1f}%)')

    print()
    print('  הכרזות N:')
    for k, v in sorted(nbid_cnt.items(), key=lambda x: -x[1]):
        pct = 100*v/done if done else 0
        print(f'    {k:<8} {v:>5}  ({pct:4.1f}%)')

    print()
    if errors:
        print(f'  ✗ שגיאות: {len(errors)}')
        for e in errors[:25]:
            print(f'    • {e}')
        if len(errors) > 25:
            print(f'    ... ועוד {len(errors)-25}')
    else:
        print('  ✓ אין שגיאות')
    print(sep)
    return len(errors)


if __name__ == '__main__':
    args    = [a for a in sys.argv[1:] if a != '-v']
    verbose = '-v' in sys.argv[1:]
    n       = int(args[0]) if args else 2000
    sys.exit(run(n, verbose))
