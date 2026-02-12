import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np

# 1. Inställningar
st.set_page_config(page_title="AktieAgenten v4", layout="wide")

# 2. Sidomeny
st.sidebar.header("Agentens Kontrollpanel")
ticker_input = st.sidebar.text_input("Ticker:", "EVO.ST")

@st.cache_resource
def get_data(symbol):
    return yf.Ticker(symbol)

stock = get_data(ticker_input)

try:
    info = stock.info
    hist = stock.history(period="1y")
    eps = info.get('trailingEps')
    
    st.title(f"🚀 Analys: {info.get('longName', ticker_input)}")

    # 3. Nyckeltal
    col1, col2, col3 = st.columns(3)
    curr_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
    pe_val = info.get('trailingPE', 0)
    
    col1.metric("Kurs", f"{curr_price} {info.get('currency', 'SEK')}")
    col2.metric("P/E (Nu)", f"{pe_val:.2f}" if pe_val else "N/A")
    col3.metric("Vinst/Aktie (EPS)", f"{eps} {info.get('currency', 'SEK')}")

    # 4. P/E-Trend med Genomsnitt
    if eps and eps > 0:
        st.subheader("Historisk Värdering (P/E-trend)")
        hist['Historical_PE'] = hist['Close'] / eps
        avg_pe = hist['Historical_PE'].mean() # Räknar ut snittet
        
        fig_pe = go.Figure()
        # Den faktiska P/E-linjen
        fig_pe.add_trace(go.Scatter(x=hist.index, y=hist['Historical_PE'], name="P/E Daglig", line=dict(color='#00FFCC', width=2)))
        # Genomsnittslinjen
        fig_pe.add_trace(go.Scatter(x=hist.index, y=[avg_pe]*len(hist), name="Genomsnitt", line=dict(color='red', width=2, dash='dash')))
        
        fig_pe.update_layout(template="plotly_dark", height=300, yaxis_title="P/E-multipel")
        st.plotly_chart(fig_pe, use_container_width=True)
        st.write(f"💡 **Agentens observation:** Genomsnittligt P/E under året är **{avg_pe:.2f}**. Just nu ligger vi {'under' if pe_val < avg_pe else 'över'} snittet.")

   # 5. Den slutgiltiga nyhetsfixen
    st.subheader("📰 Senaste händelserna")
    news_list = stock.news
    if news_list:
        for item in news_list[:5]:
            # Vi kollar ALLA ställen där rubriken kan gömma sig
            title = item.get('title') or \
                    (item.get('content') and item['content'].get('title')) or \
                    item.get('summary') or \
                    "Viktig marknadshändelse"
            
            publisher = item.get('publisher') or \
                        (item.get('content') and item['content'].get('publisher')) or \
                        "Finansnyheter"
            
            link = item.get('link') or (item.get('content') and item['content'].get('canonicalUrl')) or "#"
            
            # Vi rensar bort fula tecken om de finns
            clean_title = str(title).replace('\xa0', ' ')
            
            with st.expander(f"🔹 {publisher}: {clean_title[:75]}..."):
                st.write(f"**Rubrik:** {clean_title}")
                st.write(f"[Läs hela artikeln här]({link})")
    else:
        st.info("Inga nyheter hittades just nu.")
except Exception as e:

    st.error(f"Ett fel uppstod: {e}")
