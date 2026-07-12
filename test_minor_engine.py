# -*- coding: utf-8 -*-
"""
בדיקה שיטתית של engine המינורים:
  - respond_minor אחרי 1♣ ו-1♦ — כל מקרי הקצה
  - opener_rebid לאחר כל תגובה אפשרית
  - עקביות בין engine לטבלאות _rebid_rows
"""

import sys, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine.response import respond_minor
from engine.rebid import opener_rebid
from engine.scoring import hcp as get_hcp, distribution, is_balanced

# ─── בנאי ידיים ──────────────────────────────────────────────────────────────
_DECKS = {
    'S': 'AS KS QS JS TS 9S 8S 7S 6S 5S 4S 3S 2S'.split(),
    'H': 'AH KH QH JH TH 9H 8H 7H 6H 5H 4H 3H 2H'.split(),
    'D': 'AD KD QD JD TD 9D 8D 7D 6D 5D 4D 3D 2D'.split(),
    'C': 'AC KC QC JC TC 9C 8C 7C 6C 5C 4C 3C 2C'.split(),
}
_HCP_VAL = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}


def build(s, h, d, c, target_hcp=0):
    """בונה יד בת 13 קלפים עם אורכי צבעים וHCP נתונים."""
    assert s + h + d + c == 13, f'סה״כ {s+h+d+c} != 13'
    result = []
    remaining = target_hcp
    for suit, n in [('S', s), ('H', h), ('D', d), ('C', c)]:
        cards = []
        for card in _DECKS[suit]:
            if len(cards) == n:
                break
            val = _HCP_VAL.get(card[0], 0)
            if val > 0:
                if remaining >= val:
                    cards.append(card)
                    remaining -= val
            else:
                cards.append(card)
        # מלא בקלפים קטנים אם חסרים
        for card in reversed(_DECKS[suit]):
            if len(cards) == n:
                break
            if card not in cards:
                cards.append(card)
        result.extend(cards)
    return result


def info(hand):
    h = get_hcp(hand)
    d = distribution(hand)
    b = is_balanced(hand)
    return f'hcp={h} dist={d["S"]}-{d["H"]}-{d["D"]}-{d["C"]} bal={b}'


# ─── ריצת בדיקות ─────────────────────────────────────────────────────────────
failures = []
passes   = 0


def chk(label, got_tuple, want_bid, hand=None):
    global passes
    bid, why = got_tuple
    ok = (bid == want_bid)
    if ok:
        passes += 1
    else:
        hand_info = f'  [{info(hand)}]' if hand else ''
        failures.append(f'FAIL  {label}{hand_info}')
        failures.append(f'      got={bid!r}  ({why})')
        failures.append(f'      want={want_bid!r}')
    return ok


# ════════════════════════════════════════════════════════
print('══════════════════════════════════════════════')
print('  respond_minor אחרי 1♣')
print('══════════════════════════════════════════════')

# Pass (0-5 HCP)
h0 = build(3, 3, 4, 3, 0)
chk('1C: 0hcp → Pass', respond_minor(h0, 'C'), 'Pass', h0)

h1 = build(3, 3, 4, 3, 5)
chk('1C: 5hcp → Pass', respond_minor(h1, 'C'), 'Pass', h1)

# 1♠ — 4+ ספיידס
h2 = build(4, 3, 3, 3, 7)
chk('1C: 4♠ 7hcp → 1♠', respond_minor(h2, 'C'), '1♠', h2)

# 1♥ — 4+ הארטס, ללא 4+ ספיידס
h3 = build(2, 4, 4, 3, 7)
chk('1C: 4♥+4♦ → 1♦ (up the line, ♦ לפני ♥)', respond_minor(h3, 'C'), '1♦', h3)

# 1♦ — 4+ יהלומים, ללא מיגור
h4 = build(2, 3, 5, 3, 7)
chk('1C: 4+♦ no major → 1♦', respond_minor(h4, 'C'), '1♦', h4)

# 1NT — מאוזן 6-10, ללא 4+ בצבע
h5 = build(3, 3, 3, 4, 8)
chk('1C: balanced 8hcp → 1NT', respond_minor(h5, 'C'), '1NT', h5)

