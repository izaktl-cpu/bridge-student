"""
run_lesson10.py — תסריט בדיקה לשיעור 10 (Weak Two).
מריץ תרחישי הכרזה על שני הקבצים (מחשב פותח / תלמיד פותח)
ומדפיס את הפידבק וההכרזות ללא GUI.

הרצה:
    cd D:\\bridge-student
    python tests\\run_lesson10.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_app import MockApp
from engine.cards import SUIT_SYMBOLS
from lessons.lesson_robot_opens_weak2 import LessonRobotOpensWeak2
from lessons.lesson_student_opens_weak2 import LessonStudentOpensWeak2

_S = SUIT_SYMBOLS
_ALL_BIDS = ['Pass', '3♥', '3♠', '4♥', '4♠', '3NT']


def _wrong_bid(correct):
    """בחר הכרזה כלשהי השונה מהנכונה."""
    for b in _ALL_BIDS:
        if b != correct:
            return b
    return 'Pass'


def _show(title, app):
    fb = app.last_feedback
    print(f'=== {title} ===')
    print('auction:', ' '.join(app.auction))
    if fb:
        tag = 'OK' if fb[1] else 'WRONG'
        print(f'feedback: [{tag}] {fb[0]!r}')
    else:
        print('feedback: (none)')
    print('---')


def run_robot():
    """שיעור 10 — מחשב פותח, S עונה."""
    print('\n##### מחשב פותח Weak Two #####\n')
    ok_total = True

    # תרחיש 1: נכון
    app = MockApp(); les = LessonRobotOpensWeak2(app); les.start()
    correct = les._calc_response()
    les.on_student_bid(correct)
    _show(f'1. respond נכון ({correct})', app)
    ok_total &= app.last_feedback[1] is True

    # תרחיש 2: שגוי → נכון
    app = MockApp(); les = LessonRobotOpensWeak2(app); les.start()
    correct = les._calc_response()
    wrong = _wrong_bid(correct)
    les.on_student_bid(wrong)
    fb1 = app.last_feedback
    les.on_student_bid(correct)
    _show(f'2. respond שגוי→נכון ({wrong}→{correct})', app)
    ok_total &= (fb1[0] == 'נסה שוב' and app.last_feedback[1] is True)

    # תרחיש 3: שגוי × 2
    app = MockApp(); les = LessonRobotOpensWeak2(app); les.start()
    correct = les._calc_response()
    wrong = _wrong_bid(correct)
    les.on_student_bid(wrong)
    fb1 = app.last_feedback
    les.on_student_bid(wrong)
    _show(f'3. respond שגוי×2 ({wrong})', app)
    ok_total &= (fb1[0] == 'נסה שוב' and app.last_feedback[1] is False)

    return ok_total


def run_student():
    """שיעור 10 — תלמיד פותח, N עונה."""
    print('\n##### תלמיד פותח Weak Two #####\n')
    ok_total = True

    # תרחיש 4: נכון (פתיחת 2M)
    app = MockApp(); les = LessonStudentOpensWeak2(app); les.start()
    sym = _S[les._major]; correct = f'2{sym}'
    les.on_student_bid(correct)
    _show(f'4. open נכון ({correct})', app)
    ok_total &= app.last_feedback[1] is True

    # תרחיש 5: שגוי → נכון
    app = MockApp(); les = LessonStudentOpensWeak2(app); les.start()
    sym = _S[les._major]; correct = f'2{sym}'
    wrong = 'Pass' if correct != 'Pass' else '3NT'
    les.on_student_bid(wrong)
    fb1 = app.last_feedback
    les.on_student_bid(correct)
    _show(f'5. open שגוי→נכון ({wrong}→{correct})', app)
    ok_total &= (fb1[0] == 'נסה שוב' and app.last_feedback[1] is True)

    # תרחיש 6: שגוי × 2
    app = MockApp(); les = LessonStudentOpensWeak2(app); les.start()
    sym = _S[les._major]; correct = f'2{sym}'
    wrong = 'Pass'
    les.on_student_bid(wrong)
    fb1 = app.last_feedback
    les.on_student_bid(wrong)
    _show(f'6. open שגוי×2 ({wrong})', app)
    ok_total &= (fb1[0] == 'נסה שוב' and app.last_feedback[1] is False)

    return ok_total


if __name__ == '__main__':
    r1 = run_robot()
    r2 = run_student()
    print('\n' + '=' * 55)
    if r1 and r2:
        print('✓ כל התרחישים עברו')
    else:
        print('✗ יש תרחישים שנכשלו')
    print('=' * 55)
