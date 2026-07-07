"""
mock_app.py — MockApp המחקה את self.app בשיעורי bridge-student.

תומך בכל הממשקים הנדרשים על-ידי BaseLesson ותת-שיעוריו.
app.after(ms, func) קורא ל-func() מיד (סינכרוני), כך שניתן
לבדוק את LessonSlamSuit בלי threading.
"""


class MockBiddingBox:
    def __init__(self):
        self.last_bid = None
        self.enabled = False

    def set_last_bid(self, bid, no_pass=False):
        self.last_bid = bid

    def set_bids(self, bids):
        self._bids = bids

    def reset(self):
        self.last_bid = None

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False


class MockAuctionWidget:
    def __init__(self, app):
        self._app = app

    def reset(self):
        self._app.auction = []

    def set_dealer(self, pos):
        self._app.dealer = pos

    def add_bid(self, bid, highlight=False):
        self._app.auction.append(bid)

    def seal(self):
        # סגירת מכרז — 3 פסים אוטומטיים בסוף (המחלקה בסיס קוראת לזה)
        pass


class MockTable:
    def show_hands(self, hands, visible):
        pass


class MockApp:
    """
    MockApp — מחקה את self.app לבדיקות יחידה של שיעורי bridge-student.

    שמורים:
        self.feedbacks  — רשימת (text, ok) מכל קריאות set_feedback
        self.auction    — רשימת כל ההכרזות שנוספו ל-auction_widget
        self.last_feedback — הפידבק האחרון (text, ok) או None
    """

    def __init__(self):
        self.feedbacks: list[tuple[str, bool]] = []
        self.auction: list[str] = []
        self.dealer: str | None = None
        self.last_feedback: tuple[str, bool] | None = None

        self._instruction = ''
        self._instruction_table = None
        self._all_hands_shown = False
        self._new_deal_button_shown = False

        self.bidding_box = MockBiddingBox()
        self.auction_widget = MockAuctionWidget(self)
        self.table = MockTable()

    # ── הוראות ────────────────────────────────────────────────────────────

    def set_instruction(self, text):
        self._instruction = text

    def set_instruction_table(self, title, rows):
        self._instruction_table = (title, rows)

    def add_immediate_table(self, rows):
        self._immediate_table = rows

    # ── פידבק ─────────────────────────────────────────────────────────────

    def set_feedback(self, text, ok, correct_answer=''):
        entry = (text, ok)
        self.feedbacks.append(entry)
        self.last_feedback = entry

    # ── ידיים ──────────────────────────────────────────────────────────────

    def show_all_hands(self):
        self._all_hands_shown = True

    def show_new_deal_button(self):
        self._new_deal_button_shown = True

    # ── after ─────────────────────────────────────────────────────────────

    def after(self, ms, func):
        """מריץ func() מיד — מחיר אפס latency לבדיקות."""
        func()
