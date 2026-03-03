"""
Shared UI Components Module
Reusable Streamlit components for the X AI Automation Dashboard
"""
import streamlit as st


def get_secret(key: str, default: str = "") -> str:
    """Safely get a secret value - works both locally and on Streamlit Cloud"""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def setup_page_config(title: str = "X AI Otomasyon", icon: str = "🤖"):
    """Configure page with mobile-friendly settings"""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="auto",
    )


def inject_custom_css():
    """Inject mobile-first modern CSS"""
    st.markdown("""
    <style>
    /* ========================================
       MOBILE-FIRST MODERN DESIGN SYSTEM
       ======================================== */

    /* --- Base & Reset --- */
    .stApp {
        max-width: 100%;
        overflow-x: hidden;
    }
    .block-container {
        padding: 0.75rem 1rem 5rem 1rem !important;
        max-width: 100% !important;
    }

    /* --- Hide Streamlit chrome --- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: rgba(14, 17, 23, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }

    /* --- Typography --- */
    h1, h2, h3 { letter-spacing: -0.02em; }

    /* --- Glass Card Base --- */
    .glass-card {
        background: rgba(26, 26, 46, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    }

    /* --- Tweet Cards --- */
    .tweet-card {
        background: rgba(26, 26, 46, 0.55);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
        color: #e0e0e0;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .tweet-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(29, 161, 242, 0.08);
        border-color: rgba(29, 161, 242, 0.2);
    }
    .tweet-author {
        font-weight: 700;
        color: #1DA1F2;
        font-size: 15px;
    }
    .tweet-username {
        color: #8899a6;
        font-size: 13px;
    }
    .tweet-text {
        margin: 10px 0;
        line-height: 1.55;
        font-size: 15px;
        color: #f0f0f0;
        word-break: break-word;
    }
    .tweet-metrics {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        color: #8899a6;
        font-size: 13px;
        margin-top: 10px;
    }
    .tweet-time {
        color: #8899a6;
        font-size: 12px;
    }
    .tweet-category {
        display: inline-block;
        background: linear-gradient(135deg, #1DA1F2, #0d8bd9);
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }

    /* Relevance badges */
    .relevance-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }
    .relevance-high { background: rgba(0, 200, 83, 0.2); color: #00e676; border: 1px solid rgba(0, 200, 83, 0.3); }
    .relevance-medium { background: rgba(255, 152, 0, 0.2); color: #ffb74d; border: 1px solid rgba(255, 152, 0, 0.3); }
    .relevance-low { background: rgba(117, 117, 117, 0.2); color: #bdbdbd; border: 1px solid rgba(117, 117, 117, 0.3); }

    /* --- Generated Tweet Preview --- */
    .generated-tweet {
        background: linear-gradient(135deg, rgba(15, 25, 35, 0.8) 0%, rgba(26, 40, 54, 0.8) 100%);
        border: 1px solid rgba(29, 161, 242, 0.3);
        border-left: 3px solid #1DA1F2;
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        color: #ffffff;
        font-size: 15px;
        line-height: 1.65;
        white-space: pre-wrap;
        word-break: break-word;
    }

    /* --- Style Cards --- */
    .style-card {
        background: rgba(26, 26, 46, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 14px;
        margin: 6px 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .style-card:hover {
        border-color: rgba(29, 161, 242, 0.4);
        background: rgba(22, 33, 62, 0.6);
    }
    .style-card.active {
        border-color: #1DA1F2;
        background: rgba(29, 161, 242, 0.1);
    }

    /* --- Stat Boxes --- */
    .stat-box {
        background: rgba(26, 26, 46, 0.55);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 16px 12px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .stat-box:hover {
        transform: translateY(-1px);
        border-color: rgba(29, 161, 242, 0.2);
    }
    .stat-number {
        font-size: 26px;
        font-weight: 700;
        color: #1DA1F2;
        line-height: 1.2;
    }
    .stat-label {
        font-size: 12px;
        color: #8899a6;
        margin-top: 4px;
    }

    /* --- Action Cards (Home Page) --- */
    .action-card {
        background: rgba(26, 26, 46, 0.55);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 20px 16px;
        text-align: center;
        transition: all 0.2s ease;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .action-card:hover {
        transform: translateY(-2px);
        border-color: rgba(29, 161, 242, 0.25);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }
    .action-icon { font-size: 32px; margin-bottom: 8px; }
    .action-title { color: #f0f0f0; font-weight: 700; font-size: 15px; }
    .action-desc { color: #8899a6; font-size: 12px; margin-top: 4px; }

    /* --- Header --- */
    .main-header {
        text-align: center;
        padding: 8px 0 16px 0;
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 2px;
    }

    /* --- Buttons --- */
    .stButton > button {
        border-radius: 12px !important;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        font-size: 14px;
        min-height: 44px;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(29, 161, 242, 0.2);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1DA1F2, #0d8bd9) !important;
        border: none;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #3db5f5, #1DA1F2) !important;
    }

    /* --- Divider --- */
    .custom-divider {
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        margin: 16px 0;
    }

    /* --- Thread Tweet --- */
    .thread-tweet {
        background: rgba(15, 25, 35, 0.6);
        border-left: 3px solid #1DA1F2;
        padding: 12px 16px;
        margin: 6px 0;
        border-radius: 0 12px 12px 0;
        color: #f0f0f0;
        font-size: 14px;
        line-height: 1.55;
    }
    .thread-number {
        color: #1DA1F2;
        font-weight: 700;
        font-size: 12px;
        margin-bottom: 4px;
    }

    /* --- Inputs --- */
    .stTextArea textarea,
    .stTextInput input {
        background-color: rgba(26, 26, 46, 0.6) !important;
        color: #f0f0f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        font-size: 16px !important;
        padding: 12px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: rgba(29, 161, 242, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(29, 161, 242, 0.1) !important;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: 12px !important;
        min-height: 44px;
    }

    /* Checkbox */
    .stCheckbox label {
        min-height: 44px;
        display: flex;
        align-items: center;
    }

    /* --- Tabs --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: rgba(26, 26, 46, 0.4);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 16px;
        font-size: 14px;
        font-weight: 600;
        color: #8899a6;
        min-height: 44px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(29, 161, 242, 0.15) !important;
        color: #1DA1F2 !important;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }

    /* --- Expander --- */
    .streamlit-expanderHeader {
        font-size: 15px;
        font-weight: 600;
        border-radius: 12px;
    }

    /* --- Sidebar --- */
    section[data-testid="stSidebar"] {
        background: rgba(14, 17, 23, 0.95);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
    }
    section[data-testid="stSidebar"] .stButton > button {
        border-radius: 10px !important;
        font-size: 14px;
        text-align: left;
    }

    /* --- Nav Links --- */
    .nav-link {
        display: block;
        padding: 10px 14px;
        margin: 3px 0;
        border-radius: 10px;
        color: #f0f0f0 !important;
        text-decoration: none !important;
        transition: background 0.2s ease;
        font-size: 14px;
    }
    .nav-link:hover { background: rgba(29, 161, 242, 0.1); }
    .nav-link.active { background: #1DA1F2; color: white !important; }

    /* ==========================================
       MOBILE BOTTOM NAV
       ========================================== */
    .mobile-bottom-nav {
        display: none;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 9999;
        background: rgba(14, 17, 23, 0.92);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        padding: 6px 0 max(6px, env(safe-area-inset-bottom));
    }
    .mobile-bottom-nav .nav-items {
        display: flex;
        justify-content: space-around;
        align-items: center;
        max-width: 500px;
        margin: 0 auto;
    }
    .mobile-bottom-nav a {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-decoration: none;
        color: #8899a6;
        font-size: 10px;
        font-weight: 500;
        padding: 4px 8px;
        border-radius: 10px;
        transition: all 0.2s ease;
        min-width: 48px;
        min-height: 48px;
        justify-content: center;
    }
    .mobile-bottom-nav a .nav-icon { font-size: 20px; margin-bottom: 2px; }
    .mobile-bottom-nav a.active {
        color: #1DA1F2;
        background: rgba(29, 161, 242, 0.12);
    }
    .mobile-bottom-nav a:hover { color: #1DA1F2; }

    /* ==========================================
       RESPONSIVE BREAKPOINTS
       ========================================== */

    /* Tablet and up */
    @media (min-width: 640px) {
        .block-container {
            padding: 1rem 2rem 2rem 2rem !important;
        }
        .main-header h1 { font-size: 28px; }
        .stat-number { font-size: 28px; }
    }

    /* Desktop */
    @media (min-width: 1024px) {
        .block-container {
            padding: 1rem 3rem 2rem 3rem !important;
        }
        .main-header h1 { font-size: 32px; }
    }

    /* Mobile only */
    @media (max-width: 639px) {
        /* Show bottom nav */
        .mobile-bottom-nav { display: block; }

        /* Hide sidebar completely on mobile */
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        /* Remove sidebar toggle button */
        button[data-testid="stSidebarCollapsedControl"],
        button[kind="header"] {
            display: none !important;
        }

        /* Content padding with bottom nav space */
        .block-container {
            padding: 0.5rem 0.75rem 80px 0.75rem !important;
        }

        /* Full width buttons */
        .stButton > button {
            width: 100%;
            margin-bottom: 4px;
        }

        /* Smaller header on mobile */
        .main-header { padding: 4px 0 12px 0; }
        .main-header h1 { font-size: 22px; }

        /* Stack columns better */
        [data-testid="column"] {
            padding: 0 2px !important;
        }

        /* Tab text */
        .stTabs [data-baseweb="tab"] {
            font-size: 12px;
            padding: 8px 10px;
        }

        /* Stat boxes compact */
        .stat-box { padding: 12px 8px; }
        .stat-number { font-size: 22px; }
        .stat-label { font-size: 11px; }

        /* Action cards compact */
        .action-card {
            padding: 14px 10px;
            min-height: 90px;
        }
        .action-icon { font-size: 26px; margin-bottom: 4px; }
        .action-title { font-size: 13px; }
        .action-desc { font-size: 11px; }

        /* Tweet card compact */
        .tweet-card { padding: 14px; margin: 6px 0; }
        .tweet-metrics { gap: 10px; font-size: 12px; }

        /* Generated tweet */
        .generated-tweet { padding: 16px; font-size: 14px; }
    }

    /* Small phones */
    @media (max-width: 380px) {
        .block-container { padding: 0.5rem 0.5rem 80px 0.5rem !important; }
        .main-header h1 { font-size: 20px; }
        .stTabs [data-baseweb="tab"] { font-size: 11px; padding: 8px 6px; }
    }

    /* --- Scrollbar --- */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }

    /* --- Alerts/Info boxes --- */
    .stAlert {
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar_nav(current_page: str = ""):
    """Render sidebar nav (desktop) + bottom nav (mobile)."""
    # --- Desktop sidebar ---
    with st.sidebar:
        st.markdown("### 🤖 X AI Otomasyon")
        st.markdown("---")

        pages = [
            ("🏠 Ana Sayfa", "streamlit_app.py", "home"),
            ("🔍 Tara", "pages/1_🔍_Tara.py", "tara"),
            ("✍️ Yaz", "pages/2_✍️_Yaz.py", "yaz"),
            ("💡 İçerik", "pages/6_💡_İçerik.py", "icerik"),
            ("📊 Analiz", "pages/4_📊_Analiz.py", "analiz"),
            ("👥 Takipçiler", "pages/5_👥_Takipçiler.py", "takipci"),
            ("⚙️ Ayarlar", "pages/3_⚙️_Ayarlar.py", "ayarlar"),
        ]

        for label, path, key in pages:
            page_type = "primary" if key == current_page else "secondary"
            if st.button(label, key=f"nav_{key}", use_container_width=True,
                         type=page_type):
                st.switch_page(path)

        st.markdown("---")

        # API status
        has_twitter = bool(get_secret("twitter_bearer_token", ""))
        has_ai = bool(get_secret("minimax_api_key", "") or
                      get_secret("anthropic_api_key", "") or
                      get_secret("openai_api_key", ""))

        if has_twitter:
            st.success("Twitter API ✓", icon="🐦")
        else:
            st.warning("Twitter API eksik", icon="⚠️")

        if has_ai:
            st.success("AI API ✓", icon="🧠")
        else:
            st.warning("AI API eksik", icon="⚠️")

    # --- Mobile bottom nav ---
    mobile_nav_items = [
        ("🏠", "Ana", "streamlit_app.py", "home"),
        ("🔍", "Tara", "pages/1_🔍_Tara.py", "tara"),
        ("✍️", "Yaz", "pages/2_✍️_Yaz.py", "yaz"),
        ("💡", "İçerik", "pages/6_💡_İçerik.py", "icerik"),
        ("📊", "Analiz", "pages/4_📊_Analiz.py", "analiz"),
        ("⚙️", "Ayar", "pages/3_⚙️_Ayarlar.py", "ayarlar"),
    ]

    nav_links = ""
    for icon, label, path, key in mobile_nav_items:
        active = "active" if key == current_page else ""
        nav_links += f'<a href="/{path}" class="{active}" target="_self"><span class="nav-icon">{icon}</span>{label}</a>\n'

    st.markdown(f"""
    <div class="mobile-bottom-nav">
        <div class="nav-items">
            {nav_links}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _format_number(n: int) -> str:
    """Format large numbers with K/M suffix"""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def render_tweet_card(topic, show_select: bool = True, key_prefix: str = ""):
    """Render a tweet as a styled card"""
    # Relevance badge
    if topic.relevance_score >= 60:
        rel_class = "relevance-high"
        rel_text = "Yüksek"
    elif topic.relevance_score >= 30:
        rel_class = "relevance-medium"
        rel_text = "Orta"
    else:
        rel_class = "relevance-low"
        rel_text = "Düşük"

    # Content summary (Turkish description of what the tweet is about)
    content_summary = getattr(topic, 'content_summary', '') or ''
    summary_html = ""
    if content_summary:
        summary_html = f"""
        <div style="background:#0d2137; border-left:3px solid #1DA1F2; padding:6px 10px;
                    margin:8px 0; border-radius:0 6px 6px 0;">
            <span style="color:#1DA1F2; font-size:11px; font-weight:600;">📋 İçerik:</span>
            <span style="color:#b0c4de; font-size:12px; margin-left:4px;">{content_summary}</span>
        </div>"""

    # Follower count display
    followers = getattr(topic, 'author_followers_count', 0) or 0
    followers_html = ""
    if followers > 0:
        followers_html = f'<span style="color:#8899a6; font-size:11px; margin-left:6px;">· 👥 {_format_number(followers)}</span>'

    # Total engagement
    total_eng = topic.like_count + topic.retweet_count + topic.reply_count
    total_eng_html = f'<span style="color:#e8a838; font-size:12px; font-weight:600;">📊 {_format_number(total_eng)} etkileşim</span>'

    # Time and date
    time_and_date = getattr(topic, 'time_and_date', '') or topic.time_ago

    st.markdown(f"""
    <div class="tweet-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span class="tweet-author">{topic.author_name}</span>
                <span class="tweet-username">@{topic.author_username}</span>
                {followers_html}
            </div>
            <div>
                <span class="tweet-category">{topic.category}</span>
                <span class="relevance-badge {rel_class}">{rel_text}</span>
            </div>
        </div>
        {summary_html}
        <div class="tweet-text">{topic.text}</div>
        <div class="tweet-metrics">
            <span>❤️ {topic.like_count:,}</span>
            <span>🔁 {topic.retweet_count:,}</span>
            <span>💬 {topic.reply_count:,}</span>
            <span style="margin-left:4px;">{total_eng_html}</span>
            <span class="tweet-time">{time_and_date}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_generated_tweet(text: str):
    """Render a generated tweet preview"""
    char_count = len(text)
    st.markdown(f"""
    <div class="generated-tweet">
        {text}
    </div>
    <div style="text-align:right; color:#8899a6; font-size:13px;">
        {char_count} karakter
    </div>
    """, unsafe_allow_html=True)


def render_thread_preview(tweets: list[str]):
    """Render a thread preview"""
    for i, tweet in enumerate(tweets):
        st.markdown(f"""
        <div class="thread-tweet">
            <div class="thread-number">{i+1}/{len(tweets)}</div>
            {tweet}
        </div>
        """, unsafe_allow_html=True)


def render_stat_box(number: str, label: str):
    """Render a stat box"""
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{number}</div>
        <div class="stat-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def check_password() -> bool:
    """Simple password protection for the app"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("""
    <div class="main-header">
        <h1>🤖 X AI Otomasyon</h1>
        <p style="color:#8899a6;">Twitter/X AI İçerik Otomasyon Paneli</p>
    </div>
    """, unsafe_allow_html=True)

    password = st.text_input("Şifre", type="password", key="login_password")

    if st.button("Giriş Yap", type="primary", use_container_width=True):
        correct_password = get_secret("app_password", "admin123")
        if password == correct_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Yanlış şifre!")

    return False
