"""
Ayarlar Sayfası
API anahtarları, monitör edilen hesaplar, yazım tarzı eğitimi
"""
import streamlit as st
import json
from modules.ui_components import inject_custom_css, check_password, get_secret, render_sidebar_nav
from modules.content_generator import ContentGenerator
from modules.tweet_publisher import TweetPublisher
from modules.twitter_scanner import DEFAULT_AI_ACCOUNTS
from modules.style_manager import (
    load_user_samples, save_user_samples,
    load_custom_persona, save_custom_persona,
    load_monitored_accounts, save_monitored_accounts,
    load_post_history
)
from modules.tweet_pool import (
    load_pool, save_pool, load_pool_accounts, save_pool_accounts,
    add_tweets_to_pool, get_pool_stats, bulk_fetch_accounts,
)

# Page config
st.set_page_config(
    page_title="Ayarlar | X AI Otomasyon",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="auto",
)

inject_custom_css()

if not check_password():
    st.stop()

render_sidebar_nav(current_page="ayarlar")

# --- Header ---
st.markdown("""
<div class="page-header">
    <span class="page-icon">⚙️</span>
    <h1>Ayarlar</h1>
    <p>API anahtarları, hesaplar ve yazım tarzı ayarları</p>
</div>
""", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔑 API Anahtarları",
    "👤 X Hesap Bilgileri",
    "👀 İzlenen Hesaplar",
    "✍️ Yazım Tarzı",
    "🏊 Tweet Havuzu",
    "📊 Geçmiş",
    "🔄 Güncelleme"
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

    st.markdown("---")

    st.markdown("### Twikit (Ücretsiz Arama)")
    st.markdown("""
    > Twikit, Twitter API'ye **ücretsiz alternatif** olarak tweet arama yapmanızı sağlar.
    > Bearer Token maliyetini düşürmek için kullanılır. Yazma işlemi yapmaz, sadece okur.

    **Nasıl çalışır:** Twitter hesabınızla giriş yapar, cookie kaydeder, sonraki aramalarda cookie kullanır.
    """)

    twikit_user = get_secret("twikit_username", "")
    twikit_pass = get_secret("twikit_password", "")
    twikit_email = get_secret("twikit_email", "")
    twikit_totp = get_secret("twikit_totp_secret", "")

    col_tw1, col_tw2 = st.columns(2)
    with col_tw1:
        if twikit_user:
            st.success(f"Twikit Kullanıcı: @{twikit_user} ✓")
        else:
            st.warning("Twikit: Yapılandırılmamış")

    with col_tw2:
        from pathlib import Path
        cookies_path = Path(__file__).parent.parent / "data" / "twikit_cookies.json"
        if cookies_path.exists():
            st.success("Twikit Cookie: Kayıtlı ✓")
        else:
            st.info("Twikit Cookie: Henüz oluşturulmadı")

    col_test1, col_test2 = st.columns(2)
    with col_test1:
        if st.button("🔗 Twikit Bağlantısını Test Et", use_container_width=True):
            if twikit_user and twikit_pass:
                with st.spinner("Twikit ile giriş yapılıyor... (bu 10-20 saniye sürebilir)"):
                    try:
                        from modules.twikit_client import TwikitSearchClient
                        tc = TwikitSearchClient(
                            twikit_user, twikit_pass, twikit_email,
                            totp_secret=twikit_totp
                        )
                        if tc.authenticate():
                            st.success("Twikit bağlantısı başarılı! Cookie kaydedildi.")
                        else:
                            st.error(f"Twikit giriş başarısız!")
                            if tc.last_error:
                                st.warning(f"**Hata detayı:** {tc.last_error}")

                            # Show troubleshooting tips
                            with st.expander("🔧 Sorun Giderme"):
                                st.markdown("""
**Yaygın Çözümler:**

1. **Önce twitter.com'dan giriş yapın**
   - Tarayıcınızdan twitter.com'a gidin
   - Aynı hesapla giriş yapın
   - Eğer doğrulama isterse (captcha, e-posta kodu vb.) tamamlayın
   - Sonra buraya dönüp tekrar deneyin

2. **2FA (İki Faktörlü Doğrulama) sorunu**
   - Twitter'da 2FA açıksa, `secrets.toml`'a ekleyin:
   ```
   twikit_totp_secret = "SIZIN_TOTP_SECRET_KODUNUZ"
   ```
   - TOTP secret'ı bulamıyorsanız: Twitter → Ayarlar → Güvenlik → 2FA'yı geçici kapatın
   - Twikit giriş yaptıktan sonra 2FA'yı geri açabilirsiniz (cookie'ler 2FA'ya ihtiyaç duymaz)

3. **Şifre özel karakter sorunu**
   - Şifrenizde `"`, `'`, `\\` gibi karakterler varsa `secrets.toml`'da sorun çıkabilir
   - Şifrenizi tırnak içinde yazarken kaçış karakteri kullanın:
   ```
   twikit_password = "sifre\\"icinde\\"tirnak"
   ```

4. **Hesap kilitli/askıda**
   - twitter.com'dan giriş yapıp hesabınızın aktif olduğunu kontrol edin
   - Kilitliyse Twitter'ın istediklerini yapın (telefon doğrulama vb.)

5. **Cookie sil ve tekrar dene**
   - Sağdaki "Cookie Sil" butonuna basın
   - Sonra tekrar test edin
                                """)
                    except Exception as e:
                        st.error(f"Twikit beklenmeyen hatası: {e}")
            else:
                st.error("Twikit kullanıcı adı ve şifre gerekli! secrets.toml'a ekleyin.")

    with col_test2:
        if st.button("🗑️ Twikit Cookie Sil", use_container_width=True):
            if cookies_path.exists():
                cookies_path.unlink()
                st.success("Cookie silindi! Sonraki taramada yeniden giriş yapılacak.")
            else:
                st.info("Silinecek cookie yok.")

    # Cookie section
    st.markdown("---")
    st.markdown("### Cookie Ayarları (403 Hatası Çözümü)")

    # Check if cookies are already in secrets (permanent)
    _has_secret_cookies = bool(get_secret("twikit_auth_token", "")) and bool(get_secret("twikit_ct0", ""))

    if _has_secret_cookies:
        st.success("Cookie'ler `secrets.toml` içinde kayıtlı (kalıcı)")
    else:
        st.markdown("""
        > **403 hatası mı alıyorsun?** Twitter, cloud sunucu IP'lerinden girişi engelleyebilir.
        >
        > **Kalıcı Çözüm (Tavsiye):** Cookie'leri `secrets.toml`'a ekle - bir kez yap, hep çalışsın:
        > ```
        > twikit_auth_token = "auth_token_değerin"
        > twikit_ct0 = "ct0_değerin"
        > ```
        > Streamlit Cloud: Settings → Secrets kısmına ekle.
        >
        > **Geçici Çözüm:** Aşağıdaki alanlara yapıştır (uygulama her açıldığında tekrar gerekir).
        """)

    import json as _json

    with st.expander("🍪 Tarayıcıdan Cookie Yapıştır (Geçici)" if not _has_secret_cookies else "🍪 Tarayıcıdan Cookie Yapıştır",
                      expanded=not cookies_path.exists() and not _has_secret_cookies):
        st.markdown("""
        **F12 → Application → Cookies → x.com** altında bu değerleri bul:
        """)

        auth_token = st.text_input(
            "auth_token",
            type="password",
            placeholder="F12 → Cookies → auth_token değeri",
            key="manual_auth_token",
            help="Twitter oturum token'ı. Cookies listesinde 'auth_token' satırının Value sütunu."
        )

        ct0 = st.text_input(
            "ct0",
            type="password",
            placeholder="F12 → Cookies → ct0 değeri",
            key="manual_ct0",
            help="CSRF token. Cookies listesinde 'ct0' satırının Value sütunu."
        )

        if st.button("💾 Cookie'leri Kaydet", type="primary", use_container_width=True,
                      disabled=not (auth_token and ct0)):
            if auth_token and ct0:
                try:
                    # Build cookie dict — Twikit uses simple key-value pairs
                    cookie_dict = {
                        "auth_token": auth_token.strip(),
                        "ct0": ct0.strip(),
                    }

                    cookies_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(cookies_path, "w", encoding="utf-8") as f:
                        _json.dump(cookie_dict, f, ensure_ascii=False, indent=2)

                    st.success("Cookie'ler kaydedildi! Şimdi 'Twikit Bağlantısını Test Et' butonuna basın.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Cookie kaydetme hatası: {e}")

        st.markdown("---")

        st.markdown("**Cookie nerede bulunur? (Adım adım)**")
        st.markdown("""
1. **twitter.com** / **x.com** adresine git ve giriş yap
2. Sayfada **F12** tuşuna bas (Developer Tools açılır)
3. Üst menüden **Application** sekmesine tıkla
   - Chrome: Application
   - Firefox: Storage
4. Sol menüde **Cookies** → **https://x.com** tıkla
5. Tabloda şu satırları bul:
   - `auth_token` → Value sütunundaki değeri kopyala
   - `ct0` → Value sütunundaki değeri kopyala
6. Yukarıdaki alanlara yapıştır ve "Kaydet" butonuna bas
        """)

    with st.expander("💾 Kalıcı Kayıt (secrets.toml'a ekle)"):
        st.markdown("""
        Cookie'leri kalıcı yapmak için **Streamlit Cloud** üzerinden:

        1. Uygulamanın **Settings** sayfasına git
        2. **Secrets** sekmesine tıkla
        3. Mevcut secrets'ların **altına** şu satırları ekle:

        ```
        twikit_auth_token = "BURAYA_AUTH_TOKEN_DEĞERINI_YAZ"
        twikit_ct0 = "BURAYA_CT0_DEĞERINI_YAZ"
        ```

        4. **Save** butonuna bas
        5. Uygulama otomatik yeniden başlar ve cookie'ler kalıcı olur!

        > Cookie değerlerini yukarıdaki F12 adımlarıyla bulabilirsin.
        """)

    with st.expander("📁 Cookie Dosyası Yükle (Alternatif)"):
        st.markdown("generate_cookies.py ile oluşturulan JSON dosyasını yükleyebilirsiniz.")

        uploaded_cookie = st.file_uploader(
            "Cookie dosyası yükle (.json)",
            type=["json"],
            key="upload_twikit_cookie"
        )

        if uploaded_cookie:
            try:
                cookie_data = uploaded_cookie.read().decode("utf-8")
                _json.loads(cookie_data)

                cookies_path.parent.mkdir(parents=True, exist_ok=True)
                with open(cookies_path, "w", encoding="utf-8") as f:
                    f.write(cookie_data)

                st.success("Cookie dosyası yüklendi!")
                st.rerun()
            except _json.JSONDecodeError:
                st.error("Geçersiz JSON dosyası!")
            except Exception as e:
                st.error(f"Cookie yükleme hatası: {e}")

    st.markdown("---")

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

        st.markdown("**xAI / Grok API**")
        xai_key = get_secret("xai_api_key", "")

        if xai_key:
            st.success("xAI Grok: Yapılandırılmış ✓")
        else:
            st.info("xAI Grok: Yapılandırılmamış (opsiyonel)")

        st.markdown("""
        > [console.x.ai](https://console.x.ai) adresinden API key alın.
        > Yeni hesaplara **$25 ücretsiz kredi** verilir.
        > Grok ile X araması ve otonom araştırma yapabilirsiniz.
        """)

        if st.button("🧠 Grok Bağlantısını Test Et", use_container_width=True, key="test_grok"):
            if xai_key:
                with st.spinner("Grok API test ediliyor..."):
                    try:
                        from modules.grok_client import test_grok_connection
                        result = test_grok_connection(xai_key)
                        if result["success"]:
                            st.success(f"Grok API bağlantısı başarılı! Yanıt: {result['message']}")
                        else:
                            st.error(f"Grok API hatası: {result['error']}")
                    except Exception as e:
                        st.error(f"Grok test hatası: {e}")
            else:
                st.error("xAI API key eksik! `secrets.toml`'a `xai_api_key` ekleyin.")

    st.markdown("---")

    st.markdown("### Telegram Bildirimleri")
    st.markdown("""
    > Zamanlayıcı her taramada yeni konuları Telegram'a bildirim olarak gönderir.
    > iPhone/Android'den anında takip edebilirsin.
    """)

    tg_token = get_secret("telegram_bot_token", "")
    tg_chat_id = get_secret("telegram_chat_id", "")

    col_tg1, col_tg2 = st.columns(2)
    with col_tg1:
        if tg_token:
            st.success("Telegram Bot Token: Yapılandırılmış ✓")
        else:
            st.warning("Telegram Bot Token: Eksik")
    with col_tg2:
        if tg_chat_id:
            st.success(f"Telegram Chat ID: {tg_chat_id} ✓")
        else:
            st.warning("Telegram Chat ID: Eksik")

    if tg_token and tg_chat_id:
        if st.button("📨 Telegram Test Mesajı Gönder", use_container_width=True):
            from modules.telegram_notifier import TelegramNotifier
            notifier = TelegramNotifier(tg_token, tg_chat_id)
            info = notifier.test_connection()
            if info["ok"]:
                if notifier.send_message("✅ AI Gündem Dashboard bağlantısı başarılı!"):
                    st.success(f"Test mesajı gönderildi! Bot: @{info['bot_username']}")
                else:
                    st.error("Bot bağlandı ama mesaj gönderilemedi. Chat ID'yi kontrol edin.")
            else:
                st.error(f"Telegram bağlantı hatası: {info['error']}")

    with st.expander("Telegram Bot Nasıl Kurulur?"):
        st.markdown("""
1. Telegram'da **@BotFather**'ı aç
2. `/newbot` yaz, bir isim ver (örnek: `AI Gundem Bot`)
3. Sana bir **token** verecek → `secrets.toml`'a ekle:
   ```
   telegram_bot_token = "1234567890:ABCdef..."
   ```
4. Oluşturduğun botu bul ve `/start` yaz
5. **Chat ID** almak için:
   - Botuna herhangi bir mesaj at
   - Tarayıcıda bu URL'yi aç: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - `"chat":{"id":123456789}` değerini bul
   - `secrets.toml`'a ekle:
   ```
   telegram_chat_id = "123456789"
   ```
        """)

    st.markdown("---")

    st.markdown("### secrets.toml Şablonu")
    st.markdown("Aşağıdaki şablonu `.streamlit/secrets.toml` dosyanıza kopyalayın:")

    st.code("""# App password
app_password = "your_secure_password_here"

# Twitter/X API Keys (ücretli - opsiyonel, Twikit varsa gerekli değil)
twitter_bearer_token = "your_bearer_token"
twitter_api_key = "your_api_key"
twitter_api_secret = "your_api_secret"
twitter_access_token = "your_access_token"
twitter_access_secret = "your_access_secret"

# Twikit (ücretsiz Twitter arama - Bearer Token yerine)
twikit_username = "your_twitter_username"
twikit_password = "your_twitter_password"
twikit_email = "your_twitter_email"
twikit_totp_secret = ""  # 2FA açıksa TOTP secret (opsiyonel)

# AI API Keys (en az birini doldurun)
minimax_api_key = "your_minimax_api_key"
anthropic_api_key = "your_anthropic_api_key"
openai_api_key = "your_openai_api_key"

# xAI Grok API (opsiyonel — X araması ve otonom araştırma)
xai_api_key = "your_xai_api_key"

# Telegram Bildirimleri (opsiyonel)
telegram_bot_token = "your_bot_token"
telegram_chat_id = "your_chat_id"
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
                            <div style="font-size:24px; font-weight:bold; color:#f1f5f9;">
                                {me['name']}
                            </div>
                            <div style="color:#a5b4fc; font-size:14px;">@{me['username']}</div>
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

    # Default accounts - kategori bazlı gösterim
    import os
    _accounts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ai_accounts.json")
    _ai_data = {}
    if os.path.exists(_accounts_path):
        with open(_accounts_path, "r", encoding="utf-8") as _f:
            _ai_data = json.load(_f)

    if _ai_data.get("categories"):
        st.markdown(f"**Varsayılan Hesaplar ({len(DEFAULT_AI_ACCOUNTS)}):**")
        _cat_map = {c["id"]: c for c in _ai_data["categories"]}
        _grouped = {}
        for acc in _ai_data.get("accounts", []):
            cat_id = acc.get("category", "diger")
            _grouped.setdefault(cat_id, []).append(acc)

        for cat in _ai_data["categories"]:
            cat_accounts = _grouped.get(cat["id"], [])
            if not cat_accounts:
                continue
            with st.expander(f"**{cat['name']}** ({len(cat_accounts)}) — {cat['description']}", expanded=False):
                cols = st.columns(3)
                for i, acc in enumerate(cat_accounts):
                    with cols[i % 3]:
                        st.markdown(f"`@{acc['username']}` — {acc['name']}")
    else:
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
                <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06);
                            border-radius:8px; padding:8px 12px; margin:4px 0;
                            font-size:13px; color:#f1f5f9;">
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
        <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06);
                    border-radius:8px; padding:14px; margin:8px 0;
                    font-size:13px; color:#f1f5f9; line-height:1.6;">
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
# TAB 5: Tweet Havuzu
# ===================
with tab5:
    st.markdown("### Tweet Havuzu Yönetimi")
    st.markdown("""
    Birden fazla hesaptan yüksek etkileşimli tweet'leri otomatik çekip biriktir.
    Bu havuz, tweet yazarken AI'a çeşitli örnekler sunar. Tweet'ler hiçbir zaman silinmez, sadece birikir.
    """)

    # --- Hesap Listesi ---
    st.markdown("#### Kaynak Hesaplar")
    st.markdown("Tweet'leri çekilecek hesapları virgülle ayırarak girin.")

    pool_accounts = load_pool_accounts()

    accounts_input = st.text_area(
        "Hesap listesi",
        value=", ".join(pool_accounts) if pool_accounts else "",
        placeholder="hrrcnes, elonmusk, hesap3, hesap4",
        height=80,
        key="pool_accounts_input",
        help="@ işareti olmadan, virgülle ayırarak yazın"
    )

    col_save, col_clear = st.columns(2)
    with col_save:
        if st.button("💾 Hesap Listesini Kaydet", use_container_width=True, type="primary"):
            if accounts_input.strip():
                new_accounts = [a.strip().lstrip("@").lower()
                               for a in accounts_input.split(",") if a.strip()]
                save_pool_accounts(new_accounts)
                st.success(f"{len(new_accounts)} hesap kaydedildi!")
                st.rerun()
            else:
                st.warning("En az bir hesap girin!")

    with col_clear:
        if st.button("🗑️ Listeyi Temizle", use_container_width=True):
            save_pool_accounts([])
            st.success("Hesap listesi temizlendi!")
            st.rerun()

    st.markdown("---")

    # --- Engagement Eşiği ---
    st.markdown("#### Çekme Ayarları")
    col_eng, col_count = st.columns(2)
    with col_eng:
        min_engagement = st.slider(
            "Min Engagement Skoru",
            min_value=0, max_value=1000, value=100, step=10,
            help="Bu skorun altındaki tweet'ler havuza eklenmez. RT=20x, Reply=13.5x, Like=1x",
            key="pool_min_engagement"
        )
    with col_count:
        tweet_count = st.slider(
            "Hesap başına çekilecek tweet",
            min_value=50, max_value=1000, value=500, step=50,
            help="Her hesaptan kaç tweet çekilsin",
            key="pool_tweet_count"
        )

    # --- Çekme Butonu ---
    pool_accounts_current = load_pool_accounts()
    if pool_accounts_current:
        st.markdown(f"**{len(pool_accounts_current)} hesaptan tweet çekilecek:** {', '.join(f'@{a}' for a in pool_accounts_current)}")

        if st.button("🚀 Tweet'leri Çek ve Havuza Ekle", type="primary", use_container_width=True,
                      key="fetch_pool_tweets"):
            # Twikit client oluştur
            twikit_user = get_secret("twikit_username", "")
            twikit_pass = get_secret("twikit_password", "")
            twikit_email = get_secret("twikit_email", "")
            twikit_totp = get_secret("twikit_totp_secret", "")

            if not twikit_user or not twikit_pass:
                st.error("Twikit kullanıcı bilgileri eksik! API Anahtarları sekmesinden ayarlayın.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()

                def progress_callback(msg):
                    status_text.markdown(f"⏳ {msg}")

                with st.spinner("Tweet'ler çekiliyor..."):
                    try:
                        from modules.twikit_client import TwikitSearchClient
                        tc = TwikitSearchClient(
                            twikit_user, twikit_pass, twikit_email,
                            totp_secret=twikit_totp
                        )

                        if not tc.authenticate():
                            st.error("Twikit giriş başarısız! Cookie veya şifre kontrol edin.")
                        else:
                            results = bulk_fetch_accounts(
                                twikit_client=tc,
                                accounts=pool_accounts_current,
                                min_engagement=min_engagement,
                                tweet_count=tweet_count,
                                progress_callback=progress_callback,
                            )

                            # Sonuçları göster
                            total_added = 0
                            for i, r in enumerate(results):
                                progress_bar.progress((i + 1) / len(results))
                                if r.get("error"):
                                    st.warning(f"@{r['username']}: Hata — {r['error']}")
                                else:
                                    total_added += r["added"]
                                    st.success(
                                        f"@{r['username']}: {r['fetched']} tweet çekildi, "
                                        f"**{r['added']} eklendi**, {r['skipped']} atlandı"
                                    )

                            status_text.empty()
                            st.markdown(f"### Toplam **{total_added}** yeni tweet havuza eklendi!")

                    except Exception as e:
                        st.error(f"Beklenmeyen hata: {e}")
    else:
        st.info("Önce yukarıdan hesap listesi ekleyin, sonra tweet'leri çekebilirsiniz.")

    st.markdown("---")

    # --- Havuz İstatistikleri ---
    st.markdown("#### Havuz İstatistikleri")
    pool_data = load_pool()
    stats = get_pool_stats(pool_data)

    if stats["total_tweets"] > 0:
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric("Toplam Tweet", f"{stats['total_tweets']:,}")
        with col_s2:
            st.metric("Hesap Sayısı", stats["accounts_count"])
        with col_s3:
            st.metric("Ort. Engagement", f"{stats['avg_engagement']:,.0f}")
        with col_s4:
            st.metric("Max Engagement", f"{stats['max_engagement']:,.0f}")

        # Hesap bazlı dağılım
        if stats.get("authors"):
            st.markdown("**Hesap bazlı dağılım:**")
            for author, count in sorted(stats["authors"].items(), key=lambda x: x[1], reverse=True):
                st.markdown(f"- @{author}: **{count}** tweet")

        # Son güncelleme
        if pool_data.get("last_updated"):
            st.caption(f"Son güncelleme: {pool_data['last_updated'][:19]}")

        # Havuz önizleme
        with st.expander(f"Havuz Önizleme (ilk 10 tweet)"):
            for t in pool_data["pool"][:10]:
                st.markdown(f"""
                <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.06);
                            border-radius:8px; padding:8px 12px; margin:4px 0; font-size:13px; color:#f1f5f9;">
                    <b>@{t['author']}</b> — Skor: {t['engagement_score']:,.0f}<br>
                    {t['text'][:200]}{'...' if len(t['text']) > 200 else ''}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Havuz henüz boş. Yukarıdan hesap ekleyip tweet'leri çekin!")


# ===================
# TAB 6: History
# ===================
with tab6:
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
                    <div style="color:#94a3b8; font-size:12px;">
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


# ===================
# TAB 7: Update
# ===================
with tab7:
    st.markdown("### Uygulama Güncelleme")
    st.markdown("""
    GitHub'daki son değişiklikleri çekip uygulamayı yeniden başlatır.
    """)

    import subprocess
    from pathlib import Path

    project_dir = str(Path(__file__).parent.parent)

    # --- Mevcut durum bilgisi ---
    try:
        # Mevcut branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_dir, capture_output=True, text=True, timeout=5,
        )
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "bilinmiyor"

        # Son commit
        git_log = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=project_dir, capture_output=True, text=True, timeout=5,
        )

        # Remote'da yeni commit var mı kontrol et
        subprocess.run(
            ["git", "fetch", "origin", current_branch],
            cwd=project_dir, capture_output=True, text=True, timeout=15,
        )
        behind_result = subprocess.run(
            ["git", "rev-list", "--count", f"HEAD..origin/{current_branch}"],
            cwd=project_dir, capture_output=True, text=True, timeout=5,
        )
        behind_count = int(behind_result.stdout.strip()) if behind_result.returncode == 0 else 0

        # Durum kartları
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number" style="font-size:16px;">🌿 {current_branch}</div>
                <div class="stat-label">Aktif Branch</div>
            </div>
            """, unsafe_allow_html=True)
        with col_s2:
            if behind_count > 0:
                st.markdown(f"""
                <div class="stat-box" style="border-color: rgba(251, 191, 36, 0.3);">
                    <div class="stat-number" style="font-size:22px; background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{behind_count}</div>
                    <div class="stat-label">Yeni Güncelleme</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-number" style="font-size:18px;">✅</div>
                    <div class="stat-label">Güncel</div>
                </div>
                """, unsafe_allow_html=True)
        with col_s3:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number" style="font-size:16px;">🖥️ NSSM</div>
                <div class="stat-label">Servis Yönetimi</div>
            </div>
            """, unsafe_allow_html=True)

        if git_log.returncode == 0:
            with st.expander("Son 5 Commit", expanded=False):
                st.code(git_log.stdout.strip(), language="text")

    except Exception:
        current_branch = "main"
        behind_count = 0

    st.markdown("---")

    # --- Güncelleme butonları ---
    col_up1, col_up2, col_up3 = st.columns(3)

    with col_up1:
        update_btn = st.button(
            "📥 Güncellemeleri Çek",
            type="primary" if behind_count > 0 else "secondary",
            use_container_width=True,
            help="GitHub'dan son değişiklikleri indirir (git pull)"
        )

    with col_up2:
        restart_btn = st.button(
            "🔄 Servisi Yeniden Başlat",
            use_container_width=True,
            help="NSSM ile Streamlit servisini restart eder"
        )

    with col_up3:
        update_restart_btn = st.button(
            "⚡ Güncelle + Restart",
            type="primary",
            use_container_width=True,
            help="Güncellemeleri çeker, bağımlılıkları kurar ve servisi yeniden başlatır"
        )

    # --- Helper: NSSM restart ---
    def _nssm_restart():
        """NSSM ile Streamlit servisini restart et."""
        try:
            subprocess.Popen(
                ["nssm", "restart", "Streamlit"],
                cwd=project_dir,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            return True
        except FileNotFoundError:
            try:
                subprocess.Popen(
                    [r"C:\nssm\nssm-2.24\win64\nssm.exe", "restart", "Streamlit"],
                )
                return True
            except Exception as e:
                st.error(f"NSSM bulunamadı: {e}")
                st.code("C:\\nssm\\nssm-2.24\\win64\\nssm.exe restart Streamlit", language="powershell")
                return False

    # --- Güncelleme işlemi ---
    if update_btn or update_restart_btn:
        with st.spinner("GitHub'dan güncelleniyor..."):
            try:
                # git pull with inline config (sunucuda git config olmasa bile çalışır)
                result = subprocess.run(
                    [
                        "git",
                        "-c", "user.email=dashboard@update",
                        "-c", "user.name=Dashboard",
                        "pull", "--ff-only", "origin", current_branch,
                    ],
                    cwd=project_dir,
                    capture_output=True, text=True, timeout=30,
                )

                if result.returncode == 0:
                    if "Already up to date" in result.stdout:
                        st.info("Zaten güncel! Değişiklik yok.")
                    else:
                        st.success("Güncelleme indirildi!")
                        st.code(result.stdout.strip(), language="text")

                        # Bağımlılıkları güncelle
                        with st.spinner("Bağımlılıklar kontrol ediliyor..."):
                            pip_result = subprocess.run(
                                ["pip", "install", "-r", "requirements.txt", "--quiet"],
                                cwd=project_dir,
                                capture_output=True, text=True, timeout=120,
                            )
                            if pip_result.returncode == 0:
                                st.success("Bağımlılıklar güncellendi!")
                            else:
                                st.warning(f"Bağımlılık uyarısı: {pip_result.stderr[:200]}")

                        if update_restart_btn:
                            st.info("Servis yeniden başlatılıyor...")
                            _nssm_restart()
                        else:
                            st.info("Değişikliklerin etkili olması için servisi yeniden başlatın.")
                else:
                    # ff-only başarısız → lokal değişiklik var, reset dene
                    if "Not possible to fast-forward" in result.stderr or "fatal" in result.stderr:
                        st.warning("Lokal değişiklik tespit edildi. Sıfırlanıp güncelleniyor...")
                        reset_result = subprocess.run(
                            ["git", "reset", "--hard", f"origin/{current_branch}"],
                            cwd=project_dir,
                            capture_output=True, text=True, timeout=15,
                        )
                        if reset_result.returncode == 0:
                            st.success("Güncelleme tamamlandı! (reset + pull)")
                            # Bağımlılıkları güncelle
                            subprocess.run(
                                ["pip", "install", "-r", "requirements.txt", "--quiet"],
                                cwd=project_dir,
                                capture_output=True, text=True, timeout=120,
                            )
                            if update_restart_btn:
                                st.info("Servis yeniden başlatılıyor...")
                                _nssm_restart()
                            else:
                                st.info("Servisi yeniden başlatın.")
                        else:
                            st.error(f"Reset hatası: {reset_result.stderr}")
                    else:
                        st.error(f"Git hatası: {result.stderr}")

            except subprocess.TimeoutExpired:
                st.error("Güncelleme zaman aşımına uğradı. İnternet bağlantınızı kontrol edin.")
            except Exception as e:
                st.error(f"Güncelleme hatası: {e}")

    # --- Sadece restart ---
    if restart_btn and not update_restart_btn:
        st.info("Servis yeniden başlatılıyor... Sayfa birkaç saniye içinde yeniden yüklenecek.")
        _nssm_restart()

    st.markdown("---")
    st.markdown(f"""
    **Bilgi:**
    - Güncellemeler `origin/{current_branch}` branch'ından çekilir
    - "Servisi Yeniden Başlat" NSSM ile Streamlit'i restart eder
    - Sayfa birkaç saniye içinde otomatik yeniden yüklenir
    """)
