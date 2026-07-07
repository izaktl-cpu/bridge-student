"""
run_lesson9.py — תסריט בדיקה ל-LessonSlamSuit (שיעור 9).

בדיקה ידנית של 11 תרחישים: 3 שלבי הכרזה × נכון/שגוי×1/שגוי×2.

הרצה:
    cd D:\\bridge-student
    python tests\\run_lesson9.py
"""
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_app import MockApp
from lessons.lesson_slam_suit import LessonSlamSuit
from engine.scoring import hcp, key_cards, distribution, suit_len
from engine.cards import make_deck

# ═══════════════════════════════════════════════════════════════════════════
#  בניית ידיים — לוגיקת עזר
# ═══════════════════════════════════════════════════════════════════════════

def _complete_deck(n_hand, s_hand, e_hand):
    """מחשב יד W כשאר הקלפים."""
    used = set(n_hand + s_hand + e_hand)
    deck = set(make_deck())
    return list(deck - used)


def _verify_hands(hands):
    """מאמת שאין כפילויות ושלכל שחקן 13 קלפים."""
    for p in 'NESW':
        assert len(hands[p]) == 13, f"{p}: {len(hands[p])} cards"
    all_cards = hands['N'] + hands['S'] + hands['E'] + hands['W']
    assert len(all_cards) == 52, f"total {len(all_cards)}"
    dups = [c for c in all_cards if all_cards.count(c) > 1]
    assert not dups, f"duplicates: {dups}"


# ═══════════════════════════════════════════════════════════════════════════
#  הגדרת ידיים
#
#  trump = ♠ (S), opening = 1♣ (נדרוס בתוך _make_lesson).
#  פורמט קלף: rank+suit  e.g. 'AS'=A♠, 'KH'=K♥, '2D'=2♦, 'TC'=10♣
#
#  ── HANDS_ZERO ──────────────────────────────────────────────────────────
#  מסלול: S→1♠ → _n_raise → 3♠ → _setup_first_stage(lvl=3) → stage='first'
#  _calc_first(lvl=3, n_min=hn): '4NT' אם hs_adj+hn≥33 else game_bid='4♠'
#
#  N: AS(4) KS(3) 9S 8S 7S | QH(2) JH(1) 5H | QD(2) 4D | AC(4) 9C 8C 7C 6C
#     HCP = 4+3+2+1+2+4 = 16  ✓ (15-17 → n_raise = '3♠')
#     5♠: AS KS 9S 8S 7S ✓
#     key_cards(N,'S') = AS(ace) + KS(trump_K) = 2
#
#  S: TS 6S 5S 4S | AH(4) TH 3H 2H | KD(3) 7D 6D | QC(2) JC(1) 3C
#     HCP = 4+3+2+1 = 10  (trump_bonus: 5+4=9 → +1 → hs_adj=11)
#     hs_adj+hn = 11+16 = 27 < 33 → correct(first) = '4♠' ✓
#     4♠: TS 6S 5S 4S ✓
#     key_cards(S,'S') = AH(ace) = 1
#
#  E: 3S 2S | KH(3) 9H 8H 7H | JD(1) TD 9D 8D 5D | KC(3) TC 5C 4C
#     HCP = 3+1+3 = 7 < 12 ✓,  max suit = diamonds=5 ≤ 5 ✓
#
#  W: QS JS | AH... wait AH is in S. W gets: QS JS | -- (hearts used above?)
#  Let me check remaining after N+S+E:
#  N: AS KS 9S 8S 7S QH JH 5H QD 4D AC 9C 8C 7C 6C  (15 - need 13!)
#  Oops, that's 15. Let me recount: 5+3+2+5 = 15 ≠ 13. Fix.
# ═══════════════════════════════════════════════════════════════════════════

# ── HANDS_ZERO: zero_free + first(4♠) ───────────────────────────────────
# N: 5♠, HCP=16, gives 3♠
# S: 4♠, hs_adj=11, correct(first)='4♠'
# key_cards: n_kc=2, s_kc=1 (for later reference)

