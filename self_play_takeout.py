# -*- coding: utf-8 -*-
"""
סימולטור דבל להוצאה — שיעור 14.
4 סוכנים עצמאיים: W/E פותח, N/S מכריזים X ועונים.
הבדיקות עצמאיות — אינן מסתמכות על פונקציות המנוע עצמן.

שלב 1: W פותח, N מדבל, S עונה (+ המשך קיו-ביט)
שלב 2: E פותח, S מחליט X/Pass
"""
import sys, io, random
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine.opening   import opening_bid
from engine.scoring   import hcp, distribution
from engine.cards     import SUIT_SYMBOLS, make_deck
from engine.takeout_double import (
    can_double, respond_to_double,
    doubler_raises, doubler_rebid, respond_to_cue, _count_stoppers,
)

_S    = SUIT_SYMBOLS
_SYM  = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}
_RANK = {'C': 1, 'D': 2, 'H': 3, 'S': 4}

DEALS    = 500
MAX_BUGS = 40
random.seed(None)

# ─── עזרים ──────────────────────────────────────────────────────────────────

def hand_str(hand):
    result = []
    for suit, sym in [('S','♠'), ('H','♥'), ('D','♦'), ('C','♣')]:
        cards = sorted([c for c in hand if c.endswith(suit)],
                       key=lambda c: 'AKQJT98765432'.index(c[0]))
        result.append(f'{sym} {"".join(c[0] for c in cards)}')
    return '  '.join(result)

def suit_of(bid):
    for ch, s in _SYM.items():
        if ch in bid:
            return s
    return None

def _deal_random():
    deck = make_deck()
    random.shuffle(deck)
    return {'N': deck[:13], 'E': deck[13:26], 'S': deck[26:39], 'W': deck[39:]}

def _deal_phase1():
    """W פותח 1 בצבע, N מדבל, S עונה."""
    _SYM_MAP = {chr(0x2663): 'C', chr(0x2666): 'D', chr(0x2665): 'H', chr(0x2660): 'S'}
    scenario = random.choices(['weak', 'medium', 'strong'], weights=[2, 2, 2])[0]
    for _ in range(80_000):
        hands = _deal_random()
        w, n, s = hands['W'], hands['N'], hands['S']
        hw, hn, hs = hcp(w), hcp(n), hcp(s)
        dn, ds = distribution(n), distribution(s)
        if not (12 <= hw <= 15): continue
        if hcp(hands['E']) > 8: continue
        w_bid, _ = opening_bid(w)
        if not w_bid or w_bid[0] != '1' or 'NT' in w_bid: continue
        w_suit = next((v for k, v in _SYM_MAP.items() if k in w_bid), None)
        if not w_suit: continue
        if w_suit in ('H', 'S') and random.random() < 0.8: continue
        if ds.get(w_suit, 0) >= 4: continue
        if not (12 <= hn <= 16): continue
        if not can_double(n, w_suit, level=1): continue
        if any(dn[s2] >= 5 for s2 in ['S','H','D','C'] if s2 != w_suit): continue
        if scenario == 'weak'   and not (0  <= hs <= 8):  continue
        if scenario == 'medium' and not (9  <= hs <= 12): continue
        if scenario == 'strong' and not (13 <= hs <= 17): continue
        if min(ds.values()) < 1: continue
        return hands, w_bid, w_suit
    raise RuntimeError('phase1: לא ניתן לחלק')

def _deal_phase2():
    """E פותח 1 בצבע, S מחליט X/Pass."""
    _SYM_MAP = {chr(0x2663): 'C', chr(0x2666): 'D', chr(0x2665): 'H', chr(0x2660): 'S'}
    for _ in range(80_000):
        hands = _deal_random()
        e, s = hands['E'], hands['S']
        he, hs = hcp(e), hcp(s)
        if not (12 <= he <= 15): continue
        if hcp(hands['N']) > 8: continue
        if hcp(hands['W']) > 8: continue
        e_bid, _ = opening_bid(e)
        if not e_bid or e_bid[0] != '1' or 'NT' in e_bid: continue
        e_suit = next((v for k, v in _SYM_MAP.items() if k in e_bid), None)
        if not e_suit: continue
        if e_suit in ('H', 'S') and random.random() < 0.8: continue
        if distribution(s).get(e_suit, 0) >= 4: continue
        if min(distribution(s).values()) < 1: continue
        return hands, e_bid, e_suit
    raise RuntimeError('phase2: לא ניתן לחלק')

