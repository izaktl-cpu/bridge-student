"""
סקייל בדיקה לשיעור 14 — דבל להוצאה.
מריץ N ידיות ובודק עקביות:
  - W פותח 1 בצבע
  - N יכול לדבל להוצאה
  - תגובת S מתאימה לנקודותיה (0-8 / 9-12 / 13+)
  - הצבע שנבחר אינו צבע W
  - גובה ההכרזה חוקי

שימוש:
    python tests/scale_takeout_double.py          # ברירת מחדל: 2000 ידיות
    python tests/scale_takeout_double.py 500      # 500 ידיות
    python tests/scale_takeout_double.py 2000 -v  # מפורט (5 ידיות ראשונות)
"""

import sys, os
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_takeout_double
from engine.takeout_double import can_double, respond_to_double, suit_of, best_response_suit
from engine.opening import opening_bid as _opening_bid
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS
_RANK = {'C': 1, 'D': 2, 'H': 3, 'S': 4}
_SYM_MAP = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}


def _e_suit(bid):
    for ch, s in _SYM_MAP.items():
        if ch in bid:
            return s
    return None


def _bid_level(bid):
    if bid and bid[0].isdigit():
        return int(bid[0])
    return 0


def _bid_suit_sym(bid):
    for ch in ('♣', '♦', '♥', '♠'):
        if ch in bid:
            return ch
    return None


def _min_legal_level(response_suit, opp_suit, opp_level=1):
    rs = _RANK.get(response_suit, 0)
    os = _RANK.get(opp_suit, 0)
    if rs <= os:
        return opp_level + 1
    return opp_level


def _check_one(hands, idx, errors):
    w = hands['W']
    n = hands['N']
    s = hands['S']

    hw = hcp(w)
    hn = hcp(n)
    hs = hcp(s)
    dn = distribution(n)

    # ── בדיקת W ──────────────────────────────────────────────────────────────
    if not (12 <= hw <= 15):
        errors.append(f'#{idx}: W HCP={hw} מחוץ לטווח 12-15')

    w_bid, _ = _opening_bid(w)
    if not w_bid or w_bid[0] != '1' or 'NT' in w_bid:
        errors.append(f'#{idx}: W לא פתח 1-בצבע (פתח {w_bid})')
        return {'hs': hs, 'response': '?', 'category': '?'}

    w_suit = _e_suit(w_bid)
    if not w_suit:
        errors.append(f'#{idx}: לא זוהה צבע W מ-{w_bid}')
        return {'hs': hs, 'response': '?', 'category': '?'}

    # ── בדיקת N (יכול לדבל) ──────────────────────────────────────────────────
    if not (9 <= hn <= 16):
        errors.append(f'#{idx}: N HCP={hn} מחוץ לטווח 9-16')

    if not can_double(n, w_suit, level=1):
        errors.append(f'#{idx}: N לא יכול לדבל (HCP={hn}, dn={dn})')

    # ── תגובת S ───────────────────────────────────────────────────────────────
    response, expl = respond_to_double(s, w_suit, opp_level=1)

    if response == 'Pass':
        return {'hs': hs, 'response': response, 'category': 'Pass'}

    # צבע תגובה
    resp_sym = _bid_suit_sym(response)
    resp_suit = _SYM_MAP.get(resp_sym, '') if resp_sym else ''
    is_nt  = 'NT' in response
    is_cue = bool(resp_suit) and not is_nt and resp_suit == w_suit

    if not is_nt and not is_cue:
        # עקביות צבע עם best_response_suit (לא חל על קיו ביט)
        best = best_response_suit(s, w_suit)
        if best and resp_suit != best:
            errors.append(
                f'#{idx}: S הכריז {response} אבל הצבע הטוב ביותר הוא {_S[best]}')

    # גובה חוקי
    lvl = _bid_level(response)
    if lvl == 0:
        errors.append(f'#{idx}: הכרזה לא תקינה: {response}')
    else:
        if not is_nt and not is_cue:
            min_lvl = _min_legal_level(resp_suit, w_suit, opp_level=1)
            if lvl < min_lvl:
                errors.append(
                    f'#{idx}: S הכריז {response} — גובה {lvl} נמוך מהמינימום {min_lvl}')

    # עקביות נקודות ↔ גובה
    if hs <= 8:
        category = 'חלש (0-8)'
        if is_cue:
            errors.append(
                f'#{idx}: S={hs}נק׳ (חלש) קיו ביט — צפוי רמה נמוכה')
        elif not is_nt and resp_suit:
            min_lvl = _min_legal_level(resp_suit, w_suit, opp_level=1)
            if lvl != min_lvl:
                errors.append(
                    f'#{idx}: S={hs}נק׳ (חלש) הכריז {response} — צפוי רמה {min_lvl}')
    elif hs <= 12:
        category = 'בינוני (9-12)'
        if is_cue:
            errors.append(
                f'#{idx}: S={hs}נק׳ (בינוני) קיו ביט — צפוי קפיצה')
        elif not is_nt and resp_suit:
            is_minor_resp = resp_suit in ('C', 'D')
            jump_thr_check = 11 if is_minor_resp else 9
            min_lvl = _min_legal_level(resp_suit, w_suit, opp_level=1)
            if hs >= jump_thr_check:
                expected_lvl = min_lvl + 1
                if lvl != expected_lvl:
                    errors.append(
                        f'#{idx}: S={hs}נק׳ (בינוני) הכריז {response} — צפוי רמה {expected_lvl}')
            else:
                if lvl != min_lvl:
                    errors.append(
                        f'#{idx}: S={hs}נק׳ (בינוני-מינור) הכריז {response} — צפוי רמה {min_lvl}')
    else:
        category = 'חזק (13+)'
        if not is_cue:
            cue_expected = f'{1 + 1}{_S[w_suit]}'
            errors.append(
                f'#{idx}: S={hs}נק׳ (חזק) הכריז {response} — צפוי קיו ביט {cue_expected}')

    return {'hs': hs, 'response': response, 'category': category}


