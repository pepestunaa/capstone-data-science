import pandas as pd
import plotly.express as px
import streamlit as st

# Konfigurasi Halaman
st.set_page_config(
    page_title="Bank Churn Analysis Dashboard",
    page_icon="🏦",
    layout="wide",
)


# Load Data
@st.cache_data
def load_data():
    return pd.read_csv("dashboard/data_clean.csv")


df = load_data()

# Branding Warna
CHURN_COLOR = "#FF4B4B"
RETAINED_COLOR = "#0068C9"

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.title("🏦 Filter Dashboard")
    st.markdown("---")

    # Filter Gender
    gender_opt = ["All"] + sorted(df["gender"].unique().tolist())
    sel_gender = st.selectbox("Pilih Gender", gender_opt)

    # Filter Card Category
    card_opt = ["All"] + sorted(df["card_category"].unique().tolist())
    sel_card = st.selectbox("Pilih Kategori Kartu", card_opt)

    # Filter Age
    age_min, age_max = int(df["customer_age"].min()), int(df["customer_age"].max())
    sel_age = st.slider("Rentang Usia", age_min, age_max, (age_min, age_max))

# Jalankan Filter
dff = df.copy()
if sel_gender != "All":
    dff = dff[dff["gender"] == sel_gender]
if sel_card != "All":
    dff = dff[dff["card_category"] == sel_card]
dff = dff[(dff["customer_age"] >= sel_age[0]) & (dff["customer_age"] <= sel_age[1])]

# Perhitungan Metrik
total_cust = len(dff)
churned = (dff["attrition_flag"] == "Attrited Customer").sum()
churn_rate = (churned / total_cust * 100) if total_cust > 0 else 0

# --- HEADER ---
st.title("🏦 Bank Customer Churn Executive Dashboard")
st.markdown(
    f"Analisis profil risiko dan perilaku transaksi pelanggan. | Total Data Terfilter: **{total_cust:,}**"
)
st.markdown("---")

# --- KPI METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Pelanggan", f"{total_cust:,}")
col2.metric(
    "Pelanggan Churn",
    f"{churned:,}",
    delta=f"{churn_rate:.1f}% churn rate",
    delta_color="inverse",
)
col3.metric("Rata-rata Transaksi", f"${dff['total_trans_amt'].mean():,.0f}")
col4.metric("Rata-rata Usia", f"{dff['customer_age'].mean():.1f} thn")

st.markdown("---")

# --- VISUALISASI JAWABAN PERTANYAAN BISNIS ---
tab1, tab2 = st.tabs(["📊 Analisis Strategis", "👥 Profil Demografi"])

with tab1:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Q1: Churn Berdasarkan Kategori Kartu")
        # Analisis Card Category
        card_analysis = (
            dff.groupby(["card_category", "attrition_flag"], observed=False)
            .size()
            .reset_index(name="count")
        )
        card_total = card_analysis.groupby("card_category")["count"].transform("sum")
        card_analysis["percentage"] = card_analysis["count"] / card_total * 100

        fig_card = px.bar(
            card_analysis,
            x="card_category",
            y="percentage",
            color="attrition_flag",
            barmode="group",
            text_auto=".1f",
            color_discrete_map={
                "Existing Customer": RETAINED_COLOR,
                "Attrited Customer": CHURN_COLOR,
            },
            labels={"percentage": "Proporsi (%)", "card_category": "Kategori Kartu"},
        )
        st.plotly_chart(fig_card, use_container_width=True)
        st.info(
            "💡 Kategori Platinum memiliki tingkat churn proporsional tertinggi meskipun Blue Card memiliki volume terbanyak."
        )
        st.warning(
            "📌 **Kesimpulan Q1:** Blue Card **tidak terbukti** memiliki churn 50% lebih tinggi. "
            "Secara proporsional: Platinum 25% > Gold 18.1% > Blue 16.1% > Silver 14.8%."
        )

    with col_b:
        st.subheader("Q2: Pengaruh Nominal Transaksi")
        # Analisis Trans Amt Group
        dff["trans_amt_group"] = pd.cut(
            dff["total_trans_amt"],
            bins=[-1, 2500, 5000, 100000],
            labels=["$0-2500", "$2501-5000", "$5000+"],
        )
        trans_analysis = (
            dff.groupby(["trans_amt_group", "attrition_flag"], observed=False)
            .size()
            .reset_index(name="count")
        )
        trans_total = trans_analysis.groupby("trans_amt_group")["count"].transform(
            "sum"
        )
        trans_analysis["percentage"] = trans_analysis["count"] / trans_total * 100

        fig_trans = px.bar(
            trans_analysis,
            x="trans_amt_group",
            y="percentage",
            color="attrition_flag",
            barmode="group",
            text_auto=".1f",
            color_discrete_map={
                "Existing Customer": RETAINED_COLOR,
                "Attrited Customer": CHURN_COLOR,
            },
            labels={
                "percentage": "Proporsi (%)",
                "trans_amt_group": "Rentang Transaksi",
            },
        )
        st.plotly_chart(fig_trans, use_container_width=True)
        st.info(
            "Customer dengan transaksi di bawah \$2500 memiliki risiko churn 2x lebih tinggi dibanding kelompok \$5000+."
        )
        st.warning(
            "📌 **Kesimpulan Q2:** Churn \$0–2500 (30.84%) vs \$5000+ (13.57%), selisih 17.27% — "
            "tidak mencapai target 40% yang dihipotesiskan, namun tren pengaruhnya terbukti signifikan."
        )

