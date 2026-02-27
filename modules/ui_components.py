"""
Shared UI Components Module
Reusable Streamlit components for the X AI Automation Dashboard
"""
import streamlit as st


def setup_page_config(title: str = "X AI Otomasyon", icon: str = "🤖"):
    """Configure page with mobile-friendly settings"""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def inject_custom_css():
    """Inject mobile-friendly custom CSS"""
    st.markdown("""
    <style>
    /* Mobile-friendly base styles */
    .stApp {
        max-width: 100%;
    }

    /* Better mobile sidebar */
    @media (max-width: 768px) {
        .css-1d391kg { padding: 1rem 0.5rem; }
        .stButton > button { width: 100%; margin-bottom: 0.5rem; }
        section[data-testid="stSidebar"] { width: 280px !important; }
        .block-container { padding: 1rem 0.5rem !important; }
    }

    /* Tweet card styles */
    .tweet-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2a2a4a;
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        color: #e0e0e0;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .tweet-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    .tweet-author {
        font-weight: bold;
        color: #1DA1F2;
        font-size: 15px;
    }
    .tweet-username {
        color: #8899a6;
        font-size: 13px;
    }
    .tweet-text {
        margin: 12px 0;
        line-height: 1.5;
        font-size: 15px;
        color: #f0f0f0;
    }
    .tweet-metrics {
        display: flex;
        gap: 20px;
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
        background: #1DA1F2;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }

    /* Relevance score badge */
    .relevance-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: bold;
    }
    .relevance-high { background: #00c853; color: white; }
    .relevance-medium { background: #ff9800; color: white; }
    .relevance-low { background: #757575; color: white; }

    /* Generated tweet preview */
    .generated-tweet {
        background: linear-gradient(135deg, #0f1923 0%, #1a2836 100%);
        border: 2px solid #1DA1F2;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        color: #ffffff;
        font-size: 16px;
        line-height: 1.6;
        white-space: pre-wrap;
    }

    /* Style selector cards */
    .style-card {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        padding: 15px;
        margin: 8px 0;
        cursor: pointer;
        transition: border-color 0.2s;
    }
    .style-card:hover {
        border-color: #1DA1F2;
    }
    .style-card.active {
        border-color: #1DA1F2;
        background: #16213e;
    }

    /* Stats boxes */
    .stat-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .stat-number {
        font-size: 28px;
        font-weight: bold;
        color: #1DA1F2;
    }
    .stat-label {
        font-size: 12px;
        color: #8899a6;
        margin-top: 4px;
    }

    /* Header styling */
    .main-header {
        text-align: center;
        padding: 10px 0 20px 0;
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 28px;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
    }

    /* Divider */
    .custom-divider {
        border-top: 1px solid #2a2a4a;
        margin: 20px 0;
    }

    /* Thread tweet */
    .thread-tweet {
        background: #0f1923;
        border-left: 3px solid #1DA1F2;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
        color: #f0f0f0;
        font-size: 14px;
        line-height: 1.5;
    }
    .thread-number {
        color: #1DA1F2;
        font-weight: bold;
        font-size: 13px;
        margin-bottom: 4px;
    }

    /* Dark mode for inputs */
    .stTextArea textarea {
        background-color: #1a1a2e !important;
        color: #f0f0f0 !important;
        border-color: #2a2a4a !important;
    }
    .stTextInput input {
        background-color: #1a1a2e !important;
        color: #f0f0f0 !important;
        border-color: #2a2a4a !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


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

    st.markdown(f"""
    <div class="tweet-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span class="tweet-author">{topic.author_name}</span>
                <span class="tweet-username">@{topic.author_username}</span>
            </div>
            <div>
                <span class="tweet-category">{topic.category}</span>
                <span class="relevance-badge {rel_class}">{rel_text}</span>
            </div>
        </div>
        <div class="tweet-text">{topic.text}</div>
        <div class="tweet-metrics">
            <span>❤️ {topic.like_count:,}</span>
            <span>🔁 {topic.retweet_count:,}</span>
            <span>💬 {topic.reply_count:,}</span>
            <span class="tweet-time">{topic.time_ago}</span>
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
        correct_password = st.secrets.get("app_password", "admin123")
        if password == correct_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Yanlış şifre!")

    return False
