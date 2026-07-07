import random
from lessons.base import BaseLesson
from engine.deal_constraints import deal_student_opens_minor
from engine.response import respond_minor
from engine.rebid import opener_rebid
from engine.scoring import hcp, distribution, is_balanced
from engine.cards import SUIT_SYMBOLS, SUITS
from engine.opening import opening_bid as _opening_bid

_S = SUIT_SYMBOLS

# ═══════════════════════════════════════════════════════════════════════════
#  5 ידיים קבועות לתרגול ראשוני (S בלבד. שאר האפיקים אקראיים)
# ═══════════════════════════════════════════════════════════════════════════
_FIXED_S = [
    # יד 1: 5 יהלומים. סדרה ארוכה ביותר → 1♦
    ['AS','KS','QS','5S', '9H','8H', 'TD','8D','4D','3D','2D', 'AC','4C'],
    # יד 2: 18 נק' מאוזן, 4 ספיידים, 3-3 במינורים → 1♣ (מאולץ)
    ['AS','KS','TS','8S', 'AH','KH','TH', 'TD','4D','3D', 'AC','4C','2C'],
    # יד 3: 4♥ ו-4♦. 2 רביעיות, הנמוכה = ♦ → 1♦
    ['AS','KS', '9H','8H','7H','6H', '8D','4D','3D','2D', 'AC','KC','2C'],
    # יד 4: 4♥, אין 5 מיגור, 3-3 במינורים → 1♣ (מאולץ)
    ['AS','KS','QS', '9H','8H','7H','6H', 'TD','4D','3D', 'AC','4C','2C'],
    # יד 5: 17 נק' מאוזן → 1NT (לא מינור!)
    ['AS','KS','QS','JS', '9H','8H','7H','6H', 'KD','4D','3D', 'AC','4C'],
]

# הסבר לכל יד קבועה: (כלל, למה)
_FIXED_RULES = [
    ('1♦', 'סדרה ארוכה ביותר',
     'יש לך 5 קלפי ♦. תמיד פותחים בסדרה הארוכה.'),
    ('1♣', 'מינור מאולץ (18 נק\' מאוזן)',
     'יש 18 נקודות מאוזן. חזק מדי ל-1NT (15-17).\nאין 5 קלפי מיגור, 3-3 במינורים.\nפותחים 1♣ ומתכוונים להכריז 2NT בסיבוב הבא.'),
    ('1♦', 'נמוכה מ-2 רביעיות',
     'יש לך 4♥ ו-4♦. שתי רביעיות.\nפותחים בנמוכה מביניהן. ♦ נמוכה מ-♥.'),
    ('1♣', 'מינור מאולץ (4♥, אין 5 מיגור)',
     'יש לך 4♥ אבל אין 5 קלפי מיגור לפתיחה.\n3-3 במינורים. פותחים 1♣ (הנמוך).'),
    ('1NT', 'יד מאוזנת 15-17 נקודות',
     'יש 17 נקודות מאוזן (4-4-3-2).\nזוהי פתיחת 1NT. לא מינור'),
]


def _complete_deal(s_cards):
    """מחלק את שאר הקלפים ל-N/E/W כך ש-N יש 6-12 נקודות."""
    from engine.cards import make_deck
    from engine.scoring import hcp as _hcp
    s_set = set(s_cards)
    remaining = [c for c in make_deck() if c not in s_set]
    for _ in range(5000):
        random.shuffle(remaining)
        n = remaining[:13]
        hn = _hcp(n)
        if 6 <= hn <= 12:
            return {'N': n, 'E': remaining[13:26], 'S': list(s_cards), 'W': remaining[26:]}
    # fallback. כל N סביר
    random.shuffle(remaining)
    return {'N': remaining[:13], 'E': remaining[13:26], 'S': list(s_cards), 'W': remaining[26:]}


