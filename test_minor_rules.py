# -*- coding: utf-8 -*-
"""
בדיקה מקיפה של כל חוקי המינורים:
  שכבה 1 — hand-crafted: respond, rebid, continuation, stopper ask, קפיצה
  שכבה 2 — fuzz: 500 חלוקות, עקביות לוגית
"""

import sys, io, random
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine.response import respond_minor, responder_continuation_after_minor
from engine.rebid    import opener_rebid, opener_later_bid
from engine.scoring  import hcp as get_hcp, distribution, is_balanced, has_stopper
from engine.deal_constraints import deal_robot_opens_minor
from engine.opening  import opening_bid

# ─── בנאי ידיים ──────────────────────────────────────────────────────────────
_DECKS = {
    'S': 'AS KS QS JS TS 9S 8S 7S 6S 5S 4S 3S 2S'.split(),
    'H': 'AH KH QH JH TH 9H 8H 7H 6H 5H 4H 3H 2H'.split(),
    'D': 'AD KD QD JD TD 9D 8D 7D 6D 5D 4D 3D 2D'.split(),
    'C': 'AC KC QC JC TC 9C 8C 7C 6C 5C 4C 3C 2C'.split(),
}
_HCP_VAL = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}


def build(s, h, d, c, target_hcp=0):
    assert s + h + d + c == 13, f'סה״כ {s+h+d+c} != 13'
    result, remaining = [], target_hcp
    for suit, n in [('S', s), ('H', h), ('D', d), ('C', c)]:
        cards = []
        for card in _DECKS[suit]:
            if len(cards) == n: break
            val = _HCP_VAL.get(card[0], 0)
            if val > 0:
                if remaining >= val:
                    cards.append(card); remaining -= val
            else:
                cards.append(card)
        for card in reversed(_DECKS[suit]):
            if len(cards) == n: break
            if card not in cards: cards.append(card)
        result.extend(cards)
    return result


def build_with_cards(s_cards, h_cards, d_cards, c_cards):
    """בונה יד מקלפים ספציפיים."""
    hand = s_cards + h_cards + d_cards + c_cards
    assert len(hand) == 13
    return hand


# ─── מנגנון בדיקה ────────────────────────────────────────────────────────────
failures, passes = [], 0


def chk(label, got, want, hand=None):
    global passes
    bid = got[0] if isinstance(got, tuple) else got
    ok  = (bid == want)
    if ok:
        passes += 1
    else:
        h_info = ''
        if hand:
            d = distribution(hand)
            h_info = f'  [hcp={get_hcp(hand)} {d["S"]}-{d["H"]}-{d["D"]}-{d["C"]}]'
        failures.append(f'FAIL  {label}{h_info}')
        if isinstance(got, tuple):
            failures.append(f'      got={got[0]!r}  ({got[1][:60]})')
        else:
            failures.append(f'      got={got!r}')
        failures.append(f'      want={want!r}')
    return ok


def section(title):
    print()
    print('══════════════════════════════════════════════════════')
    print(f'  {title}')
    print('══════════════════════════════════════════════════════')


# ════════════════════════════════════════════════════════════════════════════════
section('has_stopper')
# ════════════════════════════════════════════════════════════════════════════════

chk('stopper: A     = עוצר',   has_stopper(['AH','2H','3S','4S','5S','6S','7S','8S','9S','TS','JS','QS','KS'], 'H'), True)
chk('stopper: Kx    = עוצר',   has_stopper(['KH','2H','3S','4S','5S','6S','7S','8S','9S','TS','JS','QS','AS'], 'H'), True)
chk('stopper: Qxx   = עוצר',   has_stopper(['QH','2H','3H','4S','5S','6S','7S','8S','9S','TS','JS','AS','KS'], 'H'), True)
chk('stopper: Jxxxx = עוצר',   has_stopper(['JH','2H','3H','4H','5S','6S','7S','8S','9S','TS','JS','AS','KS'], 'H'), True)
chk('stopper: J     = לא',     has_stopper(['JH','2S','3S','4S','5S','6S','7S','8S','9S','TS','QS','AS','KS'], 'H'), False)
chk('stopper: Qx    = לא',     has_stopper(['QH','2H','3S','4S','5S','6S','7S','8S','9S','TS','JS','AS','KS'], 'H'), False)
chk('stopper: חוסר = לא',      has_stopper(['2S','3S','4S','5S','6S','7S','8S','9S','TS','JS','QS','AS','KS'], 'H'), False)


