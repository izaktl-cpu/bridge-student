"""
דבל להוצאה (Takeout Double). Acol
W פותח, N מכריז X, S עונה.
"""

from engine.scoring import hcp, distribution, is_balanced, has_stopper
from engine.cards import SUIT_SYMBOLS

_S    = SUIT_SYMBOLS
_RANK = {'C': 1, 'D': 2, 'H': 3, 'S': 4}
_SYM  = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}


def suit_of(bid):
    for ch, s in _SYM.items():
        if ch in bid:
            return s
    return None


def can_double(hand, opp_suit, level=1):
    """
    האם N יכול לדבל להוצאה?
    level: גובה פתיחת W (1 או 2).
    """
    h = hcp(hand)
    d = distribution(hand)

    if level == 1 and not (12 <= h <= 16):
        return False
    if level >= 2 and not (12 <= h <= 16):
        return False

    # מקסימום 2 קלפים בצבע היריב (צורה קלאסית 4-4-3-2)
    if opp_suit and d.get(opp_suit, 0) > 2:
        return False

    # 3+ קלפים בכל צבע חוץ מצבע היריב
    other = [s for s in ['S', 'H', 'D', 'C'] if s != opp_suit]
    for suit in other:
        if d[suit] < 3:
            return False

    # לפחות 2 סדרות מהשאר עם 4+ קלפים (4-4-3)
    if sum(1 for s in other if d[s] >= 4) < 2:
        return False

    return True


def phase2_decision(hand, opp_suit, level=1):
    """
    החלטת S אחרי פתיחת יריב. כולל 1NT ודבל גדול.
    עדיפות: 1NT (15-18, מאוזן, עוצר בצבע יריב) > דבל גדול (17+, כל חלוקה) >
             דבל רגיל (12-16, צורה קלאסית. can_double) > Pass.
    """
    h = hcp(hand)

    if 15 <= h <= 18 and is_balanced(hand) and opp_suit and has_stopper(hand, opp_suit):
        return '1NT'
    if h >= 17:
        return 'X'
    if can_double(hand, opp_suit, level=level):
        return 'X'
    return 'Pass'


def best_response_suit(hand, opp_suit):
    """הצבע הטוב ביותר לS. הארוך ביותר שאינו צבע הפותח, עדיפות למיגור."""
    d = distribution(hand)
    best = None
    best_len = -1
    for suit in ['S', 'H', 'D', 'C']:
        if suit == opp_suit:
            continue
        length = d[suit]
        if length > best_len:
            best_len = length
            best = suit
        elif length == best_len:
            # עדיפות מיגור על מינור
            if best in ('D', 'C') and suit in ('S', 'H'):
                best = suit
            # בין שני מיגורים שווים. עדיפות לזול יותר (♥ לפני ♠)
            elif best == 'S' and suit == 'H':
                best = suit
    return best


def respond_to_double(hand, opp_suit, opp_level=1):
    """
    תגובת S לדבל להוצאה של N.
    מחזיר (bid, explanation).
    0-8 נק': רמה נמוכה
    9-12 נק': קפיצה
    13+ נק': משחק מלא
    """
    h    = hcp(hand)
    d    = distribution(hand)

    suit = best_response_suit(hand, opp_suit)

    if not suit:
        return 'Pass', f'{h} נק׳. אין צבע'

    sym       = _S[suit]
    suit_rank = _RANK[suit]
    opp_rank  = _RANK.get(opp_suit, 0)

    # גובה מינימלי: אם צבע S נמוך מצבע הפותח → עולים רמה
    min_lvl = opp_level
    if suit_rank <= opp_rank:
        min_lvl = opp_level + 1

    cue_thr  = 13
    jump_thr = 8

    if h >= cue_thr:
        opp_sym = _S[opp_suit]
        cue_lvl = opp_level + 1
        return f'{cue_lvl}{opp_sym}', f'{h} נק׳. קיו ביט, חיפוש התאמה'

    if h >= jump_thr:
        lvl = min_lvl + 1
        return f'{lvl}{sym}', f'{d[suit]} קלפי {sym}\n{h} נק׳. קפיצה'

    lvl = min_lvl
    return f'{lvl}{sym}', f'{d[suit]} קלפי {sym}\n{h} נק׳'


