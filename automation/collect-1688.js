const { chromium } = require('playwright-core');
const fs = require('fs');
(async () => {
 const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
 const context = browser.contexts()[0];
 const page = context.pages().find(p=>p.url().includes('s.1688.com'));
 const offers = await page.locator('a[href*="detail.1688.com/offer/"]').evaluateAll(as=>as.map(a=>({text:a.innerText,href:a.href})).filter(x=>x.text.trim()));
 const unique=[...new Map(offers.map(o=>[o.href.match(/offer\/(\d+)/)?.[1],o])).values()];
 fs.writeFileSync('data/search-offers.json',JSON.stringify(unique,null,2));
 const picked=unique.filter(o=>/中性笔|可擦笔/.test(o.text)&&!/定制|LOGO|logo|商务|企业|U盘|礼品|晨\.|得力|东米|百金/.test(o.text)).slice(0,5);
 console.log('Selected',picked.map(p=>({title:p.text.split('\n')[0],url:p.href})));
 const results=[];
 for(const [index,offer] of picked.entries()){
   const p=await context.newPage();
   try{
    await p.goto(offer.href.replace('http:','https:'),{waitUntil:'domcontentloaded',timeout:60000});
    await p.waitForTimeout(5000);
    const body=await p.locator('body').innerText();
    const data={search:offer,url:p.url(),title:await p.title(),body,inputs:await p.locator('input').evaluateAll(es=>es.map(e=>({name:e.name,value:e.value,placeholder:e.placeholder})).filter(x=>x.value||x.placeholder)),priceTexts:await p.locator('[class*=price],[class*=Price],[class*=sku],[class*=Sku],[class*=freight],[class*=Freight]').evaluateAll(es=>es.map(e=>({tag:e.tagName,cls:e.className,text:(e.innerText||'').trim()})).filter(x=>x.text).slice(0,200))};
    results.push(data);
    await p.screenshot({path:`output/offer-${index+1}.png`,fullPage:false});
   }catch(e){results.push({search:offer,error:e.message});}
   await p.close();
 }
 fs.writeFileSync('data/offer-details.json',JSON.stringify(results,null,2));
 console.log('Saved',results.length,'details',results.map(r=>({title:r.title,chars:r.body?.length,error:r.error})));
 await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1});
