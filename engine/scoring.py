from engine.cards import SUITS, RANKS, card_rank, card_suit

_HCP = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}

def hcp(hand):
    return sum(_HCP.get(card_rank(c), 0) for c in hand)

def suit_len(hand, suit):
    return sum(1 for c in hand if card_suit(c) == suit)

def distribution(hand):
    return {s: suit_len(hand, s) for s in SUITS}

def is_balanced(hand):
    lengths = sorted(distribution(hand).values())
    return lengths in ([3, 3, 3, 4], [2, 3, 4, 4], [2, 3, 3, 5])

def longest_suit(hand):
    dist = distribution(hand)
    return max(dist, key=dist.get)

def total_pts(hand):
    dist = distribution(hand)
    length_pts = sum(max(0, v - 4) for v in dist.values())
    return hcp(hand) + length_pts

def has_stopper(hand, suit):
    """A / Kx / QJx / Jxxx"""
    cards = [c for c in hand if card_suit(c) == suit]
    ranks = [card_rank(c) for c in cards]
    n = len(ranks)
    if 'A' in ranks:                              return True  # A
    if 'K' in ranks and n >= 2:                  return True  # Kx
    if 'Q' in ranks and 'J' in ranks and n >= 3: return True  # QJx
    if 'J' in ranks and n >= 4:                  return True  # Jxxx
    return False


def key_cards(hand, trump_suit):
    """מפתחות: אסים (כל הצבעים) + K בשליט — סה״כ 5 מפתחות אפשריים."""
    count = 0
    for card in hand:
        r = card_rank(card)
        s = card_suit(card)
        if r == 'A':
            count += 1
        elif r == 'K' and s == trump_suit:
            count += 1
    return count


def rkcb_response(hand, trump_suit):
    """
    תגובת RKCB (Roman Key Card Blackwood) לשאלת 4NT בצבע.
    מחזיר (bid, kc_count, has_q).
      5♣ = 0 או 3 מפתחות
      5♦ = 1 או 4 מפתחות
      5♥ = 2 מפתחות, ללא Q שליט
      5♠ = 2 מפתחות + Q שליט
    """
    kc = key_cards(hand, trump_suit)
    has_q = any(card_rank(c) == 'Q' and card_suit(c) == trump_suit for c in hand)
    mod = kc % 3
    if mod == 0:
        bid = '5♣'
    elif mod == 1:
        bid = '5♦'
    else:  # mod == 2
        bid = '5♠' if has_q else '5♥'
    return bid, kc, has_q


def bw_response(hand):
    """
    תגובת Blackwood רגילה (ב-NT — 4 אסים בלבד, ללא K שליט).
      5♣ = 0 אסים
      5♦ = 1 אס
      5♥ = 2 אסים
      5♠ = 3 אסים
      (4 אסים נדיר — מטופל כ-5♣)
    """
    aces = sum(1 for c in hand if card_rank(c) == 'A')
    responses = {0: '5♣', 1: '5♦', 2: '5♥', 3: '5♠', 4: '5♣'}
    return responses.get(aces, '5♣'), aces


def sure_tricks(hand):
    """לקיחות מידיות — רצף אונורים מה-A כלפי מטה, בכל צבע."""
    total = 0
    for suit in SUITS:
        suit_ranks = {card_rank(c) for c in hand if card_suit(c) == suit}
        count = 0
        for r in RANKS:
            if r in suit_ranks:
                count += 1
            else:
                break
        total += count
    return total


def dist_fit_pts(hand, trump=None):
    """נקודות חלוקה עם התאמה — חוסר + אורך.
    חוסר (בצבעים שאינם קוז): ווייד=3, סינגלטון=2 — שניה — לא מוסיפים.
    אורך: כל קלף מעל 4 בכל צבע = +1.
    trump: צבע הקוז — לא סופרים חוסר בצבע הקוז עצמו."""
    d = distribution(hand)
    pts = 0
    honors = {'A', 'K', 'Q', 'J'}
    suit_cards = {s: [card_rank(c) for c in hand if card_suit(c) == s] for s in SUITS}
    for suit in SUITS:
        # נקודות חוסר — לא בצבע הקוז, ולא אם יש בכיר בסדרה הקצרה
        if suit != trump:
            ranks = suit_cards[suit]
            has_honor = any(r in honors for r in ranks)
            if d[suit] == 0:
                pts += 3
            elif d[suit] == 1 and not has_honor:
                pts += 2
        # נקודות אורך — קלף 6 ומעלה = +1 לכל קלף
        pts += max(0, d[suit] - 5)
    return pts