def doubler_raises(n_hand, s_bid, opp_suit):
    """
    N מחליט האם להעלות אחרי תגובת S לדבל (לא קיו ביט).
    S הכריז ברמה שמשקפת את הניקוד שלו:
      רמה נמוכה = 0-8 נק׳  → N פס תמיד
      קפיצה     = 9-12 נק׳ → N מעלה למשחק אם יש התאמה ו-N >= 14
    """
    hn   = hcp(n_hand)
    dn   = distribution(n_hand)
    s_suit = suit_of(s_bid)
    if not s_suit or s_suit == opp_suit:
        return 'Pass', 'אין צבע ברור'

    s_level = int(s_bid[0]) if s_bid and s_bid[0].isdigit() else 0

    # גובה מינימלי לצבע זה
    s_rank  = _RANK.get(s_suit, 0)
    opp_rank = _RANK.get(opp_suit, 0)
    min_lvl = 1 if s_rank > opp_rank else 2
    is_jump = s_level > min_lvl

    if not is_jump:
        return 'Pass', f'S ברמה נמוכה (0-8 נק׳). N פס.'

    # S קפץ (9-12 נק׳). N מעלה למשחק אם יש התאמה ו-N >= 13
    fit = dn.get(s_suit, 0) >= 3
    if fit and hn >= 13:
        sym = _S[s_suit]
        lvl = 4 if s_suit in ('H', 'S') else 5
        return f'{lvl}{sym}', f'N={hn} נק׳, S=9-12, התאמה. מעלה ל-{lvl}{sym}'

    return 'Pass', f'N={hn} נק׳. לא מספיק להעלות'


def doubler_rebid(hand, opp_suit):
    """N מראה סדרה אחרי קיו ביט של S. מיגורים לפני מינורים."""
    d   = distribution(hand)
    h   = hcp(hand)
    opp_rank = _RANK[opp_suit]

    for suit in ['H', 'S', 'D', 'C']:
        if suit == opp_suit:
            continue
        if d[suit] >= 4:
            sym       = _S[suit]
            suit_rank = _RANK[suit]
            lvl       = 2 if suit_rank > opp_rank else 3
            return f'{lvl}{sym}', f'{d[suit]} קלפי {sym}'

    # אין סדרה של 4 קלפים → NT
    return '2NT', f'{h} נק׳. אין מיגור, NT'


def _count_stoppers(hand, suit):
    """האם ליד יש עוצר בסדרה: A / Kx / Qxx. מחזיר 0 או 1."""
    from engine.cards import card_suit, card_rank
    if not hand or not suit:
        return 0
    cards = [c for c in hand if card_suit(c) == suit]
    ranks = [card_rank(c) for c in cards]
    n     = len(ranks)
    if ('A' in ranks or
            ('K' in ranks and n >= 2) or
            ('Q' in ranks and n >= 3)):
        return 1
    return 0


def respond_to_cue(hand, n_suit, opp_suit=None, n_hand=None):
    """S עונה לסדרת N אחרי הקיו ביט.
    עדיפות: 5+ מיגור → 4M. 4+ מיגור עם N → 4M.
    אחרת: S+N יחד 2+ עוצרים → 3NT. אחרת → 5 מינור אם התאמה.
    """
    d = distribution(hand)

    # 1. 5+ קלפי מיגור. N מובטח 3+ מהדבל
    for major in ['H', 'S']:
        if major == opp_suit:
            continue
        if d[major] >= 5:
            sym = _S[major]
            if n_suit == major:
                # N הראה בדיוק את המיגור הזה → סגור 4M ישיר
                return f'4{sym}', f'{d[major]} קלפי {sym}, שותף עם 3+. התאמה'
            else:
                # N הראה סדרה אחרת → הראה 3M, שותף יסגור ל-4M
                return f'3{sym}', f'{d[major]} קלפי {sym}. מראה מיגור, שותף יסגור ל-4{sym}'

    # 2. התאמה במיגור עם N
    if n_suit and n_suit in ('H', 'S'):
        n_len = d.get(n_suit, 0)
        sym   = _S[n_suit]
        if n_len >= 4:
            return f'4{sym}', f'{n_len} קלפי {sym}. התאמה'

    # 3. עוצר בסדרת יריב ביד S. מכריז 3NT
    if opp_suit and _count_stoppers(hand, opp_suit):
        return '3NT', 'עוצר בסדרת יריב. 3NT'

    # 4. אין עוצרים. מינור רק עם 28+ נק׳ משותף
    if n_suit and n_suit in ('C', 'D'):
        n_len = d.get(n_suit, 0)
        sym   = _S[n_suit]
        if n_len >= 4:
            combined = hcp(hand) + (hcp(n_hand) if n_hand else 0)
            if combined >= 28:
                return f'5{sym}', f'{combined} נק׳, {n_len} קלפי {sym}. 5 מינור'

    # 5. עוצר בN? (N הכריז NT קודם)
    if n_suit is None and n_hand and _count_stoppers(n_hand, opp_suit):
        return '3NT', 'עוצר בN. 3NT'

    # 6. אין עוצר בשום יד. 5 במינור הטוב יותר
    for minor in ['C', 'D']:
        if minor == opp_suit:
            continue
        n_len = d.get(minor, 0)
        if n_len >= 3:
            sym = _S[minor]
            return f'5{sym}', f'אין עוצר. {n_len} קלפי {sym}, 5 מינור'

    return '3NT', 'אין ברירה. 3NT'
