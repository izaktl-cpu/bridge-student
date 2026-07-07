"""
run_lesson15.py — תסריט בדיקה לשיעור 15 (NT במינור).
זרימה: respond (S מראה 3m) → ask (S עונה לשאלת עוצר, אם N שואל).
הבודק נוהג את S עם ההכרזה הנכונה עד סוף המכרז על הרבה חלוקות,
וסורק כל פידבק לאיתור הפרות סקייל.

הרצה:
    cd D:\\bridge-student
    set PYTHONIOENCODING=utf-8
    python tests\\run_lesson15.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_app import MockApp
from lessons.lesson_minor_nt import LessonMinorNT
from engine.response import respond_minor_nt, responder_stopper_reply

_FORBIDDEN = {
    'טעית': 'משפט נזיפה',
    '—': 'מקף ארוך',
    '!': 'סימן קריאה',
    ':': 'נקודתיים',
}


def _scan(text):
    return [name for ch, name in _FORBIDDEN.items() if ch in text]


def _new():
    for _ in range(20):
        app = MockApp()
        les = LessonMinorNT(app)
        try:
            les.start()
            return app, les
        except RuntimeError:
            continue
    raise RuntimeError('לא ניתן לחלק יד אחרי 20 ניסיונות')


def _correct(les):
    if les._stage == 'respond':
        c, _ = respond_minor_nt(les.hands['S'], les._minor)
        return c
    if les._stage == 'ask':
        c, _ = responder_stopper_reply(les.hands['S'], les._minor, les._ask_suit)
        return c
    return None


def drive(n_deals=120):
    violations = []
    for _ in range(n_deals):
        app, les = _new()
        for _step in range(5):
            if app._new_deal_button_shown:
                break
            c = _correct(les)
            if c is None:
                break
            les.on_student_bid(c)
        if app.last_feedback:
            v = _scan(app.last_feedback[0])
            if v:
                violations.append((app.last_feedback[0], v))
    return violations


def test_wrong_patterns():
    ok = True
    # שלב respond שגוי × 2
    app, les = _new()
    correct = _correct(les)
    wrong = '3NT' if correct != '3NT' else 'Pass'
    les.on_student_bid(wrong)
    fb1 = app.last_feedback
    les.on_student_bid(wrong)
    fb = app.last_feedback
    print(f'respond שגוי×1: [{"WRONG" if not fb1[1] else "OK"}] {fb1[0]!r}')
    print(f'respond שגוי×2: [{"WRONG" if not fb[1] else "OK"}] {fb[0]!r}')
    ok &= (fb1[0] == 'נסה שוב' and fb[1] is False and not _scan(fb[0]))
    return ok


if __name__ == '__main__':
    print('סורק חלוקות...')
    v = drive()

    print('\n--- תבניות שגיאה ---')
    patterns_ok = test_wrong_patterns()

    print('\n' + '=' * 55)
    if len(v) == 0 and patterns_ok:
        print('✓ אין הפרות סקייל בכל הפידבקים')
    else:
        print(f'✗ נמצאו {len(v)} הפרות בפידבקים:')
        for text, names in v[:10]:
            print(f'  {names}: {text!r}')
        if not patterns_ok:
            print('✗ תבנית שגיאה לא תקינה')
    print('=' * 55)
