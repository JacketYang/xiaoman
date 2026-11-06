// collect_unemployment.js - 修正版
// 直接调用 API，绕过表单验证，确保 arg_salary=5000 生效

const fs = require('fs');

const CDP_URL = 'http://localhost:3456';
const TARGET = '550B777AC485D26625B1FCDDCF16E56C';
const OUTPUT_JSON = 'D:/ISO/pxx/unemployment_data.json';
const MUNICIPALITIES = ['110000', '120000', '310000', '500000'];

let sessionStartTime = Date.now();

async function evalJS(code) {
    const res = await fetch(`${CDP_URL}/eval?target=${TARGET}`, {
        method: 'POST', body: code,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    const text = await res.text();
    try {
        const json = JSON.parse(text);
        if (json.value !== undefined) {
            try { return JSON.parse(json.value); } catch { return json.value; }
        }
        if (json.result !== undefined) return json.result;
        return json;
    } catch { return text; }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function closeAllModals() {
    try { await evalJS(`document.querySelector(".ant-modal-close") && document.querySelector(".ant-modal-close").click(); document.querySelector(".ant-btn-primary") && document.querySelector(".ant-btn-primary").click(); "ok"`); } catch(e) {}
    await sleep(600);
}

// 直接调用后端 API（绕过表单验证）
async function callApi(regionCode) {
    const code = `
    (function() {
        return new Promise(function(resolve) {
            Base.sendRequest("api/unemploymentRestApi/getSyjcs", {
                aab301: "${regionCode}",
                jiaofei_zhishu: "0",
                arg_salary: "5000",
                jiaofei_year: "5",
                jiaofei_year_st: "0",
                jiaofei_month: "0"
            }, function(e) {
                if (e && e.data) {
                    resolve(JSON.stringify({
                        months: e.data.receivedmonth,
                        amount: e.data.money,
                        after13: e.data.get_money_for_13th,
                        success: e.data.bizSuccess
                    }));
                } else {
                    resolve(JSON.stringify({error: "no data", raw: JSON.stringify(e)}));
                }
            });
        });
    })()`;
    try {
        const raw = await evalJS(code);
        if (typeof raw === 'string') {
            try { return JSON.parse(raw); } catch { return { error: raw }; }
        }
        return raw;
    } catch (e) {
        return { error: e.message };
    }
}

// 获取全部省份
async function getProvinces() {
    return await evalJS(`var v=document.getElementById("aab301").__vue__;JSON.stringify(v.$data.optionsProvince.map(function(p){return{id:p.id,name:p.name}}))`);
}

// 获取某省的城市列表
async function getCities(provinceId) {
    await evalJS(`var v=document.getElementById("aab301").__vue__;v.handleReValue("${provinceId}");"ok"`);
    await sleep(1500);
    return await evalJS(`var v=document.getElementById("aab301").__vue__;JSON.stringify(v.$data.optionsCity.map(function(c){return{id:c.id,name:c.name}}))`);
}

// 获取某城市的区县列表
async function getCounties(cityId) {
    await evalJS(`var v=document.getElementById("aab301").__vue__;v.handleReValue("${cityId}");"ok"`);
    await sleep(1500);
    return await evalJS(`var v=document.getElementById("aab301").__vue__;JSON.stringify(v.$data.optionsCounty.map(function(c){return{id:c.id,name:c.name}}))`);
}

async function main() {
    const results = [];

    if (fs.existsSync(OUTPUT_JSON)) {
        const existing = JSON.parse(fs.readFileSync(OUTPUT_JSON, 'utf-8'));
        results.push(...existing);
        console.log(`已加载 ${existing.length} 条已有数据`);
    }

    await closeAllModals();
    const provinces = await getProvinces();
    console.log(`共 ${provinces.length} 个省份/直辖市\n`);

    for (const province of provinces) {
        const isMunicipality = MUNICIPALITIES.includes(province.id);

        if (isMunicipality) {
            // 直辖市：省→市本级（第二级）
            const existing = results.find(r => r.province === province.name && r.city === province.name + '市本级');
            if (existing && !existing.error && existing.amount) {
                console.log(`[跳过] ${province.name}市本级 (已采集 ${existing.amount}元)`);
                continue;
            }

            let cities;
            try { cities = await getCities(province.id); } catch(e) {
                console.log(`[错误] ${province.name} 获取城市失败: ${e.message}`);
                continue;
            }
            const shibenji = cities.find(c => c.name.includes('市本级'));
            if (!shibenji) {
                console.log(`[错误] ${province.name} 无市本级`);
                continue;
            }

            try {
                const result = await callApi(shibenji.id);
                results.push({ province: province.name, city: province.name + '市本级', ...result });
                console.log(`[直辖市] ${province.name}市本级: ${result.amount}元/月 (${result.months}个月)`);
            } catch(e) {
                console.log(`[错误] ${province.name}: ${e.message}`);
                results.push({ province: province.name, city: province.name + '市本级', error: e.message });
            }
            fs.writeFileSync(OUTPUT_JSON, JSON.stringify(results, null, 2));

        } else {
            // 普通省份：省→市→市本级（第三级）
            let cities;
            try { cities = await getCities(province.id); } catch(e) {
                console.log(`[错误] ${province.name} 获取城市失败: ${e.message}`);
                continue;
            }

            console.log(`[省份] ${province.name} (${cities.length}个城市)`);

            for (const city of cities) {
                if (city.name.includes('省本级')) continue;

                const existingCity = results.find(r => r.province === province.name && r.city === city.name);
                if (existingCity && !existingCity.error && existingCity.amount) {
                    console.log(`  [跳过] ${city.name} (${existingCity.amount}元)`);
                    continue;
                }

                let counties;
                try { counties = await getCounties(city.id); } catch(e) {
                    console.log(`  [错误] ${city.name}: ${e.message}`);
                    continue;
                }

                const shibenji = counties.find(c => c.name.includes('市本级'));
                if (!shibenji) {
                    console.log(`  [跳过] ${city.name} (无市本级)`);
                    continue;
                }

                try {
                    const result = await callApi(shibenji.id);
                    results.push({ province: province.name, city: city.name, ...result });
                    console.log(`  ${city.name}: ${result.amount}元/月 (${result.months}个月)`);
                } catch(e) {
                    console.log(`  [错误] ${city.name}: ${e.message}`);
                    results.push({ province: province.name, city: city.name, error: e.message });
                }

                fs.writeFileSync(OUTPUT_JSON, JSON.stringify(results, null, 2));
            }
        }
    }

    console.log(`\n===== 完成！共采集 ${results.length} 条数据 =====`);
}

main().catch(err => { console.error('脚本错误:', err); process.exit(1); });