def _opening_rule(hand):
    """מחזיר (bid, rule_name, explanation) לפי הכלל שחל."""
    h  = hcp(hand)
    d  = distribution(hand)
    bal = is_balanced(hand)

    # 1NT
    if 15 <= h <= 17 and bal:
        return ('1NT', 'יד מאוזנת 15-17 נקודות',
                f'יש {h} נקודות מאוזן. פותחים 1NT.')

    # מיגור 5+
    for suit, sym in [('S','♠'),('H','♥')]:
        if d[suit] >= 5:
            other = 'H' if suit == 'S' else 'S'
            osym  = '♥' if suit == 'S' else '♠'
            if d[other] >= 5:
                return (f'1{sym}',
                        'גבוהה מ-2 חמישיות',
                        f'יש לך 5{sym} ו-5{osym}. פותחים בגבוהה מביניהן {sym}.')
            return (f'1{sym}',
                    'סדרה ארוכה ביותר',
                    f'יש לך {d[suit]} קלפי {sym}. פותחים בסדרה הארוכה.')

    # מינורים
    bid, _ = _opening_bid(hand)             # 1♣ / 1♦
    dc, dd = d['C'], d['D']
    sym = '♣' if bid == '1♣' else '♦'
    osym = '♦' if bid == '1♣' else '♣'

    # האם יש 4+ מיגור שאי אפשר לפתוח בו?
    has_4h = d['H'] == 4
    has_4s = d['S'] == 4
    forced = (max(d['H'], d['S']) < 5) and (dc < 4 and dd < 4)

    if forced:
        msym = '♥' if has_4h else ('♠' if has_4s else '')
        if msym:
            return (bid, 'מינור מאולץ',
                    f'יש לך 4{msym} אבל אין 5 קלפי מיגור.\n'
                    f'אין 4+ קלפי מינור. פותחים {bid} עם 3 קלפים.')
        if h >= 18 and bal:
            return (bid, 'מינור מאולץ (18+ נק\')',
                    f'יש {h} נקודות מאוזן. חזק מדי ל-1NT.\n'
                    f'פותחים {bid} ומכריזים 2NT בסיבוב הבא.')
        return (bid, 'מינור מאולץ',
                f'אין 5 קלפי מיגור ואין 4+ מינור.\nפותחים {bid} עם 3 קלפים.')

    if dc == dd:
        if dc >= 5:
            return (bid, 'גבוהה מ-2 חמישיות',
                    f'יש לך {dd} קלפי ♦ ו-{dc} קלפי ♣. פותחים בגבוהה {bid}.')
        return (bid, 'נמוכה מ-2 רביעיות',
                f'יש לך {dd} קלפי ♦ ו-{dc} קלפי ♣. שוות אורך.\n'
                f'פותחים בנמוכה מביניהן {bid}.')

    # סדרה ארוכה. רק אם המינור הוא בדיוק 4 קלפים (כמו המיגור) → "שתי רביעיות"
    longer = dc if bid == '1♣' else dd
    if longer == 4 and (d['H'] == 4 or d['S'] == 4):
        maj = '♥' if d['H'] == 4 else '♠'
        return (bid, 'נמוכה מ-2 רביעיות',
                f'יש לך 4{maj} ו-4 קלפי {sym}. שתי רביעיות.\n'
                f'פותחים בנמוכה. {sym} נמוכה מ-{maj}.')
    return (bid, 'סדרה ארוכה ביותר',
            f'יש לך {longer} קלפי {sym}. הסדרה הארוכה ביותר.')


