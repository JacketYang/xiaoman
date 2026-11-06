import json,re,math
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.formatting.rule import CellIsRule

search=json.loads(Path('data/large-search-pool.json').read_text(encoding='utf-8'))
new=json.loads(Path('data/large-detail-pages.json').read_text(encoding='utf-8'))
old=json.loads(Path('data/expanded-offers.json').read_text(encoding='utf-8'))
byid={}
for item in old+new:
 if 'category' not in item:item['category']=item.get('query','').split()[0]
 if 'category'=='笔类':item['category']='笔类'
 elif '作业本' in item['category']:item['category']='作业本'
 elif '笔记本' in item['category']:item['category']='笔记本'
 elif '便利贴' in item['category']:item['category']='便利贴'
 elif '文件袋' in item['category']:item['category']='文件袋'
 elif '笔袋' in item['category']:item['category']='笔袋'
 elif '铅笔' in item['category']:item['category']='铅笔'
 elif '套尺' in item['category']:item['category']='套尺'
 elif '橡皮擦' in item['category']:item['category']='橡皮擦'
 elif '荧光笔' in item['category']:item['category']='荧光笔'
 elif '文具盒' in item['category']:item['category']='文具盒'
 byid[item['id']]=item
ip_re=re.compile(r'宝可梦|Pokémon|漫威|迪士尼|三丽鸥|奥特曼|卡皮巴拉|库洛米|玉桂狗',re.I)
count_words=re.compile(r'\d+\s*(支|本|张|块|个|件套|色|页|贴)|四件套|八件套|整盒|套装|组合')
def value(body,pattern):
 m=re.search(pattern,body);return m.group(1).strip() if m else ''
def section(body,start,end):
 if start not in body:return ''
 return body.split(start,1)[1].split(end,1)[0].strip()
def form(category,title,attributes):
 if category=='笔类':
  if '替芯' in title and not re.search(r'\d+支笔|送\d+支笔|成品笔',title):return '仅替芯'
  if re.search(r'替芯|笔芯',title):return '笔＋替芯组合/待核实'
  return '成品笔/套装'
 return '仅替芯' if category=='替芯' else category

def parse(item):
 body=item.get('body','');title=item.get('title','').replace(' - 阿里巴巴','');category=item['category']
 supplier=body.split('\n')[0] if body else ''
 dropship=section(body,'代发下单','官方仓退货') if '官方仓退货' in body.split('代发下单')[-1] else section(body,'代发下单','商家代发热度')
 if not dropship:dropship=section(body,'代发下单','铺货素材预览')
 prices=re.findall(r'￥\s*\n?([\d.]+)',dropship)
 cost=float(prices[0]) if prices else None
 one_free='1件包邮' in dropship
 shipping_text=value(body,r'运费¥([\d.]+)起')
 shipping=0 if one_free else (float(shipping_text) if shipping_text else None)
 min_unit=value(body,r'1(盒|套|支|本|件|个|包|盒)起批')
 perf=value(body,r'综合履约率\n([\d.]+)%');returning=value(body,r'店铺回头率\n([\d.]+)%')
 attrs=section(body,'商品属性\n','包装信息')
 sku=''
 for marker in ['\n笔芯颜色\n','\n封面颜色\n','\n规格\n','\n颜色\n','\n颜色分类\n','\n款式\n','\n尺寸\n']:
  if marker in body:
   sku=body.split(marker,1)[1].split('立即下单',1)[0].strip();break
 sku=re.sub(r'加图加字[\s\S]*$','',sku).strip()
 reasons=[]
 if not body:reasons.append('详情读取失败')
 if not dropship or cost is None:reasons.append('无明确单件代发价格')
 if shipping is None:reasons.append('单件运费未确认')
 if not sku:reasons.append('SKU区域未识别')
 if not min_unit:reasons.append('起订计价单位未识别')
 if ip_re.search(title+attrs):reasons.append('IP或授权信息需单独核验')
 if re.search(r'定制|盲盒',title):reasons.append('定制或盲盒不纳入首轮')
 if category in ['笔类','替芯','作业本','笔记本','便利贴','文件袋','铅笔','橡皮擦','荧光笔','书皮','便签本'] and not count_words.search(title+sku):
  reasons.append('数量或套装规格不明确')
 if re.search(r'单个价|单支价|单块价|单本价',sku):
  reasons.append('SKU为单件价，不能直接当整盒/套装成本')
 if re.search(r'\d+\s*(支|块|本|张|个)\s*/\s*盒',title+sku) and not re.search(r'整盒|盒装|一套|套装',title+sku):
  reasons.append('标题盒装数量未确认对应售卖单位')
 if re.search(r'起批|≥\d+件',dropship) and '1件' not in dropship:
  reasons.append('代发并非单件起发')
 if perf and float(perf)<90:reasons.append('供应商综合履约率低于90%')
 if returning and float(returning)<40:reasons.append('供应商回头率低于40%')
 if cost is not None and cost>50:reasons.append('单件代发价超过首轮50元上限')
 return {'id':item['id'],'category':category,'form':form(category,title,attrs),'title':title,'supplier':supplier,'url':f"https://detail.1688.com/offer/{item['id']}.html",'cost':cost,'shipping':shipping,'landed':cost+shipping if cost is not None and shipping is not None else None,'minUnit':min_unit,'perf':float(perf) if perf else None,'returning':float(returning) if returning else None,'dropship':dropship,'sku':sku,'attributes':attrs,'status':'待核验' if reasons else '待逐SKU复核（未完成选品）','reason':'；'.join(reasons)}
