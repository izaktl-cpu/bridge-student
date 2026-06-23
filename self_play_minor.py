# -*- coding: utf-8 -*-
"""
סימולטור שני-שחקנים — פתיחת מינור.
N ו-S מכריזים אוטומטית; הסקייל מאתר טעויות לוגיות ומדפיס אותן.
"""
import sys, io, random
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine.opening   import opening_bid
from engine.response  import respond_minor, responder_continuation_after_minor
from engine.rebid     import opener_rebid, opener_later_bid
from engine.scoring   import hcp, distribution, is_balanced
from engine.deal_constraints import deal_robot_opens_minor
from engine.cards     import SUIT_SYMBOLS

_S = SUIT_SYMBOLS
FINAL = {'3NT','4♥','4♠','5♣','5♦','Pass'}
GAME  = {'3NT','4♥','4♠','5♣','5♦'}

# ── הגדרות ──────────────────────────────────────────────────────────────────
DEALS      = 2000
SHOW_BUGS  = True   # הדפס פרטי כל באג
MAX_BUGS   = 30     # עצור אחרי N באגים (למניעת flood)
random.seed(None)   # אקראי בכל ריצה

# ── עזרים ───────────────────────────────────────────────────────────────────
def hand_str(hand):
    d = distribution(hand)
    suits = []
    for suit, sym in [('S','♠'),('H','♥'),('D','♦'),('C','♣')]:
        cards = sorted([c for c in hand if c.endswith(suit)],
                       key=lambda c: 'AKQJT98765432'.index(c[0]))
        suits.append(f'{sym} {"".join(c[0] for c in cards)}')
    return '  '.join(suits)

def suit_of(bid):
    for ch, suit in {'♠':'S','♥':'H','♦':'D','♣':'C'}.items():
        if ch in bid:
            return suit
    return None

def bid_level(bid):
    return int(bid[0]) if bid and bid[0].isdigit() else 0

# ── בדיקות לוגיות ──────────────────────────────────────────────────────────
def check_s_response(hand, bid, hn, hs, minor, sym):
    """בדיקות על תגובת S הראשונה."""
    errors = []
    d = distribution(hand)
    if hs <= 5 and bid != 'Pass':
        errors.append(f'S עם {hs} נק\' הכריז {bid} במקום Pass')
    if hs >= 6 and bid == 'Pass':
        errors.append(f'S עם {hs} נק\' פסם')
    suit = suit_of(bid)
    if suit in ('H','S') and bid.startswith('1') and d.get(suit,0) < 4:
        errors.append(f'S הכריז {bid} עם {d.get(suit,0)} קלפים בלבד')
    if bid == f'2{sym}' and d.get(minor,0) < (5 if minor=='C' else 4):
        errors.append(f'S תמך ב-{bid} עם {d.get(minor,0)} קלפי {sym} בלבד')
    return errors

def check_n_rebid(hand, bid, hn, s_resp, sym, minor):
    """בדיקות על rebid של N."""
    errors = []
    d = distribution(hand)
    s_suit = suit_of(s_resp)

    if bid == '1♠' and d.get('S',0) < 4:
        errors.append(f'N הכריז 1♠ עם {d["S"]} קלפי ♠ בלבד')
    if bid == '1♥' and d.get('H',0) < 4:
        errors.append(f'N הכריז 1♥ עם {d["H"]} קלפי ♥ בלבד')
    if bid in ('2♥','3♥','4♥') and d.get('H',0) < 3:
        errors.append(f'N תמך ב-{bid} עם {d["H"]} קלפי ♥ בלבד')
    if bid in ('2♠','3♠','4♠') and d.get('S',0) < 3:
        errors.append(f'N תמך ב-{bid} עם {d["S"]} קלפי ♠ בלבד')
    if bid == '1NT' and s_suit == 'H' and d.get('S',0) >= 4:
        errors.append(f'N הכריז 1NT עם 4 קלפי ♠ — היה צריך להכריז 1♠')
    if bid == '1NT' and s_suit in ('D','C') and (d.get('S',0) >= 4 or d.get('H',0) >= 4):
        maj = '♠' if d.get('S',0) >= 4 else '♥'
        errors.append(f'N הכריז 1NT עם 4 קלפי {maj} — היה צריך להכריז 1{maj}')
    if bid == f'2{sym}' and d.get(minor,0) < 4:
        errors.append(f'N חזר ל-{bid} עם {d.get(minor,0)} קלפי {sym} בלבד')
    return errors

def check_game_missed(hn, hs, final_bid):
    """האם פספסו משחק עם 26+ נקודות?"""
    if hn + hs >= 26 and final_bid not in GAME:
        return [f'N+S={hn+hs} נק\' אך הגיעו ל-{final_bid} בלבד (לא משחק)']
    return []

def check_overcall(hn, hs, final_bid):
    """האם הכריזו יותר מדי עם נקודות מועטות?"""
    if hn + hs < 22 and final_bid in ('3NT','4♥','4♠'):
        return [f'N+S={hn+hs} נק\' אך הגיעו ל-{final_bid} (יתר על המידה)']
    return []

def _print_bug(num, N, S, hn, hs, auction, errors):
    global bugs_found
    print(f'{"─"*56}')
    print(f'  באג #{bugs_found+1}  (חלוקה {num+1})')
    print(f'  N ({hn} נק\'): {hand_str(N)}')
    print(f'  S ({hs} נק\'): {hand_str(S)}')
    print(f'  מכרז: {" → ".join(auction)}')
    for e in errors:
        print(f'  ⚠ {e}')
    print()
    bugs_found += 1