with tab2:
    churned_df = dff[dff["attrition_flag"] == "Attrited Customer"]

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("Distribusi Churn by Gender")
        fig_gen = px.pie(
            churned_df,
            names="gender",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig_gen, use_container_width=True)

    with col_d:
        st.subheader("Inaktivitas vs Churn")
        fig_inact = px.box(
            dff,
            x="attrition_flag",
            y="months_inactive_12_mon",
            color="attrition_flag",
            color_discrete_map={
                "Existing Customer": RETAINED_COLOR,
                "Attrited Customer": CHURN_COLOR,
            },
        )
        st.plotly_chart(fig_inact, use_container_width=True)

    # Baris tambahan: Income Category & Age Group
    col_e, col_f = st.columns(2)

    with col_e:
        st.subheader("Churn by Income Category")
        inc_pct = (
            churned_df["income_category"].value_counts(normalize=True).reset_index()
        )
        inc_pct.columns = ["Income", "Persentase"]
        inc_pct["Persentase"] *= 100
        fig_inc = px.bar(
            inc_pct.sort_values("Persentase"),
            x="Persentase",
            y="Income",
            orientation="h",
            text_auto=".1f",
            labels={"Persentase": "% dari Total Churn", "Income": "Kategori Income"},
            color_discrete_sequence=[CHURN_COLOR],
        )
        fig_inc.update_layout(showlegend=False)
        st.plotly_chart(fig_inc, use_container_width=True)

    with col_f:
        st.subheader("Churn Rate per Kelompok Usia")
        dff_age = dff.copy()
        dff_age["Kelompok Usia"] = pd.cut(
            dff_age["customer_age"],
            bins=[25, 35, 45, 55, 65, 100],
            labels=["26-35", "36-45", "46-55", "56-65", "66+"],
        )
        age_data = (
            dff_age.groupby(["Kelompok Usia", "attrition_flag"], observed=False)
            .size()
            .reset_index(name="count")
        )
        age_data["pct"] = (
            age_data["count"]
            / age_data.groupby("Kelompok Usia")["count"].transform("sum")
            * 100
        )
        fig_age = px.bar(
            age_data,
            x="Kelompok Usia",
            y="pct",
            color="attrition_flag",
            barmode="group",
            text_auto=".1f",
            color_discrete_map={
                "Existing Customer": RETAINED_COLOR,
                "Attrited Customer": CHURN_COLOR,
            },
            labels={"pct": "Proporsi (%)", "attrition_flag": "Status"},
        )
        fig_age.update_layout(legend_title="Status")
        st.plotly_chart(fig_age, use_container_width=True)

    st.info(
        "💡 Perempuan lebih banyak churn (57.2%). Income <$40K tertinggi (37.6%). Kelompok usia 46–55 tahun paling rentan churn (42.3%)."
    )
