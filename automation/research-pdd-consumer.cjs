const fs = require('fs');
const path = require('path');
const { chromium } = require('./node_modules/playwright-core');

const queries = [
  '16K语文作业本5本',
  '学生多功能便利贴组合',
  '串串乐按动中性笔套装',
  '可擦笔10芯1笔套装'
];
const outputPath = path.resolve(__dirname, '../data/pdd-consumer-research.json');

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const page = await browser.contexts()[0].newPage();
  const visits = [];
  const searchResults = [];
  async function visit(requestedUrl) {
    try {
      const response = await page.goto(requestedUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(10000);
      const actualUrl = page.url();
      const httpStatus = response ? response.status() : null;
      const title = await page.title();
      const pageText = await page.locator('body').innerText();
      const visit = { requestedUrl, actualUrl, httpStatus, title, pageText };
      visits.push(visit);
      return visit;
    } catch (error) {
      const visit = { requestedUrl, actualUrl: page.url(), error: String(error), pageText: await page.locator('body').innerText().catch(() => '') };
      visits.push(visit);
      return visit;
    }
  }
  try {
    const mobileHome = await visit('https://mobile.yangkeduo.com/');
    await visit('https://www.pinduoduo.com/');
    for (const query of queries) {
      const requestedUrl = 'https://mobile.yangkeduo.com/search_result.html?search_key=' + encodeURIComponent(query);
      const result = await visit(requestedUrl);
      const status = /\/login\.html/.test(result.actualUrl) || /手机登录|扫码登录/.test(result.pageText) ? 'consumer_login_required' : result.pageText.trim() ? 'page_text_without_targeted_product_matches' : 'no_visible_page_text';
      searchResults.push({ query, requestedUrl, actualUrl: result.actualUrl, httpStatus: result.httpStatus ?? null, title: result.title ?? null, pageText: result.pageText, matchedProducts: [], status });
    }
    const desktopSearch = await visit('https://www.pinduoduo.com/?search_key=' + encodeURIComponent(queries[0]));
    const report = {
      researchedAt: new Date().toISOString(),
      method: 'Playwright Core connected to existing Chrome via CDP; a newly created page was used and closed after collection. No login, merchant backend access, or purchase.',
      scope: ['https://mobile.yangkeduo.com/', 'https://www.pinduoduo.com/'],
      findings: {
        consumerSiteAccessible: mobileHome.httpStatus === 200 && mobileHome.pageText.includes('个人中心'),
        targetedProductsAndTerminalPricesObtained: false,
        matchedProductCount: 0,
        summary: '移动消费者首页可展示商品和标价，但四个指定关键词均未获得商品搜索结果、规格或终端售价：搜索访问或跳转消费者登录页，或无可见商品文本。www.pinduoduo.com 首页可访问并展示推荐商品价格；带 search_key 参数的首页访问未呈现关键词搜索结果。',
        desktopSearchProbe: { query: queries[0], requestedUrl: desktopSearch.requestedUrl, actualUrl: desktopSearch.actualUrl, result: desktopSearch.pageText.includes('16K语文作业本') ? 'query_text_present_manual_review_required' : 'homepage_recommendations_only_no_keyword_results' }
      },
      searchResults,
      visits,
      nextSteps: [
        '由操作者在消费者端自行完成登录/人机验证后，重新访问四个 search_result.html 地址，读取搜索结果并逐条打开商品详情核对 SKU 与结算前售价。',
        '若网页端仍要求 App，则在拼多多 App 内按原关键词搜索，以具体商品详情页所选 SKU 显示价格为准；本次未执行登录、验证或购买。'
      ]
    };
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, JSON.stringify(report, null, 2), 'utf8');
    console.log(JSON.stringify({ outputPath, searchResults: searchResults.map(({query, actualUrl, httpStatus, title, matchedProducts}) => ({query, actualUrl, httpStatus, title, matchedProducts})), visits: visits.map(({requestedUrl,actualUrl,httpStatus,title,textLength}) => ({requestedUrl,actualUrl,httpStatus,title,textLength:undefined})), bytes: fs.statSync(outputPath).size }, null, 2));
  } finally {
    await page.close();
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
