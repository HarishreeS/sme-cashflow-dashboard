import pandas as pd
import numpy as np

def compute_kpis(df: pd.DataFrame, starting_cash: float = 200000.0):
    if df.empty:
        return {
            "inflows": 0.0,
            "outflows": 0.0,
            "net_cashflow": 0.0,
            "burn_rate": 0.0,
            "runway_months": float("inf"),
            "outstanding_receivables": 0.0,
            "cash_series": pd.Series(dtype=float),
        }

    df = df.copy()
    df['SignedAmount'] = np.where(df['Transaction_Type'] == 'Inflow', df['Amount'], -df['Amount'])
    df = df.sort_values('Date')
    cash_series = df['SignedAmount'].cumsum() + starting_cash

    inflows = df.loc[df['Transaction_Type'] == 'Inflow', 'Amount'].sum()
    outflows = df.loc[df['Transaction_Type'] == 'Outflow', 'Amount'].sum()

    # Monthly burn (average monthly outflow)
    if not df[df['Transaction_Type'] == 'Outflow'].empty:
        monthly_out = (df[df['Transaction_Type']=='Outflow']
                       .groupby(pd.Grouper(key='Date', freq='MS'))['Amount'].sum()
                      )
        burn_rate = monthly_out.mean()
    else:
        burn_rate = 0.0

    current_cash = cash_series.iloc[-1] if not cash_series.empty else starting_cash
    runway_months = (current_cash / burn_rate) if burn_rate > 0 else float("inf")

    outstanding_receivables = df[(df['Transaction_Type']=='Inflow') & (df['Payment_Status']=='Pending')]['Amount'].sum()

    return {
        "inflows": float(inflows),
        "outflows": float(outflows),
        "net_cashflow": float(inflows - outflows),
        "burn_rate": float(burn_rate),
        "runway_months": float(runway_months),
        "outstanding_receivables": float(outstanding_receivables),
        "cash_series": cash_series,
    }

def monthly_agg(df: pd.DataFrame):
    if df.empty:
        return pd.DataFrame(columns=['Month','Inflows','Outflows','Net'])
    g = df.groupby([pd.Grouper(key='Date', freq='MS'), 'Transaction_Type'])['Amount'].sum().unstack(fill_value=0)
    g['Net'] = g.get('Inflow', 0) - g.get('Outflow', 0)
    g = g.rename_axis('Month').reset_index()
    g['Month'] = g['Month'].dt.date
    g['Inflows'] = g.get('Inflow', 0)
    g['Outflows'] = g.get('Outflow', 0)
    return g[['Month','Inflows','Outflows','Net']]