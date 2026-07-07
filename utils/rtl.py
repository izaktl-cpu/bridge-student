import re

_RLE = '‫'  # Right-to-Left Embedding
_LRO = '‭'  # Left-to-Right Override
_PDF = '‬'  # Pop Directional Formatting
_RLM = '‏'  # Right-to-Left Mark
_LRM = '‎'  # Left-to-Right Mark

# מספרים בלבד (כולל טווחים ו-+ נגרר), לעטיפה ב-LRM בתוך שורה בעברית טבעית
_NUM_RE = re.compile(r'\d+(?:[+\-=]\d+)*\+?')

_LTR_RE = re.compile(
    r'[1-7](?:NT|[♣♦♥♠X])'
    r'|[♣♦♥♠]'
    r'|[A-Za-z][A-Za-z0-9]*'
    r'|\d+(?:[+\-=]\d+)*\+?'
)

# תווים שאחריהם הגיוני לשבור שורה
_BREAK_AFTER = re.compile(r'([.!?,])\s+')


def _wrap_line(line, max_words=4):
    # פיצול ב-": " (כותרת: ערך → שורות נפרדות)
    line = re.sub(r':\s+', '\n', line)
    # פיצול בסוף משפט
    broken = _BREAK_AFTER.sub(lambda m: m.group(1) + '\n', line).strip()
    result = []
    for part in broken.split('\n'):
        words = part.split()
        if not words:
            continue
        for i in range(0, len(words), max_words):
            result.append(' '.join(words[i:i + max_words]))
    return '\n'.join(result)


def wrap(text, max_words=4):
    if not text:
        return text
    return '\n'.join(_wrap_line(line, max_words) for line in text.split('\n'))


def _protect_ltr(line):
    return _LTR_RE.sub(lambda m: _LRO + m.group() + _PDF, line)


def fix(text):
    if not text:
        return text
    return '\n'.join(
        _RLE + _protect_ltr(line) + _PDF
        for line in text.split('\n')
    )


def fix_num(text):
    """עברית טבעית לשורות טבלה: בסיס RTL (RLM) + עטיפת מספרים ב-LRM
    כדי שמספרים/+/טווחים יישארו שלמים מבלי להפוך את כיוון השורה."""
    if not text:
        return text
    return '\n'.join(
        _RLM + _NUM_RE.sub(lambda m: _LRM + m.group() + _LRM, line)
        for line in text.split('\n')
    )
