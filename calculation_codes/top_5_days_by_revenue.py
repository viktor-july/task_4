import pandas as pd  
  
for i in range(1, 6):  
    o = pd.read_parquet(f"task4/cleaned/STORE{i}/orders.parquet")  
    top = o.groupby("date")["paid_price"].sum().sort_values(ascending=False).head(5)  
    print(f"=== STORE{i} ===")  
    print(top)  
    print()