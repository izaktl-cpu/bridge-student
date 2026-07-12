from lessons.base import BaseLesson
from engine.deal_constraints import deal_robot_opens_2c
from engine.response import respond_2c, respond_2c_second, respond_2c_third
from engine.rebid import opener_rebid, opener_bid_2c_round3
from engine.scoring import hcp, distribution, key_cards, rkcb_response, bw_response
from engine.cards import SUIT_SYMBOLS, card_rank
from utils.messages import msg_suboptimal

_S = SUIT_SYMBOLS
_GAME = {'3NT', '4♥', '4♠', '5♣', '5♦', '6NT', '6♥', '6♠', '6♣', '6♦',
         '7NT', '7♥', '7♠', '7♣', '7♦'}

_BW_EXPLAIN_2C = {
    '5♣': '0 או 3 אסים',
    '5♦': '1 או 4 אסים',
    '5♥': '2 אסים, ללא Q שליט',
    '5♠': '2 אסים + Q שליט',
    '5NT': '5 מפתחות',
}


def _is_final(bid):
    return bid in _GAME


class LessonRobotOpens2C(BaseLesson):
    """מחשב (N) פותח 2♣ חזקה, תלמיד (S) עונה. דו-שיח עד לחוזה"""

    _deal_count = 0
    _opener_idx = 0
    _FEEDBACK_OPENERS = ['כל הכבוד', 'נכון', 'מעולה']

    def _next_opener(self):
        cls = LessonRobotOpens2C
        word = cls._FEEDBACK_OPENERS[cls._opener_idx % len(cls._FEEDBACK_OPENERS)]
        cls._opener_idx += 1
        return word

    def _correct_message(self, final, extra_line=''):
        lines = [self._next_opener()]
        if extra_line:
            lines.append(extra_line)
        lines += ['ההכרזה הנכונה', final]
        return '\n'.join(lines)

    def _wrong_message(self, correct, extra_line=''):
        lines = []
        if extra_line:
            lines.append(extra_line)
        lines += ['ההכרזה הנכונה', correct]
        return '\n'.join(lines)

    def _table(self, header, rows):
        """שומר את שורות הטבלה (לתצוגה בסיום) ומציג את הכותרת."""
        self._panel_rows = rows
        self.app.set_instruction_table(header, rows)

    def start(self):
        if not self._replaying:
            LessonRobotOpens2C._deal_count += 1
            self.hands = deal_robot_opens_2c()
        self._replaying = False
        self._stage    = 'respond'
        self._tries    = 0
        self._round    = 1
        self._history_n = []
        self._history_s = []
        self._all_bids  = ['2♣', 'Pass']
        self._awaiting_close = False

        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid('2♣')
        self.app.auction_widget.add_bid('Pass')
        self.app.bidding_box.set_last_bid('2♣')

        self._panel_rows = [
            ('2♦',  'ממתין ללא תגובה חיובית'),
            ('2♥',  '8+ נקודות 5 קלפי ♥'),
            ('2♠',  '8+ נקודות 5 קלפי ♠'),
            ('2NT', '8+ נקודות יד מאוזנת'),
            ('3♣',  '7+ נקודות 5 קלפי ♣'),
            ('3♦',  '7+ נקודות 5 קלפי ♦'),
        ]
        if LessonRobotOpens2C._deal_count <= 3:
            self._table('מה תכריז', self._panel_rows)

    # ── ניתוב ──────────────────────────────────────────────────────────────

    def on_student_bid(self, bid):
        if self._handle_close(bid): return
        if self._stage in ('respond', 'continue'):
            self._handle_student_bid(bid)
        elif self._stage == 'gerber':
            self._handle_gerber(bid)
        elif self._stage == 'gerber_south':
            self._handle_gerber_south(bid)
        elif self._stage == 'blackwood':
            self._handle_blackwood(bid)

    # ── לוגיקה מרכזית ─────────────────────────────────────────────────────

    def _handle_student_bid(self, bid):
        correct, why = self._correct_bid()
        wrong_note = ''

        if bid != correct:
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                last = self._history_n[-1] if self._history_n else '2♣'
                self.app.bidding_box.reset()
                self.app.bidding_box.set_last_bid(last)
                self.app.set_feedback('נסה שוב', ok=False)
                return
            # טעות שנייה — מציגים הודעה ואת ההכרזה הנכונה, מסיימים
            self.app.auction_widget.add_bid(bid, highlight=True)
            extra = f'יש {hcp(self.hands["S"])} נקודות'
            self._finish(self._wrong_message(correct, extra_line=extra), ok=False)
            return

        # מקבל את ההכרזה (נכונה)
        self.app.auction_widget.add_bid(bid, highlight=True)
        self.app.auction_widget.add_bid('Pass')
        self._history_s.append(bid)
        self._all_bids += [bid, 'Pass']
        self._tries = 0

        # 3NT אחרי השלמת טרנספר (שלב 3). N בוחר 4M אם יש 3+ קלפי שליט
        if bid == '3NT' and self._round == 3 and len(self._history_s) >= 2:
            s_transfer = self._history_s[1]
            trump_suit = 'H' if s_transfer == '3♦' else ('S' if s_transfer == '3♥' else None)
            if trump_suit:
                trump_sym  = '♥' if trump_suit == 'H' else '♠'
                n_trump    = distribution(self.hands['N'])[trump_suit]
                ok         = not wrong_note
                extra = f'יש {hcp(self.hands["S"])} נקודות'
                msg = self._correct_message(correct, extra_line=extra) if ok else self._wrong_message(correct, extra_line=extra)
                if n_trump >= 3:
                    n_bid = f'4{trump_sym}'
                    self.app.auction_widget.add_bid(n_bid)   # N מתקן
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._start_closing(msg, ok=ok)
                else:
                    self.app.auction_widget.add_bid('Pass')  # N
                    self.app.auction_widget.add_bid('Pass')  # E
                    self._finish(msg, ok=ok)
                return

        # חוזה סופי?
        if _is_final(bid) or bid == 'Pass' or self._round >= 4:
            h = hcp(self.hands['S'])
            ok = not wrong_note
            extra = f'יש {h} נקודות'
            msg = self._correct_message(correct, extra_line=extra) if ok else self._wrong_message(correct, extra_line=extra)
            self.app.auction_widget.add_bid('Pass')  # N
            self.app.auction_widget.add_bid('Pass')  # E
            self._finish(msg, ok=ok)
            return

        # תגובה חיובית 2NT → N מציג מיגור אם יש, אחרת גרבר
        if bid == '2NT' and self._stage == 'respond':
            if wrong_note:
                self.app.set_feedback(msg_suboptimal(wrong_note.rstrip()), ok=False)
            n_bid, n_why = self._opener_bid('2NT')
            if n_bid in ('3♠', '3♥'):
                # N יש 5+ מיגור. מציג ומחכה לתגובת S
                self.app.auction_widget.add_bid(n_bid)
                self.app.auction_widget.add_bid('Pass')
                self._history_n.append(n_bid)
                self._all_bids += [n_bid, 'Pass']
                self._round += 1
                self._stage = 'continue'
                self._tries = 0
                self.app.bidding_box.reset()
                self.app.bidding_box.set_last_bid(n_bid)
                self._set_continue_instruction(n_bid)
            else:
                # N ללא 5 מיגור. תמיד 3NT — S יחליט אם לשאול גרבר (גם עם 25+)
                self.app.auction_widget.add_bid('3NT')
                self.app.auction_widget.add_bid('Pass')
                self._history_n.append('3NT')
                self._all_bids += ['3NT', 'Pass']
                self._round += 1
                self._stage = 'continue'
                self._tries = 0
                self.app.bidding_box.reset()
                self.app.bidding_box.set_last_bid('3NT')
                self._set_continue_instruction('3NT')
            return

        # Gerber 4♣. אחרי NT ישיר או אחרי Stayman שנדחה (2NT→3♦)
        _last_n = self._history_n[-1] if self._history_n else ''
        _prev_n = self._history_n[-2] if len(self._history_n) >= 2 else ''
        _is_gerber = (_last_n in ('2NT', '3NT') or
                      (_last_n in ('3♦', '3♥', '3♠') and _prev_n == '2NT'))
        if bid == '4♣' and _is_gerber:
            if wrong_note:
                self.app.set_feedback(msg_suboptimal(wrong_note.rstrip()), ok=False)
            self._do_gerber_south()
            return

        # 4NT כמותי אחרי 2NT או אחרי 2NT-positive→3NT
        _s_first = self._history_s[0] if self._history_s else ''
        _last_n2 = self._history_n[-1] if self._history_n else ''
        _quant = ((_last_n2 == '2NT' and _s_first not in ('2♥', '2♠')) or
                  (_last_n2 == '3NT' and _s_first == '2NT'))
        if bid == '4NT' and _quant:
            total_pts = hcp(self.hands['N']) + hcp(self.hands['S'])
            ok = not bool(wrong_note)
            extra = f'יש {hcp(self.hands["S"])} נקודות'
            msg = self._correct_message(correct, extra_line=extra) if ok else self._wrong_message(correct, extra_line=extra)
            if total_pts >= 33:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('6NT')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
            self._finish(msg, ok=ok)
            return

        # Blackwood 4NT. כולל אחרי תגובה חיובית 2♥/2♠
        if bid == '4NT' and self._stage == 'continue':
            if wrong_note:
                self.app.set_feedback(msg_suboptimal(wrong_note.rstrip()), ok=False)
            self._do_blackwood()
            return

        # הפותח מכריז לפי מה שקיבל (לא לפי ניקוד התלמיד)
        try:
            n_bid, n_why = self._opener_bid(bid)
        except Exception:
            n_bid, n_why = 'Pass', 'אין תגובה'
        self.app.auction_widget.add_bid(n_bid)
        self.app.auction_widget.add_bid('Pass')
        self._history_n.append(n_bid)
        self._all_bids += [n_bid, 'Pass']
        self._round += 1

        # חוזה סופי אחרי הכרזת הפותח?
        # אם S הכריז חיובי (2♥/2♠) ו-N מכריז 3NT. לא סוגרים, S ישאל Blackwood
        s_first = self._history_s[0] if self._history_s else ''
        skip_final = (s_first in ('2♥', '2♠') and n_bid == '3NT')
        if (_is_final(n_bid) or n_bid == 'Pass') and not skip_final:
            ok = not wrong_note
            extra = f'יש {hcp(self.hands["S"])} נקודות'
            msg = self._correct_message(correct, extra_line=extra) if ok else self._wrong_message(correct, extra_line=extra)
            if n_bid != 'Pass':
                self._start_closing(msg, ok=ok)
            else:
                self.app.auction_widget.add_bid('Pass')  # S
                self.app.auction_widget.add_bid('Pass')  # W
                self._finish(msg, ok=ok)
            return

        # המשך
        if wrong_note:
            self.app.set_feedback(msg_suboptimal(wrong_note.rstrip()), ok=False)
        self._stage = 'continue'
        self._tries = 0
        self.app.bidding_box.reset()
        self.app.bidding_box.set_last_bid(n_bid)
        self._set_continue_instruction(n_bid)

    def _opener_bid(self, s_bid):
        """מחשב את הכרזת הפותח לפי השלב."""
        if self._round == 1:
            return opener_rebid(self.hands['N'], '2♣', s_bid)
        # שלב 3. תגובה לסטיימן/טרנספר
        n_second = self._history_n[0]
        return opener_bid_2c_round3(self.hands['N'], n_second, s_bid)

    def _correct_bid(self):
        if self._stage == 'respond':
            return respond_2c(self.hands['S'])
        s_first = self._history_s[0] if self._history_s else ''
        if self._round == 2:
            # S כבר הראה מיגור. לא עושים טרנספר שוב
            if s_first in ('2♥', '2♠'):
                return self._correct_bid_after_positive(s_first, self._history_n[-1])
            # S הכריז 2NT חיובי ו-N ענה 3NT — S מחליט אם לשאול גרבר
            if s_first == '2NT' and self._history_n[-1] == '3NT':
                h = hcp(self.hands['S'])
                if h >= 10:
                    return '4♣', '10+ נקודות מאוזן. גרבר לחקור 6NT'
                if h == 9:
                    return '4NT', '9 נקודות. כמותי. N עוצר עם 23, 6NT עם 24'
                return 'Pass', f'יש {h} נקודות. 3NT חוזה סופי'
            return respond_2c_second(self.hands['S'], self._history_n[-1])
        # שלב 3. אחרי תגובת סטיימן/טרנספר
        s_second = self._history_s[1]
        n_third  = self._history_n[-1]
        return respond_2c_third(self.hands['S'], s_second, n_third)

    def _correct_bid_after_positive(self, s_first, n_bid):
        """S הכריז 2♥/2♠ חיובי בסיבוב 1. מיגור כבר ידוע."""
        h         = hcp(self.hands['S'])
        trump_sym = '♥' if s_first == '2♥' else '♠'
        trump_suit = 'H' if trump_sym == '♥' else 'S'
        if n_bid in ('2NT', '3NT'):
            # N דחה את המייג׳ור והכריז NT → החוזה ל-NT. שאלת אסים = 4♣ גרבר לחקור 6NT
            return '4♣', f'יש {h} נקודות. גרבר לחקור 6NT'
        if n_bid == f'4{trump_sym}':
            return 'Pass', 'חוזה סופי'
        if n_bid == f'3{trump_sym}':
            if h >= 8:
                return '4NT', f'יש {h} נקודות, תמיכה. Blackwood לחקור 6{trump_sym}'
            return f'4{trump_sym}', f'תמיכה. משחק מלא ב-{trump_sym}'
        return f'4{trump_sym}', f'ממשיכים למשחק מלא'

    # ── הוראות ─────────────────────────────────────────────────────────────

    def _set_continue_instruction(self, n_bid):
        h = hcp(self.hands['S'])
        d = distribution(self.hands['S'])

        if n_bid in ('2NT', '3NT'):
            s_first = self._history_s[0] if self._history_s else ''
            if s_first in ('2♥', '2♠'):
                trump_sym = '♥' if s_first == '2♥' else '♠'
                self._table(
                    'מה תכריז',
                    [
                        ('4♣', '8+ נקודות גרבר חוקר 6NT'),
                        (f'4{trump_sym}', 'רק משחק מלא'),
                    ]
                )
            elif s_first == '2NT':
                # S הכריז 2NT חיובי. N מכריז 3NT ללא מיגור
                self._table(
                    'מה תכריז',
                    [
                        ('Pass', '8 נקודות לא מספיק לסלם'),
                        ('4NT', '9 נקודות כמותי N עוצר עם 23 6NT עם 24'),
                        ('4♣',  '10+ נקודות גרבר לחקור 6NT'),
                    ]
                )
            else:
                self._table(
                    'מה תכריז',
                    [
                        ('פס',  '0-3 נקודות אין עניין'),
                        ('3NT', '4-8 נקודות מאוזן משחק מלא'),
                        ('3♣',  '4+ נקודות 4+ קלפי מיגור סטיימן'),
                        ('3♦',  '0+ 5+ קלפי ♥ טרנספר ל-♥'),
                        ('3♥',  '0+ 5+ קלפי ♠ טרנספר ל-♠'),
                        ('4NT', '9 נקודות מאוזן כמותי N עוצר עם 23 6NT עם 24'),
                        ('4♣',  '10+ נקודות מאוזן גרבר'),
                    ]
                )
        elif n_bid in ('3♦', '3♥', '3♠') and self._round == 3:
            # תגובה לסטיימן או השלמת טרנספר (שלב 3)
            s_second = self._history_s[1]
            if s_second == '3♣':  # תגובה לסטיימן
                if n_bid == '3♦':
                    self.app.set_instruction('מה תכריז')
                else:
                    self.app.set_instruction('מה תכריז')
            else:  # השלמת טרנספר
                sym = n_bid[1]
                suit = {'♥': 'H', '♠': 'S'}[sym]
                trump_len = distribution(self.hands['S'])[suit]
                rows = [('3NT', f'5 קלפי {sym} מזמין הפותח יבחר {n_bid} אם יש 3+ קלפי {sym}')]
                if trump_len >= 6:
                    rows.insert(0, (f'4{sym}', f'6+ קלפי {sym} משחק מלא ישיר'))
                self._table('מה תכריז', rows)
        elif n_bid in ('2♥', '2♠', '3♣', '3♦', '3♥', '3♠') and self._round == 2:
            sym = n_bid[1]
            suit = {'♥': 'H', '♠': 'S', '♣': 'C', '♦': 'D'}[sym]
            is_major = suit in ('H', 'S')
            s_first = self._history_s[0] if self._history_s else ''
            # N תמך במיגור שS הראה חיובי. טבלה פשוטה
            if is_major and s_first in ('2♥', '2♠') and n_bid == f'3{sym}':
                rows = []
                if h >= 8:
                    rows.append(('4NT', f'8+ נקודות Blackwood לחקור 6{sym}'))
                rows.append((f'4{sym}', 'משחק מלא'))
                self._table('מה תכריז', rows)
                return
            if is_major:
                other_sym = '♠' if sym == '♥' else '♥'
                d = distribution(self.hands['S'])
                has_fit = d[suit] >= 3
                rows = []
                if h >= 8:
                    rows.append(('4NT', f'8+ נקודות Blackwood לחקור סלם'))
                if has_fit:
                    rows.append((f'4{sym}', f'3+ קלפי {sym} תמיכה משחק מלא'))
                other_suit = 'S' if sym == '♥' else 'H'
                other_len  = d.get(other_suit, 0)
                if other_len >= 5:
                    _sord = {'♣': 0, '♦': 1, '♥': 2, '♠': 3}
                    n_lvl = int(n_bid[0])
                    _2ok  = n_lvl < 2 or (n_lvl == 2 and _sord.get(other_sym, 0) > _sord.get(sym, 0))
                    level = '2' if _2ok else '3'
                    rows.append((f'{level}{other_sym}', f'{other_len} קלפי {other_sym} ללא התאמה ב-{sym}'))
                rows.append(('3♣', f'אין התאמה. 3♣ אינו מראה ♣\nהפותח יכריז 3NT'))
                self._table('מה תכריז', rows)
            else:
                # מינור. מראים מיגור אחר ב-3 או 3NT
                self._table(
                    'מה תכריז',
                    [
                        ('3♠',  '5+ קלפי ♠ מראה מיגור'),
                        ('3♥',  '5+ קלפי ♥ מראה מיגור'),
                        ('3NT', 'ללא 5 קלפי מיגור 3NT'),
                    ]
                )
        else:
            self.app.set_instruction('מה תכריז')

    # ── הסברים ─────────────────────────────────────────────────────────────

    def _explain(self, bid, correct):
        h = hcp(self.hands['S'])
        d = distribution(self.hands['S'])

        if self._stage == 'respond':
            if correct == '2♦':
                if h >= 8:
                    return (f'יש לך {h} נקודות גבוהות, אך אין 5 קלפי מיגור ואין יד מאוזנת. '
                            f'מכריזים 2♦ ממתין.')
                return f'יש לך {h} נקודות גבוהות. עם 0-7 נקודות, מכריזים 2♦. תגובת המתנה.'
            if bid == '2♦':
                suit_info = self._best_suit_str(d)
                return (f'יש לך {h} נקודות גבוהות{suit_info}. '
                        f'עם 7 נקודות ומעלה, מכריזים תגובה חיובית. {correct}.')
            return f'יש לך {h} נקודות גבוהות. ההכרזה הנכונה היא {correct}.'

        n_last = self._history_n[-1] if self._history_n else '2♣'
        if n_last == '2NT':
            if correct == 'Pass':
                return f'יש לך {h} נקודות. עם 0-3 נקודות, מכריזים פס.'
            if correct == '3♦':
                return f'יש לך 5+ קלפי ♥. מכריזים 3♦. טרנספר ל-♥ כדי שהיד החזקה תשחק.'
            if correct == '3♥':
                return f'יש לך 5+ קלפי ♠. מכריזים 3♥. טרנספר ל-♠ כדי שהיד החזקה תשחק.'
            if correct == '3♣':
                return f'יש לך 4+ קלפי מיגור. מכריזים 3♣. סטיימן לחיפוש התאמה.'
            return f'יש לך {h} נקודות. ממשיכים למשחק מלא. {correct}.'
        if n_last in ('3♦', '3♥', '3♠'):
            return f'מחשב הכריז {n_last}. ההכרזה הנכונה היא {correct}.'
        if n_last in ('2♥', '2♠'):
            sym = n_last[1]
            suit = 'H' if sym == '♥' else 'S'
            if correct == '4NT':
                return f'יש לך {h} נקודות ו-{d[suit]} קלפי {sym}. עם 8+ נקודות והתאמה. Blackwood לחקור סלם.'
            if correct.startswith('4'):
                return f'יש לך {d[suit]} קלפי {sym}. תמיכה, מכריזים משחק מלא.'
            return f'ללא התאמה ב-{sym}, מכריזים {correct}.'
        return f'יש לך {h} נקודות. ההכרזה הנכונה היא {correct}.'

    def _best_suit_str(self, d):
        for suit in ['H', 'S', 'C', 'D']:
            if d[suit] >= 5:
                return f' ו-{d[suit]} קלפי {_S[suit]}'
        return ''

    # ── Blackwood 4NT אחרי מיגור עיקרי ──────────────────────────────────────

    def _do_blackwood(self):
        _sym_to_suit = {'♥': 'H', '♠': 'S', '♣': 'C', '♦': 'D'}

        # מצא את הסדרה המוסכמת. מ-S הראשון (2♥/2♠) או מ-N האחרון
        s_first    = self._history_s[0] if self._history_s else ''
        agreed_bid = self._history_n[-1] if self._history_n else '2♣'
        if s_first in ('2♥', '2♠'):
            trump_sym  = s_first[1]
            trump_suit = _sym_to_suit[trump_sym]
            has_fit    = True
        elif len(agreed_bid) == 2 and agreed_bid[1] in _sym_to_suit:
            trump_suit = _sym_to_suit[agreed_bid[1]]
            trump_sym  = agreed_bid[1]
            has_fit    = distribution(self.hands['S']).get(trump_suit, 0) >= 2
        else:
            trump_suit = None
            trump_sym  = None
            has_fit    = False

        self._bw_fit   = has_fit
        self._bw_sym   = trump_sym
        self._bw_trump = trump_suit

        # חישוב תגובת N
        if trump_suit and has_fit:
            # RKCB. צבע מוסכם
            n_bid, n_kc, _ = rkcb_response(self.hands['N'], trump_suit)
            s_kc   = key_cards(self.hands['S'], trump_suit)
            total  = n_kc + s_kc
            rows = [
                (f'6{trump_sym}', f'4+ אסים סלם ב-{trump_sym}'),
                (f'5{trump_sym}', 'פחות מ-4 עוצרים'),
            ]
            instr = f'{total} אסים מ-5'
        else:
            # Blackwood רגיל. NT, 4 אסים
            n_bid, n_aces = bw_response(self.hands['N'])
            s_aces = sum(1 for c in self.hands['S'] if card_rank(c) == 'A')
            total  = n_aces + s_aces
            rows = [
                ('6NT', '4 אסים + 33 נקודות משותפות סלם ב-NT'),
                ('5NT', 'פחות מזה עוצרים'),
            ]
            instr = f'{total} אסים מ-4'

        self.app.auction_widget.add_bid(n_bid)
        self.app.auction_widget.add_bid('Pass')
        self._history_n.append(n_bid)
        self._all_bids += [n_bid, 'Pass']
        self._stage = 'blackwood'
        self._tries = 0

        self._table(instr, rows)
        self.app.bidding_box.reset()
        self.app.bidding_box.set_last_bid(n_bid)

    def _handle_blackwood(self, bid):
        has_fit    = getattr(self, '_bw_fit', False)
        sym        = getattr(self, '_bw_sym', None)
        trump_suit = getattr(self, '_bw_trump', None)

        if has_fit and trump_suit:
            # RKCB. אסים (5 = 4 אסים + K שליט)
            n_kc  = key_cards(self.hands['N'], trump_suit)
            s_kc  = key_cards(self.hands['S'], trump_suit)
            total = n_kc + s_kc
            total_pts = hcp(self.hands['N']) + hcp(self.hands['S'])
            # 33+ נקודות: מספיק 4 אסים; אחרת צריך 5
            needed = 4 if total_pts >= 33 else 5
            correct = f'6{sym}' if total >= needed else f'5{sym}'
            total_str = f'{total} אסים מ-5'
        else:
            # Blackwood רגיל. NT: צריך 4 אסים + 33 נקודות משותפות
            n_aces = sum(1 for c in self.hands['N'] if card_rank(c) == 'A')
            s_aces = sum(1 for c in self.hands['S'] if card_rank(c) == 'A')
            total  = n_aces + s_aces
            total_pts = hcp(self.hands['N']) + hcp(self.hands['S'])
            correct = '6NT' if (total >= 4 and total_pts >= 33) else '5NT'
            total_str = f'{total} אסים מ-4'

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self._finish(self._correct_message(bid, extra_line=f'יש לנו {total_str}'), ok=True)
        else:
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.bidding_box.reset()
                self.app.bidding_box.set_last_bid(self._history_n[-1])
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(
                    f'{self._wrong_message(correct, extra_line=f"{total_str}")}',
                    ok=False)

    # ── ג׳רבר אחרי 2NT חיובי ─────────────────────────────────────────────

    def _do_gerber(self):
        self.app.auction_widget.add_bid('4♣')    # N שואל
        self.app.auction_widget.add_bid('Pass')  # E
        self._history_n.append('4♣')
        self._all_bids += ['4♣', 'Pass']
        self._stage = 'gerber'
        self._tries = 0
        self._table(
            "כמה אסים יש לך",
            [
                ('4♦',  '0 או 4 אסים'),
                ('4♥',  '1 אס'),
                ('4♠',  '2 אסים'),
                ('4NT', '3 אסים'),
            ]
        )
        self.app.bidding_box.set_last_bid('4♣')

    def _calc_gerber_response(self):
        n = sum(1 for c in self.hands['S'] if card_rank(c) == 'A')
        return ['4♦', '4♥', '4♠', '4NT', '4♦'][n]

    def _handle_gerber(self, bid):
        correct = self._calc_gerber_response()
        s_aces = sum(1 for c in self.hands['S'] if card_rank(c) == 'A')
        n_aces = sum(1 for c in self.hands['N'] if card_rank(c) == 'A')
        total  = s_aces + n_aces

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)  # S
            self.app.auction_widget.add_bid('Pass')               # W
            if total >= 4:
                self.app.auction_widget.add_bid('6NT')   # N. סלם
                self.app.auction_widget.add_bid('Pass')  # E
                self._start_closing(
                    self._correct_message('6NT', extra_line=f'יש לנו {total} אסים מ-4'),
                    ok=True)
            else:
                self.app.auction_widget.add_bid('5NT')   # N. עצירה
                self.app.auction_widget.add_bid('Pass')  # E
                self._start_closing(
                    self._correct_message('5NT', extra_line=f'יש לנו {total} אסים מ-4'),
                    ok=True)
        else:
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)  # S
                self.app.auction_widget.add_bid('Pass')               # W
                self.app.auction_widget.add_bid('Pass')               # N
                self.app.auction_widget.add_bid('Pass')               # E
                self._finish(
                    f'{self._wrong_message(correct, extra_line=f"יש לך {s_aces} אסים")}',
                    ok=False)

    # ── ג׳רבר כשS שואל (אחרי 3NT של N) ──────────────────────────────────────

    def _do_gerber_south(self):
        n_aces = sum(1 for c in self.hands['N'] if card_rank(c) == 'A')
        replies = ['4♦', '4♥', '4♠', '4NT', '4♦']
        n_bid = replies[n_aces]
        self.app.auction_widget.add_bid(n_bid)   # N עונה
        self.app.auction_widget.add_bid('Pass')  # E
        self._history_n.append(n_bid)
        self._all_bids += [n_bid, 'Pass']
        self._stage = 'gerber_south'
        self._tries = 0
        self._gerber_n_aces = n_aces

        s_aces = sum(1 for c in self.hands['S'] if card_rank(c) == 'A')
        total  = n_aces + s_aces
        self._table(
            f'{total} אסים מ-4',
            [
                ('6NT', '4 אסים + 33 נקודות משותפות סלם'),
                ('5NT', 'פחות מזה עוצרים'),
            ]
        )
        self.app.bidding_box.reset()
        self.app.bidding_box.set_last_bid(n_bid)

    def _handle_gerber_south(self, bid):
        n_aces = self._gerber_n_aces
        s_aces = sum(1 for c in self.hands['S'] if card_rank(c) == 'A')
        total  = n_aces + s_aces
        total_pts = hcp(self.hands['N']) + hcp(self.hands['S'])
        correct = '6NT' if (total == 4 and total_pts >= 33) else '5NT'
        total_str = f'{total} אסים מ-4'

        if bid == correct:
            self.app.auction_widget.add_bid(bid, highlight=True)
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self.app.auction_widget.add_bid('Pass')
            self._finish(self._correct_message(bid, extra_line=f'יש לנו {total_str}'), ok=True)
        else:
            self._tries += 1
            if self._tries < 3:
                self._last_wrong_bid = bid
                self.app.bidding_box.reset()
                self.app.bidding_box.set_last_bid(self._history_n[-1])
                self.app.set_feedback('נסה שוב', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self.app.auction_widget.add_bid('Pass')
                self._finish(
                    f'{self._wrong_message(correct, extra_line=f"{total_str}")}',
                    ok=False)

    def _finish(self, message, ok, correct_answer=''):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        # בסוף כל יד — מציגים את טבלת האפשרויות האחרונה (נכון וגם טעות)
        rows = getattr(self, '_panel_rows', None)
        if rows:
            self.app.add_immediate_table(rows)
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
