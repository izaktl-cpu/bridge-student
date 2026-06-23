from engine.scoring import hcp, is_balanced, distribution, suit_len, longest_suit

# ─── North responds to South's 1NT (Acol: 15-17 balanced) ───────────────────

def north_respond_to_1nt(north_hand):
    h = hcp(north_hand)
    if h <= 7:
        return 'Pass', f'לצפון {h} נקודות גבוהות, מכריזים פס'
    elif h <= 9:
        return '2NT', f'לצפון {h} נקודות גבוהות, מזמין'
    else:
        return '3NT', f'לצפון {h} נקודות גבוהות, משחק מלא'

# ─── South rebids after North's 2NT ─────────────────────────────────────────

def south_rebid_after_2nt(south_hand):
    h = hcp(south_hand)
    if h <= 15:
        return 'Pass', f'לדרום {h} נקודות + 2NT מצפון (8-9) — סה״כ 23-24, לא מספיק למשחק מלא'
    else:
        return '3NT', f'לדרום {h} נקודות + 2NT מצפון (8-9) — סה״כ 24-26, משחק מלא'
