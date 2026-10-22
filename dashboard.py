import streamlit as st
import pandas as pd
import yaml
from pathlib import Path
import plotly.express as px

st.set_page_config(
    page_title="Bookstore Dashboard",
    page_icon="📚",
    layout="wide",
)

DATA_ROOT = Path("data/cleaned")
STORES = [f"STORE{i}" for i in range(1, 6)]


@st.cache_data(show_spinner="Loading data…")
def load_all_data():
    orders_list, users_list, books_list = [], [], []

    for store in STORES:
        store_path = DATA_ROOT / store

        o = pd.read_parquet(store_path / "orders.parquet")
        o["store"] = store
        o["date"] = pd.to_datetime(o["date"]).dt.date
        orders_list.append(o)

        u = pd.read_csv(store_path / "users.csv")
        u["store"] = store
        users_list.append(u)

        with open(store_path / "books.yaml", encoding="utf-8") as f:
            books_raw = yaml.safe_load(f)
        b = pd.DataFrame(books_raw)
        b["store"] = store
        books_list.append(b)

    orders = pd.concat(orders_list, ignore_index=True)
    users = pd.concat(users_list, ignore_index=True)
    books = pd.concat(books_list, ignore_index=True)

    orders["revenue"] = orders["paid_price"]

    return orders, users, books


orders, users, books = load_all_data()

st.sidebar.title("Store filter")
selected = st.sidebar.selectbox(
    "Choose store",
    options=["All stores"] + STORES,
    index=0,
)

if selected == "All stores":
    o = orders
    u = users
    b = books
else:
    o = orders[orders["store"] == selected]
    u = users[users["store"] == selected]
    b = books[books["store"] == selected]

# 1. Top 5 days by revenue (YYYY-MM-dd)
daily_rev = (
    o.groupby("date", as_index=False)["revenue"]
    .sum()
    .sort_values("revenue", ascending=False)
)
top5 = daily_rev.head(5).copy()
top5["date"] = top5["date"].apply(lambda d: d.strftime("%Y-%m-%d"))

n_unique_users = o["user_id"].nunique()

n_unique_authors = b["author"].nunique()

merged = o.merge(
    b[["id", "author"]].drop_duplicates(),
    left_on="book_id",
    right_on="id",
    how="left",
)
author_stats = (
    merged.groupby("author", as_index=False)["quantity"]
    .sum()
    .sort_values("quantity", ascending=False)
)
if not author_stats.empty:
    max_qty = author_stats["quantity"].iloc[0]
    most_popular = author_stats[author_stats["quantity"] == max_qty]["author"].tolist()
else:
    most_popular = []

buyer_stats = (
    o.groupby("user_id", as_index=False)["revenue"]
    .sum()
    .sort_values("revenue", ascending=False)
)
if not buyer_stats.empty:
    max_spend = buyer_stats["revenue"].iloc[0]
    best_buyers = buyer_stats[buyer_stats["revenue"] == max_spend]["user_id"].tolist()
else:
    best_buyers = []

st.title("📚 Bookstore Multi-Store Dashboard")
st.caption(f"Currently viewing: **{selected}**")

tab1, tab2, tab3 = st.tabs([
    "Overview metrics",
    "Daily revenue chart",
    "Top 5 days detail",
])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Unique users", f"{n_unique_users:,}")
    c2.metric("Unique authors", f"{n_unique_authors:,}")
    c3.metric("Total orders", f"{len(o):,}")

    st.subheader("Most popular author(s)")
    st.write(most_popular if most_popular else "—")

    st.subheader("Best buyer (with aliases) – array of ids")
    st.code(str(best_buyers))

with tab2:
    st.subheader("Daily revenue")
    daily_sorted = daily_rev.sort_values("date")
    fig = px.line(
        daily_sorted,
        x="date",
        y="revenue",
        title=f"Daily revenue – {selected}",
        labels={"date": "Date", "revenue": "Revenue"},
    )
    fig.update_layout(xaxis_tickformat="%Y-%m-%d")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Top 5 days by revenue (YYYY-MM-dd)")
    st.dataframe(
        top5[["date", "revenue"]].rename(columns={"date": "Date (YYYY-MM-dd)", "revenue": "Revenue"}),
        use_container_width=True,
        hide_index=True,
    )

st.sidebar.markdown("---")
st.sidebar.info("Data: orders.parquet + users.csv + books.yaml\n(STORE1–STORE5)")