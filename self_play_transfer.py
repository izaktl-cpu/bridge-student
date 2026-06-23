# -*- coding: utf-8 -*-
"""
סימולטור טרנספר — בודק שגיאות לוגיות בשיעור טרנספר.
N פותח 1NT (15-17), S מגיב עם טרנספר או חלופות.
"""
import sys, io, random
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine.scoring import hcp, distribution, is_balanced
from engine.deal_constraints import deal_robot_opens_1nt_transfer
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
    if d['H'] >= 5:
        return '2♦'   # טרנספר ל-♥
    if d['S'] >= 5:
        return '2♥'   # טרנספר ל-♠
    if h <= 7:
        return 'Pass'
    if h <= 9:
        return '2NT'
    return '3NT'

def n_transfer_reply(bid):
    """N מסיים את הטרנספר"""
    if bid == '2♦':
        return '2♥'
    if bid == '2♥':
        return '2♠'
    return None   # לא טרנספר

def s_transfer_cont(hand_s, target_sym):
    """S ממשיך לאחר השלמת הטרנספר"""
    h = hcp(hand_s)
    if h <= 7:
        return 'Pass'
    if h <= 9:
        return f'3{target_sym}'
    return f'4{target_sym}'

# ── בדיקות לוגיות ────────────────────────────────────────────────────────────

def check_s_first(hand_s, bid):
    errors = []
    h = hcp(hand_s)
    d = distribution(hand_s)

    if d['H'] >= 5:
        if bid != '2♦':
            errors.append(f'S עם {d["H"]} קלפי ♥ היה צריך לטרנספר 2♦, לא {bid}')
    elif d['S'] >= 5:
        if bid != '2♥':
            errors.append(f'S עם {d["S"]} קלפי ♠ היה צריך לטרנספר 2♥, לא {bid}')
    else:
        # אין חמישייה — אמור לשחק 1NT / 2NT / 3NT
        if bid in ('2♦', '2♥'):
            errors.append(f'S טרנספר {bid} אך אין לו 5+ קלפי מיגור עיקרי')
        if h >= 10 and bid == '2NT':
            errors.append(f'S עם {h} נקג הכריז 2NT במקום 3NT')
        if h <= 7 and bid != 'Pass':
            errors.append(f'S עם {h} נקג הכריז {bid} במקום פס')
    return errors

def check_n_transfer(hand_n, s_bid, n_bid):
    errors = []
    expected = n_transfer_reply(s_bid)
    if expected and n_bid != expected:
        errors.append(f'N לא השלים טרנספר: S הכריז {s_bid}, N ענה {n_bid} במקום {expected}')
    return errors

def check_transfer_cont(hand_s, bid, target_sym):
    errors = []
    correct = s_transfer_cont(hand_s, target_sym)
    if bid != correct:
        h = hcp(hand_s)
        errors.append(f'S הכריז {bid} במקום {correct} (h={h}, מיגור={target_sym})')
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

print(f'\nמריץ {DEALS} חלוקות טרנספר...\n')

for deal_num in range(DEALS):
    if bugs_found >= MAX_BUGS:
        print(f'⚠ הגענו ל-{MAX_BUGS} באגים — עוצרים.')
        break
    try:
        hands = deal_robot_opens_1nt_transfer()
    except RuntimeError:
        continue

    N, S = hands['N'], hands['S']
    hn, hs = hcp(N), hcp(S)
    total += 1
    auction = ['1NT']
    errors = []

    # S מגיב
    s1 = s_first_bid(S)
    errors += check_s_first(S, s1)
    auction.append('Pass')
    auction.append(s1)

    if s1 in ('2♦', '2♥'):
        # N משלים טרנספר
        n1 = n_transfer_reply(s1)
        errors += check_n_transfer(N, s1, n1)
        target_sym = '♥' if s1 == '2♦' else '♠'
        auction += ['Pass', n1, 'Pass']

        # S ממשיך
        s2 = s_transfer_cont(S, target_sym)
        errors += check_transfer_cont(S, s2, target_sym)
        auction.append(s2)

        if s2 == 'Pass':
            final = f'2{target_sym}'
        elif s2 in GAME:
            final = s2
            games += 1
        else:
            # הזמנה: N מחליט
            suit = target_sym
            n2 = f'4{suit}' if hn >= 16 else 'Pass'
            auction += ['Pass', n2]
            final = f'2{suit}' if n2 == 'Pass' else n2
            if final in GAME:
                games += 1
        errors += check_game(hn, hs, final)

    elif s1 == '2NT':
        n_reply = '3NT' if hn >= 16 else 'Pass'
        auction += ['Pass', n_reply]
        final = n_reply
        if final in GAME:
            games += 1
        errors += check_game(hn, hs, final)
    elif s1 == '3NT':
        auction.append('Pass')
        final = '3NT'
        games += 1
        errors += check_game(hn, hs, final)
    else:
        final = '1NT'
        errors += check_game(hn, hs, final)

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
