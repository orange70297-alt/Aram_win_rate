import requests
import time

API_KEY = "RGAPI-06a8dfea-346c-468b-beb6-c21299bea06e"
headers = {"X-Riot-Token": API_KEY}

# ================================
# 安全 request（含 429 重試）
# ================================
def safe_request(url, max_retry=5):
    retry = 0
    while retry < max_retry:
        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            return res

        if res.status_code == 429:
            wait = 3 + retry
            print(f"⚠ 429 限速 — 等待 {wait} 秒後重試")
            time.sleep(wait)
            retry += 1
            continue

        print(f"⚠ API 錯誤 {res.status_code}，略過")
        return None

    return None


# ================================
# 抓最近 N 場比賽
# ================================
def get_recent_match_ids(puuid, count=20):
    url = f"https://sea.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
    res = safe_request(url)
    if res is None:
        return []
    return res.json()


# ================================
# 抓 queueId
# ================================
def get_queue_id(match_id):
    url = f"https://sea.api.riotgames.com/lol/match/v5/matches/{match_id}"
    res = safe_request(url)
    if res is None:
        return None
    return res.json()["info"]["queueId"]


# ================================
# 判斷是否常玩 ARAM
# ================================
def is_aram_player(puuid, threshold=0.2):
    match_ids = get_recent_match_ids(puuid, count=20)

    if len(match_ids) == 0:
        return False

    aram = 0

    for mid in match_ids:
        qid = get_queue_id(mid)
        if qid == 450:
            aram += 1

        time.sleep(1.2)  # 安全限速

    ratio = aram / len(match_ids)
    print(f"{puuid} — ARAM 比例：{ratio:.2f}")

    return ratio >= threshold


# ================================
# 分批處理 PUUID
# ================================
def batch_process(all_puuids, batch_size=100):
    all_puuids = list(all_puuids)

    for i in range(0, len(all_puuids), batch_size):
        batch = all_puuids[i : i+batch_size]
        print(f"\n===== 處理第 {i//batch_size + 1} 批：{len(batch)} 人 =====")

        result_file = f"aram_players_batch_{i//batch_size + 1}.txt"
        f = open(result_file, "w", encoding="utf-8")

        for puuid in batch:
            print(f"\n→ 檢查玩家：{puuid}")

            if is_aram_player(puuid):
                f.write(puuid + "\n")
                f.flush()
                print("✔ 加入 ARAM 玩家名單")
            else:
                print("✖ 非 ARAM 玩家")

        f.close()
        print(f"📄 批次完成：已輸出 {result_file}")
        print("休息 10 秒避免 API 過熱…\n")
        time.sleep(10)


# ================================
# MAIN：從 txt 讀入 PUUID
# ================================
if __name__ == "__main__":
    with open("collected_puuids.txt", "r", encoding="utf-8") as f:
        puuids = set(line.strip() for line in f if line.strip())

    print(f"成功讀取 {len(puuids)} 個 PUUID")
    batch_process(puuids, batch_size=100)
