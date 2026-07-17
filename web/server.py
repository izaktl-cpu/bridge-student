"""
שרת FastAPI שעוטף את ה-engine והשיעורים ומגיש אותם ל-web.
מריץ את השיעורים ללא שינוי דרך מתאם ה-View המנותק (web_view.WebApp).
"""
import os
import re
import sys
import uuid
import importlib

# מאפשר להריץ מכל מקום — מוסיף את שורש הפרויקט ל-path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from web.web_view import WebApp
from web import reports

# ── מיפוי שיעורים (מתוך app.py, בלי תלות ב-tkinter) ──────────────────────────
_LESSONS = [
    ('lessons.lesson_robot_opens_1nt',     'LessonRobotOpens1NT'),      # 0
    ('lessons.lesson_nt_open',             'LessonNTOpen'),             # 1
    ('lessons.lesson_student_opens_major', 'LessonStudentOpensMajor'),  # 2
    ('lessons.lesson_robot_opens_major',   'LessonRobotOpensMajor'),    # 3
    ('lessons.lesson_stayman',             'LessonStayman'),            # 4
    ('lessons.lesson_transfer',            'LessonTransfer'),           # 5
    ('lessons.lesson_student_opens_minor', 'LessonStudentOpensMinor'),  # 6
    ('lessons.lesson_robot_opens_minor',   'LessonRobotOpensMinor'),    # 7
    ('lessons.lesson_robot_opens_2c',      'LessonRobotOpens2C'),       # 8
    ('lessons.lesson_robot_opens_2nt',     'LessonRobotOpens2NT'),      # 9
    ('lessons.lesson_slam_nt',             'LessonSlamNT'),             # 10
    ('lessons.lesson_slam_suit',           'LessonSlamSuit'),           # 11
    ('lessons.lesson_robot_opens_weak2',   'LessonRobotOpensWeak2'),    # 12
    ('lessons.lesson_student_opens_weak2', 'LessonStudentOpensWeak2'),  # 13
    ('lessons.lesson_ogust',               'LessonOgust'),              # 14
    ('lessons.lesson_overcall',            'LessonOvercall'),           # 15
    ('lessons.lesson_overcall_response',   'LessonOvercallResponse'),   # 16
    ('lessons.lesson_fourth_suit',         'LessonFourthSuit'),         # 17
    ('lessons.lesson_takeout_double',      'LessonTakeoutDouble'),      # 18
    ('lessons.lesson_negative_double',     'LessonNegativeDouble'),     # 19
    ('lessons.lesson_minor_nt',            'LessonMinorNT'),            # 20
]

# כפתורי התפריט: (תווית, אינדקס שיעור)
_BUTTONS = [
    ('שיעור 1 · מענה ל-1NT',   0),
    ('שיעור 2 · מיגורים',       3),
    ('שיעור 3 · מינורים',       7),
    ('שיעור 4 · סטיימן',        4),
    ('שיעור 5 · טרנספר',        5),
    ('שיעור 6 · 2NT',           9),
    ('שיעור 7 · 2♣ חזקה',       8),
    ('שיעור 8 · סלם NT',        10),
    ('שיעור 9 · סלם בצבע',      11),
    ('שיעור 10 · Weak Two',     12),
    ('שיעור 11 · Ogust',        14),
    ('שיעור 12 · אוברקול',      15),
    ('שיעור 13 · דבל להוצאה',   18),
    ('שיעור 14 · נגטיב דבל',    19),
    ('שיעור 15 · NT במינור',    20),
]


def _lesson_class(idx):
    module_path, class_name = _LESSONS[idx]
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


def _start_with_retry(webapp, lesson_cls, tries=8):
    """מחלק ומתחיל שיעור. חלק מהמחלקים נכשלים לעיתים נדירות (אילוצים צפופים) —
    מנסים שוב עם חלוקה טרייה במקום להקריס את היד לתלמיד."""
    last_err = None
    for _ in range(tries):
        try:
            lesson = webapp.load_lesson(lesson_cls)
            lesson.start()
            return lesson
        except RuntimeError as e:
            last_err = e
    raise HTTPException(500, f'לא ניתן לחלק יד לשיעור זה: {last_err}')


# ── מצב סשנים בזיכרון ────────────────────────────────────────────────────────
_SESSIONS: dict[str, dict] = {}   # sid → {'app': WebApp, 'lesson_idx': int}


app = FastAPI(title="עוזר ברידג׳ לתלמיד")


