"""
בדיקת עשן לכל השיעורים דרך מתאם ה-web (WebApp).
לכל שיעור: מריץ הרבה ידיים, מזין הכרזות אקראיות מהחוקיות, ומוודא
שאין חריגות (AttributeError/TypeError וכו') — כלומר שהמתאם תואם לשיעור.
"""
import os
import sys
import random
import traceback

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

sys.stdout.reconfigure(encoding='utf-8')

from web.web_view import WebApp
from web import server

_BUTTONS = server._BUTTONS
DEALS_PER_LESSON = 60
MAX_TURNS = 40


def drive_one(idx):
    """יד אחת: start ואז הכרזות אקראיות עד סיום. מחזיר (finished, err)."""
    webapp = WebApp()
    lesson = server._start_with_retry(webapp, server._lesson_class(idx))
    for _ in range(MAX_TURNS):
        snap = webapp.snapshot()
        if snap['done']:
            return True, None
        enabled = snap['bidding_box']['enabled']
        if not enabled:
            return snap['done'], None
        bid = random.choice(enabled)
        lesson.on_student_bid(bid)
    return webapp.snapshot()['done'], None


def run():
    print('=' * 60)
    print('בדיקת עשן — כל השיעורים דרך מתאם ה-web')
    print('=' * 60)
    total_err = 0
    for label, idx in _BUTTONS:
        errors = []
        not_finished = 0
        for i in range(DEALS_PER_LESSON):
            try:
                finished, _ = drive_one(idx)
                if not finished:
                    not_finished += 1
            except Exception as e:
                errors.append((i, repr(e), traceback.format_exc()))
        mark = '✓' if not errors else '✗'
        note = 'תקין' if not errors else f'{len(errors)} חריגות'
        if not_finished:
            note += f'  (לא הסתיימו: {not_finished}/{DEALS_PER_LESSON})'
        print(f'  {mark}  שיעור idx={idx:<2} {label:<22} {note}')
        if errors:
            total_err += len(errors)
            # מדפיס את החריגה הראשונה בלבד
            print('       └─ ' + errors[0][1])
            for line in errors[0][2].strip().splitlines()[-4:]:
                print('          ' + line)
    print('=' * 60)
    print('✓ אין חריגות בכל השיעורים' if total_err == 0 else f'✗ סה״כ חריגות: {total_err}')
    print('=' * 60)
    return total_err


if __name__ == '__main__':
    sys.exit(1 if run() else 0)
