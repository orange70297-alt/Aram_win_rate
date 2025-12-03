import pandas as pd

# ============================
# 模擬歷史比賽資料（假資料）
# ============================
# 每列代表一場 ARAM
# champs = 該隊伍5人
# win = 是否勝利

data = [
    (["Garen", "Lux", "Ezreal", "Sona", "Jinx"], 1),
    (["Garen", "Lux", "Ezreal", "Sona", "Ashe"], 0),
    (["Garen", "Lux", "Ezreal", "Sona", "Jhin"], 1),
    (["Garen", "Lux", "Ezreal", "Sona", "Vayne"], 0),
    (["Garen", "Lux", "Ezreal", "Sona", "Yasuo"], 1),
]

match_history = pd.DataFrame(data, columns=["champs", "win"])

# =====================================
# 計算：給定隊友4人 → 計算基本勝率
# =====================================
def calc_base_winrate(teammates, df):
    # 過濾「包含這4隻」的歷史對局
    cond = df["champs"].apply(lambda lst: all(champ in lst for champ in teammates))
    subset = df[cond]

    if len(subset) == 0:
        return None, 0

    winrate = subset["win"].mean()
    return subset, winrate


# =====================================
# 計算：加入候選角色 → 計算 5 人組合勝率
# =====================================
def calc_candidate_winrate(teammates, candidates, df):
    results = {}

    for cand in candidates:
        full_team = teammates + [cand]

        cond = df["champs"].apply(lambda lst: set(full_team) == set(lst))
        subset = df[cond]

        if len(subset) == 0:
            # 若沒有對局資料，用拉普拉斯平滑避免0%
            winrate = 0.5
        else:
            winrate = subset["win"].mean()

        results[cand] = winrate

    return results


# =====================================
# CLI 流程
# =====================================
print("=== 請輸入隊友 4 位英雄 ===")
teammates = []
for i in range(4):
    teammates.append(input(f"第 {i+1} 位英雄名稱：").strip())

print("\n=== 請輸入候選英雄（用空白分隔）===")
candidates = input("候選英雄：").split()

print("\n開始分析...\n")

# Step 1：隊友4人基本勝率
subset, base_winrate = calc_base_winrate(teammates, match_history)

print(f"隊友 4 人組合 {teammates} 的歷史勝率 = {base_winrate:.2%}")
print("-" * 50)

# Step 2：加入候選英雄後的勝率
results = calc_candidate_winrate(teammates, candidates, match_history)

print("候選角色勝率（由高到低）：")
sorted_res = sorted(results.items(), key=lambda x: x[1], reverse=True)

for champ, winrate in sorted_res:
    print(f"{champ:<10} → {winrate:.2%}")

best = sorted_res[0]
print("\n推薦你選：", best[0], f"(勝率 {best[1]:.2%})")
