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
    """Inject premium mobile-first CSS design system"""
    st.markdown("""
    <style>
    /* ========================================
       PREMIUM DESIGN SYSTEM v3.0
       ======================================== */

    /* --- CSS Variables --- */
    :root {
        --bg-primary: #0a0e1a;
        --bg-card: rgba(15, 20, 35, 0.7);
        --bg-card-hover: rgba(20, 28, 50, 0.8);
        --border-subtle: rgba(255, 255, 255, 0.06);
        --border-glow: rgba(99, 102, 241, 0.3);
        --accent-blue: #6366f1;
        --accent-cyan: #22d3ee;
        --accent-purple: #a855f7;
        --accent-twitter: #1DA1F2;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --gradient-main: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7);
        --gradient-card: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.05));
        --gradient-accent: linear-gradient(135deg, #6366f1, #22d3ee);
        --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.25);
        --shadow-glow: 0 0 30px rgba(99, 102, 241, 0.15);
        --radius-sm: 10px;
        --radius-md: 14px;
        --radius-lg: 20px;
        --radius-xl: 24px;
    }

    /* --- Base & Reset --- */
    .stApp {
        max-width: 100%;
        overflow-x: hidden;
        background: var(--bg-primary) !important;
    }
    .block-container {
        padding: 0.75rem 1rem 5rem 1rem !important;
        max-width: 100% !important;
    }

    /* --- Hide Streamlit chrome --- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: rgba(10, 14, 26, 0.9) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid var(--border-subtle);
    }

    /* --- Typography --- */
    h1, h2, h3 {
        letter-spacing: -0.03em;
        font-weight: 700;
    }
    h1 { color: var(--text-primary) !important; }
    h2 { color: var(--text-primary) !important; }
    h3 { color: var(--text-primary) !important; font-size: 18px !important; }

    /* ==========================================
       PREMIUM CARDS
       ========================================== */

    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 20px;
        margin: 8px 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.4), transparent);
    }
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-glow);
        border-color: var(--border-glow);
    }

    /* --- Tweet Cards --- */
    .tweet-card {
        background: var(--bg-card);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 18px;
        margin: 10px 0;
        color: var(--text-primary);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .tweet-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 3px; height: 100%;
        background: var(--gradient-main);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    .tweet-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.12);
        border-color: rgba(99, 102, 241, 0.2);
    }
    .tweet-card:hover::before {
        opacity: 1;
    }
    .tweet-author {
        font-weight: 700;
        color: var(--accent-twitter);
        font-size: 15px;
    }
    .tweet-username {
        color: var(--text-secondary);
        font-size: 13px;
    }
    .tweet-text {
        margin: 10px 0;
        line-height: 1.6;
        font-size: 15px;
        color: var(--text-primary);
        word-break: break-word;
    }
    .tweet-metrics {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        color: var(--text-secondary);
        font-size: 13px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--border-subtle);
    }
    .tweet-time {
        color: var(--text-muted);
        font-size: 12px;
    }
    .tweet-category {
        display: inline-block;
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
        color: white;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    /* Relevance badges */
    .relevance-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }
    .relevance-high {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.25);
    }
    .relevance-medium {
        background: rgba(251, 191, 36, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.25);
    }
    .relevance-low {
        background: rgba(148, 163, 184, 0.15);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.2);
    }

    /* --- Generated Tweet Preview --- */
    .generated-tweet {
        background: linear-gradient(135deg, rgba(10, 20, 40, 0.9), rgba(20, 30, 55, 0.9));
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-left: 3px solid var(--accent-blue);
        border-radius: var(--radius-lg);
        padding: 22px;
        margin: 14px 0;
        color: #ffffff;
        font-size: 15px;
        line-height: 1.7;
        white-space: pre-wrap;
        word-break: break-word;
        position: relative;
        overflow: hidden;
    }
    .generated-tweet::before {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 120px; height: 120px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.08) 0%, transparent 70%);
    }

    /* --- Style Cards --- */
    .style-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 14px;
        margin: 6px 0;
        cursor: pointer;
        transition: all 0.25s ease;
    }
    .style-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        background: rgba(99, 102, 241, 0.06);
    }
    .style-card.active {
        border-color: var(--accent-blue);
        background: rgba(99, 102, 241, 0.1);
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.1);
    }

    /* ==========================================
       STAT BOXES - Premium gradient style
       ========================================== */
    .stat-box {
        background: var(--bg-card);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 18px 14px;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .stat-box::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: var(--gradient-accent);
        opacity: 0.6;
    }
    .stat-box:hover {
        transform: translateY(-2px);
        border-color: var(--border-glow);
        box-shadow: var(--shadow-glow);
    }
    .stat-number {
        font-size: 28px;
        font-weight: 800;
        background: var(--gradient-accent);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.2;
    }
    .stat-label {
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 4px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ==========================================
       ACTION CARDS - Premium home page
       ========================================== */
    .action-card {
        background: var(--bg-card);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 24px 16px 16px;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        min-height: 130px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        overflow: hidden;
    }
    .action-card::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle at center, rgba(99, 102, 241, 0.06) 0%, transparent 50%);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    .action-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15);
    }
    .action-card:hover::before { opacity: 1; }
    .action-icon {
        font-size: 36px;
        margin-bottom: 10px;
        filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
    }
    .action-title {
        color: var(--text-primary);
        font-weight: 700;
        font-size: 15px;
        letter-spacing: -0.01em;
    }
    .action-desc {
        color: var(--text-secondary);
        font-size: 12px;
        margin-top: 4px;
        line-height: 1.4;
    }

    /* ==========================================
       HEADER - Premium gradient
       ========================================== */
    .main-header {
        text-align: center;
        padding: 12px 0 20px 0;
        position: relative;
    }
    .main-header h1 {
        color: var(--text-primary) !important;
        font-size: 26px;
        font-weight: 800;
        margin-bottom: 4px;
        letter-spacing: -0.03em;
    }
    .main-header p {
        color: var(--text-secondary);
        font-size: 14px;
    }

    /* --- Page Header with icon accent --- */
    .page-header {
        text-align: center;
        padding: 16px 0 24px 0;
    }
    .page-header .page-icon {
        font-size: 48px;
        display: block;
        margin-bottom: 8px;
        filter: drop-shadow(0 4px 12px rgba(99, 102, 241, 0.3));
    }
    .page-header h1 {
        font-size: 24px;
        font-weight: 800;
        background: var(--gradient-main);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 !important;
    }
    .page-header p {
        color: var(--text-secondary);
        font-size: 13px;
        margin-top: 4px;
    }

    /* ==========================================
       HERO SECTION - Home page
       ========================================== */
    .hero-section {
        position: relative;
        text-align: center;
        padding: 28px 16px 24px;
        margin: -8px -8px 20px -8px;
        border-radius: 0 0 var(--radius-xl) var(--radius-xl);
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(168, 85, 247, 0.08) 50%, rgba(34, 211, 238, 0.06) 100%);
        border-bottom: 1px solid rgba(99, 102, 241, 0.15);
        overflow: hidden;
    }
    .hero-section::before {
        content: '';
        position: absolute;
        top: -40%; right: -20%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, transparent 70%);
        animation: pulse-glow 4s ease-in-out infinite;
    }
    .hero-section::after {
        content: '';
        position: absolute;
        bottom: -30%; left: -10%;
        width: 250px; height: 250px;
        background: radial-gradient(circle, rgba(168, 85, 247, 0.08) 0%, transparent 70%);
        animation: pulse-glow 4s ease-in-out infinite 2s;
    }
    @keyframes pulse-glow {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 1; }
    }
    .hero-logo {
        font-size: 52px;
        display: block;
        margin-bottom: 8px;
        filter: drop-shadow(0 4px 16px rgba(99, 102, 241, 0.4));
        position: relative;
        z-index: 1;
    }
    .hero-title {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin: 0;
        position: relative;
        z-index: 1;
        background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-subtitle {
        color: var(--text-secondary);
        font-size: 14px;
        margin-top: 6px;
        position: relative;
        z-index: 1;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        font-weight: 500;
    }

    /* ==========================================
       ACTIVITY TIMELINE
       ========================================== */
    .activity-item {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 14px 16px;
        margin: 6px 0;
        transition: all 0.25s ease;
        position: relative;
        display: flex;
        gap: 12px;
        align-items: flex-start;
    }
    .activity-item:hover {
        border-color: rgba(99, 102, 241, 0.2);
        background: var(--bg-card-hover);
    }
    .activity-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--gradient-accent);
        margin-top: 6px;
        flex-shrink: 0;
        box-shadow: 0 0 8px rgba(99, 102, 241, 0.4);
    }
    .activity-content {
        flex: 1;
        min-width: 0;
    }
    .activity-text {
        color: var(--text-primary);
        font-size: 14px;
        line-height: 1.5;
        word-break: break-word;
    }
    .activity-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 6px;
    }
    .activity-time {
        color: var(--text-muted);
        font-size: 12px;
    }
    .activity-link {
        color: var(--accent-blue) !important;
        font-size: 12px;
        text-decoration: none !important;
        font-weight: 600;
        transition: color 0.2s ease;
    }
    .activity-link:hover { color: var(--accent-cyan) !important; }

    /* ==========================================
       SECTION HEADERS
       ========================================== */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 20px 0 12px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border-subtle);
    }
    .section-header h3 {
        margin: 0 !important;
        padding: 0;
        font-size: 16px !important;
        font-weight: 700;
        color: var(--text-primary) !important;
    }
    .section-badge {
        background: rgba(99, 102, 241, 0.12);
        color: var(--accent-blue);
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    /* ==========================================
       BUTTONS - Premium style
       ========================================== */
    .stButton > button {
        border-radius: var(--radius-sm) !important;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        font-size: 14px;
        min-height: 44px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid var(--border-subtle) !important;
        letter-spacing: -0.01em;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.2);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        border: none !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #7c7ff7, #9d6ffc) !important;
        box-shadow: 0 4px 24px rgba(99, 102, 241, 0.35) !important;
    }

    /* --- Divider --- */
    .custom-divider {
        border-top: 1px solid var(--border-subtle);
        margin: 18px 0;
    }

    /* --- Thread Tweet --- */
    .thread-tweet {
        background: rgba(10, 20, 40, 0.6);
        border-left: 3px solid var(--accent-blue);
        padding: 14px 16px;
        margin: 6px 0;
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
        color: var(--text-primary);
        font-size: 14px;
        line-height: 1.6;
    }
    .thread-number {
        color: var(--accent-blue);
        font-weight: 700;
        font-size: 12px;
        margin-bottom: 4px;
    }

    /* ==========================================
       INPUTS - Modern glass style
       ========================================== */
    .stTextArea textarea,
    .stTextInput input {
        background-color: rgba(15, 20, 35, 0.8) !important;
        color: var(--text-primary) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: var(--radius-sm) !important;
        font-size: 16px !important;
        padding: 12px !important;
        transition: all 0.3s ease;
    }
    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: rgba(99, 102, 241, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1), 0 0 20px rgba(99, 102, 241, 0.05) !important;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: var(--radius-sm) !important;
        min-height: 44px;
    }

    /* Checkbox */
    .stCheckbox label {
        min-height: 44px;
        display: flex;
        align-items: center;
    }

    /* ==========================================
       TABS - Premium pill style
       ========================================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: rgba(15, 20, 35, 0.6);
        border-radius: var(--radius-md);
        padding: 4px;
        border: 1px solid var(--border-subtle);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm);
        padding: 10px 16px;
        font-size: 14px;
        font-weight: 600;
        color: var(--text-secondary);
        min-height: 44px;
        transition: all 0.25s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.1)) !important;
        color: #a5b4fc !important;
        box-shadow: 0 0 12px rgba(99, 102, 241, 0.1);
    }
    .stTabs [data-baseweb="tab-border"] { display: none; }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }

    /* ==========================================
       EXPANDER
       ========================================== */
    .streamlit-expanderHeader {
        font-size: 15px;
        font-weight: 600;
        border-radius: var(--radius-md);
    }

    /* ==========================================
       SIDEBAR - Premium dark
       ========================================== */
    section[data-testid="stSidebar"] {
        background: rgba(8, 12, 24, 0.97) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid var(--border-subtle);
    }
    section[data-testid="stSidebar"] .stButton > button {
        border-radius: var(--radius-sm) !important;
        font-size: 14px;
        text-align: left;
    }

    /* --- Nav Links --- */
    .nav-link {
        display: block;
        padding: 10px 14px;
        margin: 3px 0;
        border-radius: var(--radius-sm);
        color: var(--text-primary) !important;
        text-decoration: none !important;
        transition: all 0.2s ease;
        font-size: 14px;
    }
    .nav-link:hover {
        background: rgba(99, 102, 241, 0.1);
    }
    .nav-link.active {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white !important;
    }

    /* ==========================================
       MOBILE BOTTOM NAV - Premium glass
       ========================================== */
    .mobile-bottom-nav {
        display: none;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 9999;
        background: rgba(8, 12, 24, 0.95);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border-top: 1px solid rgba(99, 102, 241, 0.15);
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
        color: var(--text-muted);
        font-size: 10px;
        font-weight: 500;
        padding: 4px 8px;
        border-radius: var(--radius-sm);
        transition: all 0.25s ease;
        min-width: 48px;
        min-height: 48px;
        justify-content: center;
    }
    .mobile-bottom-nav a .nav-icon { font-size: 20px; margin-bottom: 2px; }
    .mobile-bottom-nav a.active {
        color: #a5b4fc;
        background: rgba(99, 102, 241, 0.15);
    }
    .mobile-bottom-nav a:hover { color: #a5b4fc; }

    /* ==========================================
       EMPTY STATE
       ========================================== */
    .empty-state {
        text-align: center;
        padding: 40px 20px;
        color: var(--text-secondary);
    }
    .empty-state .empty-icon {
        font-size: 48px;
        margin-bottom: 12px;
        opacity: 0.5;
    }
    .empty-state p {
        font-size: 14px;
        line-height: 1.6;
    }

    /* ==========================================
       INFO BANNER
       ========================================== */
    .info-banner {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.06));
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: var(--radius-md);
        padding: 14px 16px;
        margin: 10px 0;
    }
    .info-banner-title {
        color: #a5b4fc;
        font-weight: 700;
        font-size: 15px;
    }
    .info-banner-desc {
        color: var(--text-secondary);
        font-size: 13px;
        margin-top: 4px;
    }

    /* ==========================================
       SETUP WARNING
       ========================================== */
    .setup-warning {
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.08), rgba(245, 158, 11, 0.04));
        border: 1px solid rgba(251, 191, 36, 0.2);
        border-radius: var(--radius-md);
        padding: 16px;
        margin-top: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .setup-warning-icon { font-size: 24px; }
    .setup-warning-text {
        color: #fbbf24;
        font-size: 14px;
        font-weight: 600;
    }

    /* ==========================================
       RESPONSIVE BREAKPOINTS
       ========================================== */

    /* Tablet and up */
    @media (min-width: 640px) {
        .block-container {
            padding: 1rem 2rem 2rem 2rem !important;
        }
        .hero-title { font-size: 32px; }
        .hero-section { padding: 36px 20px 28px; }
        .stat-number { font-size: 30px; }
        .main-header h1 { font-size: 28px; }
    }

    /* Desktop */
    @media (min-width: 1024px) {
        .block-container {
            padding: 1rem 3rem 2rem 3rem !important;
        }
        .hero-title { font-size: 36px; }
        .main-header h1 { font-size: 32px; }
    }

    /* Mobile only */
    @media (max-width: 639px) {
        /* Show bottom nav */
        .mobile-bottom-nav { display: block; }

        /* Hide sidebar completely on mobile */
        section[data-testid="stSidebar"] { display: none !important; }
        button[data-testid="stSidebarCollapsedControl"],
        button[kind="header"] { display: none !important; }

        /* Content padding with bottom nav space */
        .block-container {
            padding: 0.5rem 0.75rem 80px 0.75rem !important;
        }

        /* Full width buttons */
        .stButton > button { width: 100%; margin-bottom: 4px; }

        /* Smaller header on mobile */
        .main-header { padding: 4px 0 12px 0; }
        .main-header h1 { font-size: 22px; }

        /* Hero compact */
        .hero-section {
            padding: 20px 12px 18px;
            margin: -4px -4px 14px -4px;
        }
        .hero-logo { font-size: 42px; }
        .hero-title { font-size: 24px; }
        .hero-subtitle { font-size: 11px; letter-spacing: 0.12em; }

        /* Stack columns better */
        [data-testid="column"] { padding: 0 2px !important; }

        /* Tab text */
        .stTabs [data-baseweb="tab"] { font-size: 12px; padding: 8px 10px; }

        /* Stat boxes compact */
        .stat-box { padding: 14px 8px; }
        .stat-number { font-size: 22px; }
        .stat-label { font-size: 10px; }

        /* Action cards compact */
        .action-card { padding: 16px 10px 12px; min-height: 100px; }
        .action-icon { font-size: 28px; margin-bottom: 6px; }
        .action-title { font-size: 13px; }
        .action-desc { font-size: 11px; }

        /* Tweet card compact */
        .tweet-card { padding: 14px; margin: 6px 0; }
        .tweet-metrics { gap: 10px; font-size: 12px; }

        /* Generated tweet */
        .generated-tweet { padding: 16px; font-size: 14px; }

        /* Activity compact */
        .activity-item { padding: 12px; }
    }

    /* Small phones */
    @media (max-width: 380px) {
        .block-container { padding: 0.5rem 0.5rem 80px 0.5rem !important; }
        .hero-title { font-size: 20px; }
        .stTabs [data-baseweb="tab"] { font-size: 11px; padding: 8px 6px; }
    }

    /* ==========================================
       SCROLLBAR
       ========================================== */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(99, 102, 241, 0.2);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(99, 102, 241, 0.35);
    }

    /* --- Alerts/Info boxes --- */
    .stAlert { border-radius: var(--radius-md) !important; }

    /* ==========================================
       METRICS - Override default
       ========================================== */
    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
    }

    /* ==========================================
       LOGIN PAGE
       ========================================== */
    .login-container {
        max-width: 360px;
        margin: 60px auto 0;
        padding: 32px 24px;
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-xl);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .login-container::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--gradient-main);
    }
    .login-logo {
        font-size: 56px;
        display: block;
        margin-bottom: 12px;
        filter: drop-shadow(0 4px 16px rgba(99, 102, 241, 0.4));
    }
    .login-title {
        font-size: 22px;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 4px;
    }
    .login-subtitle {
        color: var(--text-secondary);
        font-size: 13px;
        margin-bottom: 24px;
    }
    </style>
    """, unsafe_allow_html=True)


