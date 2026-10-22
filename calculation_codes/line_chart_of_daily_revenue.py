
import pandas as pd  
import matplotlib.pyplot as plt  
import numpy as np  
  
for i in range(1, 6):  
    o = pd.read_parquet(f"task4/cleaned/STORE{i}/orders.parquet")  
  
    daily = o.groupby("date")["paid_price"].sum().sort_index()  
    daily.index = pd.to_datetime(daily.index)  
  
    x = np.arange(len(daily))  
    x_smooth = np.linspace(x.min(), x.max(), len(x) * 10)  
    y_smooth = np.interp(x_smooth, x, daily.values)  
  
    plt.figure(figsize=(12, 5))  
    plt.plot(  
        daily.index[0] + pd.to_timedelta(x_smooth, unit="D"),  
        y_smooth,  
        linewidth=2  
    )  
  
    plt.title(f"STORE{i} Daily Revenue")  
    plt.xlabel("Date")  
    plt.ylabel("Revenue")  
    plt.tight_layout()  
  
plt.show()