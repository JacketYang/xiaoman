const { chromium } = require('playwright-core');
const fs = require('fs');
(async()=>{
 const browser=await chromium.connectOverCDP('http://127.0.0.1:9222');
 const context=browser.contexts()[0];
 const page=context.pages().find(p=>p.url().includes('yangkeduo.com'))||await context.newPage();
 await page.bringToFront();
 const keyword=process.argv[2]||'16K语文作业本5本';
 await page.goto('https://mobile.yangkeduo.com/search_result.html?search_key='+encodeURIComponent(keyword),{waitUntil:'domcontentloaded',timeout:60000});
 await page.waitForTimeout(6000);
 const body=await page.locator('body').innerText();
 const data={keyword,url:page.url(),title:await page.title(),body,html:(await page.content()).slice(0,500000),links:await page.locator('a').evaluateAll(as=>as.map(a=>({text:a.innerText,href:a.href})).filter(x=>x.text.trim()).slice(0,100)),collectedAt:new Date().toISOString()};
 fs.writeFileSync('data/pdd-search-current.json',JSON.stringify(data,null,2));
 console.log(JSON.stringify({url:data.url,title:data.title,body:body.slice(0,12000)},null,2));
 await page.screenshot({path:'output/pdd-consumer-search.png',fullPage:false});
 await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1});
