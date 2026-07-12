"""
סקייל שיעור 6 — מחשב (N) פותח 2NT (20-22 HCP).
מבוסס על scale_lesson4 (סטיימן) + scale_lesson5 (טרנספר) עם הורדת 5 נקודות לסף S.

  סטיימן (S=5-12 HCP, 4 קלפי מיגור בדיוק):
    S מכריז 3♣, N עונה 3♥/3♠/3♦, S מסיים תמיד במשחק (4M/3NT)

  טרנספר (S=0-9 HCP, 5+ קלפי מיגור):
    0-4 נק'          → Pass
    5+  נק', 5 קל'   → 3NT  (N מחליט: 3+ קל' → 4M, 2 קל' → Pass)
    5+  נק', 6+ קל'  → 4M   (משחק ישיר)

  N אחרי 3NT (S=3-4, 5 קל'):
    3+ קל' בסדרה → 4M
    2  קל'       → Pass
"""
import sys, os, random
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import (deal_robot_opens_2nt_stayman,
                                      deal_robot_opens_2nt_transfer,
                                      deal_robot_opens_2nt_nt)
from engine.scoring import hcp, is_balanced, distribution
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


# ── סטיימן ────────────────────────────────────────────────────────────────

def _north_stayman_reply(d_n):
    if d_n['H'] >= 4: return '3♥'
    if d_n['S'] >= 4: return '3♠'
    return '3♦'


def _stayman_cont(has_fit, fit_sym, hs):
    """אחרי 2NT + סטיימן. 11-12 → 4♣ גרבר; 5-10 → 4M (התאמה) או 3NT."""
    if hs >= 11:
        return '4♣'
    return f'4{fit_sym}' if has_fit else '3NT'


def _check_stayman(hands, idx, errors):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    d_n, d_s = distribution(n), distribution(s)

    if not (20 <= hn <= 22):
        errors.append(f'#{idx} (סטיימן): N HCP={hn} מחוץ לטווח 20-22')
    if not is_balanced(n):
        errors.append(f'#{idx} (סטיימן): N לא מאוזן')
    if not (5 <= hs <= 12):
        errors.append(f'#{idx} (סטיימן): S HCP={hs} מחוץ לטווח 5-12')
    if d_s['H'] >= 5 or d_s['S'] >= 5:
        errors.append(f'#{idx} (סטיימן): S יש 5+ קלפי מיגור (צ"ל 4 בדיוק)')
    if not (d_s['H'] == 4 or d_s['S'] == 4):
        errors.append(f'#{idx} (סטיימן): S אין 4 קלפי מיגור')

    reply = _north_stayman_reply(d_n)
    fit_sym = '♥' if reply == '3♥' else '♠'
    has_fit = (reply == '3♥' and d_s['H'] >= 4) or (reply == '3♠' and d_s['S'] >= 4)
    cont = _stayman_cont(has_fit, fit_sym, hs)
    return reply, cont


# ── טרנספר ────────────────────────────────────────────────────────────────

def _s_transfer_bid(d_s):
    if d_s['H'] >= 5: return '3♦', 'H', '♥'
    if d_s['S'] >= 5: return '3♥', 'S', '♠'
    return None, None, None


def _s_cont_transfer(hs, suit_len, sym):
    """המשך S אחרי השלמת הטרנספר — 0-4 פס, 5+ לפי אורך."""
    if hs <= 4:
        return 'Pass'
    if suit_len == 5:
        return '3NT'
    return f'4{sym}'


def _n_resp_3nt(north_fit, sym):
    """N אחרי 3NT של S (3-4 נק', 5 קל') — זהה ל-1NT."""
    return f'4{sym}' if north_fit >= 3 else 'Pass'


def _check_transfer(hands, idx, errors):
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    d_n, d_s = distribution(n), distribution(s)

    if not (20 <= hn <= 22):
        errors.append(f'#{idx} (טרנספר): N HCP={hn} מחוץ לטווח 20-22')
    if not is_balanced(n):
        errors.append(f'#{idx} (טרנספר): N לא מאוזן')
    if not (0 <= hs <= 9):
        errors.append(f'#{idx} (טרנספר): S HCP={hs} מחוץ לטווח 0-9')

    t_bid, suit_key, sym = _s_transfer_bid(d_s)
    if t_bid is None:
        errors.append(f'#{idx} (טרנספר): S אין 5+ קלפי מיגור')
        return None, None, None

    suit_len  = d_s[suit_key]
    north_fit = d_n[suit_key]
    s_cont    = _s_cont_transfer(hs, suit_len, sym)
    n_resp    = _n_resp_3nt(north_fit, sym) if s_cont == '3NT' else 'Pass'
    final     = n_resp if n_resp != 'Pass' else (f'3{sym}' if s_cont == 'Pass' else s_cont)
    return s_cont, n_resp, final


