import requests
import pymysql
import json
import time
from datetime import datetime


puuid = "Uxhlou9ckzikVvgq3ADjYKROzMhRSJEskLJNzXEOPW93XPpDxjhru_Y-eN_5FGbggCTU4hgCTJ3A9Q"

API_KEY = "RGAPI-06a8dfea-346c-468b-beb6-c21299bea06e"
headers = {"X-Riot-Token": API_KEY}


def safe_request(url, headers):
    """確保不會 429，被限速時自動等待後重試"""
    while True:
        res = requests.get(url, headers=headers)

        # 通常會成功
        if res.status_code == 200:
            time.sleep(1)  # ★★★ 修改點：每個 request 等 1 秒（避免超速）
            return res

        # 被限速 → 等 2-3 秒再重試
        if res.status_code == 429:
            print("⚠ 429 Too Many Requests → 等待 2 秒後重試…")
            time.sleep(2)
            continue

        # 其他錯誤直接印出，但不重試
        print(f"⚠ Request Error: {res.status_code}")
        time.sleep(1)
        return None


# ======================================================
# MySQL 連線
# ======================================================
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="P@ssw0rd",
    database="lol_data",
    charset="utf8mb4"
)
cursor = conn.cursor()

sql = """
INSERT IGNORE INTO aram_matches (match_id, champ_list, win, duration, timestamp)
VALUES (%s, %s, %s, %s, %s)
"""

total_inserted = 0

# ======================================================
#  ★★★ 主流程：抓 0~3000 場資料（確定抓完）
# ======================================================
for start in range(0, 3000, 100):
    print(f"\n====== 抓取第 {start}~{start+100} 場比賽 ======\n")

    # ======================================================
    #  ★★★修改點★★★：把所有 request 改成 safe_request()
    # ======================================================
    match_ids_url = f"https://sea.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count=100"
    res = safe_request(match_ids_url, headers)

    if not res:
        print("⚠ 無法取得 matchIds，跳過這一頁")
        continue

    match_ids = res.json()

    if not match_ids:
        print("🚫 沒有更多比賽了，提前停止")
        break

    print(f"抓到 {len(match_ids)} 個 matchId")

    # ======================================================
    # 處理每一場比賽
    # ======================================================
    for match_id in match_ids:
        print(f"處理比賽：{match_id}")

        detail_url = f"https://sea.api.riotgames.com/lol/match/v5/matches/{match_id}"
        detail_res = safe_request(detail_url, headers)

        if not detail_res:
            print("⚠ 詳細資料抓取失敗（略過）")
            continue

        data = detail_res.json()
        info = data["info"]

        # 只抓 ARAM
        if info["queueId"] != 450:
            print("非 ARAM（略過）")
            continue

        # 找該玩家在哪隊
        participants = info["participants"]
        player_team_id = None
        for p in participants:
            if p["puuid"] == puuid:
                player_team_id = p["teamId"]
                break

        if player_team_id is None:
            print("⚠ 找不到玩家隊伍（略過）")
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

        # 寫入資料庫
        champ_json = json.dumps(team_champs, ensure_ascii=False)
        win_val = 1 if team_win else 0
        values = (match_id, champ_json, win_val, duration, timestamp)

        try:
            cursor.execute(sql, values)
            conn.commit()
            if cursor.rowcount == 1:
                total_inserted += 1
                print(f"✔ 成功寫入 ARAM 比賽：{match_id}")
            else:
                print("（已存在，略過）")
        except Exception as e:
            print("⚠ 寫入錯誤：", e)
            continue

cursor.close()
conn.close()

print("\n==============================")
print(f"🎉 批次完成！成功寫入 {total_inserted} 筆 ARAM 比賽")
print("==============================")
