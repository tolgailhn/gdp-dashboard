"""
Onayli Takipci Sayfasi
Benzer hesaplarin onayli (mavi tikli) takipcilerini cek ve goster.
Otomatik takip YOK - kullanici tiklasin ve manuel takip etsin.

Streamlit Cloud uyumlulugu:
- Veriler hem dosya sistemine hem session_state'e kaydedilir
- Export/Import ile veriler indirilebilir ve geri yuklenebilir
"""
import json
import datetime
import streamlit as st
from modules.ui_components import inject_custom_css, check_password, get_secret
from modules.twikit_client import TwikitSearchClient

# Page config
st.set_page_config(
    page_title="Takipciler | X AI Otomasyon",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_custom_css()

if not check_password():
    st.stop()


# --- Session-state aware persistence ---
def _save_followers(username: str, followers: list[dict]):
    """Save to both session_state and file."""
    data = {
        "username": username,
        "fetched_at": datetime.datetime.now().isoformat(),
        "followers": followers,
    }
    # Session state
    if "follower_suggestions" not in st.session_state:
        st.session_state["follower_suggestions"] = {}
    st.session_state["follower_suggestions"][username.lower()] = data

    # File
    try:
        from modules.style_manager import save_follower_suggestions
        save_follower_suggestions(username, followers)
    except Exception:
        pass


def _load_all_followers() -> dict:
    """Load from session_state first, then files."""
    result = {}

    # Files first
    try:
        from modules.style_manager import load_all_follower_suggestions
        result = load_all_follower_suggestions()
    except Exception:
        pass

    # Overlay with session_state
    ss = st.session_state.get("follower_suggestions", {})
    result.update(ss)

    # Sync back to session_state
    if result:
        st.session_state["follower_suggestions"] = result

    return result


def _delete_followers(username: str):
    """Delete from both session_state and file."""
    ss = st.session_state.get("follower_suggestions", {})
    if username.lower() in ss:
        del ss[username.lower()]
    try:
        from modules.style_manager import delete_follower_suggestions
        delete_follower_suggestions(username)
    except Exception:
        pass


def _export_followers_json() -> str:
    """Export all follower data as JSON."""
    data = _load_all_followers()
    return json.dumps({
        "type": "follower_suggestions_export",
        "exported_at": datetime.datetime.now().isoformat(),
        "suggestions": data,
    }, ensure_ascii=False, indent=2)


def _import_followers_json(json_str: str) -> int:
    """Import follower data from JSON. Returns count."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return 0

    suggestions = data.get("suggestions", {})
    if not suggestions:
        return 0

    if "follower_suggestions" not in st.session_state:
        st.session_state["follower_suggestions"] = {}

    count = 0
    for key, value in suggestions.items():
        st.session_state["follower_suggestions"][key] = value
        # Also save to file
        try:
            from modules.style_manager import save_follower_suggestions
            save_follower_suggestions(value.get("username", key), value.get("followers", []))
        except Exception:
            pass
        count += 1

    return count


# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>👥 Onayli Takipci Kesfet</h1>
    <p style="color:#8899a6;">Benzer hesaplarin mavi tikli takipcilerini bul, manuel takip et</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:#16213e; border:1px solid #1DA1F2; border-radius:12px;
            padding:16px; margin-bottom:16px;">
    <div style="color:#1DA1F2; font-weight:bold; font-size:16px;">Nasil Calisiyor?</div>
    <div style="color:#8899a6; font-size:13px; margin-top:4px;">
        1. Senin nisindeki bir hesabin kullanici adini gir<br>
        2. O hesabin onayli (mavi tikli) takipcilerini cekeriz<br>
        3. Listeden profillerine tikla ve manuel takip et<br>
        4. Geri takip ederlerse onayli takipci sayin artar<br>
        <br>
        <strong>⚠️ Otomatik takip YOK</strong> — ban riski yuzunden. Sen tikla, sen takip et.<br>
        <strong>💡 Streamlit Cloud:</strong> Sonuclari "Disa/Iceri Aktar" sekmesinden indirip saklayabilirsin.
    </div>
</div>
""", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["🔍 Takipci Cek", "📁 Kayitli Listeler", "💾 Disa/Iceri Aktar"])

