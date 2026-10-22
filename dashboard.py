import streamlit as st
import pandas as pd
import yaml, json, os
from pathlib import Path
import plotly.express as px
from groq import Groq

st.set_page_config(page_title="Bookstore Analytics", page_icon="📚", layout="wide")
st.markdown("<style>div[data-testid=stMetric]{background:#1e293b;padding:12px;border-radius:8px}</style>", unsafe_allow_html=True)

DATA, STORES = Path("data/cleaned"), [f"STORE{i}" for i in range(1, 6)]

@st.cache_data
def load():
    o, u, b = [], [], []
    for s in STORES:
        p = DATA / s
        df = pd.read_parquet(p / "orders.parquet").assign(store=s)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        o.append(df)
        u.append(pd.read_csv(p / "users.csv").assign(store=s))
        b.append(pd.DataFrame(yaml.safe_load(open(p / "books.yaml"))).assign(store=s))
    return pd.concat(o).assign(revenue=lambda x: x.paid_price), pd.concat(u), pd.concat(b)

orders, users, books = load()

# ── Tools ───────────────────────────────────────────────────
def tool_unique_users(store=None):
    df = orders if not store or store == "All" else orders[orders.store == store]
    return int(df.user_id.nunique())

def tool_unique_authors(store=None):
    df = books if not store or store == "All" else books[books.store == store]
    return int(df.author.nunique())

def tool_top_days(n=5, store=None):
    df = orders if not store or store == "All" else orders[orders.store == store]
    top = df.groupby("date").revenue.sum().nlargest(n).reset_index()
    top["date"] = top.date.astype(str)
    return top.to_dict("records")

def tool_popular_authors(store=None):
    df = orders if not store or store == "All" else orders[orders.store == store]
    m = df.merge(books[["id", "author"]].drop_duplicates(), left_on="book_id", right_on="id")
    return m.groupby("author").quantity.sum().nlargest(3).to_dict()

def tool_best_buyers(store=None):
    df = orders if not store or store == "All" else orders[orders.store == store]
    return df.groupby("user_id").revenue.sum().nlargest(5).round(2).to_dict()

def tool_revenue(store=None):
    df = orders if not store or store == "All" else orders[orders.store == store]
    return round(float(df.revenue.sum()), 2)

def tool_most_sold_book(store=None):
    df = orders if not store or store == "All" else orders[orders.store == store]
    m = df.merge(books[["id", "title", "author"]].drop_duplicates(), left_on="book_id", right_on="id")
    top = m.groupby(["title", "author"]).quantity.sum().nlargest(1)
    return [{"title": t, "author": a, "quantity": int(q)} for (t, a), q in top.items()]

TOOLS = [
    {"type": "function", "function": {"name": "tool_unique_users", "description": "Unique users count", "parameters": {"type": "object", "properties": {"store": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "tool_unique_authors", "description": "Unique authors count", "parameters": {"type": "object", "properties": {"store": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "tool_top_days", "description": "Top N days by revenue", "parameters": {"type": "object", "properties": {"n": {"type": "integer"}, "store": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "tool_popular_authors", "description": "Most popular authors", "parameters": {"type": "object", "properties": {"store": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "tool_best_buyers", "description": "Best buyers by revenue", "parameters": {"type": "object", "properties": {"store": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "tool_revenue", "description": "Total revenue", "parameters": {"type": "object", "properties": {"store": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "tool_most_sold_book", "description": "Most sold book by quantity", "parameters": {"type": "object", "properties": {"store": {"type": "string"}}}}},
]
TOOL_MAP = {t["function"]["name"]: globals()[t["function"]["name"]] for t in TOOLS}

# ── UI ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("📚 Bookstore")
    sel = st.selectbox("Store", ["All stores"] + STORES)

o = orders if sel == "All stores" else orders[orders.store == sel]
b = books if sel == "All stores" else books[books.store == sel]
daily = o.groupby("date", as_index=False).revenue.sum().sort_values("revenue", ascending=False)
top5 = daily.head(5).assign(date=lambda x: x.date.astype(str), fmt=lambda x: x.revenue.map("${:,.2f}".format))
pop = o.merge(b[["id", "author"]].drop_duplicates(), left_on="book_id", right_on="id").groupby("author").quantity.sum().nlargest(1)
best = o.groupby("user_id").revenue.sum().nlargest(1)

st.title("Bookstore Analytics")
st.caption(f"Viewing: **{sel}**")
t1, t2, t3, t4 = st.tabs(["Overview", "Daily Revenue", "Top 5 Days", "Chat"])

with t1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique Users", f"{o.user_id.nunique():,}")
    c2.metric("Unique Authors", f"{b.author.nunique():,}")
    c3.metric("Orders", f"{len(o):,}")
    c4.metric("Revenue", f"${o.revenue.sum():,.0f}")
    st.write("**Most popular author(s):**", ", ".join(pop.index) or "—")
    st.write("**Best buyer ids:**", best.index.tolist())

with t2:
    fig = px.area(daily.sort_values("date"), x="date", y="revenue", template="plotly_dark")
    fig.update_layout(height=420, xaxis_tickformat="%Y-%m-%d")
    st.plotly_chart(fig, use_container_width=True)

with t3:
    st.dataframe(top5[["date", "fmt"]].rename(columns={"date": "Date (YYYY-MM-dd)", "fmt": "Revenue"}), hide_index=True)
    fig = px.bar(top5, x="date", y="revenue", text="fmt", template="plotly_dark", color_discrete_sequence=["#3b82f6"])
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

# ── Chat (Part 2) ───────────────────────────────────────────
with t4:
    if "msgs" not in st.session_state:
        st.session_state.msgs = [{"role": "system", "content": "You are a data analyst. Always use tools for any numbers or lists. Never invent data. Stores: STORE1-STORE5 or All."}]

    for m in st.session_state.msgs:
        if m["role"] in ("user", "assistant"):
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

    if q := st.chat_input("Ask about the data..."):
        st.session_state.msgs.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)

        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        with st.chat_message("assistant"):
            res = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=st.session_state.msgs,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0
            )
            msg = res.choices[0].message

            if msg.tool_calls:
                st.session_state.msgs.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in msg.tool_calls]
                })
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments or "{}")
                    result = TOOL_MAP[tc.function.name](**args)
                    st.session_state.msgs.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.function.name,
                        "content": json.dumps(result, default=str)
                    })
                res2 = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=st.session_state.msgs,
                    temperature=0
                )
                answer = res2.choices[0].message.content
            else:
                answer = msg.content

            st.markdown(answer)
            st.session_state.msgs.append({"role": "assistant", "content": answer})
