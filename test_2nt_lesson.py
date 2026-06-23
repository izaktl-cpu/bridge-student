# -*- coding: utf-8 -*-
"""
בדיקת לוגיקת שיעור 6 — 2NT (סטיימן וטרנספר)
מריץ 2000 ידיים אקראיות ומוודא:
  - אילוצי חלוקה (N=20-22 מאוזן)
  - הכרזה ראשונה נכונה (Pass/3♣/3♦/3♥/3NT)
  - המשך טרנספר (Pass/3NT/4M) לפי אורך ונקודות
  - תגובת North ל-3NT (מתקן ל-4M או עובר)
  - המשך סטיימן (4M עם התאמה, 3NT ללא)
"""

import sys, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine.deal_constraints import deal_robot_opens_2nt_stayman, deal_robot_opens_2nt_transfer
from engine.scoring import hcp, distribution, is_balanced

N = 2000

# ─── תשתית ────────────────────────────────────────────────────────────────────

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

# ─── לוגיקה (שיקוף של lesson_robot_opens_2nt) ────────────────────────────────

def first_bid(hands):
    h = hcp(hands['S'])
    d = distribution(hands['S'])
    if d['H'] >= 5:
        return '3♦'
    if d['S'] >= 5:
        return '3♥'
    if h >= 5 and (d['H'] == 4 or d['S'] == 4):
        return '3♣'
    if h <= 4:
        return 'Pass'
    return '3NT'

def transfer_cont(hands, sym):
    h   = hcp(hands['S'])
    key = 'H' if sym == '♥' else 'S'
    n   = distribution(hands['S'])[key]
    if h <= 4:   return 'Pass'
    if n == 5:   return '3NT'
    return f'4{sym}'

def north_reply_3nt(hands, sym):
    key = 'H' if sym == '♥' else 'S'
    fit = distribution(hands['N'])[key]
    return f'4{sym}' if fit >= 3 else 'Pass'

def stayman_reply(hands):
    d = distribution(hands['N'])
    if d['H'] >= 4: return '3♥'
    if d['S'] >= 4: return '3♠'
    return '3♦'

def stayman_cont(hands, reply):
    d = distribution(hands['S'])
    if reply == '3♥' and d['H'] >= 4: return '4♥'
    if reply == '3♠' and d['S'] >= 4: return '4♠'
    return '3NT'

# ═══════════════════════════════════════════════════════════════════════════════
#  סטיימן — N=20-22 מאוזן, S=4+ HCP, 4 קלפי מיגור בדיוק
# ═══════════════════════════════════════════════════════════════════════════════

print('═' * 50)
print('  שיעור 6 — Stayman ×', N)
print('═' * 50)

for i in range(N):
    h = deal_robot_opens_2nt_stayman()
    nh = hcp(h['N'])
    d  = distribution(h['S'])
    sh = hcp(h['S'])
    info = f'N={nh} S={sh} dist={d["S"]}-{d["H"]}-{d["D"]}-{d["C"]}'

    # אילוצים
    chk(f'[{i}] N HCP 20-22',       20 <= nh <= 22,          True,  info)
    chk(f'[{i}] N balanced',         is_balanced(h['N']),     True,  info)
    chk(f'[{i}] S no 5+ major',      d['H'] < 5 and d['S'] < 5, True, info)
    chk(f'[{i}] S has 4-card major', d['H'] == 4 or d['S'] == 4, True, info)
    chk(f'[{i}] S HCP >= 4',         sh >= 4,                 True,  info)

    # הכרזה ראשונה תמיד 3♣ (כי deal מבטיח 4-card major + 4+ HCP)
    chk(f'[{i}] first_bid=3♣', first_bid(h), '3♣', info)

    # המשך אחרי תגובת סטיימן
    reply = stayman_reply(h)
    cont  = stayman_cont(h, reply)
    # עם התאמה → 4M, בלי → 3NT
    ds = distribution(h['S'])
    has_fit = (reply == '3♥' and ds['H'] >= 4) or (reply == '3♠' and ds['S'] >= 4)
    if has_fit:
        suit = '♥' if reply == '3♥' else '♠'
        chk(f'[{i}] stayman-cont fit={suit}', cont, f'4{suit}', info)
    else:
        chk(f'[{i}] stayman-cont no-fit', cont, '3NT', info)

# ═══════════════════════════════════════════════════════════════════════════════
#  טרנספר — N=20-22 מאוזן, S=0-9 HCP, 5+ מיגור
# ═══════════════════════════════════════════════════════════════════════════════

print('═' * 50)
print('  שיעור 6 — Transfer ×', N)
print('═' * 50)

t_pass = t_3nt = t_4m = 0

for i in range(N):
    h  = deal_robot_opens_2nt_transfer()
    nh = hcp(h['N'])
    sh = hcp(h['S'])
    ds = distribution(h['S'])
    dn = distribution(h['N'])
    sym = '♥' if ds['H'] >= 5 else '♠'
    key = 'H' if sym == '♥' else 'S'
    suit_len = ds[key]
    info = f'N={nh} S={sh} sym={sym} len={suit_len}'

    # אילוצים
    chk(f'[{i}] N HCP 20-22',   20 <= nh <= 22,              True,  info)
    chk(f'[{i}] N balanced',     is_balanced(h['N']),         True,  info)
    chk(f'[{i}] S has 5+ major', ds['H'] >= 5 or ds['S'] >= 5, True, info)
    chk(f'[{i}] S HCP 0-9',      0 <= sh <= 9,               True,  info)

    # הכרזה ראשונה
    fb = first_bid(h)
    if ds['H'] >= 5:
        chk(f'[{i}] first_bid 5+H=3♦', fb, '3♦', info)
    else:
        chk(f'[{i}] first_bid 5+S=3♥', fb, '3♥', info)

    # המשך טרנספר
    tc = transfer_cont(h, sym)
    if sh <= 4:
        chk(f'[{i}] transfer-cont weak=Pass', tc, 'Pass', info)
        t_pass += 1
    elif suit_len == 5:
        chk(f'[{i}] transfer-cont 5-card=3NT', tc, '3NT', info)
        t_3nt += 1
        # תגובת North ל-3NT
        nr = north_reply_3nt(h, sym)
        north_fit = dn[key]
        if north_fit >= 3:
            chk(f'[{i}] north-reply 3+fit=4M', nr, f'4{sym}', info)
        else:
            chk(f'[{i}] north-reply 2fit=Pass', nr, 'Pass', info)
    else:
        chk(f'[{i}] transfer-cont 6+card=4M', tc, f'4{sym}', info)
        t_4m += 1

print(f'  התפלגות: Pass={t_pass}  3NT={t_3nt}  4M={t_4m}')

# ─── תוצאות ───────────────────────────────────────────────────────────────────

total = passes + len(failures) // 3
print()
print('═' * 50)
if failures:
    for f in failures:
        print(f)
    print(f'═' * 50)
    print(f'  תוצאות: {passes} עברו, {len(failures)//3} נכשלו')
else:
    print(f'  ✓ כל הבדיקות עברו בהצלחה!')
    print(f'  {passes} בדיקות — שיעור 6 (2NT)')
print('═' * 50)
