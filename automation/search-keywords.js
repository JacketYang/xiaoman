const { chromium } = require('playwright-core');
const fs = require('fs');
(async()=>{
 const browser=await chromium.connectOverCDP('http://127.0.0.1:9222');
 const context=browser.contexts()[0];
 const p=context.pages().find(p=>p.url().includes('s.1688.com'));
 for(const keyword of process.argv.slice(2)){
  const input=p.locator('#alisearch-input');
  await input.fill(keyword);await input.press('Enter');await p.waitForTimeout(6000);
  const offers=await p.locator('a[href*="detail.1688.com/offer/"]').evaluateAll(as=>as.map(a=>({text:a.innerText,href:a.href})).filter(x=>x.text.trim()));
  const unique=[...new Map(offers.map(o=>[o.href.match(/offer\/(\d+)/)?.[1],o])).values()];
  fs.writeFileSync('data/search-'+keyword.replace(/[\\/:*?"<>|]/g,'_')+'.json',JSON.stringify(unique,null,2));
  console.log('\n### '+keyword+' ###');
  console.log(unique.slice(0,15).map((o,i)=>({n:i+1,text:o.text,url:o.href}))); 
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1});
