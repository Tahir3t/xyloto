import pandas as pd
import numpy as np
import streamlit as st
st.set_page_config(layout="wide", page_title="XYLOTO", page_icon="chart_with_upwards_trend",)
import yfinance as yf
import requests
from datetime import date
import altair as alt

st.markdown(
    """
<style>
[data-testid="stMetricValue"] {
    font-size: 20px;
}
#MainMenu {visibility: hidden;}
footer {visibility: visible;}
footer:after{content:'Made by Tahir Elfaki <Telfaki@student.hult.edu>'; display:block; position:relative}
</style>
""",
    unsafe_allow_html=True,
)
st.title("XYLOTO Financial Analysis")
col_1, col_2 = st.columns(2)
nyse_url = "https://www.nyse.com/listings_directory/stock"
with col_1:
    ticker = st.text_input('Please enter Ticker/Symbol of a company', "AAPL").upper()
    st.write("You can find tickers/symbols listed in NYSE by clicking [here](https://www.nyse.com/listings_directory/stock)")
with col_2:
    st.markdown("")
    st.markdown("")
    button_clicked = st.button('Get Financial Analysis')

def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '$%.2f%s' % (num, ['', 'Thousand', ' Million', ' Billion', ' Trillion'][magnitude])
st.markdown("---")
if button_clicked:
    try:
        get_info = yf.Ticker(ticker)
    except:
        st.metric('This company is not listed in NYSE, please try another one')
    col_l, col_m, col_r = st.columns(3)
    with col_l:
        try:
            st.metric('Organization', get_info.info['longName'])
        except:
            st.metric('Organization', 'no information')
        try:
            st.metric('Sector', get_info.info['sector'])
        except:
            st.metric('Sector', 'no information')
        try:
            st.metric('Industry', get_info.info['industry'])
        except:
            st.metric('Industry', 'no information')
    with col_m:
        try:
            st.metric('Website', get_info.info['website'])
        except:
            st.metric('Website', 'no information')
        try:
            market_cap = get_info.info['marketCap']
            market_cap_fr = human_format(market_cap)
            st.metric('Market Cap', market_cap_fr)
        except:
            st.metric('Market Cap', 'no information')
    with col_r:
        try:
            st.image(get_info.info['logo_url'], width=200)
        except:
            st.metric("")
    try:
        with st.expander(f"About {get_info.info['longName']}"):
            st.write(get_info.info['longBusinessSummary'])
    except:
        st.write("no information")
    
    st.markdown("---")
    df_stock = yf.download(ticker, period="10y")
    st.area_chart(df_stock['Close'])
    
    st.metric("As of ", str(date.today().strftime("%d-%m-%Y")))
    col1, col2, col3 = st.columns(3)
    with col1:
        try:
            st.metric("Previous Close", get_info.info['previousClose'])
        except:
            st.metric("Previous Close", "N/A")
        try:
            st.metric("Volume", get_info.info['volume'])
        except:
            st.metric("Volume", "N/A")
    with col2:
        try:
            st.metric("Open", get_info.info['open'])
        except:
            st.metric("Open", "N/A")
        try:
            st.metric("PE Ratio (TTM)", "%.2f" % get_info.info['trailingPE'])
        except:
            st.metric("PE Ratio (TTM)", "N/A")
    with col3:
        try:
            st.metric("Target", get_info.info['targetMeanPrice'])
        except:
            st.metric("Targe", "N/A")
        try:
            st.metric("EPS (TTM)", "%.2f" % get_info.info['trailingEps'])
        except:
            st.metric("EPS (TTM)", "N/A")
    income_stmt = get_info.get_income_stmt(proxy='PROXY_SERVER')
    balance_sheet = get_info.get_balance_sheet(proxy='PROXY_SERVER')
    
    st.markdown("---")
    
    with st.expander(f"{ticker} Liquidity"):
        current_ratio = pd.DataFrame((balance_sheet.loc['CurrentAssets'] / balance_sheet.loc['CurrentLiabilities'])*100)
        try:
            quick_ratio = pd.DataFrame(((balance_sheet.loc['CurrentAssets'] - balance_sheet.loc['Inventory']) / balance_sheet.loc['CurrentLiabilities'])*100)
        except KeyError:
            quick_ratio = pd.DataFrame(((balance_sheet.loc['CurrentAssets']) / balance_sheet.loc['CurrentLiabilities'])*100)
            st.write("Note: No Inventory is found for this company.")
            st.write("Current Ratio = Quick Ratio")
        except ZeroDivisionError:
            quick_ratio = pd.DataFrame(0)
            st.write("No further information")
        
        liquidity = pd.concat([current_ratio, quick_ratio], axis=1)
        liquidity = liquidity.reset_index()
        liquidity.columns = ['Date', 'Current Ratio', 'Quick Ratio']
        liquidity['Date'] = liquidity['Date'].dt.strftime("%Y-%m-%d")
        liquidity_melt = liquidity.melt('Date')
        col1, col2 = st.columns(2)
        with col1:
            st.write(liquidity)
        with col2:
            fig = alt.Chart(liquidity_melt, title='Liquidity Ratios').mark_line().encode(
                x='Date', y=alt.Y('value', title="Current Ratio/Quick Ratio (%)"), color=alt.Color('variable', title=""))
            st.altair_chart(fig, use_container_width=True)
            # st.line_chart(liquidity)
    
    with st.expander(f"{ticker} Efficiency"):
        try:
            inv_to = pd.DataFrame(income_stmt.loc['TotalRevenue'] / balance_sheet.loc['Inventory'])
            inv_to.columns = ['Inventory Turnover']
        except (ZeroDivisionError, KeyError):
            if all(item !=0 for item in income_stmt.loc['TotalRevenue']):
                inv_to = pd.DataFrame(0 / income_stmt.loc['TotalRevenue'])
                inv_to.columns = ['Inventory Turnover']
                st.write("Note: No Inventory is found for this company.")
                st.write("Inventory Turnover = 0")
            else:
                inv_to = pd.DataFrame(0, index=np.arange(len(income_stmt)), columns=['Inventory Turnover'])
 
        dso = pd.DataFrame((balance_sheet.loc['AccountsReceivable'] / income_stmt.loc['TotalRevenue'])*365)
        dso.columns = ['DSO']
        fa_to = pd.DataFrame(income_stmt.loc['TotalRevenue'] / balance_sheet.loc['NetPPE'])
        fa_to.columns = ['Fixed Assets Turnover']
        
        eff_list = [dso, inv_to, fa_to]
        efficiency = pd.concat(eff_list, axis=1)
        efficiency = efficiency.reset_index()
        efficiency.columns = ['Date', 'DSO', 'Inventory Turnover', 'Fixed Assets Turnover']
        efficiency['Date'] = efficiency['Date'].dt.strftime("%Y-%m-%d")
        efficiency_melt = efficiency.melt('Date')
        col1, col2 = st.columns(2)
        with col1:
            st.write(efficiency)
        with col2:
            fig = alt.Chart(efficiency_melt, title='Efficiency Ratios').mark_line().encode(
                    x='Date', y=alt.Y('value', title="Turnover (Inv. & FA) / DSO"), color=alt.Color('variable', title=""))
            st.altair_chart(fig, use_container_width=True)
    
    with st.expander(f"{ticker} Profitability"):
        try:
            gp_ratio = pd.DataFrame((income_stmt.loc['GrossProfit'] / income_stmt.loc['TotalRevenue'])*100)
        except KeyError:
            gp_ratio = pd.DataFrame((0 / income_stmt.loc['TotalRevenue'])*100)
        gp_ratio.columns = ['Gross Profit Ratio']
        op_ratio = pd.DataFrame((income_stmt.loc['OperatingIncome'] / income_stmt.loc['TotalRevenue'])*100)
        op_ratio.columns = ['Operating Profit Ratio']
        sales2assets = pd.DataFrame((income_stmt.loc['TotalRevenue'] / balance_sheet.loc['TotalAssets'])*100)
        sales2assets.columns = ['Sales-to-Assets']
        roa = pd.DataFrame((income_stmt.loc['NetIncomeContinuousOperations'] / balance_sheet.loc['TotalAssets'])*100)
        roa.columns = ['ROA']
        roe = pd.DataFrame((income_stmt.loc['NetIncomeContinuousOperations'] / balance_sheet.loc['CommonStockEquity'])*100)
        roe.columns = ['ROE']
        profit_list1 = [gp_ratio, op_ratio, sales2assets]
        profit_list2 = [roa, roe]
        profit_list = [gp_ratio, op_ratio, sales2assets, roa, roe]
        profitability_1 = pd.concat(profit_list1, axis=1)
        profitability_2 = pd.concat(profit_list2, axis=1)
        profitability = pd.concat(profit_list, axis=1)
        profitability_1 = profitability_1.reset_index()
        profitability_2 = profitability_2.reset_index()
        profitability_1.columns = ['Date','Gross Profit Ratio', 'Operating Profit Ratio', 'Sales-to-Assets']
        profitability_2.columns = ['Date','ROA', 'ROE']
        profitability_1_melt = profitability_1.melt('Date')
        profitability_2_melt = profitability_2.melt('Date')
        
        profitability = profitability.reset_index()
        profitability.columns = ['Date', 'Gross Profit Ratio', 'Operating Profit Ratio', 'Sales-to-Assets', 'ROA', 'ROE']
        profitability['Date'] = profitability['Date'].dt.strftime("%Y-%m-%d")


        st.write(profitability)

        col1, col2 = st.columns(2)
        with col1:
            fig = alt.Chart(profitability_1_melt, title='Profitability Ratios').mark_line().encode(
                        x='Date', y=alt.Y('value', title="Gross Profit/Op. Profit/Sales2Assets"), color=alt.Color('variable', title=""))
            st.altair_chart(fig, use_container_width=True)
        with col2:
            fig = alt.Chart(profitability_2_melt, title='Profitability Ratios').mark_line().encode(
                        x='Date', y=alt.Y('value', title="ROA/ROE"), color=alt.Color('variable', title=""))
            st.altair_chart(fig, use_container_width=True)
    
    with st.expander(f"{ticker} Leverage"):
        debt_ratio = pd.DataFrame((balance_sheet.loc['TotalLiabilitiesNetMinorityInterest'] / balance_sheet.loc['TotalAssets'])*100)
        debt_ratio.columns = ['Debt Ratio']
        equity_ratio = pd.DataFrame((balance_sheet.loc['CommonStockEquity'] / balance_sheet.loc['TotalAssets'])*100)
        equity_ratio.columns = ['Equity Ratio']
        debt2equity = pd.DataFrame((balance_sheet.loc['TotalLiabilitiesNetMinorityInterest'] / balance_sheet.loc['CommonStockEquity']))
        debt2equity.columns = ['Debt-to-Equity']
        try:
            tie = pd.DataFrame(income_stmt.loc['EBIT'] / income_stmt.loc['InterestExpense'])
        except KeyError:
            tie = pd.DataFrame(income_stmt.loc['EBIT']*0)
        tie.columns = ['TIE']
        try:
            ccr = pd.DataFrame((income_stmt.loc['EBIT'] + income_stmt.loc['ReconciledDepreciation'])/ income_stmt.loc['InterestExpense'])
        except KeyError:
            ccr = pd.DataFrame((income_stmt.loc['EBIT'])*0)
        ccr.columns = ['Cash Coverage']

        lev_list1 = [debt_ratio, equity_ratio]
        lev_list2 = [debt2equity, tie, ccr]
        lev_list = [debt_ratio, equity_ratio, debt2equity, tie, ccr]

        leverage_1 = pd.concat(lev_list1, axis=1)
        leverage_2 = pd.concat(lev_list2, axis=1)
        leverage = pd.concat(lev_list, axis=1)

        leverage_1 = leverage_1.reset_index()
        leverage_1.columns = ['Date', 'Debt Ratio', 'Equity Ratio']
        leverage_2 = leverage_2.reset_index()
        leverage_2.columns = ['Date', 'Debt-to-Equity', 'TIE', 'Cash Coverage']
        leverage_1_melt = leverage_1.melt('Date')
        leverage_2_melt = leverage_2.melt('Date')
        leverage = leverage.reset_index()
        leverage.columns = ['Date', 'Debt Ratio', 'Equity Ratio', 'Debt-to-Equity', 'TIE', 'Cash Coverage']
        leverage['Date'] = leverage['Date'].dt.strftime("%Y-%m-%d")

        st.write(leverage)

        col1, col2 = st.columns(2)
        with col1:
            fig = alt.Chart(leverage_1_melt, title='Leverage Ratios').mark_line().encode(
                            x='Date', y=alt.Y('value', title="Debt Ratio/Equity Ratio"), color=alt.Color('variable', title=""))
            st.altair_chart(fig, use_container_width=True)
        with col2:
            fig = alt.Chart(leverage_2_melt, title='Leverage Ratios').mark_line().encode(
                            x='Date', y=alt.Y('value', title="Debt-to-Equity/TIE/Cash Coverage"), color=alt.Color('variable', title=""))
            st.altair_chart(fig, use_container_width=True)
    
    with st.expander(f"{ticker} Market Value"):
        final_stock_date = leverage['Date'].to_list()
        final_stock_price = []
        for i in range(0,len(final_stock_date)):
            price = yf.download(ticker, final_stock_date[i], interval="1d")['Close'][0]
            final_stock_price.append({'Date': final_stock_date[i], 'price':price})
            stprice_df = pd.DataFrame(final_stock_price)
        
        eps = pd.DataFrame(income_stmt.loc['NetIncomeContinuousOperations'] / balance_sheet.loc['OrdinarySharesNumber'])
        eps = eps.reset_index()
        eps.columns = ['Date','EPS']
        eps['Date'] = eps['Date'].dt.strftime("%Y-%m-%d")

        p2e = pd.DataFrame()
        p2e['Date'] = eps['Date']
        p2e['P/E'] = stprice_df['price'] / eps['EPS']

        bv2share = pd.DataFrame(balance_sheet.loc['CommonStockEquity'] / balance_sheet.loc['OrdinarySharesNumber'])
        bv2share = bv2share.reset_index()
        bv2share.columns = ['Date', 'Share Book Value']
        bv2share['Date'] = bv2share['Date'].dt.strftime("%Y-%m-%d")

        market_book = pd.DataFrame()
        market_book['Date'] = bv2share['Date']
        market_book['Market-to-Book'] = stprice_df['price'] / bv2share['Share Book Value']

        market_value1 = pd.merge(eps, bv2share, on='Date', how='outer')
        market_value2 = pd.merge(p2e, market_book, on='Date', how='outer')
        mv_df = pd.merge(market_value1, market_value2, on='Date', how='outer')

        
        st.write(mv_df)

        col1, col2 = st.columns(2)
        with col1:
            fig = alt.Chart(market_value1.melt('Date'), title='Market Value').mark_line().encode(
                            x='Date', y=alt.Y('value', title="EPS/Share Book Value"), color=alt.Color('variable', title=""))
            st.altair_chart(fig, use_container_width=True)
        with col2:
            fig = alt.Chart(market_value2.melt('Date'), title='Market Value').mark_line().encode(
                            x='Date', y=alt.Y('value', title="P/E + Market-to-Book Value"), color=alt.Color('variable', title=""))
            st.altair_chart(fig, use_container_width=True)

    