# ════════════════════════════════════════════════════════════════════════════════
section('respond_minor אחרי 1♣ — כל הטווחים')
# ════════════════════════════════════════════════════════════════════════════════

# Pass
chk('1C 0hcp → Pass',  respond_minor(build(3,3,4,3,0),  'C'), 'Pass')
chk('1C 5hcp → Pass',  respond_minor(build(3,3,4,3,5),  'C'), 'Pass')

# מיגורים — עדיפות ראשונה
chk('1C 4♠ 7hcp → 1♠', respond_minor(build(4,3,3,3,7), 'C'), '1♠')
chk('1C 4♥ no4♠ → 1♥', respond_minor(build(3,4,3,3,7), 'C'), '1♥')
chk('1C 4♠=4♥ → 1♥',   respond_minor(build(4,4,2,3,9), 'C'), '1♥')
chk('1C 5♠+4♥ → 1♠',   respond_minor(build(5,4,1,3,9), 'C'), '1♠')
chk('1C 5♠+4♥+13 → 1♠',respond_minor(build(5,4,1,3,13),'C'), '1♠')   # first response always 1♠

# 1♦ up-the-line לפני ♥/♠
chk('1C 4♦+4♥ → 1♦',   respond_minor(build(2,4,4,3,9), 'C'), '1♦')

# NT ותמיכה
chk('1C bal 8hcp → 1NT',  respond_minor(build(3,3,3,4,8),  'C'), '1NT')
chk('1C 6♣ nonbal 8hcp → 2♣',  respond_minor(build(2,2,3,6,8),  'C'), '2♣')
chk('1C 5♣ bal 8hcp → 2♣',     respond_minor(build(3,3,2,5,8),  'C'), '2♣')
chk('1C bal 11hcp → 2NT',       respond_minor(build(3,3,3,4,11), 'C'), '2NT')
chk('1C bal 12hcp → 2NT',       respond_minor(build(3,3,3,4,12), 'C'), '2NT')
chk('1C 6♣ nonbal 11hcp → 3♣',  respond_minor(build(2,2,3,6,11), 'C'), '3♣')
chk('1C 6♣ nonbal 12hcp → 3♣',  respond_minor(build(2,2,3,6,12), 'C'), '3♣')
chk('1C bal 13hcp → 3NT',       respond_minor(build(3,3,3,4,13), 'C'), '3NT')
chk('1C 6♣ nonbal 13hcp → 3NT', respond_minor(build(2,2,3,6,13), 'C'), '3NT')


# ════════════════════════════════════════════════════════════════════════════════
section('respond_minor אחרי 1♦')
# ════════════════════════════════════════════════════════════════════════════════

chk('1D 5hcp → Pass',          respond_minor(build(3,3,4,3,5),  'D'), 'Pass')
chk('1D 4♠ → 1♠',              respond_minor(build(4,3,3,3,7),  'D'), '1♠')
chk('1D 4♥ no4♠ → 1♥',         respond_minor(build(3,4,3,3,7),  'D'), '1♥')
chk('1D bal 8hcp → 1NT',        respond_minor(build(3,3,3,4,8),  'D'), '1NT')
chk('1D 4♦ bal → 1NT (not 2♦)',respond_minor(build(3,3,4,3,8),  'D'), '1NT')
chk('1D 5♦ nonbal 8hcp → 2♦',  respond_minor(build(2,2,5,4,8),  'D'), '2♦')
# יד עם עוצרים בכל הצבעים: ♠AJx ♥Qxx ♦xxxx ♣KJx = 11 נק'
chk('1D bal 11hcp עוצרים → 2NT', respond_minor(
    build_with_cards(['AS','JS','2S'],['QH','5H','2H'],['9D','8D','4D','2D'],['KC','JC','2C']), 'D'), '2NT')
