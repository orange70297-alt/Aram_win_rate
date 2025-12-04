import requests
import pymysql
import json
import time
from datetime import datetime

API_KEY = "你的API_KEY"

puuids = [
    "你的PUUID",
    "好友1的PUUID",s
    "好友2的PUUID",
    # 你要加幾個都可以
]

headers = {"X-Riot-Token": API_KEY}

# === MySQL 連線 ===
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="你的root密碼",
    database="lol_data",
    charset="utf8mb4"
)
cursor = conn.cursor()

sql = """
INSERT IGNORE INTO aram_matches (match_id, champ_list, win, duration, timestamp)
VALUES (%s, %s, %s, %s, %s)
"""

total_inserted = 0   # 紀錄成功寫入數量

# =====================================
# 🚀 主流程：逐個 PUUID 批次抓取資料
# =====================================
for puuid in puuids:
    print(f"\n====== 處理玩家：{puuid} ======\n")

    # 抓最近 200 場（0~99、100~199）
    for start in [0, 100]:
        match_ids_url = f"https://sea.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count=100"

        res = requests.get(match_ids_url, headers=headers)
        if res.status_code != 200:
            print("抓取 matchIds 失敗：", res.status_code)
            continue

        match_ids = res.json()
        print(f"抓到 {len(match_ids)} 個 matchId（start={start}）")

        # 逐場抓詳細資料
        for match_id in match_ids:
            print("處理比賽：", match_id)

            detail_url = f"https://sea.api.riotgames.com/lol/match/v5/matches/{match_id}"
            detail_res = requests.get(detail_url, headers=headers)

            if detail_res.status_code != 200:
                print("抓詳細資料失敗（略過）")
                continue

            data = detail_res.json()
            info = data["info"]

            # 只抓 ARAM
            if info["queueId"] != 450:
                print("非 ARAM（略過）")
                continue

            # ===== 擷取隊伍資訊 =====
            participants = info["participants"]

            # 找這個 puuid 在哪一隊
            player_team_id = None
            for p in participants:
                if p["puuid"] == puuid:
                    player_team_id = p["teamId"]
                    break

            if player_team_id is None:
                print("找不到玩家隊伍（略過）")
                continue

            # 取得隊伍英雄 + 勝利
            team_champs = []
            team_win = None
            for p in participants:
                if p["teamId"] == player_team_id:
                    team_champs.append(p["championName"])
                    team_win = p["win"]

            duration = info["gameDuration"]
            timestamp = datetime.fromtimestamp(info["gameStartTimestamp"] / 1000)

            # ===== 寫入資料庫 =====
            champ_json = json.dumps(team_champs, ensure_ascii=False)
            win_val = 1 if team_win else 0

            values = (match_id, champ_json, win_val, duration, timestamp)

            try:
                cursor.execute(sql, values)
                conn.commit()
                if cursor.rowcount == 1:
                    total_inserted += 1
                    print("✔ 成功寫入 ARAM 比賽")
                else:
                    print("（已存在，略過）")
            except Exception as e:
                print("寫入錯誤：", e)

            time.sleep(1)  # 防止 API 過快

cursor.close()
conn.close()

print("\n==============================")
print(f"🎉 批次完成！總共新增 {total_inserted} 筆 ARAM 資料")
print("==============================")