N_ZERO = ['AS', 'KS', '9S', '8S', '7S',   # 5♠ (7 HCP)
          'KH', '5H',                        # 2♥ (3 HCP)
          'QD', '4D',                        # 2♦ (2 HCP)
          'AC', '9C', '8C', '7C']           # 4♣ (4 HCP) → 5+2+2+4=13 ✓, total HCP=16

S_ZERO = ['QS', 'JS', 'TS', '4S',          # 4♠ (HCP: 2+1=3)
           'AH', 'TH', '3H',                # 3♥ (HCP: 4)
           'KD', '7D', '6D',                # 3♦ (HCP: 3)
           'JC', '2C', '3C']                # 3♣ (HCP: 1) → 3+4+3+1=11
# hs_adj = 11 + trump_bonus
# N(5♠) + S(4♠) = 9 → trump_bonus=1 → hs_adj=12
# 12+16=28 < 33 → correct(first)='4♠' ✓

# E: quiet (HCP<12, max suit≤5)
E_ZERO = ['6S', '5S',                       # 2♠
           'QH', 'JH', '9H', '8H', '7H',   # 5♥ (HCP: 2+1=3)
           'JD', 'TD', '9D',                # 3♦ (HCP: 1)
           'KC', 'TC', '5C']                # 3♣ (HCP: 3) → 3+1+3=7 ✓

# Verify and get W
def _build_zero():
    N, S, E = N_ZERO, S_ZERO, E_ZERO
    W = _complete_deck(N, S, E)
    hands = {'N': N, 'S': S, 'E': E, 'W': W}
    _verify_hands(hands)
    return hands

# ── HANDS_4NT: first(4NT) + second(6♠) ──────────────────────────────────
# Path: S→1♠ → N gives 4♠ (hn≥18) → _setup_first_stage(lvl=4, game_bid='Pass')
# _calc_first: hs_adj+hn≥33 → '4NT'. Need hs_adj≥33-hn.
# After 4NT: _do_blackwood → N answers RKCB → second stage
# For 6♠: total_kc≥4 AND combined≥33.
#
# N: 5♠, HCP=18, n_kc=3 (AS+AH+KS)
# N: AS(4) KS(3) QS(2) 9S 8S | AH(4) 5H | QD(2) 4D | KC(3) 8C 7C 6C
#    that's 5+2+2+4=13 cards ✓
#    HCP: AS=4,KS=3,QS=2,AH=4,QD=2,KC=3 = 18 ✓
#    n_kc: AS(ace)+AH(ace)+KS(trump_K) = 3
#    rkcb_response(N,'S'): kc=3 → 3%3=0 → '5♣'
#
# S: 4♠, HCP=15, s_kc=2 (AD+AC, no KS as N has it)
# hs_adj=15+1(trump)=16, 16+18=34≥33 → correct(first)='4NT' ✓
# total_kc=3+2=5≥4 and combined=18+15+1=34≥33 → correct(second)='6♠' ✓
# But wait: 5♣ response → _stop_bid: '5♠' if _bid_rank('5♠')>_bid_rank('5♣') → ✓ stop='5♠'
# _calc_second: total≥4 AND combined≥33 → '6♠' ✓
#
# S: TS 6S 5S 4S | TH 3H 2H | AD(4) KC... wait KC is N's
# S: TS 6S 5S 4S | TH 9H 3H | AD(4) 7D 6D | AC(4) QC(2) JC(1)
#    HCP: AD=4, AC=4, QC=2, JC=1 = 11... need 15
#    Add: KH(3): TS 6S 5S 4S | KH(3) TH 3H | AD(4) 7D 6D | AC(4) QC(2) = HCP=3+4+4+2=13
#    Still need 15: add JD(1) + one more
#    S: TS 6S 5S 4S | KH(3) TH 3H | AD(4) JD(1) 7D | AC(4) QC(2) JC(1)
#       HCP=3+4+1+4+2+1=15 ✓ s_kc=AC+AD=2 ✓

N_4NT = ['AS', 'KS', 'QS', '9S', '8S',    # 5♠ (9 HCP)
          'AH', '5H',                        # 2♥ (4 HCP)
          'QD', '4D',                        # 2♦ (2 HCP)
          'KC', '8C', '7C', '6C']           # 4♣ (3 HCP) → 18 ✓