def render_research_engine_toggle(key_suffix: str = "") -> str:
    """Render research engine toggle (Standard vs Grok).
    Returns "standard" or "grok"."""
    from modules.grok_client import has_grok_key

    if not has_grok_key():
        return "standard"

    engine = st.radio(
        "Araştırma Motoru",
        options=["standard", "grok"],
        format_func=lambda x: "🔍 Standart (DuckDuckGo — ücretsiz)" if x == "standard"
                              else "🧠 Grok AI (X + Web — premium)",
        index=0,
        key=f"research_engine_{key_suffix}",
        horizontal=True,
        help="Grok: X verilerine doğrudan erişim, gerçek zamanlı arama. Standart: DuckDuckGo ücretsiz arama."
    )
    return engine


def render_agentic_mode_toggle(key_suffix: str = "") -> str:
    """Render agentic research mode toggle (None, Standard, Grok).
    Returns "none", "standard", or "grok". Mutual exclusive."""
    from modules.grok_client import has_grok_key

    _has_grok = has_grok_key()

    col_ag1, col_ag2 = st.columns(2)

    with col_ag1:
        use_standard_agentic = st.checkbox(
            "🤖 AI Otonom Araştırma",
            value=False,
            key=f"use_agentic_{key_suffix}",
            help="AI modeli kendi başına DuckDuckGo'da gezinerek araştırma yapar.",
        )

    with col_ag2:
        if _has_grok:
            use_grok_agentic = st.checkbox(
                "🧠 Grok Otonom Araştırma",
                value=False,
                key=f"use_grok_agentic_{key_suffix}",
                help="Grok modeli X'te ve web'de kendi başına gezinerek araştırma yapar. "
                     "X verilerine doğrudan erişim avantajı.",
            )
        else:
            use_grok_agentic = False

    # Mutual exclusive: if both selected, last one wins
    if use_standard_agentic and use_grok_agentic:
        # Grok was just selected — disable standard
        st.session_state[f"use_agentic_{key_suffix}"] = False
        return "grok"
    elif use_grok_agentic:
        return "grok"
    elif use_standard_agentic:
        return "standard"
    return "none"


