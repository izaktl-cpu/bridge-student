# bridge-audit — ביקורת מלאה של מערכת ההכרזה
> 🔍 **תוכן: מנהל הביקורת — טוען bridge-rules + bridge-code, בודק את ה-engine, מתקן שגיאות**

**תפקיד**: מנהל הביקורת. קורא את bridge-rules ו-bridge-code, בודק את קבצי ה-engine מול הכללים, ומתקן כל סטייה.

---

## שלב 1 — טען את מסמכי הידע

קרא את שני הקבצים הבאים לפני כל פעולה:
- `D:\bridge-student\.claude\commands\bridge-rules.md` — כללי ההכרזה
- `D:\bridge-student\.claude\commands\bridge-code.md` — הוראות קוד

---

## שלב 2 — קרא את קבצי ה-engine

```
D:\bridge-student\engine\opening.py
D:\bridge-student\engine\response.py
D:\bridge-student\engine\rebid.py
D:\bridge-student\engine\overcall.py
```

---

## שלב 3 — בדיקות מול bridge-rules

### opening.py — נקודות בדיקה:

| כלל | מה לבדוק בקוד |
|-----|--------------|
| סדר בדיקות | פרי-אמפט → Weak Two → Pass → 2♣ → 1NT → צבע |
| Weak Two | רק ♥/♠/♦ (לא ♣); 6–9 HCP; בדיוק 6 קלפים; 2+ מ-{A,K,Q,J} |
| 2♣ חזקה | ≥20 HCP (לא 19) |
| 1NT | 15–17 HCP מאוזן בלבד |
| 5-5 מינורים | 1♦ (גבוה) |
| 4-4 מינורים | 1♣ (נמוך) |
| 3-3 מינורים | 1♣ (נמוך) |

### response.py — נקודות בדיקה:

| כלל | מה לבדוק |
|-----|---------|
| respond_1nt | 0–7→Pass, 8–9→2NT, 10+→3NT |
| respond_major — תמיכה | 3+ קלפים + נק' חלוקה; 6-9→2M, 10-12→3M, 13+→4M |
| respond_major — up the line | אחרי 1♥: 4+♠→1♠ לפני NT |
| respond_minor — up the line | אחרי 1♣: 4+♦ עדיפות ראשונה (גם לפני מיגורים) |
| respond_minor — 4-4 מיגורים | 1♥ לפני 1♠ |
| respond_weak2 | 15+→4M, 12-14→3M (תמיכה); 16+ מאוזן→2NT (Ogust) |

### rebid.py — נקודות בדיקה:

| כלל | מה לבדוק |
|-----|---------|
| אחרי 1NT–2NT | 15→Pass, 16-17→3NT |
| אחרי תמיכה 2M | 12-14→Pass, 15-17→3M, 18+→4M |
| אחרי תמיכה 2m | 12-14→Pass, 15-17→3m, 18++עוצרים→3NT |
| אחרי לימיט 3M | 12-14→Pass, 15+→4M |
| אחרי לימיט 3m | 12-14→Pass, 15+→3NT |
| אחרי תגובת מיגור ממינור | 4+ תמיכה→2M/3M/4M לפי HCP |

### overcall.py — נקודות בדיקה:

| כלל | מה לבדוק |
|-----|---------|
| 1NT אוברקול | 15–18 HCP (לא 15–17!) מאוזן + כבלה |
| אוברקול רמה 1 | 9–16 HCP, 5+, ≥2 מכובדים |
| אוברקול רמה 2 | 12–16 HCP, 5+, ≥2 מכובדים |
| Takeout Double | 12+, שורטאז' ≤2, 3+ בשלושת האחרים |
| _suit_quality | A/K/Q=1 כל אחד; JT=1; T98=1; צריך ≥2 |

---

## שלב 4 — בדיקות מול bridge-code

- [ ] כל `CTkLabel` עם עברית+מספרים עטוף ב-`fix()`
- [ ] `set_instruction_table`: wraplength=220, מפריד=`.`
- [ ] כפתורי שיעורים: `text=fix(label)`
- [ ] אין קיצורי Ctrl+אות בודד

---

## שלב 5 — דיווח ותיקון

### פורמט דיווח:

```
## ממצאי ביקורת

### opening.py
✅ סדר בדיקות — תקין
❌ Weak Two: קוד בודק h <= 9, אבל הכלל הוא 6-9 HCP. [שורה X]
   תיקון: שנה `h <= 9` ל-`6 <= h <= 9`

### response.py
...
```

### תיקון:
- הצג את הממצאים לפני תיקון
- תקן רק לאחר אישור המשתמש (כלל: plan before executing)
- אחרי תיקון — שאל "תיקנתי?"

---

## הרצה מהירה

להרצת הביקורת כעת — הפעל:
```
/bridge-audit
```
Claude יטען את bridge-rules + bridge-code, יקרא את ה-engine, ידווח על ממצאים.
