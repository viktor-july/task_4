
import pandas as pd  
import yaml  
import re   
  
for i in range(1, 6):  
    o = pd.read_parquet(f"task4/cleaned/STORE{i}/orders.parquet")  
    b = pd.DataFrame(yaml.safe_load(open(f"task4/cleaned/STORE{i}/books.yaml")))  
    b["author_set"] = b["author"].map(lambda x: frozenset(re.split(r"\s*,\s*|\s+and\s+|\s*&\s*", str(x).strip())) if pd.notna(x) else frozenset())  
    m = o.merge(b[["id", "author_set"]], left_on="book_id", right_on="id")  
    top = m.groupby("author_set")["quantity"].sum().sort_values(ascending=False).head(1)  
    print(f"=== STORE{i} ===")  
    print(top)  
    print()