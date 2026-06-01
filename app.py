import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Portfolio Tracker",
    layout="wide"
)

st.title("📈 Portfolio Tracker")

# ==========================================
# LOAD FILES
# ==========================================

portfolio = pd.read_csv("portfolio.csv")
stocks_df = pd.read_csv("stocks.csv")

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("Portfolio Manager")

with st.sidebar.form("add_stock_form"):

    company = st.selectbox(
        "🔍 Search & Select Stock",
        stocks_df["Company"]
    )

    shares = st.number_input(
        "Units / Shares",
        min_value=1,
        value=1,
        step=1
    )

    purchase_price = st.number_input(
        "Purchase Price",
        min_value=0.0,
        value=0.0,
        step=1.0
    )

    submit = st.form_submit_button(
        "➕ Add Stock"
    )

if submit:

    ticker = stocks_df.loc[
        stocks_df["Company"] == company,
        "Ticker"
    ].iloc[0]

    new_stock = pd.DataFrame({
        "Ticker": [ticker],
        "Shares": [shares],
        "PurchasePrice": [purchase_price]
    })

    portfolio = pd.concat(
        [portfolio, new_stock],
        ignore_index=True
    )

    portfolio.to_csv(
        "portfolio.csv",
        index=False
    )

    st.sidebar.success(
        f"{company} Added Successfully!"
    )

    st.rerun()

# ==========================================
# FUNCTIONS
# ==========================================

def get_price(ticker):

    try:

        stock = yf.Ticker(ticker)

        data = stock.history(
            period="1d"
        )

        if data.empty:
            return 0

        return float(
            data["Close"].iloc[-1]
        )

    except:
        return 0


@st.cache_data
def get_historical_prices(tickers):

    try:

        data = yf.download(
            tickers,
            period="1y",
            auto_adjust=True,
            progress=False
        )

        if len(tickers) == 1:
            return data["Close"].to_frame()

        return data["Close"]

    except:
        return pd.DataFrame()

# ==========================================
# CHECK PORTFOLIO
# ==========================================

if portfolio.empty:

    st.warning(
        "No stocks in portfolio."
    )

    st.stop()

# ==========================================
# LIVE PRICES
# ==========================================

portfolio["Current Price"] = (
    portfolio["Ticker"]
    .apply(get_price)
)

# ==========================================
# CALCULATIONS
# ==========================================

portfolio["Current Value"] = (
    portfolio["Shares"]
    * portfolio["Current Price"]
)

portfolio["Invested Value"] = (
    portfolio["Shares"]
    * portfolio["PurchasePrice"]
)

portfolio["Profit/Loss"] = (
    portfolio["Current Value"]
    - portfolio["Invested Value"]
)

# ==========================================
# SUMMARY METRICS
# ==========================================

total_value = portfolio["Current Value"].sum()

total_investment = portfolio["Invested Value"].sum()

total_profit = portfolio["Profit/Loss"].sum()

col1, col2, col3 = st.columns(3)

col1.metric(
    "Portfolio Value",
    f"₹{total_value:,.2f}"
)

col2.metric(
    "Invested Amount",
    f"₹{total_investment:,.2f}"
)

col3.metric(
    "Profit / Loss",
    f"₹{total_profit:,.2f}"
)

# ==========================================
# HOLDINGS TABLE
# ==========================================

st.subheader("📋 Holdings")

st.dataframe(
    portfolio,
    use_container_width=True
)

# ==========================================
# DELETE STOCK
# ==========================================

st.subheader("🗑 Delete Stock")

delete_stock = st.selectbox(
    "Select stock to delete",
    portfolio["Ticker"].unique()
)

if st.button("Delete Stock"):

    portfolio = portfolio[
        portfolio["Ticker"] != delete_stock
    ]

    portfolio.to_csv(
        "portfolio.csv",
        index=False
    )

    st.success(
        f"{delete_stock} deleted successfully!"
    )

    st.rerun()

# ==========================================
# PORTFOLIO ALLOCATION
# ==========================================

st.subheader("🥧 Portfolio Allocation")

fig = px.pie(
    portfolio,
    values="Current Value",
    names="Ticker"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# RISK ANALYSIS
# ==========================================

st.subheader("⚠️ Risk Analysis")

try:

    tickers = portfolio["Ticker"].tolist()

    prices = get_historical_prices(
        tickers
    )

    returns = (
        prices
        .pct_change()
        .dropna()
    )

    weights = (
        portfolio["Current Value"]
        /
        portfolio["Current Value"].sum()
    )

    annual_returns = (
        returns.mean()
        * 252
    )

    portfolio_return = np.sum(
        weights.values
        * annual_returns
    )

    covariance_matrix = (
        returns.cov()
        * 252
    )

    portfolio_volatility = np.sqrt(
        np.dot(
            weights.values.T,
            np.dot(
                covariance_matrix,
                weights.values
            )
        )
    )

    risk_free_rate = 0.05

    sharpe_ratio = (
        portfolio_return
        - risk_free_rate
    ) / portfolio_volatility

    r1, r2, r3 = st.columns(3)

    r1.metric(
        "Annual Return",
        f"{portfolio_return:.2%}"
    )

    r2.metric(
        "Volatility",
        f"{portfolio_volatility:.2%}"
    )

    r3.metric(
        "Sharpe Ratio",
        f"{sharpe_ratio:.2f}"
    )

except Exception as e:

    st.error(
        f"Risk Analysis Error: {e}"
    )

# ==========================================
# PORTFOLIO GROWTH
# ==========================================

try:

    st.subheader(
        "📈 Portfolio Growth"
    )

    portfolio_daily_returns = (
        returns
        * weights.values
    ).sum(axis=1)

    cumulative_returns = (
        1 + portfolio_daily_returns
    ).cumprod()

    st.line_chart(
        cumulative_returns
    )

except:
    pass

# ==========================================
# BENCHMARK COMPARISON
# ==========================================

try:

    st.subheader(
        "📊 Portfolio vs Nifty 50"
    )

    nifty = yf.download(
        "^NSEI",
        period="1y",
        auto_adjust=True,
        progress=False
    )

    nifty_close = (
        nifty["Close"]
        .squeeze()
    )

    nifty_returns = (
        nifty_close
        .pct_change()
        .dropna()
    )

    nifty_growth = (
        1 + nifty_returns
    ).cumprod()

    comparison = pd.concat(
        [
            cumulative_returns.rename("Portfolio"),
            nifty_growth.rename("Nifty50")
        ],
        axis=1
    )

    st.line_chart(
        comparison
    )

except:
    pass