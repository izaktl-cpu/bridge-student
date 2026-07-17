"""
דיווחי "נתקעתי" — אוסף snapshot מלא של המצב שהתלמיד נתקע בו,
שומר לקובץ (מקור-אמת מתמיד), ואם מוגדר מפתח Resend — שולח מייל למורה.

הכל אנונימי: נשמרת רק היד, המכרז וההקשר — בלי שם או פרטים מזהים.
"""
import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

from engine.scoring import hcp as _hcp
from engine.cards import SUITS, SUIT_SYMBOLS, hand_by_suit, fmt_rank

_REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
_REPORTS_FILE = os.path.join(_REPORTS_DIR, 'reports.jsonl')


# ── בניית הדיווח ─────────────────────────────────────────────────────────────

def _hand_str(hand):
    """מחרוזת קריאה של יד: ♠AKx ♥Qxx ..."""
    by = hand_by_suit(hand)
    parts = []
    for s in SUITS:
        ranks = ''.join(fmt_rank(r) for r in by[s]) or '-'
        parts.append(f'{SUIT_SYMBOLS[s]}{ranks}')
    return ' '.join(parts)


def build_report(webapp, note='', lesson_idx=None, lesson_label=''):
    """אוסף את מלוא המצב מהסשן. כולל את כל 4 הידיים (לשחזור מדויק)."""
    lesson = webapp._lesson
    hands = getattr(lesson, 'hands', {}) or {}
    snap = webapp.snapshot()

    hands_full = {}
    for seat in ('N', 'E', 'S', 'W'):
        h = hands.get(seat)
        if h is None:
            continue
        hands_full[seat] = {
            'cards': list(h),                 # רשימת קלפים גולמית — לשחזור
            'pretty': _hand_str(h),           # קריא לאדם
            'hcp': _hcp(h),
        }

    return {
        'ts': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'lesson_idx': lesson_idx,
        'lesson': lesson_label or snap.get('title', ''),
        'note': (note or '').strip(),
        'dealer': snap['auction']['dealer'],
        'auction': [f"{b['seat']}:{b['bid']}" for b in snap['auction']['bids']],
        'feedback': snap['feedback'].get('text', ''),
        'panel_header': snap['panel'].get('header', ''),
        'enabled_bids': snap['bidding_box'].get('enabled', []),
        'hands': hands_full,
    }


# ── שמירה ────────────────────────────────────────────────────────────────────

def save_report(report):
    os.makedirs(_REPORTS_DIR, exist_ok=True)
    with open(_REPORTS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(report, ensure_ascii=False) + '\n')


# ── פורמט מייל ───────────────────────────────────────────────────────────────

def report_text(r):
    lines = [
        f"דיווח 'נתקעתי' — {r['lesson']}",
        f"זמן: {r['ts']}",
        '',
    ]
    if r['note']:
        lines += [f"הערת התלמיד: {r['note']}", '']
    lines.append(f"מחלק: {r['dealer']}")
    lines.append("מכרז: " + ' '.join(r['auction']))
    if r['feedback']:
        lines.append("משוב אחרון: " + r['feedback'].replace('\n', ' / '))
    lines.append('')
    lines.append('ידיים:')
    for seat in ('N', 'E', 'S', 'W'):
        h = r['hands'].get(seat)
        if h:
            lines.append(f"  {seat} ({h['hcp']}): {h['pretty']}")
    return '\n'.join(lines)


# ── שליחת מייל דרך Resend (אופציונלי, לפי משתני סביבה) ────────────────────────

def send_email(report):
    """שולח מייל אם מוגדר RESEND_API_KEY. מחזיר (sent: bool, info: str)."""
    key = os.environ.get('RESEND_API_KEY', '').strip()
    if not key:
        return False, 'no-key'
    to_addr = os.environ.get('REPORT_EMAIL', 'izaktl@gmail.com').strip()
    from_addr = os.environ.get('RESEND_FROM', 'onboarding@resend.dev').strip()

    body = report_text(report)
    payload = json.dumps({
        'from': from_addr,
        'to': [to_addr],
        'subject': f"נתקעתי — {report['lesson']}",
        'text': body,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            # בלי User-Agent, Cloudflare שלפני Resend חוסם עם error 1010
            'User-Agent': 'bridge-student/1.0',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True, f'sent ({resp.status})'
    except urllib.error.HTTPError as e:
        return False, f'http-error {e.code}: {e.read().decode("utf-8", "ignore")[:200]}'
    except Exception as e:
        return False, f'error: {e}'