S_4NT = ['TS', '6S', '5S', '4S',           # 4♠ (0 HCP)
          'KH', 'TH', '3H',                 # 3♥ (3 HCP)
          'AD', 'JD', '7D',                 # 3♦ (5 HCP)
          'AC', 'QC', 'JC']                 # 3♣ (7 HCP) → 3+5+7=15 ✓

# n_kc: AS(ace)+AH(ace)+KS(trump K) = 3, rkcb → kc%3=0 → '5♣'
# s_kc: AD(ace)+AC(ace) = 2, no KS
# total_kc = 5 ≥ 4, combined = 18+15+1 = 34 ≥ 33 → 6♠ ✓

E_4NT = ['3S', '2S',
          'QH', 'JH', '9H', '8H', '7H',    # 5♥ (2+1=3 HCP)
          'KD', 'TD', '9D',                 # 3♦ (3 HCP)
          'TC', '5C', '4C', '3C']           # 4♣ (0 HCP) → 6 HCP < 12 ✓
# Count: 2+5+3+4=14 ≠ 13. Fix:
E_4NT = ['3S', '2S',
          'QH', 'JH', '9H', '8H', '7H',    # 5♥
          'KD', 'TD', '9D',                 # 3♦
          'TC', '5C', '4C']                 # 3♣ → 2+5+3+3=13 ✓, HCP=2+1+3=6 ✓

def _build_4nt():
    N, S, E = N_4NT, S_4NT, E_4NT
    W = _complete_deck(N, S, E)
    hands = {'N': N, 'S': S, 'E': E, 'W': W}
    _verify_hands(hands)
    return hands

# ── HANDS_STOP: first(4NT) + second(5♠ stop) ────────────────────────────
# N: 5♠, HCP=18, n_kc=1 (only KS — no aces for N)
# rkcb_response(N,'S'): kc=1 → 1%3=1 → '5♦'
# _stop_bid: '5♠' if rank(5♠)>rank('5♦') → 20+3>20+1 → '5♠' ✓
# S: 4♠, hs_adj≥15 for 4NT, s_kc=2 (AS+AH)
# total_kc = 1+2 = 3 < 4 → stop ✓
# combined = 18+15+1 = 34 ≥ 33 but total_kc<4 → stop ✓
#
# N (no aces, 18 HCP): KS(3)+QS(2)+JS(1) in spades
# N: KS(3) QS(2) JS(1) 9S 8S | KH(3) QH(2) 5H | KD(3) QD(2) 4D | KC(3) 8C
#    HCP: 3+2+1+3+2+3+2+3 = 19. Need 18.
#    Remove QD(2): KS QS JS 9S 8S | KH QH 5H | KD JD 4D | KC 8C
#    HCP: 3+2+1+3+2+3+1+3 = 18 ✓
#    n_kc: KS (trump_K) = 1 ✓ (no aces)

N_STOP = ['KS', 'QS', 'JS', '9S', '8S',   # 5♠ (6 HCP)
           'KH', 'QH', '5H',                # 3♥ (5 HCP)
           'KD', 'JD', '4D',                # 3♦ (4 HCP)
           'KC', '8C']                       # 2♣ (3 HCP) → 18 ✓

