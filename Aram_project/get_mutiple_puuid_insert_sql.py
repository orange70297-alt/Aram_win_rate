import pymysql
import requests
import time

API_KEY = "RGAPI-06a8dfea-346c-468b-beb6-c21299bea06e"
headers = {"X-Riot-Token": API_KEY}

# ==== MySQL 連線 ====
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="P@ssw0rd",
    database="lol_data",
    charset="utf8mb4"
)
cursor = conn.cursor()

# ==== 抓出所有 match_id ====
cursor.execute("SELECT match_id FROM aram_matches;")
match_ids = [row[0] for row in cursor.fetchall()]
print(f"共找到 {len(match_ids)} 個 match_id")

all_puuids = set()


# ==== 建立 API 請求函式（含錯誤處理） ====
def safe_request(url, headers, retry=3):
    """
    安全 request：遇到錯誤會自動 retry，避免程式崩潰
    """
    for attempt in range(retry):
        try:
            res = requests.get(url, headers=headers)

            # 429 Too Many Requests → 必須等待
            if res.status_code == 429:
                print("⚠ 429 限速，被 Riot 擋，休息 10 秒再試…")
                time.sleep(10)
                continue

            return res

        except Exception as e:
            print(f"⚠ Request 發生錯誤：{e}")
            time.sleep(3)

    return None


# ==== 逐筆處理 match_id → 收集 10 個 puuid ====
for i, match_id in enumerate(match_ids, start=1):

    print(f"處理 {i}/{len(match_ids)}：{match_id}")

    url = f"https://sea.api.riotgames.com/lol/match/v5/matches/{match_id}"
    res = safe_request(url, headers)

    if res is None or res.status_code != 200:
        print(f"⚠ 無法取得比賽資料（HTTP {res.status_code if res else 'None'}）略過")
        time.sleep(1)
        continue

    data = res.json()
    participants = data["info"]["participants"]

    # 收集 10 名玩家 PUUID
    for p in participants:
        all_puuids.add(p["puuid"])

    # 限速保護
    time.sleep(1)


# ==== 結果 ====
print("\n===========================")
print(f"🎉 完成！共蒐集到 {len(all_puuids)} 個不重複 PUUID")
print("===========================\n")

# （可選）輸出到檔案
with open("collected_puuids.txt", "w", encoding="utf-8") as f:
    for puuid in all_puuids:
        f.write(puuid + "\n")

print("已將 PUUID 寫入 collected_puuids.txt")
