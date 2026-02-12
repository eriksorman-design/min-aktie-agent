import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np

# 1. Inställningar
st.set_page_config(page_title="AktieAgenten v6", layout="wide")

# 2. Sidomeny
st.sidebar.header("Agentens Kontrollpanel")
ticker_input = st.sidebar.text_input("Ticker:", "EVO.ST")

@st.cache_resource
def get_data(symbol):
    return yf.Ticker(symbol)

stock = get_data(ticker_input)

try:
    # Hämta data
    hist = stock.history(period="1y")
    info = stock.info or {}
    news_list = stock.news
    eps = info.get('trailingEps')
    
    st.title(f"🚀 Analys: {info.get('longName', ticker_input)}")

    # 3. Nyckeltal
    col1, col2, col3 = st.columns(3)
    curr_price = info.get('currentPrice') or info.get('regularMarketPrice') or (not hist.empty and hist['Close'].iloc[-1]) or 0
    pe_val = info.get('trailingPE')
    
    col1.metric("Kurs", f"{curr_price:.2f} {info.get('currency', 'SEK')}")
    col2.metric("P/E (Nu)", f"{pe_val:.2f}" if pe_val else "N/A")
    col3.metric("Vinst/Aktie (EPS)", f"{eps:.2f} {info.get('currency', 'SEK')}" if eps else "N/A")

    # 4. Historisk P/E-Trend med Genomsnitt
    if eps and eps > 0 and not hist.empty:
        st.subheader("Historisk Värdering (P/E-trend)")
        hist['Historical_PE'] = hist['Close'] / eps
        avg_pe = hist['Historical_PE'].mean()
        
        fig_pe = go.Figure()
        # P/E-linjen
        fig_pe.add_trace(go.Scatter(x=hist.index, y=hist['Historical_PE'], name="P/E Daglig", line=dict(color='#00FFCC', width=2)))
        # Genomsnittslinjen (Röd/Streckad)
        fig_pe.add_trace(go.Scatter(x=hist.index, y=[avg_pe]*len(hist), name="Snitt (1 år)", line=dict(color='red', width=2, dash='dash')))
        
        fig_pe.update_layout(template="plotly_dark", height=350, yaxis_title="P/E-multipel")
        st.plotly_chart(fig_pe, use_container_width=True)
        
        # Agentens kommentar
        if pe_val:
            diff = ((pe_val - avg_pe) / avg_pe) * 100
            status = "över" if pe_val > avg_pe else "under"
            st.write(f"💡 **Agentens observation:** Snitt-P/E är **{avg_pe:.2f}**. Nuvarande värdering är ca **{abs(diff):.1f}% {status}** snittet.")

    # 5. Nyheter (Felsäker version)
    st.subheader("📰 Senaste händelserna")
    if news_list:
        for item in news_list[:5]:
            title = item.get('title') or (item.get('content') and item['content'].get('title')) or item.get('summary') or "Nyhet"
            publisher = item.get('publisher') or (item.get('content') and item['content'].get('publisher')) or "Finans"
            link = item.get('link') or (item.get('content') and item['content'].get('canonicalUrl')) or "#"
            
            with st.expander(f"🔹 {publisher}: {str(title)[:70]}..."):
                st.write(f"**Rubrik:** {title}")
                st.write(f"[Läs hela artikeln här]({link})")
    else:
        st.info("Inga nyheter hittades just nu.")

    # 6. Kursgraf
    if not hist.empty:
        st.subheader("Kursgraf (1 år)")
        fig_stock = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
        fig_stock.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig_stock, use_container_width=True)

except Exception as e:
    st.error(f"Ett tekniskt fel uppstod: {e}")
