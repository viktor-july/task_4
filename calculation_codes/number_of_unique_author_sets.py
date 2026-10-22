import pandas as pd
import re

for i in range(1, 6):
    b = pd.read_csv(f"task4/cleaned/STORE{i}/books.yaml") if False else None
    import yaml
    b = pd.DataFrame(yaml.safe_load(open(f"task4/cleaned/STORE{i}/books.yaml")))
    sets = b["author"].dropna().map(lambda x: frozenset(re.split(r"\s*,\s*|\s+and\s+|\s*&\s*", str(x).strip())))
    print(f"STORE{i}: {sets.nunique()} unique author sets")