# ─── בדיקות עצמאיות ──────────────────────────────────────────────────────────

def verify_can_double(hand, opp_suit, bid):
    """בדיקה עצמאית: X/Pass לפי כללי שיעור 14."""
    errors = []
    h = hcp(hand)
    d = distribution(hand)
    other = [s for s in ['S','H','D','C'] if s != opp_suit]

    if bid == 'X':
        if not (12 <= h <= 16):
            errors.append(f'X עם {h} נק׳ (צריך 12–16)')
        if d.get(opp_suit, 0) > 2:
            errors.append(f'X עם {d[opp_suit]} קלפים בצבע יריב (מקס׳ 2)')
        for s in other:
            if d[s] < 3:
                errors.append(f'X עם {d[s]} קלפי {_S[s]} בלבד (צריך 3+)')
        if sum(1 for s in other if d[s] >= 4) < 2:
            errors.append('X ללא 2 סדרות של 4+ קלפים')
    elif bid == 'Pass':
        nok_pts  = not (12 <= h <= 16)
        nok_opp  = d.get(opp_suit, 0) > 2
        nok_suit = any(d[s] < 3 for s in other)
        nok_4ct  = sum(1 for s in other if d[s] >= 4) < 2
        if not (nok_pts or nok_opp or nok_suit or nok_4ct):
            errors.append(f'Pass עם {h} נק׳ ותבנית מתאימה (היה צריך X)')
    return errors

def verify_response(hand, opp_suit, bid, opp_level=1):
    """בדיקה עצמאית: תגובת S לדבל."""
    errors = []
    h = hcp(hand)
    d = distribution(hand)
    bid_suit  = suit_of(bid)
    bid_level = int(bid[0]) if bid and bid[0].isdigit() else 0

    # קיו ביט — 13+
    if bid_suit == opp_suit:
        if h < 13:
            errors.append(f'קיו ביט עם {h} נק׳ (צריך 13+)')
        return errors

    if bid == 'Pass':
        errors.append('S לא יכול לפס אחרי X')
        return errors

    if not bid_suit:
        return errors

    # צריך לפחות 3 קלפים בצבע שהכריז
    if d.get(bid_suit, 0) < 3:
        errors.append(f'ענה {bid} עם {d[bid_suit]} קלפי {_S[bid_suit]} (צריך 3+)')

    # גובה מינימלי
    bid_rank = _RANK.get(bid_suit, 0)
    opp_rank = _RANK.get(opp_suit, 0)
    min_lvl  = opp_level if bid_rank > opp_rank else opp_level + 1
    is_minor = bid_suit in ('C', 'D')
    jump_thr = 11 if is_minor else 9

    if h >= 13:
        errors.append(f'{h} נק׳ — היה צריך קיו ביט, לא {bid}')
    elif h >= jump_thr:
        if bid_level < min_lvl + 1:
            errors.append(f'{h} נק׳ — קפיצה לרמה {min_lvl+1}, הכריז {bid}')
    else:
        if bid_level != min_lvl:
            errors.append(f'{h} נק׳ — רמה {min_lvl}, הכריז {bid}')
    return errors

def verify_n_rebid(hand, opp_suit, bid):
    """בדיקה עצמאית: doubler_rebid — N מראה סדרה של 4+."""
    errors = []
    d = distribution(hand)
    bid_suit = suit_of(bid)
    if bid == '2NT':
        # ודא שאין 4+ במיגור
        for m in ['H', 'S']:
            if m != opp_suit and d[m] >= 4:
                errors.append(f'N הכריז 2NT עם {d[m]} קלפי {_S[m]} (היה צריך להראות מיגור)')
    elif bid_suit:
        if d.get(bid_suit, 0) < 4:
            errors.append(f'N הכריז {bid} עם {d[bid_suit]} קלפי {_S[bid_suit]} (צריך 4+)')
    return errors

