"""快速采集全国失业金数据 - 直接 HTTP API 调用"""
import requests
import json
import time
import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# === 浏览器 cookies ===
COOKIES = {
    "TERMINAL-JTOKEN": "hbdtisksQLgHcf+n63ZgxD7l/G8c06omqAKG4kiuBGcISzcCHFJDYB/rBqcamS44AEqg5NNk60Abkemjp60c8u3dGf9Im2Eo2Q4etg/h8MFQwPAvZB4vLUL82a9Zr2SlB7qVclubFCIj9sMmYxo1vA==",
    "arialoadData": "false",
    "osptb-v1-svc-3777": "5c2c4589aef366e0",
    "SF_cookie_83": "32407114"
}

API_URL = "https://si.12333.gov.cn/osptb/api/unemploymentRestApi/getSyjcs"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
}

# 省份列表
PROVINCES = [
    {"id": "110000", "name": "北京市", "isDirect": True},
    {"id": "120000", "name": "天津市", "isDirect": True},
    {"id": "130000", "name": "河北省", "isDirect": False},
    {"id": "140000", "name": "山西省", "isDirect": False},
    {"id": "150000", "name": "内蒙古自治区", "isDirect": False},
    {"id": "210000", "name": "辽宁省", "isDirect": False},
    {"id": "220000", "name": "吉林省", "isDirect": False},
    {"id": "230000", "name": "黑龙江省", "isDirect": False},
    {"id": "310000", "name": "上海市", "isDirect": True},
    {"id": "320000", "name": "江苏省", "isDirect": False},
    {"id": "330000", "name": "浙江省", "isDirect": False},
    {"id": "340000", "name": "安徽省", "isDirect": False},
    {"id": "350000", "name": "福建省", "isDirect": False},
    {"id": "360000", "name": "江西省", "isDirect": False},
    {"id": "370000", "name": "山东省", "isDirect": False},
    {"id": "410000", "name": "河南省", "isDirect": False},
    {"id": "420000", "name": "湖北省", "isDirect": False},
    {"id": "430000", "name": "湖南省", "isDirect": False},
    {"id": "440000", "name": "广东省", "isDirect": False},
    {"id": "450000", "name": "广西壮族自治区", "isDirect": False},
    {"id": "460000", "name": "海南省", "isDirect": False},
    {"id": "500000", "name": "重庆市", "isDirect": True},
    {"id": "510000", "name": "四川省", "isDirect": False},
    {"id": "520000", "name": "贵州省", "isDirect": False},
    {"id": "530000", "name": "云南省", "isDirect": False},
    {"id": "540000", "name": "西藏自治区", "isDirect": False},
    {"id": "610000", "name": "陕西省", "isDirect": False},
    {"id": "620000", "name": "甘肃省", "isDirect": False},
    {"id": "630000", "name": "青海省", "isDirect": False},
    {"id": "640000", "name": "宁夏回族自治区", "isDirect": False},
    {"id": "650000", "name": "新疆维吾尔自治区", "isDirect": False},
    {"id": "660000", "name": "新疆生产建设兵团", "isDirect": False},
]

session = requests.Session()
session.cookies.update(COOKIES)
session.headers.update(HEADERS)


