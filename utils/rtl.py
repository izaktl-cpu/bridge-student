import re

_RLE = '‫'  # Right-to-Left Embedding
_LRE = '‪'  # Left-to-Right Embedding
_PDF = '‬'  # Pop Directional Formatting
_RLM = '‏'  # Right-to-Left Mark

_LTR_RE = re.compile(
    r'[1-7](?:NT|[♣♦♥♠X])'
    r'|[♣♦♥♠]'
    r'|[A-Za-z][A-Za-z0-9]*'
    r'|\d+(?:[+\-=]\d+)*'
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
    return _LTR_RE.sub(lambda m: _LRE + m.group() + _PDF + _RLM, line)


def fix(text):
    if not text:
        return text
    return '\n'.join(
        _RLE + _RLM + _protect_ltr(line) + _RLM + _PDF
        for line in text.split('\n')
    )
