import random
from lessons.base import BaseLesson
from utils.messages import msg_retry, msg_correct
from engine.deal_constraints import deal_robot_opens_minor
from engine.response import respond_minor, responder_continuation_after_minor
from engine.rebid import opener_rebid, opener_later_bid
from engine.scoring import hcp, distribution
from engine.cards import SUIT_SYMBOLS

_S = SUIT_SYMBOLS

_FINAL = {'3NT', '4♥', '4♠', '5♣', '5♦', 'Pass'}
_GAME  = {'3NT', '4♥', '4♠', '5♣', '5♦'}


def _is_final_contract(bid):
    return bid in _GAME


def _consecutive_passes(bids, n=3):
    """האם n הפסים האחרונים ברצף (כולל E/W)."""
    return len(bids) >= n and all(b == 'Pass' for b in bids[-n:])


class LessonRobotOpensMinor(BaseLesson):
    """מחשב (N) פותח מינור, תלמיד (S) עונה. עד 4 סביבים או 3 פסים"""

    _deal_count = 0

    def start(self):
        if not self._replaying:
            LessonRobotOpensMinor._deal_count += 1
            self._minor = random.choice(['C', 'D'])
            r = random.random()
            if r < 0.40:
                scenario = 'major_fit'
            elif r < 0.65:
                scenario = 'nt'
            elif r < 0.75:
                scenario = 'free'
            else:
                scenario = 'minor_partial'
            self.hands  = deal_robot_opens_minor(self._minor, scenario=scenario)
        self._replaying = False
        self._stage  = 'respond'
        self._tries  = 0
        self._round  = 1          # סביב נוכחי (1-4)
        self._history_n = []      # הכרזות N (אחרי הפתיחה)
        self._history_s = []      # הכרזות S
        self._all_bids  = []      # כל ההכרזות לפי סדר (לבדיקת 3 פסים)

        sym = _S[self._minor]
        self.app.table.show_hands(self.hands, visible=('S',))
        self.app.auction_widget.reset()
        self.app.auction_widget.set_dealer('N')
        self.app.auction_widget.add_bid(f'1{sym}')  # N
        self.app.auction_widget.add_bid('Pass')      # E

        self._all_bids.append(f'1{sym}')
        self._all_bids.append('Pass')

        self.app.bidding_box.set_last_bid(f'1{sym}')
        self._set_respond_instruction()

    # ── הוראות ────────────────────────────────────────────────────────────

    def _set_respond_instruction(self):
        sym = _S[self._minor]
        if LessonRobotOpensMinor._deal_count <= 4:
            if self._minor == 'C':
                self.app.set_instruction_table(
                    f'מחשב פתח 1{sym}.\nעדיפות ראשונה: מיגורים.\nעדיפות שנייה: NT במשחק מלא.',
                    [
                        ('פס',   '0-5 נקודות'),
                        ('1♦',   '6+ נקודות, 4+ קלפי ♦'),
                        ('1♥',   '6+ נקודות, 4+ קלפי ♥'),
                        ('1♠',   '6+ נקודות, 4+ קלפי ♠'),
                        ('1NT',  '6-10 נקודות, מאוזן'),
                        ('2♣',   '6-10 נקודות, 5+ קלפי ♣'),
                        ('2NT',  '11-12 נקודות, מאוזן'),
                        ('3♣',   '11-12 נקודות, 5+ קלפי ♣, לא מאוזן'),
                        ('3NT',  '13+ נקודות. 25+ ביחד'),
                    ]
                )
            else:
                self.app.set_instruction_table(
                    f'מחשב פתח 1{sym}.\nעדיפות ראשונה: מיגורים.\nעדיפות שנייה: NT במשחק מלא.',
                    [
                        ('פס',   '0-5 נקודות'),
                        ('1♥',   '6+ נקודות, 4+ קלפי ♥'),
                        ('1♠',   '6+ נקודות, 4+ קלפי ♠'),
                        ('1NT',  '6-10 נקודות, מאוזן'),
                        ('2♦',   '6-10 נקודות, תמיכה 5+ ♦, לא מאוזן'),
                        ('2NT',  '11-12 נקודות, מאוזן'),
                        ('3♦',   '11-12 נקודות, תמיכה 5+ ♦, הזמנה'),
                        ('2♣',   '11+ נקודות, 5+ קלפי ♣'),
                        ('3NT',  '13+ נקודות. 25+ ביחד'),
                    ]
                )

    def _set_continue_instruction(self, n_bid):
        d      = distribution(self.hands['S'])
        _map   = {'♥': 'H', '♠': 'S', '♦': 'D', '♣': 'C'}
        s_last = self._history_s[-1] if self._history_s else ''
        s_suit = next((suit for ch, suit in _map.items() if ch in s_last), None)
        s_sym  = _S[s_suit] if s_suit else ''
        s_len  = d.get(s_suit, 0) if s_suit else 0
        n_suit = next((suit for ch, suit in _map.items() if ch in n_bid), None)
        n_sym  = _S[n_suit] if n_suit else ''

        # תמיכה ב-2M (פותח חלש 12-14)
        if n_bid.startswith('2') and n_suit in ('H', 'S'):
            self.app.set_instruction_table(
                f'מחשב תמך ב-{n_bid} (12-14 נקודות). מה תכריז?',
                [
                    ('פס',      '6-10 נקודות, חלש'),
                    (f'3{n_sym}', '11-12 נקודות, הזמנה'),
                    (f'4{n_sym}', '13+ נקודות, משחק מלא'),
                ]
            )
        # הזמנה ב-3M (פותח בינוני 15-17)
        elif n_bid.startswith('3') and n_suit in ('H', 'S'):
            self.app.set_instruction_table(
                f'מחשב הזמין ב-{n_bid} (15-17 נקודות). מה תכריז?',
                [
                    ('פס',      '6-9 נקודות, דוחה הזמנה'),
                    (f'4{n_sym}', '10+ נקודות, מקבל הזמנה, משחק מלא'),
                ]
            )
        elif n_bid == '1NT' and s_suit in ('H', 'S') and s_len >= 6:
            self.app.set_instruction_table(
                f'מחשב הכריז {n_bid}. יש לך {s_len} קלפי {s_sym}. מה תכריז?',
                [
                    (f'2{s_sym}', 'עד 10 נקודות, חוזר לסדרה'),
                    (f'3{s_sym}', '11-12 נקודות, מזמין'),
                    (f'4{s_sym}', '13+ נקודות (כולל חלוקה), משחק'),
                ]
            )
        elif n_bid in ('2♣', '2♦') and s_suit in ('H', 'S') and s_len >= 6:
            self.app.set_instruction_table(
                f'מחשב הכריז {n_bid}. יש לך {s_len} קלפי {s_sym}. מה תכריז?',
                [
                    (f'2{s_sym}', 'עד 10 נקודות, חוזר לסדרה'),
                    (f'3{s_sym}', '11-14 נקודות, מזמין'),
                    (f'4{s_sym}', '15+ נקודות (כולל חלוקה), משחק'),
                ]
            )
        elif n_bid in ('3♣', '3♦'):
            self.app.set_instruction_table(
                f'מחשב הכריז {n_bid} (מזמין). מה תכריז?',
                [
                    ('פס',  '0-8 נקודות, דוחה הזמנה'),
                    ('3NT', '9+ נקודות, עוצרים בכל הצבעים'),
                    ('3♥',  '9+ נקודות, אין עוצר בלב. מחפש עוצר'),
                    ('3♠',  '9+ נקודות, אין עוצר בספייד. מחפש עוצר'),
                ]
            )
        # 5♠+4♥ אחרי 1NT. הראה ♥ ב-2 (9-12) או קפיצה ב-3♥ (13+)
        elif n_bid == '1NT' and s_suit == 'S' and s_len >= 5 and d.get('H', 0) >= 4:
            self.app.set_instruction_table(
                f'מחשב הכריז 1NT. יש לך 5 ♠ ו-4 ♥. מה תכריז?',
                [
                    ('3♥', '13+ נקודות, קפיצה. יד חזקה, כפוי למשחק'),
                    ('2♥', '9-12 נקודות, מראה 4 קלפי ♥'),
                    ('2♠', 'עד 8 נקודות, חוזר לסדרה'),
                ]
            )
        # 5♥+4♠ אחרי 1NT. הראה ♠ ב-1
        elif n_bid == '1NT' and s_suit == 'H' and s_len >= 5 and d.get('S', 0) >= 4:
            self.app.set_instruction_table(
                f'מחשב הכריז 1NT. יש לך 5 ♥ ו-4 ♠. מה תכריז?',
                [
                    ('1♠', '6+ נקודות, מראה 4 קלפי ♠ ברמה 1'),
                ]
            )
        else:
            h = hcp(self.hands['S'])
            self.app.set_instruction(f'מחשב הכריז {n_bid}.\nיש לך {h} נקודות גבוהות.\nמה תכריז?')

    # ── ניתוב הכרזות ──────────────────────────────────────────────────────

    def on_student_bid(self, bid):
        if self._stage == 'respond':
            self._handle_student_bid(bid)
        elif self._stage == 'continue':
            self._handle_student_bid(bid)

    # ── לוגיקה מרכזית ─────────────────────────────────────────────────────

    def _handle_student_bid(self, bid):
        sym = _S[self._minor]

        # חישוב התשובה הנכונה לפי שלב
        if self._stage == 'respond':
            correct, why = respond_minor(self.hands['S'], self._minor)
        else:
            s_prev = self._history_s[-1]
            n_prev = self._history_n[-1]
            correct, why = responder_continuation_after_minor(
                self.hands['S'], s_prev, n_prev)

        if bid != correct:
            if self._tries >= 1 and bid == self._last_wrong_bid:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')   # W
                self.app.auction_widget.add_bid('Pass')   # N
                self.app.auction_widget.add_bid('Pass')   # E
                explanation = self._explain_wrong(bid, correct)
                self._finish(f'בחרת {bid}.\n{explanation}\nהנכון: {correct}.', ok=False)
                return
            self._tries += 1
            if self._tries < 2:
                self._last_wrong_bid = bid
                last_bid = self._history_n[-1] if self._history_n else f'1{sym}'
                self.app.bidding_box.reset()
                self.app.bidding_box.set_last_bid(last_bid)
                hint = self._first_try_hint(correct)
                self.app.set_feedback(f'{hint}\nנסה שוב.', ok=False)
            else:
                self.app.auction_widget.add_bid(bid, highlight=True)
                self.app.auction_widget.add_bid('Pass')   # W
                self.app.auction_widget.add_bid('Pass')   # N
                self.app.auction_widget.add_bid('Pass')   # E
                explanation = self._explain_wrong(bid, correct)
                self._finish(
                    f'בחרת {bid}.\n{explanation}\nההכרזה הנכונה: {correct}.', ok=False)
            return

        # תשובה נכונה
        self.app.auction_widget.add_bid(bid, highlight=True)
        self.app.auction_widget.add_bid('Pass')   # W
        self._history_s.append(bid)
        self._all_bids += [bid, 'Pass']
        self._tries = 0

        # בדיקת עצירה אחרי הכרזת S
        if _is_final_contract(bid) or _consecutive_passes(self._all_bids) or self._round >= 4:
            final = bid if bid != 'Pass' else (self._history_n[-1] if self._history_n else f'1{sym}')
            self._finish(msg_correct(why, final), ok=True)
            return

        # N מכריז שוב
        opening = f'1{sym}'
        if self._round == 1:
            n_bid, n_why = opener_rebid(self.hands['N'], opening, bid)
        else:
            # agreed_minor רק אם S תמך במינור במפורש (2m/3m בסיבוב ראשון)
            s_first = self._history_s[0] if self._history_s else ''
            _agreed = self._minor if (f'2{sym}' in s_first or f'3{sym}' in s_first) else None
            # S הראה 6 לבבות אם: פתח ב-1♥ ועכשיו קופץ ל-3♥
            _6h = (s_first == '1♥' and bid == '3♥')
            n_bid, n_why = opener_later_bid(self.hands['N'], bid, agreed_minor=_agreed, s_showed_6h=_6h)

        self.app.auction_widget.add_bid(n_bid)
        self.app.auction_widget.add_bid('Pass')   # E
        self._history_n.append(n_bid)
        self._all_bids += [n_bid, 'Pass']
        self._round += 1

        # בדיקת עצירה אחרי הכרזת N
        if _is_final_contract(n_bid) or _consecutive_passes(self._all_bids):
            final = n_bid if n_bid != 'Pass' else bid
            self._finish(
                f'נכון!\n{why}.\n\nמחשב הכריז {n_bid}: {n_why}.\n\nחוזה סופי: {final}.', ok=True)
            return

        # המשך. שלב הבא
        self._stage  = 'continue'
        self._tries  = 0
        self.app.bidding_box.reset()
        self.app.bidding_box.set_last_bid(n_bid)
        self._set_continue_instruction(n_bid)

    # ── רמזים והסברים ─────────────────────────────────────────────────────

    def _first_try_hint(self, correct):
        from engine.scoring import dist_fit_pts
        d = distribution(self.hands['S'])
        h = hcp(self.hands['S'])
        if correct in ('1♥', '1♠'):
            rs = 'H' if correct == '1♥' else 'S'
            if d.get(rs, 0) >= 5 and any(d.get(s, 0) >= 5 for s in ['D','C','H','S'] if s != rs):
                return 'יש לך שתי חמישיות. בדוק איזו סדרה גבוהה יותר.'
            return f'יש לך {d[rs]} קלפי {_S[rs]}. בדוק את המיגורים שלך.'
        if correct == 'Pass':
            return f'יש לך {h} נקודות גבוהות. בדוק אם יש מספיק לענות.'
        # הראה סדרה שנייה אחרי 1NT. לא קשור לנקודות חלוקה
        if correct == '3♥' and d.get('S', 0) >= 5 and d.get('H', 0) >= 4:
            return f'יש לך {h} נקודות ו-5 ♠+4 ♥. קפיצה ל-3♥. יד חזקה, כפוי למשחק.'
        if correct == '2♥' and d.get('S', 0) >= 5 and d.get('H', 0) >= 4:
            return f'יש לך {d["S"]} קלפי ♠ ו-{d["H"]} קלפי ♥. מחשב לא תמך בספייד. הראה ♥ ב-2♥.'
        if correct == '2♠' and d.get('H', 0) >= 5 and d.get('S', 0) >= 4:
            return f'יש לך 5 קלפי ♥ ו-{d["S"]} קלפי ♠. מחשב לא תמך בלב. הראה ♠ ב-2♠.'
        # תמיכה במיגור. כולל נקודות חלוקה
        if correct[1:] in ('♥', '♠') or (len(correct) == 2 and correct[1] in ('♥', '♠')):
            trump = 'H' if '♥' in correct else 'S'
            dp  = dist_fit_pts(self.hands['S'], trump=trump)
            tot = h + dp
            if dp > 0:
                return f'יש לך {h} נקודות גבוהות + {dp} נקודות חלוקה = {tot} נקודות סה״כ.'
        return f'יש לך {h} נקודות גבוהות.'

    def _explain_wrong(self, bid, correct):
        h   = hcp(self.hands['S'])
        d   = distribution(self.hands['S'])
        sym = _S[self._minor]

        # הראה סדרה שנייה. אחרי שN הכריז NT בלי תמיכה
        if correct == '2♥' and d.get('S', 0) >= 5 and d.get('H', 0) >= 4:
            return (f'יש לך {d["S"]} קלפי ♠ ו-{d["H"]} קלפי ♥. מחשב הכריז 1NT. אין לו ספייד. '
                    f'הכרז 2♥ כדי לחפש התאמה בלב.')
        if correct == '2♠' and d.get('H', 0) >= 5 and d.get('S', 0) >= 4:
            return (f'יש לך 5 קלפי ♥ ו-{d["S"]} קלפי ♠. מחשב הכריז 1NT. אין לו לב. '
                    f'הכרז 2♠ כדי לחפש התאמה בספייד.')

        if bid == 'Pass' and correct != 'Pass':
            # בדוק אם זה שלב המשך עם תמיכה במיגור
            if correct[1:] in ('♥', '♠') or (len(correct) == 2 and correct[1] in ('♥', '♠')):
                from engine.scoring import dist_fit_pts
                trump = 'H' if '♥' in correct else 'S'
                dp  = dist_fit_pts(self.hands['S'], trump=trump)
                tot = h + dp
                msym = '♥' if trump == 'H' else '♠'
                return (f'יש לך {h} נקודות גבוהות + {dp} נקודות חלוקה = {tot} נקודות. '
                        f'עם {tot} נקודות כדאי להכריז {correct}.')
            return f'יש לך {h} נקודות גבוהות, ויש לענות לפתיחה.'
        if correct == 'Pass':
            return f'יש לך {h} נקודות גבוהות. כדי לענות לפתיחה צריך לפחות 6 נקודות.'

        if correct in ('1♥', '1♠') and bid not in ('1♥', '1♠'):
            rs = 'H' if correct == '1♥' else 'S'
            bid_suit = {'1♦': 'D', '1♣': 'C'}.get(bid)
            if bid_suit and d.get(bid_suit, 0) >= 5 and d.get(rs, 0) >= 5:
                return (f'יש לך {d[rs]} קלפי {_S[rs]} ו-{d[bid_suit]} קלפי {_S[bid_suit]}.\n'
                        f'כשיש שתי חמישיות, מכריזים את החמישייה הגבוהה יותר קודם.')
            return (f'יש לך {d[rs]} קלפי {_S[rs]}.\n'
                    f'עם 4 קלפים ומעלה במיגור, מכריזים את המיגור לפני כל הכרזה אחרת.')

        if bid == '1♥' and correct == '1♠':
            return (f'יש לך {d["S"]} קלפי ♠ ו-{d["H"]} קלפי ♥.\n'
                    f'כשיש שתי סדרות, מכריזים את הסדרה הארוכה יותר קודם.')
        if bid == '1♠' and correct == '1♥':
            return (f'יש לך {d["H"]} קלפי ♥ ו-{d["S"]} קלפי ♠.\n'
                    f'כשהסדרות שוות באורכן, מכריזים את הסדרה הזולה יותר קודם.')

        if 'NT' in bid:
            if correct in ('1♥', '1♠'):
                rs = 'H' if correct == '1♥' else 'S'
                return (f'יש לך {d[rs]} קלפי {_S[rs]}.\n'
                        f'עם 4 קלפים או יותר בסדרה, מכריזים את הסדרה לפני NT.')
            if correct == '1♦':
                return (f'יש לך {d["D"]} קלפי ♦.\n'
                        f'עם 4 קלפים או יותר בסדרה, מכריזים את הסדרה לפני NT.')
            if correct == f'3{sym}':
                min_cards = 5 if self._minor == 'C' else 4
                suffix = '' if self._minor == 'C' else ' ויד לא מאוזנת'
                return (f'יש לך {h} נקודות גבוהות ו-{d[self._minor]} קלפי {sym}.\n'
                        f'עם 11-12 נקודות, {min_cards}+ קלפי {sym}{suffix}. מכריזים {correct}.')
            if correct == f'2{sym}':
                min_cards = 5 if self._minor == 'C' else 4
                suffix = '' if self._minor == 'C' else ' ויד לא מאוזנת'
                return (f'יש לך {h} נקודות גבוהות ו-{d[self._minor]} קלפי {sym}.\n'
                        f'עם 6-10 נקודות ו-{min_cards}+ קלפי {sym}{suffix}, מכריזים {correct}.')

        if bid == '1NT' and correct == '2NT':
            return (f'יש לך {h} נקודות גבוהות.\n'
                    f'עם 11-12 נקודות יד מאוזנת, מזמינים ל-3NT על ידי הכרזת 2NT.')
        if bid == '2NT' and correct == '1NT':
            return (f'יש לך {h} נקודות גבוהות.\n'
                    f'הכרזת 2NT דורשת 11-12 נקודות. עם 6-10 נקודות מאוזן מכריזים 1NT.')
        if bid == '2NT' and correct == '3NT':
            return (f'יש לך {h} נקודות גבוהות.\n'
                    f'עם 13 נקודות ומעלה, ניתן לקפוץ ישר ל-3NT.')
        if bid == '3NT' and correct == '2NT':
            return (f'יש לך {h} נקודות גבוהות.\n'
                    f'הכרזת 3NT דורשת לפחות 13 נקודות. עם 11-12 מכריזים 2NT כהזמנה.')
        if bid == f'3{sym}' and correct == '2NT':
            return (f'יש לך {h} נקודות ו-{d[self._minor]} קלפי {sym}, אבל היד מאוזנת.\n'
                    f'עם 11-12 נקודות מאוזן, מכריזים 2NT עם עוצרים בכל הצבעים.')
        if bid == '2NT' and correct == f'3{sym}':
            return (f'יש לך {h} נקודות ו-{d[self._minor]} קלפי {sym}, יד לא מאוזנת.\n'
                    f'עם 11-12 נקודות ולא מאוזן, מכריזים {correct} לתמיכה.')

        if bid == f'2{sym}' and correct == f'3{sym}':
            return (f'יש לך {h} נקודות גבוהות ו-{d[self._minor]} קלפי {sym}.\n'
                    f'עם 11-12 נקודות ותמיכה, מכריזים {correct} כהזמנה.')
        if bid == f'3{sym}' and correct == f'2{sym}':
            return (f'יש לך {h} נקודות גבוהות.\n'
                    f'הכרזת {bid} דורשת 11-12 נקודות. עם 6-10 מכריזים {correct}.')
        if bid in (f'2{sym}', f'3{sym}'):
            return (f'יש לך רק {d[self._minor]} קלפי {sym}.\n'
                    f'כדי לתמוך בסדרת הפותח צריך לפחות 5 קלפים.')

        return f'יש לך {h} נקודות גבוהות.'

    def _finish(self, message, ok):
        self._stage = 'done'
        self._seal_auction()
        self.app.bidding_box.disable()
        self.app.set_instruction('')
        self.app.set_feedback(message, ok=ok)
        self.app.show_all_hands()
        self.app.show_new_deal_button()
