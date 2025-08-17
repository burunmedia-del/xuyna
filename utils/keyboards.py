from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def build_privet_keyboard(text: str, link: str, demo: bool = False, privet_id=None, pull_id=None):
    kb = InlineKeyboardBuilder()

    text = eval(text)
    for i in text:
        temp_keys = []
        for x in i:
            temp_keys.append(InlineKeyboardButton(text=x, url=link))
        kb.row(*temp_keys, width=len(i))
    if demo:
        kb.row(InlineKeyboardButton(text='Удалить приветку', callback_data=f'DELPRIVET_{privet_id}_{pull_id}'), width=1)
        kb.row(InlineKeyboardButton(text='Назад ◀', callback_data='BACK'), width=1)
    return kb.as_markup()

def build_last_privet_keyboard(button_data: list, demo: bool = False):
    kb = InlineKeyboardBuilder()
    for row in button_data:
        buttons = [
            InlineKeyboardButton(text=text, url=url)
            for text, url in row
        ]
        kb.row(*buttons, width=len(buttons))
    if demo:
        kb.row(InlineKeyboardButton(text='Назад ◀', callback_data='BACK'), width=1)
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


def parse_last_privet_message(s):
    s = s.strip()
    lines = [line.strip() for line in s.split('\n')]

    if '-' not in lines:
        return [s, []]

    split_index = lines.index('-')
    header = '\n'.join(lines[:split_index]).strip()
    button_lines = lines[split_index + 1:]

    keyboard = []

    for line in button_lines:
        if not line.strip():
            continue
        row = []
        for btn in line.split('|'):
            btn = btn.strip()
            if '*' in btn:
                text, url = btn.split('*', 1)
                row.append([text.strip(), url.strip()])
        if row:
            keyboard.append(row)

    return [header, keyboard]