def scale_takeout(n=2000, verbose=False):
    errors = []
    category_counts = Counter()
    response_dist = Counter()

    for i in range(n):
        try:
            hands = deal_takeout_double()
            result = _check_one(hands, i, errors)

            category_counts[result['category']] += 1
            resp = result['response']
            if resp == 'Pass':
                response_dist['Pass'] += 1
            elif 'NT' in resp:
                response_dist['NT'] += 1
            elif resp[0] in '12':
                response_dist[f'רמה {resp[0]}'] += 1
            elif resp[0] == '3':
                response_dist['רמה 3'] += 1
            else:
                response_dist[f'רמה {resp[0]}+'] += 1

            if verbose and i < 5:
                w_bid, _ = _opening_bid(hands['W'])
                hw = hcp(hands['W'])
                hn = hcp(hands['N'])
                hs = result['hs']
                print(f'  #{i}: W={hw}נק׳ פתח {w_bid} | '
                      f'N={hn}נק׳ דבל | '
                      f'S={hs}נק׳ → {resp}  [{result["category"]}]')

        except Exception as e:
            errors.append(f'#{i}: חריגה — {e}')

    return errors, category_counts, response_dist


def _bar(counts, total):
    lines = []
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        pct = 100 * v / total if total else 0
        lines.append(f'    {k:<25} {v:>5}  ({pct:4.1f}%)')
    return '\n'.join(lines)


def run(n=2000, verbose=False):
    sep = '─' * 60
    print(sep)
    print(f' שיעור 14 — דבל להוצאה  |  {n} ידיות')
    print(sep)

    errors, categories, responses = scale_takeout(n, verbose=verbose)
    total = sum(categories.values())

    print(f'  ידיות שהורצו: {total}')
    print()
    print('  התפלגות ידיות S:')
    print(_bar(categories, total))
    print()
    print('  התפלגות הכרזות S:')
    print(_bar(responses, total))
    print()

    if errors:
        print(f'  ✗ שגיאות: {len(errors)}')
        for e in errors[:20]:
            print(f'    • {e}')
        if len(errors) > 20:
            print(f'    ... ועוד {len(errors) - 20}')
    else:
        print('  ✓ אין שגיאות')
    print(sep)


if __name__ == '__main__':
    args = sys.argv[1:]
    n       = int(args[0]) if args and args[0].lstrip('-').isdigit() else 2000
    verbose = '-v' in args
    run(n, verbose=verbose)