# יד עם 4♦ בלנסד אך חסר עוצר ♣ → תמיכה ב-3♦
chk('1D 4♦ bal 11hcp ללא עוצר♣ → 3♦', respond_minor(build(3,3,4,3,11), 'D'), '3♦')
chk('1D 5♦ nonbal 11hcp → 3♦',  respond_minor(build(2,2,5,4,11), 'D'), '3♦')
chk('1D bal 13hcp → 3NT',       respond_minor(build(3,3,4,3,13), 'D'), '3NT')
chk('1D 6♣ no4♦ 11hcp → 2♣',  respond_minor(build(2,2,3,6,11), 'D'), '2♣')


# ════════════════════════════════════════════════════════════════════════════════
section('responder_continuation — אחרי תמיכה ב-2M')
# ════════════════════════════════════════════════════════════════════════════════

# S הכריז 1♠, N תמך 2♠ (12-14). S ממשיך:
s1 = build(5,3,2,3, 8)   # 8 HCP + void-free → pass
s2 = build(5,3,2,3,10)   # 10 HCP → 3♠ הזמנה
s3 = build(5,3,2,3,13)   # 13 HCP → 4♠ משחק
s4 = build(5,2,1,5,11)   # 11 HCP + singleton → נקודות חלוקה

chk('cont 2♠: 8hcp  → Pass', responder_continuation_after_minor(s1,'1♠','2♠'), 'Pass')
chk('cont 2♠: 10hcp → 3♠',  responder_continuation_after_minor(s2,'1♠','2♠'), '3♠')
chk('cont 2♠: 13hcp → 4♠',  responder_continuation_after_minor(s3,'1♠','2♠'), '4♠')

# S הכריז 1♥, N תמך 2♥ (12-14)
h1 = build(2,5,3,3, 8)
h2 = build(2,5,3,3,10)
h3 = build(2,5,3,3,13)

chk('cont 2♥: 8hcp  → Pass', responder_continuation_after_minor(h1,'1♥','2♥'), 'Pass')
chk('cont 2♥: 10hcp → 3♥',  responder_continuation_after_minor(h2,'1♥','2♥'), '3♥')
chk('cont 2♥: 13hcp → 4♥',  responder_continuation_after_minor(h3,'1♥','2♥'), '4♥')


# ════════════════════════════════════════════════════════════════════════════════
section('responder_continuation — 5♠+4♥ אחרי 1NT')
# ════════════════════════════════════════════════════════════════════════════════

# S הכריז 1♠, N הכריז 1NT (ללא תמיכה)
nt1 = build(5,4,1,3, 8)   # 8 HCP → 2♠ (חזרה חלשה)
nt2 = build(5,4,1,3, 9)   # 9 HCP → 2♥ (מראה שנייה)
nt3 = build(5,4,1,3,11)   # 11 HCP → 2♥
nt4 = build(5,4,1,3,13)   # 13 HCP → 3♥ קפיצה!
nt5 = build(5,4,1,3,14)   # 14 HCP → 3♥ קפיצה!

chk('5♠4♥ 1NT 8hcp  → 2♠ (חזרה)', responder_continuation_after_minor(nt1,'1♠','1NT'), '2♠')
chk('5♠4♥ 1NT 9hcp  → 2♥',         responder_continuation_after_minor(nt2,'1♠','1NT'), '2♥')
chk('5♠4♥ 1NT 11hcp → 2♥',         responder_continuation_after_minor(nt3,'1♠','1NT'), '2♥')
chk('5♠4♥ 1NT 13hcp → 3♥ קפיצה',  responder_continuation_after_minor(nt4,'1♠','1NT'), '3♥')
chk('5♠4♥ 1NT 14hcp → 3♥ קפיצה',  responder_continuation_after_minor(nt5,'1♠','1NT'), '3♥')


