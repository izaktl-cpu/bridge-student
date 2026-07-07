"""
run_lesson8.py — תסריט בדיקה לשיעור 8 (סלם ב-NT).
4 מודים: A (1NT), B (2NT), C (ריבאד 1NT), D (ריבאד 1NT / התאמת מינור→RKCB).
נוהג את S אוטומטית בכל מוד עד סוף המכרז, סורק פידבק להפרות סקייל,
ומדווח כיסוי מודים + חוזי Mode-D.

הרצה:
    cd D:\\bridge-student
    set PYTHONIOENCODING=utf-8
    python tests\\run_lesson8.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_app import MockApp
from lessons.lesson_slam_nt import LessonSlamNT
from engine.scoring import suit_len
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS
_FORBIDDEN = {'טעית': 'נזיפה', '—': 'מקף', '!': 'קריאה', ':': 'נקודתיים'}


def _scan(text):
    return [n for ch, n in _FORBIDDEN.items() if ch in text]


def _new():
    for _ in range(30):
        app = MockApp(); les = LessonSlamNT(app)
        try:
            les.start(); return app, les
        except RuntimeError:
            continue
    raise RuntimeError('חלוקה נכשלה')


def _correct(les):
    st = les._stage
    if st == 'decide':
        return les._calc_correct()
    if st == 'respond_c':
        _, _, _, resp = les._mode_c_seq
        if resp == f'1{_S["H"]}' and suit_len(les.hands['S'], 'S') >= 5:
            resp = f'1{_S["S"]}'
        return resp
    if st == 'respond_d':
        return les._mode_d_seq[3]
    if st == 'rkcb_ask_d':
        return '4NT'
    if st == 'rkcb_decide_d':
        m = _S[les._trump]
        return f'6{m}' if (les._d_total_kc >= 5 and les._d_combined >= 33) else f'5{m}'
    if st == 'decide_d':
        return '4NT'
    if st == 'decide_grand':
        return '5NT'
    return None


def run(n=500):
    modes = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    d_minor = 0          # מקרי התאמת-מינור ב-D (RKCB)
    d_contracts = {}
    violations = []

    for _ in range(n):
        app, les = _new()
        mode = les._mode
        modes[mode] = modes.get(mode, 0) + 1
        used_rkcb = False
        for _step in range(10):
            if app._new_deal_button_shown:
                break
            if getattr(les, '_awaiting_close', False):
                les.on_student_bid('Pass'); continue
            if les._stage in ('rkcb_ask_d', 'rkcb_decide_d'):
                used_rkcb = True
            c = _correct(les)
            if c is None:
                break
            les.on_student_bid(c)
        if used_rkcb:
            d_minor += 1
            contract = next((b for b in reversed(app.auction)
                             if b not in ('Pass',)), '?')
            d_contracts[contract] = d_contracts.get(contract, 0) + 1
        if app.last_feedback:
            v = _scan(app.last_feedback[0])
            if v:
                violations.append((app.last_feedback[0], v))

    print('כיסוי מודים:', modes)
    print(f'Mode D התאמת-מינור (RKCB): {d_minor} מקרים, חוזים: {d_contracts}')
    print('=' * 55)
    if not violations:
        print('✓ אין הפרות סקייל בכל הפידבקים')
    else:
        print(f'✗ {len(violations)} הפרות:')
        for t, names in violations[:8]:
            print(f'  {names}: {t!r}')
    print('=' * 55)


if __name__ == '__main__':
    run()
