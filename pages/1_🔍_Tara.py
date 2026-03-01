"""
AI Gündem Tarayıcı Sayfası
X/Twitter'da AI gelişmelerini tarar ve listeler
"""
import streamlit as st
import datetime
from modules.ui_components import inject_custom_css, check_password, render_tweet_card, get_secret, render_sidebar_nav
from modules.twitter_scanner import TwitterScanner, DEFAULT_AI_ACCOUNTS
from modules.style_manager import load_monitored_accounts

# Page config
st.set_page_config(
    page_title="AI Tara | X AI Otomasyon",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="auto",
)

inject_custom_css()

if not check_password():
    st.stop()

render_sidebar_nav(current_page="tara")

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>🔍 AI Gündem Tarayıcı</h1>
    <p style="color:#8899a6;">X/Twitter'da son saatlerin AI gelişmelerini tara</p>
</div>
""", unsafe_allow_html=True)

# --- Controls ---
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    time_range = st.selectbox(
        "Zaman Aralığı",
        options=[6, 12, 24],
        format_func=lambda x: f"Son {x} saat",
        index=2,
        key="scan_time_range"
    )

with col2:
    category_filter = st.selectbox(
        "Kategori Filtresi",
        options=["Tümü", "Yeni Model", "Model Güncelleme", "Araştırma",
                 "Benchmark", "Açık Kaynak", "API/Platform", "AI Ajanlar",
                 "Görüntü/Video", "Endüstri"],
        key="scan_category"
    )

with col3:
    max_results = st.number_input(
        "Maks. Sonuç",
        min_value=5, max_value=50, value=20,
        key="scan_max_results"
    )

# Custom search query
with st.expander("Gelişmiş Arama"):
    custom_query = st.text_input(
        "Özel arama sorgusu (opsiyonel)",
        placeholder="Örn: 'Qwen release' veya 'GPT-5 leak'",
        key="custom_query"
    )
    col1, col2 = st.columns(2)
    with col1:
        min_likes = st.number_input("Min. beğeni", min_value=0, value=10, key="min_likes")
    with col2:
        min_retweets = st.number_input("Min. retweet", min_value=0, value=5, key="min_retweets")

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# --- Scan Button ---
scan_clicked = st.button("🔍 Tara", type="primary", use_container_width=True, key="scan_button")

# --- Results ---
if scan_clicked:
    # Check API keys
    bearer_token = get_secret("twitter_bearer_token", "")
    api_key = get_secret("twitter_api_key", "")
    api_secret = get_secret("twitter_api_secret", "")
    access_token = get_secret("twitter_access_token", "")
    access_secret = get_secret("twitter_access_secret", "")

    # Twikit credentials (free alternative)
    twikit_username = get_secret("twikit_username", "")
    twikit_password = get_secret("twikit_password", "")
    twikit_email = get_secret("twikit_email", "")

    if not bearer_token and not twikit_username:
        st.error("Twitter API veya Twikit bilgileri yapılandırılmamış! Ayarlar sayfasından ekleyin.")
        st.stop()

    with st.spinner("X'te AI gelişmeleri taranıyor..."):
        try:
            scanner = TwitterScanner(
                bearer_token=bearer_token,
                api_key=api_key,
                api_secret=api_secret,
                access_token=access_token,
                access_secret=access_secret,
                twikit_username=twikit_username,
                twikit_password=twikit_password,
                twikit_email=twikit_email,
            )

            if scanner.use_twikit:
                st.success("Twikit ile taranıyor (ücretsiz)")
            elif scanner.client:
                st.info("Twitter API ile taranıyor")
            else:
                twikit_err = getattr(scanner, 'twikit_error', '')
                if twikit_err:
                    st.error(f"Twikit bağlantı hatası: {twikit_err}")
                else:
                    st.error("Ne Twikit ne de Twitter API bağlanamadı. Ayarlar sayfasından kontrol edin.")
                st.stop()

            # Get custom accounts
            custom_accounts = load_monitored_accounts()

            # Build custom queries
            custom_queries = []
            if custom_query:
                custom_queries.append(f"{custom_query} -is:retweet")

            # Scan
            topics = scanner.scan_ai_topics(
                time_range_hours=time_range,
                max_results_per_query=max_results,
                custom_accounts=custom_accounts,
                custom_queries=custom_queries,
            )

            # Show search errors if any
            errors = getattr(scanner, 'search_errors', [])
            if errors:
                unique_errors = list(dict.fromkeys(errors))[:5]
                with st.expander(f"⚠️ {len(errors)} arama hatası oluştu", expanded=not topics):
                    for err in unique_errors:
                        st.warning(err)
                    if len(errors) > 5:
                        st.caption(f"...ve {len(errors) - 5} hata daha")

            # Apply filters
            if category_filter != "Tümü":
                topics = [t for t in topics if t.category == category_filter]

            if min_likes > 0:
                topics = [t for t in topics if t.like_count >= min_likes]

            if min_retweets > 0:
                topics = [t for t in topics if t.retweet_count >= min_retweets]

            # Store in session state
            st.session_state.scan_results = topics

        except Exception as e:
            st.error(f"Tarama hatası: {e}")
            st.session_state.scan_results = []

# Display results
if "scan_results" in st.session_state and st.session_state.scan_results:
    topics = st.session_state.scan_results

    st.markdown(f"### 📊 {len(topics)} sonuç bulundu")

    # Category summary
    categories = {}
    for t in topics:
        categories[t.category] = categories.get(t.category, 0) + 1

    if categories:
        cols = st.columns(min(len(categories), 5))
        for i, (cat, count) in enumerate(sorted(categories.items(), key=lambda x: -x[1])):
            with cols[i % len(cols)]:
                st.metric(cat, count)

    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

    # List topics
    for i, topic in enumerate(topics):
        render_tweet_card(topic, key_prefix=f"scan_{i}")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("✍️ Bu konuda yaz", key=f"write_{i}", use_container_width=True):
                st.session_state.selected_topic = {
                    "text": topic.text,
                    "author": topic.author_username,
                    "url": topic.url,
                    "id": topic.id,
                    "category": topic.category,
                }
                st.switch_page("pages/2_✍️_Yaz.py")

        with col2:
            if st.button("💬 Quote Tweet", key=f"quote_{i}", use_container_width=True):
                st.session_state.quote_topic = {
                    "text": topic.text,
                    "author": topic.author_username,
                    "url": topic.url,
                    "id": topic.id,
                }
                st.session_state.write_mode = "quote"
                st.switch_page("pages/2_✍️_Yaz.py")

        with col3:
            st.link_button("🔗 X'te Aç", topic.url, use_container_width=True)

        st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

elif "scan_results" in st.session_state:
    st.info("Arama kriterlerine uygun sonuç bulunamadı. Filtreleri değiştirmeyi deneyin.")

else:
    # Show monitored accounts
    st.markdown("### 👀 İzlenen AI Hesapları")
    st.markdown("Tarama başlatıldığında bu hesaplar kontrol edilecek:")

    custom_accounts = load_monitored_accounts()
    all_accounts = DEFAULT_AI_ACCOUNTS + custom_accounts

    # Display in columns
    cols = st.columns(4)
    for i, account in enumerate(all_accounts[:24]):
        with cols[i % 4]:
            st.markdown(f"""
            <div style="background:#1a1a2e; border:1px solid #2a2a4a; border-radius:8px;
                        padding:8px 12px; margin:4px 0; font-size:13px;">
                <span style="color:#1DA1F2;">@{account}</span>
            </div>
            """, unsafe_allow_html=True)

    if len(all_accounts) > 24:
        st.caption(f"...ve {len(all_accounts) - 24} hesap daha")

    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

    st.info("💡 **İpucu:** Tarama butonuna basarak son saatlerin AI gelişmelerini bulun. "
            "Sonra bir konu seçip tweet yazabilirsiniz.")