# ════════════════════════════════════════════════════════════════════════════════
section('responder_continuation — stopper ask אחרי 3♣/3♦')
# ════════════════════════════════════════════════════════════════════════════════

# S הכריז 2♣, N הכריז 3♣ (הזמנה). S בוחן stopper:
# ידיים: 10 HCP, 5♣, לא מאוזן [2-2-4-5] — בדיוק גבול ל-2♣

# יד עם עוצרים בשניהם → 3NT
# AS(4)+KH(3)+QD(2)+JD(1) = 10 HCP
st1 = build_with_cards(
    ['AS','2S'],            # ♠: Ax = עוצר
    ['KH','4H'],            # ♥: Kx = עוצר
    ['QD','JD','9D','6D'],  # ♦: 4 קלפים
    ['9C','8C','7C','6C','5C']  # ♣: 5 קלפים
)
chk('stopper: A♠+K♥ → 3NT', responder_continuation_after_minor(st1,'2♣','3♣'), '3NT')

# יד ללא עוצר בלב → 3♥ (stopper ask)
# AS(4)+KD(3)+QD(2)+JC(1) = 10 HCP
st2 = build_with_cards(
    ['AS','2S'],            # ♠: Ax = עוצר
    ['7H','4H'],            # ♥: xx = אין עוצר!
    ['KD','QD','9D','6D'],  # ♦
    ['JC','9C','7C','6C','5C']
)
chk('stopper: A♠ no♥ → 3♥ ask', responder_continuation_after_minor(st2,'2♣','3♣'), '3♥')

# יד ללא עוצר בספייד → 3♠ (stopper ask)
# KH(3)+QD(2)+JD(1)+AC(4) = 10 HCP
st3 = build_with_cards(
    ['7S','2S'],            # ♠: xx = אין עוצר!
    ['KH','4H'],            # ♥: Kx = עוצר
    ['QD','JD','9D','6D'],  # ♦
    ['AC','9C','7C','6C','5C']
)
chk('stopper: K♥ no♠ → 3♠ ask', responder_continuation_after_minor(st3,'2♣','3♣'), '3♠')

# פחות מ-10 נקודות → Pass
st4 = build(3,3,2,5, 8)   # 8 HCP → דוחה הזמנה
chk('stopper: 8hcp → Pass',   responder_continuation_after_minor(st4,'2♣','3♣'), 'Pass')

# אחרי 3♦ — AS(4)+KH(3)+QD(2)+JD(1)=10, שנייה ל-2♦
st5 = build_with_cards(
    ['AS','2S'],            # ♠: Ax = עוצר
    ['KH','4H'],            # ♥: Kx = עוצר
    ['QD','JD','9D','6D'],  # ♦: 4 קלפים
    ['9C','8C','7C','6C','5C']
)
chk('stopper 3♦: A♠+K♥ → 3NT', responder_continuation_after_minor(st5,'2♦','3♦'), '3NT')


# ════════════════════════════════════════════════════════════════════════════════
section('opener_rebid — N מראה מיגור אחרי תגובת מינור (1♣→1♦ / 1♦→1♥)')
# ════════════════════════════════════════════════════════════════════════════════

# 1♣ → 1♦: N עם 4♠ → מכריז 1♠
n_4s_after_1d = build_with_cards(
    ['KS','8S','7S','4S'],     # 4 ספיידים
    ['KH','JH','3H'],          # 3 לבות
    ['7D','3D'],               # 2 דיאמונדים
    ['AС','QC','5C','4C']      # 4 קלובים
)
chk('1♣→1♦: N עם 4♠ → 1♠', opener_rebid(n_4s_after_1d, '1♣', '1♦'), '1♠')

