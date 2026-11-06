import json
from pathlib import Path
from openpyxl import load_workbook

source = Path('output/文具代发选品与定价核算.xlsx')
out = Path('output/文具代发首批候选核算_2026-10-26.xlsx')
items = json.loads(Path('data/candidate-products.json').read_text(encoding='utf-8'))
wb = load_workbook(source)
ws = wb['商品核算']
for r, item in enumerate(items, 8):
    values = {
        1:item['id'], 2:item['title'], 3:f"https://detail.1688.com/offer/{item['id']}.html",
        4:item['supplier'], 5:item['sku'], 6:'是', 7:item['cost'], 8:item['shipping'],
        9:0, 11:item['price'], 22:'2026-10-26', 23:item['supplierMetrics'],
        24:item['shipping48'], 25:item['pddShippingLabel'], 26:item['afterSales'],27:item['note']
    }
    for c, value in values.items(): ws.cell(r,c,value)
    ws.cell(r,3).hyperlink = ws.cell(r,3).value
    ws.cell(r,3).style = 'Hyperlink'
wb.save(out)
check=load_workbook(out,data_only=False)
assert check['商品核算']['A8'].value=='827560431252'
assert check['商品核算']['G12'].value==6.89
assert check['商品核算']['P8'].data_type=='f'
print(out.resolve())
print(f'已写入并重新验证 {len(items)} 个真实1688候选；公式保留，待重算。')
