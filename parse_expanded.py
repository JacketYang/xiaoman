import json,re
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

raw=json.loads(Path('data/expanded-offers.json').read_text(encoding='utf-8'))
rows=[]
for item in raw:
 body=item.get('body','')
 title=item.get('title','').replace(' - 阿里巴巴','')
 def find(pattern,flags=0):
  m=re.search(pattern,body,flags);return m.group(1).strip() if m else ''
 supplier=body.split('\n')[0] if body else ''
 rating=find(r'综合履约率\n([\d.]+%)')
 returning=find(r'店铺回头率\n([\d.]+%)')
 attributes=''
 if '商品属性\n' in body:
  part=body.split('商品属性\n')[-1]
  attributes=part.split('包装信息')[0].strip()
 elif '全部参数' in body:
  attributes=body.split('全部参数')[0][-1800:]
 shipping=find(r'运费¥([\d.]+)起')
 free_shipping='是' if re.search(r'\n包邮\n',body) else '否'
 dropship=''
 if '代发下单' in body:
  part=body.split('代发下单')[-1]
  part=re.split(r'官方仓退货|商家代发热度|铺货素材预览|商品发布时间',part)[0]
  dropship=part.strip()
 price_parts=re.findall(r'￥\s*\n?([\d.]+)',dropship)
 dropship_price=price_parts[0] if price_parts else ''
 sku_section=''
 if '商品详情\n' in body:
  offer=body.split('商品详情\n')[-1]
  if '\n笔芯颜色\n' in offer: sku_section=offer.split('\n笔芯颜色\n')[-1].split('立即下单')[0].strip()
  elif '\n封面颜色\n' in offer: sku_section=offer.split('\n封面颜色\n')[-1].split('立即下单')[0].strip()
  elif '\n规格\n' in offer: sku_section=offer.split('\n规格\n')[-1].split('立即下单')[0].strip()
 if '中性笔' in item['query']: category='笔类'
 elif '作业本' in item['query']: category='作业本'
 elif '笔记本' in item['query']: category='笔记本'
 elif '便利贴' in item['query']: category='便利贴'
 elif '文件袋' in item['query']: category='文件袋'
 elif '笔袋' in item['query']: category='笔袋'
 elif '铅笔' in item['query']: category='铅笔'
 elif '套尺' in item['query']: category='套尺'
 elif '橡皮擦' in item['query']: category='橡皮擦'
 elif '荧光笔' in item['query']: category='荧光笔'
 elif '文具盒' in item['query']: category='文具盒'
 else: category=item['query']
 if category=='笔类':
  if '替芯' in title or ('笔芯' in title and not re.search(r'套装|\d+支笔|送\d+支笔',title)):
   form='仅替芯/待确认'
  elif re.search(r'套装|组合|整盒|盒装',title): form='笔类套装'
  else: form='成品笔（支数待核实）'
 else: form=category
 unit=find(r'1(盒|套|支|本|件|个)起批')
 status='待逐SKU核验'
 reasons=[]
 if not body: reasons.append('详情未读取')
 if not dropship: reasons.append('未识别代发区')
 if not dropship_price: reasons.append('无单件代发价')
 if not sku_section: reasons.append('SKU区未识别')
 if form=='笔类套装' and not re.search(r'\d+支|支芯|整盒|盒装',title+sku_section): reasons.append('笔/替芯及支数不清')
 if re.search(r'定制|盲盒',title): reasons.append('定制或盲盒需单独评估')
 if re.search(r'漫威|迪士尼|三丽鸥|宝可梦|奥特曼',title+attributes): reasons.append('品牌/IP需核验')
 rows.append({'id':item['id'],'query':item['query'],'title':title,'supplier':supplier,'form':form,'url':item['url'],'cost':dropship_price,'shipping':shipping,'freeShipping':free_shipping,'minUnit':unit,'rating':rating,'returning':returning,'dropship':dropship,'sku':sku_section,'attributes':attributes,'status':status,'reason':'；'.join(reasons)})
Path('data/expanded-normalized.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
wb=Workbook();ws=wb.active;ws.title='1688扩展候选池'
headers=['商品ID','搜索类目','商品名称','供应商','商品形态','1688链接','代发区首价（未选SKU勿作成本）','运费起（元）','批发包邮标记','批发起订单位','综合履约率','回头率','代发区原文','页面SKU区原文','商品属性','规格可信度','排除/待核实原因']
ws.append(headers)
for row in rows:ws.append([row[k] for k in ['id','query','title','supplier','form','url','cost','shipping','freeShipping','minUnit','rating','returning','dropship','sku','attributes','status','reason']])
for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='305496');c.alignment=Alignment(wrap_text=True)
for r in range(2,ws.max_row+1):
 ws.cell(r,6).hyperlink=ws.cell(r,6).value;ws.cell(r,6).style='Hyperlink'
 for c in range(1,ws.max_column+1):ws.cell(r,c).alignment=Alignment(vertical='top',wrap_text=True)
for i,w in enumerate([16,28,45,28,20,42,22,14,16,16,14,14,25,65,65,18,38],1):ws.column_dimensions[ws.cell(1,i).column_letter].width=w
ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
out=Path('output/1688文具扩展候选池_规格待核验.xlsx');wb.save(out)
print('DETAIL_COUNT',len(rows))
for form in sorted(set(r['form'] for r in rows)):print(form,sum(1 for r in rows if r['form']==form))
print('UNRESOLVED',sum(1 for r in rows if r['reason']))
print(out.resolve())
