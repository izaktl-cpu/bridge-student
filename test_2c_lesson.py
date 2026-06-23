# -*- coding: utf-8 -*-
"""
בדיקת לוגיקת שיעור 7 — 2♣ חזקה
מריץ 2000 ידיים אקראיות ומוודא:
  - אילוצי חלוקה (N=23+ HCP, S=0-10 HCP)
  - תגובה ראשונה נכונה (2♦/2♥/2♠/2NT/3♣/3♦)
  - תגובה שנייה לאחר רביד N (Pass/3NT/3♣/3♦/3♥/4M/5m)
  - תגובה שלישית (סטיימן/טרנספר) כולל תיקון שS חייב 4+ קלפי מיגור לפני 4M
"""

import sys, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine.deal_constraints import deal_robot_opens_2c
from engine.scoring import hcp, is_balanced, distribution, sure_tricks
from engine.response import respond_2c, respond_2c_second, respond_2c_third
from engine.rebid import opener_rebid, opener_bid_2c_round3

N = 2000

failures = []
passes   = 0

def chk(label, got, want, info=''):
    global passes
    if got == want:
        passes += 1
    else:
        suffix = f'  [{info}]' if info else ''
        failures.append(f'FAIL  {label}{suffix}')
        failures.append(f'      got={got!r}  want={want!r}')

# ─── מראות לוגיקה (עצמאיות מ-response.py) ────────────────────────────────────

def mirror_respond_2c(hand):
    h   = hcp(hand)
    d   = distribution(hand)
    bal = is_balanced(hand)
    if h <= 6:
        return '2♦'
    if d['H'] >= 5 and d['H'] >= d['S']:
        return '2♥'
    if d['S'] >= 5:
        return '2♠'
    if d['H'] >= 5:
        return '2♥'
    if bal and h >= 10:
        return '2NT'
    if d['C'] >= 5 and d['C'] >= d['D']:
        return '3♣'
    if d['D'] >= 5:
        return '3♦'
    if d['C'] >= 5:
        return '3♣'
    return '2♦'  # 7-9 HCP ללא 5 קלפי צבע ולא מאוזן ברור — ממתין


def mirror_respond_2c_second(hand, opener_second):
    h   = hcp(hand)
    d   = distribution(hand)
    bal = is_balanced(hand)

    if opener_second == '2NT':
        if h <= 3:
            return 'Pass'
        if d['H'] >= 5:
            return '3♦'
        if d['S'] >= 5:
            return '3♥'
        if d['H'] >= 4 or d['S'] >= 4:
            return '3♣'
        return '3NT'

    if opener_second == '3NT':
        return 'Pass'

    _suit_map = {'2♥': 'H', '2♠': 'S', '3♣': 'C', '3♦': 'D'}
    opener_suit = _suit_map.get(opener_second)

    if opener_suit in ('H', 'S'):
        sym = {'H': '♥', 'S': '♠'}[opener_suit]
        if d[opener_suit] >= 3:
            return f'4{sym}'
        return '3NT'

    if opener_suit in ('C', 'D'):
        sym = {'C': '♣', 'D': '♦'}[opener_suit]
        if d['H'] >= 5:
            return '4♥'
        if d['S'] >= 5:
            return '4♠'
        if d[opener_suit] >= 5:
            return f'5{sym}'
        return '3NT'

    return '3NT'


def mirror_respond_2c_third(hand, s_second, n_third):
    d = distribution(hand)
    if s_second == '3♣':  # סטיימן
        if n_third == '3♥':
            return '4♥' if d['H'] >= 4 else '3NT'
        if n_third == '3♠':
            return '4♠' if d['S'] >= 4 else '3NT'
        return '3NT'  # n_third == '3♦' — ללא מיגור
    if s_second == '3♦':  # טרנספר ל-♥
        return '4♥'
    if s_second == '3♥':  # טרנספר ל-♠
        return '4♠'
    return 'Pass'

# ─── סטטיסטיקה ────────────────────────────────────────────────────────────────

_FINAL = {'3NT', '4♥', '4♠', '5♣', '5♦', 'Pass'}

stat_first = {}
stat_n_rebid = {}
stat_s2 = {}
stat_s3 = {}

print('═' * 56)
print('  שיעור 7 — 2♣ חזקה ×', N)
print('═' * 56)