# ===================
# TAB 1: Pull Followers
# ===================
with tab1:
    twikit_user = get_secret("twikit_username", "")
    twikit_pass = get_secret("twikit_password", "")
    twikit_email = get_secret("twikit_email", "")

    if not twikit_user or not twikit_pass:
        st.error("Twikit yapilandirilmamis! Ayarlar sayfasindan Twikit kullanici adi ve sifre ekleyin.")
        st.stop()

    st.markdown("### Hedef Hesap")
    st.markdown("Senin nisindeki bir hesap gir. O hesabin onayli takipcilerini cekecegiz.")

    target_username = st.text_input(
        "Twitter kullanici adi",
        placeholder="ornek: AnthropicAI veya sama (@ olmadan)",
        key="target_follower_username"
    )

    col1, col2 = st.columns(2)
    with col1:
        follower_limit = st.slider("Maks takipci sayisi", 50, 500, 200, step=50, key="follower_limit")
    with col2:
        verified_only = st.checkbox("Sadece onayli (mavi tikli)", value=True, key="verified_only")

    fetch_clicked = st.button(
        "👥 Takipci Cek",
        type="primary",
        use_container_width=True,
        disabled=not target_username.strip()
    )

    if fetch_clicked:
        username = target_username.strip().lstrip("@")

        with st.spinner("Twikit ile giris yapiliyor..."):
            twikit = TwikitSearchClient(twikit_user, twikit_pass, twikit_email)
            if not twikit.authenticate():
                st.error("Twikit giris basarisiz!")
                st.stop()

        progress = st.empty()
        progress.caption(f"@{username} bilgileri aliniyor...")

        user_info = twikit.get_user_info(username)
        if not user_info:
            st.error(f"@{username} bulunamadi. Kullanici adi dogru mu?")
            st.stop()

        st.markdown(f"""
        <div style="background:#1a1a2e; border:1px solid #1DA1F2; border-radius:12px;
                    padding:16px; margin:12px 0;">
            <div style="display:flex; align-items:center; gap:12px;">
                <div>
                    <span style="color:#f0f0f0; font-weight:bold; font-size:16px;">{user_info['name']}</span>
                    <span style="color:#1DA1F2; font-size:14px;"> @{user_info['username']}</span>
                    {"<span style='color:#1DA1F2;'> ✓</span>" if user_info.get('is_blue_verified') else ""}
                </div>
            </div>
            <div style="color:#8899a6; font-size:13px; margin-top:6px;">{user_info.get('bio', '')[:200]}</div>
            <div style="color:#8899a6; font-size:12px; margin-top:8px;">
                👥 {user_info.get('followers_count', 0):,} takipci |
                👤 {user_info.get('following_count', 0):,} takip |
                📝 {user_info.get('tweet_count', 0):,} tweet
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner(f"@{username} takipcileri cekiliyor... Bu biraz zaman alabilir."):
            followers = twikit.get_user_followers(
                username, limit=follower_limit,
                verified_only=verified_only,
                progress_callback=lambda msg: progress.caption(msg)
            )

        progress.empty()

        if not followers:
            if verified_only:
                st.warning(f"@{username} hesabinda onayli takipci bulunamadi. "
                          f"'Sadece onayli' secenegini kapatip tekrar deneyin.")
            else:
                st.warning(f"@{username} takipcileri cekilemedi.")
        else:
            _save_followers(username, followers)
            st.success(f"{len(followers)} {'onayli ' if verified_only else ''}takipci bulundu ve kaydedildi!")
            _display_followers(followers, username)


# ===================
# TAB 2: Saved Lists
# ===================
with tab2:
    st.markdown("### Kayitli Takipci Listeleri")

    all_suggestions = _load_all_followers()

    if not all_suggestions:
        st.info("Henuz kayitli takipci listesi yok. 'Takipci Cek' sekmesinden baslayin "
                "veya 'Disa/Iceri Aktar' sekmesinden onceki dosyanizi yukleyin.")
    else:
        for key, data in all_suggestions.items():
            username = data.get("username", key)
            fetched_at = data.get("fetched_at", "?")[:16]
            followers = data.get("followers", [])

            with st.expander(f"@{username} — {len(followers)} takipci ({fetched_at})"):
                _display_followers(followers, username)

                if st.button(f"🗑️ @{username} Listesini Sil", key=f"del_followers_{username}"):
                    _delete_followers(username)
                    st.success(f"@{username} listesi silindi!")
                    st.rerun()


# ===================
# TAB 3: Export / Import
# ===================
with tab3:
    st.markdown("### Disa / Iceri Aktar")

    st.markdown("""
    <div style="background:#16213e; border:1px solid #1DA1F2; border-radius:12px;
                padding:16px; margin-bottom:16px;">
        <div style="color:#1DA1F2; font-weight:bold; font-size:16px;">Neden Gerekli?</div>
        <div style="color:#8899a6; font-size:13px; margin-top:4px;">
            Streamlit Cloud'da dosya sistemi gecicidir.<br>
            Takipci listelerinizi indirin ve bir sonraki oturumda geri yukleyin.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_exp, col_imp = st.columns(2)

    with col_exp:
        st.markdown("#### 📤 Disa Aktar")

        current = _load_all_followers()
        if current:
            usernames = list(current.keys())
            total = sum(len(d.get("followers", [])) for d in current.values())
            st.info(f"{len(current)} liste, toplam {total} takipci")

            export_json = _export_followers_json()
            st.download_button(
                label="📥 Tumunu Indir (JSON)",
                data=export_json,
                file_name="follower_suggestions_export.json",
                mime="application/json",
                use_container_width=True,
                type="primary"
            )
        else:
            st.warning("Indirilecek liste yok.")

    with col_imp:
        st.markdown("#### 📥 Iceri Aktar")

        uploaded_file = st.file_uploader(
            "Onceki takipci dosyasini yukleyin",
            type=["json"],
            key="import_followers_file"
        )

        if uploaded_file:
            try:
                json_str = uploaded_file.read().decode("utf-8")
                preview = json.loads(json_str)
                suggestions = preview.get("suggestions", {})

                if suggestions:
                    total = sum(len(d.get("followers", [])) for d in suggestions.values())
                    st.info(f"Dosyada {len(suggestions)} liste, toplam {total} takipci")

                    if st.button("✅ Iceri Aktar", type="primary", use_container_width=True,
                                 key="import_followers_btn"):
                        count = _import_followers_json(json_str)
                        st.success(f"{count} liste yuklendi!")
                        st.rerun()
                else:
                    st.error("Gecersiz dosya formati.")
            except Exception as e:
                st.error(f"Dosya okuma hatasi: {e}")


def _display_followers(followers: list[dict], source_username: str):
    """Display follower list with profile links for manual follow."""

    verified_count = sum(1 for f in followers if f.get("is_blue_verified"))
    total_followers_of_followers = sum(f.get("followers_count", 0) for f in followers)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Toplam", len(followers))
    with col2:
        st.metric("Onayli", verified_count)
    with col3:
        avg_followers = total_followers_of_followers // max(len(followers), 1)
        st.metric("Ort. Takipci", f"{avg_followers:,}")

    sort_by = st.selectbox(
        "Sirala",
        options=["followers_count", "name"],
        format_func=lambda x: {"followers_count": "Takipci sayisina gore", "name": "Isme gore"}[x],
        key=f"sort_{source_username}"
    )

    sorted_followers = sorted(followers, key=lambda f: f.get(sort_by, 0),
                              reverse=(sort_by == "followers_count"))

    for i, f in enumerate(sorted_followers):
        name = f.get("name", "?")
        uname = f.get("username", "?")
        bio = f.get("bio", "")[:120]
        f_count = f.get("followers_count", 0)
        is_verified = f.get("is_blue_verified", False)
        profile_url = f"https://x.com/{uname}"

        verified_badge = ' <span style="color:#1DA1F2;">✓</span>' if is_verified else ""

        st.markdown(f"""
        <div style="background:#1a1a2e; border:1px solid #2a2a4a; border-radius:8px;
                    padding:10px 14px; margin:4px 0; display:flex; justify-content:space-between; align-items:center;">
            <div style="flex:1;">
                <div>
                    <span style="color:#f0f0f0; font-weight:bold; font-size:14px;">{name}</span>{verified_badge}
                    <span style="color:#8899a6; font-size:13px;"> @{uname}</span>
                </div>
                <div style="color:#8899a6; font-size:12px; margin-top:2px;">{bio}</div>
                <div style="color:#8899a6; font-size:11px; margin-top:2px;">👥 {f_count:,} takipci</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.link_button(
            f"@{uname} Profilini Ac",
            profile_url,
            use_container_width=False,
            key=f"follow_{source_username}_{i}_{uname}"
        )
