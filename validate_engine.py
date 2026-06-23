# -*- coding: utf-8 -*-
"""
סקריפט ולידציה של engine — מינורים ומיגורים.
מחלק N ידיים אקראיות ובודק עקביות לוגית של כל פונקציות ה-engine.
"""

import sys, io, random, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine.cards import make_deck, SUIT_SYMBOLS
from engine.scoring import hcp, distribution, is_balanced, dist_fit_pts
from engine.opening import opening_bid as _opening_bid
from engine.response import respond_minor, respond_major, responder_continuation_after_minor
from engine.rebid import opener_rebid

_S = SUIT_SYMBOLS
N_DEALS = 5000
random.seed(42)

failures = []
crashes  = []
passes   = 0


def deal_random():
    deck = make_deck()
    random.shuffle(deck)
    return {'N': deck[:13], 'E': deck[13:26], 'S': deck[26:39], 'W': deck[39:]}


def fail(label, msg, hand=None):
    h_str = ''
    if hand:
        d = distribution(hand)
        h_str = f' [hcp={hcp(hand)} {d["S"]}-{d["H"]}-{d["D"]}-{d["C"]} bal={is_balanced(hand)}]'
    failures.append(f'  FAIL {label}{h_str}: {msg}')


def check_respond_minor(hand, opener_suit):
    global passes
    try:
        bid, why = respond_minor(hand, opener_suit)
    except Exception as e:
        crashes.append(f'respond_minor({opener_suit}): {e}')
        return None

    h   = hcp(hand)
    d   = distribution(hand)
    bal = is_balanced(hand)
    fit = d[opener_suit]
    sym = _S[opener_suit]

    label = f'respond_{sym}'

    # Pass: חייב 0-5
    if bid == 'Pass':
        if h > 5:
            fail(label, f'Pass עם {h} נקודות', hand)
        else:
            passes += 1
        return bid

    # יש לפחות 6 נקודות
    if h < 6:
        fail(label, f'{bid} עם {h} נקודות (פחות מ-6)', hand)
        return bid

    # מיגורים — בדיקת אורך
    if bid == '1♥':
        if d['H'] < 4:
            fail(label, f'1♥ עם {d["H"]} קלפי ♥', hand)
        elif d['S'] > d['H'] and d['S'] >= 4:
            fail(label, f'1♥ כשיש {d["S"]} ♠ > {d["H"]} ♥', hand)
        else:
            passes += 1
    elif bid == '1♠':
        if d['S'] < 4:
            fail(label, f'1♠ עם {d["S"]} קלפי ♠', hand)
        elif d['H'] > d['S'] and d['H'] >= 4:
            fail(label, f'1♠ כשיש {d["H"]} ♥ > {d["S"]} ♠', hand)
        else:
            passes += 1
    # 1♦ כתגובה ל-1♣
    elif bid == '1♦':
        if opener_suit != 'C':
            fail(label, '1♦ כתגובה ל-1♦ (לא ל-1♣)', hand)
        elif d['D'] < 4:
            fail(label, f'1♦ עם {d["D"]} קלפי ♦', hand)
        else:
            passes += 1
    # תמיכת מינור
    elif bid == f'2{sym}':
        if opener_suit == 'C' and (fit < 5 or bal or h > 10):
            if fit < 5:
                fail(label, f'2{sym} עם {fit} קלפים בלבד (צריך 5+)', hand)
            elif bal:
                fail(label, f'2{sym} עם יד מאוזנת', hand)
            elif h > 10:
                fail(label, f'2{sym} עם {h} נקודות (צריך 6-10)', hand)
        elif opener_suit == 'D' and (fit < 4 or bal or h > 10):
            if fit < 4:
                fail(label, f'2{sym} עם {fit} קלפים (צריך 4+)', hand)
            elif bal:
                fail(label, f'2{sym} עם יד מאוזנת', hand)
            elif h > 10:
                fail(label, f'2{sym} עם {h} נקודות (צריך 6-10)', hand)
        else:
            passes += 1
    elif bid == f'3{sym}':
        if opener_suit == 'D' and (fit < 4 or bal or h < 11):
            fail(label, f'3{sym} לא תקין: fit={fit} bal={bal} h={h}', hand)
        else:
            passes += 1
    # NT
    elif bid == '1NT':
        if h > 10:
            fail(label, f'1NT עם {h} נקודות (צריך 6-10)', hand)
        else:
            passes += 1
    elif bid == '2NT':
        if h < 11 or h > 12:
            fail(label, f'2NT עם {h} נקודות (צריך 11-12)', hand)
        else:
            passes += 1
    elif bid == '3NT':
        if h < 13:
            fail(label, f'3NT עם {h} נקודות (צריך 13+)', hand)
        else:
            passes += 1
    # 2♣ כתגובה ל-1♦
    elif bid == '2♣' and opener_suit == 'D':
        if d['C'] < 5 or h < 11:
            fail(label, f'2♣/1♦ עם {d["C"]} ♣ ו-{h} נקודות', hand)
        else:
            passes += 1
    else:
        passes += 1

    return bid


