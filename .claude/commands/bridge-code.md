# bridge-code — הוראות קוד ו-UI
> 🖥️ **תוכן: מבנה הפרויקט, RTL/fix(), עיצוב UI, BiddingPanel, כללי פיתוח שיעורים**

מסמך ידע: כל הוראות הקוד, UI, ו-RTL עבור פרויקט bridge-student.
משמש כ-reference לביקורת קוד ולפיתוח שיעורים חדשים.

---

## מבנה הפרויקט

```
D:\bridge-student\
├── main.py                          # BridgeApp().mainloop()
├── app.py                           # מחלקה ראשית + בורר שיעורים
├── bridge_theme.json                # ערכת עיצוב CTk (כחול-לבן)
├── engine\
│   ├── cards.py                     # make_deck, SUITS, SUIT_SYMBOLS, SUIT_COLORS
│   ├── scoring.py                   # hcp(), is_balanced(), distribution(), suit_len()
│   ├── deal_constraints.py          # פונקציות חלוקה מבוקרת
│   ├── opening.py                   # opening_bid(hand) → (bid, explanation)
│   ├── response.py                  # respond_1nt / respond_major / respond_minor / respond_2c / respond_weak2
│   ├── rebid.py                     # opener_rebid(hand, opening, partner_response) → (bid, why)
│   └── overcall.py                  # get_overcall(hand, opening_bid, position) → (bid, why)
├── ui\
│   ├── table_widget.py              # BridgeTable (שולחן ירוק) + PlayerPanel
│   ├── auction_widget.py            # AuctionWidget — עמודת מכרז
│   └── bidding_panel.py             # BiddingPanel — פנל הכרזה מלא
├── utils\
│   └── rtl.py                       # fix() — תיקון עברית-אנגלית מעורבת
└── lessons\
    ├── base.py
    ├── lesson_*.py                  # כל שיעור בקובץ נפרד
```

---

## שיעורים פעילים (app.py _BUTTONS)

| index | כפתור | נושא | קובץ |
|-------|-------|------|------|
| 0,1 | שיעור 1 — 1NT | תלמיד/רובוט פותח 1NT | lesson_nt_open / lesson_robot_opens_1nt |
| 2,3 | שיעור 2 — מיגורים | רובוט/תלמיד פותח מיגור | lesson_robot_opens_major / lesson_student_opens_major |
| 4 | שיעור 4 — סטיימן | סטיימן אחרי 1NT | lesson_stayman_transfer |
| 5 | שיעור 5 — טרנספר | טרנספר אחרי 1NT | lesson_stayman_transfer |
| 6,7 | שיעור 3 — מינורים | רובוט/תלמיד פותח מינור | lesson_robot_opens_minor / lesson_student_opens_minor |
| 8 | שיעור 7 — 2♣ חזקה | lesson_robot_opens_2c |
| 9 | שיעור 6 — 2NT | lesson_robot_opens_2nt |
| 10 | שיעור 8 — סלם NT | lesson_slam_nt |
| 11 | שיעור 9 — סלם בצבע | lesson_slam_suit |
| 12,13 | שיעור 10 — Weak Two | lesson_robot/student_opens_weak2 |
| 14 | שיעור 11 — Ogust | lesson_ogust |
| 15,16 | שיעור 12 — אוברקול | lesson_overcall / lesson_overcall_response |
| 17 | שיעור 13 — צבע רביעי | lesson_fourth_suit |

**חשוב**: "שיעור 6" בכפתור ≠ index 6. לפני עריכה — תמיד בדוק `_BUTTONS` ב-app.py.

---

## API של app.py לשיעורים

```python
self.app.table.show_hands(hands, visible=('N','E','S','W'))
self.app.auction_widget.reset()
self.app.auction_widget.set_dealer('S')        # או 'N'
self.app.auction_widget.add_bid(bid, highlight=False)
self.app.set_instruction(text)                 # מופיע מתחת למכרז
self.app.set_feedback(text, ok=True/False)     # פינה ימין-תחתון של השולחן
self.app.bidding_box.set_bids([...])           # הגבלה פדגוגית
self.app.bidding_box.disable()
self.app.show_new_deal_button()
```

