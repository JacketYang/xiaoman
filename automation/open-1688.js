const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const context = browser.contexts()[0];
  const pages = context.pages();
  const page = pages.find(p => !p.url().startsWith('devtools://')) || await context.newPage();
  await page.bringToFront();
  const keyword = process.argv[2] || '文具 一件代发';
  if (!page.url().includes('s.1688.com')) {
    await page.goto('https://s.1688.com/selloffer/offer_search.htm', { waitUntil: 'domcontentloaded', timeout: 60000 });
  }
  const input = page.locator('#alisearch-input');
  await input.fill(keyword);
  await input.press('Enter');
  await page.waitForTimeout(7000);
  console.log(JSON.stringify({ title: await page.title(), url: page.url(), text: (await page.locator('body').innerText()).slice(0, 5000) }, null, 2));
  await page.screenshot({ path: 'output/1688-search.png', fullPage: false });
  await browser.close();
})().catch(error => { console.error(error); process.exitCode = 1; });
