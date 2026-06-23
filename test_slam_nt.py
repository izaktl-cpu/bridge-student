"""
בדיקות לשיעור 8 — סלם ב-NT.
מאמת: כללי deal constraints, סף נקודות, הגיון סלם (33+).
"""
import pytest
from engine.deal_constraints import deal_slam_nt_mode_a, deal_slam_nt_mode_b, deal_slam_nt_mode_c
from engine.scoring import hcp, is_balanced, distribution, suit_len
from engine.opening import opening_bid


# ─── Mode A: 1NT opening ──────────────────────────────────────────────────────

def test_mode_a_constraints():
    for _ in range(30):
        h = deal_slam_nt_mode_a()
        hn = hcp(h['N'])
        hs = hcp(h['S'])
        assert 15 <= hn <= 17, f"N HCP {hn} out of range"
        assert is_balanced(h['N']), "N not balanced"
        assert 14 <= hs <= 18, f"S HCP {hs} out of range"
        assert is_balanced(h['S']), "S not balanced"
        d = distribution(h['S'])
        assert d['H'] < 5 and d['S'] < 5, "S has 5-card major"


def test_mode_a_slam_logic():
    """עם 18 נק' ל-S: סה״כ >= 33 תמיד (18+15=33). עם 16-17: צריך N=17."""
    results = {'18_slam': 0, '16_invite_accepted': 0, '15_game': 0}
    for _ in range(200):
        h = deal_slam_nt_mode_a()
        hn = hcp(h['N'])
        hs = hcp(h['S'])
        if hs == 18:
            assert hn + hs >= 33, f"18+{hn}={hn+hs} < 33"
            results['18_slam'] += 1
        if hs in (16, 17) and hn == 17:
            assert hn + hs >= 33
            results['16_invite_accepted'] += 1
        if hs <= 15:
            assert hn + hs <= 32, f"{hs}+{hn}={hs+hn} >= 33 but should be 3NT"
            results['15_game'] += 1
    assert results['18_slam'] > 0
    assert results['15_game'] > 0


# ─── Mode B: 2NT opening ──────────────────────────────────────────────────────

def test_mode_b_constraints():
    for _ in range(30):
        h = deal_slam_nt_mode_b()
        hn = hcp(h['N'])
        hs = hcp(h['S'])
        assert 20 <= hn <= 22, f"N HCP {hn} out of range"
        assert is_balanced(h['N']), "N not balanced"
        assert 9 <= hs <= 13, f"S HCP {hs} out of range"
        assert is_balanced(h['S']), "S not balanced"
        d = distribution(h['S'])
        assert d['H'] < 5 and d['S'] < 5, "S has 5-card major"


def test_mode_b_slam_logic():
    """עם 13 נק' ל-S: סה״כ >= 33 תמיד (13+20=33). עם 10: לא סלם."""
    for _ in range(200):
        h = deal_slam_nt_mode_b()
        hn = hcp(h['N'])
        hs = hcp(h['S'])
        if hs >= 13:
            assert hn + hs >= 33, f"{hs}+{hn}={hs+hn} < 33"
        if hs <= 10:
            assert hn + hs <= 32, f"{hs}+{hn}={hs+hn} >= 33 but should be 3NT"


# ─── Mode C: suit opening → 1NT rebid ────────────────────────────────────────

_ALL_C = [('C', 'H'), ('C', 'S'), ('D', 'H'), ('D', 'S'), ('H', 'S')]


def test_mode_c_constraints():
    from engine.cards import SUIT_SYMBOLS
    for opening, response in _ALL_C:
        open_sym = SUIT_SYMBOLS[opening]
        h = deal_slam_nt_mode_c(opening, response)
        hn = hcp(h['N'])
        hs = hcp(h['S'])
        assert 12 <= hn <= 14, f"{opening}-{response}: N HCP {hn}"
        assert is_balanced(h['N']), f"{opening}-{response}: N not balanced"
        assert opening_bid(h['N'])[0] == f'1{open_sym}', \
            f"{opening}-{response}: N opens {opening_bid(h['N'])[0]}"
        assert suit_len(h['N'], response) < 4, \
            f"{opening}-{response}: N has 4+ fit in response suit"
        assert 17 <= hs <= 21, f"{opening}-{response}: S HCP {hs}"
        resp_len = suit_len(h['S'], response)
        assert 4 <= resp_len <= 5, \
            f"{opening}-{response}: S has {resp_len} in response suit (need 4-5)"


def test_mode_c_18_no_slam():
    """עם 18 נק' ל-S ו-N מקסימום 14: סה״כ=32 — אין סלם."""
    for _ in range(300):
        h = deal_slam_nt_mode_c('C', 'H')
        hn = hcp(h['N'])
        hs = hcp(h['S'])
        if hs == 18:
            assert hn + hs <= 32, f"18+{hn}={hn+hs} >= 33 — unexpected slam"


def test_mode_c_19_slam_with_max():
    """עם 19 נק' ל-S ו-N=14: סה״כ=33 — סלם."""
    found = False
    for _ in range(500):
        h = deal_slam_nt_mode_c('D', 'H')
        if hcp(h['S']) == 19 and hcp(h['N']) == 14:
            assert hcp(h['S']) + hcp(h['N']) == 33
            found = True
            break
    assert found, "לא נמצאה יד עם S=19, N=14"


def test_mode_c_21_slam_guaranteed():
    """עקרון מתמטי: עם S≥21 ו-N מינימום 12, תמיד מגיעים ל-33."""
    for s_hcp in range(21, 24):
        for n_hcp in range(12, 15):
            assert s_hcp + n_hcp >= 33, f"{s_hcp}+{n_hcp}={s_hcp+n_hcp} < 33"


def test_mode_c_uptheline_club_heart():
    """אחרי 1♣: S שמגיב 1♥ לא אמור להיות עם 4+ ♦."""
    for _ in range(50):
        h = deal_slam_nt_mode_c('C', 'H')
        assert suit_len(h['S'], 'D') < 4, "S has 4+D — would respond 1D not 1H"


def test_mode_c_uptheline_club_spade():
    """אחרי 1♣: S שמגיב 1♠ לא אמור להיות עם 4+ ♦ או 4+ ♥."""
    for _ in range(50):
        h = deal_slam_nt_mode_c('C', 'S')
        assert suit_len(h['S'], 'D') < 4, "S has 4+D — would respond 1D"
        assert suit_len(h['S'], 'H') < 4, "S has 4+H — would respond 1H"


def test_mode_c_uptheline_diamond_spade():
    """אחרי 1♦: S שמגיב 1♠ לא אמור להיות עם 4+ ♥."""
    for _ in range(50):
        h = deal_slam_nt_mode_c('D', 'S')
        assert suit_len(h['S'], 'H') < 4, "S has 4+H — would respond 1H"
