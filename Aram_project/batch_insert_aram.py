import requests
import pymysql
import json
from datetime import datetime
import time

API_KEY = "RGAPI-bab9b26d-7e14-40d1-9229-e1758537babd"
your_puuid = "wqOMPHbCr7zLKxQ9g7Yrh_kXolCbhO2iZXK2N17b8mZeVBRUA0mOU7EJ9wAeyk8EjOP0nLh3qSHjKA"

headers = {
    "X-Riot-Token": API_KEY
}

# === 1️⃣ 取得最近 20 場比賽 ID ===
match_ids_url = f"https://sea.api.riotgames.com/lol/match/v5/matches/by-puuid/{your_puuid}/ids?start=0&count=20"
res = requests.get(match_ids_url, headers=headers)
match_ids = res.json()

print("抓到的 match IDs:", match_ids)

# === 2️⃣ 連線 MySQL ===
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="P@ssw0rd",
    database="lol_data",
    charset="utf8mb4"
)
cursor = conn.cursor()

insert_sql = """
INSERT INTO aram_matches (match_id, champ_list, win, duration, timestamp)
VALUES (%s, %s, %s, %s, %s)
"""

insert_count = 0

# === 3️⃣ 逐場抓取詳細資料 ===
for match_id in match_ids:
    print(f"處理中：{match_id}")

    detail_url = f"https://sea.api.riotgames.com/lol/match/v5/matches/{match_id}"
    detail_res = requests.get(detail_url, headers=headers)

    if detail_res.status_code != 200:
        print("抓取失敗，略過")
        continue

    data = detail_res.json()
    info = data["info"]

    # === 4️⃣ 只保留 ARAM（queueId = 450）===
    if info["queueId"] != 450:
        print("不是 ARAM，略過")
        continue

    participants = info["participants"]

    # 找你在哪一隊
    player_team_id = None
    for p in participants:
        if p["puuid"] == your_puuid:
            player_team_id = p["teamId"]
            break

    # 取你這隊的 5 隻英雄 + 勝負
    team_champs = []
    team_win = None
    for p in participants:
        if p["teamId"] == player_team_id:
            team_champs.append(p["championName"])
            team_win = p["win"]

    # 其他欄位
    duration = info["gameDuration"]
    timestamp = datetime.fromtimestamp(info["gameStartTimestamp"] / 1000)

    # === 5️⃣ 寫入 MySQL ===
    champ_list_json = json.dumps(team_champs, ensure_ascii=False)
    win_db = 1 if team_win else 0

    values = (match_id, champ_list_json, win_db, duration, timestamp)

    try:
        cursor.execute(insert_sql, values)
        conn.commit()
        insert_count += 1
        print("✅ 已寫入:", match_id)
    except Exception as e:
        print("❌ 寫入失敗:", e)

    time.sleep(1)  # 避免 API 過快被封鎖

cursor.close()
conn.close()

print(f"\n🎉 批次完成！成功寫入 {insert_count} 筆 ARAM 對局資料")
