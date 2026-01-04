import requests
import re
import datetime

# --- 設定區 ---

# 1. 來源列表 (聚合多個穩定的公開源)
SOURCE_URLS = [
    "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "https://raw.githubusercontent.com/yuanzl77/IPTV/main/live.m3u",
    "https://raw.githubusercontent.com/live-television/m3u/master/Hong%20Kong.m3u"
]

# 2. 關鍵字過濾 (只保留這些頻道)
KEYWORDS = ["ViuTV", "HOY", "RTHK", "Jade", "Pearl", "J2", "無線新聞", "有線新聞", "Now", "港台", "翡翠", "明珠"]

# 3. 必備的官方/穩定源 (不管檢測結果如何，強制加入，保證有台可看)
STATIC_CHANNELS = [
    # RTHK 官方源 (通常無鎖，全球可看)
    {"name": "RTHK 31", "url": "https://rthklive1-lh.akamaihd.net/i/rthk31_1@167495/index_2052_av-b.m3u8"},
    {"name": "RTHK 32", "url": "https://rthklive2-lh.akamaihd.net/i/rthk32_1@168450/index_2052_av-b.m3u8"}
]

# --- 邏輯區 ---

def check_url(url):
    """檢測鏈接是否有效 (超時 2 秒)"""
    try:
        response = requests.get(url, timeout=2, stream=True)
        return response.status_code == 200
    except:
        return False

def fetch_and_parse():
    found_channels = []
    
    print("正在抓取網路源...")
    for source in SOURCE_URLS:
        try:
            print(f"Processing: {source}")
            r = requests.get(source)
            if r.status_code != 200: continue
            
            lines = r.text.split('\n')
            current_name = ""
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                if line.startswith("#EXTINF"):
                    # 嘗試提取頻道名稱
                    match = re.search(r',(.+)$', line)
                    if match:
                        current_name = match.group(1).strip()
                elif line.startswith("http") and current_name:
                    # 檢查名稱是否包含關鍵字
                    if any(k.lower() in current_name.lower() for k in KEYWORDS):
                        # 去重
                        if not any(c['url'] == line for c in found_channels):
                            found_channels.append({"name": current_name, "url": line})
                    current_name = "" # 重置
        except Exception as e:
            print(f"Error fetching {source}: {e}")

    return found_channels

def generate_m3u(channels):
    print(f"共找到 {len(channels)} 個潛在頻道，開始檢測有效性...")
    
    final_list = []
    
    # 1. 先加入靜態必備源
    for static in STATIC_CHANNELS:
        final_list.append(static)
        print(f"[Static] {static['name']} Added.")

    # 2. 檢測抓取到的源
    for ch in channels:
        print(f"Checking: {ch['name']}...", end=" ")
        if check_url(ch['url']):
            final_list.append(ch)
            print("OK")
        else:
            print("FAIL")

    # 3. 寫入文件
    content = '#EXTM3U x-tvg-url="https://epg.112114.xyz/pp.xml"\n'
    content += f'# Update: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
    
    for item in final_list:
        content += f'#EXTINF:-1 group-title="Hong Kong" logo="https://epg.112114.xyz/logo/{item["name"]}.png",{item["name"]}\n'
        content += f'{item["url"]}\n'

    with open("hk_live.m3u", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"完成！共收錄 {len(final_list)} 個有效頻道。")

if __name__ == "__main__":
    candidates = fetch_and_parse()
    generate_m3u(candidates)