# 1♣ → 1♦: N עם 4♥ (ללא 4♠) → מכריז 1♥
n_4h_after_1d = build_with_cards(
    ['KS','8S'],               # 2 ספיידים
    ['AH','QH','4H','2H'],     # 4 לבות
    ['7D','3D'],               # 2 דיאמונדים
    ['AС','QC','JC','5C','4C'] # 5 קלובים
)
chk('1♣→1♦: N עם 4♥ בלי 4♠ → 1♥', opener_rebid(n_4h_after_1d, '1♣', '1♦'), '1♥')

# 1♣ → 1♦: N ללא מיגור (3-3-2-5) → 1NT
n_no_major_after_1d = build_with_cards(
    ['KS','8S','3S'],          # 3 ספיידים
    ['AH','JH','3H'],          # 3 לבות
    ['7D','3D'],               # 2 דיאמונדים
    ['AС','QC','JC','5C','4C'] # 5 קלובים
)
chk('1♣→1♦: N ללא 4-קלף מיגור → 1NT', opener_rebid(n_no_major_after_1d, '1♣', '1♦'), '1NT')

# 1♦ → 1♥: N עם 4♠ → מכריז 1♠
n_4s_after_1h = build_with_cards(
    ['KS','8S','7S','4S'],     # 4 ספיידים
    ['JH','3H'],               # 2 לבות
    ['AD','QD','9D','7D','6D'],# 5 דיאמונדים
    ['AС','4C']                # 2 קלובים
)
chk('1♦→1♥: N עם 4♠ → 1♠', opener_rebid(n_4s_after_1h, '1♦', '1♥'), '1♠')

# 1♦ → 1♥: N ללא 4♠ ו-6♦ → 2♦
n_6d_after_1h = build_with_cards(
    ['KS','8S','3S'],          # 3 ספיידים
    ['JH','3H'],               # 2 לבות
    ['AD','QD','9D','7D','6D','2D'], # 6 דיאמונדים
    ['AС','4C']                # 2 קלובים
)
chk('1♦→1♥: N עם 6♦ ללא 4♠ → 2♦', opener_rebid(n_6d_after_1h, '1♦', '1♥'), '2♦')


# ════════════════════════════════════════════════════════════════════════════════
section('opener_later_bid — תגובה ל-stopper ask (agreed_minor)')
# ════════════════════════════════════════════════════════════════════════════════

# N יש עוצר בלב → 3NT
n_yes_h = build_with_cards(
    ['QS','6S'],
    ['KH','9H','4H'],       # K♥xx = עוצר
    ['KD','QD','TD','7D'],
    ['KC','QC','JC','8C']
)
chk('stopper ask 3♥: N has K♥ → 3NT',
    opener_later_bid(n_yes_h, '3♥', agreed_minor='C'), '3NT')

# N אין עוצר בלב → 5♣
n_no_h = build_with_cards(
    ['QS','6S'],
    ['7H','4H','2H'],       # xxx = אין עוצר
    ['KD','QD','TD','7D'],
    ['KC','QC','JC','8C']
)
chk('stopper ask 3♥: N no ♥ → 5♣',
    opener_later_bid(n_no_h, '3♥', agreed_minor='C'), '5♣')

# N יש עוצר בספייד → 3NT
n_yes_s = build_with_cards(
    ['KS','9S','4S'],       # K♠xx = עוצר
    ['7H','4H','2H'],
    ['KD','QD','TD','7D'],
    ['KC','QC','JC']
)
chk('stopper ask 3♠: N has K♠ → 3NT',
    opener_later_bid(n_yes_s, '3♠', agreed_minor='C'), '3NT')

# N אין עוצר בספייד → 5♣
n_no_s = build_with_cards(
    ['7S','4S','2S'],       # xxx = אין עוצר
    ['KH','9H','4H'],
    ['KD','QD','TD','7D'],
    ['KC','QC','JC']
)
chk('stopper ask 3♠: N no ♠ → 5♣',
    opener_later_bid(n_no_s, '3♠', agreed_minor='C'), '5♣')

