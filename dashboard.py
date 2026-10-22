import streamlit as st
import pandas as pd
import yaml
from pathlib import Path
import plotly.express as px

st.set_page_config(page_title="Bookstore Analytics", page_icon="📚", layout="wide")
st.markdown("""<style>
div[data-testid="stMetric"]{background:#1e293b;border:1px solid #334155;padding:14px;border-radius:10px}
.tag{display:inline-block;background:#1e40af;color:#fff;padding:3px 10px;border-radius:16px;margin:2px;font-size:.85rem}
.tag-g{background:#047857}
</style>""", unsafe_allow_html=True)

DATA = Path("data/cleaned")
STORES = [f"STORE{i}" for i in range(1, 6)]

@st.cache_data
def load():
    o, u, b = [], [], []
    for s in STORES:
        p = DATA / s
        df = pd.read_parquet(p / "orders.parquet").assign(store=s)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        o.append(df)
        u.append(pd.read_csv(p / "users.csv").assign(store=s))
        with open(p / "books.yaml") as f:
            b.append(pd.DataFrame(yaml.safe_load(f)).assign(store=s))
    orders = pd.concat(o).assign(revenue=lambda x: x.paid_price)
    return orders, pd.concat(u), pd.concat(b)

orders, users, books = load()

with st.sidebar:
    st.title("📚 Bookstore")
    sel = st.selectbox("Store", ["All stores"] + STORES)

o = orders if sel == "All stores" else orders.query("store == @sel")
b = books if sel == "All stores" else books.query("store == @sel")

daily = o.groupby("date", as_index=False).revenue.sum().sort_values("revenue", ascending=False)
top5 = daily.head(5).assign(date=lambda x: x.date.map(lambda d: d.strftime("%Y-%m-%d")),
                            revenue_fmt=lambda x: x.revenue.map("${:,.2f}".format))

merged = o.merge(b[["id", "author"]].drop_duplicates(), left_on="book_id", right_on="id", how="left")
pop = merged.groupby("author").quantity.sum().nlargest(1)
best = o.groupby("user_id").revenue.sum().nlargest(1)

st.title("Bookstore Analytics Dashboard")
st.caption(f"Viewing: **{sel}**")

t1, t2, t3 = st.tabs(["📊 Overview", "📈 Daily Revenue", "🏆 Top 5 Days"])

with t1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique Users", f"{o.user_id.nunique():,}")
    c2.metric("Unique Authors", f"{b.author.nunique():,}")
    c3.metric("Orders", f"{len(o):,}")
    c4.metric("Revenue", f"${o.revenue.sum():,.0f}")

    st.markdown("**Most popular author(s)**")
    st.markdown("".join(f'<span class="tag">{a}</span>' for a in pop.index) or "—", unsafe_allow_html=True)

    st.markdown("**Best buyer (aliases) – array of ids**")
    ids = best.index.tolist()
    st.markdown("".join(f'<span class="tag tag-g">{i}</span>' for i in ids) or "—", unsafe_allow_html=True)
    st.code(str(ids))

with t2:
    fig = px.area(daily.sort_values("date"), x="date", y="revenue",
                  template="plotly_dark", labels={"revenue": "Revenue ($)"})
    fig.update_traces(line_color="#3b82f6", fillcolor="rgba(59,130,246,.25)")
    fig.update_layout(height=450, xaxis_tickformat="%Y-%m-%d", margin=dict(t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

with t3:
    st.dataframe(top5[["date", "revenue_fmt"]].rename(columns={"date": "Date (YYYY-MM-dd)", "revenue_fmt": "Revenue"}),
                 hide_index=True, use_container_width=True)
    fig = px.bar(top5, x="date", y="revenue", text="revenue_fmt", template="plotly_dark",
                 color_discrete_sequence=["#3b82f6"])
    fig.update_traces(textposition="outside")
    fig.update_layout(height=350, showlegend=False, margin=dict(t=20))
    st.plotly_chart(fig, use_container_width=True)
