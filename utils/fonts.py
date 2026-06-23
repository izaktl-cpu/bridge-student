import customtkinter as ctk

_FAMILY = 'Gisha'


def F(size: int) -> ctk.CTkFont:
    return ctk.CTkFont(family=_FAMILY, size=size)


def FB(size: int) -> ctk.CTkFont:
    return ctk.CTkFont(family=_FAMILY, size=size, weight='bold')
