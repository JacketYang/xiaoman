const { chromium } = require('playwright-core');
const fs = require('fs');
const queries = [
 ['笔类','按动中性笔 套装 一件代发'],['笔类','可擦笔 成品笔 套装 一件代发'],['笔类','中性笔 20支 一件代发'],['替芯','中性笔替芯 20支 一件代发'],
 ['作业本','作业本 16K 10本 一件代发'],['笔记本','A5笔记本 4本 一件代发'],['便利贴','便利贴 组合套装 一件代发'],
 ['文件袋','文件袋 A4 10个 一件代发'],['笔袋','学生笔袋 大容量 一件代发'],['铅笔','学生铅笔 12支 一件代发'],
 ['套尺','学生套尺 四件套 一件代发'],['橡皮擦','橡皮擦 30块 一件代发'],['荧光笔','荧光笔 6支 一件代发'],
 ['文具盒','学生文具盒 一件代发'],['书皮','自粘书皮 10张 一件代发'],['试卷收纳','试卷收纳袋 一件代发'],
 ['便签本','便签本 5本 一件代发'],['订书机','学生订书机套装 一件代发'],['美工工具','学生美工剪刀 一件代发'],['桌面收纳','桌面笔筒收纳 一件代发']
];
const irrelevant=/U盘|键盘|电脑|手机|耳机|清洁|书包|眉笔|钢笔|毛笔|油画|纹身|玩具|美妆|办公椅|广告|定制|LOGO|logo|企业礼品|伴手礼/i;
(async()=>{
 const b=await chromium.connectOverCDP('http://127.0.0.1:9222');const c=b.contexts()[0];
 let p=c.pages().find(p=>p.url().includes('s.1688.com'));if(!p)throw Error('1688 search missing');
 const saved=fs.existsSync('data/large-search-pool.json')?JSON.parse(fs.readFileSync('data/large-search-pool.json','utf8')):[];
 const all=saved;const completed=new Set(saved.map(x=>x.query));const summary=[];
 for(const [category,query] of queries){
  if(completed.has(query)){console.log('SKIP SEARCH',query);continue;}
  let input=p.locator('#alisearch-input');
  if(!await input.count()){
   await p.goto('https://s.1688.com/selloffer/offer_search.htm?keywords=%D6%D0%D0%D4%B1%CA%CC%D7%D7%B0+%D2%BB%BC%FE%B4%FA%B7%A2',{waitUntil:'domcontentloaded',timeout:60000});
   await p.waitForTimeout(1500);
   input=p.locator('#alisearch-input');
  }
  if(!await input.count()){
   await p.close();p=await c.newPage();
   await p.goto('https://s.1688.com/selloffer/offer_search.htm?keywords=%D6%D0%D0%D4%B1%CA%CC%D7%D7%B0+%D2%BB%BC%FE%B4%FA%B7%A2',{waitUntil:'domcontentloaded',timeout:60000});
   await p.waitForTimeout(1500);
   input=p.locator('#alisearch-input');
  }
  if(!await input.count()){console.log('SEARCH UNAVAILABLE',query,p.url());continue;}
  await input.fill(query);await input.press('Enter');await p.waitForTimeout(4500);
  const cards=await p.locator('a[href*="detail.1688.com/offer/"]').evaluateAll(as=>as.map(a=>({text:a.innerText,href:a.href})).filter(x=>x.text.trim()));
  const unique=[...new Map(cards.map(o=>[o.href.match(/offer\/(\d+)/)?.[1],o])).values()];
  for(const o of unique){const id=o.href.match(/offer\/(\d+)/)[1];all.push({id,category,query,title:o.text.split('\n')[0],card:o.text,url:`https://detail.1688.com/offer/${id}.html`,initialReject:irrelevant.test(o.text)?'标题含跨类目或定制品':''});}
  summary.push({category,query,count:unique.length});console.log('SEARCH',query,unique.length,'TOTAL',all.length);
  fs.writeFileSync('data/large-search-pool.json',JSON.stringify(all,null,2));
 }
 const uniqueAll=[...new Map(all.map(x=>[x.id,x])).values()];
 fs.writeFileSync('data/large-search-pool.json',JSON.stringify(uniqueAll,null,2));
 console.log('UNIQUE',uniqueAll.length);
 const existing=new Set(JSON.parse(fs.readFileSync('data/expanded-offers.json','utf8')).map(x=>x.id));
 const candidates=uniqueAll.filter(x=>!x.initialReject&&!existing.has(x.id));
 const selected=[];
 for(const [category] of queries){const group=candidates.filter(x=>x.category===category);selected.push(...group.slice(0,8));}
 fs.writeFileSync('data/large-detail-queue.json',JSON.stringify(selected,null,2));
 console.log('DETAIL QUEUE',selected.length);
 const details=fs.existsSync('data/large-detail-pages.json')?JSON.parse(fs.readFileSync('data/large-detail-pages.json','utf8')):[];
 const completedDetails=new Set(details.map(x=>x.id));
 for(const [i,item] of selected.entries()){
  if(completedDetails.has(item.id))continue;
  const page=await c.newPage();
  try{await page.goto(item.url,{waitUntil:'domcontentloaded',timeout:45000});await page.waitForTimeout(2500);details.push({...item,title:await page.title(),body:await page.locator('body').innerText(),collectedAt:new Date().toISOString()});console.log('DETAIL',i+1,'/',selected.length,item.id)}catch(e){details.push({...item,error:e.message});console.log('ERROR',item.id,e.message)}await page.close();
  if(i%10===9)fs.writeFileSync('data/large-detail-pages.json',JSON.stringify(details,null,2));
 }
 fs.writeFileSync('data/large-detail-pages.json',JSON.stringify(details,null,2));
 console.log('DONE',JSON.stringify({search:uniqueAll.length,details:details.length,summary}));await b.close();
})().catch(e=>{console.error(e);process.exitCode=1});