# agreed_minor=D → 5♦
n_no_h2 = build_with_cards(
    ['QS','6S'],
    ['7H','4H','2H'],
    ['KD','QD','TD','7D'],
    ['KC','QC','JC','8C']
)
chk('stopper ask 3♥ agreed=D: no♥ → 5♦',
    opener_later_bid(n_no_h2, '3♥', agreed_minor='D'), '5♦')


# ════════════════════════════════════════════════════════════════════════════════
section('opener_later_bid — תגובה ל-3♥ טבעי (5♠+4♥, no agreed_minor)')
# ════════════════════════════════════════════════════════════════════════════════

# N יש 4♥ → 4♥
n_4h = build_with_cards(
    ['JS','TS','6S'],
    ['QH','JH','TH','9H'],  # 4 לבות
    ['KD','4D'],
    ['KC','QC','6C','3C']
)
chk('3♥ natural: N has 4♥ → 4♥',
    opener_later_bid(n_4h, '3♥', agreed_minor=None), '4♥')

# N יש 3♥ → 3NT
n_3h = build_with_cards(
    ['JS','TS','6S'],
    ['QH','JH','TH'],       # 3 לבות
    ['KD','4D','3D'],
    ['KC','QC','6C','3C']
)
chk('3♥ natural: N has 3♥ → 3NT',
    opener_later_bid(n_3h, '3♥', agreed_minor=None), '3NT')

# N יש 2♥ → 3♠ (חוזר לספייד)
n_2h = build_with_cards(
    ['JS','TS','6S'],
    ['QH','JH'],            # 2 לבות
    ['KD','4D','3D','2D'],
    ['KC','QC','6C','3C']
)
chk('3♥ natural: N has 2♥ → 3♠',
    opener_later_bid(n_2h, '3♥', agreed_minor=None), '3♠')


# ════════════════════════════════════════════════════════════════════════════════
section('opener_later_bid — S הראה 6 קלפי ♥ (1♥→3♥ קפיצה, s_showed_6h=True)')
# ════════════════════════════════════════════════════════════════════════════════

# N יש 2♥ + 6♣ + 16 HCP (כמו הדוגמה מהשיעור) → 4♥ (6+2=8)
n_6h_real = build_with_cards(
    ['AS','TS','6S'],          # 3 ספיידים
    ['KH','9H'],               # 2 לבות (K9)
    ['AD','2D'],               # 2 דיאמונדים
    ['KС','QC','9C','4C','3C','2C']
)
chk('6♥ jump: N has 2♥ → 4♥',
    opener_later_bid(n_6h_real, '3♥', agreed_minor=None, s_showed_6h=True), '4♥')

# N יש 3♥ → 4♥ (ממילא)
n_6h_3h = build_with_cards(
    ['AS','TS'],               # 2 ספיידים
    ['KH','9H','6H'],          # 3 לבות
    ['AD','2D'],               # 2 דיאמונדים
    ['KС','QC','JC','9C','4C','3C']
)
chk('6♥ jump: N has 3♥ → 4♥',
    opener_later_bid(n_6h_3h, '3♥', agreed_minor=None, s_showed_6h=True), '4♥')

# N יש 0♥ (סינגלטון לבד) → 3NT
n_6h_0h = build_with_cards(
    ['AS','KS','TS','6S'],     # 4 ספיידים
    [],                        # 0 לבות
    ['AD','KD','2D'],          # 3 דיאמונדים
    ['QC','JC','9C','4C','3C','2C']
)
chk('6♥ jump: N has 0♥ → 3NT',
    opener_later_bid(n_6h_0h, '3♥', agreed_minor=None, s_showed_6h=True), '3NT')


