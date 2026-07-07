import random
import threading
from lessons.base import BaseLesson
from engine.deal_constraints import deal_slam_major
from engine.scoring import hcp, key_cards, rkcb_response, distribution
from engine.cards import SUIT_SYMBOLS
from utils.messages import msg_slam_correct, msg_slam_stop, msg_slam_wrong, msg_slam_possible

_S = SUIT_SYMBOLS

_SUIT_RANK = {'♣': 0, '♦': 1, '♥': 2, '♠': 3, 'NT': 4}

def _bid_rank(bid):
    if not bid or bid in ('Pass', 'X', 'XX'):
        return -1
    return int(bid[0]) * 5 + _SUIT_RANK[bid[1:]]

_BW_EXPLAIN = {
    '5♣': '0 או 3 אסים',
    '5♦': '1 או 4 אסים',
    '5♥': '2 אסים, ללא Q שליט',
    '5♠': '2 אסים + Q שליט',
}


class LessonSlamSuit(BaseLesson):
    """שיעור 9: סלם בצבע — 1♣ פתיחה, קפיצה=18+, תמיכה מראה חוזק"""

    TITLE = 'שיעור 9. סלם בצבע'

    def start(self):
        if self._replaying:
            self._replaying = False
            self._setup_ui()
            return
        self.app.bidding_box.disable()
        self.app.set_instruction('טוען יד...')
        def _deal():
            for _ in range(5):
                try:
                    self._trump = random.choice(['H', 'S', 'H', 'S'])
                    self.hands = deal_slam_major(self._trump)
                    self._opening = self._choose_opening()
                    self.app.after(0, self._setup_ui)
                    return
                except RuntimeError:
                    continue
            self.app.after(0, lambda: (
                self.app.bidding_box.enable(),
                self.app.set_instruction('שגיאה בחלוקה. נסה שנית.')
            ))
        threading.Thread(target=_deal, daemon=True).start()

    def _setup_ui(self):
        self._trump_sym = _S[self._trump]
        self._stage = 'zero_free'
        self._zero_path = None
        self._tries = 0
        self._hn = hcp(self.hands['N'])
        self._hs = hcp(self.hands['S'])
        self._n_kc = key_cards(self.hands['N'], self._trump)
        self._s_kc = key_cards(self.hands['S'], self._trump)
        self._n_response, _, _ = rkcb_response(self.hands['N'], self._trump)
        self._shortage = self._calc_shortage()
        self._game_bid = f'4{self._trump_sym}'

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')

        self.app.auction_widget.add_bid(self._opening)
        self.app.auction_widget.add_bid('Pass')  # E

        title, options = self._opening_options()
        self.app.set_instruction_table(title, options)
        self.app.bidding_box.enable()
        self.app.bidding_box.set_last_bid(self._opening, no_pass=True)

    def _choose_opening(self):
        return random.choice(['1♣', '1♦'])

    def _opening_options(self):
        t = self._trump_sym
        op = self._opening
        title = 'מה תכריז?'
        if op == '1♥':
            # trump=♠ — S מכריז 1♠ ישירות
            return title, [(f'1{t}', f'5+ {t} — מראה שליט')]
        other = '1♥/1♠' if op == '1♦' else '1♦/1♥/1♠'
        return title, [
            (f'1{t}', f'5+ {t} — מראה שליט ישירות'),
            (other, '4+ בסדרה — ללא 5-קלף מיגור'),
        ]

    # ── ניתוב ─────────────────────────────────────────────────────────────

    def on_student_bid(self, bid):
        if self._stage == 'zero_free':
            self._handle_zero_free(bid)
        elif self._stage == 'zero_raise':
            self._handle_zero_raise(bid)
        elif self._stage == 'rkcb_s':
            self._handle_rkcb_s(bid)
        elif self._stage == 'first':
            self._handle_first(bid)
        elif self._stage == 'second':
            self._handle_second(bid)

    # ── שלב 0a: הכרזה חופשית ──────────────────────────────────────────────

    def _handle_zero_free(self, bid):
        t = self._trump_sym

        if not bid.endswith(t) and bid[0] not in ('1', 'P'):
            self._tries += 1
            if self._tries < 2:
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                disp = '1' + t
                self._finish(f'יש לך {self._hs} נקודות\nההכרזה הנכונה\n{disp}', ok=False)
            return

        self.app.auction_widget.add_bid(bid)

        if bid.endswith(t):
            # S הראה שליט ישירות — N מרים לפי חוזק
            self._zero_path = 'direct'
            n_rebid = self._n_raise(bid)
            self._n_rebid_lvl = int(n_rebid[0])
            self.app.auction_widget.add_bid('Pass')  # W
            self.app.auction_widget.add_bid(n_rebid)
            self.app.auction_widget.add_bid('Pass')  # E
            self._tries = 0
            self._setup_first_stage(n_rebid)
        else:
            # S הכריז סדרה אחרת — N מציג שליט: מינימום (12-17) או קפיצה (18+)
            n_trump, jumped = self._n_introduce_trump(bid)
            if jumped is None:
                # N לא יכול לכריז שליט ברמה 2 ללא רוורס — מכריז 1NT
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid(n_trump)  # 1NT
                self.app.auction_widget.add_bid('Pass')
                self._finish(
                    f'N אינו יכול להכריז {t} ללא רוורס (18+).\n'
                    f'N הכריז 1NT. קח יד חדשה.',
                    ok=True)
                return
            self._zero_path = 'n_jumped' if jumped else 'n_min'
            self._n_rebid_lvl = int(n_trump[0])
            self.app.auction_widget.add_bid('Pass')  # W
            self.app.auction_widget.add_bid(n_trump)
            self.app.auction_widget.add_bid('Pass')  # E
            self._tries = 0

            if jumped:
                # N קפץ = 18+ — S מחליט
                self._setup_first_stage(n_trump)
            else:
                # N מינימום — S מראה רמת תמיכה
                self._stage = 'zero_raise'
                dp = self._dist_points()
                hs_adj = self._hs + dp
                if hs_adj >= 16:
                    raise_options = [
                        (f'2{t}', '6-9 נק׳'),
                        (f'3{t}', '10-12 נק׳'),
                        (f'4{t}', '13-15 נק׳'),
                        ('4NT', '16+ נק׳ — שאל מפתחות'),
                    ]
                else:
                    raise_options = [
                        (f'2{t}', '6-9 נק׳'),
                        (f'3{t}', '10-12 נק׳'),
                        (f'4{t}', '13+ נק׳'),
                    ]
                self.app.set_instruction_table(
                    f'N הכריז {n_trump} (12-17 נק׳). הראה רמת תמיכה ב-{t}.',
                    raise_options
                )
                self.app.bidding_box.set_last_bid(n_trump, no_pass=True)

    def _n_raise(self, s_bid):
        """N מרים שליט S: min+1=12-14, min+2=15-17, 4M=18+."""
        t = self._trump_sym
        hn = self._hn
        min_lvl = int(s_bid[0]) + 1
        if min_lvl >= 4 or hn >= 18:
            return f'4{t}'
        if hn >= 15:
            return f'{min(min_lvl + 1, 3)}{t}'
        return f'{min_lvl}{t}'

    def _n_introduce_trump(self, s_bid):
        """N מציג שליט לראשונה. מחזיר (הכרזה, קפץ?)."""
        t = self._trump_sym
        hn = self._hn
        min_lvl = next(
            (lvl for lvl in range(1, 5)
             if _bid_rank(f'{lvl}{t}') > _bid_rank(s_bid)),
            4
        )
        if min_lvl >= 4:
            return f'4{t}', hn >= 18
        # רמה 2+ = רוורס = 18+ בלבד
        is_reverse = min_lvl >= 2
        if is_reverse:
            if hn >= 18:
                return f'{min_lvl}{t}', True  # רוורס = 18+
            # N אינו יכול להכריז שליט — מכריז 1NT
            return '1NT', None
        if hn >= 18:
            return f'{min(min_lvl + 1, 4)}{t}', True
        return f'{min_lvl}{t}', False

    # ── שלב 0b: S מראה רמת תמיכה (N היה מינימום) ────────────────────────

    def _handle_zero_raise(self, bid):
        t = self._trump_sym
        correct = self._calc_raise_level()

        # 4NT — מותר רק כש-hs_adj ≥ 16
        if bid == '4NT':
            if correct == '4NT':
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._do_blackwood()
            else:
                self._tries += 1
                if self._tries < 2:
                    self.app.set_feedback('נסה שוב', ok=False)
                else:
                    disp = correct
                    self.app.auction_widget.add_bid(bid, highlight=True)
                    self._finish(f'יש לך {self._hs} נקודות\nההכרזה הנכונה\n{disp}', ok=False)
            return

        if not bid.endswith(t):
            self._tries += 1
            if self._tries < 2:
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                correct = self._calc_raise_level()
                disp = correct
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(
                    f'יש לך {self._hs} נקודות\nההכרזה הנכונה\n{disp}',
                    ok=False)
            return

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self._n_auto_decide(bid, ok=True)
        else:
            self._tries += 1
            if self._tries < 2:
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                disp = correct
                self.app.auction_widget.add_bid(bid, highlight=True)
                self._finish(f'יש לך {self._hs} נקודות\nההכרזה הנכונה\n{disp}', ok=False)

    def _calc_raise_level(self):
        """רמת תמיכה נכונה לפי HCP+חלוקה של S."""
        dp = self._dist_points()
        hs_adj = self._hs + dp
        t = self._trump_sym
        if hs_adj >= 16:
            return '4NT'
        if hs_adj >= 13:
            return f'4{t}'
        if hs_adj >= 10:
            return f'3{t}'
        return f'2{t}'

    def _n_auto_decide(self, s_raise, ok):
        """N מחליט אוטומטית: 4NT לסלם או משחק."""
        dp = self._dist_points()
        combined = self._hn + self._hs + dp
        t = self._trump_sym
        prefix = ''

        self.app.auction_widget.add_bid('Pass')  # W

        if combined >= 33:
            # N שואל אסים — S עונה בעצמו
            self.app.auction_widget.add_bid('4NT')
            self.app.auction_widget.add_bid('Pass')  # E
            self._raise_prefix = prefix
            self._stage = 'rkcb_s'
            self._tries = 0
            self.app.set_instruction_table(
                f'N שאל 4NT ({combined} נק. משותפות). כמה מפתחות יש לך?',
                [
                    ('5♣', '0 או 3 מפתחות'),
                    ('5♦', '1 או 4 מפתחות'),
                    ('5♥', '2 ללא Q שליט'),
                    ('5♠', '2 + Q שליט'),
                ]
            )
            self.app.bidding_box.set_last_bid('4NT', no_pass=True)
            return
        elif combined >= 26:
            # N מגיע למשחק
            s_lvl = int(s_raise[0])
            if s_lvl < 4:
                self.app.auction_widget.add_bid(f'4{t}')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
            else:
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
            dp_str = f'+{dp}' if dp else ''
            self._finish('נכון\nאין מספיק נקודות\nעצרנו במשחק מלא', ok=ok)
        else:
            # combined < 26 — אין גם משחק
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            dp_str = f'+{dp}' if dp else ''
            self._finish('נכון\nאין מספיק נקודות\nאין משחק מלא', ok=ok)

    # ── שלב rkcb_s: S עונה לשאלת N ──────────────────────────────────────────

    def _handle_rkcb_s(self, bid):
        valid_rkcb = {'5♣', '5♦', '5♥', '5♠'}
        if bid not in valid_rkcb:
            self.app.set_feedback('הכרז מפתחות\n5♣/5♦/5♥/5♠', ok=False)
            return

        s_rkcb, _, _ = rkcb_response(self.hands['S'], self._trump)
        correct = s_rkcb
        is_correct = (bid == correct)

        if not is_correct:
            self._tries += 1
            if self._tries < 2:
                self.app.set_feedback('נסה שוב', ok=False)
                return

        self.app.auction_widget.add_bid(bid, highlight=True)
        self.app.auction_widget.add_bid('Pass')  # W

        t = self._trump_sym
        total_kc = self._n_kc + self._s_kc
        dp = self._dist_points()
        combined = self._hn + self._hs + dp
        prefix = getattr(self, '_raise_prefix', '')
        wrong_note = '' if is_correct else f'יש לך {self._s_kc} מפתחות\nההכרזה הנכונה\n{correct}\n'

        if total_kc >= 4 and combined >= 33:
            contract6 = f'6{t}'
            self.app.auction_widget.add_bid(contract6)
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self._finish(
                f'{prefix}{wrong_note}{msg_slam_correct(contract6, total_kc, combined)}',
                ok=is_correct)
        else:
            game5 = f'5{t}'
            stop = game5 if _bid_rank(game5) > _bid_rank(bid) else 'Pass'
            stop_contract = stop if stop != 'Pass' else bid
            if stop != 'Pass':
                self.app.auction_widget.add_bid(stop)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
            else:
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
            self._finish(
                f'{prefix}{wrong_note}{msg_slam_stop(stop_contract, total_kc, combined)}',
                ok=is_correct)

    # ── הגדרת שלב 1 (S מחליט) ─────────────────────────────────────────────

    def _setup_first_stage(self, n_rebid):
        t = self._trump_sym
        lvl = int(n_rebid[0])
        self._n_rebid_lvl = lvl

        if lvl >= 4:
            self._game_bid = 'Pass'
            game_desc = 'N הגיע למשחק. עצור'
            n_strength = '18+ נק׳'
        elif self._zero_path == 'n_jumped':
            game_desc = 'פחות מ-33 נק׳ משותפות. משחק'
            n_strength = '18+ נק׳'
        elif lvl == 3:
            game_desc = 'פחות מ-33 נק׳ משותפות. משחק'
            n_strength = '15-17 נק׳'
        else:
            # N מינימום 12-14: S מחליט Pass/game לפי כוחו
            n_strength = '12-14 נק׳'
            dp = self._dist_points()
            hs_adj = self._hs + dp
            self._stage = 'first'
            self.app.set_instruction_table(
                f'N הכריז {n_rebid} ({n_strength}). מה תכריז?',
                [
                    (f'4{t}', '14+ נק׳. יש משחק'),
                    ('Pass', 'פחות מ-14 נק׳. אין משחק'),
                ]
            )
            self.app.bidding_box.set_last_bid(n_rebid, no_pass=False)
            return

        self._stage = 'first'
        self.app.set_instruction_table(
            f'N הכריז {n_rebid} ({n_strength}). מה תכריז?',
            [
                (self._game_bid, game_desc),
                ('4NT', '33+ נק׳ משותפות. שאל אסים'),
            ]
        )
        self.app.bidding_box.set_last_bid(n_rebid, no_pass=lvl < 4)

    # ── שלב 1: S מחליט ────────────────────────────────────────────────────

    def _handle_first(self, bid):
        correct = self._calc_first()
        game_bid = self._game_bid
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            if correct != '4NT':
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                dp = self._dist_points()
                total = self._hs + self._hn + dp
                t = self._trump_sym
                if correct == 'Pass':
                    disp = f'{self._n_rebid_lvl}{t}'
                    self._finish(
                        f'נכון\nיש {total} נקודות\nאין מספיק לסלם\nההכרזה הנכונה\n{disp}',
                        ok=True)
                else:
                    contract = f'4{t}' if game_bid == 'Pass' else game_bid
                    self._finish(
                        f'נכון\nיש {total} נקודות\nאין מספיק לסלם\nההכרזה הנכונה\n{contract}',
                        ok=True)
            else:
                self._do_blackwood()
        else:
            self._tries += 1
            if self._tries < 2:
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                if bid == '4NT':
                    disp = correct
                    self._finish(f'יש לך {self._hs} נקודות\nההכרזה הנכונה\n{disp}', ok=False)
                else:
                    self.app.auction_widget.add_bid('Pass')
                    self.app.auction_widget.add_bid('Pass')
                    self.app.auction_widget.add_bid('Pass')
                    if correct == '4NT':
                        self._finish(
                            f'יש לך {self._hs} נקודות\nיש סלם\nההכרזה הנכונה\n4NT',
                            ok=False)
                    else:
                        disp = correct
                        self._finish(f'יש לך {self._hs} נקודות\nההכרזה הנכונה\n{disp}', ok=False)

    def _calc_first(self):
        lvl = self._n_rebid_lvl
        t = self._trump_sym
        dp = self._dist_points()
        hs_adj = self._hs + dp
        if lvl >= 4:
            return '4NT' if hs_adj + self._hn >= 33 else self._game_bid
        if self._zero_path == 'n_jumped':
            n_min = 18
        elif lvl == 3:
            n_min = self._hn
        else:
            # N מינימום 12-14: S מחליט game/pass
            return f'4{t}' if hs_adj >= 14 else 'Pass'
        if hs_adj + n_min >= 33:
            return '4NT'
        return self._game_bid

    # ── utils ─────────────────────────────────────────────────────────────

    def _calc_shortage(self):
        d = distribution(self.hands['S'])
        for suit in ['S', 'H', 'D', 'C']:
            if suit != self._trump and d[suit] <= 1:
                return suit
        return None

    def _dist_points(self):
        dp = 0
        if self._shortage is not None:
            d = distribution(self.hands['S'])
            if d[self._shortage] == 0:
                dp = 3  # ווייד — תמיד +3
            else:
                # סינגלטון — רק אם הקלף אינו תמונה
                singleton_card = next(
                    (c for c in self.hands['S'] if c[1] == self._shortage), None)
                if singleton_card and singleton_card[0] not in ('A', 'K', 'Q', 'J'):
                    dp = 2
        dp += self._trump_bonus()
        return dp

    def _trump_bonus(self):
        """תוספת +1 כש-9+ קלפי שליט משותפים."""
        from engine.scoring import suit_len
        combined_trump = (suit_len(self.hands['S'], self._trump) +
                          suit_len(self.hands['N'], self._trump))
        return 1 if combined_trump >= 9 else 0

    # ── בלאקווד (S שאל 4NT) ───────────────────────────────────────────────

    def _do_blackwood(self):
        response = self._n_response
        self.app.auction_widget.add_bid('Pass')
        self.app.auction_widget.add_bid(response)
        self.app.auction_widget.add_bid('Pass')

        self._stage = 'second'
        self._tries = 0
        t = self._trump_sym
        total = self._n_kc + self._s_kc
        explain = _BW_EXPLAIN[response]

        game5 = f'5{t}'
        self._stop_bid = game5 if _bid_rank(game5) > _bid_rank(response) else 'Pass'

        dp = self._dist_points()
        combined = self._hn + self._hs + dp
        dist_note = f' (+{dp} חלוקה)' if dp else ''
        self.app.set_instruction_table(
            f'מחשב ענה {response} = {explain}.\n'
            f'יש לך {self._s_kc} אסים. סה״כ {total} מ-5. נק משותפות: {combined}{dist_note}.',
            [
                (f'6{t}',         '4+ מפתחות + 33 נק. סלם'),
                (self._stop_bid,  'פחות מ-4 מפתחות / פחות מ-33. עוצרים'),
            ]
        )
        self.app.bidding_box.set_last_bid(response)

    # ── שלב 2 ─────────────────────────────────────────────────────────────

    def _handle_second(self, bid):
        correct = self._calc_second()
        t = self._trump_sym
        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            total = self._n_kc + self._s_kc
            combined = self._hn + self._hs + self._dist_points()
            contract = self._n_response if bid == 'Pass' else bid
            if bid.startswith('6'):
                self._finish(msg_slam_correct(contract, total, combined), ok=True)
            else:
                self._finish(msg_slam_stop(contract, total, combined), ok=True)
        else:
            self._tries += 1
            if self._tries < 2:
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                total = self._n_kc + self._s_kc
                combined = self._hn + self._hs + self._dist_points()
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(msg_slam_wrong(bid, correct, total, combined), ok=False)

    def _calc_second(self):
        total = self._n_kc + self._s_kc
        combined = self._hn + self._hs + self._dist_points()
        return f'6{self._trump_sym}' if total >= 4 and combined >= 33 else self._stop_bid

    # ── סיום ──────────────────────────────────────────────────────────────

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.show_all_hands()
        self.app.set_feedback(message, ok=ok, correct_answer=correct_answer)
        self.app.show_new_deal_button()