# S: 4♠, s_kc=2 (AS+AH), hs≥14 for hs_adj≥15
# S: AS(4) TS 7S 4S | AH(4) TH 6H 2H | QD(2) 9D 6D | QC(2) JC(1) 3C
#    HCP: 4+4+2+2+1=13 < 14. Need 14+.
#    Add KD(3)? But N has KD. Use KC? N has KC.
#    Hmm: remaining after N_STOP: many cards. Let me use:
#    S: AS(4) TS 7S 4S | AH(4) TH 6H 2H | QD(2) 9D 6D | AC(4) 3C
#       HCP: 4+4+2+4=14, s_kc: AS(ace)+AH(ace)+AC(ace)=3 → total=1+3=4 → SLAM not stop!
#    Need s_kc=2: S has exactly 2 aces. Remove AC.
#    S: AS(4) TS 7S 4S | AH(4) TH 6H 2H | QD(2) 9D 6D | TC 3C 2C
#       HCP: 4+4+2=10 < 14. Insufficient.
#    Add KD(3)? N has KD. Add JC(1)+more?
#    S: AS(4) TS 7S 4S | AH(4) TH 6H 2H | QD(2) TD 6D | JC(1) TC 3C
#       HCP: 4+4+2+1=11. Still <14.
#    Hmm, the problem is S has only 2 aces and non-ace non-king cards.
#    Solution: give S a king of non-trump suit (doesn't affect kc).
#    S: AS(4) TS 7S 4S | AH(4) TH 6H | KD(3)... N has KD.
#    Available kings: KS(N has), KH(N has), KD(N has), KC(N has) — N took all kings!
#    Need to reduce N's kings. Restructure N.
#
# New N: still 18 HCP, no aces, 5♠, but free up some kings.
# N: KS(3) QS(2) JS(1) 9S 8S | QH(2) JH(1) 5H | QD(2) JD(1) 4D | AC... but no aces!
#    Without aces: KS(3)+QS(2)+JS(1)+QH(2)+JH(1)+QD(2)+JD(1) = 12 HCP.
#    Need 18: add kings in non-trump suits.
#    KC(3)+KD(3)+KH(3) = 9 more → 12+9=21 too high.
#    KS(3)+QS(2)+JS(1)+KH(3)+KD(3) = 12; need 6 more: QH(2)+JH(1)+QD(2)+JD(1) = 6 → 18 ✓
#
# N: KS(3) QS(2) JS(1) 9S 8S | KH(3) QH(2) JH(1) | KD(3) QD(2) JD(1) | 2C 3C
#    HCP = 3+2+1+3+2+1+3+2+1 = 18 ✓ n_kc=1 (KS only) ✓
#    5♠: KS QS JS 9S 8S ✓
#    rkcb_response(N,'S'): kc=1 → 1%3=1 → '5♦' ✓
#
# Now S: 4♠ (AS + 3 small), s_kc=2 (AS+AH), hs HCP high enough.
# S: AS(4) TS 7S 4S | AH(4) TH 6H | AD(4)... makes s_kc=3 again.
# Really we need EXACTLY 2 aces for S. But need high HCP.
# Use honor cards other than aces: kings are taken by N's hearts/diamonds.
# Available non-A non-K high cards: Q J T of various suits.
# Plus: AH for S if not in N. N has KH not AH, so AH available ✓.
# S with AS+AH: s_kc=2. To get HCP≥14 add queens and jacks:
# S: AS(4) TS 7S 4S | AH(4) QH(was N's)... N has QH. Hmm.
# N above has KH QH JH — can I restructure to free QH?
# New N (18 HCP, no aces, KS, frees QH):
# N: KS(3) QS(2) JS(1) 9S 8S | KH(3) JH(1) 5H | KD(3) JD(1) 4D | QC(2) TC 2C
#    HCP: 3+2+1+3+1+3+1+2=16 < 18. Add: QD(2)+QH(2) → but need to remove others.
#    N: KS(3) QS(2) JS(1) 9S 8S | KH(3) QH(2) 5H | KD(3) QD(2) 4D | JC(1) TC 2C
#       HCP=3+2+1+3+2+3+2+1=17. Need 18: replace TC with KC? but then n_kc still 1 (KS).
#    N: KS(3) QS(2) JS(1) 9S 8S | KH(3) QH(2) 5H | KD(3) QD(2) 4D | KC(3) 2C
#       HCP=3+2+1+3+2+3+2+3=19 > 18.
#    N: KS(3) QS(2) 9S 8S 7S | KH(3) QH(2) 5H | KD(3) QD(2) 4D | JC(1) TC 2C
#       HCP=3+2+3+2+3+2+1=16 < 18. Add more: replace JC(1) with KC(3): → 16+2=18 ✓!
#    N: KS(3) QS(2) 9S 8S 7S | KH(3) QH(2) 5H | KD(3) QD(2) 4D | KC(3) TC 2C
#       HCP=3+2+3+2+3+2+3=18 ✓ n_kc=1 (KS) ✓ 5♠ ✓

