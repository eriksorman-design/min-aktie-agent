import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np

# 1. Inställningar
st.set_page_config(page_title="AktieAgenten v7", layout="wide")

# 2. Sidomeny
st.sidebar.header("Agentens Kontrollpanel")
ticker_input = st.sidebar.text_input("Ticker:", "EVO.ST")

@st.cache_resource
def get_data(symbol):
    return yf.Ticker(symbol)

stock = get_data(ticker_input)

try:
    hist = stock.history(period="1y")
    info = stock.info or {}
    news_list = stock.news
    
    # FÖRBÄTTRAD VINSTHÄMTNING (EPS)
    # Vi letar på flera ställen efter vinsten för att kunna rita P/E-grafen
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or (not hist.empty and hist['Close'].iloc[-1]) or 0
    pe_now = info.get('trailingPE')
    eps = info.get('trailingEps')
    
    # Om EPS saknas men P/E finns, räknar vi ut EPS själva: EPS = Pris / P/E
    if not eps and pe_now and pe_now > 0:
        eps = current_price / pe_now

    st.title(f"🚀 Analys: {info.get('longName', ticker_input)}")

    # 3. Nyckeltal
    col1, col2, col3 = st.columns(3)
    col1.metric("Kurs", f"{current_price:.2f} {info.get('currency', 'SEK')}")
    col2.metric("P/E (Nu)", f"{pe_now:.2f}" if pe_now else "N/A")
    col3.metric("Vinst/Aktie (EPS)", f"{eps:.2f}" if eps else "N/A")

    # 4. Historisk P/E-Trend (Med backup-logik)
    if eps and eps > 0 and not hist.empty:
        st.subheader("Historisk Värdering (P/E-trend)")
        hist['Historical_PE'] = hist['Close'] / eps
        avg_pe = hist['Historical_PE'].mean()
        
        fig_pe = go.Figure()
        fig_pe.add_trace(go.Scatter(x=hist.index, y=hist['Historical_PE'], name="P/E Daglig", line=dict(color='#00FFCC', width=2)))
        fig_pe.add_trace(go.Scatter(x=hist.index, y=[avg_pe]*len(hist), name="Snitt (1 år)", line=dict(color='red', width=2, dash='dash')))
        
        fig_pe.update_layout(template="plotly_dark", height=350, yaxis_title="P/E-multipel")
        st.plotly_chart(fig_pe, use_container_width=True)
        st.write(f"💡 **Agentens observation:** Genomsnittligt P/E under året är **{avg_pe:.2f}**.")
    else:
        # Om vi fortfarande inte har EPS visar vi ett tydligt meddelande varför grafen saknas
        st.warning("⚠️ Historisk P/E-graf kan inte ritas eftersom vinstdata (EPS) saknas för denna ticker just nu.")

    # 5. Nyheter
    st.subheader("📰 Senaste händelserna")
    if news_list:
        for item in news_list[:5]:
            title = item.get('title') or (item.get('content') and item['content'].get('title')) or "Nyhet"
            publisher = item.get('publisher') or "Finans"
            link = item.get('link') or "#"
            with st.expander(f"🔹 {publisher}: {str(title)[:75]}..."):
                st.write(title)
                st.write(f"[Länk]({link})")

    # 6. Kursgraf
    if not hist.empty:
        st.subheader("Kursgraf (1 år)")
        fig_stock = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
        fig_stock.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig_stock, use_container_width=True)

except Exception as e:
    st.error(f"Ett tekniskt fel uppstod: {e}")