# ════════════════════════════════════════════════════════════════════════════════
section('מכרז מלא end-to-end — ידיים ספציפיות')
# ════════════════════════════════════════════════════════════════════════════════

def full_auction_minor(north, south, minor, label, expect_contract=None):
    """מריץ מכרז מלא ומחזיר חוזה סופי."""
    from engine.cards import SUIT_SYMBOLS
    sym = SUIT_SYMBOLS[minor]

    s1_bid, _  = respond_minor(south, minor)
    if s1_bid in ('Pass','3NT','4♥','4♠','5♣','5♦'):
        return s1_bid

    n1_bid, _  = opener_rebid(north, f'1{sym}', s1_bid)
    if n1_bid in ('Pass','3NT','4♥','4♠','5♣','5♦'):
        return n1_bid

    s_first = s1_bid
    s_agreed = f'2{sym}' in s_first or f'3{sym}' in s_first
    s2_bid, _  = responder_continuation_after_minor(south, s1_bid, n1_bid)
    if s2_bid in ('Pass','3NT','4♥','4♠','5♣','5♦'):
        return s2_bid

    _agreed = minor if s_agreed else None
    n2_bid, _  = opener_later_bid(north, s2_bid, agreed_minor=_agreed)
    return n2_bid


# יד 1: 1♣-1♠-1NT-3♥(קפיצה)-4♥  [N עם 2♠ בלבד → 1NT, לא תמיכה]
e2n = ['TS','6S','QH','JH','TH','9H','KD','4D','3D','KC','QC','6C','3C']
e2s = ['AS','KS','8S','5S','2S','AH','KH','8H','5H','8C','7C','4C','2C']
result = full_auction_minor(e2n, e2s, 'C', 'קפיצה 3♥→4♥')
chk('e2e קפיצה: 1♣-1♠-1NT-3♥-4♥', (result,''), '4♥')

# יד 2: stopper ask 1♣-2♣-3♣-3♥-3NT
# N: KH=עוצר, 15 HCP. S: AS+אין K♥, 10 HCP, 5♣
st_n = build_with_cards(['QS','6S'],['KH','9H','4H'],['KD','QD','TD','7D'],['KC','QC','JC','8C'])
st_s = build_with_cards(['AS','2S'],['7H','4H'],['KD_x','QD_x','9D','6D'],['JC','9C','7C','6C','5C'])
# בונה ידנית (קלפי ♦ ייחודיים):
# AS(4)+KC(3)+QC(2)+JC(1)=10 HCP, 3-2-2-6 לא מאוזן, ללא 4+♦
st_s = ['AS','7S','2S','7H','4H','9D','6D','KC','QC','JC','9C','8C','7C']
result2 = full_auction_minor(st_n, st_s, 'C', 'stopper ask → 3NT')
chk('e2e stopper: 1♣-2♣-3♣-3♥-3NT', (result2,''), '3NT')


# ════════════════════════════════════════════════════════════════════════════════
section('FUZZ — 500 חלוקות אקראיות: עקביות לוגית')
# ════════════════════════════════════════════════════════════════════════════════

FINAL_CONTRACTS = {'3NT','4♥','4♠','5♣','5♦','Pass'}
GAME_CONTRACTS  = {'3NT','4♥','4♠','5♣','5♦'}

fuzz_errors  = 0
games_count  = 0
total_fuzz   = 500
random.seed(42)