N_STOP = ['KS', 'QS', '9S', '8S', '7S',   # 5♠ (5 HCP)
           'KH', 'QH', '5H',                # 3♥ (5 HCP)
           'KD', 'QD', '4D',                # 3♦ (5 HCP)
           'KC', 'TC', '2C']                # 3♣ (3 HCP) → 18 ✓
# n_kc: KS(trump_K)=1 ✓, rkcb: kc=1 → '5♦' ✓

# S: AS(4) + AH(4) = s_kc=2, need hs_adj≥15 for 4NT correct
# hs_adj = hs + trump_bonus(N=5♠+S=4♠=9 → +1)
# Need hs+1≥15 → hs≥14.
# S: AS(4) TS 7S 4S | AH(4) TH 6H 2H | JD(1) 9D 6D | JC(1) 5C 3C
#    HCP=4+4+1+1=10 < 14.
# Need more HCP without aces or kings (all kings in N above):
# KS: N; KH: N; KD: N; KC: N — all kings taken by N!
# This is impossible with N holding all 4 kings.
# Solution: reduce N's kings and give one to S. But S's kc count: K of non-trump doesn't matter.
# Give S KD (not trump king KS): s_kc still = AS+AH = 2. But N has KD.
# Need to restructure. Let N have only 3 kings (drop one non-trump king).
#
# N: KS(3) QS(2) 9S 8S 7S | KH(3) QH(2) 5H | KD(3) QD(2) 4D | JC(1) TC 2C
#    HCP=3+2+3+2+3+2+1=16 < 18. Replace JC(1)+TC with AC... no aces.
#    Replace JC(1) with KC(3)+drop QD: 3+2+3+2+3+3=16 < 18...
#    Alternative: add AH to N → but then rkcb n_kc would include AH as an ace: kc=2 → '5♦' still (2%3=2→5♠/5♥ depending on Q)
#    Let's allow N to have ONE ace (non-KS extra key card).
#    N with n_kc=2 gives 2%3=2 → '5♥' or '5♠'.
#    For stop: total_kc=n_kc+s_kc=2+2=4 → total≥4 → SLAM if combined≥33!
#    Need total<4 for stop. So n_kc must be ≤1 with s_kc=2 (total≤3) or s_kc=1.
#    With n_kc=1 (only KS) we need N at 18 HCP without any aces.
#    That means ONLY K Q J T type cards. Max possible: K=3×4=12, Q=2×4=8, J=1×4=4 → lots.
#    But N uses all 4 kings = 12 HCP. Plus queens and jacks = 18-12=6 HCP.
#    6 HCP of Q/J with 5♠: QS(2)+JS(1) already in N. Plus in other suits.
#    N: KS(3) QS(2) JS(1) 9S 8S | KH(3) QH(2) 5H | KD(3) 4D 3D | KC(3) 2C
#       HCP=3+2+1+3+2+3+3=17. Need 18: add JH(1) → but then 13 cards?
#       5(♠)+3(♥)+3(♦)+2(♣) = 13 ✓ but only if I recount:
#       KS QS JS 9S 8S = 5, KH QH 5H = 3, KD 4D 3D = 3, KC 2C = 2 → 13 ✓
#       HCP=3+2+1+3+2+3+3=17. Add JH: KS QS JS 9S 8S | KH QH JH | KD 4D 3D | KC 2C
#       5+3+3+2=13 ✓, HCP=3+2+1+3+2+1+3+3=18 ✓ n_kc=1 ✓
#
# Now S can have: AS AH and any remaining cards.
# Remaining after N_STOP = {KS QS JS 9S 8S KH QH JH KD 4D 3D KC 2C}:
# Available ♠: AS TS 7S 6S 5S 4S 3S 2S (minus QS JS 9S 8S in N → AS TS 7S 6S 5S 4S 3S 2S available)
# Available ♥: AH TH 9H 8H 7H 6H 5H 4H 3H 2H (minus KH QH JH in N)
# Available ♦: AD QD JD TD 9D 8D 7D 6D 5D 2D (minus KD 4D 3D in N)
# Available ♣: AC QC JC TC 9C 8C 7C 6C 5C 4C 3C (minus KC 2C in N)
# S: AS(4) TS 7S 4S | AH(4) TH 9H 2H | QD(2) JD(1) 6D | QC(2) JC(1) 3C
#    Count: 4+4+3+3=14 ✓, HCP=4+4+2+1+2+1=14 ✓ s_kc=AS(ace)+AH(ace)=2 ✓
#    hs_adj = 14+1 = 15, 15+18=33 ≥ 33 → correct(first)='4NT' ✓
#    total_kc=1+2=3 < 4 → stop ✓, _stop_bid='5♠' ✓