parsed=[parse(item) for item in byid.values() if 'category' in item]
for row in parsed:
 if row['landed'] is not None:row['minPrice']=math.ceil((row['landed']+3)/(1-.006-.03-.5)*10)/10
 else:row['minPrice']=None
passed=[r for r in parsed if r['status']=='待逐SKU复核（未完成选品）']
# More data always helps, but no unverified row is promoted to a listing candidate.
wb=Workbook();summary=wb.active;summary.title='筛选漏斗'
summary.append(['层级','数量','口径'])
summary.append(['搜索候选（去重）',len(search),'20个文具搜索词，商品ID去重；不代表合格品'])
summary.append(['详情页已读取',len(parsed),'历史扩展与本轮详情页合并去重'])
summary.append(['待逐SKU复核',len(passed),'自动规则未排除；尚未选定SKU，未完成选品，不可上架'])
summary.append(['规格/代发/履约待核验',len(parsed)-len(passed),'每一行保留具体原因'])
summary.append(['消费端同规格核价',0,'消费者端尚未登录，不虚构市场价格'])
summary.append(['最终可上架',0,'需完成消费端比价、供应商面单与素材确认、店铺类目核对'])
for c in summary[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='305496')
summary.column_dimensions['A'].width=28;summary.column_dimensions['B'].width=15;summary.column_dimensions['C'].width=100
for row in summary.iter_rows():
 for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
ws=wb.create_sheet('详情筛选')
headers=['商品ID','细分类目','商品形态','商品名称','供应商','1688链接','代发区首价（元）','单件运费（元）','到岸成本（待选SKU复核）','起订单位','履约率%','回头率%','筛选状态','原因','目标投产比2最低售价（暂算）','代发区原文','SKU区域原文','商品属性']
ws.append(headers)
for r in parsed:ws.append([r[k] for k in ['id','category','form','title','supplier','url','cost','shipping','landed','minUnit','perf','returning','status','reason','minPrice','dropship','sku','attributes']])
for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='305496')
for row in range(2,ws.max_row+1):
 ws.cell(row,6).hyperlink=ws.cell(row,6).value;ws.cell(row,6).style='Hyperlink'
 for col in range(1,ws.max_column+1):ws.cell(row,col).alignment=Alignment(vertical='top',wrap_text=True)
for i,w in enumerate([16,14,22,48,28,42,18,15,20,12,12,12,26,45,22,26,70,70],1):ws.column_dimensions[ws.cell(1,i).column_letter].width=w
ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
raw=wb.create_sheet('全部搜索候选');raw.append(['商品ID','细分类目','搜索词','标题','搜索卡片原文','链接','标题初筛排除原因'])
for r in search:raw.append([r['id'],r['category'],r['query'],r['title'],r['card'],r['url'],r['initialReject']])
for c in raw[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='305496')
for i,w in enumerate([16,14,38,55,75,42,32],1):raw.column_dimensions[raw.cell(1,i).column_letter].width=w
for row in raw.iter_rows():
 for c in row:c.alignment=Alignment(vertical='top',wrap_text=True)
raw.freeze_panes='A2';raw.auto_filter.ref=raw.dimensions
out=Path('output/文具代发大规模筛选漏斗.xlsx');wb.save(out)
Path('data/large-parsed.json').write_text(json.dumps(parsed,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'search':len(search),'details':len(parsed),'passed':len(passed),'pending':len(parsed)-len(passed),'output':str(out.resolve())},ensure_ascii=False))
