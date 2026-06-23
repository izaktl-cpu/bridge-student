# -*- coding: utf-8 -*-
"""
סימולטור סטיימן — בודק שגיאות לוגיות בשיעור סטיימן.
N פותח 1NT (15-17), S מגיב עם סטיימן או חלופות.
"""
import sys, io, random
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine.scoring import hcp, distribution, is_balanced
from engine.deal_constraints import deal_robot_opens_1nt_stayman
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS
GAME = {'3NT', '4♥', '4♠'}
FINAL = GAME | {'Pass', '2NT', '2♥', '2♠', '3♥', '3♠'}

DEALS   = 2000
MAX_BUGS = 30
random.seed(None)

# ── לוגיקת S ────────────────────────────────────────────────────────────────

def s_first_bid(hand):
    h = hcp(hand)
    d = distribution(hand)
    has_major_4 = d['H'] == 4 or d['S'] == 4
    four_count = sum([d['S'] == 4, d['H'] == 4, d['D'] >= 4, d['C'] >= 4])
    if h >= 8 and has_major_4 and four_count >= 2:
        return '2♣'
    if h <= 7:
        return 'Pass'
    if h <= 9:
        return '2NT'
    return '3NT'

def n_stayman_reply(hand):
    d = distribution(hand)
    if d['H'] >= 4:
        return '2♥'
    if d['S'] >= 4:
        return '2♠'
    return '2♦'

def s_stayman_cont(hand_s, stayman_reply):
    h = hcp(hand_s)
    d = distribution(hand_s)
    has_fit = (stayman_reply == '2♥' and d['H'] >= 4) or \
              (stayman_reply == '2♠' and d['S'] >= 4)
    if has_fit:
        suit = '♥' if stayman_reply == '2♥' else '♠'
        return f'4{suit}' if h >= 10 else f'3{suit}'
    return '3NT' if h >= 10 else '2NT'

# ── בדיקות לוגיות ────────────────────────────────────────────────────────────

def check_s_first(hand_s, bid, hn):
    errors = []
    h = hcp(hand_s)
    d = distribution(hand_s)
    has_major_4 = d['H'] == 4 or d['S'] == 4
    four_count = sum([d['S'] == 4, d['H'] == 4, d['D'] >= 4, d['C'] >= 4])
    should_stayman = h >= 8 and has_major_4 and four_count >= 2

    if should_stayman and bid != '2♣':
        errors.append(f'S עם {h} נקג ו-4-{_S["H" if d["H"]==4 else "S"]} היה צריך לפתוח סטיימן 2♣, לא {bid}')
    if not should_stayman and bid == '2♣':
        errors.append(f'S הכריז 2♣ סטיימן ללא תנאים (h={h}, 4M={has_major_4}, 4-count={four_count})')
    if h >= 10 and bid == '2NT':
        errors.append(f'S עם {h} נקג הכריז 2NT במקום 3NT')
    if h <= 7 and bid != 'Pass':
        errors.append(f'S עם {h} נקג הכריז {bid} במקום פס')
    return errors

def check_n_stayman(hand_n, bid):
    errors = []
    d = distribution(hand_n)
    if bid == '2♥' and d['H'] < 4:
        errors.append(f'N ענה 2♥ עם {d["H"]} קלפי ♥ בלבד')
    if bid == '2♠' and d['S'] < 4:
        errors.append(f'N ענה 2♠ עם {d["S"]} קלפי ♠ בלבד')
    if bid == '2♦' and (d['H'] >= 4 or d['S'] >= 4):
        maj = '♥' if d['H'] >= 4 else '♠'
        errors.append(f'N ענה 2♦ (אין מיגור) אבל יש לו 4 קלפי {_S[maj[1:]]}')
    return errors

def check_stayman_cont(hand_s, bid, stayman_reply):
    errors = []
    h = hcp(hand_s)
    d = distribution(hand_s)
    correct = s_stayman_cont(hand_s, stayman_reply)
    if bid != correct:
        errors.append(f'S הכריז {bid} במקום {correct} (h={h}, תגובת N={stayman_reply})')
    return errors

