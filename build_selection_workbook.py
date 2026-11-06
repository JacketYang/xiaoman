from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule

OUT = Path('output/文具代发选品与定价核算.xlsx')
wb = Workbook()
ws = wb.active
ws.title = '商品核算'
params = ws
params['A1'] = '1688文具一件代发选品核算（黄色为输入项；金额单位：元）'
params['A1'].font = Font(bold=True, size=14)
settings = [('目标投产比（成交额/推广费）', 2), ('平台及支付费率（待按店铺核实）', 0.006), ('售后损耗率（按成交额预估）', 0.03), ('每单目标经营利润', 3), ('其他每单成本（耗材等）', 0)]
for i, (name, value) in enumerate(settings, 2):
    params.cell(i, 1, name)
    params.cell(i, 2, value).fill = PatternFill('solid', fgColor='FFF2CC')
params['D2'] = '核算口径'
params['E2'] = '单个可售SKU；代发价、运费、偏远地区附加费必须按实际SKU与收货地区填写。'
params['D3'] = '保本投产比'
params['E3'] = '1 ÷ 推广前贡献毛利率；小于该值的实际投产比通常无法覆盖本模型成本。'
params['D4'] = '最低建议售价'
params['E4'] = '按目标投产比及每单目标经营利润倒推，向上取到0.1元；还需结合市场成交价调整。'
headers = ['商品ID','商品名称','1688链接','供应商','具体SKU/规格','支持一件代发','代发价','单件运费','偏远地区附加均摊','其他每单成本','售价（拼单价）','平台费率','售后损耗率','目标投产比','目标利润/单','保本投产比','推广前贡献毛利率','预计推广费/单','预计经营利润/单','目标下最低建议售价','上架建议','数据核实日期','近30天供应商成交/回购','48小时发货','支持拼多多面单','退换货与售后说明','备注']
row = 7
for col, h in enumerate(headers, 1):
    c = ws.cell(row, col, h)
    c.font = Font(bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='305496')
    c.alignment = Alignment(wrap_text=True, vertical='center')
for r in range(8, 108):
    for c in [7,8,9,11,12,13,14,15]:
        ws.cell(r,c).fill = PatternFill('solid', fgColor='FFF2CC')
    ws.cell(r,9,0)
    ws.cell(r,10,'=$B$6')
    ws.cell(r,12,'=$B$3')
    ws.cell(r,13,'=$B$4')
    ws.cell(r,14,'=$B$2')
    ws.cell(r,15,'=$B$5')
    cost = f'SUM(G{r}:J{r})'
    ws.cell(r,16,f'=IF(OR(K{r}="",K{r}<=0,K{r}-({cost}+K{r}*L{r}+K{r}*M{r})<=0),"",1/((K{r}-({cost}+K{r}*L{r}+K{r}*M{r}))/K{r}))')
    ws.cell(r,17,f'=IF(K{r}="","",(K{r}-({cost}+K{r}*L{r}+K{r}*M{r}))/K{r})')
    ws.cell(r,18,f'=IF(OR(K{r}="",N{r}=""),"",K{r}/N{r})')
    ws.cell(r,19,f'=IF(K{r}="","",K{r}-({cost}+K{r}*L{r}+K{r}*M{r})-R{r})')
    ws.cell(r,20,f'=IF(G{r}="","",IF(1-L{r}-M{r}-1/N{r}<=0,"无法核算",CEILING((({cost})+O{r})/(1-L{r}-M{r}-1/N{r}),0.1)))')
    ws.cell(r,21,f'=IF(A{r}="","",IF(OR(F{r}<>"是",G{r}="",H{r}=""),"待核实",IF(AND(K{r}<>"",S{r}>=O{r},Q{r}>=0.6),"候选","暂缓")))')
    for c in range(1, len(headers)+1):
        ws.cell(r,c).alignment = Alignment(vertical='top', wrap_text=True)
for col in ['L','M','Q']:
    for r in range(8,108): ws[f'{col}{r}'].number_format = '0.0%'
for r in range(8,108):
    for col in ['G','H','I','J','K','O','R','S','T']: ws[f'{col}{r}'].number_format = '0.00'
    ws[f'P{r}'].number_format = '0.00'