for i in range(N):
    h_dict = deal_robot_opens_2c()
    n_hand = h_dict['N']
    s_hand = h_dict['S']

    hn  = hcp(n_hand)
    hs  = hcp(s_hand)
    st  = sure_tricks(n_hand)
    dn  = distribution(n_hand)
    ds  = distribution(s_hand)
    bal = is_balanced(n_hand)
    info_base = f'N={hn} S={hs} sure={st}'

    # ── אילוצי חלוקה ─────────────────────────────────────────────────────────
    chk(f'[{i}] N 23+ or sure-tricks',
        hn >= 23 or (hn >= 18 and st >= 9), True, info_base)
    chk(f'[{i}] S HCP 0-10', 0 <= hs <= 10, True, info_base)

    # ── תגובה ראשונה ─────────────────────────────────────────────────────────
    s_first_actual  = respond_2c(s_hand)[0]
    s_first_mirror  = mirror_respond_2c(s_hand)
    info_s1 = f'{info_base} ds={ds["S"]}-{ds["H"]}-{ds["D"]}-{ds["C"]} bal={is_balanced(s_hand)}'

    chk(f'[{i}] respond_2c mirror', s_first_actual, s_first_mirror, info_s1)
    stat_first[s_first_actual] = stat_first.get(s_first_actual, 0) + 1

    # ── רביד N (הכרזה שנייה של הפותח) ────────────────────────────────────────
    n_rebid_actual = opener_rebid(n_hand, '2♣', s_first_actual)[0]
    stat_n_rebid[n_rebid_actual] = stat_n_rebid.get(n_rebid_actual, 0) + 1
    info_n1 = f'{info_s1} n_rebid={n_rebid_actual}'

    if n_rebid_actual in _FINAL:
        continue  # חוזה סופי — ממשיכים ליד הבאה

    # ── תגובה שנייה של S ─────────────────────────────────────────────────────
    s2_actual = respond_2c_second(s_hand, n_rebid_actual)[0]
    s2_mirror = mirror_respond_2c_second(s_hand, n_rebid_actual)
    info_s2 = f'{info_n1} s2={s2_actual}'

    chk(f'[{i}] respond_2c_second mirror', s2_actual, s2_mirror, info_n1)
    stat_s2[s2_actual] = stat_s2.get(s2_actual, 0) + 1

    if s2_actual in _FINAL:
        continue

    # ── שלב 3: אחרי 2NT-סטיימן/טרנספר ──────────────────────────────────────
    # s2_actual ∈ {3♣, 3♦, 3♥} רק אחרי n_rebid == '2NT'
    if n_rebid_actual != '2NT' or s2_actual not in ('3♣', '3♦', '3♥'):
        continue

    n_third_actual = opener_bid_2c_round3(n_hand, '2NT', s2_actual)[0]
    s3_actual = respond_2c_third(s_hand, s2_actual, n_third_actual)[0]
    s3_mirror = mirror_respond_2c_third(s_hand, s2_actual, n_third_actual)
    info_s3 = f'{info_s2} s3_bid={s2_actual} n_third={n_third_actual}'

    chk(f'[{i}] respond_2c_third mirror', s3_actual, s3_mirror, info_s3)
    stat_s3[s3_actual] = stat_s3.get(s3_actual, 0) + 1

    # ── בדיקת תיקון: סטיימן עם 4♥ רק כשיש 4+ ♥ ─────────────────────────────
    if s2_actual == '3♣' and n_third_actual == '3♥':
        if s3_actual == '4♥':
            chk(f'[{i}] 4♥ needs 4+H', ds['H'] >= 4, True, info_s3)
        elif s3_actual == '3NT':
            chk(f'[{i}] 3NT means <4H', ds['H'] < 4, True, info_s3)

    if s2_actual == '3♣' and n_third_actual == '3♠':
        if s3_actual == '4♠':
            chk(f'[{i}] 4♠ needs 4+S', ds['S'] >= 4, True, info_s3)
        elif s3_actual == '3NT':
            chk(f'[{i}] 3NT means <4S', ds['S'] < 4, True, info_s3)

# ─── סטטיסטיקה ────────────────────────────────────────────────────────────────

print(f'\n  תגובה ראשונה של S:')
for k in sorted(stat_first):
    print(f'    {k}: {stat_first[k]}')

print(f'\n  רביד N:')
for k in sorted(stat_n_rebid):
    print(f'    {k}: {stat_n_rebid[k]}')

if stat_s2:
    print(f'\n  תגובה שנייה של S:')
    for k in sorted(stat_s2):
        print(f'    {k}: {stat_s2[k]}')

if stat_s3:
    print(f'\n  תגובה שלישית של S (סטיימן/טרנספר):')
    for k in sorted(stat_s3):
        print(f'    {k}: {stat_s3[k]}')

# ─── תוצאות ───────────────────────────────────────────────────────────────────

total_fail = len(failures) // 2
print()
print('═' * 56)
if failures:
    for f in failures:
        print(f)
    print('═' * 56)
    print(f'  תוצאות: {passes} עברו, {total_fail} נכשלו')
else:
    print(f'  ✓ כל הבדיקות עברו בהצלחה!')
    print(f'  {passes} בדיקות — שיעור 7 (2♣ חזקה)')
print('═' * 56)
