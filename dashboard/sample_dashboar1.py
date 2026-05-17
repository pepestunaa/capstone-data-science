import streamlit as st
import pandas as pd
import plotly.express as px

# Page Config
st.set_page_config(
    page_title="Bank Churn Dashboard",
    page_icon="🏦",
    layout="wide",
)

# Load Data
@st.cache_data
def load_data():
    return pd.read_csv("data_clean.csv")

df = load_data()

CHURN_COLOR    = "#ef4444"
RETAINED_COLOR = "#22c55e"

# Sidebar Filters
with st.sidebar:
    st.title("🏦 Churn Dashboard")
    st.markdown("---")
    st.subheader("Filter Data")

    gender_opt = ["All"] + sorted(df["gender"].unique().tolist())
    sel_gender = st.selectbox("Gender", gender_opt)

    income_opt = ["All"] + df["income_category"].value_counts().index.tolist()
    sel_income = st.selectbox("Income Category", income_opt)

    age_min, age_max = int(df["customer_age"].min()), int(df["customer_age"].max())
    sel_age = st.slider("Age Range", age_min, age_max, (age_min, age_max))

    st.markdown("---")
    st.caption(f"Total data: **{len(df):,}** baris")

# Apply Filters
dff = df.copy()
if sel_gender != "All":
    dff = dff[dff["gender"] == sel_gender]
if sel_income != "All":
    dff = dff[dff["income_category"] == sel_income]
dff = dff[(dff["customer_age"] >= sel_age[0]) & (dff["customer_age"] <= sel_age[1])]

total    = len(dff)
churned  = (dff["attrition_flag"] == "Attrited Customer").sum()
retained = total - churned
churn_rate = churned / total * 100 if total > 0 else 0

# Header
st.title("🏦 Bank Customer Churn Dashboard")
st.caption("Analisis churn pelanggan kartu kredit bank")
st.markdown("---")

# KPI Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Pelanggan",   f"{total:,}")
col2.metric("Pelanggan Churn",   f"{churned:,}", delta=f"{churn_rate:.1f}% churn rate", delta_color="inverse")
col3.metric("Pelanggan Aktif",   f"{retained:,}", delta=f"{100 - churn_rate:.1f}% retained")
col4.metric("Rata-rata Transaksi", f"${dff['total_trans_amt'].mean():,.0f}")

st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Overview", "👥 Demografi", "💳 Transaksi"])

# TAB 1 — OVERVIEW
with tab1:
    col_a, col_b = st.columns(2)

    # Donut chart: Distribusi Attrition
    with col_a:
        st.subheader("Distribusi Attrition")
        pie_data = dff["attrition_flag"].value_counts().reset_index()
        pie_data.columns = ["Status", "Count"]
        fig_pie = px.pie(
            pie_data, values="Count", names="Status", hole=0.5,
            color="Status",
            color_discrete_map={
                "Existing Customer": RETAINED_COLOR,
                "Attrited Customer": CHURN_COLOR,
            },
        )
        fig_pie.update_traces(textinfo="percent+label")
        fig_pie.update_layout(showlegend=False, height=320,
                              annotations=[dict(text=f"<b>{churn_rate:.1f}%</b><br>Churn",
                                               x=0.5, y=0.5, showarrow=False,
                                               font_size=16, font_color=CHURN_COLOR)])
        st.plotly_chart(fig_pie, use_container_width=True)

    # Bar chart: Churn per Card Category
    with col_b:
        st.subheader("Churn per Card Category")
        card_data = dff.groupby(["card_category", "attrition_flag"]).size().reset_index(name="count")
        total_per_card = card_data.groupby("card_category")["count"].transform("sum")
        card_data["pct"] = card_data["count"] / total_per_card * 100
        fig_card = px.bar(
            card_data, x="card_category", y="pct", color="attrition_flag",
            barmode="stack", text_auto=".1f",
            color_discrete_map={"Existing Customer": RETAINED_COLOR, "Attrited Customer": CHURN_COLOR},
            labels={"pct": "Persentase (%)", "card_category": "Kategori Kartu", "attrition_flag": "Status"},
        )
        fig_card.update_layout(height=320, legend_title="Status")
        st.plotly_chart(fig_card, use_container_width=True)

    # Tabel statistik ringkas
    st.subheader("Statistik Ringkas")
    stats_cols = ["customer_age", "credit_limit", "total_trans_amt", "total_trans_ct", "avg_utilization_ratio"]
    stats_labels = {
        "customer_age": "Umur",
        "credit_limit": "Kredit Limit",
        "total_trans_amt": "Total Transaksi (Rp)",
        "total_trans_ct": "Jumlah Transaksi",
        "avg_utilization_ratio": "Utilisasi Rata-rata",
    }
    desc = dff[stats_cols].describe().T.round(2)
    desc.index = [stats_labels[c] for c in stats_cols]
    st.dataframe(desc[["mean", "std", "min", "50%", "max"]], use_container_width=True)

    st.info(f"💡 Dari total **{total:,}** pelanggan, sebanyak **{churned:,}** ({churn_rate:.1f}%) melakukan churn. "
            f"Pelanggan churn cenderung memiliki frekuensi transaksi lebih rendah.")