def verify_game(hn, hs, final_bid, s_bid=None, opp_suit=None):
    """האם פספסו/הגזימו משחק?"""
    errors = []
    GAME = {'3NT', '4♥', '4♠', '5♣', '5♦'}
    total = hn + hs
    if total >= 25 and final_bid not in GAME:
        # בדוק אם זו מגבלת שיטה: S עם 9-10 נק' במינור → רמה נמוכה, N לא יכול לדעת
        if s_bid and opp_suit:
            s_suit = suit_of(s_bid)
            s_level = int(s_bid[0]) if s_bid and s_bid[0].isdigit() else 0
            s_rank  = _RANK.get(s_suit, 0)
            opp_rank = _RANK.get(opp_suit, 0)
            min_lvl = 1 if s_rank > opp_rank else 2
            is_jump = s_level > min_lvl
            if not is_jump and s_suit in ('C', 'D') and 9 <= hs <= 10:
                return []  # מגבלת שיטה — לא באג
        errors.append(f'פספסו משחק\nN = {hn}  |  S = {hs}  |  ביחד = {total}\nהגיעו ל: {final_bid}')
    if total < 20 and final_bid in GAME:
        errors.append(f'הגזמה\nN = {hn}  |  S = {hs}  |  ביחד = {total}\nהגיעו ל: {final_bid}')
    return errors

# ─── הדפסת באג ──────────────────────────────────────────────────────────────

bugs_found  = 0
total_p1    = 0
total_p2    = 0
games_found = 0
exceptions  = 0

def print_bug(label, deal_num, hands, auction, errors, extra=''):
    global bugs_found
    bugs_found += 1
    print(f'{"─"*60}')
    print(f'  [{label}] באג #{bugs_found}  (חלוקה {deal_num+1})')
    for seat in ['N', 'S', 'W', 'E']:
        print(f'  {seat} ({hcp(hands[seat])} נק׳): {hand_str(hands[seat])}')
    print(f'  מכרז: {" → ".join(auction)}')
    for e in errors:
        print(f'  ⚠ {e}')
    if extra:
        print(f'  ℹ {extra}')
    print()

GAME_BIDS = {'3NT', '4♥', '4♠', '5♣', '5♦'}

# ═══════════════════════════════════════════════════════════════════════════
# שלב 1: W פותח, N מדבל, S עונה
# ═══════════════════════════════════════════════════════════════════════════

print(f'\n══ שלב 1: W פותח, N מדבל, S עונה ══')
print(f'מריץ {DEALS} חלוקות...\n')