# ── לולאת הסימולציה ──────────────────────────────────────────────────────────
bugs_found = 0
games = 0
total_played = 0

print(f'\nמריץ {DEALS} חלוקות...\n')

for deal_num in range(DEALS):
    if bugs_found >= MAX_BUGS:
        print(f'\n⚠ הגענו ל-{MAX_BUGS} באגים — עוצרים.')
        break

    minor = random.choice(['C','D'])
    r = random.random()
    scenario = 'major_fit' if r < 0.5 else ('nt' if r < 0.8 else 'free')
    try:
        hands = deal_robot_opens_minor(minor, scenario=scenario)
    except RuntimeError:
        continue

    N, S = hands['N'], hands['S']
    sym = _S[minor]
    hn, hs = hcp(N), hcp(S)
    total_played += 1

    auction = [f'1{sym}']  # N פתח
    deal_errors = []

    # ── סיבוב 1: S עונה ──────────────────────────────────────────────────
    try:
        s1, _ = respond_minor(S, minor)
    except Exception as e:
        deal_errors.append(f'respond_minor נכשל: {e}')
        s1 = 'Pass'

    deal_errors += check_s_response(S, s1, hn, hs, minor, sym)
    auction.append(s1)

    if s1 in FINAL:
        if s1 in GAME:
            games += 1
        deal_errors += check_game_missed(hn, hs, s1)
        deal_errors += check_overcall(hn, hs, s1)
        if deal_errors and SHOW_BUGS:
            _print_bug(deal_num, N, S, hn, hs, auction, deal_errors)
        continue

    # ── סיבוב 2: N מכריז מחדש ───────────────────────────────────────────
    try:
        n1, _ = opener_rebid(N, f'1{sym}', s1)
    except Exception as e:
        deal_errors.append(f'opener_rebid נכשל: {e}')
        n1 = 'Pass'

    deal_errors += check_n_rebid(N, n1, hn, s1, sym, minor)
    auction.append(n1)

    if n1 in FINAL:
        if n1 in GAME:
            games += 1
        deal_errors += check_game_missed(hn, hs, n1)
        deal_errors += check_overcall(hn, hs, n1)
        if deal_errors and SHOW_BUGS:
            _print_bug(deal_num, N, S, hn, hs, auction, deal_errors)
        continue

    # ── סיבוב 3: S ממשיך ─────────────────────────────────────────────────
    try:
        s2, _ = responder_continuation_after_minor(S, s1, n1)
    except Exception as e:
        deal_errors.append(f'responder_continuation נכשל: {e}')
        s2 = 'Pass'

    auction.append(s2)

    if s2 in FINAL:
        if s2 in GAME:
            games += 1
        deal_errors += check_game_missed(hn, hs, s2)
        deal_errors += check_overcall(hn, hs, s2)
        if deal_errors and SHOW_BUGS:
            _print_bug(deal_num, N, S, hn, hs, auction, deal_errors)
            bugs_found += 1
        continue

    # ── סיבוב 4: N מכריז שוב ─────────────────────────────────────────────
    s_first = s1
    _agreed = minor if (f'2{sym}' in s_first or f'3{sym}' in s_first or n1 == f'3{sym}') else None
    _6h = (s_first == '1♥' and s2 == '3♥')
    try:
        n2, _ = opener_later_bid(N, s2, agreed_minor=_agreed, s_showed_6h=_6h)
    except Exception as e:
        deal_errors.append(f'opener_later_bid נכשל: {e}')
        n2 = 'Pass'

    auction.append(n2)

    if n2 in FINAL:
        if n2 in GAME:
            games += 1
        deal_errors += check_game_missed(hn, hs, n2)
        deal_errors += check_overcall(hn, hs, n2)
        if deal_errors and SHOW_BUGS:
            _print_bug(deal_num, N, S, hn, hs, auction, deal_errors)
            bugs_found += 1
        continue

    # ── סיבוב 5: S מגיב שוב ───────────────────────────────────────────────
    try:
        s3, _ = responder_continuation_after_minor(S, s2, n2)
    except Exception as e:
        deal_errors.append(f'responder_continuation s3 נכשל: {e}')
        s3 = 'Pass'

    auction.append(s3)
    final = s3

    if s3 in GAME:
        games += 1
    deal_errors += check_game_missed(hn, hs, final)
    deal_errors += check_overcall(hn, hs, final)

    if deal_errors and SHOW_BUGS:
        _print_bug(deal_num, N, S, hn, hs, auction, deal_errors)
        bugs_found += 1


def _print_bug(num, N, S, hn, hs, auction, errors):
    print(f'{"─"*56}')
    print(f'  באג #{bugs_found+1}  (חלוקה {num+1})')
    print(f'  N ({hn} נק\'): {hand_str(N)}')
    print(f'  S ({hs} נק\'): {hand_str(S)}')
    print(f'  מכרז: {" → ".join(auction)}')
    for e in errors:
        print(f'  ⚠ {e}')
    print()


# ── תוצאות ──────────────────────────────────────────────────────────────────
print(f'\n{"═"*56}')
print(f'  חלוקות: {total_played}')
print(f'  באגים:  {bugs_found}')
print(f'  משחקים: {games}/{total_played} = {games/total_played*100:.0f}%')
print(f'{"═"*56}')
if bugs_found == 0:
    print('  ✓ לא נמצאו באגים!')
