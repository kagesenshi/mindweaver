import reflex as rx 

def default(el, default):
    return rx.cond(el, el, default)