def check_opener_rebid(opener_hand, opener_suit, resp_bid):
    global passes
    opening = f'1{_S[opener_suit]}'
    try:
        bid, why = opener_rebid(opener_hand, opening, resp_bid)
    except Exception as e:
        crashes.append(f'opener_rebid({opening},{resp_bid}): {e}')
        return None

    h  = hcp(opener_hand)
    d  = distribution(opener_hand)

    # בדיקות בסיסיות
    if bid not in ('Pass', '3NT') and bid.startswith('4') and h < 13:
        fail(f'rebid_{opening}_{resp_bid}', f'{bid} עם {h} נקודות', opener_hand)
    else:
        passes += 1
    return bid


def check_respond_major(hand, opener_suit):
    global passes
    try:
        bid, why = respond_major(hand, opener_suit)
    except Exception as e:
        crashes.append(f'respond_major({opener_suit}): {e}')
        return None

    h   = hcp(hand)
    d   = distribution(hand)
    fit = d[opener_suit]
    sym = _S[opener_suit]
    label = f'respond_major_{sym}'

    # Pass: חייב 0-5
    if bid == 'Pass':
        if h > 5:
            fail(label, f'Pass עם {h} נקודות', hand)
        else:
            passes += 1
        return bid

    # חייב 6+ נקודות
    if h < 6:
        fail(label, f'{bid} עם {h} נקודות (פחות מ-6)', hand)
        return bid

    # תמיכה ב-M: 2M/3M/4M
    if bid in (f'2{sym}', f'3{sym}', f'4{sym}'):
        if fit < 3:
            fail(label, f'{bid} עם {fit} קלפי {sym} בלבד (צריך 3+)', hand)
            return bid
        dp  = dist_fit_pts(hand, trump=opener_suit)
        tot = h + dp
        if bid == f'2{sym}':
            if tot >= 10:
                fail(label, f'2{sym} עם tot={tot} (היה צריך 3M/4M)', hand)
            else:
                passes += 1
        elif bid == f'3{sym}':
            if tot < 10:
                fail(label, f'3{sym} עם tot={tot} (צריך 10+)', hand)
            elif tot >= 13:
                fail(label, f'3{sym} עם tot={tot} (היה צריך 4M)', hand)
            else:
                passes += 1
        elif bid == f'4{sym}':
            rule19 = fit >= 5 and h >= 7
            if tot < 13 and not rule19:
                fail(label, f'4{sym} עם tot={tot} (צריך 13+ או חוק 19: 5 קלפים ו-7+ נקג)', hand)
            else:
                passes += 1
        return bid

    # 1NT: 6-10
    if bid == '1NT':
        if h > 10:
            fail(label, f'1NT עם {h} נקודות (צריך 6-10)', hand)
        else:
            passes += 1
        return bid

    # 2NT: 11-12
    if bid == '2NT':
        if h < 11 or h > 12:
            fail(label, f'2NT עם {h} נקודות (צריך 11-12)', hand)
        else:
            passes += 1
        return bid

    # 3NT: 13+
    if bid == '3NT':
        if h < 13:
            fail(label, f'3NT עם {h} נקודות (צריך 13+)', hand)
        else:
            passes += 1
        return bid

    # 1♠ אחרי 1♥
    if bid == '1♠' and opener_suit == 'H':
        if d['S'] < 4:
            fail(label, f'1♠/1♥ עם {d["S"]} ♠ (צריך 4+)', hand)
        elif h < 6:
            fail(label, f'1♠/1♥ עם {h} נקודות (צריך 6+)', hand)
        else:
            passes += 1
        return bid

    # צבע חדש ברמה 2 (2H/2D/2C)
    if bid[0] == '2' and bid != f'2{sym}':
        if h < 11:
            fail(label, f'{bid} עם {h} נקודות (צריך 11+ לצבע חדש ברמה 2)', hand)
        else:
            bid_suit_sym = bid[1]
            bid_suit_map = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
            bid_suit = bid_suit_map.get(bid_suit_sym)
            if bid_suit and d.get(bid_suit, 0) < 5:
                fail(label, f'{bid} עם {d.get(bid_suit,0)} קלפים (צריך 5+ לצבע חדש)', hand)
            else:
                passes += 1
        return bid

    passes += 1
    return bid


