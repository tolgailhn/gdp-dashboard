"""
X AI Otomasyon Dashboard - Ana Sayfa
Twitter/X üzerinde AI gelişmelerini tarayıp doğal tweet üreten otomasyon sistemi
"""
import streamlit as st
import datetime
from modules.ui_components import inject_custom_css, check_password, render_stat_box, get_secret
from modules.style_manager import load_post_history, load_draft_tweets

# Page config
st.set_page_config(
    page_title="X AI Otomasyon",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS
inject_custom_css()

# Authentication
if not check_password():
    st.stop()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🤖 X AI Otomasyon")
    st.markdown("---")
    st.markdown("**Sayfalar:**")
    st.markdown("- 🔍 **Tara** - AI gündem tarayıcı")
    st.markdown("- ✍️ **Yaz** - Tweet yazıcı")
    st.markdown("- ⚙️ **Ayarlar** - Sistem ayarları")
    st.markdown("---")

    # API status indicators
    st.markdown("**API Durumu:**")

    has_twitter = bool(get_secret("twitter_bearer_token", ""))
    has_ai = bool(get_secret("minimax_api_key", "") or get_secret("anthropic_api_key", "") or get_secret("openai_api_key", ""))

    if has_twitter:
        st.success("Twitter API ✓", icon="🐦")
    else:
        st.warning("Twitter API yapılandırılmamış", icon="⚠️")

    if has_ai:
        st.success("AI API ✓", icon="🧠")
    else:
        st.warning("AI API yapılandırılmamış", icon="⚠️")

    st.markdown("---")
    st.caption(f"v1.0 | {datetime.datetime.now().strftime('%d.%m.%Y')}")

# --- Main Dashboard ---
st.markdown("""
<div class="main-header">
    <h1>🤖 X AI Otomasyon Paneli</h1>
    <p style="color:#8899a6; font-size:16px;">
        AI gelişmelerini tara, doğal tweet'ler üret, direkt paylaş
    </p>
</div>
""", unsafe_allow_html=True)

# Quick stats
col1, col2, col3, col4 = st.columns(4)

post_history = load_post_history()
drafts = load_draft_tweets()

with col1:
    render_stat_box(str(len(post_history)), "Paylaşılan Tweet")

with col2:
    render_stat_box(str(len(drafts)), "Taslak")

with col3:
    today_posts = len([p for p in post_history
                       if p.get("posted_at", "").startswith(datetime.datetime.now().strftime("%Y-%m-%d"))])
    render_stat_box(str(today_posts), "Bugünkü Paylaşım")

with col4:
    api_status = "Aktif" if (has_twitter and has_ai) else "Eksik"
    render_stat_box(api_status, "API Durumu")

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# Quick actions
st.markdown("### Hızlı İşlemler")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="stat-box">
        <div style="font-size:36px; margin-bottom:8px;">🔍</div>
        <div style="color:#f0f0f0; font-weight:bold; font-size:16px;">AI Gündem Tara</div>
        <div style="color:#8899a6; font-size:13px; margin-top:4px;">
            X'te son saatlerin AI gelişmelerini bul
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Taramaya Başla", key="scan_btn", use_container_width=True, type="primary"):
        st.switch_page("pages/1_🔍_Tara.py")

with col2:
    st.markdown("""
    <div class="stat-box">
        <div style="font-size:36px; margin-bottom:8px;">✍️</div>
        <div style="color:#f0f0f0; font-weight:bold; font-size:16px;">Tweet Yaz</div>
        <div style="color:#8899a6; font-size:13px; margin-top:4px;">
            AI ile doğal tweet üret ve paylaş
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Yazmaya Başla", key="write_btn", use_container_width=True, type="primary"):
        st.switch_page("pages/2_✍️_Yaz.py")

with col3:
    st.markdown("""
    <div class="stat-box">
        <div style="font-size:36px; margin-bottom:8px;">⚙️</div>
        <div style="color:#f0f0f0; font-weight:bold; font-size:16px;">Ayarlar</div>
        <div style="color:#8899a6; font-size:13px; margin-top:4px;">
            API anahtarları ve yazım tarzı ayarları
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Ayarları Aç", key="settings_btn", use_container_width=True):
        st.switch_page("pages/3_⚙️_Ayarlar.py")

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# Recent activity
st.markdown("### Son Aktiviteler")

if post_history:
    for entry in post_history[:5]:
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                text_preview = entry.get("text", "")[:120]
                if len(entry.get("text", "")) > 120:
                    text_preview += "..."
                st.markdown(f"""
                <div class="tweet-card" style="padding:12px 16px; margin:4px 0;">
                    <div style="color:#f0f0f0; font-size:14px;">{text_preview}</div>
                    <div style="color:#8899a6; font-size:12px; margin-top:6px;">
                        {entry.get('posted_at', 'N/A')} | {entry.get('style', 'N/A')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if entry.get("url"):
                    st.link_button("Görüntüle", entry["url"], use_container_width=True)
else:
    st.info("Henüz paylaşım yapılmamış. **Tara** sayfasından başlayın!")

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# How to use guide
with st.expander("📖 Nasıl Kullanılır?"):
    st.markdown("""
    ### Kullanım Kılavuzu

    **1. API Anahtarlarını Ayarla** (⚙️ Ayarlar)
    - Twitter/X API anahtarlarını girin (tweet okuma ve yazma için)
    - AI API anahtarını girin (Anthropic Claude veya OpenAI)

    **2. AI Gündem Tara** (🔍 Tara)
    - Zaman aralığını seçin (6/12/24 saat)
    - "Tara" butonuna tıklayın
    - Bulunan AI gelişmelerini inceleyin
    - İlgilendiğiniz konuyu seçin

    **3. Tweet Yaz** (✍️ Yaz)
    - Bir konu seçin veya manuel girin
    - Yazım tarzını seçin (Samimi, Profesyonel, Hook, Analitik)
    - "Yaz" butonuna tıklayın
    - Oluşturulan tweet'i düzenleyin
    - Beğendiyseniz "Paylaş" ile X'te paylaşın

    **4. Yazım Tarzı Eğitimi** (⚙️ Ayarlar)
    - Kendi tweet örneklerinizi ekleyin
    - AI tarzınızı analiz etsin
    - Artık sizin gibi yazar!

    ### API Anahtarları Nereden Alınır?

    **Twitter/X API:**
    - [developer.x.com](https://developer.x.com) adresinden başvurun
    - Basic ($100/ay) veya Pro plan gerekli

    **AI API:**
    - Anthropic Claude: [console.anthropic.com](https://console.anthropic.com)
    - OpenAI: [platform.openai.com](https://platform.openai.com)
    """)

# Setup check
if not has_twitter or not has_ai:
    st.markdown("---")
    st.warning("""
    **Kurulum Gerekli:** API anahtarlarınızı yapılandırmanız gerekiyor.

    Streamlit Cloud kullanıyorsanız, `.streamlit/secrets.toml` dosyasına ekleyin.
    Lokal kullanıyorsanız, Ayarlar sayfasından girin.
    """)