for deal_num in range(DEALS):
    if bugs_found >= MAX_BUGS:
        print(f'\n⚠ הגענו ל-{MAX_BUGS} באגים — עוצרים.')
        break

    try:
        hands, w_bid, w_suit = _deal_phase1()
    except RuntimeError:
        continue

    total_p1 += 1
    hn, hs = hcp(hands['N']), hcp(hands['S'])
    auction = [w_bid, 'Pass', 'X', 'Pass']
    errs = []

    # סוכן S עונה לדבל
    try:
        s_bid, s_expl = respond_to_double(hands['S'], w_suit, opp_level=1)
    except Exception as ex:
        exceptions += 1
        errs.append(f'respond_to_double קרס: {ex}')
        print_bug('שלב1', deal_num, hands, auction, errs)
        continue

    auction.append(s_bid)
    errs += verify_response(hands['S'], w_suit, s_bid, opp_level=1)
    if errs:
        print_bug('שלב1', deal_num, hands, auction, errs, s_expl)
        continue

    final_bid = s_bid

    # קיו ביט: S חזק (13+), N מראה סדרה
    if suit_of(s_bid) == w_suit:
        auction.append('Pass')
        try:
            n_bid, n_expl = doubler_rebid(hands['N'], w_suit)
        except Exception as ex:
            exceptions += 1
            errs.append(f'doubler_rebid קרס: {ex}')
            print_bug('שלב1', deal_num, hands, auction, errs)
            continue

        auction.append(n_bid)
        errs += verify_n_rebid(hands['N'], w_suit, n_bid)
        n_suit = suit_of(n_bid)

        auction.append('Pass')
        try:
            s2_bid, s2_expl = respond_to_cue(
                hands['S'], n_suit, opp_suit=w_suit, n_hand=hands['N'])
        except Exception as ex:
            exceptions += 1
            errs.append(f'respond_to_cue קרס: {ex}')
            print_bug('שלב1', deal_num, hands, auction, errs)
            continue

        auction.append(s2_bid)
        s2_suit = suit_of(s2_bid)

        # בדיקה עצמאית: תגובת S לסדרת N
        ds = distribution(hands['S'])
        if s2_suit and s2_suit in ('H', 'S') and s2_suit != w_suit:
            if ds.get(s2_suit, 0) < 3:
                errs.append(f'S הכריז {s2_bid} עם {ds[s2_suit]} קלפי {_S[s2_suit]} (צריך 3+)')
        elif s2_bid.endswith('NT'):
            stops_s = _count_stoppers(hands['S'], w_suit)
            stops_n = _count_stoppers(hands['N'], w_suit)
            if stops_s + stops_n < 1:
                errs.append(f'3NT ללא עוצר בסדרת W ({_S[w_suit]})')

        # N מעלה ל-4M אחרי 3M של S (כשS הראה מיגור)
        if s2_bid[0] == '3' and s2_suit in ('H', 'S') and s2_suit != w_suit:
            game = f'4{_S[s2_suit]}'
            auction.append('Pass')
            auction.append(game)
            auction.append('Pass')
            auction.append('Pass')
            auction.append('Pass')
            final_bid = game
        else:
            auction.append('Pass')
            auction.append('Pass')
            auction.append('Pass')
            final_bid = s2_bid

        if errs:
            print_bug('שלב1', deal_num, hands, auction, errs,
                      f'{s_expl} / {n_expl} / {s2_expl}')
            continue
    else:
        # N מחליט פס/העלאה אחרי תגובת S
        try:
            n2_bid, n2_expl = doubler_raises(hands['N'], s_bid, w_suit)
        except Exception as ex:
            exceptions += 1
            errs.append(f'doubler_raises קרס: {ex}')
            print_bug('שלב1', deal_num, hands, auction, errs)
            continue

        auction.append('Pass')
        auction.append(n2_bid)
        if n2_bid != 'Pass':
            auction += ['Pass', 'Pass', 'Pass']
            final_bid = n2_bid
        else:
            auction += ['Pass', 'Pass']

    errs += verify_game(hn, hs, final_bid, s_bid=s_bid, opp_suit=w_suit)
    if final_bid in GAME_BIDS:
        games_found += 1
    if errs:
        print_bug('שלב1', deal_num, hands, auction, errs)

p1_bugs = bugs_found

# ═══════════════════════════════════════════════════════════════════════════
# שלב 2: E פותח, S מדבל, N עונה, S מחליט להעלות/פס
# W=Pass, N=Pass, E=פתיחה, S=X/Pass → W=Pass, N=תגובה, E=Pass, S=העלאה/פס
# ═══════════════════════════════════════════════════════════════════════════

print(f'\n══ שלב 2: E פותח, S מדבל, N עונה, S מחליט ══')
print(f'מריץ {DEALS} חלוקות...\n')

games_p2 = 0

