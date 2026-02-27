"""
Ayarlar Sayfası
API anahtarları, monitör edilen hesaplar, yazım tarzı eğitimi
"""
import streamlit as st
import json
from modules.ui_components import inject_custom_css, check_password, get_secret
from modules.content_generator import ContentGenerator
from modules.tweet_publisher import TweetPublisher
from modules.twitter_scanner import DEFAULT_AI_ACCOUNTS
from modules.style_manager import (
    load_user_samples, save_user_samples,
    load_custom_persona, save_custom_persona,
    load_monitored_accounts, save_monitored_accounts,
    load_post_history
)

# Page config
st.set_page_config(
    page_title="Ayarlar | X AI Otomasyon",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_custom_css()

if not check_password():
    st.stop()

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>⚙️ Ayarlar</h1>
    <p style="color:#8899a6;">API anahtarları, hesaplar ve yazım tarzı ayarları</p>
</div>
""", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔑 API Anahtarları",
    "👤 X Hesap Bilgileri",
    "👀 İzlenen Hesaplar",
    "✍️ Yazım Tarzı",
    "📊 Geçmiş"
])

# ===================
# TAB 1: API Keys
# ===================
with tab1:
    st.markdown("### Twitter/X API Anahtarları")
    st.markdown("""
    > Twitter API anahtarlarını [developer.x.com](https://developer.x.com) adresinden alabilirsiniz.
    > Basic plan ($100/ay) tweet okuma ve yazma için gereklidir.

    **Streamlit Cloud kullanıyorsanız:** `.streamlit/secrets.toml` dosyasına ekleyin.
    **Lokal kullanıyorsanız:** Aşağıdaki alanları doldurun.
    """)

    st.markdown("---")

    # Show current status
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Twitter API**")
        bearer = get_secret("twitter_bearer_token", "")
        api_key = get_secret("twitter_api_key", "")
        api_secret = get_secret("twitter_api_secret", "")
        access_token = get_secret("twitter_access_token", "")
        access_secret = get_secret("twitter_access_secret", "")

        if bearer:
            st.success("Bearer Token: Yapılandırılmış ✓")
        else:
            st.warning("Bearer Token: Eksik")

        if all([api_key, api_secret]):
            st.success("API Key/Secret: Yapılandırılmış ✓")
        else:
            st.warning("API Key/Secret: Eksik")

        if all([access_token, access_secret]):
            st.success("Access Token/Secret: Yapılandırılmış ✓")
        else:
            st.warning("Access Token/Secret: Eksik")

    with col2:
        st.markdown("**AI API**")
        minimax_key = get_secret("minimax_api_key", "")
        anthropic_key = get_secret("anthropic_api_key", "")
        openai_key = get_secret("openai_api_key", "")

        if minimax_key:
            st.success("MiniMax: Yapılandırılmış ✓")
        else:
            st.warning("MiniMax: Eksik")

        if anthropic_key:
            st.success("Anthropic Claude: Yapılandırılmış ✓")
        else:
            st.warning("Anthropic Claude: Eksik")

        if openai_key:
            st.success("OpenAI: Yapılandırılmış ✓")
        else:
            st.warning("OpenAI: Eksik")

    st.markdown("---")

    st.markdown("### secrets.toml Şablonu")
    st.markdown("Aşağıdaki şablonu `.streamlit/secrets.toml` dosyanıza kopyalayın:")

    st.code("""# App password
app_password = "your_secure_password_here"

# Twitter/X API Keys
twitter_bearer_token = "your_bearer_token"
twitter_api_key = "your_api_key"
twitter_api_secret = "your_api_secret"
twitter_access_token = "your_access_token"
twitter_access_secret = "your_access_secret"

# AI API Keys (en az birini doldurun)
minimax_api_key = "your_minimax_api_key"
anthropic_api_key = "your_anthropic_api_key"
openai_api_key = "your_openai_api_key"
""", language="toml")

    # Test connections
    st.markdown("### Bağlantı Testi")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🐦 Twitter Bağlantısını Test Et", use_container_width=True):
            if all([api_key, api_secret, access_token, access_secret]):
                try:
                    publisher = TweetPublisher(
                        api_key=api_key,
                        api_secret=api_secret,
                        access_token=access_token,
                        access_secret=access_secret,
                        bearer_token=bearer,
                    )
                    me = publisher.get_me()
                    if me["success"]:
                        st.success(f"Bağlantı başarılı! Hesap: @{me['username']}")
                    else:
                        st.error(f"Bağlantı hatası: {me['error']}")
                except Exception as e:
                    st.error(f"Hata: {e}")
            else:
                st.error("Twitter API anahtarları eksik!")

    with col2:
        if st.button("🧠 AI API Bağlantısını Test Et", use_container_width=True):
            test_provider = "minimax" if minimax_key else "anthropic" if anthropic_key else "openai" if openai_key else None
            test_key = minimax_key or anthropic_key or openai_key

            if test_provider and test_key:
                try:
                    gen = ContentGenerator(provider=test_provider, api_key=test_key)
                    result = gen.generate_tweet(
                        topic_text="Test mesajı - AI bağlantı testi",
                        style="samimi"
                    )
                    st.success(f"AI API bağlantısı başarılı! ({test_provider.capitalize()})")
                    st.caption(f"Test yanıtı: {result[:100]}...")
                except Exception as e:
                    st.error(f"AI API hatası: {e}")
            else:
                st.error("AI API anahtarı eksik!")


# ===================
# TAB 2: X Account
# ===================
with tab2:
    st.markdown("### X Hesap Bilgileri")

    if all([api_key, api_secret, access_token, access_secret]):
        if st.button("Hesap Bilgilerini Getir", type="primary", use_container_width=True):
            try:
                publisher = TweetPublisher(
                    api_key=api_key,
                    api_secret=api_secret,
                    access_token=access_token,
                    access_secret=access_secret,
                    bearer_token=bearer,
                )
                me = publisher.get_me()

                if me["success"]:
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"""
                        <div class="stat-box">
                            <div style="font-size:24px; font-weight:bold; color:#f0f0f0;">
                                {me['name']}
                            </div>
                            <div style="color:#1DA1F2; font-size:14px;">@{me['username']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.metric("Takipçi", f"{me['followers']:,}")

                    with col3:
                        st.metric("Tweet", f"{me['tweet_count']:,}")

                    if me.get("bio"):
                        st.markdown(f"**Bio:** {me['bio']}")

                else:
                    st.error(me["error"])

            except Exception as e:
                st.error(f"Hata: {e}")
    else:
        st.info("X hesap bilgilerini görmek için önce API anahtarlarını yapılandırın.")


# ===================
# TAB 3: Monitored Accounts
# ===================
with tab3:
    st.markdown("### İzlenen AI Hesapları")
    st.markdown("Bu hesaplar tarama sırasında otomatik kontrol edilir.")

    # Default accounts
    st.markdown("**Varsayılan Hesaplar:**")
    cols = st.columns(4)
    for i, account in enumerate(DEFAULT_AI_ACCOUNTS[:20]):
        with cols[i % 4]:
            st.markdown(f"`@{account}`")

    if len(DEFAULT_AI_ACCOUNTS) > 20:
        st.caption(f"...ve {len(DEFAULT_AI_ACCOUNTS) - 20} hesap daha")

    st.markdown("---")

    # Custom accounts
    st.markdown("**Özel Hesaplar:**")
    custom_accounts = load_monitored_accounts()

    new_account = st.text_input(
        "Yeni hesap ekle",
        placeholder="@username (@ olmadan yazın)",
        key="new_account"
    )

    if st.button("Hesap Ekle", key="add_account"):
        if new_account:
            clean = new_account.strip().lstrip("@")
            if clean and clean not in custom_accounts:
                custom_accounts.append(clean)
                save_monitored_accounts(custom_accounts)
                st.success(f"@{clean} eklendi!")
                st.rerun()
            elif clean in custom_accounts:
                st.warning("Bu hesap zaten ekli!")
        else:
            st.warning("Hesap adı girin!")

    if custom_accounts:
        for i, account in enumerate(custom_accounts):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**@{account}**")
            with col2:
                if st.button("Kaldır", key=f"remove_account_{i}"):
                    custom_accounts.pop(i)
                    save_monitored_accounts(custom_accounts)
                    st.rerun()
    else:
        st.info("Henüz özel hesap eklenmemiş.")


# ===================
# TAB 4: Writing Style
# ===================
with tab4:
    st.markdown("### Yazım Tarzı Eğitimi")
    st.markdown("""
    AI'ın senin gibi yazması için kendi tweet örneklerini ekle.
    Ne kadar çok örnek eklersen, tarz o kadar doğru olur.
    """)

    # Sample tweets
    st.markdown("#### Tweet Örneklerin")

    user_samples = load_user_samples()

    new_sample = st.text_area(
        "Yeni örnek tweet ekle",
        placeholder="Kendi tarzında yazdığın bir tweet örneği yapıştır...",
        height=80,
        key="new_sample"
    )

    if st.button("Örnek Ekle", key="add_sample"):
        if new_sample:
            user_samples.append(new_sample.strip())
            save_user_samples(user_samples)
            st.success("Örnek eklendi!")
            st.rerun()

    # Bulk add
    with st.expander("Toplu Örnek Ekle"):
        bulk_samples = st.text_area(
            "Her satıra bir tweet yaz",
            placeholder="Tweet 1\nTweet 2\nTweet 3",
            height=150,
            key="bulk_samples"
        )
        if st.button("Toplu Ekle", key="bulk_add"):
            if bulk_samples:
                new_samples = [s.strip() for s in bulk_samples.split("\n") if s.strip()]
                user_samples.extend(new_samples)
                save_user_samples(user_samples)
                st.success(f"{len(new_samples)} örnek eklendi!")
                st.rerun()

    # Show existing samples
    if user_samples:
        st.markdown(f"**Kayıtlı Örnekler ({len(user_samples)}):**")
        for i, sample in enumerate(user_samples):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"""
                <div style="background:#1a1a2e; border:1px solid #2a2a4a;
                            border-radius:8px; padding:8px 12px; margin:4px 0;
                            font-size:13px; color:#f0f0f0;">
                    {sample}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("Sil", key=f"del_sample_{i}"):
                    user_samples.pop(i)
                    save_user_samples(user_samples)
                    st.rerun()
    else:
        st.info("Henüz örnek tweet eklenmemiş. AI'ın senin gibi yazması için örnekler ekle!")

    st.markdown("---")

    # Style analysis
    st.markdown("#### Tarz Analizi")
    st.markdown("AI, örnek tweet'lerini analiz edip yazım tarzını öğrenebilir.")

    custom_persona = load_custom_persona()

    if custom_persona:
        st.markdown("**Mevcut Tarz Profili:**")
        st.markdown(f"""
        <div style="background:#1a1a2e; border:1px solid #2a2a4a;
                    border-radius:8px; padding:14px; margin:8px 0;
                    font-size:13px; color:#f0f0f0; line-height:1.6;">
            {custom_persona}
        </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🧠 Tarzımı Analiz Et", type="primary", use_container_width=True,
                      disabled=len(user_samples) < 5):
            if len(user_samples) < 5:
                st.warning("En az 5 tweet örneği gerekli!")
            else:
                if get_secret("minimax_api_key", ""):
                    ai_provider = "minimax"
                elif get_secret("anthropic_api_key", ""):
                    ai_provider = "anthropic"
                else:
                    ai_provider = "openai"
                api_key = get_secret("minimax_api_key", "") or get_secret("anthropic_api_key", "") or get_secret("openai_api_key", "")

                if not api_key:
                    st.error("AI API anahtarı gerekli!")
                else:
                    with st.spinner("Yazım tarzın analiz ediliyor..."):
                        try:
                            gen = ContentGenerator(provider=ai_provider, api_key=api_key)
                            analysis = gen.analyze_writing_style(user_samples)
                            save_custom_persona(analysis)
                            st.success("Tarz analizi tamamlandı!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Analiz hatası: {e}")

    with col2:
        if st.button("🗑️ Tarz Profilini Sıfırla", use_container_width=True):
            save_custom_persona("")
            st.success("Tarz profili sıfırlandı!")
            st.rerun()

    if len(user_samples) < 5:
        st.caption(f"Analiz için en az 5 örnek gerekli. Şu an: {len(user_samples)}/5")

    st.markdown("---")

    # Custom persona override
    with st.expander("Manuel Persona Tanımı"):
        st.markdown("AI'a nasıl yazması gerektiğini manuel olarak tanımlayabilirsin:")
        manual_persona = st.text_area(
            "Persona tanımı",
            value=custom_persona,
            height=200,
            placeholder="Örn: Genç bir Türk yazılımcıyım. Kısa ve öz yazıyorum...",
            key="manual_persona"
        )
        if st.button("Kaydet", key="save_persona"):
            save_custom_persona(manual_persona)
            st.success("Persona kaydedildi!")


# ===================
# TAB 5: History
# ===================
with tab5:
    st.markdown("### Paylaşım Geçmişi")

    history = load_post_history()

    if history:
        st.markdown(f"**Toplam {len(history)} paylaşım**")

        for i, entry in enumerate(history):
            with st.container():
                st.markdown(f"""
                <div class="tweet-card" style="padding:12px 16px;">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="tweet-category">{entry.get('type', 'tweet').upper()}</span>
                        <span class="tweet-time">{entry.get('posted_at', '')[:16]}</span>
                    </div>
                    <div class="tweet-text" style="margin:8px 0; font-size:14px;">
                        {entry.get('text', '')[:200]}
                    </div>
                    <div style="color:#8899a6; font-size:12px;">
                        Tarz: {entry.get('style', 'N/A')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if entry.get("url"):
                    st.link_button("X'te Görüntüle", entry["url"],
                                   key=f"view_history_{i}")

        st.markdown("---")

        if st.button("🗑️ Geçmişi Temizle", key="clear_history"):
            from modules.style_manager import save_post_history
            save_post_history([])
            st.success("Geçmiş temizlendi!")
            st.rerun()
    else:
        st.info("Henüz paylaşım geçmişi yok.")
