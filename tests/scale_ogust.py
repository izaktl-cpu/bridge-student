"""
סקייל בדיקה לשיעור 11 — Ogust.

בודק:
  1. אילוצי ה-deal (S, N, יריבים)
  2. חישוב _calc_ogust
  3. חישוב _north_tricks
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
    '3♣':  '6-7 נקודות מפוזרות',
    '3♦':  '6-7 נקודות בסדרה המוכרזת',
    '3♥':  '8-9 נקודות מפוזרות',
    '3♠':  '8-9 נקודות מרוכזות בסדרה',
    '3NT': 'AKQ בסדרה',
}


# ─── לוגיקה (מועתקת מ-lesson_ogust.py) ─────────────────────────────────────

def _calc_ogust(hand, major):
    honors = sum(1 for c in hand if c[1] == major and c[0] in ('A', 'K', 'Q'))
    if honors == 3:
        return '3NT'
    h = hcp(hand)
    # מרוכז = אין שום מכובד (A/K/Q/J) מחוץ לשליט; מפוזר = יש מכובד כלשהו בחוץ, כולל J
    outside = sum(1 for c in hand if c[1] != major and c[0] in ('A', 'K', 'Q', 'J'))
    concentrated = outside == 0
    if h <= 7:
        return '3♦' if concentrated else '3♣'
    else:
        return '3♠' if concentrated else '3♥'


_BID_RANK = {'3♣': 0, '3♦': 1, '3♥': 2, '3♠': 3, '3NT': 4}


def _partscore_bid(major, ogust_response):
    """הזמנת החלק-משחק של N: 3 בשליט אם חוקי מעל תשובת האוגוסט, אחרת Pass."""
    target = f'3{_S[major]}'
    if _BID_RANK[target] > _BID_RANK.get(ogust_response, -1):
        return target
    return 'Pass'


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
    if suit_len(n, major) < 2:
        return f'3{sym}'
    # הכל לפי לקיחות גבוהות (sure_tricks): 4=הזמנה, 5=משחק, 6+=שאלת אסים
    st = sure_tricks(n)
    if st >= 6:
        return '4NT'
    if st >= 5:
        return f'4{sym}'
    return _partscore_bid(major, ogust_response)


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
    if not n_fit:
        errors.append(f'#{idx}: N אין תמיכה 2+ במיגור {sym}')

    # ── עקביות אוגוסט ─────────────────────────────────────────────────────────
    # מרוכז = אין שום מכובד (A/K/Q/J) מחוץ לשליט; מפוזר = יש מכובד כלשהו בחוץ, כולל J
    outside      = sum(1 for c in s if c[1] != major and c[0] in ('A', 'K', 'Q', 'J'))
    concentrated = outside == 0
    ogust = _calc_ogust(s, major)
    if ogust == '3♣':
        if not (6 <= hs <= 7) or concentrated:
            errors.append(f'#{idx}: 3♣ שגוי — HCP={hs} מרוכז={concentrated}')
    elif ogust == '3♦':
        if not (6 <= hs <= 7) or not concentrated or honors_akq == 3:
            errors.append(f'#{idx}: 3♦ שגוי — HCP={hs} מרוכז={concentrated} AKQ בשליט={honors_akq}')
    elif ogust == '3♥':
        if not (8 <= hs <= 9) or concentrated:
            errors.append(f'#{idx}: 3♥ שגוי — HCP={hs} מרוכז={concentrated}')
    elif ogust == '3♠':
        if not (8 <= hs <= 9) or not concentrated or honors_akq == 3:
            errors.append(f'#{idx}: 3♠ שגוי — HCP={hs} מרוכז={concentrated} AKQ בשליט={honors_akq}')
    elif ogust == '3NT':
        if honors_akq != 3:
            errors.append(f'#{idx}: 3NT שגוי — AKQ={honors_akq} (צ"ל 3)')

    # ── לקיחות גבוהות N (sure_tricks) ─────────────────────────────────────────
    et = sure_tricks(n)
    if et < 0 or et > 13:
        errors.append(f'#{idx}: sure_tricks={et} חריג')

    # ── החלטת N ───────────────────────────────────────────────────────────────
    # כלל שטוח לפי לקיחות גבוהות: 4=הזמנה, 5=4M משחק, 6+=4NT שאלת אסים.
    # הזמנה = 3 בשליט, או Pass אם הפותח כבר בגובה 3 בשליט או מעל (למשל 3♥ בשליט לב).
    n_bid = _north_final(ogust, n, major)
    valid = {f'3{sym}', f'4{sym}', '4NT', 'Pass'}
    if n_bid not in valid:
        errors.append(f'#{idx}: N הכריז {n_bid} שאינו ב-{valid}')

    if not n_fit:
        exp = _partscore_bid(major, ogust)
    elif n_st >= 6:
        exp = '4NT'
    elif n_st >= 5:
        exp = f'4{sym}'
    else:
        exp = _partscore_bid(major, ogust)
    if n_bid != exp:
        errors.append(f'#{idx}: N הכריז {n_bid} צ"ל {exp} (sure_tricks={n_st})')

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
