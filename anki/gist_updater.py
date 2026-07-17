import os
import json
import time
import urllib.request
import urllib.error

# ================= 配置 =================
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GIST_ID = '422fab6e44d55af1173d19f27ddb5664'
FILENAME = 'anki_stats.json'

# 上海时区 UTC+8
TZ_OFFSET = 8 * 3600  # 28800 秒

def get_shanghai_now():
    """获取当前上海时间的时间戳（秒）"""
    return time.time() + TZ_OFFSET

def get_shanghai_today_start_utc_ms():
    """获取上海时间今天 00:00 对应的 UTC 毫秒时间戳（用于查询 Anki 数据库）"""
    # 上海时间今天 00:00 的秒时间戳
    shanghai_now = get_shanghai_now()
    shanghai_today_start = (shanghai_now // 86400) * 86400
    # 转回 UTC 毫秒（Anki revlog.id 是 UTC 毫秒）
    return int((shanghai_today_start - TZ_OFFSET) * 1000)

def get_anki_data():
    from aqt import mw
    
    db = mw.col.db
    today_ts = get_shanghai_today_start_utc_ms()
    
    today_learned = db.scalar("SELECT COUNT(*) FROM revlog WHERE id > ?", today_ts)
    today_total = db.scalar("SELECT COUNT(*) FROM cards WHERE queue >= 0 AND due <= ?", 
                            int(time.time() / 86400))
    duration_minutes = db.scalar("SELECT COALESCE(SUM(time), 0) / 60000 FROM revlog WHERE id > ?", 
                                  today_ts) or 0
    
    recent_rows = db.all("""
        SELECT n.flds FROM revlog r
        JOIN cards c ON r.cid = c.id
        JOIN notes n ON c.nid = n.id
        WHERE r.id > ? ORDER BY r.id DESC LIMIT 5
    """, today_ts)
    
    recent_words = []
    for row in recent_rows:
        fields = row[0].split('\x1f')
        if fields:
            recent_words.append(fields[0])
    
    heatmap_data = get_heatmap_data(db)
    
    return {
        "today_learned": today_learned,
        "today_total": max(today_total, today_learned),
        "duration_minutes": int(duration_minutes),
        "recent_words": recent_words,
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(get_shanghai_now())),
        "heatmap": heatmap_data
    }

def get_heatmap_data(db):
    """生成最近30天每天的学习数量（按上海时间）"""
    shanghai_now = get_shanghai_now()
    # 上海时间今天 00:00
    shanghai_today_start = (shanghai_now // 86400) * 86400
    
    heatmap = []
    
    for i in range(29, -1, -1):
        # 第 i 天前（上海时间）的 00:00 和 23:59:59
        shanghai_day_start = shanghai_today_start - i * 86400
        shanghai_day_end = shanghai_day_start + 86400
        
        # 转回 UTC 毫秒（Anki 数据库查询用）
        utc_day_start_ms = int((shanghai_day_start - TZ_OFFSET) * 1000)
        utc_day_end_ms = int((shanghai_day_end - TZ_OFFSET) * 1000)
        
        count = db.scalar(
            "SELECT COUNT(*) FROM revlog WHERE id >= ? AND id < ?", 
            utc_day_start_ms, utc_day_end_ms
        )
        
        # 日期显示用上海时间
        date = time.strftime("%Y-%m-%d", time.gmtime(shanghai_day_start))
        
        heatmap.append({
            "date": date,
            "count": count
        })
    
    return heatmap

def update_gist(data):
    if not GITHUB_TOKEN:
        raise Exception("未设置 GITHUB_TOKEN 环境变量")
    
    url = f"https://api.github.com/gists/{GIST_ID}"
    
    payload = json.dumps({
        "files": {
            FILENAME: {
                "content": json.dumps(data, indent=2, ensure_ascii=False)
            }
        }
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, method='PATCH')
    req.add_header('Authorization', f'Bearer {GITHUB_TOKEN}')
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return True
            else:
                raise Exception(f"更新失败: {response.status}")
    except urllib.error.HTTPError as e:
        raise Exception(f"更新失败: {e.code} - {e.read().decode()}")