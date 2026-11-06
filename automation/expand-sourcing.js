const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const queries = [
  '按动中性笔 整盒 一件代发',
  '可擦中性笔 套装 一件代发',
  '铅笔 套装 学生 一件代发',
  '作业本 16K 10本 一件代发',
  'A5笔记本 4本 一件代发',
  '便利贴 组合套装 一件代发',
  '文件袋 A4 10个 一件代发',
  '学生笔袋 大容量 一件代发',
  '尺子套装 学生 一件代发',
  '橡皮擦 30块 一件代发'
];
const sleep = ms => new Promise(r=>setTimeout(r,ms));
(async()=>{
 const browser=await chromium.connectOverCDP('http://127.0.0.1:9222');
 const context=browser.contexts()[0];
 const page=context.pages().find(p=>p.url().includes('s.1688.com'));
 if(!page) throw new Error('1688 search page not found');
 const manifest=[];
 for(const query of queries){
  const input=page.locator('#alisearch-input');
  await input.fill(query);await input.press('Enter');await page.waitForTimeout(5000);
  const offers=await page.locator('a[href*="detail.1688.com/offer/"]').evaluateAll(as=>as.map(a=>({text:a.innerText,href:a.href})).filter(x=>x.text.trim()));
  const unique=[...new Map(offers.map(o=>[o.href.match(/offer\/(\d+)/)?.[1],o])).values()];
  const relevant=unique.filter(o=>!/定制|LOGO|logo|商务|企业|U盘|键盘|电脑|清洁|书包|眉笔|画笔|钢笔/.test(o.text));
  console.log(query,'total',unique.length,'relevant',relevant.length);
  for(const o of relevant.slice(0,5)) manifest.push({query,id:o.href.match(/offer\/(\d+)/)[1],...o});
 }
 fs.writeFileSync('data/expanded-manifest.json',JSON.stringify(manifest,null,2));
 const all=[];
 for(const [i,item] of manifest.entries()){
  const p=await context.newPage();
  try{
   await p.goto(`https://detail.1688.com/offer/${item.id}.html`,{waitUntil:'domcontentloaded',timeout:50000});
   await p.waitForTimeout(3000);
   const body=await p.locator('body').innerText();
   all.push({...item,url:p.url(),title:await p.title(),body,collectedAt:new Date().toISOString()});
   console.log(`${i+1}/${manifest.length}`,item.id,(await p.title()).slice(0,45));
  }catch(e){all.push({...item,error:e.message});console.error(item.id,e.message)}
  await p.close();
 }
 fs.writeFileSync('data/expanded-offers.json',JSON.stringify(all,null,2));
 console.log('Saved',all.length,'detail pages');
 await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1});