# 2♣ — לא מאוזן, 3+ קלפי ♣, 6-10
h6 = build(2, 2, 3, 6, 8)
chk('1C: 6♣ nonbal 8hcp → 2♣', respond_minor(h6, 'C'), '2♣', h6)

h7 = build(1, 3, 3, 6, 9)   # 6 קלפי ♣, לא מאוזן (1-3-3-6)
chk('1C: 6♣ nonbal2 9hcp → 2♣', respond_minor(h7, 'C'), '2♣', h7)

# 2NT — מאוזן 11-12
h8 = build(3, 3, 3, 4, 11)
chk('1C: balanced 11hcp → 2NT', respond_minor(h8, 'C'), '2NT', h8)

h9 = build(3, 3, 3, 4, 12)
chk('1C: balanced 12hcp → 2NT', respond_minor(h9, 'C'), '2NT', h9)

# 3NT — מאוזן 13+
h10 = build(3, 3, 3, 4, 13)
chk('1C: balanced 13hcp → 3NT', respond_minor(h10, 'C'), '3NT', h10)

# עדיפויות
h11 = build(4, 4, 2, 3, 9)
chk('1C priority: 4♠+4♥ → 1♥ (up the line)', respond_minor(h11, 'C'), '1♥', h11)

h12 = build(2, 4, 4, 3, 9)
chk('1C priority: 4♥+4♦ → 1♦ (up the line)', respond_minor(h12, 'C'), '1♦', h12)

h13 = build(3, 3, 4, 3, 9)  # 4♦, balanced
chk('1C priority: 4♦ before bal → 1♦', respond_minor(h13, 'C'), '1♦', h13)

# 2♣ לא מוחזר כשמאוזן (מאוזן + קלפי ♣ → 1NT)
h14 = build(3, 3, 2, 5, 8)  # 5♣ מאוזן → 2♣ (תמיכה קודמת ל-1NT)
chk('1C: 5♣ balanced 8hcp → 2♣', respond_minor(h14, 'C'), '2♣', h14)

# 2NT — חצי-מאוזן (6-3-2-2), 11-12 → מעדיפים NT על העלאת מינור
h15 = build(2, 2, 3, 6, 11)  # 6♣, חצי-מאוזן, 11 נקודות
chk('1C: 6♣ semibal 11hcp → 2NT', respond_minor(h15, 'C'), '2NT', h15)

h16 = build(2, 2, 3, 6, 12)  # 6♣, חצי-מאוזן, 12 נקודות
chk('1C: 6♣ semibal 12hcp → 2NT', respond_minor(h16, 'C'), '2NT', h16)

h17 = build(2, 3, 2, 6, 11)  # 6♣, חצי-מאוזן (2-3-2-6)
chk('1C: 6♣ semibal2 11hcp → 2NT', respond_minor(h17, 'C'), '2NT', h17)

# 3NT — לא מאוזן, 5+ קלפי ♣, 13+
h18 = build(2, 2, 3, 6, 13)
chk('1C: 6♣ nonbal 13hcp → 3NT', respond_minor(h18, 'C'), '3NT', h18)

h19 = build(1, 3, 3, 6, 14)
chk('1C: 6♣ nonbal 14hcp → 3NT', respond_minor(h19, 'C'), '3NT', h19)


# ════════════════════════════════════════════════════════
print()
print('══════════════════════════════════════════════')
print('  respond_minor אחרי 1♦')
print('══════════════════════════════════════════════')

# Pass
h20 = build(3, 3, 4, 3, 0)
chk('1D: 0hcp → Pass', respond_minor(h20, 'D'), 'Pass', h20)

# 1♠
h21 = build(4, 3, 3, 3, 7)
chk('1D: 4♠ → 1♠', respond_minor(h21, 'D'), '1♠', h21)

# 1♥ ללא 4+ ספיידס
h22 = build(2, 4, 4, 3, 7)
chk('1D: 4♥ no4♠ → 1♥', respond_minor(h22, 'D'), '1♥', h22)

# 1NT — מאוזן 6-10 (אין בדיקת יהלומים אחרי 1♦)
h23 = build(3, 3, 3, 4, 8)
chk('1D: balanced 8hcp → 1NT', respond_minor(h23, 'D'), '1NT', h23)