---

## RTL — fix() חובה

**כלל**: כל טקסט עברי ב-CTkLabel חייב לעבור `fix()` מ-`utils/rtl.py`.

```python
from utils.rtl import fix

# בתוך שיעור — app.py מטפל אוטומטית ב-set_instruction / set_feedback
# label חדש עם עברית+מספרים: חובה לעטוף ידנית
label = CTkLabel(parent, text=fix("15-17 נקודות גבוהות"))
```

**מה fix() מגן עליו**:
- הכרזות: `2♣`, `1NT`, `7NT`
- `Pass`, `X`, `XX`
- טווחי מספרים: `8-9`, `10+`, `15-17`
- מילים אנגליות: `AKQ`, `KQ`, `Ogust`

**כפתורי שיעורים** עם מספרים/לטינית (למשל `שיעור 6 — 2NT`):
```python
text=fix(label)  # חובה, כבר מיושם ב-app.py שורה 79
```

---

## set_instruction_table — כללי עיצוב

1. **wraplength לעמודת תנאי**: `220` (לא 120 — צר מדי)
2. **מפריד**: נקודה `.` (לא נקודותיים `:` — בעיית RTL)
3. **טקסט ארוך**: לחצות ל-2 שורות עם `\n` (לא 3+ שורות)

## RTL — כללים קבועים

- `fix()` מטפל ב-`W`, `E`, `N`, `S`, `X`, `Pass`, מספרים, הכרזות — **אין להסיר אנגלית מהטקסט**
- כל `CTkLabel` עם טקסט מעורב **חייב** `justify='right'` + `wraplength`
- כותרת עם `\n` ב-`set_instruction_table` **חייבת** `justify='right'` — בלי זה שורה שנייה נשברת שמאלה
- `app.py` מטפל בזה אוטומטית — label חדש מחוץ ל-`app.py`: לוודא ידנית

---

## UI — עיצוב

| פריט | ערך |
|------|-----|
| חלון | min(900, sw-40) × min(720, sh-80), resizable |
| שולחן | `#1e5c1e`, grid 3×3 |
| N | row=0 col=1 |
| S | row=2 col=1 |
| W | row=1 col=0 |
| E | row=1 col=2 |
| PlayerPanel — שם | font=12 |
| PlayerPanel — קלפים | font=19bold |
| AuctionWidget | תאים רוחב=56, כותרות font=12bold |
| הוראות | wraplength=200, font=11 |

---

## BiddingPanel (ui/bidding_panel.py)

```python
panel.set_bids(['Pass', '2NT', '3NT'])   # הגבלה פדגוגית
panel.set_last_bid('1♥')                  # חוקיות אוטומטית
panel.disable()                           # נעילה
panel.enable()
panel.reset()                             # יד חדשה
panel.clear()                             # מסיר הגבלה
```

---

## עקרונות פדגוגיים

1. ידיים מבוקרות — רק החומר הנלמד בשיעור
2. כל שיעור = קובץ נפרד עם stages (`open`/`respond`/`rebid`/`done`)
3. תלמיד תמיד ב-S; גולם ב-N; E/W = Pass תמיד
4. ריטריי: ניסיון 1 → "נסה שנית בבקשה.", ניסיון 2 → הצגת תשובה נכונה
5. "תלמיד מתעקש" בשיעור 2♣: ניסיון 2 שגוי → קבל ההכרזה, ממשיך לפי מה שקיבל

---

## קיצורי מקלדת גלובליים

**אסור**: `Ctrl+אות` בלבד (ספריית `keyboard` מאזינה לפיזי, לא לוגי — T הפיזי = א בעברית).

**מותר**: מקשי פונקציה (F9, F10 וכו') או `Ctrl+Shift+Alt+אות`.

---

## pythonw — שגיאות שקטות

`pythonw.exe` מסתיר SyntaxError — אפליקציה לא נפתחת ללא הודעה.
בדיקה: `python main.py` (לא pythonw) לפני הפצה.

---

## הפעלה

```
python D:\bridge-student\main.py
```
אסור להשתמש ב-`run.bat` עם נתיב עברי — cmd.exe לא מטפל בו.