# ── NT (בלי מיגור) ─────────────────────────────────────────────────────────

def _check_nt(hands, idx, errors):
    """S מאוזן 0-12 בלי מיגור רביעייה. 0-4 → פס, 5-10 → 3NT, 11-12 → 4NT."""
    n, s = hands['N'], hands['S']
    hn, hs = hcp(n), hcp(s)
    d_s = distribution(s)
    if not (20 <= hn <= 22):
        errors.append(f'#{idx} (NT): N HCP={hn} מחוץ לטווח 20-22')
    if not is_balanced(n):
        errors.append(f'#{idx} (NT): N לא מאוזן')
    if not (0 <= hs <= 12):
        errors.append(f'#{idx} (NT): S HCP={hs} מחוץ ל-0-12')
    if d_s['H'] >= 4 or d_s['S'] >= 4:
        errors.append(f'#{idx} (NT): S יש מיגור רביעייה')
    if not is_balanced(s):
        errors.append(f'#{idx} (NT): S לא מאוזן')
    if hs <= 4:
        return 'פס'
    return '4♣' if hs >= 11 else '3NT'


# ── ריצה ──────────────────────────────────────────────────────────────────

def run(n=2000):
    errors   = []
    modes    = Counter()
    st_replies = Counter()
    st_conts   = Counter()
    tr_conts   = Counter()
    tr_n_resps = Counter()
    tr_finals  = Counter()
    nt_firsts  = Counter()

    for i in range(n):
        r = random.random()
        mode = 'nt' if r < 0.25 else ('stayman' if r < 0.625 else 'transfer')
        try:
            if mode == 'stayman':
                hands = deal_robot_opens_2nt_stayman()
                reply, cont = _check_stayman(hands, i, errors)
                st_replies[reply] += 1
                st_conts[cont]    += 1
            elif mode == 'transfer':
                hands = deal_robot_opens_2nt_transfer()
                result = _check_transfer(hands, i, errors)
                if result[0] is not None:
                    sc, nr, fin = result
                    tr_conts[sc]   += 1
                    tr_n_resps[nr] += 1
                    tr_finals[fin] += 1
            else:
                hands = deal_robot_opens_2nt_nt()
                nt_firsts[_check_nt(hands, i, errors)] += 1
            modes[mode] += 1
        except Exception as e:
            errors.append(f'#{i} ({mode}): {e}')

    sep   = '─' * 55
    total = sum(modes.values())
    print(sep)
    print(f' שיעור 6 — 2NT  |  {n} ידיות')
    print(sep)
    print(f'  סטיימן={modes["stayman"]}  טרנספר={modes["transfer"]}  NT={modes["nt"]}')

    print()
    print('  NT — הכרזה ראשונה של S:')
    for k, v in sorted(nt_firsts.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/max(modes["nt"],1):4.1f}%)')

    print()
    print('  סטיימן — תגובות N:')
    for k, v in sorted(st_replies.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/modes["stayman"]:4.1f}%)')
    print('  סטיימן — המשך S:')
    for k, v in sorted(st_conts.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/modes["stayman"]:4.1f}%)')

    print()
    print('  טרנספר — המשך S:')
    for k, v in sorted(tr_conts.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/modes["transfer"]:4.1f}%)')
    print('  טרנספר — תגובת N (אחרי 3NT):')
    for k, v in sorted(tr_n_resps.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/modes["transfer"]:4.1f}%)')
    print('  טרנספר — חוזות סופיים:')
    for k, v in sorted(tr_finals.items(), key=lambda x: -x[1]):
        print(f'    {k:<6} {v:>5}  ({100*v/modes["transfer"]:4.1f}%)')

    print()
    if errors:
        print(f'  ✗ שגיאות: {len(errors)}')
        for e in errors[:10]:
            print(f'    • {e}')
    else:
        print('  ✓ אין שגיאות')
    print(sep)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    run(n)
