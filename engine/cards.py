SUITS = ['S', 'H', 'D', 'C']
SUIT_SYMBOLS = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}
SUIT_COLORS  = {'S': 'black', 'H': '#cc0000', 'D': '#cc0000', 'C': 'black'}
RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
_RANK_DISPLAY = {'T': '10'}

def make_deck():
    return [r + s for s in SUITS for r in RANKS]

def card_rank(card): return card[0]
def card_suit(card): return card[1]

def fmt_rank(r):
    return _RANK_DISPLAY.get(r, r)

def hand_by_suit(hand):
    result = {s: [] for s in SUITS}
    for card in hand:
        result[card_suit(card)].append(card_rank(card))
    for s in SUITS:
        result[s].sort(key=lambda r: RANKS.index(r))
    return result

def fmt_suit_cards(ranks):
    return ' '.join(fmt_rank(r) for r in ranks) if ranks else '—'
