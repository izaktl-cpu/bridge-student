"""
תבניות הודעות — לכל השיעורים.
"""


def msg_try_again():
    return 'טעות.\nנסה שוב.'


def msg_try_again_pts(h):
    return f'יש לך {h} נקודות.\nנסה שוב.'


def msg_try_again_hint(hint):
    return f'רמז:\n{hint}\nנסה שוב.'


def msg_correct(why, final):
    return f'נכון!\n{why}\nחוזה: {final}.'


def msg_wrong(bid, correct, why=''):
    base = f'הכרזת {bid}.\nהנכון: {correct}.'
    return f'{base}\n{why}' if why else base


def msg_computer(bid, why=''):
    base = f'מחשב הכריז {bid}.'
    return f'{base}\n{why}' if why else base


# ── תבניות סלם ────────────────────────────────────────────────────────────────

def msg_slam_possible(hn, hs, dp, total):
    """יש 33+ נקודות — שאל אסים."""
    dp_part = f'+{dp}' if dp else ''
    return (
        f'{hn}+{hs}{dp_part}={total}\n'
        f'יש סלם\n'
        f'שאל אסים'
    )


def tricks(n):
    """יחיד/רבים ללקיחות."""
    return 'לקיחה אחת' if n == 1 else f'{n} לקיחות'


def high_tricks(n):
    """יחיד/רבים ללקיחות גבוהות."""
    return 'לקיחה גבוהה אחת' if n == 1 else f'{n} לקיחות גבוהות'


def cards_of(n, sym):
    """יחיד/רבים לקלפים בסדרה."""
    return f'קלף {sym} אחד' if n == 1 else f'{n} קלפי {sym}'


def msg_slam_correct(contract, aces, pts):
    """סלם הצליח."""
    return f'נכון\nיש {aces} אסים\n{pts} נקודות\nההכרזה הנכונה\n{contract}'


def msg_slam_stop(contract, aces, pts):
    """עצרנו לפני סלם — נכון."""
    return f'נכון\nיש {aces} אסים בלבד\n{pts} נקודות\nההכרזה הנכונה\n{contract}'


def msg_slam_wrong(bid, correct, aces, pts):
    """הכרזת סלם שגויה."""
    return f'יש {aces} אסים\n{pts} נקודות\nההכרזה הנכונה\n{correct}'


def msg_no_slam(pts, contract):
    """אין מספיק נקודות לסלם — משחק מלא."""
    return f'יש פחות מ 33 נקודות.\nאין סיכוי לסלם.\nמכריזים משחק מלא.\nחוזה: {contract}.'


def msg_calc_game(contract):
    """לא מספיק נקודות — אין משחק מלא."""
    return (
        f'פחות מ 33 נקודות.\n'
        f'אין משחק מלא.\n'
        f'חוזה: {contract}.'
    )


# ── תבניות שורות טבלה ────────────────────────────────────────────────────────

def row_support(bid, pts, cards, sym=''):
    """שורת תמיכה: pts נקודות, +cards קלפים"""
    return f"נקודות {pts}, +{cards} קלפים"


# ── כללי ──────────────────────────────────────────────────────────────────────

def msg_retry():
    """נסה שנית — ללא הסבר."""
    return 'נסה שנית.'


def msg_chose_wrong(bid, correct):
    """בחרת X — הנכון Y."""
    return f'בחרת {bid}.\nהנכון: {correct}.'


def msg_chose_wrong_why(bid, correct, why):
    """בחרת X — הסבר — הנכון Y."""
    return f'בחרת {bid}.\n{why}\nהנכון: {correct}.'


def msg_correct_final(final):
    """נכון + חוזה סופי."""
    return f'נכון!\nחוזה: {final}.'


def msg_contract_wrong(bid, correct):
    """חוזה X — הנכון Y."""
    return f'הנכון: {correct}.\nחוזה: {bid}.'


def msg_suboptimal(note):
    """לא מיטבי — ממשיכים."""
    return f'לא מיטבי.\n{note}\nממשיכים...'
