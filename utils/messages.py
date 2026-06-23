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
        f'יש סלם!\n'
        f'שאל אסים.'
    )


def msg_slam_correct(contract, aces, pts):
    """סלם הצליח."""
    return f'נכון סלם!\nיש {aces} אסים\n{pts} נקודות\nחוזה: {contract}.'


def msg_slam_stop(contract, aces, pts):
    """עצרנו לפני סלם — נכון."""
    return f'נכון! עצרנו.\nיש {aces} אסים\n{pts} נקודות\nחוזה: {contract}.'


def msg_slam_wrong(bid, correct, aces, pts):
    """הכרזת סלם שגויה."""
    return f'הנכון: {correct}.\nיש {aces} אסים\n{pts} נקודות\nחוזה: {bid}.'


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
