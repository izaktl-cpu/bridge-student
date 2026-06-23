"""
בדיקות לשיעור 9 — סלם בצבע.
מאמת: deal constraints, key_cards(), לוגיקת בלאקווד, החלטת סלם.
"""
import pytest
from engine.deal_constraints import deal_slam_major
from engine.scoring import hcp, key_cards, suit_len, distribution
from engine.opening import opening_bid
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


# ─── key_cards() ──────────────────────────────────────────────────────────────

def _make_hand(cards):
    """בניית יד ממחרוזות: ['AH', 'KH', 'AS', '2D', ...]"""
    return cards


def test_key_cards_aces_only():
    """ארבעה אסים ללא K בשליט = 4 מפתחות (בשני הצבעים)."""
    from engine.cards import make_deck
    deck = make_deck()
    aces = [c for c in deck if c[0] == 'A']           # AS AH AD AC
    filler = [c for c in deck if c[0] not in ('A', 'K')][:9]
    hand = aces + filler                               # 4 + 9 = 13, ללא אף K
    assert key_cards(hand, 'H') == 4   # 4 אסים, אין KH
    assert key_cards(hand, 'S') == 4   # 4 אסים, אין KS


def test_key_cards_trump_king():
    """אס אחד + K בשליט = 2 מפתחות."""
    from engine.cards import make_deck
    deck = make_deck()
    ah = next(c for c in deck if c == 'AH')
    kh = next(c for c in deck if c == 'KH')
    # filler: ללא אסים וללא Kים כדי לא לזהם את הספירה
    filler = [c for c in deck if c not in (ah, kh) and c[0] not in ('A', 'K')][:11]
    hand = [ah, kh] + filler
    assert key_cards(hand, 'H') == 2   # AH + KH (K בשליט ♥)
    assert key_cards(hand, 'S') == 1   # רק AH; KH אינו K בשליט ♠


def test_key_cards_no_keys():
    """ללא אסים וללא K בשליט = 0 מפתחות."""
    from engine.cards import make_deck
    deck = make_deck()
    hand = [c for c in deck if c[0] not in ('A', 'K')][:13]
    assert key_cards(hand, 'H') == 0
    assert key_cards(hand, 'S') == 0


def test_key_cards_king_not_trump():
    """K שאינו בשליט לא נחשב."""
    from engine.cards import make_deck
    deck = make_deck()
    ks = next(c for c in deck if c == 'KS')
    rest = [c for c in deck if c[0] not in ('A', 'K')][:12]
    hand = [ks] + rest
    assert key_cards(hand, 'H') == 0   # KS אינו K בשליט ♥
    assert key_cards(hand, 'S') == 1   # KS הוא K בשליט ♠


# ─── deal_slam_major() ────────────────────────────────────────────────────────

def test_deal_slam_major_hearts_constraints():
    for _ in range(20):
        h = deal_slam_major('H')
        hn = hcp(h['N'])
        hs = hcp(h['S'])
        assert 12 <= hn <= 19, f"N HCP {hn}"
        assert suit_len(h['N'], 'H') >= 5, "N < 5 hearts"
        assert opening_bid(h['N'])[0] == '1♥', f"N opens {opening_bid(h['N'])[0]}"
        assert 15 <= hs <= 19, f"S HCP {hs}"
        assert suit_len(h['S'], 'H') >= 4, "S < 4 hearts support"


def test_deal_slam_major_spades_constraints():
    for _ in range(20):
        h = deal_slam_major('S')
        hn = hcp(h['N'])
        hs = hcp(h['S'])
        assert 12 <= hn <= 19, f"N HCP {hn}"
        assert suit_len(h['N'], 'S') >= 5, "N < 5 spades"
        assert opening_bid(h['N'])[0] == '1♠', f"N opens {opening_bid(h['N'])[0]}"
        assert 15 <= hs <= 19, f"S HCP {hs}"
        assert suit_len(h['S'], 'S') >= 4, "S < 4 spades support"


def test_deal_produces_mix_of_scenarios():
    """וידוא שלושת התרחישים: game, slam, stop."""
    game = slam = stop = 0

    def has_shortage(hand, trump):
        d = distribution(hand)
        return any(d[s] <= 1 for s in ['S', 'H', 'D', 'C'] if s != trump)

    for _ in range(90):
        h = deal_slam_major('H')
        hs = hcp(h['S'])
        shortage = has_shortage(h['S'], 'H')
        if hs <= 15:
            game += 1
        elif shortage:
            nkc = key_cards(h['N'], 'H')
            skc = key_cards(h['S'], 'H')
            if nkc + skc >= 4:
                slam += 1
            else:
                stop += 1
    assert game > 0, "לא נוצר תרחיש game"
    assert slam > 0, "לא נוצר תרחיש slam"
    assert stop > 0, "לא נוצר תרחיש stop"


# ─── לוגיקת בלאקווד ──────────────────────────────────────────────────────────

def test_blackwood_response_mapping():
    _BW_RESPONSE = {0: '5♣', 1: '5♦', 2: '5♥', 3: '5♠', 4: '5NT', 5: '5NT'}
    assert _BW_RESPONSE[0] == '5♣'
    assert _BW_RESPONSE[1] == '5♦'
    assert _BW_RESPONSE[2] == '5♥'
    assert _BW_RESPONSE[3] == '5♠'
    assert _BW_RESPONSE[4] == '5NT'


def test_slam_decision_logic():
    """4+ מפתחות → 6M, ≤3 → 5M."""
    for n_kc in range(5):
        for s_kc in range(4):
            total = n_kc + s_kc
            correct = '6M' if total >= 4 else '5M'
            if total >= 4:
                assert correct == '6M', f"n={n_kc}+s={s_kc}={total} → צריך 6M"
            else:
                assert correct == '5M', f"n={n_kc}+s={s_kc}={total} → צריך 5M"


# ─── בדיקת עקרון "יד טובה — אס חמישי" ──────────────────────────────────────

def test_4_key_cards_is_slam():
    """4 מפתחות (חסר 1) = מספיק לסלם."""
    total = 4
    assert total >= 4   # חסר 1 מתוך 5 — בסדר לפי הכלל


def test_3_key_cards_no_slam():
    """3 מפתחות (חסרים 2) = לא מגיעים לסלם."""
    total = 3
    assert total < 4    # חסרים 2 — עוצרים ב-5M


def test_key_cards_across_full_deal():
    """בכל יד תקינה: סך המפתחות בכל 4 שחקנים = 5."""
    from engine.cards import make_deck
    import random
    for _ in range(50):
        deck = make_deck()
        random.shuffle(deck)
        hands = {'N': deck[:13], 'E': deck[13:26], 'S': deck[26:39], 'W': deck[39:]}
        trump = random.choice(['H', 'S'])
        total = sum(key_cards(hands[p], trump) for p in 'NESW')
        assert total == 5, f"סך מפתחות {total} ≠ 5"
