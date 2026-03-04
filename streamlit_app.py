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
# Bu ozellik sadece ENABLE_AUTO_UPDATE=true ise calisir (Streamlit Cloud icin)
if "auto_updated" not in st.session_state:
    st.session_state.auto_updated = True
    import os
    if os.environ.get("ENABLE_AUTO_UPDATE", "").lower() == "true":
        try:
            project_dir = str(Path(__file__).parent)
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=project_dir,
                capture_output=True, text=True, timeout=15,
            )
            if "Already up to date" not in result.stdout:
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

# --- Data ---
post_history = load_post_history()
drafts = load_draft_tweets()
today_posts = len([p for p in post_history
                   if p.get("posted_at", "").startswith(datetime.datetime.now().strftime("%Y-%m-%d"))])

# --- Hero Section ---
api_dot = "🟢" if (has_twitter and has_ai) else "🟡"
api_label = "Aktif" if (has_twitter and has_ai) else "Kurulum Gerekli"

st.markdown(f"""
<div class="hero-section">
    <span class="hero-logo">🤖</span>
    <div class="hero-title">X AI Otomasyon</div>
    <div class="hero-subtitle">Tara &middot; Yaz &middot; Paylaş</div>
</div>
""", unsafe_allow_html=True)

# --- Quick Stats ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_stat_box(str(len(post_history)), "Paylaşılan")
with col2:
    render_stat_box(str(len(drafts)), "Taslak")
with col3:
    render_stat_box(str(today_posts), "Bugün")
with col4:
    render_stat_box(f"{api_dot}", api_label)

# --- Section: Quick Actions ---
st.markdown("""
<div class="section-header">
    <h3>Hızlı İşlemler</h3>
</div>
""", unsafe_allow_html=True)

# Row 1: Primary actions
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="action-card">
        <div class="action-icon">🔍</div>
        <div class="action-title">AI Gündem Tara</div>
        <div class="action-desc">X'te AI gelişmelerini keşfet</div>
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

# Row 2: Secondary actions
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
        <div class="action-desc">Nişindeki hesapları bul</div>
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

# --- Section: Recent Activity ---
st.markdown(f"""
<div class="section-header">
    <h3>Son Aktiviteler</h3>
    <span class="section-badge">{len(post_history)} toplam</span>
</div>
""", unsafe_allow_html=True)

if post_history:
    for entry in post_history[:5]:
        text_preview = entry.get("text", "")[:140]
        if len(entry.get("text", "")) > 140:
            text_preview += "..."
        url = entry.get("url", "")
        url_html = f'<a href="{url}" target="_blank" class="activity-link">Görüntüle →</a>' if url else ""

        posted_at = entry.get('posted_at', '')
        style = entry.get('style', '')
        meta_parts = []
        if posted_at:
            meta_parts.append(posted_at[:16])
        if style:
            meta_parts.append(style)

        st.markdown(f"""
        <div class="activity-item">
            <div class="activity-dot"></div>
            <div class="activity-content">
                <div class="activity-text">{text_preview}</div>
                <div class="activity-meta">
                    <span class="activity-time">{' · '.join(meta_parts)}</span>
                    {url_html}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📝</div>
        <p>Henüz paylaşım yapılmamış.<br>
        <strong>Tara</strong> sayfasından başlayarak ilk tweet'ini oluştur!</p>
    </div>
    """, unsafe_allow_html=True)

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
    st.markdown(f"""
    <div class="setup-warning">
        <span class="setup-warning-icon">⚠️</span>
        <span class="setup-warning-text">API anahtarlarınızı ⚙️ Ayarlar sayfasından yapılandırın.</span>
    </div>
    """, unsafe_allow_html=True)
