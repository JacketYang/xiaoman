# -*- coding: utf-8 -*-
import json
import os

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

INPUT = r"D:\ISO\pxx\yyima_clean.json"
OUTPUT = r"D:\ISO\pxx\firefighter_exam.xlsx"

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

wb = Workbook()
# remove default sheet
wb.remove(wb.active)

header_font = Font(bold=True, size=11, color="FFFFFF")
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
cell_align = Alignment(vertical="top", wrap_text=True)
thin_border = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="thin", color="D9D9D9"),
)

headers = ["题号", "题目", "选项A", "选项B", "选项C", "选项D", "选项E", "答案", "解析"]
col_widths = [6, 50, 20, 20, 20, 20, 20, 8, 50]

sheet_map = [
    ("判断题", data.get("pdt", [])),
    ("多选题", data.get("mul", [])),
    ("单选题", data.get("sin", [])),
]

for sheet_name, items in sheet_map:
    ws = wb.create_sheet(title=sheet_name)
    # headers
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border
    # column widths
    for col_idx, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = w
    # data rows
    for row_idx, item in enumerate(items, 2):
        values = [
            item.get("n", ""),
            item.get("q", ""),
            item.get("a", ""),
            item.get("b", ""),
            item.get("c", ""),
            item.get("d", ""),
            item.get("e", ""),
            item.get("ans", ""),
            item.get("ana", ""),
        ]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.alignment = cell_align
            cell.border = thin_border
    # freeze header row
    ws.freeze_panes = "A2"
    # auto filter
    ws.auto_filter.ref = f"A1:I{len(items)+1}"
    print(f"  {sheet_name}: {len(items)} rows written")

wb.save(OUTPUT)
file_size = os.path.getsize(OUTPUT)
print(f"\nSaved: {OUTPUT}")
print(f"Size: {file_size} bytes ({file_size/1024:.1f} KB)")

# compute MD5
import hashlib
with open(OUTPUT, "rb") as f:
    md5 = hashlib.md5(f.read()).hexdigest()
print(f"MD5: {md5}")
