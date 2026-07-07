"""
בדיקה שיטתית של שיעור 14 — מריץ 200 ידיים ומדווח על כל בעיה.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from engine.deal_constraints import deal_negative_double_phase1, deal_negative_double_phase2
from engine.negative_double import (s_response, opener_rebid,
                                    opener_after_natural, opener_after_cue)
from engine.opening import opening_bid as _opening_bid
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS
_RANK = {'C': 1, 'D': 2, 'H': 3, 'S': 4}
_SYM_MAP = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}

def _bid_suit(bid):
    for ch, s in _SYM_MAP.items():
        if ch in bid:
            return s
    return None

def _bid_level(bid):
    if bid and bid[0].isdigit():
        return int(bid[0])
    return 0

def _bid_rank(bid):
    """דירוג הכרזה לבדיקת עלייה."""
    if bid == 'Pass': return 0
    if bid == 'X': return 0
    lvl = _bid_level(bid)
    suit = _bid_suit(bid)
    if suit:
        return lvl * 5 + _RANK[suit]
    if 'NT' in bid:
        return lvl * 5 + 5
    return 0

errors = []

def check(cond, msg):
    if not cond:
        errors.append(msg)

# ── שלב 1 ────────────────────────────────────────────────────────────────────
print("בודק שלב 1...")
for i in range(200):
    try:
        hands = deal_negative_double_phase1()
    except RuntimeError as e:
        errors.append(f"שלב1 יד {i}: הגרלה נכשלה — {e}")
        continue

    n, e, s = hands['N'], hands['E'], hands['S']
    n_bid, _ = _opening_bid(n)
    n_suit = _bid_suit(n_bid)
    e_suits = [m for m in ['H','S'] if distribution(e)[m] >= 5]
    if not e_suits:
        errors.append(f"שלב1 יד {i}: E אין מיגור ל-overcall")
        continue
    e_suit = e_suits[0]
    e_bid = f'1{_S[e_suit]}'

    s_bid, s_expl = s_response(s, n_suit, e_suit, 1)

    # בדיקה: S לא מכריז מתחת לרמת ה-overcall
    if s_bid not in ('Pass', 'X') and _bid_rank(s_bid) <= _bid_rank(e_bid):
        errors.append(f"שלב1 יד {i}: S bid {s_bid} מתחת ל-{e_bid}")

    # בדיקה: ריבאד N אחרי X
    if s_bid == 'X':
        n_rbid, _ = opener_rebid(n, n_suit, e_suit, 1)
        if n_rbid == 'Pass':
            errors.append(f"שלב1 יד {i}: opener_rebid החזיר Pass אחרי X — N={hcp(n)}נק, {distribution(n)}")
        if n_rbid not in ('Pass','X') and _bid_rank(n_rbid) <= _bid_rank(e_bid):
            errors.append(f"שלב1 יד {i}: opener_rebid {n_rbid} מתחת ל-{e_bid}")

    # בדיקה: ריבאד N אחרי הכרזה טבעית
    s_suit = _bid_suit(s_bid)
    s_level = int(s_bid[0]) if s_bid and s_bid[0].isdigit() else 1
    if s_suit and s_suit != e_suit:
        n_rbid2, _ = opener_after_natural(n, n_suit, s_suit, s_level)
        if n_rbid2 not in ('Pass','X') and s_suit != n_suit:
            # N's rebid must be above s_bid
            if _bid_rank(n_rbid2) <= _bid_rank(s_bid):
                errors.append(f"שלב1 יד {i}: opener_after_natural {n_rbid2} מתחת ל-S:{s_bid} "
                               f"| n_suit={n_suit} s_suit={s_suit} N={distribution(n)}")
        if n_rbid2 not in ('Pass','X') and s_suit == n_suit:
            # כשS תמך בסדרת N, N צריך פס
            pass  # Pass is OK here

    # בדיקה: ריבאד N אחרי קיו
    if s_suit and s_suit == e_suit:
        n_rbid3, _ = opener_after_cue(n, n_suit, e_suit)
        if n_rbid3 not in ('Pass','X') and _bid_rank(n_rbid3) <= _bid_rank(s_bid):
            errors.append(f"שלב1 יד {i}: opener_after_cue {n_rbid3} מתחת ל-S:{s_bid}")

# ── שלב 2 ────────────────────────────────────────────────────────────────────
print("בודק שלב 2...")
for i in range(200):
    try:
        hands = deal_negative_double_phase2()
    except RuntimeError as e:
        errors.append(f"שלב2 יד {i}: הגרלה נכשלה — {e}")
        continue

    n, e = hands['N'], hands['E']
    n_bid, _ = _opening_bid(n)
    n_suit = _bid_suit(n_bid)
    e_suits = [m for m in ['H','S'] if distribution(e)[m] >= 5]
    if not e_suits:
        errors.append(f"שלב2 יד {i}: E אין מיגור")
        continue
    e_suit = e_suits[0]
    e_bid = f'1{_S[e_suit]}'

    n_rbid, _ = opener_rebid(n, n_suit, e_suit, 1)

    if n_rbid == 'Pass':
        errors.append(f"שלב2 יד {i}: opener_rebid=Pass | N={hcp(n)}נק, {distribution(n)} n_suit={n_suit} e_suit={e_suit}")
    if n_rbid not in ('Pass','X') and _bid_rank(n_rbid) <= _bid_rank(e_bid):
        errors.append(f"שלב2 יד {i}: opener_rebid {n_rbid} מתחת ל-{e_bid} | N={distribution(n)}")

# ── תוצאות ───────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
if not errors:
    print("✓ אין שגיאות!")
else:
    print(f"נמצאו {len(errors)} שגיאות:\n")
    for e in errors[:30]:
        print(" •", e)
    if len(errors) > 30:
        print(f"  ... ועוד {len(errors)-30}")