def get_cities(province_id):
    """通过 CDP 获取省份下的城市列表"""
    import urllib.request
    import urllib.parse
    
    js = f"""
    var v = document.getElementById("aab301").__vue__;
    v.handleReValue("{province_id}");
    await new Promise(function(r) {{ setTimeout(r, 500); }});
    var cities = v.$data.optionsCity;
    return JSON.stringify(cities.map(function(c){{return {{id:c.id,name:c.name}}}}));
    """
    
    data = js.encode('utf-8')
    req = urllib.request.Request(
        f"http://localhost:3456/eval?target=550B777AC485D26625B1FCDDCF16E56C",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        if "value" in result:
            return json.loads(result["value"])
        return []
    except Exception as e:
        print(f"  CDP 错误: {e}")
        return []


def get_counties(city_id):
    """通过 CDP 获取城市下的区县列表"""
    import urllib.request
    
    js = f"""
    var v = document.getElementById("aab301").__vue__;
    v.handleReValue("{city_id}");
    await new Promise(function(r) {{ setTimeout(r, 400); }});
    var counties = v.$data.optionsCounty;
    if (!counties || counties.length === 0) return "[]";
    return JSON.stringify(counties.map(function(c){{return {{id:c.id,name:c.name}}}}));
    """
    
    data = js.encode('utf-8')
    req = urllib.request.Request(
        f"http://localhost:3456/eval?target=550B777AC485D26625B1FCDDCF16E56C",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        if "value" in result:
            return json.loads(result["value"])
        return []
    except Exception as e:
        print(f"    CDP 错误: {e}")
        return []


def query_api(region_code):
    """直接调用 API 获取失业金数据"""
    payload = {
        "aab301": region_code,
        "jiaofei_zhishu": "0",
        "arg_salary": "5000",
        "jiaofei_year": "5",
        "jiaofei_year_st": "0",
        "jiaofei_month": "0"
    }
    try:
        resp = session.post(API_URL, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("bizSuccess"):
                d = data["data"]
                return {
                    "months": int(float(d.get("receivedmonth", 0))),
                    "amount": float(d.get("money", 0)),
                    "after13": float(d.get("get_money_for_13th", 0)),
                    "success": True
                }
            else:
                return {"error": data.get("bizMessage", "unknown"), "success": False}
        else:
            return {"error": f"HTTP {resp.status_code}", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


# === 1. 收集所有区域编码 ===
print("=== 收集区域编码 ===")
all_regions = []

for prov in PROVINCES:
    pname = prov["name"]
    pid = prov["id"]
    
    if prov["isDirect"]:
        # 直辖市：第二级有"市本级"
        print(f"\n{pname} (直辖市)")
        cities = get_cities(pid)
        shibenji = [c for c in cities if "市本级" in c["name"]]
        if shibenji:
            all_regions.append({"province": pname, "city": f"{pname}市本级", "code": shibenji[0]["id"]})
            print(f"  -> {pname}市本级 ({shibenji[0]['id']})")
    else:
        # 普通省份：第三级有"市本级"
        print(f"\n{pname}")
        cities = get_cities(pid)
        if not cities:
            print(f"  无城市数据，跳过")
            continue
        
        for city in cities:
            cname = city["name"]
            if cname == "省本级" or "省直辖" in cname:
                continue
            
            counties = get_counties(city["id"])
            if not counties:
                continue
            
            shibenji = [c for c in counties if "市本级" in c["name"]]
            if shibenji:
                all_regions.append({"province": pname, "city": cname, "code": shibenji[0]["id"]})
                print(f"  -> {cname}市本级 ({shibenji[0]['id']})")
    
    time.sleep(0.3)

print(f"\n=== 共 {len(all_regions)} 个区域 ===")

# 保存区域编码
with open("D:/ISO/pxx/region_codes.json", "w", encoding="utf-8") as f:
    json.dump(all_regions, f, ensure_ascii=False, indent=2)

# === 2. 调用 API 获取失业金数据 ===
print("\n=== 调用 API 获取失业金数据 ===")
results = []
total = len(all_regions)

for i, region in enumerate(all_regions):
    pname = region["province"]
    cname = region["city"]
    code = region["code"]
    
    print(f"[{i+1}/{total}] {pname} - {cname} ({code})", end=" ")
    data = query_api(code)
    
    if data.get("success"):
        entry = {
            "province": pname,
            "city": cname,
            "months": data["months"],
            "amount": data["amount"],
            "after13": data["after13"],
            "success": True
        }
        print(f"-> {data['amount']}元/月 ({data['months']}个月)")
    else:
        entry = {
            "province": pname,
            "city": cname,
            "error": data.get("error", "unknown"),
            "success": False
        }
        print(f"-> 失败: {data.get('error', 'unknown')}")
    
    results.append(entry)
    sys.stdout.flush()
    
    # 每10个保存一次进度
    if (i + 1) % 10 == 0:
        with open("D:/ISO/pxx/unemployment_data.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    time.sleep(0.2)

# 最终保存
with open("D:/ISO/pxx/unemployment_data.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n=== 数据采集完成！共 {len(results)} 条 ===")
success_count = sum(1 for r in results if r.get("success"))
fail_count = sum(1 for r in results if not r.get("success"))
print(f"成功: {success_count}, 失败: {fail_count}")

# === 3. 生成 Excel ===
print("\n=== 生成 Excel ===")
wb = Workbook()
ws = wb.active
ws.title = "全国失业金对比"

# 样式
header_font = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
cell_font = Font(name="微软雅黑", size=10)
cell_alignment = Alignment(horizontal="center", vertical="center")
thin_border = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="thin", color="D9D9D9")
)
highlight_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

# 表头
headers = ["序号", "省份", "城市", "可领月数", "每月金额(元)", "13个月后金额(元)"]
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_alignment
    cell.border = thin_border

# 数据排序：按省份分组，金额降序
success_data = [r for r in results if r.get("success")]
success_data.sort(key=lambda x: x["amount"], reverse=True)

top3 = max(r["amount"] for r in success_data) if success_data else 0

for idx, row_data in enumerate(success_data, 1):
    row = idx + 1
    ws.cell(row=row, column=1, value=idx).font = cell_font
    ws.cell(row=row, column=1).alignment = cell_alignment
    ws.cell(row=row, column=1).border = thin_border
    
    ws.cell(row=row, column=2, value=row_data["province"]).font = cell_font
    ws.cell(row=row, column=2).alignment = cell_alignment
    ws.cell(row=row, column=2).border = thin_border
    
    ws.cell(row=row, column=3, value=row_data["city"]).font = cell_font
    ws.cell(row=row, column=3).alignment = cell_alignment
    ws.cell(row=row, column=3).border = thin_border
    
    ws.cell(row=row, column=4, value=row_data["months"]).font = cell_font
    ws.cell(row=row, column=4).alignment = cell_alignment
    ws.cell(row=row, column=4).border = thin_border
    
    ws.cell(row=row, column=5, value=row_data["amount"]).font = cell_font
    ws.cell(row=row, column=5).alignment = cell_alignment
    ws.cell(row=row, column=5).border = thin_border
    ws.cell(row=row, column=5).number_format = '#,##0.00'
    
    ws.cell(row=row, column=6, value=row_data["after13"]).font = cell_font
    ws.cell(row=row, column=6).alignment = cell_alignment
    ws.cell(row=row, column=6).border = thin_border
    ws.cell(row=row, column=6).number_format = '#,##0.00'
    
    # 高亮金额最高的3个
    if row_data["amount"] >= top3:
        for c in range(1, 7):
            ws.cell(row=row, column=c).fill = highlight_fill

# 列宽
ws.column_dimensions["A"].width = 6
ws.column_dimensions["B"].width = 16
ws.column_dimensions["C"].width = 18
ws.column_dimensions["D"].width = 10
ws.column_dimensions["E"].width = 16
ws.column_dimensions["F"].width = 16

# 冻结首行
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:F{len(success_data)+1}"

excel_path = "D:/ISO/pxx/全国失业金对比.xlsx"
wb.save(excel_path)

# 失败记录
if fail_count > 0:
    fail_data = [r for r in results if not r.get("success")]
    with open("D:/ISO/pxx/failed_regions.json", "w", encoding="utf-8") as f:
        json.dump(fail_data, f, ensure_ascii=False, indent=2)
    print(f"\n失败记录已保存到 failed_regions.json ({fail_count} 条)")

print(f"\nExcel 已保存到: {excel_path}")
print(f"共 {len(success_data)} 条有效数据")
