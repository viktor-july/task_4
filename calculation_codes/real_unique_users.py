
import pandas as pd

cols = ["name", "address", "phone", "email"]

for i in range(1, 6):
    u = pd.read_csv(f"task4/cleaned/STORE{i}/users.csv").fillna("").astype(str)[cols]
    parent = list(range(len(u)))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    seen = {}
    for j, row in enumerate(u.itertuples(index=False, name=None)):
        for k in range(4):
            key = (k, row[:k] + row[k+1:])
            if key in seen: parent[find(j)] = find(seen[key])
            else: seen[key] = j
    print(f"STORE{i}: {len({find(j) for j in range(len(u))})} real unique users")