# 1NT גם עם 4♦ אם מאוזן (מאוזן קודם)
h24 = build(3, 3, 4, 3, 8)  # 3-3-4-3, מאוזן
chk('1D: 4♦ balanced 8hcp → 1NT (not 2♦)', respond_minor(h24, 'D'), '1NT', h24)

# 2♦ — לא מאוזן, 4+♦, 6-10
h25 = build(2, 2, 5, 4, 8)
chk('1D: 5♦ nonbal 8hcp → 2♦', respond_minor(h25, 'D'), '2♦', h25)

h26 = build(2, 2, 4, 5, 9)  # 4♦, חצי-מאוזן (2-2-4-5) → מעדיף NT
chk('1D: 4♦ semibal 9hcp → 1NT', respond_minor(h26, 'D'), '1NT', h26)

# 3♦ — לא מאוזן, 4+♦, 11-12
h27 = build(2, 2, 5, 4, 11)
chk('1D: 5♦ nonbal 11hcp → 3♦', respond_minor(h27, 'D'), '3♦', h27)

h28 = build(2, 2, 4, 5, 12)
chk('1D: 4♦ nonbal 12hcp → 3♦', respond_minor(h28, 'D'), '3♦', h28)

# 2NT — מאוזן 11-12
h29 = build(3, 3, 3, 4, 11)
chk('1D: balanced 11hcp → 2NT', respond_minor(h29, 'D'), '2NT', h29)

# 3NT — מאוזן 13+
h30 = build(3, 3, 3, 4, 13)
chk('1D: balanced 13hcp → 3NT', respond_minor(h30, 'D'), '3NT', h30)

# חצי-מאוזן (6-3-2-2), 11-12, ללא 4+♦ → מעדיף NT על סדרה חדשה
h31 = build(2, 2, 3, 6, 11)
chk('1D: 6♣ semibal 11hcp → 2NT', respond_minor(h31, 'D'), '2NT', h31)

# עדיפות: 4+♦ לפני 2♣
h32 = build(2, 2, 4, 5, 11)
chk('1D priority: 4♦ over 5♣ 11hcp → 3♦', respond_minor(h32, 'D'), '3♦', h32)


# ════════════════════════════════════════════════════════
print()
print('══════════════════════════════════════════════')
print('  opener_rebid אחרי 1♣')
print('══════════════════════════════════════════════')

# ─ 1♣ → 1NT ─────────────────────────────────────
o1 = build(3, 3, 3, 4, 12)
chk('1C→1NT: 12hcp=Pass', opener_rebid(o1, '1♣', '1NT'), 'Pass', o1)

o2 = build(2, 3, 3, 5, 15)  # 15hcp → 2NT
chk('1C→1NT: 15hcp=2NT', opener_rebid(o2, '1♣', '1NT'), '2NT', o2)

o3 = build(3, 3, 3, 4, 15)  # 15hcp → 2NT
chk('1C→1NT: 15hcp 4♣=2NT', opener_rebid(o3, '1♣', '1NT'), '2NT', o3)

o4 = build(2, 3, 3, 5, 18)  # 18hcp → 3NT
chk('1C→1NT: 18hcp=3NT', opener_rebid(o4, '1♣', '1NT'), '3NT', o4)

# ─ 1♣ → 1♦ ─────────────────────────────────────
o5 = build(3, 3, 4, 3, 12)  # 4♦, 12hcp → 2♦
chk('1C→1D: 12hcp 4♦=2♦', opener_rebid(o5, '1♣', '1♦'), '2♦', o5)

o6 = build(3, 3, 4, 3, 17)  # 4♦, 17hcp → 2♦ (NOT 3♦)
chk('1C→1D: 17hcp 4♦=2♦ (not 3♦)', opener_rebid(o6, '1♣', '1♦'), '2♦', o6)

o7 = build(2, 3, 3, 5, 14)  # 5♣, no 4♦
chk('1C→1D: 5♣ no4♦=2♣', opener_rebid(o7, '1♣', '1♦'), '2♣', o7)

o8 = build(3, 3, 3, 4, 18)  # 4♣, no 4♦, 18hcp → 2NT
chk('1C→1D: 18hcp no4♦ no5♣=2NT', opener_rebid(o8, '1♣', '1♦'), '2NT', o8)

