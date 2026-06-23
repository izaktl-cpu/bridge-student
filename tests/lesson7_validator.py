"""
ולידטור שיעור 7 — בדיקה מלאה של זרימת השיעור.

בדיקות:
  1. טבלה↔engine: הכרזה נכונה מופיעה בטבלת הוראות
  2. כל הנתיבים מסתיימים >= 3NT/4M (לא עוצרים לפני גיים)
  3. ידיות 33+ נקודות מגיעות ל-Blackwood/Gerber
  4. ok=False בנתיב שגוי, ok=True בנכון
  5. אחרי כל תיקון — הסקריפט הזה ירוץ ויצביע על הבעיה
"""
import sys, os, traceback
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.deal_constraints import deal_robot_opens_2c
from engine.scoring import hcp

_GAME = {'3NT', '4NT', '4♥', '4♠', '5♣', '5♦', '5♥', '5♠', '5NT',
         '6NT', '6♥', '6♠', '6♣', '6♦',
         '7NT', '7♥', '7♠', '7♣', '7♦'}
_SLAM = {'6NT', '6♥', '6♠', '6♣', '6♦', '7NT', '7♥', '7♠', '7♣', '7♦'}


# ── Mock App ──────────────────────────────────────────────────────────────────

class MockAuction:
    def __init__(self): self.bids = []
    def add_bid(self, b, highlight=False): self.bids.append(b)
    def reset(self): self.bids = []
    def set_dealer(self, p): pass
    def seal(self): pass

class MockBidBox:
    def __init__(self): self.last_bid = None; self._locked = False
    def set_last_bid(self, b): self.last_bid = b
    def reset(self): pass
    def disable(self): self._locked = True
    def enable(self): self._locked = False

class MockTable:
    def show_hands(self, h, visible=None): pass
    def set_feedback(self, t, ok=True): pass
    def clear_feedback(self): pass

class MockApp:
    def __init__(self):
        self.auction_widget = MockAuction()
        self.bidding_box    = MockBidBox()
        self.table          = MockTable()
        self._pending_table = None
        self._last_instruction = None
        self._last_table_rows  = None   # [(bid, desc), ...]
        self._last_feedback    = None
        self._last_ok          = None
        self._finished         = False
        self._final_contract   = None

    def set_instruction(self, text):
        self._pending_table      = None
        self._last_instruction   = text
        self._last_table_rows    = None

    def set_instruction_table(self, header, rows):
        self._pending_table    = rows
        self._last_instruction = header
        self._last_table_rows  = rows

    def reveal_instruction_table(self): pass

    def set_feedback(self, text, ok=True, correct_answer=''):
        self._last_feedback = text
        self._last_ok       = ok
        import re
        m = re.search(r'חוזה סופי:\s*(\S+)', text)
        if m:
            self._final_contract = m.group(1).rstrip('.')
            self._finished = True  # רק כשיש חוזה סופי

    def show_all_hands(self): pass
    def show_new_deal_button(self): pass
    def clear_feedback(self): pass

    def table_bids(self):
        """מחזיר רשימת הכרזות אפשריות מהטבלה האחרונה."""
        if self._last_table_rows:
            return [r[0] for r in self._last_table_rows]
        return []


# ── הרצת נתיב אחד ────────────────────────────────────────────────────────────

def _run_path(lesson, app, errors, idx, total_pts):
    """מריץ נתיב מלא — מכריז תמיד נכון — ומאתר בעיות."""
    MAX_ROUNDS = 8

    for round_num in range(MAX_ROUNDS):
        if app._finished or app.bidding_box._locked:
            break

        # בשלבי blackwood/gerber — הטבלה קובעת, לא _correct_bid
        special_stages = {'blackwood', 'gerber', 'gerber_south'}
        table_bids = app.table_bids()

        if lesson._stage in special_stages:
            if not table_bids:
                errors.append(f'#{idx} שלב {lesson._stage} ללא טבלה')
                return
            # בחר את ההכרזה הנכונה לפי חישוב פנימי של השיעור
            if lesson._stage == 'blackwood':
                from engine.scoring import key_cards
                from engine.cards import card_rank
                has_fit  = getattr(lesson, '_bw_fit', False)
                sym      = getattr(lesson, '_bw_sym', None)
                trump    = getattr(lesson, '_bw_trump', None)
                hn_pts   = hcp(lesson.hands['N']) + hcp(lesson.hands['S'])
                if has_fit and trump and sym:
                    n_kc = key_cards(lesson.hands['N'], trump)
                    s_kc = key_cards(lesson.hands['S'], trump)
                    total_kc = n_kc + s_kc
                    needed = 4 if hn_pts >= 33 else 5
                    correct = f'6{sym}' if total_kc >= needed else f'5{sym}'
                else:
                    n_a = sum(1 for c in lesson.hands['N'] if card_rank(c) == 'A')
                    s_a = sum(1 for c in lesson.hands['S'] if card_rank(c) == 'A')
                    correct = '6NT' if (n_a + s_a) >= 4 else '5NT'
            elif lesson._stage in ('gerber', 'gerber_south'):
                from engine.cards import card_rank
                n_a = sum(1 for c in lesson.hands['N'] if card_rank(c) == 'A')
                s_a = sum(1 for c in lesson.hands['S'] if card_rank(c) == 'A')
                total_a = n_a + s_a
                if lesson._stage == 'gerber':
                    replies = ['4♦', '4♥', '4♠', '4NT', '4♦']
                    correct = replies[s_a]
                else:
                    correct = '6NT' if total_a == 4 else '5NT'
        else:
            try:
                correct, why = lesson._correct_bid()
            except Exception as e:
                errors.append(f'#{idx} _correct_bid שגיאה (שלב={lesson._stage}): {e}')
                return

            # בדיקה 1: הכרזה נכונה מופיעה בטבלה
            if table_bids and correct not in table_bids:
                errors.append(
                    f'#{idx} טבלה↔engine: נכון={correct} אבל טבלה={table_bids} '
                    f'(שלב={lesson._stage} round={lesson._round})'
                )

        # מכריז נכון
        try:
            lesson.on_student_bid(correct)
        except Exception as e:
            errors.append(f'#{idx} on_student_bid({correct}) שגיאה: {e}')
            traceback.print_exc()
            return

    # בדיקה 2: הגענו לגיים
    final = app._final_contract
    if final is None:
        errors.append(f'#{idx} לא הגיע לחוזה סופי (total={total_pts}נק\')')
        return

    contract_clean = final.replace('.', '')
    if contract_clean not in _GAME:
        errors.append(f'#{idx} חוזה סופי נמוך: {final} (total={total_pts}נק\')')

    # בדיקה 3: 33+ נקודות + 4 אסים + S>=8 HCP → חייב להיות סלם
    hs = hcp(lesson.hands['S'])
    if total_pts >= 33 and hs >= 8 and contract_clean not in _SLAM:
        from engine.cards import card_rank
        total_aces = sum(1 for c in lesson.hands['N'] + lesson.hands['S']
                        if card_rank(c) == 'A')
        if total_aces == 4:
            errors.append(f'#{idx} ⚠ סלם: total={total_pts}נק\' S={hs}נק\' + 4 אסים אבל חוזה={final}')

    # בדיקה 4: ok=True בסוף (הכרזנו נכון כל הזמן)
    if app._last_ok is False:
        errors.append(f'#{idx} ok=False למרות שהכרזנו נכון. msg={app._last_feedback!r:.60}')


