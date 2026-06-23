from lessons.base import BaseLesson
from engine.deal_constraints import deal_takeout_double_phase1, deal_takeout_double_phase2
from engine.takeout_double import can_double, respond_to_double, doubler_rebid, respond_to_cue, suit_of
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS
from engine.opening import opening_bid as _opening_bid
from utils.messages import msg_retry, msg_chose_wrong, msg_chose_wrong_why

_S = SUIT_SYMBOLS
_SYM_MAP = {'♣': 'C', '♦': 'D', '♥': 'H', '♠': 'S'}


def _bid_suit(bid):
    for ch, s in _SYM_MAP.items():
        if ch in bid:
            return s
    return None


def _suit_sym(suit):
    return next((ch for ch, s in _SYM_MAP.items() if s == suit), suit)


class LessonTakeoutDouble(BaseLesson):
    TITLE = 'שיעור 14. דבל להוצאה'

    def start(self):
        if not self._replaying:
            self._phase = getattr(self, '_next_phase', 1)
            self._next_phase = 2 if self._phase == 1 else 1

            if self._phase == 1:
                self.hands = deal_takeout_double_phase1()
                w_bid, _ = _opening_bid(self.hands['W'])
                self._w_bid  = w_bid
                self._w_suit = _bid_suit(w_bid)
                self._correct, self._expl = respond_to_double(
                    self.hands['S'], self._w_suit, opp_level=1)
            else:
                self.hands = deal_takeout_double_phase2()
                e_bid, _ = _opening_bid(self.hands['E'])
                self._e_bid  = e_bid
                self._e_suit = _bid_suit(e_bid)
                self._correct = 'X' if can_double(
                    self.hands['S'], self._e_suit, level=1) else 'Pass'

        self._replaying = False
        self._tries     = 0

        if self._phase == 1:
            self._start_phase1()
        else:
            self._start_phase2()

    # ── שלב 1: S עונה לדבל של N ────────────────────────────────────────────

    def _start_phase1(self):
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('W')
        self.app.auction_widget.add_bid(self._w_bid)
        self.app.auction_widget.add_bid('X')
        self.app.auction_widget.add_bid('Pass')
        self.app.bidding_box.set_last_bid(self._w_bid)
        self._p1_stage = 'response'

        from engine.takeout_double import best_response_suit as _brs
        h        = hcp(self.hands['S'])
        best     = _brs(self.hands['S'], self._w_suit)
        is_minor = best in ('C', 'D')
        if is_minor:
            rows = [
                ('ברמה נמוכה', '0–10 נק׳ (מינור)'),
                ('קפיצה',      '11–12 נק׳ (מינור)'),
                ('קיו ביט',    '13+ נק׳ (מינור)'),
            ]
        else:
            rows = [
                ('ברמה נמוכה', '0–8 נק׳'),
                ('קפיצה',      '9–12 נק׳'),
                ('קיו ביט',    '13+ נק׳'),
            ]
        self.app.set_instruction_table(
            f'W פתח {self._w_bid}, שותף הכריז X.\nיש לך {h} נק׳. מה תכריז?',
            rows
        )

    def _on_phase1(self, bid):
        if self._p1_stage == 'response':
            self._on_phase1_response(bid)
        else:
            self._on_phase1_cue(bid)

    def _on_phase1_response(self, bid):
        correct = self._correct
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            h = hcp(self.hands['S'])
            if h >= 13:
                self._enter_cue_dialogue(bid)
            else:
                hn = hcp(self.hands['N'])
                s_suit = _bid_suit(bid)
                is_minor = s_suit in ('C', 'D')
                need = 28 if is_minor else 25
                if s_suit and s_suit not in (self._w_suit,) and hn + h >= need:
                    lvl  = 4 if s_suit in ('H', 'S') else 5
                    game = f'{lvl}{_S[s_suit]}'
                    minor_note = f' (מינורים ♣♦. צריך {need} נק׳)' if is_minor else ''
                    self.app.auction_widget.add_bid('Pass')
                    self.app.auction_widget.add_bid(game)
                    self.app.auction_widget.add_bid('Pass')
                    self.app.auction_widget.add_bid('Pass')
                    self.app.auction_widget.add_bid('Pass')
                    self._finish(
                        f'נכון. {bid}\n{self._expl}\nN עם {hn} נק׳. מעלה ל-{game}{minor_note}',
                        ok=True)
                else:
                    self.app.auction_widget.add_bid('Pass')
                    self.app.auction_widget.add_bid('Pass')
                    self.app.auction_widget.add_bid('Pass')
                    self._finish(
                        f'נכון. {self._w_bid}. X. {bid}\n{self._expl}',
                        ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(msg_chose_wrong_why(bid, correct, self._expl), ok=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                h = hcp(self.hands['S'])
                hint = (f'{h} נק׳. הכרז ברמה הנמוכה' if h <= 8
                        else f'{h} נק׳. קפוץ רמה' if h <= 12
                        else f'{h} נק׳. הכרז קיו ביט (צבע יריב)')
                self.app.set_feedback(f'{hint}\nנסה שנית.', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(
                    msg_chose_wrong_why(bid, correct, self._expl),
                    ok=False, correct_answer=correct)

    def _enter_cue_dialogue(self, cue_bid):
        """N מכריז סדרה אחרי הקיו ביט. S יבחר חוזה."""
        self._p1_stage = 'cue_dialogue'
        self._tries    = 0

        n_bid, n_expl = doubler_rebid(self.hands['N'], self._w_suit)
        self._n_rebid = n_bid
        n_suit = _bid_suit(n_bid)

        if n_suit:
            self._cue_correct, self._cue_expl = respond_to_cue(
                self.hands['S'], n_suit, opp_suit=self._w_suit,
                n_hand=self.hands['N'])
        else:
            self._cue_correct, self._cue_expl = '3NT', 'N הכריז NT. 3NT'

        self.app.auction_widget.add_bid('Pass')
        self.app.auction_widget.add_bid(n_bid)
        self.app.auction_widget.add_bid('Pass')
        self.app.bidding_box.set_last_bid(n_bid)   # נועל הכרזות מתחת לרמת N

        d     = distribution(self.hands['S'])
        n_sym = _suit_sym(n_suit) if n_suit else 'NT'
        n_len = d.get(n_suit, 0) if n_suit else 0
        self.app.set_instruction(
            f'N הכריז {n_bid}. {n_expl}.\n'
            f'יש לך {n_len} קלפי {n_sym}. מה תכריז?'
        )

    def _on_phase1_cue(self, bid):
        correct = self._cue_correct
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            # אם S הראה מיגור ב-3 (3♥/3♠). N סוגר ל-4M אוטומטית
            s_suit = _bid_suit(bid)
            if bid[0] == '3' and s_suit in ('H', 'S'):
                game = f'4{_suit_sym(s_suit)}'
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid(game)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(f'נכון. {bid}\n{self._cue_expl}\nN סוגר ל-{game}', ok=True)
            else:
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(f'נכון. {bid}\n{self._cue_expl}', ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(f'בחרת {bid}.\n{self._cue_expl}\nהנכון: {correct}.', ok=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                self.app.set_feedback(f'נסה שוב. {self._cue_expl}', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(
                    f'בחרת {bid}. הנכון: {correct}.\n{self._cue_expl}',
                    ok=False, correct_answer=correct)

    # ── שלב 2: S מחליט האם לכריז X כנגד E ────────────────────────────────

    def _start_phase2(self):
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('W')
        self.app.auction_widget.add_bid('Pass')
        self.app.auction_widget.add_bid('Pass')
        self.app.auction_widget.add_bid(self._e_bid)
        self.app.bidding_box.set_last_bid(self._e_bid)

        h  = hcp(self.hands['S'])
        es = _suit_sym(self._e_suit)
        self.app.set_instruction_table(
            f'E פתח {self._e_bid}.\nיש לך {h} נק׳. האם תכריז X?',
            [
                ('12–16 נק׳',       'תנאי נקודות'),
                ('3+ בכל צבע',     'חוץ מצבע יריב'),
                (f'מקס׳ 3 ב-{es}', 'קוצר בצבע יריב'),
            ]
        )

    def _on_phase2(self, bid):
        correct = self._correct
        h = hcp(self.hands['S'])
        d = distribution(self.hands['S'])

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            if correct == 'X':
                ec  = d.get(self._e_suit, 0)
                msg = f'נכון. X.\n{h} נק׳, {ec} קלפים בצבע יריב. עומד בתנאים.'
            else:
                msg = f'נכון. פס.\n{self._no_double_reason(h, d)}'
            self._finish(msg, ok=True)
        else:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                reason = (f'{h} נק׳. עומד בתנאים.'
                          if correct == 'X' else self._no_double_reason(h, d))
                self._finish(f'בחרת {bid}.\n{reason}\nהנכון: {correct}.', ok=False)
                return
            self._tries += 1
            if self._tries == 1:
                self._last_wrong_bid = bid
                hint = (f'יש לך {h} נק׳ ותבנית מתאימה. כריז X.'
                        if correct == 'X' else self._no_double_reason(h, d))
                self.app.set_feedback(f'{hint}\nנסה שנית.', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                reason = (f'{h} נק׳. עומד בתנאים.'
                          if correct == 'X' else self._no_double_reason(h, d))
                self._finish(
                    f'בחרת {bid}. הנכון: {correct}.\n{reason}',
                    ok=False, correct_answer=correct)

    def _no_double_reason(self, h, d):
        if not (12 <= h <= 16):
            return f'{h} נק׳. לא בטווח 12–16.'
        ec = d.get(self._e_suit, 0)
        if ec > 3:
            es = _suit_sym(self._e_suit)
            return f'{ec} קלפים ב-{es}. יותר מדי בצבע יריב.'
        for suit in ['S', 'H', 'D', 'C']:
            if suit != self._e_suit and d[suit] < 3:
                return f'רק {d[suit]} קלפים ב-{_S[suit]}. חסרים 3.'
        return 'לא עומד בתנאים.'

    # ── ניתוב ──────────────────────────────────────────────────────────────

    def on_student_bid(self, bid):
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
