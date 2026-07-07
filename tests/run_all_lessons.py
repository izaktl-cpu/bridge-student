"""
run_all_lessons.py — מריץ את כל בודקי השיעורים ברצף ומדפיס טבלת סיכום.
כל בודק נוהג את השיעור על תרחישים/חלוקות וסורק את הפידבק להפרות סקייל
(טעית / מקף ארוך / סימן קריאה / נקודתיים).

הרצה:
    cd D:\\bridge-student
    set PYTHONIOENCODING=utf-8
    python tests\\run_all_lessons.py
"""
import sys, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

# (מספר שיעור, שם, קובץ בודק)
RUNNERS = [
    ('9',  'סלם בצבע',   'run_lesson9.py'),
    ('10', 'Weak Two',   'run_lesson10.py'),
    ('11', 'Ogust',      'run_lesson11.py'),
    ('12', 'אוברקול',    'run_lesson12.py'),
    ('13', 'דבל להוצאה', 'run_lesson13.py'),
    ('14', 'נגטיב דבל',  'run_lesson14.py'),
    ('15', 'NT במינור',  'run_lesson15.py'),
]

# סימני הצלחה שהבודקים מדפיסים
_OK_MARKS = ('✓ כל', '✓ אין הפרות')


def run_one(fname):
    path = os.path.join(HERE, fname)
    if not os.path.exists(path):
        return None, 'קובץ חסר'
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    try:
        r = subprocess.run([PY, path], capture_output=True, text=True,
                           encoding='utf-8', env=env, timeout=180,
                           cwd=os.path.dirname(HERE))
    except subprocess.TimeoutExpired:
        return False, 'timeout'
    out = (r.stdout or '') + (r.stderr or '')
    ok = any(m in out for m in _OK_MARKS) and r.returncode == 0
    # שורת הסיכום האחרונה
    last = ''
    for line in out.splitlines():
        if '✓' in line or '✗' in line:
            last = line.strip()
    return ok, last


def main():
    print('=' * 60)
    print('בדיקת כל השיעורים (9–15)')
    print('=' * 60)
    all_ok = True
    for num, name, fname in RUNNERS:
        ok, note = run_one(fname)
        mark = '✓' if ok else '✗'
        if ok is None:
            mark = '—'
            all_ok = False
        elif not ok:
            all_ok = False
        print(f'  שיעור {num:<3} {name:<12} {mark}   {note}')
    print('=' * 60)
    print('✓ כל השיעורים עברו' if all_ok else '✗ יש שיעורים שנכשלו — בדוק למעלה')
    print('=' * 60)
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
