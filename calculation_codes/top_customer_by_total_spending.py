
import pandas as pd

cols = ["name", "address", "phone", "email"]

for i in range(1, 6):
    u = pd.read_csv(f"task4/cleaned/STORE{i}/users.csv")
    o = pd.read_parquet(f"task4/cleaned/STORE{i}/orders.parquet")
    
    u[cols] = u[cols].fillna("").astype(str)
    parent = list(range(len(u)))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    
    seen = {}
    for j, row in enumerate(u[cols].itertuples(index=False, name=None)):
        for k in range(4):
            key = (k, row[:k] + row[k+1:])
            if key in seen: parent[find(j)] = find(seen[key])
            else: seen[key] = j
    
    u["comp"] = [find(j) for j in range(len(u))]
    spend = o.merge(u[["id", "comp"]], left_on="user_id", right_on="id")
    top = spend.groupby("comp")["paid_price"].sum().idxmax()
    ids = u.loc[u["comp"] == top, "id"].tolist()
    total = spend.loc[spend["comp"] == top, "paid_price"].sum()
    
    print(f"STORE{i}: {total:.2f}")
    print("user_ids:", ids)
    print()