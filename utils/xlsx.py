import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

async def create_report_excel(name: str, rows: list[list]) -> str:
    headers = [
        "usertag", "цена", "во_сколько_начали_идти_заявки", "актуал_заявок",
        "цена_заявки", "пдп_осталось", "цена_пдп_за_72ч", "процент_отписок",
        "пришло_за_10_мин", "пришло_за_28_мин", "пришло_за_60_мин",
        "пришло_за_24ч", "пришло_за_48ч", "пришло_за_72ч"
    ]
    header_titles = {
        "usertag": "@usertag",
        "цена": "цена",
        "во_сколько_начали_идти_заявки": "Начало",
        "актуал_заявок": "Актуал. заявки",
        "цена_заявки": "Цена заявки",
        "пдп_осталось": "ПДП",
        "цена_пдп_за_72ч": "Цена ПДП",
        "процент_отписок": "% отписок",
        "пришло_за_10_мин": "+ За 10 мин",
        "пришло_за_28_мин": "+ За 28 мин",
        "пришло_за_60_мин": "+ За 60 мин",
        "пришло_за_24ч": "+ За 24ч",
        "пришло_за_48ч": "+ За 48ч",
        "пришло_за_72ч": "+ За 72 ч"
    }
    column_widths = {
        "usertag": 22,
        "цена": 17,
        "во_сколько_начали_идти_заявки": 25,
        "актуал_заявок": 18,
        "цена_заявки": 16,
        "пдп_осталось": 15,
        "цена_пдп_за_72ч": 18,
        "процент_отписок": 18,
        "пришло_за_10_мин": 25,
        "пришло_за_28_мин": 25,
        "пришло_за_60_мин": 25,
        "пришло_за_24ч": 25,
        "пришло_за_48ч": 25,
        "пришло_за_72ч": 25
    }

    os.makedirs('files', exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Отчет"

    header_font = Font(size=14, bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4F81BD")
    cell_font = Font(size=12)
    cell_fill = PatternFill("solid", fgColor="DCE6F1")
    center_align = Alignment(horizontal="center", vertical="center")
    border_side = Side(border_style="thin", color="000000")
    border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)

    # Записываем заголовки
    for col_num, key in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header_titles[key])
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border
        ws.column_dimensions[get_column_letter(col_num)].width = column_widths.get(key, 15)

    # Записываем данные с вычислениями
    for row_idx, row_data in enumerate(rows, start=2):
        usertag = row_data[0]
        price = row_data[1]
        start_time = row_data[2]
        requests = row_data[3]
        joins = row_data[4]
        m10 = row_data[5]
        m28 = row_data[6]
        m60 = row_data[7]
        m24 = row_data[8]
        m48 = row_data[9]
        m72 = row_data[10]
        m10_j = row_data[11]
        m28_j = row_data[12]
        m60_j = row_data[13]
        m24_j = row_data[14]
        m48_j = row_data[15]
        m72_j = row_data[16]

        price_per_request = price / requests if requests else 0
        price_per_join_72 = price / joins if joins else 0
        unsub_percent = round(int(round((requests - joins) / requests, 4))*4, 2) if requests else 0

        values = [
            usertag, price, start_time, requests,
            round(price_per_request, 2), joins, round(price_per_join_72, 2), unsub_percent,
            f'{m10} з / {m10_j} пдп', f'{m28} з / {m28_j} пдп', f'{m60} з / {m60_j} пдп',
            f'{m24} з / {m24_j} пдп', f'{m48} з / {m48_j} пдп', f'{m72} з / {m72_j} пдп'
        ]

        for col_num, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_num, value=value)
            cell.font = cell_font
            cell.fill = cell_fill
            cell.alignment = center_align
            cell.border = border

    filepath = f"files/{name}.xlsx"
    wb.save(filepath)
    return filepath

