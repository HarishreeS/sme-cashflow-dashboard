import streamlit as st
import pandas as pd
import plotly.express as px
from utils import compute_kpis, monthly_agg

st.set_page_config(page_title="SME Cashflow Insights Dashboard", page_icon="💳", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("data/synthetic_transactions.csv", parse_dates=["Date"])
    return df

df = load_data()

st.title("SME Cashflow Insights Dashboard")
st.caption("Personal Fintech Project — analyze SME cashflows, KPIs, and trends")

# Sidebar filters
st.sidebar.header("Filters")
min_date, max_date = df['Date'].min(), df['Date'].max()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

categories = sorted(df['Category'].unique())
sel_categories = st.sidebar.multiselect("Categories", categories, default=categories)

statuses = sorted(df['Payment_Status'].unique())
sel_status = st.sidebar.multiselect("Payment Status", statuses, default=statuses)

# Filter dataframe
mask = (
    (df['Date'] >= pd.Timestamp(date_range[0])) &
    (df['Date'] <= pd.Timestamp(date_range[1])) &
    (df['Category'].isin(sel_categories)) &
    (df['Payment_Status'].isin(sel_status))
)
fdf = df.loc[mask].copy()

# KPIs
kpis = compute_kpis(fdf, starting_cash=200000.0)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Inflows", f"₹{kpis['inflows']:,.0f}")
c2.metric("Total Outflows", f"₹{kpis['outflows']:,.0f}")
c3.metric("Net Cashflow", f"₹{kpis['net_cashflow']:,.0f}")
c4.metric("Burn Rate (avg/mo)", f"₹{kpis['burn_rate']:,.0f}")
runway_txt = "∞" if kpis['runway_months'] == float('inf') else f"{kpis['runway_months']:.1f} mo"
c5.metric("Runway", runway_txt)

st.metric("Outstanding Receivables", f"₹{kpis['outstanding_receivables']:,.0f}")

# Charts
st.subheader("Monthly Trends")
magg = monthly_agg(fdf)
if not magg.empty:
    fig_bar = px.bar(magg, x="Month", y=["Inflows","Outflows"], barmode="group", title="Monthly Inflows vs Outflows")
    st.plotly_chart(fig_bar, use_container_width=True)

    # Cash balance over time
    fdf_sorted = fdf.sort_values("Date").copy()
    fdf_sorted['SignedAmount'] = fdf_sorted.apply(lambda r: r['Amount'] if r['Transaction_Type']=="Inflow" else -r['Amount'], axis=1)
    fdf_sorted['Cash'] = fdf_sorted['SignedAmount'].cumsum() + 200000.0
    fig_line = px.line(fdf_sorted, x="Date", y="Cash", title="Cash Balance Over Time")
    st.plotly_chart(fig_line, use_container_width=True)

    # Category-wise spending (Outflows only)
    out = fdf[fdf['Transaction_Type']=="Outflow"].groupby("Category")['Amount'].sum().reset_index()
    if not out.empty:
        fig_cat = px.bar(out, x="Category", y="Amount", title="Category-wise Spending (Outflows)")
        st.plotly_chart(fig_cat, use_container_width=True)
else:
    st.info("No data for selected filters.")

# Data table + download
st.subheader("Filtered Transactions")
st.dataframe(fdf, use_container_width=True)

csv = fdf.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", data=csv, file_name="filtered_transactions.csv", mime="text/csv")