def check_game(hn, hs, final):
    if hn + hs >= 25 and final not in GAME:
        return [f'N+S={hn+hs} נק אך הגיעו ל-{final} בלבד']
    if hn + hs < 22 and final in GAME:
        return [f'N+S={hn+hs} נק אך הגיעו ל-{final} — יתר']
    return []

# ── עזרים ────────────────────────────────────────────────────────────────────

def hand_str(hand):
    suits = []
    for suit, sym in [('S','♠'),('H','♥'),('D','♦'),('C','♣')]:
        cards = sorted([c for c in hand if c.endswith(suit)],
                       key=lambda c: 'AKQJT98765432'.index(c[0]))
        suits.append(f'{sym} {"".join(c[0] for c in cards) or "—"}')
    return '  '.join(suits)

def print_bug(num, deal_num, N, S, hn, hs, auction, errors):
    print(f'{"─"*54}')
    print(f'  באג #{num}  (חלוקה {deal_num+1})')
    print(f'  N ({hn} נק): {hand_str(N)}')
    print(f'  S ({hs} נק): {hand_str(S)}')
    print(f'  מכרז: {" → ".join(auction)}')
    for e in errors:
        print(f'  ⚠ {e}')
    print()

# ── לולאה ראשית ──────────────────────────────────────────────────────────────

bugs_found = 0
games = 0
total = 0

print(f'\nמריץ {DEALS} חלוקות סטיימן...\n')

for deal_num in range(DEALS):
    if bugs_found >= MAX_BUGS:
        print(f'⚠ הגענו ל-{MAX_BUGS} באגים — עוצרים.')
        break
    try:
        hands = deal_robot_opens_1nt_stayman()
    except RuntimeError:
        continue

    N, S = hands['N'], hands['S']
    hn, hs = hcp(N), hcp(S)
    total += 1
    auction = ['1NT']
    errors = []

    # S מגיב
    s1 = s_first_bid(S)
    errors += check_s_first(S, s1, hn)
    auction.append(s1)

    if s1 != '2♣':
        # סיום ישיר
        if s1 == '2NT':
            n_reply = '3NT' if hn >= 16 else 'Pass'
            auction += ['Pass', n_reply]
            final = n_reply
        elif s1 == '3NT':
            auction.append('Pass')
            final = '3NT'
        else:
            final = '1NT'
        if final in GAME:
            games += 1
        errors += check_game(hn, hs, final)
    else:
        # N עונה לסטיימן
        n_reply = n_stayman_reply(N)
        errors += check_n_stayman(N, n_reply)
        auction += ['Pass', n_reply, 'Pass']

        # S ממשיך
        s2 = s_stayman_cont(S, n_reply)
        errors += check_stayman_cont(S, s2, n_reply)
        auction.append(s2)

        if s2 in GAME:
            games += 1
            errors += check_game(hn, hs, s2)
        elif s2 in ('2NT', '3♥', '3♠'):
            # S הזמין — N מחליט אם לקבל
            if s2 == '2NT':
                n2 = '3NT' if hn >= 16 else 'Pass'
            else:
                suit = '♥' if '♥' in s2 else '♠'
                n2 = f'4{suit}' if hn >= 16 else 'Pass'
            auction += ['Pass', n2]
            final = n2
            if final in GAME:
                games += 1
            errors += check_game(hn, hs, final)
        else:
            errors += check_game(hn, hs, s2)

    if errors:
        print_bug(bugs_found + 1, deal_num, N, S, hn, hs, auction, errors)
        bugs_found += 1

print(f'\n{"═"*54}')
print(f'  חלוקות: {total}')
print(f'  באגים:  {bugs_found}')
print(f'  משחקים: {games}/{total} = {games/total*100:.0f}%')
print(f'{"═"*54}')
if bugs_found == 0:
    print('  ✓ לא נמצאו באגים!')
