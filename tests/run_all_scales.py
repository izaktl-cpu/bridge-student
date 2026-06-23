"""
הרצת כל בדיקות הסקייל — שיעורים 1-12.
שימוש: python tests/run_all_scales.py [n]
n = מספר ידיות לכל שיעור (ברירת מחדל 2000)
"""
import sys, os, importlib
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_SCALES = [
    ('שיעור 1  — 1NT תגובה',        'scale_lesson1'),
    ('שיעור 2  — מיגור N פותח',      'scale_lesson2'),
    ('שיעור 3  — מיגור S פותח',      'scale_lesson3'),
    ('שיעור 4  — סטיימן 1NT',        'scale_lesson4'),
    ('שיעור 5  — טרנספר 1NT',        'scale_lesson5'),
    ('שיעור 6  — 2NT (סטיימן/טרנ)', 'scale_lesson6'),
    ('שיעור 7  — 2♣ חזקה',           'scale_lesson7'),
    ('שיעורים 8-9 — סלמים',          'scale_slams'),
    ('שיעור 10 — פתיחה חלשה 2M',    'scale_weak2'),
    ('שיעור 11 — אוגוסט',            'scale_ogust'),
    ('שיעור 12 — אוברקול',           'scale_overcall'),
    ('שיעור 3  — אוטו (MockApp)',    'scale_auto_lesson3'),
]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    total_errors = 0

    print('=' * 50)
    print(f'  סקייל כולל — {n} ידיות לשיעור')
    print('=' * 50)

    tests_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, tests_dir)

    for label, module_name in _SCALES:
        print(f'\n▶ {label}')
        mod = importlib.import_module(module_name)
        # כל מודול מדפיס בעצמו — קורא ל-run()
        mod.run(n)

    print('=' * 50)
    print('  סיום')
    print('=' * 50)


if __name__ == '__main__':
    main()
