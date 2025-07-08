from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def build_privet_keyboard(text: str, link: str):
    kb = InlineKeyboardBuilder()
    text = eval(text)
    for i in text:
        print(i)
        for x in i:
            kb.row(InlineKeyboardButton(text=x, url=link), width=len(i))
    return kb.as_markup()


def parse_message(s):
    s = s.strip()
    if '-' in s:
        t, k = s.split('-', 1)
    else:
        return [s.strip(), []]
    t = t.strip()
    rows = [r.strip() for r in k.strip().split('\n') if r.strip()]
    kb = [r.split('|') for r in rows]
    kb = [[b.strip() for b in row if b.strip()] for row in kb if any(b.strip() for b in row)]
    return [t, kb]