"""
scale_auto_lesson3.py — בדיקה אוטומטית שיעור 3
מריץ שיעור 3 דרך MockApp, מזין כל ההכרזות נכון,
ובודק ש-lesson מגיב ok=True בכל יד.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.opening import opening_bid
from engine.response import respond_major
from engine.rebid import opener_rebid
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS


# ── Mock UI ───────────────────────────────────────────────────────────────────

class _MockBiddingBox:
    def __init__(self):
        self.last_bid = None
        self.enabled  = True
    def reset(self):              self.last_bid = None
    def set_last_bid(self, bid):  self.last_bid = bid
    def disable(self):            self.enabled  = False


class _MockAuctionWidget:
    def __init__(self):             self.bids = []
    def reset(self):                self.bids = []
    def set_dealer(self, _):        pass
    def add_bid(self, bid, highlight=False): self.bids.append(bid)
    def seal(self):                          pass


class _MockTable:
    def show_hands(self, *a, **kw): pass


class MockApp:
    def __init__(self):
        self.table          = _MockTable()
        self.auction_widget = _MockAuctionWidget()
        self.bidding_box    = _MockBiddingBox()
        self._reset()

    def _reset(self):
        self.feedback_text = None
        self.feedback_ok   = None
        self.finished      = False
        self.auction_widget.reset()
        self.bidding_box.reset()
        self.bidding_box.enabled = True

    def set_instruction_table(self, text, rows): pass
    def set_instruction(self, text):             pass
    def show_all_hands(self):                    pass

    def show_new_deal_button(self):
        self.finished = True

    def set_feedback(self, text, ok=True, correct_answer=''):
        self.feedback_text = text
        self.feedback_ok   = ok


# ── Runner ────────────────────────────────────────────────────────────────────

def run(n=500):
    from lessons.lesson_student_opens_major import LessonStudentOpensMajor

    app    = MockApp()
    lesson = LessonStudentOpensMajor(app)

    passed = 0
    failed = 0
    errors = []

    for deal_num in range(1, n + 1):
        app._reset()
        try:
            lesson.start()
            hands  = lesson.hands
            major  = lesson._major
            sym    = _S[major]

            # ── שלב 1: תלמיד פותח ──────────────────────────────
            open_bid = f'1{sym}'
            lesson.on_student_bid(open_bid)

            if app.finished:
                # N ענה 4M או 3NT — חוזה סופי, לא צריך ריבאד
                if not app.feedback_ok:
                    raise AssertionError(f'פתיחה: ok=False — {app.feedback_text}')
                passed += 1
                continue

            # ── שלב 2: תלמיד ריבאד ─────────────────────────────
            north_bid = lesson._north_bid
            rebid, _  = opener_rebid(hands['S'], open_bid, north_bid)
            lesson.on_student_bid(rebid)

            if not app.finished:
                raise AssertionError('השיעור לא הסתיים אחרי ריבאד')
            if not app.feedback_ok:
                raise AssertionError(f'ריבאד: ok=False — {app.feedback_text}')

            passed += 1

        except Exception as exc:
            failed += 1
            errors.append((deal_num, str(exc)))

    sep = '─' * 50
    total = passed + failed
    status = '✓' if failed == 0 else '✗'

    print(sep)
    print(f' שיעור 3 — אוטו (MockApp)  |  {total} ידיות  {status}')
    print(sep)
    print(f'  עברו: {passed}/{total}')
    if errors:
        print(f'  ✗ שגיאות ({len(errors)}):')
        for deal_num, msg in errors[:10]:
            print(f'    יד {deal_num:3d}: {msg}')
    else:
        print('  ✓ אין שגיאות')
    print(sep)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    run(n)