for deal_num in range(DEALS):
    if bugs_found >= MAX_BUGS:
        print(f'\n⚠ הגענו ל-{MAX_BUGS} באגים — עוצרים.')
        break

    try:
        hands, e_bid, e_suit = _deal_phase2()
    except RuntimeError:
        continue

    total_p2 += 1
    sn, ss = hcp(hands['S']), hcp(hands['N'])
    auction = ['Pass', 'Pass', e_bid]
    errs = []

    # ── סוכן S: X/Pass ────────────────────────────────────────────────────
    s_bid = 'X' if can_double(hands['S'], e_suit, level=1) else 'Pass'
    auction.append(s_bid)
    errs += verify_can_double(hands['S'], e_suit, s_bid)
    if errs:
        print_bug('שלב2', deal_num, hands, auction, errs)
        continue

    if s_bid == 'Pass':
        # S לא דבל — מכרז נגמר
        auction += ['Pass', 'Pass', 'Pass']
        continue

    # ── סוכן N: עונה לדבל של S ────────────────────────────────────────────
    auction.append('Pass')
    try:
        n_bid, n_expl = respond_to_double(hands['N'], e_suit, opp_level=1)
    except Exception as ex:
        exceptions += 1
        errs.append(f'respond_to_double (N) קרס: {ex}')
        print_bug('שלב2', deal_num, hands, auction, errs)
        continue

    auction.append(n_bid)
    errs += verify_response(hands['N'], e_suit, n_bid, opp_level=1)
    if errs:
        print_bug('שלב2', deal_num, hands, auction, errs, n_expl)
        continue

    final_bid = n_bid

    # ── קיו ביט: N חזק (13+), S מראה סדרה ──────────────────────────────────
    if suit_of(n_bid) == e_suit:
        auction.append('Pass')
        try:
            s2_bid, s2_expl = doubler_rebid(hands['S'], e_suit)
        except Exception as ex:
            exceptions += 1
            errs.append(f'doubler_rebid (S) קרס: {ex}')
            print_bug('שלב2', deal_num, hands, auction, errs)
            continue

        auction.append(s2_bid)
        errs += verify_n_rebid(hands['S'], e_suit, s2_bid)  # אותה לוגיקה
        s2_suit = suit_of(s2_bid)

        auction.append('Pass')
        try:
            n2_bid, n2_expl = respond_to_cue(
                hands['N'], s2_suit, opp_suit=e_suit, n_hand=hands['S'])
        except Exception as ex:
            exceptions += 1
            errs.append(f'respond_to_cue (N) קרס: {ex}')
            print_bug('שלב2', deal_num, hands, auction, errs)
            continue

        auction.append(n2_bid)
        # N מעלה ל-4M אחרי 3M
        if n2_bid[0] == '3' and suit_of(n2_bid) in ('H', 'S'):
            game = f'4{_S[suit_of(n2_bid)]}'
            auction += ['Pass', game, 'Pass', 'Pass', 'Pass']
            final_bid = game
        else:
            auction += ['Pass', 'Pass', 'Pass']
            final_bid = n2_bid

    # ── S מחליט פס/העלאה אחרי תגובת N (לא קיו ביט) ─────────────────────────
    else:
        auction.append('Pass')
        try:
            s2_bid, s2_expl = doubler_raises(hands['S'], n_bid, e_suit)
        except Exception as ex:
            exceptions += 1
            errs.append(f'doubler_raises (S) קרס: {ex}')
            print_bug('שלב2', deal_num, hands, auction, errs)
            continue

        auction.append(s2_bid)
        if s2_bid != 'Pass':
            auction += ['Pass', 'Pass', 'Pass']
            final_bid = s2_bid
        else:
            auction += ['Pass', 'Pass']

    errs += verify_game(sn, ss, final_bid, s_bid=n_bid, opp_suit=e_suit)
    if final_bid in GAME_BIDS:
        games_p2 += 1
    if errs:
        print_bug('שלב2', deal_num, hands, auction, errs)

p2_bugs = bugs_found - p1_bugs

# ─── תוצאות ──────────────────────────────────────────────────────────────────
print(f'\n{"═"*60}')
print(f'  שלב 1 — חלוקות: {total_p1}  |  באגים: {p1_bugs}  |  משחקים: {games_found}/{total_p1}')
print(f'  שלב 2 — חלוקות: {total_p2}  |  באגים: {p2_bugs}  |  משחקים: {games_p2}/{total_p2}')
print(f'  קריסות:  {exceptions}')
print(f'{"═"*60}')
if bugs_found == 0:
    print('  ✓ לא נמצאו באגים!')