def render_grok_cost_indicator():
    """Render Grok usage cost indicator in sidebar."""
    from modules.grok_client import has_grok_key, get_grok_cost, get_grok_call_count

    if not has_grok_key():
        return

    cost = get_grok_cost()
    calls = get_grok_call_count()

    if calls > 0:
        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.2);
                    border-radius:8px; padding:8px 12px; margin:4px 0;">
            <div style="color:#a5b4fc; font-size:11px; font-weight:bold;">🧠 Grok Kullanım</div>
            <div style="color:#f1f5f9; font-size:13px;">${cost:.3f} · {calls} çağrı</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Sıfırla", key="grok_cost_reset", type="secondary"):
            from modules.grok_client import reset_grok_cost
            reset_grok_cost()
            st.rerun()


def render_sidebar_nav(current_page: str = ""):
    """Render sidebar nav (desktop) + bottom nav (mobile)."""
    # --- Desktop sidebar ---
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 8px 0 12px;">
            <span style="font-size: 28px;">🤖</span>
            <div style="font-size: 16px; font-weight: 800; color: #f1f5f9; margin-top: 4px;
                        letter-spacing: -0.02em;">X AI Otomasyon</div>
        </div>
        """, unsafe_allow_html=True)
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

        has_grok = bool(get_secret("xai_api_key", ""))
        if has_grok:
            st.success("Grok API ✓", icon="🧠")
            render_grok_cost_indicator()

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
        <div style="background:rgba(99, 102, 241, 0.06); border-left:3px solid #6366f1; padding:6px 10px;
                    margin:8px 0; border-radius:0 8px 8px 0;">
            <span style="color:#a5b4fc; font-size:11px; font-weight:600;">📋 İçerik:</span>
            <span style="color:#94a3b8; font-size:12px; margin-left:4px;">{content_summary}</span>
        </div>"""

    # Follower count display
    followers = getattr(topic, 'author_followers_count', 0) or 0
    followers_html = ""
    if followers > 0:
        followers_html = f'<span style="color:#64748b; font-size:11px; margin-left:6px;">· 👥 {_format_number(followers)}</span>'

    # Total engagement
    total_eng = topic.like_count + topic.retweet_count + topic.reply_count
    total_eng_html = f'<span style="color:#fbbf24; font-size:12px; font-weight:600;">📊 {_format_number(total_eng)}</span>'

    # Media indicator
    media_urls = getattr(topic, 'media_urls', []) or []
    media_html = ""
    if media_urls:
        media_count = len(media_urls)
        media_html = f'<span style="color:#10b981; font-size:11px; margin-left:6px;">🖼️ {media_count} medya</span>'

    # Time and date
    time_and_date = getattr(topic, 'time_and_date', '') or topic.time_ago

    st.markdown(f"""
    <div class="tweet-card">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
            <div>
                <span class="tweet-author">{topic.author_name}</span>
                <span class="tweet-username">@{topic.author_username}</span>
                {followers_html}
            </div>
            <div style="display:flex; gap:6px; align-items:center;">
                {media_html}
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
            {total_eng_html}
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
    <div style="text-align:right; color:#64748b; font-size:13px; margin-top:4px;">
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


def render_media_suggestions(media_result, key_prefix: str = "media"):
    """Render media search results as a visual grid with download links.

    Args:
        media_result: MediaSearchResult from media_finder module
        key_prefix: Unique key prefix for Streamlit widgets
    """
    if not media_result or not media_result.has_results:
        st.info("Bu konu için görsel bulunamadı.")
        return

    # --- Images ---
    if media_result.images:
        st.markdown(f"""
        <div style="color:#a5b4fc; font-weight:bold; font-size:14px; margin:12px 0 8px 0;">
            🖼️ Önerilen Görseller ({len(media_result.images)})
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(min(len(media_result.images), 4))
        for i, img in enumerate(media_result.images):
            with cols[i % len(cols)]:
                # Show image
                try:
                    st.image(img.thumbnail_url or img.url, use_container_width=True)
                except Exception:
                    st.markdown(f"""
                    <div style="background:rgba(15,20,35,0.7); border:1px solid rgba(255,255,255,0.1);
                                border-radius:8px; padding:20px; text-align:center; color:#64748b;">
                        🖼️ Önizleme yüklenemedi
                    </div>
                    """, unsafe_allow_html=True)

                # Source badge
                source_badge = "𝕏" if img.source == "x" else "🌐"
                source_color = "#1d9bf0" if img.source == "x" else "#10b981"

                st.markdown(f"""
                <div style="font-size:11px; color:#94a3b8; margin:4px 0;">
                    <span style="color:{source_color}; font-weight:bold;">{source_badge}</span>
                    {img.title[:60] + '...' if len(img.title) > 60 else img.title}
                </div>
                """, unsafe_allow_html=True)

                # Download link
                if img.source_url:
                    st.markdown(f"[Kaynağı aç]({img.source_url})", unsafe_allow_html=False)
                st.markdown(f"[Görseli indir]({img.url})", unsafe_allow_html=False)

    # --- Videos ---
    if media_result.videos:
        st.markdown(f"""
        <div style="color:#a5b4fc; font-weight:bold; font-size:14px; margin:16px 0 8px 0;">
            🎬 Önerilen Videolar ({len(media_result.videos)})
        </div>
        """, unsafe_allow_html=True)

        for i, vid in enumerate(media_result.videos):
            col_thumb, col_info = st.columns([1, 3])
            with col_thumb:
                if vid.thumbnail_url:
                    try:
                        st.image(vid.thumbnail_url, use_container_width=True)
                    except Exception:
                        st.markdown("🎬", unsafe_allow_html=False)
                else:
                    st.markdown("🎬", unsafe_allow_html=False)
            with col_info:
                source_badge = "𝕏" if vid.source == "x" else "🌐"
                st.markdown(f"""
                <div style="color:#e2e8f0; font-size:13px; font-weight:bold;">
                    {source_badge} {vid.title[:80]}
                </div>
                """, unsafe_allow_html=True)
                if vid.author:
                    st.caption(f"@{vid.author}")
                if vid.source_url:
                    st.markdown(f"[Videoyu aç]({vid.source_url})")

    # Summary
    total = len(media_result.images) + len(media_result.videos)
    x_count = sum(1 for m in media_result.images + media_result.videos if m.source == "x")
    web_count = total - x_count
    parts = []
    if x_count:
        parts.append(f"𝕏 {x_count}")
    if web_count:
        parts.append(f"🌐 {web_count}")
    st.caption(f"Toplam {total} medya bulundu ({' | '.join(parts)})")


def render_media_source_selector(key_suffix: str = "") -> str:
    """Render a media source selector toggle.

    Returns: "x", "web", or "all"
    """
    options = {
        "x": "𝕏 Sadece X",
        "all": "𝕏+🌐 X + Web (Önerilen)",
        "web": "🌐 Sadece Web",
    }
    selected = st.selectbox(
        "Görsel Kaynağı",
        options=list(options.keys()),
        format_func=lambda x: options[x],
        index=1,  # Default: all
        key=f"media_source_{key_suffix}",
    )
    return selected


def render_image_analysis(analysis_text: str, image_url: str = ""):
    """Render the result of AI image analysis."""
    if not analysis_text:
        return

    st.markdown(f"""
    <div style="background:rgba(99,102,241,0.06); border:1px solid rgba(99,102,241,0.15);
                border-radius:12px; padding:14px; margin:8px 0;">
        <div style="color:#a5b4fc; font-weight:bold; font-size:13px; margin-bottom:8px;">
            👁️ Görsel Analizi
        </div>
        <div style="color:#e2e8f0; font-size:13px; line-height:1.6;">
            {analysis_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


def check_password() -> bool:
    """Premium password protection for the app"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Premium login page
    st.markdown("""
    <div class="login-container">
        <span class="login-logo">🤖</span>
        <div class="login-title">X AI Otomasyon</div>
        <div class="login-subtitle">Twitter/X AI İçerik Otomasyon Paneli</div>
    </div>
    """, unsafe_allow_html=True)

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Şifre", type="password", key="login_password",
                                 label_visibility="collapsed", placeholder="Şifrenizi girin...")

        if st.button("Giriş Yap", type="primary", use_container_width=True):
            correct_password = get_secret("app_password", "admin123")
            if password == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Yanlış şifre!")

    return False
