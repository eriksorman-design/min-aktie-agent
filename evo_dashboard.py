import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# 1. Inställningar
st.set_page_config(page_title="AktieAgenten v5", layout="wide")

# 2. Sidomeny
st.sidebar.header("Agentens Kontrollpanel")
ticker_input = st.sidebar.text_input("Ticker:", "EVO.ST")

@st.cache_resource
def get_data(symbol):
    return yf.Ticker(symbol)

stock = get_data(ticker_input)

# Vi använder en try-block för att fånga upp alla fel
try:
    # Försök hämta data
    hist = stock.history(period="1y")
    info = stock.info or {} # Om info är None, använd en tom mapp istället
    news_list = stock.news
    
    # Hämta namn (felsäkert)
    long_name = info.get('longName') or ticker_input
    st.title(f"🚀 Analys: {long_name}")

    # 3. Nyckeltal (med felsäkra värden)
    col1, col2, col3 = st.columns(3)
    curr_price = info.get('currentPrice') or info.get('regularMarketPrice') or (not hist.empty and hist['Close'].iloc[-1]) or 0
    pe_val = info.get('trailingPE')
    eps = info.get('trailingEps')
    
    col1.metric("Kurs", f"{curr_price:.2f} {info.get('currency', 'SEK')}")
    col2.metric("P/E (Nu)", f"{pe_val:.2f}" if pe_val else "N/A")
    col3.metric("Vinst/Aktie (EPS)", f"{eps:.2f}" if eps else "N/A")

    # 4. P/E-Trend
    if eps and eps > 0 and not hist.empty:
        st.subheader("Historisk Värdering (P/E-trend)")
        hist['Historical_PE'] = hist['Close'] / eps
        avg_pe = hist['Historical_PE'].mean()
        
        fig_pe = go.Figure()
        fig_pe.add_trace(go.Scatter(x=hist.index, y=hist['Historical_PE'], name="P/E Daglig", line=dict(color='#00FFCC')))
        fig_pe.add_trace(go.Scatter(x=hist.index, y=[avg_pe]*len(hist), name="Snitt", line=dict(color='red', dash='dash')))
        fig_pe.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig_pe, use_container_width=True)

    # 5. Nyheter (Felsäker version)
    st.subheader("📰 Senaste händelserna")
    if news_list:
        for item in news_list[:5]:
            # Letar i alla tänkbara fält efter rubriken
            title = item.get('title') or (item.get('content') and item['content'].get('title')) or "Nyhet"
            publisher = item.get('publisher') or "Finansnyheter"
            link = item.get('link') or "#"
            
            with st.expander(f"🔹 {publisher}: {str(title)[:70]}..."):
                st.write(title)
                st.write(f"[Läs artikeln här]({link})")
    else:
        st.info("Inga nyheter hittades just nu.")

    # 6. Kursgraf
    if not hist.empty:
        st.subheader("Kursgraf (1 år)")
        fig_stock = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
        fig_stock.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig_stock, use_container_width=True)

except Exception as e:
    st.error(f"Ett tekniskt fel uppstod: {e}")
    st.info("Tips: Prova att ladda om sidan eller vänta en minut så att Yahoo Finance hinner svara.")