def check_continuation(s_hand, s_bid, n_rebid):
    global passes
    try:
        bid, why = responder_continuation_after_minor(s_hand, s_bid, n_rebid)
    except Exception as e:
        crashes.append(f'continuation({s_bid},{n_rebid}): {e}')
        return None

    h   = hcp(s_hand)
    d   = distribution(s_hand)

    _map = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
    s_suit = next((suit for ch, suit in _map.items() if ch in s_bid), None)
    s_len  = d.get(s_suit, 0) if s_suit else 0
    dp     = dist_fit_pts(s_hand, trump=s_suit) if s_suit else 0
    tot    = h + dp

    label = f'cont_{s_bid}_{n_rebid}'

    # 4M — צריך 13+ (1NT) או 15+ (2m)
    if s_suit in ('H', 'S') and bid == f'4{_S[s_suit]}':
        if n_rebid == '1NT' and tot < 13:
            fail(label, f'4M אחרי 1NT עם tot={tot}', s_hand)
        elif n_rebid in ('2♣', '2♦') and tot < 15:
            fail(label, f'4M אחרי 2m עם tot={tot}', s_hand)
        else:
            passes += 1
    # 3M — צריך 11-14 (1NT) או 11-14 (2m)
    elif s_suit in ('H', 'S') and bid == f'3{_S[s_suit]}':
        if tot < 11:
            fail(label, f'3M עם tot={tot} (צריך 11+)', s_hand)
        elif n_rebid == '1NT' and tot >= 13:
            fail(label, f'3M אחרי 1NT עם tot={tot} (היה צריך 4M)', s_hand)
        elif n_rebid in ('2♣', '2♦') and tot >= 15:
            fail(label, f'3M אחרי 2m עם tot={tot} (היה צריך 4M)', s_hand)
        else:
            passes += 1
    elif bid == '3NT':
        if h < 13 and n_rebid not in ('3♣', '3♦', '2NT'):
            fail(label, f'3NT עם {h} נקודות', s_hand)
        else:
            passes += 1
    else:
        passes += 1
    return bid


# ════════════════════════════════════════════════════════════════════
print('מריץ', N_DEALS, 'ידיים אקראיות...')
print()

for i in range(N_DEALS):
    hands = deal_random()
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)

    # ── בדיקות מינורים ──
    for minor in ['C', 'D']:
        sym = _S[minor]

        # בדוק respond_minor עבור S
        s_bid = check_respond_minor(s, minor)

        # אם S ענה משהו ו-N יכול לפתוח, בדוק rebid
        if s_bid and s_bid != 'Pass' and 12 <= hn <= 19:
            if _opening_bid(n)[0] == f'1{sym}':
                n_rebid = check_opener_rebid(n, minor, s_bid)

                # בדוק continuation אם N הכריז שוב
                if n_rebid and n_rebid != 'Pass' and s_bid in ('1♥', '1♠', '1♦'):
                    check_continuation(s, s_bid, n_rebid)

    # ── בדיקות מיגורים ──
    for major in ['H', 'S']:
        check_respond_major(s, major)

# ════════════════════════════════════════════════════════════════════
n_fail = len([f for f in failures if f.startswith('  FAIL')])
print(f'תוצאות: {passes} בדיקות עברו, {n_fail} נכשלו, {len(crashes)} קריסות')
print()

if crashes:
    print('=== קריסות ===')
    for c in crashes[:20]:
        print(' ', c)
    print()

if failures:
    print(f'=== {n_fail} כשלונות (עד 30 ראשונים) ===')
    for f in failures[:30]:
        print(f)
else:
    print('כל הבדיקות עברו בהצלחה!')