N_STOP = ['KS', 'QS', 'JS', '9S', '8S',   # 5♠ (6 HCP)
           'KH', 'QH', 'JH',                # 3♥ (6 HCP)
           'KD', '4D', '3D',                # 3♦ (3 HCP)
           'KC', '2C']                       # 2♣ (3 HCP) → 18 ✓

S_STOP = ['AS', 'TS', '7S', '4S',          # 4♠ (4 HCP)
           'AH', 'TH', '2H',               # 3♥ (4 HCP)
           'QD', 'JD', '6D',                # 3♦ (3 HCP)
           'QC', 'JC', '3C']                # 3♣ (3 HCP) → 4+3+3+3=13 ✓, HCP=4+4+2+1+2+1=14 ✓

E_STOP = ['6S', '5S',
           '8H', '7H', '6H', '5H', '4H', '3H',   # 6♥ — too long!
           'AD', 'TD', '9D',
           'AC', '4C']
# E must have max 5 cards per suit. Fix:
E_STOP = ['6S', '5S', '3S',
           '8H', '7H', '6H', '5H', '4H',    # 5♥ (quiet)
           'AD', 'TD', '9D',                 # 3♦ (HCP: AD=4)
           'AC', '4C']                        # 2♣ (HCP: AC=4)
# E HCP = 4+4 = 8 < 12 ✓, max suit=5 ✓
# E count: 3+5+3+2=13 ✓

def _build_stop():
    N, S, E = N_STOP, S_STOP, E_STOP
    W = _complete_deck(N, S, E)
    hands = {'N': N, 'S': S, 'E': E, 'W': W}
    _verify_hands(hands)
    return hands


# ═══════════════════════════════════════════════════════════════════════════
#  הפעלת שיעור עם ידיים קבועות
# ═══════════════════════════════════════════════════════════════════════════

def _make_lesson(hands, trump='S', opening='1♣'):
    """מחזיר (lesson, app) מוכנים לשלב zero_free עם ידיים קבועות."""
    app = MockApp()
    lesson = LessonSlamSuit(app)
    # דריסת deal_slam_major — מגדירים ידיים ישירות
    lesson._trump = trump
    lesson._opening = opening
    lesson.hands = {p: list(h) for p, h in hands.items()}
    # _setup_ui מחשב n_kc, s_kc, shortage וכו' ומגדיר stage='zero_free'
    lesson._setup_ui()
    return lesson, app


def _print_result(scenario_num, title, app, lesson=None):
    print(f'=== תרחיש {scenario_num}: {title} ===')
    print(f'auction: {" ".join(app.auction)}')
    if lesson:
        print(f'stage:   {lesson._stage}')
    for i, (text, ok) in enumerate(app.feedbacks):
        tag = '[OK]  ' if ok else '[WRONG]'
        print(f'feedback #{i+1}: {tag} {repr(text)}')
    if not app.feedbacks:
        print('feedback: (none)')
    print('---')
    print()


# ═══════════════════════════════════════════════════════════════════════════
#  תרחישים
# ═══════════════════════════════════════════════════════════════════════════