o9 = build(3, 3, 3, 4, 12)  # 4♣, no 4♦, 12hcp → 1NT
chk('1C→1D: 12hcp no4♦ no5♣=1NT', opener_rebid(o9, '1♣', '1♦'), '1NT', o9)

# ─ 1♣ → 2♣ (6-10, תמיכה פשוטה) ─────────────────
o10 = build(3, 3, 3, 4, 12)
chk('1C→2C: 12hcp=Pass', opener_rebid(o10, '1♣', '2♣'), 'Pass', o10)

o11 = build(3, 3, 3, 4, 15)
chk('1C→2C: 15hcp=3♣', opener_rebid(o11, '1♣', '2♣'), '3♣', o11)

o12 = build(3, 3, 3, 4, 17)  # 17hcp → 3♣ (15-17)
chk('1C→2C: 17hcp=3♣', opener_rebid(o12, '1♣', '2♣'), '3♣', o12)

o13 = build(2, 2, 3, 6, 17)  # 17hcp → 3♣
chk('1C→2C: 17hcp nonbal=3♣', opener_rebid(o13, '1♣', '2♣'), '3♣', o13)

o14 = build(3, 3, 3, 4, 19)
chk('1C→2C: 19hcp=3NT', opener_rebid(o14, '1♣', '2♣'), '3NT', o14)

# ─ 1♣ → 2NT (11-12) ─────────────────────────────
o15 = build(3, 3, 3, 4, 12)
chk('1C→2NT: 12hcp=Pass', opener_rebid(o15, '1♣', '2NT'), 'Pass', o15)

o16 = build(3, 3, 3, 4, 15)
chk('1C→2NT: 15hcp=3NT', opener_rebid(o16, '1♣', '2NT'), '3NT', o16)

# ─ 1♣ → 3♣ (לימיט, 11-12) ───────────────────────
o17 = build(3, 3, 3, 4, 12)
chk('1C→3C: 12hcp=Pass', opener_rebid(o17, '1♣', '3♣'), 'Pass', o17)

o18 = build(3, 3, 3, 4, 15)
chk('1C→3C: 15hcp=3NT', opener_rebid(o18, '1♣', '3♣'), '3NT', o18)

o19 = build(2, 2, 3, 6, 17)  # לא מאוזן, 17hcp
chk('1C→3C: 17hcp=3NT', opener_rebid(o19, '1♣', '3♣'), '3NT', o19)

# ─ 1♣ → 3NT ──────────────────────────────────────
o20 = build(3, 3, 3, 4, 15)
chk('1C→3NT: Pass', opener_rebid(o20, '1♣', '3NT'), 'Pass', o20)


# ════════════════════════════════════════════════════════
print()
print('══════════════════════════════════════════════')
print('  opener_rebid אחרי 1♦')
print('══════════════════════════════════════════════')

# ─ 1♦ → 1NT ─────────────────────────────────────
d1 = build(3, 3, 4, 3, 12)
chk('1D→1NT: 12hcp=Pass', opener_rebid(d1, '1♦', '1NT'), 'Pass', d1)

d2 = build(2, 3, 5, 3, 15)  # 15hcp → 2NT
chk('1D→1NT: 15hcp=2NT', opener_rebid(d2, '1♦', '1NT'), '2NT', d2)

d3 = build(3, 3, 4, 3, 15)  # 15hcp → 2NT
chk('1D→1NT: 15hcp 4♦=2NT', opener_rebid(d3, '1♦', '1NT'), '2NT', d3)

d4 = build(2, 3, 5, 3, 18)  # 18hcp → 3NT
chk('1D→1NT: 18hcp=3NT', opener_rebid(d4, '1♦', '1NT'), '3NT', d4)

# ─ 1♦ → 2♦ (6-10, תמיכה פשוטה) ─────────────────
d5 = build(3, 3, 4, 3, 12)
chk('1D→2D: 12hcp=Pass', opener_rebid(d5, '1♦', '2♦'), 'Pass', d5)

d6 = build(3, 3, 4, 3, 15)
chk('1D→2D: 15hcp=3♦', opener_rebid(d6, '1♦', '2♦'), '3♦', d6)

