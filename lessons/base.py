class BaseLesson:
    def __init__(self, app):
        self.app             = app
        self.hands           = {}
        self._replaying      = False
        self._last_wrong_bid = None
        self._awaiting_close = False

    def start(self):
        raise NotImplementedError

    def on_student_bid(self, bid):
        raise NotImplementedError

    def replay(self):
        self._replaying = True
        self.start()

    def _seal_auction(self):
        """סגור את המכרז עם 3 פסים רצופים בסוף."""
        self.app.auction_widget.seal()

    def _start_closing(self, message, ok, correct_answer=''):
        """המתן להכרזה מ-S (תורו), אחר כך W+N פס אוטומטי."""
        self._awaiting_close = True
        self._close_msg      = message
        self._close_ok       = ok
        self._close_correct  = correct_answer
        self.app.show_all_hands()
        self.app.bidding_box.enable()
        self.app.bidding_box.set_bids(None)

    def _handle_close(self, bid):
        """קרא בתחילת on_student_bid. מחזיר True אם הטיפול הושלם."""
        if self._awaiting_close:
            self._awaiting_close = False
            self.app.auction_widget.add_bid(bid)         # S
            self.app.auction_widget.add_bid('Pass')      # W
            self.app.auction_widget.add_bid('Pass')      # N
            self._finish(self._close_msg, self._close_ok, self._close_correct)
            return True
        return False
