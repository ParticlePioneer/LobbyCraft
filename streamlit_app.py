import streamlit as st 
import requests 
 
API = 'http://localhost:8000' 
 
st.set_page_config( 
    page_title='LobbyCraft', 
    page_icon='🎮', 
    layout='wide', 
    initial_sidebar_state='expanded', 
) 
 
# ── Sidebar ────────────────────────────────────────────────────── 
with st.sidebar: 
    st.markdown('## 🎮 LobbyCraft') 
    st.markdown('**DBMS Course Project**') 
    st.markdown('CT-261 | Spring 2026') 
    st.divider() 
    st.markdown('**Tech Stack**') 
    st.markdown('`Python` `FastAPI` `Oracle FreeSQL`') 
    st.divider() 
    # API health check 
    try: 
        r = requests.get(f'{API}/docs', timeout=2) 
        st.success('API Online ✓') 
    except Exception: 
        st.error('API Offline ✗') 
        st.caption('Start: uvicorn main:app --port 8000') 
 
# ── Hero ───────────────────────────────────────────────────────── 
st.markdown('# 🎮 LobbyCraft') 
st.markdown('### Battle Royale & Competitive Shooters') 
st.markdown('> Database-driven matchmaking module — CT-261 Complex Computing Problem') 
st.divider() 
 
# ── Stats row ──────────────────────────────────────────────────── 
col1, col2, col3, col4 = st.columns(4) 
 
with col1: 
    st.metric('Game Modes', '5', help='BR Solo, BR Duo, BR Squad, Ranked 5v5, Unranked 5v5') 
with col2: 
    st.metric('DB Tables', '15', help='Fully normalised to BCNF') 
with col3: 
    st.metric('Normalization', 'BCNF', help='All 13 relations verified') 
with col4: 
    st.metric('API Endpoints', '20', help='FastAPI REST endpoints') 
 
st.divider() 
 
# ── Architecture diagram ───────────────────────────────────────── 
st.markdown('### System Architecture') 
st.code(''' 
  [This UI]  →  FastAPI :8000  →  Oracle FreeSQL DB (Cloud) 
  Streamlit      Python          15 tables, BCNF normalised 
  :8501          Raw SQL         PL/SQL stored procedures 
''', language=None) 
 
st.divider() 
 
# ── Navigation cards ───────────────────────────────────────────── 
st.markdown('### Navigate')
c1, c2, c3, c4, c5 = st.columns(5) 
with c1: 
    st.info('**👤 Players**\nCreate players, view MMR history, set role preferences') 
with c2: 
    st.info('**🎯 Parties & Queue**\nForm parties, enter matchmaking queue') 
with c3: 
    st.info('**🏆 Match Results**\nSubmit stats, view match details') 
with c4: 
    st.info('**📊 Analytics**\nLeaderboard, lobby quality, MMR trends') 
with c5:
    st.info('**⚙️ Engine Lab**\nSwitch engines per mode, compare lobby quality') 