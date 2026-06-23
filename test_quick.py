# -*- coding: utf-8 -*-
import sys, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine.rebid import opener_rebid

# N: J974 AQ Q108 A962 — 13 HCP, 4 spades, 2 hearts
n = ['JS','9S','7S','4S','AH','QH','QD','TD','8D','AC','9C','6C','2C']
bid, why = opener_rebid(n, '1♣', '1♥')
print(f'N rebid after 1C-1H: {bid}')
print(f'Why: {why}')
print('Expected: 1S')