class NewDealReq(BaseModel):
    lesson_idx: int
    session_id: str | None = None


class BidReq(BaseModel):
    session_id: str
    bid: str


class ReportReq(BaseModel):
    session_id: str
    note: str | None = ''


@app.get('/health')
def health():
    """נקודת keep-alive קלה (ל-UptimeRobot) — לא נוגעת ב-engine."""
    return {'status': 'ok'}


@app.get('/api/lessons')
def list_lessons():
    return {'buttons': [{'label': lbl, 'idx': idx} for lbl, idx in _BUTTONS]}


@app.post('/api/new_deal')
def new_deal(req: NewDealReq):
    if not (0 <= req.lesson_idx < len(_LESSONS)):
        raise HTTPException(400, 'lesson_idx לא חוקי')
    sid = req.session_id or uuid.uuid4().hex
    webapp = WebApp()
    _start_with_retry(webapp, _lesson_class(req.lesson_idx))
    _SESSIONS[sid] = {'app': webapp, 'lesson_idx': req.lesson_idx}
    state = webapp.snapshot()
    state['session_id'] = sid
    state['lesson_idx'] = req.lesson_idx
    return state


@app.post('/api/bid')
def bid(req: BidReq):
    sess = _SESSIONS.get(req.session_id)
    if not sess:
        raise HTTPException(404, 'סשן לא נמצא — התחל יד חדשה')
    webapp = sess['app']
    try:
        webapp._lesson.on_student_bid(req.bid)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f'שגיאה בעיבוד ההכרזה: {e}')
    state = webapp.snapshot()
    state['session_id'] = req.session_id
    state['lesson_idx'] = sess['lesson_idx']
    return state


@app.post('/api/report')
def report(req: ReportReq):
    sess = _SESSIONS.get(req.session_id)
    if not sess:
        raise HTTPException(404, 'סשן לא נמצא — התחל יד חדשה')
    webapp = sess['app']
    idx = sess['lesson_idx']
    label = next((lbl for lbl, i in _BUTTONS if i == idx), '')
    rec = reports.build_report(webapp, note=req.note or '', lesson_idx=idx, lesson_label=label)
    reports.save_report(rec)
    emailed, info = reports.send_email(rec)
    if not emailed:
        # הפירוט עלול להכיל את מפתח ה-API — ללוג בלבד, לא ללקוח
        print(f'[report] email failed: {info}', flush=True)
    return {'ok': True, 'saved': True, 'emailed': emailed}


@app.post('/api/replay')
def replay(req: BidReq):
    sess = _SESSIONS.get(req.session_id)
    if not sess:
        raise HTTPException(404, 'סשן לא נמצא — התחל יד חדשה')
    webapp = sess['app']
    webapp._reset_panel()
    webapp.table.clear_feedback()
    webapp.bidding_box.reset()
    webapp._lesson.replay()
    state = webapp.snapshot()
    state['session_id'] = req.session_id
    state['lesson_idx'] = sess['lesson_idx']
    return state


# ── הגשת ה-frontend ──────────────────────────────────────────────────────────
_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')


def _asset_version():
    """חותם גרסה לפי זמן העדכון של הקבצים הסטטיים.

    בלעדיו צריך להעלות ידנית את ?v=N ב-index.html בכל שינוי, ומי ששכח —
    התלמידים ממשיכים לקבל את הגרסה הישנה מהמטמון של הדפדפן.
    """
    times = []
    for name in ('app.js', 'style.css'):
        path = os.path.join(_STATIC, name)
        if os.path.exists(path):
            times.append(int(os.path.getmtime(path)))
    return str(max(times)) if times else '0'


@app.get('/')
def index():
    with open(os.path.join(_STATIC, 'index.html'), encoding='utf-8') as f:
        html = f.read()
    html = re.sub(r'(/static/(?:app\.js|style\.css))\?v=[^"\']*',
                  lambda m: f'{m.group(1)}?v={_asset_version()}', html)
    # ה-HTML עצמו לעולם לא נשמר במטמון, אחרת הדפדפן ממשיך לקרוא חותם גרסה ישן
    # ולא מגלה שהקבצים התחלפו. הקבצים הממוספרים כן נשמרים, וזו כל הנקודה.
    return HTMLResponse(html, headers={'Cache-Control': 'no-cache, must-revalidate'})


app.mount('/static', StaticFiles(directory=_STATIC), name='static')
