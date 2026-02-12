import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np

# 1. Inställningar
st.set_page_config(page_title="AktieAgenten v8", layout="wide")

# 2. Sidomeny
st.sidebar.header("Agentens Kontrollpanel")
ticker_input = st.sidebar.text_input("Ticker:", "EVO.ST")

# NYHET: Om Yahoo sviker, kan du mata in P/E manuellt här
manual_pe = st.sidebar.number_input("Manuellt P/E (om grafen saknas):", value=0.0, step=0.1)

@st.cache_resource
def get_data(symbol):
    return yf.Ticker(symbol)

stock = get_data(ticker_input)

try:
    hist = stock.history(period="1y")
    info = stock.info or {}
    news_list = stock.news
    
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or (not hist.empty and hist['Close'].iloc[-1]) or 0
    
    # LOGIK FÖR ATT RÄDDA P/E-GRAFEN
    pe_now = info.get('trailingPE')
    eps = info.get('trailingEps')
    
    # Om vi har matat in ett manuellt P/E, använd det för att räkna ut EPS
    if manual_pe > 0:
        eps = current_price / manual_pe
        pe_now = manual_pe
    elif not eps and pe_now:
        eps = current_price / pe_now

    st.title(f"🚀 Analys: {info.get('longName', ticker_input)}")

    # 3. Nyckeltal
    col1, col2, col3 = st.columns(3)
    col1.metric("Kurs", f"{current_price:.2f} {info.get('currency', 'SEK')}")
    col2.metric("P/E (Nu)", f"{pe_now:.2f}" if pe_now else "N/A")
    col3.metric("Vinst/Aktie (EPS)", f"{eps:.2f}" if eps else "N/A")

    # 4. P/E-Trend med Genomsnitt
    if eps and eps > 0 and not hist.empty:
        st.subheader("Historisk Värdering (P/E-trend)")
        hist['Historical_PE'] = hist['Close'] / eps
        avg_pe = hist['Historical_PE'].mean()
        
        fig_pe = go.Figure()
        fig_pe.add_trace(go.Scatter(x=hist.index, y=hist['Historical_PE'], name="P/E Daglig", line=dict(color='#00FFCC', width=2)))
        fig_pe.add_trace(go.Scatter(x=hist.index, y=[avg_pe]*len(hist), name="Snitt (1 år)", line=dict(color='red', width=2, dash='dash')))
        
        fig_pe.update_layout(template="plotly_dark", height=350, yaxis_title="P/E-multipel")
        st.plotly_chart(fig_pe, use_container_width=True)
        st.write(f"💡 **Agentens observation:** Snittet är **{avg_pe:.2f}**. Just nu handlas den till **{pe_now:.2f}**.")
    else:
        st.warning("⚠️ Vinstdata saknas. Skriv in ett P/E-tal i menyn till vänster för att låsa upp grafen!")

    # 5. Nyheter (Felsäker)
    st.subheader("📰 Senaste händelserna")
    if news_list:
        for item in news_list[:5]:
            title = item.get('title') or (item.get('content') and item['content'].get('title')) or "Nyhet"
            publisher = item.get('publisher') or "Finansnyhet"
            link = item.get('link') or "#"
            with st.expander(f"🔹 {publisher}: {str(title)[:70]}..."):
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
