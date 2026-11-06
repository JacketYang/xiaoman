const { chromium } = require('playwright-core');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const context = browser.contexts()[0];
  const page = context.pages().find(p => p.url().includes('1688.com'));
  if (!page) throw new Error('No 1688 page');
  await page.bringToFront();
  const other = page.getByText('Other-简体中文-USD', { exact: false }).first();
  if (await other.count()) {
    await other.click();
    await page.waitForTimeout(1000);
  }
  console.log(JSON.stringify({ text: (await page.locator('body').innerText()).slice(0, 12000), options: await page.locator('a,button,[role=option]').evaluateAll(els => els.map(e => ({tag:e.tagName,text:(e.innerText||e.textContent||'').trim(),href:e.href})).filter(e=>e.text).slice(0,100)) }, null, 2));
  await page.screenshot({ path: 'output/1688-locale.png' });
  await browser.close();
})().catch(error => { console.error(error); process.exitCode = 1; });
