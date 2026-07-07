import customtkinter as ctk

_FAMILY = 'Gisha'
_FEEDBACK_FAMILY = 'Gisha'


def F(size: int) -> ctk.CTkFont:
    return ctk.CTkFont(family=_FAMILY, size=size)


def FB(size: int) -> ctk.CTkFont:
    return ctk.CTkFont(family=_FAMILY, size=size, weight='bold')


def FB_FEEDBACK(size: int) -> ctk.CTkFont:
    """פונט כתב-יד — רק להסברים/משוב אחרי ההכרזה."""
    return ctk.CTkFont(family=_FEEDBACK_FAMILY, size=size, weight='bold')
