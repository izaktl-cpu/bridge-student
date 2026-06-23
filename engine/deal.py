import random
from engine.cards import make_deck
from engine.scoring import hcp, is_balanced

def _deal_random():
    deck = make_deck()
    random.shuffle(deck)
    return {'N': deck[:13], 'E': deck[13:26], 'S': deck[26:39], 'W': deck[39:]}

def deal_south(hcp_min, hcp_max, balanced=None, tries=50000):
    for _ in range(tries):
        hands = _deal_random()
        h = hcp(hands['S'])
        if hcp_min <= h <= hcp_max:
            if balanced is None or is_balanced(hands['S']) == balanced:
                return hands
    raise RuntimeError(f"לא ניתן לחלק יד עם {hcp_min}-{hcp_max} כבוד")

def deal_1nt_south():
    """South: 15-17 HCP balanced (פתיחת 1NT)"""
    return deal_south(15, 17, balanced=True)