# TAB 2 — DEMOGRAFI
with tab2:
    churned_df = dff[dff["attrition_flag"] == "Attrited Customer"]

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Churn by Gender")
        gen_pct = churned_df["gender"].value_counts(normalize=True).reset_index()
        gen_pct.columns = ["Gender", "Persentase"]
        gen_pct["Persentase"] *= 100
        fig_gen = px.bar(gen_pct, x="Gender", y="Persentase", text_auto=".1f",
                         color="Gender", color_discrete_sequence=px.colors.qualitative.Set2)
        fig_gen.update_layout(showlegend=False, height=280,
                              yaxis_title="% dari Churn")
        st.plotly_chart(fig_gen, use_container_width=True)

    with col_b:
        st.subheader("Churn by Income Category")
        inc_pct = churned_df["income_category"].value_counts(normalize=True).reset_index()
        inc_pct.columns = ["Income", "Persentase"]
        inc_pct["Persentase"] *= 100
        inc_pct = inc_pct.sort_values("Persentase")
        fig_inc = px.bar(inc_pct, x="Persentase", y="Income", orientation="h",
                         text_auto=".1f", color="Income",
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig_inc.update_layout(showlegend=False, height=280,
                              xaxis_title="% dari Churn")
        st.plotly_chart(fig_inc, use_container_width=True)

    # Churn Rate per Kelompok Usia
    st.subheader("Churn Rate per Kelompok Usia")
    dff_age = dff.copy()
    dff_age["Kelompok Usia"] = pd.cut(
        dff_age["customer_age"],
        bins=[25, 35, 45, 55, 65, 100],
        labels=["26-35", "36-45", "46-55", "56-65", "66+"]
    )
    age_data = dff_age.groupby(["Kelompok Usia", "attrition_flag"], observed=False).size().reset_index(name="count")
    age_total = age_data.groupby("Kelompok Usia")["count"].transform("sum")
    age_data["pct"] = age_data["count"] / age_total * 100
    fig_age = px.bar(
        age_data, x="Kelompok Usia", y="pct", color="attrition_flag",
        barmode="group", text_auto=".1f",
        color_discrete_map={"Existing Customer": RETAINED_COLOR, "Attrited Customer": CHURN_COLOR},
        labels={"pct": "Persentase (%)", "attrition_flag": "Status"},
    )
    fig_age.update_layout(height=320, legend_title="Status")
    st.plotly_chart(fig_age, use_container_width=True)

    st.info("💡 Pelanggan **perempuan** cenderung lebih banyak churn. Kelompok usia **46–55 tahun** memiliki churn tertinggi.")

# TAB 3 — TRANSAKSI
with tab3:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Distribusi Jumlah Transaksi")
        fig_hist = px.histogram(
            dff, x="total_trans_ct", color="attrition_flag",
            nbins=40, opacity=0.75, barmode="overlay",
            color_discrete_map={"Existing Customer": RETAINED_COLOR, "Attrited Customer": CHURN_COLOR},
            labels={"total_trans_ct": "Jumlah Transaksi", "attrition_flag": "Status"},
        )
        fig_hist.update_layout(height=300, legend_title="Status")
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_b:
        st.subheader("Distribusi Nilai Transaksi")
        fig_hist2 = px.histogram(
            dff, x="total_trans_amt", color="attrition_flag",
            nbins=40, opacity=0.75, barmode="overlay",
            color_discrete_map={"Existing Customer": RETAINED_COLOR, "Attrited Customer": CHURN_COLOR},
            labels={"total_trans_amt": "Nilai Transaksi ($)", "attrition_flag": "Status"},
        )
        fig_hist2.update_layout(height=300, legend_title="Status")
        st.plotly_chart(fig_hist2, use_container_width=True)

    # Scatter plot
    st.subheader("Nilai vs Jumlah Transaksi")
    sample = dff.sample(min(2000, len(dff)), random_state=42)
    fig_scatter = px.scatter(
        sample, x="total_trans_ct", y="total_trans_amt",
        color="attrition_flag", opacity=0.6,
        color_discrete_map={"Existing Customer": RETAINED_COLOR, "Attrited Customer": CHURN_COLOR},
        labels={
            "total_trans_ct": "Jumlah Transaksi",
            "total_trans_amt": "Nilai Transaksi ($)",
            "attrition_flag": "Status",
        },
    )
    fig_scatter.update_layout(height=360, legend_title="Status")
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.info("💡 Pelanggan yang **churn** memiliki jumlah dan nilai transaksi yang lebih **rendah** "
            "dibanding pelanggan aktif. Ini menjadi indikator utama potensi churn.")
