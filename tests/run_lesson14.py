"""
run_lesson14.py — תסריט בדיקה לשיעור 14 (נגטיב דאבל).
שלב 1: S מחליט (כולל דיאלוג סגירה אחרי X/קיו). שלב 2: N ריבאד.
הבודק נוהג את S עם ההכרזה הנכונה עד סוף המכרז על הרבה חלוקות,
וסורק כל פידבק לאיתור הפרות סקייל.

הרצה:
    cd D:\\bridge-student
    set PYTHONIOENCODING=utf-8
    python tests\\run_lesson14.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_app import MockApp
from lessons.lesson_negative_double import LessonNegativeDouble

_FORBIDDEN = {
    'טעית': 'משפט נזיפה',
    '—': 'מקף ארוך',
    '!': 'סימן קריאה',
    ':': 'נקודתיים',
}


def _scan(text):
    return [name for ch, name in _FORBIDDEN.items() if ch in text]


def _new(phase):
    for _ in range(20):
        app = MockApp()
        les = LessonNegativeDouble(app)
        if phase == 2:
            les._next_phase = 2
        try:
            les.start()
            return app, les
        except RuntimeError:
            continue
    raise RuntimeError('לא ניתן לחלק יד אחרי 20 ניסיונות')


def drive(phase, n_deals=300):
    violations = []
    for _ in range(n_deals):
        app, les = _new(phase)
        for _step in range(6):
            if app._new_deal_button_shown:
                break
            if getattr(les, '_awaiting_close', False):
                les.on_student_bid('Pass')   # סגור את הדיאלוג
            else:
                les.on_student_bid(les._correct)
        if app.last_feedback:
            v = _scan(app.last_feedback[0])
            if v:
                violations.append((app.last_feedback[0], v))
    return violations


def test_wrong_patterns():
    ok = True
    for phase in (1, 2):
        app, les = _new(phase)
        correct = les._correct
        wrong = 'Pass' if correct != 'Pass' else '3NT'
        les.on_student_bid(wrong)
        les.on_student_bid(wrong)
        fb = app.last_feedback
        tag = 'WRONG' if not fb[1] else 'OK'
        print(f'שלב {phase} שגוי×2: [{tag}] {fb[0]!r}')
        ok &= (fb[1] is False and not _scan(fb[0]))
    return ok


if __name__ == '__main__':
    print('סורק שלב 1 (S מחליט)...')
    v1 = drive(1)
    print('סורק שלב 2 (N ריבאד)...')
    v2 = drive(2)

    print('\n--- תבניות שגיאה ---')
    patterns_ok = test_wrong_patterns()

    print('\n' + '=' * 55)
    total = len(v1) + len(v2)
    if total == 0 and patterns_ok:
        print('✓ אין הפרות סקייל בכל הפידבקים')
    else:
        print(f'✗ נמצאו {total} הפרות בפידבקים:')
        for text, names in (v1 + v2)[:10]:
            print(f'  {names}: {text!r}')
        if not patterns_ok:
            print('✗ תבנית שגיאה לא תקינה')
    print('=' * 55)
