# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from engine.overcall import get_overcall, respond_overcall

# ── get_overcall ────────────────────────────────────────────────────────────
oc_tests = [
    # QJT95 — Q+J=3 HCP בסדרה → Pass
    ('QJT95',  ['QS','JS','TS','9S','5S','AH','2H','KD','3D','2C','3C','4C','6C'], '1♥', 'Pass'),
    # KJT95 — K+J=4 HCP בסדרה, 2 יחידות ✓, 10 HCP סה״כ → 1♠
    ('KJT95',  ['KS','JS','TS','9S','5S','AH','2H','QD','3D','2C','3C','4C','6C'], '1♥', '1♠'),
    # AJT95 — A+J=5 HCP, 10 HCP סה״כ → 1♠
    ('AJT95',  ['AS','JS','TS','9S','5S','QH','2H','KD','3D','2C','3C','4C','6C'], '1♥', '1♠'),
    # J10984 — J=1 HCP בסדרה → Pass
    ('J10984', ['JS','TS','9S','8S','4S','AH','2H','KD','3D','2C','3C','4C','6C'], '1♥', 'Pass'),
    # AK432 — A+K=7 HCP, 9 HCP סה״כ → 1♠
    ('AK432',  ['AS','KS','4S','3S','2S','QH','2H','3D','4D','2C','3C','4C','6C'], '1♥', '1♠'),
]

print('=== get_overcall ===')
passed = 0
for name, hand, opening, expected in oc_tests:
    bid, _ = get_overcall(hand, opening)
    ok = bid == expected
    if ok:
        passed += 1
    print(f'{"OK" if ok else "FAIL"} {name}: got={repr(bid)} expected={repr(expected)}')
print(f'\n{passed}/{len(oc_tests)} passed\n')


# ── respond_overcall ────────────────────────────────────────────────────────
# כל יד: 13 קלפים. הצבע הראשון — הצבע הרלוונטי לתמיכה.
resp_tests = [
    # ── רמה 1 (1♥) ──────────────────────────────────────────────────────────
    # תחרות רמה 1: 6 HCP + 3♥ + מתנגד 2♠ → 2♥
    ('1♥ תחרות 6נק',
     ['7S','6S','3S','7H','5H','4H','QD','6D','4D','3D','AC','6C','5C'],
     '1♥', '1♠', '2♠', '2♥'),
    # רגיל רמה 1: 5 HCP + 3♥ → פס (מתחת ל-7)
    ('1♥ 5נק פס',
     ['7S','6S','3S','KH','5H','4H','2D','6D','4D','3D','2C','6C','5C'],
     '1♥', '1♠', 'Pass', 'Pass'),
    # רגיל רמה 1: 9 HCP + 3♥ → 2♥
    ('1♥ 9נק תמיכה',
     ['7S','6S','3S','AH','5H','4H','2D','6D','4D','3D','AC','6C','5C'],
     '1♥', '1♠', 'Pass', '2♥'),
    # רמה 1: 11 HCP + 3♥ → הזמנה 3♥   (QS=2, AH=4, KH=3, QD=2 = 11)
    ('1♥ 11נק הזמנה',
     ['QS','6S','3S','AH','KH','4H','QD','6D','4D','3D','2C','6C','5C'],
     '1♥', '1♠', 'Pass', '3♥'),
    # רמה 1: 13 HCP + 3♥ → 4♥
    ('1♥ 13נק משחק',
     ['7S','6S','3S','AH','KH','4H','QD','6D','4D','3D','AC','6C','5C'],
     '1♥', '1♠', 'Pass', '4♥'),

    # ── רמה 2 (2♥) ──────────────────────────────────────────────────────────
    # תחרות רמה 2: 6 HCP + 3♥ + מתנגד 2♠ → פס (לא מכריז ברמה 3!)
    ('2♥ תחרות 6נק → פס',
     ['7S','6S','3S','7H','5H','4H','QD','6D','4D','3D','AC','6C','5C'],
     '2♥', '1♠', '2♠', 'Pass'),
    # רמה 2: 9 HCP + 3♥ → פס (מתחת ל-10)
    ('2♥ 9נק פס',
     ['7S','6S','3S','AH','5H','4H','QD','6D','4D','3D','2C','6C','5C'],
     '2♥', '1♠', 'Pass', 'Pass'),
    # רמה 2: 10 HCP + 3♥ → הזמנה 3♥
    ('2♥ 10נק הזמנה',
     ['7S','6S','3S','AH','5H','4H','QD','6D','4D','3D','AC','6C','5C'],
     '2♥', '1♠', 'Pass', '3♥'),
    # רמה 2: 13 HCP + 3♥ → 4♥
    ('2♥ 13נק משחק',
     ['7S','6S','3S','AH','KH','4H','QD','6D','4D','3D','AC','6C','5C'],
     '2♥', '1♠', 'Pass', '4♥'),

    # ── מינור ────────────────────────────────────────────────────────────────
    # מינור 7 HCP + 3♦ → פס
    ('2♦ 7נק פס',
     ['AS','2H','3H','4H','5H','QD','3D','4D','5D','6D','2C','3C','4C'],
     '2♦', '1♥', 'Pass', 'Pass'),
    # מינור 10 HCP + 4♦ → תמיכה 3♦   (AS=4, KS=3, QD=2, JD=1 = 10)
    ('2♦ 10נק תמיכה',
     ['AS','KS','2H','3H','4H','5H','QD','JD','4D','5D','2C','3C','4C'],
     '2♦', '1♥', 'Pass', '3♦'),
]

print('=== respond_overcall ===')
passed2 = 0
for name, hand, oc_bid, op_bid, comp_bid, expected in resp_tests:
    bid, exp_txt = respond_overcall(hand, oc_bid, op_bid, competition_bid=comp_bid)
    ok = bid == expected
    if ok:
        passed2 += 1
    print(f'{"OK" if ok else "FAIL"} {name}: got={repr(bid)} expected={repr(expected)}')
    if not ok:
        print(f'       הסבר: {exp_txt}')

print(f'\n{passed2}/{len(resp_tests)} passed')
