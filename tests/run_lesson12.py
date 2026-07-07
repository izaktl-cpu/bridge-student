"""
run_lesson12.py — תסריט בדיקה לשיעור 12 (אוברקול).
המכרז מורכב (עד 4 סיבובים), לכן הבודק:
  1. נוהג את S עם ההכרזה הנכונה עד סוף המכרז, על הרבה חלוקות.
  2. סורק כל פידבק לאיתור הפרות סקייל (טעית / מקף ארוך / נקודתיים / סימן קריאה).
  3. בודק תבנית שגוי→נכון ושגוי×2 בשלב הראשון.

הרצה:
    cd D:\\bridge-student
    set PYTHONIOENCODING=utf-8
    python tests\\run_lesson12.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_app import MockApp
from lessons.lesson_overcall import LessonOvercall, _s_rebid_correct
from lessons.lesson_overcall_response import LessonOvercallResponse, _s_correct_bid
from engine.overcall import get_overcall

_FORBIDDEN = {
    'טעית': 'משפט נזיפה',
    '—': 'מקף ארוך',
    '!': 'סימן קריאה',
    ':': 'נקודתיים',
}


def _scan(text):
    """מחזיר רשימת הפרות שנמצאו בטקסט."""
    return [name for ch, name in _FORBIDDEN.items() if ch in text]


# ── שיעור 12א: תלמיד מכריז אוברקול ──────────────────────────────────────────

def _overcall_correct(les):
    if les._stage == 'bid1':
        c, _ = get_overcall(les.hands['S'], les._e_bid)
        return c
    if les._stage == 'play':
        c, _ = _s_rebid_correct(les.hands['S'], les._s_bid1,
                                les._n_last_bid, op_bid=les._e_bid)
        return c
    return None


def drive_overcall(n_deals=300):
    violations = []
    for _ in range(n_deals):
        app = MockApp(); les = LessonOvercall(app); les.start()
        for _step in range(8):
            if les._stage == 'done':
                break
            c = _overcall_correct(les)
            if c is None:
                break
            les.on_student_bid(c)
        if app.last_feedback:
            v = _scan(app.last_feedback[0])
            if v:
                violations.append((app.last_feedback[0], v))
    return violations


# ── שיעור 12ב: תלמיד עונה לאוברקול ──────────────────────────────────────────

def _response_correct(les):
    s_prev = les._s_bids[-1] if les._s_bids else None
    n_last = les._n_rebids[-1][0] if les._n_rebids else les._n_bid
    c, _ = _s_correct_bid(les.hands['S'], les._n_bid, les._w_bid, n_last, s_prev)
    return c


def drive_response(n_deals=300):
    violations = []
    for _ in range(n_deals):
        app = MockApp(); les = LessonOvercallResponse(app); les.start()
        for _step in range(8):
            if les._stage == 99:
                break
            c = _response_correct(les)
            les.on_student_bid(c)
        if app.last_feedback:
            v = _scan(app.last_feedback[0])
            if v:
                violations.append((app.last_feedback[0], v))
    return violations


# ── תבניות שגיאה בשלב הראשון ────────────────────────────────────────────────

def test_wrong_patterns():
    ok = True

    # אוברקול — שגוי → נכון
    app = MockApp(); les = LessonOvercall(app); les.start()
    correct, _ = get_overcall(les.hands['S'], les._e_bid)
    wrong = 'Pass' if correct != 'Pass' else '1♠'
    les.on_student_bid(wrong); fb1 = app.last_feedback
    ok &= (fb1[0] == 'נסה שוב')

    # אוברקול — שגוי × 2
    app = MockApp(); les = LessonOvercall(app); les.start()
    correct, _ = get_overcall(les.hands['S'], les._e_bid)
    wrong = 'Pass' if correct != 'Pass' else '1♠'
    les.on_student_bid(wrong); les.on_student_bid(wrong)
    fb = app.last_feedback
    print(f'אוברקול שגוי×2: [{"WRONG" if not fb[1] else "OK"}] {fb[0]!r}')
    ok &= (fb[1] is False and not _scan(fb[0]))

    # תגובה — שגוי × 2
    app = MockApp(); les = LessonOvercallResponse(app); les.start()
    correct = _response_correct(les)
    wrong = 'Pass' if correct != 'Pass' else '3NT'
    les.on_student_bid(wrong); les.on_student_bid(wrong)
    fb = app.last_feedback
    print(f'תגובה שגוי×2:   [{"WRONG" if not fb[1] else "OK"}] {fb[0]!r}')
    ok &= (fb[1] is False and not _scan(fb[0]))

    return ok


if __name__ == '__main__':
    print('סורק חלוקות אוברקול...')
    v1 = drive_overcall()
    print('סורק חלוקות תגובה...')
    v2 = drive_response()

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
