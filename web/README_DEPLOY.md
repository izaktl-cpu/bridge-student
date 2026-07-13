# פריסה ל-Render — עוזר ברידג' לתלמיד (web)

מדריך צעד-אחר-צעד. כל מה שצריך כבר מוכן בקוד.

## מה כבר מוכן ✅

- `web/server.py` — שרת FastAPI שעוטף את ה-engine והשיעורים
- `web/requirements.txt` — תלויות web בלבד (בלי customtkinter)
- `render.yaml` — הגדרת הפריסה (Render קורא אותו אוטומטית)
- `/health` — נקודת keep-alive ל-UptimeRobot
- כפתור "נתקעתי" — שומר דיווח ושולח מייל (כשיוגדר מפתח)

## הרצה מקומית (לבדיקה)

```
cd D:\bridge-student
python -m uvicorn web.server:app --host 0.0.0.0 --port 8111
```
פותחים http://127.0.0.1:8111

## פריסה ל-Render — צעדים

1. **ודא שהקוד ב-GitHub** (bridge-student כבר מגובה שם).
   אם יש שינויים חדשים: `git add -A && git commit -m "web app" && git push`
2. היכנס ל-**render.com** → התחבר עם GitHub → **New → Blueprint**.
3. בחר את הריפו `bridge-student`. Render יזהה את `render.yaml` לבד.
4. לחץ **Apply**. הבנייה לוקחת דקה-שתיים.
5. בסיום מקבלים כתובת כמו `https://bridge-student.onrender.com` — זה הלינק לתלמידים.

## הפעלת מיילים של "נתקעתי" (אופציונלי, מומלץ)

1. הירשם ב-**resend.com** (חינם, 3000 מיילים/חודש) → צור **API Key**.
2. ב-Render: **Dashboard → השירות → Environment** → הוסף:
   - `RESEND_API_KEY` = המפתח מ-Resend
   - `REPORT_EMAIL` = izaktl@gmail.com (כבר ברירת מחדל)
   - `RESEND_FROM` = כתובת שולח (בהתחלה אפשר `onboarding@resend.dev`)
3. שמור — Render יפעיל מחדש. מעכשיו כל "נתקעתי" נשלח למייל שלך.

בלי מפתח — הדיווחים עדיין נשמרים בקובץ `web/reports/reports.jsonl` על השרת
(אבל נמחק בפריסה מחדש; המייל הוא הערוץ המתמיד).

## keep-alive (שלא יירדם)

1. הירשם ב-**uptimerobot.com** (חינם).
2. **Add Monitor** → HTTP(s) → כתובת: `https://<your-app>.onrender.com/health`
3. Interval: כל 5 דקות. זהו — האפליקציה תישאר ערה.

## הערות

- ה-tier החינמי מספיק ל-100–200 תלמידים שמתרגלים לבד (לא בו-זמנית).
- מצב סשן נשמר בזיכרון — נמחק בשינה/פריסה. יד באמצע תלך לאיבוד, אבל דיווחים
  (במייל) נשמרים. מקובל לפיילוט.