d7 = build(3, 3, 4, 3, 17)  # 17hcp → 3♦ (15-17)
chk('1D→2D: 17hcp=3♦', opener_rebid(d7, '1♦', '2♦'), '3♦', d7)

d8 = build(2, 2, 5, 4, 17)  # 17hcp → 3♦
chk('1D→2D: 17hcp nonbal=3♦', opener_rebid(d8, '1♦', '2♦'), '3♦', d8)

d9 = build(2, 2, 5, 4, 19)
chk('1D→2D: 19hcp nonbal=3NT', opener_rebid(d9, '1♦', '2♦'), '3NT', d9)

# ─ 1♦ → 3♦ (לימיט, 11-12) ───────────────────────
d10 = build(3, 3, 4, 3, 12)
chk('1D→3D: 12hcp=Pass', opener_rebid(d10, '1♦', '3♦'), 'Pass', d10)

d11 = build(3, 3, 4, 3, 15)
chk('1D→3D: 15hcp=3NT', opener_rebid(d11, '1♦', '3♦'), '3NT', d11)

d12 = build(2, 2, 5, 4, 17)  # לא מאוזן
chk('1D→3D: 17hcp nonbal=3NT', opener_rebid(d12, '1♦', '3♦'), '3NT', d12)

# ─ 1♦ → 2♣ (5+♣, 11+, צבע חדש ברמה 2) ───────────
d13 = build(2, 3, 4, 4, 14)  # 4♦
chk('1D→2C: 4♦=2♦', opener_rebid(d13, '1♦', '2♣'), '2♦', d13)

d14 = build(2, 3, 5, 3, 14)  # 5♦
chk('1D→2C: 5♦=2♦', opener_rebid(d14, '1♦', '2♣'), '2♦', d14)

d15 = build(2, 3, 4, 4, 18)  # 4♦, 18hcp → 2♦ (NOT 2NT)
chk('1D→2C: 18hcp 4♦=2♦ (not 2NT)', opener_rebid(d15, '1♦', '2♣'), '2♦', d15)

d16 = build(3, 3, 3, 4, 15)  # אין 4+♦ → 2NT
chk('1D→2C: no4♦=2NT', opener_rebid(d16, '1♦', '2♣'), '2NT', d16)

# ─ 1♦ → 2NT (11-12) ─────────────────────────────
d17 = build(3, 3, 4, 3, 12)
chk('1D→2NT: 12hcp=Pass', opener_rebid(d17, '1♦', '2NT'), 'Pass', d17)

d18 = build(3, 3, 4, 3, 15)
chk('1D→2NT: 15hcp=3NT', opener_rebid(d18, '1♦', '2NT'), '3NT', d18)

# ─ 1♦ → 3NT ──────────────────────────────────────
d19 = build(3, 3, 4, 3, 15)
chk('1D→3NT: Pass', opener_rebid(d19, '1♦', '3NT'), 'Pass', d19)

# ─ 1♦ → 1♥ ──────────────────────────────────────
d20 = build(2, 4, 4, 3, 14)  # פותח עם 4♥
chk('1D→1H: opener 4♥=2♥', opener_rebid(d20, '1♦', '1♥'), '2♥', d20)

d21 = build(3, 2, 5, 3, 14)  # פותח ללא 4♥, עם 5♦
chk('1D→1H: no4♥ 5♦=2♦', opener_rebid(d21, '1♦', '1♥'), '2♦', d21)

# ─ 1♦ → 1♠ ──────────────────────────────────────
d22 = build(4, 2, 4, 3, 14)  # פותח עם 4♠
chk('1D→1S: opener 4♠=2♠', opener_rebid(d22, '1♦', '1♠'), '2♠', d22)

d23 = build(3, 2, 5, 3, 14)  # פותח ללא 4♠, עם 5♦
chk('1D→1S: no4♠ 5♦=2♦', opener_rebid(d23, '1♦', '1♠'), '2♦', d23)


# ════════════════════════════════════════════════════════
print()
print('══════════════════════════════════════════════')
print(f'  תוצאות: {passes} עברו, {len([f for f in failures if f.startswith("FAIL")])} נכשלו')
print('══════════════════════════════════════════════')

if failures:
    print()
    for line in failures:
        print(line)
else:
    print()
    print('  כל הבדיקות עברו בהצלחה!')
