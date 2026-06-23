"""
scale_check_hebrew.py — בדיקת RTL בקבצי UI, engine ו-lessons.

בדיקות:
1. CTkLabel עם עברית+LTR ישיר ללא fix() — קבצי ui/
2. CTkLabel עם עברית ללא justify= — קבצי ui/
3. מחרוזות why (return tuple) עם עברית+מספר/אנגלית צמודים — engine/ + lessons/
4. fix() על כל מחרוזות why — מספרים עטופים ב-LRE..PDF

הרצה: python tests/scale_check_hebrew.py
"""
import sys, os, re, ast
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_LRE = '‪'
_PDF = '‬'
_HAS_HEBREW  = re.compile(r'[א-תװ-״יִ-ﭏ]')
_HAS_LTR     = re.compile(r'[A-Za-z0-9]')
_SUIT        = re.compile(r'[♣♦♥♠]')
# מספר/אנגלית צמוד לעברית ללא רווח
_ADJACENT    = re.compile(
    r'[א-תװ-״יִ-ﭏ][0-9A-Za-z♣♦♥♠]'
    r'|[0-9A-Za-z♣♦♥♠][א-תװ-״יִ-ﭏ]'
)
_CTKLABEL    = re.compile(r'CTkLabel\s*\(')
_CONFIGURE   = re.compile(r'\.configure\s*\(')
_TEXT_ARG    = re.compile(r'\btext\s*=\s*(["\'])(.+?)\1')
_FIX_CALL    = re.compile(r'\bfix\s*\(')
_JUSTIFY     = re.compile(r'justify\s*=')


def _files_in(subdir):
    d = os.path.join(ROOT, subdir)
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in os.listdir(d) if f.endswith('.py')]


# ── בדיקת קבצי UI ────────────────────────────────────────────────────────────

def _check_ui_file(filepath):
    issues = []
    with open(filepath, encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if _CTKLABEL.search(line) or _CONFIGURE.search(line):
            block = ''.join(lines[i:i+8])
            m = _TEXT_ARG.search(block)
            if m:
                val = m.group(2)
                if _HAS_HEBREW.search(val) and _HAS_LTR.search(val):
                    if not _FIX_CALL.search(block):
                        issues.append((i+1, 'עברית+LTR ללא fix()', f'text="{val[:60]}"'))
            if _CTKLABEL.search(line):
                if _HAS_HEBREW.search(block) and not _JUSTIFY.search(block):
                    issues.append((i+1, 'CTkLabel עם עברית ללא justify=', line.rstrip()[:80]))
    return issues


# ── בדיקת קבצי engine / lessons ──────────────────────────────────────────────

def _extract_why_strings(filepath):
    """מחזיר רשימת (lineno, string) של מחרוזות why מ-return (bid, why)."""
    results = []
    with open(filepath, encoding='utf-8') as f:
        src = f.read()
    try:
        tree = ast.parse(src, filepath)
    except SyntaxError:
        return results

    for node in ast.walk(tree):
        if not isinstance(node, ast.Return):
            continue
        val = node.value
        # return (bid, why)  או  return bid, why
        if isinstance(val, ast.Tuple) and len(val.elts) == 2:
            why_node = val.elts[1]
            text = _eval_str(why_node)
            if text and _HAS_HEBREW.search(text):
                results.append((node.lineno, text))
        # set_feedback / set_instruction / _finish עם ליטרל ישיר
        # נבדוק גם f-strings בשיחות
    return results


def _eval_str(node):
    """מחזיר את הטקסט אם הצומת הוא Constant/JoinedStr, אחרת None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        # f-string: מרכיב את הטקסט הסטטי בלבד
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append(v.value)
            else:
                parts.append('X')  # placeholder ל-{expr}
        return ''.join(parts)
    return None


def _check_engine_file(filepath):
    issues = []
    strings = _extract_why_strings(filepath)
    for lineno, text in strings:
        if not (_HAS_HEBREW.search(text) and (_HAS_LTR.search(text) or _SUIT.search(text))):
            continue
        # בדיקה 1: צמידות ללא רווח
        if _ADJACENT.search(text):
            issues.append((lineno, 'עברית+LTR צמודים ללא רווח', text[:70]))
        # בדיקה 2: אחרי fix() — בדוק שמספרים עטופים
        from utils.rtl import fix
        fixed = fix(text)
        # חפש מספר ללא LRE לפניו
        for m in re.finditer(r'\d+', fixed):
            start = m.start()
            if start == 0 or fixed[start-1] != _LRE:
                # בדוק אם קדמה לו עברית (דורש עטיפה)
                before = fixed[max(0,start-4):start]
                if _HAS_HEBREW.search(before):
                    issues.append((lineno, 'מספר לא עטוף ב-fix()', text[:70]))
                    break
    return issues


# ── ריצה ─────────────────────────────────────────────────────────────────────

def run():
    sep = '─' * 60
    print(sep)
    print('  scale_check_hebrew — בדיקת RTL: UI + engine + lessons')
    print(sep)

    all_issues = []

    # UI
    for fp in sorted(_files_in('ui')):
        iss = _check_ui_file(fp)
        if iss:
            all_issues.append((os.path.relpath(fp, ROOT), iss))

    # engine + lessons
    for subdir in ('engine', 'lessons'):
        for fp in sorted(_files_in(subdir)):
            iss = _check_engine_file(fp)
            if iss:
                all_issues.append((os.path.relpath(fp, ROOT), iss))

    if not all_issues:
        print('  ✓ אין בעיות RTL')
    else:
        total = sum(len(v) for _, v in all_issues)
        print(f'  ✗ נמצאו {total} בעיות:\n')
        for fname, issues in all_issues:
            print(f'  {fname}')
            for lineno, kind, text in issues:
                print(f'    שורה {lineno:4d}: {kind}')
                print(f'             {text}')
            print()

    print(sep)


if __name__ == '__main__':
    run()