# ── בדיקת RTL ─────────────────────────────────────────────────────────────────

def check_rtl(lesson_path):
    import re
    issues = []
    with open(lesson_path, encoding='utf-8') as f:
        lines = f.readlines()

    for lineno, line in enumerate(lines, 1):
        strings = re.findall(r"f'([^']*)'|f\"([^\"]*)\"|'([^']*)'|\"([^\"]*)\"", line)
        for groups in strings:
            text = next((g for g in groups if g), '')
            if not text:
                continue
            # {var} נקודות ללא prefix
            for m in re.finditer(r'\{[^}]+\}\s+נקודות', text):
                before = text[:m.start()].rstrip()
                prefixes = ('יש', 'סה', 'לך', 'לו', 'לנו', 'ל-', 'כ-', 'ב-')
                if not any(before.endswith(p) for p in prefixes):
                    issues.append(f'שורה {lineno}: {{{m.group()}}} ללא prefix')
            # ✓ + LTR אותה שורה
            if '✓' in text and re.search(r'[1-7][♣♦♥♠NT]', text) and '\\n' not in text:
                issues.append(f'שורה {lineno}: ✓ נכון! עם LTR אותה שורה')
    return issues


# ── ריצה ראשית ────────────────────────────────────────────────────────────────

def run(n=500):
    from lessons.lesson_robot_opens_2c import LessonRobotOpens2C

    errors   = []
    warnings = []
    stats    = Counter()

    for i in range(n):
        try:
            app    = MockApp()
            lesson = LessonRobotOpens2C(app)

            # הכנסת deal ישירה (עוקפים _deal_count)
            hands = deal_robot_opens_2c()
            lesson.hands      = hands
            lesson._replaying = True  # כדי ש-start() לא יחליף ידיות

            app.auction_widget.reset()
            lesson.start()

            total_pts = hcp(hands['N']) + hcp(hands['S'])
            stats['total'] += 1
            if total_pts >= 33:
                stats['slam_candidates'] += 1

            _run_path(lesson, app, errors, i, total_pts)

            final = (app._final_contract or '').replace('.', '')
            if final in _SLAM:
                stats['slams'] += 1
            elif final in _GAME:
                stats['games'] += 1

        except Exception as e:
            errors.append(f'#{i} חריגה כללית: {e}')

    # RTL
    lesson_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'lessons', 'lesson_robot_opens_2c.py')
    rtl_issues = check_rtl(lesson_path)

    # ── דוח ──────────────────────────────────────────────────────────────────
    sep = '─' * 60
    print(sep)
    print(f' ולידטור שיעור 7  |  {n} ידיות')
    print(sep)
    print(f'  גיים:  {stats["games"]}  |  סלם: {stats["slams"]}  |  '
          f'מועמדי סלם (33+נק\'): {stats["slam_candidates"]}')
    print()

    # מיין שגיאות לפי סוג
    by_type = defaultdict(list)
    for e in errors:
        if 'טבלה↔engine' in e:
            by_type['טבלה↔engine'].append(e)
        elif 'עצירה' in e or 'נמוך' in e or 'סופי' in e:
            by_type['עצירה/חוזה'].append(e)
        elif 'סלם' in e or '⚠' in e:
            by_type['סלם'].append(e)
        elif 'ok=False' in e:
            by_type['ok שגוי'].append(e)
        else:
            by_type['אחר'].append(e)

    if errors:
        print(f'  ✗ שגיאות: {len(errors)}')
        for t, errs in by_type.items():
            print(f'\n  [{t}] — {len(errs)}:')
            for e in errs[:4]:
                print(f'    • {e}')
            if len(errs) > 4:
                print(f'    ... ועוד {len(errs)-4}')
    else:
        print('  ✓ זרימת שיעור — אין שגיאות')

    print()
    if rtl_issues:
        print(f'  ✗ בעיות RTL: {len(rtl_issues)}')
        for r in rtl_issues:
            print(f'    • {r}')
    else:
        print('  ✓ RTL — אין בעיות')

    print(sep)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    run(n)
