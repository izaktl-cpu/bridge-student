from lessons.base import BaseLesson
from engine.deal_constraints import deal_negative_double_phase1, deal_negative_double_phase2
from engine.negative_double import (can_negative_double, s_response,
                                    opener_rebid, opener_after_natural,
                                    opener_after_cue)
from engine.opening import opening_bid as _opening_bid
from engine.scoring import hcp, distribution, has_stopper
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_chose_wrong_why

_S = SUIT_SYMBOLS
_SYM_MAP = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}
_RANK    = {'C': 1, 'D': 2, 'H': 3, 'S': 4}


def _bid_suit(bid):
    for ch, s in _SYM_MAP.items():
        if ch in bid:
            return s
    return None


def _suit_sym(suit):
    return next((ch for ch, s in _SYM_MAP.items() if s == suit), suit)


def _e_overcall(e_hand, n_suit):
    """מזהה צבע האוברקול של E (המיגור היחיד עם 5+ קלפים)."""
    d = distribution(e_hand)
    cands = [m for m in ['H', 'S'] if d[m] >= 5 and m != n_suit]
    return cands[0] if len(cands) == 1 else None


class LessonNegativeDouble(BaseLesson):
    TITLE = 'שיעור 14. נגטיב דאבל'

    def start(self):
        self._awaiting_close = False
        if not self._replaying:
            self._phase = getattr(self, '_next_phase', 1)
            self._next_phase = 2 if self._phase == 1 else 1
            self._setup()

        self._replaying = False
        self._tries     = 0

        if self._phase == 1:
            self._start_phase1()
        else:
            self._start_phase2()

    def _setup(self):
        if getattr(self, '_preset_hands', None):
            self.hands          = self._preset_hands
            self._preset_hands  = None
        elif self._phase == 1:
            self.hands = deal_negative_double_phase1()
        else:
            self.hands = deal_negative_double_phase2()

        n_bid, _ = _opening_bid(self.hands['N'])
        self._n_bid  = n_bid
        self._n_suit = _bid_suit(n_bid)
        self._e_suit = _e_overcall(self.hands['E'], self._n_suit)
        self._e_level = 1
        e_sym = _suit_sym(self._e_suit)
        self._e_bid = f'1{e_sym}'

        if self._phase == 1:
            self._correct, self._expl = s_response(
                self.hands['S'], self._n_suit, self._e_suit, self._e_level)
        else:
            self._correct, self._expl = opener_rebid(
                self.hands['N'], self._n_suit, self._e_suit, self._e_level)

    # ── שלב 1: S מחליט ────────────────────────────────────────────────────

    def _start_phase1(self):
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('W')
        self.app.auction_widget.add_bid('Pass')
        self.app.auction_widget.add_bid(self._n_bid)
        self.app.auction_widget.add_bid(self._e_bid)
        self.app.bidding_box.set_last_bid(self._e_bid)

        h   = hcp(self.hands['S'])
        d   = distribution(self.hands['S'])
        ns  = _suit_sym(self._n_suit)
        es  = _suit_sym(self._e_suit)
        unbid_major = next((m for m in ['S', 'H'] if m not in (self._n_suit, self._e_suit)), None)
        unbid_minor = next((m for m in ['D', 'C'] if m not in (self._n_suit, self._e_suit)), None)
        um_sym = _suit_sym(unbid_major) if unbid_major else '—'
        mn_sym = _suit_sym(unbid_minor) if unbid_minor else '—'

        if unbid_major:
            um_lvl     = self._e_level if _RANK[unbid_major] > _RANK[self._e_suit] else self._e_level + 1
            um_bid     = f'{um_lvl}{um_sym}'
            um_hcp     = '6' if um_lvl == self._e_level else '11'
        else:
            um_bid, um_hcp = um_sym, '6'
        mn_lvl = (self._e_level if unbid_minor and _RANK[unbid_minor] > _RANK[self._e_suit]
                  else self._e_level + 1)
        mn_bid = f'{mn_lvl}{mn_sym}' if unbid_minor else '—'

        rows = [
            (um_bid,              f'5+ {um_sym}, {um_hcp}+ נק׳'),
            ('3NT',               f'13+ נק׳, עוצר ב{es}'),
            (f'קיו {es}',         f'13+ נק׳, אין עוצר'),
            ('2NT',               f'11–12 נק׳, עוצר ב{es}'),
            (mn_bid,              f'5+ {mn_sym}, 11+ נק׳'),
            ('X',                 f'8+ נק׳, 4 {um_sym}'),
            ('1NT',               f'7–10 נק׳, עוצר ב{es}'),
            ('פס',                'אין מספיק'),
        ]
        self.app.set_instruction_table(
            f'N פתח {self._n_bid}, E הכריז {self._e_bid}.\n'
            f'יש לך {h} נק׳. מה תכריז?',
            rows
        )

    def _on_phase1(self, bid):
        correct = self._correct
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            if bid == 'Pass':
                # S פס — W ו-N פסים אוטומטית, אין צורך בקליק נוסף
                self.app.auction_widget.add_bid('Pass')   # W
                self.app.auction_widget.add_bid('Pass')   # N
                self._finish(f'נכון. פס\n{self._expl}', ok=True)
                return
            if bid == 'X':
                n_bid, n_expl = opener_rebid(
                    self.hands['N'], self._n_suit, self._e_suit, self._e_level)
                self.app.auction_widget.add_bid('Pass')   # W
                self.app.auction_widget.add_bid(n_bid)    # N
                self.app.auction_widget.add_bid('Pass')   # E
                self._start_closing(
                    f'נכון. X\n{self._expl}\nN מכריז {n_bid}: {n_expl}',
                    ok=True)
            elif _bid_suit(bid) is None:  # 1NT וכדומה
                self.app.auction_widget.add_bid('Pass')   # W
                self.app.auction_widget.add_bid('Pass')   # N
                self.app.auction_widget.add_bid('Pass')   # E
                self._finish(f'נכון. {bid}\n{self._expl}', ok=True)
            else:
                s_suit = _bid_suit(bid)
                is_cue = (s_suit == self._e_suit)
                if is_cue:
                    n_bid, n_expl = opener_after_cue(
                        self.hands['N'], self._n_suit, self._e_suit)
                else:
                    n_bid, n_expl = opener_after_natural(self.hands['N'], s_suit)
                self.app.auction_widget.add_bid('Pass')   # W
                self.app.auction_widget.add_bid(n_bid)    # N
                self.app.auction_widget.add_bid('Pass')   # E
                self._start_closing(
                    f'נכון. {bid}\n{self._expl}\nN מכריז {n_bid}: {n_expl}',
                    ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._close_wrong_phase1(bid, msg_chose_wrong_why(bid, correct, self._expl))
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(f'{self._expl}\nנסה שנית.', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._close_wrong_phase1(
                    bid,
                    msg_chose_wrong_why(bid, correct, self._expl),
                    correct_answer=correct)

    def _close_wrong_phase1(self, bid, msg, correct_answer=''):
        """סגירת שלב 1 לאחר הכרזה שגויה — X תמיד מקבל ריבאד N."""
        if bid == 'X':
            n_bid, n_expl = opener_rebid(
                self.hands['N'], self._n_suit, self._e_suit, self._e_level)
            self.app.auction_widget.add_bid('Pass')   # W
            self.app.auction_widget.add_bid(n_bid)    # N
            self.app.auction_widget.add_bid('Pass')   # E
            self._start_closing(msg, ok=False, correct_answer=correct_answer)
        else:
            self.app.auction_widget.add_bid('Pass')   # W
            self.app.auction_widget.add_bid('Pass')   # N
            self.app.auction_widget.add_bid('Pass')   # E
            self._finish(msg, ok=False, correct_answer=correct_answer)

    # ── שלב 2: N מכריז ריבאד ──────────────────────────────────────────────

    def _start_phase2(self):
        self.app.table.show_hands(self.hands, visible=('N',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('W')
        self.app.auction_widget.add_bid('Pass')
        self.app.auction_widget.add_bid(self._n_bid)
        self.app.auction_widget.add_bid(self._e_bid)
        self.app.auction_widget.add_bid('X')
        self.app.auction_widget.add_bid('Pass')
        self.app.bidding_box.set_last_bid(self._e_bid)

        h  = hcp(self.hands['N'])
        es = _suit_sym(self._e_suit)
        unbid_major = next((m for m in ['S', 'H'] if m not in (self._n_suit, self._e_suit)), None)
        unbid_minor = next((m for m in ['D', 'C'] if m not in (self._n_suit, self._e_suit)), None)
        um_sym = _suit_sym(unbid_major) if unbid_major else '—'
        mn_sym = _suit_sym(unbid_minor) if unbid_minor else '—'

        def _lvl(suit):
            return self._e_level if _RANK[suit] > _RANK[self._e_suit] else self._e_level + 1

        um_bid = f'{_lvl(unbid_major)}{um_sym}' if unbid_major else '—'
        mn_bid = f'{_lvl(unbid_minor)}{mn_sym}' if unbid_minor else '—'
        ns_bid = f'{_lvl(self._n_suit)}{_suit_sym(self._n_suit)}'
        nt_bid = f'{self._e_level}NT'

        rows = [
            (um_bid,  f'3+ קלפי {um_sym}'),
            (nt_bid,  f'12+ נק׳, עוצר ב{es}'),
            (mn_bid,  f'4+ קלפי {mn_sym}'),
            (ns_bid,  f'חזרה ל{_suit_sym(self._n_suit)}'),
        ]
        self.app.set_instruction_table(
            f'N פתח {self._n_bid}, E הכריז {self._e_bid}, S הכריז X.\n'
            f'יש לך {h} נק׳. מה תכריז?',
            rows
        )

    def _on_phase2(self, bid):
        correct = self._correct
        h = hcp(self.hands['N'])
        d = distribution(self.hands['N'])

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self.app.auction_widget.add_bid('Pass')   # E
            self.app.auction_widget.add_bid('Pass')   # S
            self.app.auction_widget.add_bid('Pass')   # W
            self._finish(f'נכון. {bid}\n{self._expl}', ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')   # E
                self.app.auction_widget.add_bid('Pass')   # S
                self.app.auction_widget.add_bid('Pass')   # W
                self._finish(msg_chose_wrong_why(bid, correct, self._expl), ok=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(f'{self._expl}\nנסה שנית.', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')   # E
                self.app.auction_widget.add_bid('Pass')   # S
                self.app.auction_widget.add_bid('Pass')   # W
                self._finish(
                    msg_chose_wrong_why(bid, correct, self._expl),
                    ok=False, correct_answer=correct)

    # ── ניתוב ──────────────────────────────────────────────────────────────

    def on_student_bid(self, bid):
        if self._handle_close(bid):
            return
        if self._phase == 1:
            self._on_phase1(bid)
        else:
            self._on_phase2(bid)

    def _finish(self, message, ok, correct_answer=''):
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.show_all_hands()
        self.app.set_feedback(message, ok=ok, correct_answer=correct_answer)
        self.app.show_new_deal_button()