def run_scenarios():
    errors = []

    # בניית ידיים — כולל assertion על תקינות
    print('בונה ידיים...')
    hands_zero = _build_zero()
    hands_4nt  = _build_4nt()
    hands_stop = _build_stop()
    print('ידיים תקינות ✓\n')

    # הדפסת סיכום ידיים לאימות
    from engine.scoring import hcp, key_cards, distribution
    for name, h in [('zero', hands_zero), ('4nt', hands_4nt), ('stop', hands_stop)]:
        hn = hcp(h['N']); hs = hcp(h['S'])
        nkc = key_cards(h['N'], 'S'); skc = key_cards(h['S'], 'S')
        d_s = distribution(h['S']); trump_bonus = 1 if suit_len(h['N'],'S')+suit_len(h['S'],'S')>=9 else 0
        shortage = next((s for s in ['S','H','D','C'] if s!='S' and d_s[s]<=1), None)
        dp = (3 if shortage and d_s.get(shortage,2)==0 else 2 if shortage else 0) + trump_bonus
        print(f'[{name}] N={hn}HCP n_kc={nkc} | S={hs}HCP s_kc={skc} hs_adj={hs+trump_bonus} shortage={shortage} dp={dp}')
        print(f'       N♠={suit_len(h["N"],"S")} S♠={suit_len(h["S"],"S")} trump_bonus={trump_bonus} combined={hn+hs+dp}')
    print()

    # ── שלב zero_free ─────────────────────────────────────────────────────

    # תרחיש 1: zero_free — נכון (S מכריז 1♠)
    lesson, app = _make_lesson(hands_zero)
    lesson.on_student_bid('1♠')
    _print_result(1, 'zero_free נכון (1♠)', app, lesson)

    # תרחיש 2: zero_free — שגוי→נכון
    lesson, app = _make_lesson(hands_zero)
    lesson.on_student_bid('3♦')   # שגוי
    lesson.on_student_bid('1♠')   # נכון
    _print_result(2, 'zero_free שגוי→נכון (3♦ → 1♠)', app, lesson)
    if len([f for f in app.feedbacks if not f[1]]) == 0:
        errors.append('תרחיש 2: חסר פידבק שגוי')

    # תרחיש 3: zero_free — שגוי×2
    lesson, app = _make_lesson(hands_zero)
    lesson.on_student_bid('3♦')
    lesson.on_student_bid('3♦')
    _print_result(3, 'zero_free שגוי×2', app, lesson)
    if not app.feedbacks:
        errors.append('תרחיש 3: אין פידבקים')
    elif app.last_feedback and app.last_feedback[1] is not False:
        errors.append(f'תרחיש 3: פידבק אחרון אמור להיות שגוי, קיבלנו: {app.last_feedback}')

    # ── שלב first ─────────────────────────────────────────────────────────
    # מגיעים ל-first דרך zero_free: S מכריז 1♠ תחילה

    # תרחיש 4: first — נכון game (4♠)
    lesson, app = _make_lesson(hands_zero)
    lesson.on_student_bid('1♠')   # zero_free → first
    first_correct = lesson._calc_first()
    lesson.on_student_bid(first_correct)   # '4♠'
    _print_result(4, f'first נכון game ({first_correct})', app, lesson)
    if app.last_feedback and app.last_feedback[1] is not True:
        errors.append(f'תרחיש 4: פידבק שגוי — {app.last_feedback}')

    # תרחיש 5: first — נכון 4NT
    lesson, app = _make_lesson(hands_4nt)
    lesson.on_student_bid('1♠')   # zero_free → first (N gave 4♠, lvl=4)
    first_correct_4nt = lesson._calc_first()
    lesson.on_student_bid('4NT')
    _print_result(5, f'first נכון 4NT (correct={first_correct_4nt})', app, lesson)
    if first_correct_4nt != '4NT':
        errors.append(f'תרחיש 5: correct(first) אמור להיות 4NT, קיבלנו {first_correct_4nt}')
    if lesson._stage != 'second' and app.last_feedback:
        # finished already (maybe N decided game on its own)
        pass

    # תרחיש 6: first — שגוי→נכון (3♠ → 4NT)
    lesson, app = _make_lesson(hands_4nt)
    lesson.on_student_bid('1♠')
    wrong_first = '3♠'
    right_first = lesson._calc_first()
    lesson.on_student_bid(wrong_first)
    lesson.on_student_bid(right_first)
    _print_result(6, f'first שגוי→נכון ({wrong_first} → {right_first})', app, lesson)

    # תרחיש 7: first — שגוי×2 (3♠ פעמיים)
    lesson, app = _make_lesson(hands_4nt)
    lesson.on_student_bid('1♠')
    lesson.on_student_bid('3♠')
    lesson.on_student_bid('3♠')
    _print_result(7, 'first שגוי×2 (3♠ פעמיים)', app, lesson)
    if not app.feedbacks or app.last_feedback[1] is not False:
        errors.append(f'תרחיש 7: פידבק אחרון אמור להיות שגוי')

    # ── שלב second ────────────────────────────────────────────────────────

    def _reach_second(hands, trump='S', opening='1♣'):
        l, a = _make_lesson(hands, trump, opening)
        l.on_student_bid('1♠')   # zero_free
        first_c = l._calc_first()
        l.on_student_bid('4NT')  # first (expect correct=4NT)
        return l, a, first_c

    # תרחיש 8: second — נכון סלם (6♠)
    lesson, app, fc = _reach_second(hands_4nt)
    if lesson._stage != 'second':
        errors.append(f'תרחיש 8: לא הגענו לשלב second (stage={lesson._stage}, first_correct={fc})')
        _print_result(8, 'second נכון 6♠ — NOT IN SECOND STAGE', app, lesson)
    else:
        second_correct = lesson._calc_second()
        lesson.on_student_bid('6♠')
        _print_result(8, f'second נכון 6♠ (correct={second_correct})', app, lesson)
        if second_correct != '6♠':
            errors.append(f'תרחיש 8: correct(second)={second_correct} לא 6♠')
        elif app.last_feedback and app.last_feedback[1] is not True:
            errors.append(f'תרחיש 8: פידבק שגוי — {app.last_feedback}')

    # תרחיש 9: second — נכון עצור (5♠)
    lesson, app, fc = _reach_second(hands_stop)
    if lesson._stage != 'second':
        errors.append(f'תרחיש 9: לא הגענו לשלב second (stage={lesson._stage}, first_correct={fc})')
        _print_result(9, 'second נכון עצור — NOT IN SECOND STAGE', app, lesson)
    else:
        second_correct = lesson._calc_second()
        stop_bid = lesson._stop_bid
        lesson.on_student_bid(stop_bid)
        _print_result(9, f'second נכון עצור {stop_bid} (correct={second_correct})', app, lesson)
        if app.last_feedback and app.last_feedback[1] is not True:
            errors.append(f'תרחיש 9: פידבק שגוי — {app.last_feedback}')

    # תרחיש 10: second — שגוי→נכון
    lesson, app, fc = _reach_second(hands_4nt)
    if lesson._stage == 'second':
        correct_s = lesson._calc_second()
        wrong_bid = '5♠' if correct_s == '6♠' else '6♠'
        lesson.on_student_bid(wrong_bid)
        lesson.on_student_bid(correct_s)
        _print_result(10, f'second שגוי→נכון ({wrong_bid} → {correct_s})', app, lesson)
    else:
        errors.append(f'תרחיש 10: לא הגענו לשלב second')
        _print_result(10, 'second שגוי→נכון — NOT IN SECOND STAGE', app, lesson)

    # תרחיש 11: second — שגוי×2
    lesson, app, fc = _reach_second(hands_stop)
    if lesson._stage == 'second':
        correct_s = lesson._calc_second()
        wrong_bid = '6♠' if correct_s != '6♠' else '5♠'
        lesson.on_student_bid(wrong_bid)
        lesson.on_student_bid(wrong_bid)
        _print_result(11, f'second שגוי×2 ({wrong_bid}, correct={correct_s})', app, lesson)
        if not app.feedbacks or app.last_feedback[1] is not False:
            errors.append(f'תרחיש 11: פידבק אחרון אמור להיות שגוי')
    else:
        errors.append(f'תרחיש 11: לא הגענו לשלב second')
        _print_result(11, 'second שגוי×2 — NOT IN SECOND STAGE', app, lesson)

    # ── סיכום ─────────────────────────────────────────────────────────────
    print('=' * 55)
    if errors:
        print(f'✗ {len(errors)} שגיאות:')
        for e in errors:
            print(f'  • {e}')
    else:
        print('✓ כל 11 התרחישים עברו')
    print('=' * 55)
    return len(errors)


if __name__ == '__main__':
    n_errors = run_scenarios()
    sys.exit(0 if n_errors == 0 else 1)
