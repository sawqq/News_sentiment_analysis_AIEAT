import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from new_scraper  import get_news
from news_analysis_ollama import analyze

st.set_page_config(
    page_title="News Sentiment Tracker",
    layout="wide",
)

st.markdown("""
<style>
    .main { background: #0f1117; }
    .stTextInput > div > div > input { background: #1e2130; }
    .metric-card {
        background: #1e2130; border-radius: 12px; padding: 1rem 1.5rem;
        border-left: 4px solid #4f8ef7;
    }
    .sentiment-pos { color: #22c55e; font-weight: bold; }
    .sentiment-neg { color: #ef4444; font-weight: bold; }
    .sentiment-neu { color: #94a3b8; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("News Sentiment Tracker")
    st.caption("Named Entity Recognition + Sentiment Analysis")
    st.divider()

    url_input = st.text_input(
        "Article URL",
        placeholder="Example: https://www.bangkokpost.com/...",
    )

    filter_input = st.text_input(
        "Filter persons (optional)",
        placeholder="e.g. Paetongtarn, Thaksin",
        help="Comma-separated names. Leave blank to show all.",
    )

    analyze_btn = st.button("Analyze Article", use_container_width=True, type="primary")

    st.divider()

    # History stored in session
    if "history" not in st.session_state:
        st.session_state.history = []   # list of result dicts

    if st.session_state.history:
        st.caption(f"📋 {len(st.session_state.history)} article(s) analyzed this session")
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
            st.rerun()

st.title("News Entity & Sentiment Tracker")

if analyze_btn:
    if not url_input.strip():
        st.warning("Please enter a URL in the sidebar first.")
    else:
        filter_names = (
            [n.strip() for n in filter_input.split(",") if n.strip()]
            if filter_input else None
        )

        with st.status("Working…", expanded=True) as status:
            st.write("Scraping article…")
            try:
                article = get_news(url_input.strip())
            except ValueError as e:
                st.error(str(e))
                st.stop()

            st.write("Running NER + sentiment analysis via Ollama…")
            result = analyze(article["text"], filter_names=None)

            if "error" in result:
                st.error(result["error"])
                st.stop()

            # Merge article metadata into result for history
            result["_url"]   = article["url"]
            result["_title"] = article["title"]
            result["_date"]  = article["date"]
            st.session_state.history.append(result)

            status.update(label="Done!", state="complete")

if not st.session_state.history:
    st.info("Enter a news URL in the sidebar and click **Analyze Article** to get started.")
    st.stop()


latest = st.session_state.history[-1]

st.subheader(f"📄 {latest['_title']}")
st.caption(f"Published: {latest['_date']}  •  [Open article]({latest['_url']})")

if latest.get("summary"):
    with st.expander("📝 Article summary", expanded=True):
        st.write(latest["summary"])

st.divider()

persons = latest.get("persons", [])
sentiments = [p["sentiment"] for p in persons]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Persons found",   len(persons))
col2.metric("Positive",        sentiments.count("Positive"))
col3.metric("Negative",        sentiments.count("Negative"))
col4.metric("Neutral",         sentiments.count("Neutral"))

st.divider()

if persons:
    df = pd.DataFrame(persons)

    left, right = st.columns([1, 1])

    # Pie chart
    with left:
        st.subheader("Sentiment distribution")
        color_map = {"Positive": "#22c55e", "Negative": "#ef4444", "Neutral": "#94a3b8"}
        pie = px.pie(
            df, names="sentiment",
            color="sentiment",
            color_discrete_map=color_map,
            hole=0.45,
        )
        pie.update_traces(textposition="inside", textinfo="percent+label")
        pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(pie, use_container_width=True)

    # Bar chart: sentiment per person
    with right:
        st.subheader("Persons & sentiment")
        sentiment_order = {"Positive": 1, "Negative": -1, "Neutral": 0}
        df["_score"] = df["sentiment"].map(sentiment_order)
        bar = px.bar(
            df.sort_values("_score"),
            x="_score", y="name",
            orientation="h",
            color="sentiment",
            color_discrete_map=color_map,
            labels={"_score": "Sentiment score", "name": "Person"},
        )
        bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            xaxis=dict(tickvals=[-1, 0, 1], ticktext=["Negative", "Neutral", "Positive"]),
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(bar, use_container_width=True)

    # Person table
    st.subheader("Detailed entity table")

    def badge(s):
        colors = {"Positive": "🟢", "Negative": "🔴", "Neutral": "⚪"}
        return f"{colors.get(s, '⚪')} {s}"

    display_df = df[["name", "role", "sentiment", "reason"]].copy()
    display_df["sentiment"] = display_df["sentiment"].apply(badge)
    display_df.columns = ["Name", "Role", "Sentiment", "Reason"]
    display_df = display_df.fillna("—")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # CSV export
    csv = df[["name", "role", "sentiment", "reason"]].to_csv(index=False)
    st.download_button(
        "⬇️ Download CSV",
        data=csv,
        file_name="entities.csv",
        mime="text/csv",
    )

else:
    st.warning("No public persons were detected in this article.")

# ── Cross-article trend (if multiple articles analyzed in same session) ───────────────────────
if len(st.session_state.history) > 1:
    st.divider()
    st.subheader("📊 Cross-article trends")

    all_rows = []
    for entry in st.session_state.history:
        for p in entry.get("persons", []):
            all_rows.append({
                "article": entry["_title"][:50] + "…",
                "name":    p["name"],
                "sentiment": p["sentiment"],
            })

    if all_rows:
        all_df = pd.DataFrame(all_rows)
        top_persons = all_df["name"].value_counts().head(10).index.tolist()
        filtered = all_df[all_df["name"].isin(top_persons)]

        heat_data = (
            filtered.groupby(["name", "sentiment"])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=["Positive", "Neutral", "Negative"], fill_value=0)
        )

        fig = go.Figure(data=go.Heatmap(
            z=heat_data.values,
            x=heat_data.columns.tolist(),
            y=heat_data.index.tolist(),
            colorscale=[[0, "#1e2130"], [0.5, "#4f8ef7"], [1, "#22c55e"]],
            showscale=True,
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig, use_container_width=True)
