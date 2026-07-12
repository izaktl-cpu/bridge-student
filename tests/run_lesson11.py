"""
run_lesson11.py — תסריט בדיקה לשיעור 11 (Ogust).
זרימה: open → respond (תגובת אוגוסט) → north (החלטת N).
כל שלב נבדק ב-3 תבניות: נכון / שגוי→נכון / שגוי×2.

הרצה:
    cd D:\\bridge-student
    set PYTHONIOENCODING=utf-8
    python tests\\run_lesson11.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_app import MockApp
from engine.cards import SUIT_SYMBOLS
from lessons.lesson_ogust import LessonOgust, _calc_ogust

_S = SUIT_SYMBOLS
_OGUST_BIDS = ['3♣', '3♦', '3♥', '3♠', '3NT']


def _new():
    app = MockApp()
    les = LessonOgust(app)
    les.start()
    return app, les


def _sym(les):
    return _S[les._major]


def _open_correct(les):
    return f'2{_sym(les)}'


def _respond_correct(les):
    return _calc_ogust(les.hands['S'], les._major)


def _north_correct(les):
    return les._north_final(les._ogust_bid)


def _bw_correct(les):
    sym = _S[les._major]
    return f'6{sym}' if les._total_kc >= 4 else f'5{sym}'


def _play_blackwood_if_needed(les):
    """אם ההחלטה הייתה 4NT — ממשיך לשלב שאלת האסים עד הסלם."""
    if les._stage == 'blackwood':
        les.on_student_bid(_bw_correct(les))


def _other(options, correct):
    for b in options:
        if b != correct:
            return b
    return options[0]


def _advance_to_respond(les):
    les.on_student_bid(_open_correct(les))


def _advance_to_north(les):
    les.on_student_bid(_open_correct(les))
    les.on_student_bid(_respond_correct(les))


def _show(title, app, les):
    fb = app.last_feedback
    print(f'=== {title} ===')
    print('auction:', ' '.join(app.auction))
    print('stage:  ', les._stage)
    if fb:
        tag = 'OK' if fb[1] else 'WRONG'
        print(f'feedback: [{tag}] {fb[0]!r}')
    else:
        print('feedback: (none)')
    print('---')


def run():
    ok = True

    # ── שלב open ──────────────────────────────────────────────────────────
    app, les = _new()
    les.on_student_bid(_open_correct(les))
    _show(f'1. open נכון ({_open_correct(les)})', app, les)
    ok &= les._stage == 'respond'

    app, les = _new()
    correct = _open_correct(les)
    les.on_student_bid('Pass'); fb1 = app.last_feedback
    les.on_student_bid(correct)
    _show(f'2. open שגוי→נכון (Pass→{correct})', app, les)
    ok &= (fb1[0] == 'נסה שוב' and les._stage == 'respond')

    app, les = _new()
    correct = _open_correct(les)
    les.on_student_bid('Pass'); fb1 = app.last_feedback
    les.on_student_bid('Pass')
    _show('3. open שגוי×2 (Pass)', app, les)
    ok &= (fb1[0] == 'נסה שוב' and app.last_feedback[1] is False)

    # ── שלב respond ───────────────────────────────────────────────────────
    app, les = _new(); _advance_to_respond(les)
    correct = _respond_correct(les)
    les.on_student_bid(correct)
    _show(f'4. respond נכון ({correct})', app, les)
    ok &= les._stage == 'north'

    app, les = _new(); _advance_to_respond(les)
    correct = _respond_correct(les); wrong = _other(_OGUST_BIDS, correct)
    les.on_student_bid(wrong); fb1 = app.last_feedback
    les.on_student_bid(correct)
    _show(f'5. respond שגוי→נכון ({wrong}→{correct})', app, les)
    ok &= (fb1[0] == 'נסה שוב' and les._stage == 'north')

    app, les = _new(); _advance_to_respond(les)
    correct = _respond_correct(les); wrong = _other(_OGUST_BIDS, correct)
    les.on_student_bid(wrong); fb1 = app.last_feedback
    les.on_student_bid(wrong)
    _show(f'6. respond שגוי×2 ({wrong})', app, les)
    ok &= (fb1[0] == 'נסה שוב' and app.last_feedback[1] is False)

    # ── שלב north ─────────────────────────────────────────────────────────
    app, les = _new(); _advance_to_north(les)
    correct = _north_correct(les)
    les.on_student_bid(correct)
    _play_blackwood_if_needed(les)
    _show(f'7. north נכון ({correct})', app, les)
    ok &= app.last_feedback[1] is True

    app, les = _new(); _advance_to_north(les)
    sym = _sym(les); correct = _north_correct(les)
    wrong = _other([f'3{sym}', f'4{sym}', f'6{sym}'], correct)
    les.on_student_bid(wrong); fb1 = app.last_feedback
    les.on_student_bid(correct)
    _play_blackwood_if_needed(les)
    _show(f'8. north שגוי→נכון ({wrong}→{correct})', app, les)
    ok &= (fb1[0] == 'נסה שוב' and app.last_feedback[1] is True)

    app, les = _new(); _advance_to_north(les)
    sym = _sym(les); correct = _north_correct(les)
    wrong = _other([f'3{sym}', f'4{sym}', f'6{sym}'], correct)
    les.on_student_bid(wrong); fb1 = app.last_feedback
    les.on_student_bid(wrong)
    _show(f'9. north שגוי×2 ({wrong})', app, les)
    ok &= (fb1[0] == 'נסה שוב' and app.last_feedback[1] is False)

    print('\n' + '=' * 55)
    print('✓ כל 9 התרחישים עברו' if ok else '✗ יש תרחישים שנכשלו')
    print('=' * 55)


if __name__ == '__main__':
    run()