for i in range(total_fuzz):
    minor = random.choice(['C','D'])
    r = random.random()
    scenario = 'major_fit' if r < 0.5 else ('nt' if r < 0.8 else 'free')
    try:
        hands = deal_robot_opens_minor(minor, scenario=scenario)
    except RuntimeError:
        continue

    north, south = hands['N'], hands['S']
    hn, hs = get_hcp(north), get_hcp(south)
    dn, ds = distribution(north), distribution(south)

    from engine.cards import SUIT_SYMBOLS
    sym = SUIT_SYMBOLS[minor]

    try:
        # סיבוב 1
        s1_bid, s1_why = respond_minor(south, minor)

        # כלל: 0-5 נק' → Pass תמיד
        if hs <= 5 and s1_bid != 'Pass':
            fuzz_errors += 1
            failures.append(f'FUZZ#{i} 1C: S has {hs}hcp but bid {s1_bid!r} (expected Pass)')
            continue

        # כלל: 6+ נק' → לא Pass
        if hs >= 6 and s1_bid == 'Pass':
            fuzz_errors += 1
            failures.append(f'FUZZ#{i} 1{sym}: S has {hs}hcp but passed')
            continue

        if s1_bid in FINAL_CONTRACTS:
            if s1_bid in GAME_CONTRACTS:
                games_count += 1
            continue

        # סיבוב 2
        n1_bid, _ = opener_rebid(north, f'1{sym}', s1_bid)

        if n1_bid in FINAL_CONTRACTS:
            if n1_bid in GAME_CONTRACTS:
                games_count += 1
            continue

        # כלל: N פתח מינור → לא יכול לקפוץ ל-4M ישירות אחרי מענה
        if n1_bid in ('4♥','4♠') and hn < 18:
            fuzz_errors += 1
            failures.append(f'FUZZ#{i}: N jumped to {n1_bid} with only {hn}hcp')

        # סיבוב 3
        s_first = s1_bid
        s_agreed = f'2{sym}' in s_first or f'3{sym}' in s_first
        s2_bid, _ = responder_continuation_after_minor(south, s1_bid, n1_bid)

        if s2_bid in FINAL_CONTRACTS:
            if s2_bid in GAME_CONTRACTS:
                games_count += 1
            continue

        # כלל: stopper ask (3♥/3♠) רק עם 9+ נק' — רק אחרי הזמנת מינור (3♣/3♦)
        if s2_bid in ('3♥','3♠') and not s_agreed and n1_bid in ('3♣','3♦') and hs < 9:
            fuzz_errors += 1
            failures.append(f'FUZZ#{i}: stopper ask {s2_bid} with {hs}hcp (<9)')

        # סיבוב 4
        _agreed = minor if s_agreed else None
        n2_bid, _ = opener_later_bid(north, s2_bid, agreed_minor=_agreed)

        if n2_bid in GAME_CONTRACTS:
            games_count += 1

        # כלל: לא מכריז חוזה גבוה מדי ביחס לנקודות
        if n2_bid in ('4♥','4♠') and hn + hs < 20:
            fuzz_errors += 1
            failures.append(f'FUZZ#{i}: game {n2_bid} with only {hn+hs} combined hcp')

    except Exception as e:
        fuzz_errors += 1
        failures.append(f'FUZZ#{i} EXCEPTION: {e}')

game_pct = games_count / total_fuzz * 100
fuzz_label = f'fuzz {total_fuzz} חלוקות — {fuzz_errors} שגיאות לוגיות'
chk(fuzz_label, (str(fuzz_errors),''), '0')

print()
print(f'  משחקי מלא (3NT/4M/5m): {games_count}/{total_fuzz} = {game_pct:.0f}%')
if game_pct < 60:
    failures.append(f'WARN: רק {game_pct:.0f}% משחקי מלא — מתחת ל-60% המטרה')
    print(f'  ⚠ מתחת ל-60% משחקי מלא')
else:
    print(f'  ✓ עומד ביעד 60%+ משחקי מלא')


# ════════════════════════════════════════════════════════════════════════════════
print()
total_fails = len([f for f in failures if f.startswith('FAIL') or f.startswith('WARN')])
print('══════════════════════════════════════════════════════')
print(f'  תוצאות: {passes} עברו | {total_fails} נכשלו')
print('══════════════════════════════════════════════════════')

if failures:
    print()
    for line in failures:
        print(line)
    sys.exit(1)
else:
    print()
    print('  ✓ כל הבדיקות עברו בהצלחה!')
    sys.exit(0)