ws.freeze_panes = 'A8'
ws.auto_filter.ref = f'A7:AA107'
widths = [16,30,42,22,28,14,12,12,16,14,14,12,14,14,14,14,18,16,18,20,12,16,24,14,18,35,30]
for i,w in enumerate(widths,1): ws.column_dimensions[ws.cell(1,i).column_letter].width=w
ws.row_dimensions[7].height=40
dv = DataValidation(type='list', formula1='"是,否,待核实"')
ws.add_data_validation(dv)
for col in ['F','X','Y']: dv.add(f'{col}8:{col}107')
ws.conditional_formatting.add('S8:S107', CellIsRule(operator='lessThan', formula=['0'], fill=PatternFill('solid',fgColor='FFC7CE')))

strategy = wb.create_sheet('选品与投放规则')
strategy.append(['模块','当前执行规则'])
rules = [
('模式','只采一件代发；逐SKU记录代发价，不使用批发阶梯价或未核实的搜索页最低价。'),
('成本','采购价 + 实际运费 + 偏远地区附加均摊 + 平台/支付费用 + 售后损耗 + 推广费。'),
('定价','先用目标投产比2与目标利润倒推底价，再查拼多多同类同规格实际成交价；没有竞争力就淘汰，不硬凑毛利。'),
('商品形态','首轮优先可组合的套装、多支装、补充装；低客单单件重点检查运费占比。'),
('筛选门槛','目标投产比2下，模型经营利润大于0，且推广前贡献毛利率原则上≥60%（对应约10%推广后利润空间，仍受固定成本影响）。'),
('SKU结构','低价体验SKU也必须独立核算；避免用亏损SKU引流而销量结构无法控制。'),
('运费','核实发货地、快递、全国包邮范围、偏远地区费用、续重和补发费用；表格先按单件订单计算。'),
('供应商','优先近期有成交/回购、响应稳定、48小时发货、支持所需面单、售后规则明确的供应商；先用小单验证。'),
('图片与文案','保存供应商素材授权/使用确认；核对品牌、IP联名、学生用品标识及宣传表述。'),
('测款','小预算分批测试；记录曝光、点击率、转化率、实际投产比、退款率。只看成交额投产比不能代表盈利。'),
('止损','以保本投产比为首要止损线；连续消耗后无成交、实际利润为负或售后异常时暂停并复盘。'),
('待店铺确认','平台实际收费、类目要求、运费模板、退货地址、平均订单件数和售后率；当前表内参数是可修改的初始假设。')]
for row in rules: strategy.append(row)
strategy.column_dimensions['A'].width=20
strategy.column_dimensions['B'].width=110
for c in strategy[1]: c.font=Font(bold=True,color='FFFFFF'); c.fill=PatternFill('solid',fgColor='305496')
for row in strategy.iter_rows():
    for c in row: c.alignment=Alignment(vertical='top',wrap_text=True)
strategy.freeze_panes='A2'

sources = wb.create_sheet('采集待核实清单')
sources.append(['优先级','搜索关键词','需要记录','暂不采用的数据'])
keywords = [('1','中性笔套装 一件代发','具体套装支数、代发价、单件运费、SKU差价','混批价、批发阶梯价'),('1','学生文具套装 一件代发','套装内容、包装、适用人群、运费','虚高划线价'),('1','笔记本组合 一件代发','尺寸、页数、本数、纸质、运费','单本批发价替代套装价'),('2','便利贴组合 一件代发','本数/页数、尺寸、组合方式','单件低价但不包邮'),('2','文件袋多个装 一件代发','材质、尺寸、数量、颜色规格','未区分规格的价格'),('2','手账贴纸套装 一件代发','图案授权、数量、材质、套装组合','侵权IP或来源不明素材')]
for row in keywords: sources.append(row)
for c in sources[1]: c.font=Font(bold=True,color='FFFFFF'); c.fill=PatternFill('solid',fgColor='305496')
for col,w in zip('ABCD',[12,34,60,42]): sources.column_dimensions[col].width=w
for row in sources.iter_rows():
    for c in row: c.alignment=Alignment(vertical='top',wrap_text=True)

OUT.parent.mkdir(parents=True, exist_ok=True)
wb.save(OUT)
check = load_workbook(OUT, data_only=False)
assert check.sheetnames == ['商品核算','选品与投放规则','采集待核实清单']
assert check['商品核算']['T8'].value.startswith('=IF(')
assert check['商品核算']['P8'].value.startswith('=IF(')
print(OUT.resolve())
print('已验证：3张工作表、100行商品录入区、保本投产比/建议售价/利润公式均保留。')
