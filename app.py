import os, json, customtkinter as ctk
import tkinter as tk
from ui.table_widget import BridgeTable
from ui.auction_widget import AuctionWidget
from ui.bidding_panel import BiddingPanel
from ui.animations import maybe_animate
from utils.rtl import fix, wrap, tokens
from utils.fonts import F, FB

_DIR = os.path.dirname(os.path.abspath(__file__))

ctk.set_appearance_mode('light')
ctk.set_default_color_theme(os.path.join(_DIR, 'bridge_theme.json'))

_LESSONS = [
    ('lessons.lesson_robot_opens_1nt',    'LessonRobotOpens1NT'),      # 0
    ('lessons.lesson_nt_open',            'LessonNTOpen'),             # 1
    ('lessons.lesson_student_opens_major','LessonStudentOpensMajor'),  # 2
    ('lessons.lesson_robot_opens_major',  'LessonRobotOpensMajor'),    # 3
    ('lessons.lesson_stayman',            'LessonStayman'),            # 4
    ('lessons.lesson_transfer',           'LessonTransfer'),           # 5
    ('lessons.lesson_student_opens_minor','LessonStudentOpensMinor'),  # 6
    ('lessons.lesson_robot_opens_minor',  'LessonRobotOpensMinor'),    # 7
    ('lessons.lesson_robot_opens_2c',     'LessonRobotOpens2C'),       # 8
    ('lessons.lesson_robot_opens_2nt',    'LessonRobotOpens2NT'),      # 9
    ('lessons.lesson_slam_nt',            'LessonSlamNT'),             # 10
    ('lessons.lesson_slam_suit',          'LessonSlamSuit'),           # 11
    ('lessons.lesson_robot_opens_weak2',  'LessonRobotOpensWeak2'),    # 12
    ('lessons.lesson_student_opens_weak2','LessonStudentOpensWeak2'),  # 13
    ('lessons.lesson_ogust',             'LessonOgust'),              # 14
    ('lessons.lesson_overcall',          'LessonOvercall'),           # 15
    ('lessons.lesson_overcall_response', 'LessonOvercallResponse'),  # 16
    ('lessons.lesson_fourth_suit',       'LessonFourthSuit'),        # 17
    ('lessons.lesson_takeout_double',    'LessonTakeoutDouble'),     # 18
    ('lessons.lesson_negative_double',   'LessonNegativeDouble'),    # 19
    ('lessons.lesson_minor_nt',          'LessonMinorNT'),           # 20
]
# כפתורי שיעורים בתפריט: (תווית, אינדקס ברירת מחדל)
_BUTTONS = [
    ('1 שיעור\n1NT',        0),
    ('2 שיעור\nמיגורים',    3),
    ('3 שיעור\nמינורים',    7),
    ('4 שיעור\nסטיימן',     4),
    ('5 שיעור\nטרנספר',     5),
    ('6 שיעור\n2NT',        9),
    ('7 שיעור\n2♣ חזקה',   8),
    ('8 שיעור\nNT סלם ב',    10),
    ('9 שיעור\nסלם בצבע',  11),
    ('10 שיעור\nWeak Two', 12),
    ('11 שיעור\nOgust',    14),
    ('12 שיעור\nאוברקול',  15),
    ('13 שיעור\nדבל',       18),
    ('14 שיעור\nנגטיב X',  19),
    ('15 שיעור\nNT במינור', 20),
]
# זוגות שיעורים: מחשב פותח ↔ תלמיד פותח
_PAIRS = {0: 1, 1: 0, 2: 3, 3: 2, 4: 4, 5: 5, 6: 7, 7: 6, 8: 8, 9: 9, 10: 10, 11: 11, 12: 13, 13: 12, 14: 14, 15: 16, 16: 15, 18: 18, 20: 20}
_COMPUTER_OPENS = {0, 3, 4, 5, 7, 8, 9, 10, 11, 12, 15, 16, 18, 20}
_LESSON_TO_BTN  = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 5, 6: 3, 7: 3, 8: 7, 9: 6, 10: 8, 11: 9, 12: 10, 13: 10, 14: 11, 15: 12, 16: 12, 18: 13, 19: 14, 20: 15}
_DEFAULT      = 0
_MISTAKE_FILE = os.path.join(_DIR, 'last_mistake.json')


class BridgeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("עוזר ברידג׳ לתלמיד")
        self.resizable(True, True)
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = min(900, sw - 40)
        h = min(700, sh - 120)
        x = (sw - w) // 2
        y = max(20, (sh - h) // 4)
        self.geometry(f'{w}x{h}+{x}+{y}')
        self.minsize(750, 600)
        self._lesson             = None
        self._lesson_idx         = _DEFAULT
        self._key_buf            = None
        self._mistake_lesson     = None
        self._mistake_lesson_idx = None
        self._mistake_phase      = 1
        self._build_ui()
        self._start_lesson(_DEFAULT)
        self.bind_all('<Key>', self._on_key)
        if os.path.exists(_MISTAKE_FILE):
            self._retry_btn.configure(state='normal')

    # ── בניית ממשק ─────────────────────────────────────────────────────────

    def _build_ui(self):
        # כותרת
        ctk.CTkLabel(self,
                     text="עוזר ברידג׳ לתלמיד",
                     font=FB(17),
                     text_color='#1a3a6b').pack(pady=(6, 2))

        # כפתורי שיעורים — עד 8 בשורה, שורה נוספת אם צריך
        lesson_bar = ctk.CTkFrame(self, fg_color='#e8edf8', corner_radius=8)
        lesson_bar.pack(fill='x', padx=10, pady=(0, 3))

        _ROW_SIZE = 8
        rows_data = [_BUTTONS[i:i+_ROW_SIZE] for i in range(0, len(_BUTTONS), _ROW_SIZE)]

        self._lesson_btns = []
        for row_btns in rows_data:
            row = ctk.CTkFrame(lesson_bar, fg_color='transparent')
            row.pack(fill='x')
            for label, default_idx in row_btns:
                btn = ctk.CTkButton(
                    row, text=fix(label),
                    width=88, height=38,
                    font=F(12),
                    fg_color='#2a5a9b', hover_color='#1a3a6b',
                    command=lambda idx=default_idx: self._start_lesson(idx)
                )
                btn.pack(side='right', padx=2, pady=3)
                self._lesson_btns.append(btn)

        # שורה אמצעית: שולחן + מכרז
        mid = ctk.CTkFrame(self, fg_color='transparent')
        mid.pack(fill='both', expand=True, padx=10, pady=2)

        right = ctk.CTkFrame(mid, fg_color='transparent')
        right.pack(side='right', fill='y', padx=(6, 0))

        self.table = BridgeTable(mid)
        self.table.pack(side='left', fill='both', expand=True)

        # מכרז — בתוך שולחן הברידג', ליד הצפון (row=0, col=2)
        self.auction_widget = AuctionWidget(self.table)
        self.auction_widget.grid(row=0, column=2, padx=(6, 8), pady=4, sticky='nsew')

        self._instr_container = ctk.CTkFrame(right, fg_color='transparent')
        self._instr_container.pack(pady=(1, 0), padx=4, fill='x')

        # כפתור החלפת פותח — בתחתית
        self._toggle_btn = ctk.CTkButton(
            right, text='',
            width=140, height=28,
            font=FB(13),
            fg_color='#7a3a00', hover_color='#5a2a00',
            command=self._toggle_opener)
        self._toggle_btn.pack(side='bottom', pady=(0, 2), padx=4)

        self._retry_btn = ctk.CTkButton(
            right, text=fix('חזור על הטעות ↺'),
            command=self._retry_mistake,
            width=140, height=28,
            font=F(13),
            fg_color='#b05a00', hover_color='#8a4200',
            state='disabled')
        # הכפתור "חזור על הטעות" הוסר מהתצוגה (לפי בקשת המשתמש);
        # האובייקט נשאר קיים כדי לא לשבור קריאות configure() במקומות אחרים.
        # self._retry_btn.pack(side='bottom', pady=(0, 2), padx=4)

        # כפתורי יד חדשה / שחק שוב — מעל כפתור המחשב, תמיד גלויים
        _btn_row = ctk.CTkFrame(right, fg_color='transparent')
        _btn_row.pack(side='bottom', pady=(0, 2), padx=4)

        self.bidding_box = BiddingPanel(right, on_bid=self._on_bid)
        self.bidding_box.pack(side='bottom', pady=(0, 2), padx=4)

        self._new_deal_btn = ctk.CTkButton(
            _btn_row, text='יד חדשה ▶',
            command=self._new_deal,
            width=82, height=30,
            font=F(13),
            fg_color='#2a7a2a', hover_color='#1e5e1e')
        self._new_deal_btn.pack(side='right', padx=2)

        self._replay_btn = ctk.CTkButton(
            _btn_row, text='שחק שוב ↺',
            command=self._replay_deal,
            width=82, height=30,
            font=F(13),
            fg_color='#5a3a80', hover_color='#3a2060')
        self._replay_btn.pack(side='right', padx=2)

    # ── שיעורים ────────────────────────────────────────────────────────────

    def _start_lesson(self, idx):
        self._lesson_idx = idx
        self._setup_lesson_ui(idx)
        import importlib
        module_path, class_name = _LESSONS[idx]
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        self._lesson = cls(self)
        self._lesson.start()

    def _new_deal(self):
        self._start_lesson(self._lesson_idx)

    def _toggle_opener(self):
        companion = _PAIRS.get(self._lesson_idx, self._lesson_idx)
        self._start_lesson(companion)
        self._update_toggle_btn()

    def _update_toggle_btn(self):
        if self._lesson_idx in _COMPUTER_OPENS:
            self._toggle_btn.configure(text='מחשב פותח')
        else:
            self._toggle_btn.configure(text='אני פותח')

    def _on_bid(self, bid):
        if self._lesson:
            try:
                self._lesson.on_student_bid(bid)
            except Exception as e:
                import traceback
                self.set_feedback(f'שגיאה: {e}', ok=False)
                traceback.print_exc()

    # ── API לשיעורים ───────────────────────────────────────────────────────

    def set_instruction(self, text):
        # התקדמות לסבב/שלב הבא עם הוראה = התלמיד הכריז נכון. אם מוצג 'לא נכון'
        # (טעות שתוקנה) — מחליפים אותו ב'נכון' ירוק מיד.
        if text and self.table.showing_wrong():
            self.table.set_feedback('', ok=True)
        self._pending_table = None
        for w in self._instr_container.winfo_children():
            w.destroy()
        self._instr_container.update_idletasks()
        if text:
            self._render_rtl(
                self._instr_container, text,
                font=('Gisha', 14), fg='#1a3a6b', anchor='center'
            )

    def _panel_bg(self):
        """צבע רקע הפנל בזמן ריצה — להתאמת tk.Label לתמה."""
        return self._apply_appearance_mode(self.cget('fg_color'))

    def _render_rtl(self, parent, text, font, fg, anchor='center', bold=False):
        """מרנדר טקסט עברי בפנל בלי תווי-בקרה: כל אסימון = tk.Label נפרד,
        ארוז side='right'. עברית נשארת ימין→שמאל, וכל אשכול לטיני (מספר/טווח/
        הכרזה/סמל) נשאר שלם ולא מתהפך. זה הפתרון היחיד שלא עושה "סלט"."""
        bg = self._panel_bg()
        for line in str(text).split('\n'):
            row = tk.Frame(parent, bg=bg)
            row.pack(anchor=anchor, pady=1)
            toks = tokens(line)
            if not toks:
                # שורה ריקה — שומרים רווח אנכי
                tk.Label(row, text=' ', font=font, bg=bg, fg=fg).pack()
                continue
            for tok in toks:
                tk.Label(row, text=tok, font=font, bg=bg, fg=fg).pack(
                    side='right', padx=1
                )

    def set_instruction_table(self, header, rows):
        """header: str, rows: [(bid, condition_str), ...]
        מציג רק את הכותרת — הטבלה תוצג אחרי הכרזת התלמיד."""
        # מעבר לשלב חדש = התלמיד הכריז נכון. אם קודם הוצג 'לא נכון' (טעות
        # שתוקנה) — מחליפים אותו ב'נכון' ירוק. אחרת מנקים פידבק ישן.
        if self.table.showing_wrong():
            self.table.set_feedback('', ok=True)
        else:
            self.table.clear_feedback()
        self._pending_table = rows
        for w in self._instr_container.winfo_children():
            w.destroy()
        if header:
            hdr = tk.Frame(self._instr_container, bg=self._panel_bg())
            hdr.pack(anchor='center', pady=(0, 3))
            self._render_rtl(
                hdr, header,
                font=('Gisha', 14, 'bold'), fg='#1a3a6b', anchor='center'
            )

    def _render_table(self, parent, rows, font_size=13, fg='#555555'):
        """מרנדר שורות טבלה לתוך parent.
        2-tuple (bid, cond): שורה בודדת.
        3-tuple (pts, support, bid): גריד 3 עמודות — נקודות | תמיכה עם | הכרזה."""
        bg = self._panel_bg()
        if rows and len(rows[0]) == 3:
            HEADERS = ('הכרזה', 'תמיכה עם', 'נקודות')
            grid = tk.Frame(parent, bg=bg)
            grid.pack(anchor='e', pady=(4, 0))
            # כותרות
            for c_idx, h in enumerate(HEADERS):
                tk.Label(grid, text=h,
                         font=('Gisha', font_size - 1, 'bold'),
                         bg=bg, fg='#1a3a6b',
                         anchor='center', padx=14, pady=2
                         ).grid(row=0, column=c_idx, sticky='nsew')
            # שורות נתונים
            for r_idx, row_data in enumerate(rows, start=1):
                pts, sup, bid = row_data
                # עמודה 0: הכרזה — אשכול לטיני אטומי, בלי תווי-בקרה
                tk.Label(grid, text=str(bid),
                         font=('Gisha', font_size), bg=bg, fg=fg,
                         anchor='center', padx=14, pady=2
                         ).grid(row=r_idx, column=0, sticky='nsew')
                # עמודה 1: תמיכה — כל חלק ב-Label נפרד, side='right' → ימין-לשמאל
                sup_frame = tk.Frame(grid, bg=bg)
                sup_frame.grid(row=r_idx, column=1, sticky='nsew', padx=4)
                if isinstance(sup, (list, tuple)):
                    parts = list(sup)
                elif sup:
                    # פירוק אוטומטי דרך הטוקנייזר — טווחים כמו 8-9 נשארים שלמים
                    parts = tokens(sup)
                else:
                    parts = []
                for part in parts:
                    tk.Label(sup_frame, text=str(part),
                             font=('Gisha', font_size), bg=bg, fg=fg,
                             anchor='center', padx=3
                             ).pack(side='right')
                # עמודה 2: נקודות — Label בודד
                tk.Label(grid, text=str(pts),
                         font=('Gisha', font_size), bg=bg, fg=fg,
                         anchor='center', padx=14, pady=2
                         ).grid(row=r_idx, column=2, sticky='nsew')
        else:
            for row in rows:
                bid, cond = row
                # שורה אחת: ההכרזה מימין, התנאי לצידה — כל אסימון Label נפרד
                line = tk.Frame(parent, bg=bg)
                line.pack(anchor='e', pady=1)
                tk.Label(line, text=str(bid),
                         font=('Gisha', font_size, 'bold'), bg=bg, fg=fg,
                         padx=6).pack(side='right')
                for tok in tokens(str(cond)):
                    tk.Label(line, text=tok,
                             font=('Gisha', font_size), bg=bg, fg=fg,
                             padx=1).pack(side='right')

    def add_immediate_table(self, rows):
        """מוסיף טבלה מיידית לאזור ההוראות (לא ממתינה לפידבק)."""
        tbl = ctk.CTkFrame(self._instr_container, fg_color='transparent')
        tbl.pack(anchor='e', pady=(4, 0))
        self._render_table(tbl, rows, font_size=13, fg='#555555')

    def reveal_instruction_table(self):
        """מציג את הטבלה השמורה (נקרא אוטומטית לפני פידבק)."""
        rows = getattr(self, '_pending_table', None)
        if not rows:
            return
        self._pending_table = None
        tbl = ctk.CTkFrame(self._instr_container, fg_color='transparent')
        tbl.pack(anchor='e')
        self._render_table(tbl, rows, font_size=15, fg='#333333')

    def set_feedback(self, text, ok=True, correct_answer=''):
        self.reveal_instruction_table()
        self.table.set_feedback(fix(wrap(text.replace('\n\n', '\n'))), ok)
        if ok:
            maybe_animate(self.table)
        if self.bidding_box._locked:
            self._mistake_lesson     = self._lesson
            self._mistake_lesson_idx = self._lesson_idx
            self._mistake_phase      = getattr(self._lesson, '_phase', 1)
            self._save_mistake_file()
            self._retry_btn.configure(state='normal')

    def show_all_hands(self):
        if self._lesson:
            self.table.show_hands(self._lesson.hands, visible=('N', 'E', 'S', 'W'))

    def show_new_deal_button(self):
        pass  # כפתור תמיד גלוי

    def _save_mistake_file(self):
        try:
            data = {
                'lesson_idx': self._mistake_lesson_idx,
                'phase':      self._mistake_phase,
                'hands':      {seat: list(hand) for seat, hand in self._mistake_lesson.hands.items()},
            }
            with open(_MISTAKE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def _load_mistake_file(self):
        try:
            with open(_MISTAKE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def _retry_mistake(self):
        if self._lesson:
            # שיעור פעיל — אותה חלוקה
            self._setup_lesson_ui(self._lesson_idx)
            self._lesson.replay()
        elif self._mistake_lesson:
            # באותה הפעלה — replay ישיר
            self._lesson_idx = self._mistake_lesson_idx
            self._lesson     = self._mistake_lesson
            self._setup_lesson_ui(self._lesson_idx)
            self._lesson.replay()
        else:
            # הפעלה חדשה — טוען מקובץ
            data = self._load_mistake_file()
            if not data:
                return
            lesson_idx = data['lesson_idx']
            phase      = data['phase']
            hands      = {seat: list(cards) for seat, cards in data['hands'].items()}
            import importlib
            module_path, class_name = _LESSONS[lesson_idx]
            mod    = importlib.import_module(module_path)
            lesson = getattr(mod, class_name)(self)
            self._lesson_idx = lesson_idx
            self._lesson     = lesson
            self._setup_lesson_ui(lesson_idx)
            lesson._preset_hands = hands
            lesson._next_phase   = phase
            lesson.start()

    def _setup_lesson_ui(self, idx):
        active_btn = _LESSON_TO_BTN.get(idx, 0)
        for i, btn in enumerate(self._lesson_btns):
            btn.configure(fg_color='#1a3a6b' if i + 1 == active_btn else '#2a5a9b')
        self._update_toggle_btn()
        self.table.clear_feedback()
        self.set_instruction('')
        self.bidding_box.reset()

    def _replay_deal(self):
        self.table.clear_feedback()
        self.set_instruction('')
        self.bidding_box.reset()
        if self._lesson:
            self._lesson.replay()

    # ── קיצורי מקלדת ──────────────────────────────────────────────────────

    def _on_key(self, event):
        k = event.char.lower()
        if not k:
            return
        bid = None
        if k == 'p':
            bid = 'Pass'
        elif k == 'x':
            bid = 'X'
        elif k in '1234567':
            self._key_buf = k
            return
        elif self._key_buf and k in 'cdhsn':
            suit = {'c': '♣', 'd': '♦', 'h': '♥', 's': '♠', 'n': 'NT'}[k]
            bid = f'{self._key_buf}{suit}'
        self._key_buf = None
        if bid and self._bid_enabled(bid):
            self._on_bid(bid)

    def _bid_enabled(self, bid):
        btn = self.bidding_box._btns.get(bid)
        return btn is not None and btn.cget('state') == 'normal'