class LessonStudentOpensMinor(BaseLesson):
    """תלמיד (S) פותח מינור (או 1NT), מחשב (N) עונה. עם 5 ידיים קבועות ראשונות"""

    _deal_count = 0
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonStudentOpensMinor
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def _correct_message(self, final):
        h = hcp(self.hands['S'])
        return (f'{self._next_opener()}\n'
                f'יש לך {h} נקודות\n'
                f'ההכרזה הנכונה\n'
                f'{final}')

    def start(self):
        LessonStudentOpensMinor._deal_count += 1
        idx = LessonStudentOpensMinor._deal_count - 1

        if not self._replaying:
            if idx < len(_FIXED_S):
                self.hands = _complete_deal(_FIXED_S[idx])
                self._fixed_idx = idx
            else:
                self._fixed_idx = None
                # בחר מינור אקראי
                self._minor = random.choice(['C', 'D'])
                r = random.random()
                scenario = 'minor_partial' if r < 0.25 else 'free'
                self.hands = deal_student_opens_minor(self._minor, scenario=scenario)
        self._replaying = False
        self._stage = 'open'
        self._tries = 0

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('S')
        self.app.bidding_box.reset()
        self._set_open_instruction()

    def _set_open_instruction(self):
        s  = self.hands['S']
        h  = hcp(s)
        d  = distribution(s)
        bid, rule, expl = _opening_rule(s)

        lines = [
            f'יש לך {h} נקודות.',
            f'♠{d["S"]} ♥{d["H"]} ♦{d["D"]} ♣{d["C"]}',
        ]
        # ידיים ראשונות. מראים כלל
        if self._fixed_idx is not None or LessonStudentOpensMinor._deal_count <= 8:
            lines.append(f'כלל\n{rule}')
        self.app.set_instruction('\n'.join(lines))

    # ── שלב 1: תלמיד פותח ─────────────────────────────────────────────────

    def on_student_bid(self, bid):
        if self._stage == 'open':
            self._handle_open(bid)
        elif self._stage == 'rebid':
            self._handle_rebid(bid)

    def _handle_open(self, bid):
        s = self.hands['S']
        correct, _, _ = _opening_rule(s)

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')                # W

            # N עונה
            if correct == '1NT':
                # לידיים שפותחות 1NT. המחשב יענה לפי NT
                from engine.response import respond_1nt
                north_bid, n_why = respond_1nt(self.hands['N'])
            else:
                minor = 'C' if '♣' in correct else 'D'
                north_bid, n_why = respond_minor(self.hands['N'], minor)
                self._minor = minor

            self._north_bid = north_bid
            self._north_why = n_why
            self.app.auction_widget.add_bid(north_bid)             # N
            self.app.auction_widget.add_bid('Pass')                # E

            if north_bid in ('3NT', '4♥', '4♠', '5♣', '5♦') or correct == '1NT':
                self._finish(self._correct_message(north_bid), ok=True)
            else:
                self._stage = 'rebid'
                self._tries = 0
                self.app.bidding_box.set_last_bid(north_bid)
                self._set_rebid_instruction(north_bid)
        else:
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.bidding_box.reset()
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(self._explain_open_wrong(correct), ok=False)

    # ── שלב 2: תלמיד עושה חזרה ─────────────────────────────────────────────

    def _set_rebid_instruction(self, north_bid):
        rows = self._rebid_rows(north_bid)
        if rows:
            self.app.set_instruction_table('מה תכריז?', rows)
        else:
            h_s = hcp(self.hands['S'])
            self.app.set_instruction(
                f'מחשב ענה {north_bid}.\n{self._north_why}.\n'
                f'יש לך {h_s} נקודות.\nמה תכריז?')

    def _rebid_rows(self, north_bid):
        sym = _S.get(getattr(self, '_minor', 'C'), '♣')
        if north_bid == '1NT':
            return [
                ('פס',  '12-14 נקודות'),
                ('2NT', '15-17 נקודות'),
                ('3NT', '18+ נקודות'),
            ]
        if north_bid == f'2{sym}':
            return [
                ('פס',      '12-14 נקודות'),
                (f'3{sym}', '15-17 נקודות'),
                ('3NT',     '18+ נקודות'),
            ]
        if north_bid == f'3{sym}':
            return [
                ('פס',  '12-14 נקודות'),
                ('3NT', '15+ נקודות'),
            ]
        if north_bid == '2NT':
            return [
                ('פס',  '12-14 נקודות'),
                ('3NT', '15+ נקודות'),
            ]
        if north_bid == '1♦' and getattr(self, '_minor', '') == 'C':
            return [
                ('1NT', '12-14 נקודות, מאוזן'),
                ('2♦',  '4+ קלפי ♦, תמיכה'),
                ('2♣',  '5+ קלפי ♣'),
                ('2NT', '18-19 נקודות'),
            ]
        if north_bid in ('1♥', '1♠'):
            msym = '♥' if north_bid == '1♥' else '♠'
            msuit = 'H' if north_bid == '1♥' else 'S'
            d = distribution(self.hands['S'])
            fit = d.get(msuit, 0)
            if fit >= 4:
                return [
                    (f'2{msym}', f'12-14 נקודות, 4+ קלפי {msym}'),
                    (f'3{msym}', f'15-17 נקודות, 4+ קלפי {msym}'),
                    (f'4{msym}', f'18+ נקודות, 4+ קלפי {msym}'),
                ]
            return [
                ('1NT', '12-14 נקודות, מאוזן'),
                (f'2{sym}', f'5+ קלפי {sym}, 15+'),
                ('2NT', '18-19 נקודות'),
            ]
        return []

    def _handle_rebid(self, bid):
        opening = f'1{_S.get(getattr(self, "_minor", "C"), "♣")}'
        correct, why = opener_rebid(self.hands['S'], opening, self._north_bid)

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            final = self._north_bid if bid == 'Pass' else bid
            self._finish(self._correct_message(final), ok=True)
        else:
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                self.app.bidding_box.set_last_bid(self._north_bid)
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(self._explain_rebid_wrong(correct), ok=False)

    def _explain_rebid_wrong(self, correct):
        h = hcp(self.hands['S'])
        return f'יש לך {h} נקודות\nההכרזה הנכונה\n{correct}'

    def _explain_open_wrong(self, correct):
        h = hcp(self.hands['S'])
        return f'יש לך {h} נקודות\nההכרזה הנכונה\n{correct}'

    # ── סיום ───────────────────────────────────────────────────────────────

    def _finish(self, message, ok):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.table.show_hands(self.hands, visible=('N','E','S','W'))
        self.app.show_new_deal_button()
