"""
X AI Otomasyon Dashboard - Ana Sayfa
Twitter/X üzerinde AI gelişmelerini tarayıp doğal tweet üreten otomasyon sistemi
"""
import streamlit as st
import datetime
import subprocess
from pathlib import Path
from modules.ui_components import inject_custom_css, check_password, render_stat_box, get_secret, render_sidebar_nav
from modules.style_manager import load_post_history, load_draft_tweets

# --- Auto-update: Her baslatmada GitHub'dan son halini cek ---
if "auto_updated" not in st.session_state:
    st.session_state.auto_updated = True
    try:
        project_dir = str(Path(__file__).parent)
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=project_dir,
            capture_output=True, text=True, timeout=15,
        )
        if "Already up to date" not in result.stdout:
            # Yeni bagimlilik varsa kur
            subprocess.run(
                ["pip", "install", "-r", "requirements.txt", "--quiet"],
                cwd=project_dir,
                capture_output=True, timeout=60,
            )
    except Exception:
        pass  # Offline veya git yoksa sessizce gec

# Page config
st.set_page_config(
    page_title="X AI Otomasyon",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto",
)

# Custom CSS
inject_custom_css()

# Authentication
if not check_password():
    st.stop()

# --- Sidebar Navigation ---
render_sidebar_nav(current_page="home")

has_twitter = bool(get_secret("twitter_bearer_token", ""))
has_ai = bool(get_secret("minimax_api_key", "") or get_secret("anthropic_api_key", "") or get_secret("openai_api_key", ""))

# --- Main Dashboard ---
st.markdown("""
<div class="main-header">
    <h1>🤖 X AI Otomasyon</h1>
    <p style="color:#8899a6; font-size:14px; margin-top:2px;">
        Tara &middot; Yaz &middot; Paylaş
    </p>
</div>
""", unsafe_allow_html=True)

# Quick stats - 2x2 on mobile, 4x1 on desktop
post_history = load_post_history()
drafts = load_draft_tweets()
today_posts = len([p for p in post_history
                   if p.get("posted_at", "").startswith(datetime.datetime.now().strftime("%Y-%m-%d"))])
api_status = "Aktif" if (has_twitter and has_ai) else "Eksik"

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_stat_box(str(len(post_history)), "Paylaşılan")
with col2:
    render_stat_box(str(len(drafts)), "Taslak")
with col3:
    render_stat_box(str(today_posts), "Bugün")
with col4:
    render_stat_box(api_status, "API")

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# Quick actions - grid layout
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="action-card">
        <div class="action-icon">🔍</div>
        <div class="action-title">AI Gündem Tara</div>
        <div class="action-desc">X'te AI gelişmelerini bul</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Tara", key="scan_btn", use_container_width=True, type="primary"):
        st.switch_page("pages/1_🔍_Tara.py")

with col2:
    st.markdown("""
    <div class="action-card">
        <div class="action-icon">✍️</div>
        <div class="action-title">Tweet Yaz</div>
        <div class="action-desc">AI ile doğal tweet üret</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Yaz", key="write_btn", use_container_width=True, type="primary"):
        st.switch_page("pages/2_✍️_Yaz.py")

with col3:
    st.markdown("""
    <div class="action-card">
        <div class="action-icon">💡</div>
        <div class="action-title">İçerik Üret</div>
        <div class="action-desc">Konu keşfet, uzun içerik yaz</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("İçerik", key="content_btn", use_container_width=True, type="primary"):
        st.switch_page("pages/6_💡_İçerik.py")

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div class="action-card">
        <div class="action-icon">📊</div>
        <div class="action-title">Tweet Analizi</div>
        <div class="action-desc">Analiz et, AI'ı eğit</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Analiz", key="analysis_btn", use_container_width=True):
        st.switch_page("pages/4_📊_Analiz.py")

with col5:
    st.markdown("""
    <div class="action-card">
        <div class="action-icon">👥</div>
        <div class="action-title">Takipçi Keşfet</div>
        <div class="action-desc">Onaylı takipçileri bul</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Takipçi", key="followers_btn", use_container_width=True):
        st.switch_page("pages/5_👥_Takipçiler.py")

with col6:
    st.markdown("""
    <div class="action-card">
        <div class="action-icon">⚙️</div>
        <div class="action-title">Ayarlar</div>
        <div class="action-desc">API ve yazım tarzı</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Ayarlar", key="settings_btn", use_container_width=True):
        st.switch_page("pages/3_⚙️_Ayarlar.py")

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# Recent activity
st.markdown("### Son Aktiviteler")

if post_history:
    for entry in post_history[:5]:
        text_preview = entry.get("text", "")[:120]
        if len(entry.get("text", "")) > 120:
            text_preview += "..."
        url = entry.get("url", "")
        url_html = f'<a href="{url}" target="_blank" style="color:#1DA1F2; font-size:12px; text-decoration:none;">Gör &rarr;</a>' if url else ""
        st.markdown(f"""
        <div class="tweet-card" style="padding:14px 16px; margin:4px 0;">
            <div style="color:#f0f0f0; font-size:14px; line-height:1.5;">{text_preview}</div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                <span style="color:#8899a6; font-size:12px;">
                    {entry.get('posted_at', 'N/A')} &middot; {entry.get('style', '')}
                </span>
                {url_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Henüz paylaşım yapılmamış. **Tara** sayfasından başlayın!")

# How to use guide
with st.expander("📖 Nasıl Kullanılır?"):
    st.markdown("""
    **1. API Anahtarlarını Ayarla** (⚙️ Ayarlar)
    - AI API anahtarını girin (MiniMax, Anthropic veya OpenAI)
    - X çerezlerini girin (tweet okuma/yazma için)

    **2. AI Gündem Tara** (🔍 Tara)
    - Zaman aralığını seçin, "Tara" butonuna tıklayın
    - AI gelişmelerini inceleyin, konuyu seçin

    **3. Tweet / İçerik Yaz** (✍️ Yaz / 💡 İçerik)
    - Konu girin veya keşfedilen konuyu seçin
    - Yazım tarzı ve uzunluk seçin, AI üretsin
    - Beğendiyseniz direkt paylaşın

    **4. Tweet Analizi** (📊 Analiz)
    - Hesap tweet'lerini çekip analiz edin
    - AI bu verilerle daha iyi tweet yazar

    **5. Takipçi Keşfi** (👥 Takipçiler)
    - Nişinizdeki hesapların takipçilerini keşfedin
    """)

# Setup check
if not has_twitter or not has_ai:
    st.markdown("---")
    st.warning("**Kurulum:** API anahtarlarınızı ⚙️ Ayarlar sayfasından yapılandırın.")
