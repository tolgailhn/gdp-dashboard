"""
Shared UI Components Module
Reusable Streamlit components for the X AI Automation Dashboard
"""
import streamlit as st


_secrets_cache = None
_secrets_mtime = 0  # Track file modification time for auto-refresh

def _load_secrets_toml(force_reload: bool = False):
    """Load secrets from .streamlit/secrets.toml directly (bypass st.secrets).
    Auto-refreshes when file is modified on disk."""
    global _secrets_cache, _secrets_mtime
    from pathlib import Path
    toml_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"

    # Check if file was modified since last load
    current_mtime = 0
    if toml_path.exists():
        try:
            current_mtime = toml_path.stat().st_mtime
        except Exception:
            pass

    if _secrets_cache is not None and not force_reload and current_mtime == _secrets_mtime:
        return _secrets_cache

    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # Python < 3.11 fallback

    if toml_path.exists():
        try:
            with open(toml_path, "rb") as f:
                _secrets_cache = tomllib.load(f)
            _secrets_mtime = current_mtime
        except Exception:
            _secrets_cache = {}
    else:
        _secrets_cache = {}
    return _secrets_cache


def invalidate_secrets_cache():
    """Force reload of secrets on next get_secret() call."""
    global _secrets_cache, _secrets_mtime
    _secrets_cache = None
    _secrets_mtime = 0


def get_secret(key: str, default: str = "") -> str:
    """Safely get a secret value - reads .streamlit/secrets.toml directly"""
    import os
    # First try environment variables
    env_val = os.environ.get(key, "")
    if env_val:
        return env_val
    # Then read TOML file directly (no st.secrets dependency)
    secrets = _load_secrets_toml()
    return secrets.get(key, default)


def setup_page_config(title: str = "X AI Otomasyon", icon: str = "🤖"):
    """Configure page with mobile-friendly settings"""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="auto",
    )


def inject_custom_css():
    """Inject premium mobile-first CSS design system v4.0"""
    st.markdown("""
    <style>
    /* ========================================
       PREMIUM DESIGN SYSTEM v4.0
       Animated Glassmorphism + Neon Accents
       ======================================== */

    /* --- Import Google Font --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* --- CSS Variables --- */
    :root {
        --bg-primary: #050810;
        --bg-secondary: #0a0f1e;
        --bg-card: rgba(12, 17, 35, 0.65);
        --bg-card-hover: rgba(18, 25, 50, 0.8);
        --bg-card-solid: #0d1225;
        --border-subtle: rgba(255, 255, 255, 0.04);
        --border-glow: rgba(99, 102, 241, 0.35);
        --accent-primary: #6366f1;
        --accent-secondary: #8b5cf6;
        --accent-cyan: #22d3ee;
        --accent-emerald: #10b981;
        --accent-rose: #f43f5e;
        --accent-amber: #f59e0b;
        --accent-twitter: #1DA1F2;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #475569;
        --gradient-main: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        --gradient-neon: linear-gradient(135deg, #6366f1 0%, #22d3ee 100%);
        --gradient-warm: linear-gradient(135deg, #f43f5e 0%, #f59e0b 100%);
        --gradient-mesh: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(168,85,247,0.08) 30%, rgba(34,211,238,0.06) 60%, rgba(16,185,129,0.04) 100%);
        --shadow-neon: 0 0 20px rgba(99, 102, 241, 0.15), 0 0 60px rgba(99, 102, 241, 0.05);
        --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.3), 0 2px 8px rgba(0, 0, 0, 0.2);
        --shadow-elevated: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 40px rgba(99, 102, 241, 0.08);
        --radius-sm: 12px;
        --radius-md: 16px;
        --radius-lg: 20px;
        --radius-xl: 28px;
        --transition-smooth: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        --transition-bounce: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    /* --- Base & Reset --- */
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }

    .stApp {
        max-width: 100%;
        overflow-x: hidden;
        background: var(--bg-primary) !important;
    }

    /* Animated mesh background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background:
            radial-gradient(ellipse 80% 50% at 20% 20%, rgba(99,102,241,0.08) 0%, transparent 50%),
            radial-gradient(ellipse 60% 40% at 80% 80%, rgba(168,85,247,0.06) 0%, transparent 50%),
            radial-gradient(ellipse 50% 60% at 50% 10%, rgba(34,211,238,0.04) 0%, transparent 50%);
        animation: meshMove 20s ease-in-out infinite alternate;
        pointer-events: none;
        z-index: 0;
    }
    @keyframes meshMove {
        0% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(-2%, 3%) scale(1.02); }
        66% { transform: translate(2%, -2%) scale(0.98); }
        100% { transform: translate(-1%, 1%) scale(1.01); }
    }

    .block-container {
        padding: 0.75rem 1rem 5rem 1rem !important;
        max-width: 100% !important;
        position: relative;
        z-index: 1;
    }

    /* --- Hide Streamlit chrome --- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebarNav"] { display: none !important; }
    div[data-testid="stSidebarNav"] { display: none !important; }
    /* Hide Streamlit's built-in page nav (shows broken material icons) */
    [data-testid="stSidebarNavItems"],
    div[data-testid="stSidebarNavSeparator"],
    nav[data-testid="stSidebarNav"],
    [data-testid="stPageLink"],
    ul[data-testid="stSidebarNavItems"],
    section[data-testid="stSidebar"] > div > div > div > ul,
    section[data-testid="stSidebar"] nav {
        display: none !important;
    }

    header[data-testid="stHeader"] {
        background: rgba(5, 8, 16, 0.85) !important;
        backdrop-filter: blur(30px) saturate(180%);
        -webkit-backdrop-filter: blur(30px) saturate(180%);
        border-bottom: 1px solid rgba(99, 102, 241, 0.08);
    }
    /* Fix broken material icon text in header/toolbar */
    header[data-testid="stHeader"] [data-testid="stToolbar"] {
        font-size: 0 !important;
    }
    header[data-testid="stHeader"] [data-testid="stToolbar"] button {
        font-size: 14px !important;
    }
    /* Hide raw :material/ icon text leaking in page chrome */
    [data-testid="stHeaderActionElements"] span:not([data-testid]) {
        font-size: 0;
        overflow: hidden;
        width: 0;
        display: inline-block;
    }

    /* --- Typography --- */
    h1, h2, h3 {
        letter-spacing: -0.04em;
        font-weight: 800;
    }
    h1 { color: var(--text-primary) !important; }
    h2 { color: var(--text-primary) !important; }
    h3 { color: var(--text-primary) !important; font-size: 18px !important; }

    /* ==========================================
       GLASSMORPHISM CARDS v2
       ========================================== */
    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(24px) saturate(150%);
        -webkit-backdrop-filter: blur(24px) saturate(150%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: var(--radius-lg);
        padding: 22px;
        margin: 10px 0;
        transition: var(--transition-smooth);
        position: relative;
        overflow: hidden;
    }
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(99,102,241,0.5) 50%, transparent 100%);
    }
    .glass-card::after {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle at center, rgba(99,102,241,0.03) 0%, transparent 40%);
        opacity: 0;
        transition: opacity 0.6s ease;
        pointer-events: none;
    }
    .glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.2);
        box-shadow: var(--shadow-neon);
    }
    .glass-card:hover::after { opacity: 1; }

    /* --- Tweet Cards --- */
    .tweet-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px) saturate(140%);
        -webkit-backdrop-filter: blur(20px) saturate(140%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: var(--radius-lg);
        padding: 20px;
        margin: 10px 0;
        color: var(--text-primary);
        transition: var(--transition-smooth);
        position: relative;
        overflow: hidden;
    }
    .tweet-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 3px; height: 100%;
        background: var(--gradient-neon);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    .tweet-card::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(99,102,241,0.03) 0%, transparent 60%);
        opacity: 0;
        transition: opacity 0.4s ease;
        pointer-events: none;
    }
    .tweet-card:hover {
        transform: translateY(-3px) scale(1.005);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.12), 0 0 0 1px rgba(99,102,241,0.1);
        border-color: rgba(99, 102, 241, 0.15);
    }
    .tweet-card:hover::before { opacity: 1; }
    .tweet-card:hover::after { opacity: 1; }

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
        margin: 12px 0;
        line-height: 1.65;
        font-size: 15px;
        color: var(--text-primary);
        word-break: break-word;
    }
    .tweet-metrics {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        color: var(--text-secondary);
        font-size: 13px;
        margin-top: 14px;
        padding-top: 14px;
        border-top: 1px solid rgba(255,255,255,0.04);
    }
    .tweet-time { color: var(--text-muted); font-size: 12px; }
    .tweet-category {
        display: inline-block;
        background: var(--gradient-main);
        color: white;
        padding: 3px 14px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.03em;
        box-shadow: 0 2px 8px rgba(99,102,241,0.25);
    }

    /* Relevance badges */
    .relevance-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        backdrop-filter: blur(8px);
    }
    .relevance-high {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.2);
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.08);
    }
    .relevance-medium {
        background: rgba(245, 158, 11, 0.12);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    .relevance-low {
        background: rgba(148, 163, 184, 0.1);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.15);
    }

    /* --- Generated Tweet Preview --- */
    .generated-tweet {
        background: linear-gradient(135deg, rgba(8, 15, 35, 0.95), rgba(15, 25, 50, 0.95));
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-left: 3px solid transparent;
        border-image: var(--gradient-neon) 1;
        border-image-slice: 0 0 0 1;
        border-radius: var(--radius-lg);
        padding: 24px;
        margin: 16px 0;
        color: #ffffff;
        font-size: 15px;
        line-height: 1.75;
        white-space: pre-wrap;
        word-break: break-word;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    .generated-tweet::before {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 200px; height: 200px;
        background: radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 60%);
        animation: gentlePulse 6s ease-in-out infinite;
    }
    .generated-tweet::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0;
        width: 150px; height: 150px;
        background: radial-gradient(circle, rgba(34,211,238,0.04) 0%, transparent 60%);
        animation: gentlePulse 6s ease-in-out infinite 3s;
    }
    @keyframes gentlePulse {
        0%, 100% { opacity: 0.5; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.1); }
    }

    /* ==========================================
       STAT BOXES — Animated Glow Ring
       ========================================== */
    .stat-box {
        background: var(--bg-card);
        backdrop-filter: blur(20px) saturate(140%);
        -webkit-backdrop-filter: blur(20px) saturate(140%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: var(--radius-lg);
        padding: 20px 16px;
        text-align: center;
        transition: var(--transition-smooth);
        position: relative;
        overflow: hidden;
    }
    .stat-box::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: var(--gradient-neon);
        opacity: 0.7;
        transition: opacity 0.4s ease;
    }
    .stat-box::after {
        content: '';
        position: absolute;
        top: -2px; left: 50%; transform: translateX(-50%);
        width: 40px; height: 40px;
        background: radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%);
        opacity: 0;
        transition: all 0.4s ease;
    }
    .stat-box:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.15);
        box-shadow: var(--shadow-neon);
    }
    .stat-box:hover::before { opacity: 1; }
    .stat-box:hover::after { opacity: 1; width: 100px; height: 60px; }
    .stat-number {
        font-size: 30px;
        font-weight: 900;
        background: var(--gradient-neon);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.2;
        letter-spacing: -0.03em;
    }
    .stat-label {
        font-size: 11px;
        color: var(--text-secondary);
        margin-top: 6px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* ==========================================
       ACTION CARDS — 3D Perspective Hover
       ========================================== */
    .action-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px) saturate(140%);
        -webkit-backdrop-filter: blur(20px) saturate(140%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: var(--radius-lg);
        padding: 28px 16px 18px;
        text-align: center;
        transition: var(--transition-smooth);
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        overflow: hidden;
        cursor: pointer;
    }
    .action-card::before {
        content: '';
        position: absolute;
        inset: 0;
        background: var(--gradient-mesh);
        opacity: 0;
        transition: opacity 0.5s ease;
        pointer-events: none;
    }
    .action-card::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 2px;
        background: var(--gradient-neon);
        transform: scaleX(0);
        transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .action-card:hover {
        transform: translateY(-6px) rotateX(2deg);
        border-color: rgba(99, 102, 241, 0.2);
        box-shadow: var(--shadow-elevated);
    }
    .action-card:hover::before { opacity: 1; }
    .action-card:hover::after { transform: scaleX(1); }
    .action-icon {
        font-size: 40px;
        margin-bottom: 12px;
        filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.3));
        transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .action-card:hover .action-icon {
        transform: scale(1.15) translateY(-2px);
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
        margin-top: 6px;
        line-height: 1.4;
    }

    /* ==========================================
       HERO SECTION — Animated Gradient + Particles
       ========================================== */
    .hero-section {
        position: relative;
        text-align: center;
        padding: 40px 20px 32px;
        margin: -8px -8px 24px -8px;
        border-radius: 0 0 var(--radius-xl) var(--radius-xl);
        background: linear-gradient(160deg,
            rgba(99,102,241,0.12) 0%,
            rgba(139,92,246,0.08) 25%,
            rgba(34,211,238,0.06) 50%,
            rgba(16,185,129,0.04) 75%,
            rgba(99,102,241,0.08) 100%);
        background-size: 200% 200%;
        animation: heroGradient 8s ease-in-out infinite;
        border-bottom: 1px solid rgba(99, 102, 241, 0.1);
        overflow: hidden;
    }
    @keyframes heroGradient {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }

    /* Floating orbs */
    .hero-section::before {
        content: '';
        position: absolute;
        top: -30%; right: -10%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 60%);
        border-radius: 50%;
        animation: floatOrb 8s ease-in-out infinite;
        filter: blur(40px);
    }
    .hero-section::after {
        content: '';
        position: absolute;
        bottom: -20%; left: -5%;
        width: 250px; height: 250px;
        background: radial-gradient(circle, rgba(34,211,238,0.1) 0%, transparent 60%);
        border-radius: 50%;
        animation: floatOrb 8s ease-in-out infinite 4s;
        filter: blur(40px);
    }
    @keyframes floatOrb {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(10px, -20px) scale(1.05); }
        50% { transform: translate(-5px, 10px) scale(0.95); }
        75% { transform: translate(15px, 5px) scale(1.02); }
    }

    .hero-logo {
        font-size: 60px;
        display: block;
        margin-bottom: 12px;
        filter: drop-shadow(0 4px 20px rgba(99,102,241,0.5));
        position: relative;
        z-index: 1;
        animation: logoFloat 4s ease-in-out infinite;
    }
    @keyframes logoFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }

    .hero-title {
        font-size: 32px;
        font-weight: 900;
        letter-spacing: -0.04em;
        margin: 0;
        position: relative;
        z-index: 1;
        background: linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 40%, #a5b4fc 80%, #818cf8 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmerText 4s linear infinite;
    }
    @keyframes shimmerText {
        0% { background-position: 0% center; }
        100% { background-position: 200% center; }
    }

    .hero-subtitle {
        color: var(--text-secondary);
        font-size: 14px;
        margin-top: 8px;
        position: relative;
        z-index: 1;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        font-weight: 600;
    }

    /* ==========================================
       HEADER — Page headers with gradient
       ========================================== */
    .main-header {
        text-align: center;
        padding: 12px 0 20px 0;
        position: relative;
    }
    .main-header h1 {
        color: var(--text-primary) !important;
        font-size: 28px;
        font-weight: 900;
        margin-bottom: 4px;
        letter-spacing: -0.04em;
    }
    .main-header p {
        color: var(--text-secondary);
        font-size: 14px;
    }

    .page-header {
        text-align: center;
        padding: 20px 0 28px 0;
    }
    .page-header .page-icon {
        font-size: 52px;
        display: block;
        margin-bottom: 10px;
        filter: drop-shadow(0 4px 16px rgba(99,102,241,0.35));
        animation: logoFloat 4s ease-in-out infinite;
    }
    .page-header h1 {
        font-size: 26px;
        font-weight: 900;
        background: var(--gradient-neon);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 !important;
        letter-spacing: -0.03em;
    }
    .page-header p {
        color: var(--text-secondary);
        font-size: 13px;
        margin-top: 6px;
    }

    /* ==========================================
       ACTIVITY TIMELINE — Animated pulse dots
       ========================================== */
    .activity-item {
        background: var(--bg-card);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: var(--radius-md);
        padding: 16px 18px;
        margin: 6px 0;
        transition: var(--transition-smooth);
        position: relative;
        display: flex;
        gap: 14px;
        align-items: flex-start;
    }
    .activity-item:hover {
        border-color: rgba(99, 102, 241, 0.15);
        background: var(--bg-card-hover);
        transform: translateX(4px);
    }
    .activity-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--gradient-neon);
        margin-top: 5px;
        flex-shrink: 0;
        box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
        animation: dotPulse 3s ease-in-out infinite;
    }
    .activity-item:nth-child(2) .activity-dot { animation-delay: 0.5s; }
    .activity-item:nth-child(3) .activity-dot { animation-delay: 1s; }
    .activity-item:nth-child(4) .activity-dot { animation-delay: 1.5s; }
    .activity-item:nth-child(5) .activity-dot { animation-delay: 2s; }
    @keyframes dotPulse {
        0%, 100% { box-shadow: 0 0 6px rgba(99,102,241,0.3); transform: scale(1); }
        50% { box-shadow: 0 0 16px rgba(99,102,241,0.6); transform: scale(1.15); }
    }
    .activity-content { flex: 1; min-width: 0; }
    .activity-text {
        color: var(--text-primary);
        font-size: 14px;
        line-height: 1.55;
        word-break: break-word;
    }
    .activity-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 8px;
    }
    .activity-time { color: var(--text-muted); font-size: 12px; }
    .activity-link {
        color: var(--accent-primary) !important;
        font-size: 12px;
        text-decoration: none !important;
        font-weight: 700;
        transition: all 0.3s ease;
        position: relative;
    }
    .activity-link::after {
        content: '';
        position: absolute;
        bottom: -2px; left: 0;
        width: 0; height: 1px;
        background: var(--accent-cyan);
        transition: width 0.3s ease;
    }
    .activity-link:hover { color: var(--accent-cyan) !important; }
    .activity-link:hover::after { width: 100%; }

    /* ==========================================
       SECTION HEADERS
       ========================================== */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 24px 0 14px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        position: relative;
    }
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -1px; left: 0;
        width: 60px; height: 2px;
        background: var(--gradient-neon);
        border-radius: 1px;
    }
    .section-header h3 {
        margin: 0 !important;
        padding: 0;
        font-size: 16px !important;
        font-weight: 800;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em;
    }
    .section-badge {
        background: rgba(99, 102, 241, 0.1);
        color: #a5b4fc;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        border: 1px solid rgba(99,102,241,0.15);
    }

    /* ==========================================
       BUTTONS — Neon Glow Style
       ========================================== */
    .stButton > button {
        border-radius: var(--radius-sm) !important;
        padding: 0.55rem 1.5rem;
        font-weight: 700;
        font-size: 14px;
        min-height: 46px;
        transition: var(--transition-smooth);
        border: 1px solid rgba(255,255,255,0.06) !important;
        letter-spacing: -0.01em;
        position: relative;
        overflow: hidden;
    }
    .stButton > button::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 60%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(99, 102, 241, 0.15);
    }
    .stButton > button:hover::after { opacity: 1; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 16px rgba(99,102,241,0.2);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #7c7ff7, #9d6ffc) !important;
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.35), 0 0 0 1px rgba(99,102,241,0.2) !important;
        transform: translateY(-2px);
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0) scale(0.98);
    }

    /* --- Divider --- */
    .custom-divider {
        border-top: 1px solid rgba(255,255,255,0.04);
        margin: 20px 0;
    }

    /* --- Thread Tweet --- */
    .thread-tweet {
        background: rgba(8, 15, 35, 0.7);
        border-left: 3px solid transparent;
        border-image: var(--gradient-neon) 1;
        padding: 16px 18px;
        margin: 6px 0;
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
        color: var(--text-primary);
        font-size: 14px;
        line-height: 1.65;
        transition: var(--transition-smooth);
    }
    .thread-tweet:hover {
        background: rgba(12, 20, 40, 0.8);
    }
    .thread-number {
        color: var(--accent-primary);
        font-weight: 800;
        font-size: 12px;
        margin-bottom: 6px;
    }

    /* ==========================================
       INPUTS — Glass Style with Glow Focus
       ========================================== */
    .stTextArea textarea,
    .stTextInput input {
        background-color: rgba(10, 15, 30, 0.8) !important;
        color: var(--text-primary) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: var(--radius-sm) !important;
        font-size: 16px !important;
        padding: 14px !important;
        transition: var(--transition-smooth);
    }
    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: rgba(99, 102, 241, 0.4) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.08), 0 0 30px rgba(99, 102, 241, 0.06) !important;
        background-color: rgba(12, 18, 35, 0.9) !important;
    }

    .stSelectbox > div > div {
        border-radius: var(--radius-sm) !important;
        min-height: 46px;
    }
    .stCheckbox label {
        min-height: 46px;
        display: flex;
        align-items: center;
    }

    /* ==========================================
       TABS — Animated Pill Style
       ========================================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: rgba(10, 15, 30, 0.7);
        border-radius: var(--radius-md);
        padding: 4px;
        border: 1px solid rgba(255,255,255,0.04);
        backdrop-filter: blur(12px);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm);
        padding: 12px 18px;
        font-size: 14px;
        font-weight: 600;
        color: var(--text-secondary);
        min-height: 46px;
        transition: var(--transition-smooth);
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary);
        background: rgba(99, 102, 241, 0.06);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(139,92,246,0.1)) !important;
        color: #c4b5fd !important;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.1), inset 0 0 0 1px rgba(99,102,241,0.15);
    }
    .stTabs [data-baseweb="tab-border"] { display: none; }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }

    /* ==========================================
       EXPANDER
       ========================================== */
    .streamlit-expanderHeader {
        font-size: 15px;
        font-weight: 700;
        border-radius: var(--radius-md);
    }
    /* Hide broken material icon text in expanders (Streamlit 1.37+) */
    [data-testid="stExpander"] summary span[data-testid="stMarkdownContainer"] + span {
        font-size: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
    }
    /* Hide raw material icon text globally (arrow_downward, double_arrow_right, etc) */
    .st-emotion-cache-material-icon,
    span[class*="material"] {
        font-size: 0 !important;
    }

    /* ==========================================
       SIDEBAR — Premium Dark Glass
       ========================================== */
    section[data-testid="stSidebar"] {
        background: rgba(5, 8, 18, 0.97) !important;
        backdrop-filter: blur(30px) saturate(150%);
        -webkit-backdrop-filter: blur(30px) saturate(150%);
        border-right: 1px solid rgba(99, 102, 241, 0.06);
    }
    section[data-testid="stSidebar"] .stButton > button {
        border-radius: var(--radius-sm) !important;
        font-size: 14px;
        text-align: left;
        transition: var(--transition-smooth);
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        transform: translateX(4px);
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        box-shadow: 0 0 20px rgba(99,102,241,0.15);
    }

    /* --- Nav Links --- */
    .nav-link {
        display: block;
        padding: 10px 14px;
        margin: 3px 0;
        border-radius: var(--radius-sm);
        color: var(--text-primary) !important;
        text-decoration: none !important;
        transition: var(--transition-smooth);
        font-size: 14px;
    }
    .nav-link:hover { background: rgba(99, 102, 241, 0.1); }
    .nav-link.active {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white !important;
        box-shadow: 0 4px 16px rgba(99,102,241,0.25);
    }

    /* ==========================================
       EMPTY STATE
       ========================================== */
    .empty-state {
        text-align: center;
        padding: 48px 24px;
        color: var(--text-secondary);
    }
    .empty-state .empty-icon {
        font-size: 56px;
        margin-bottom: 16px;
        opacity: 0.4;
        animation: logoFloat 4s ease-in-out infinite;
    }
    .empty-state p {
        font-size: 14px;
        line-height: 1.7;
    }

    /* ==========================================
       INFO BANNER
       ========================================== */
    .info-banner {
        background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(34,211,238,0.04));
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: var(--radius-md);
        padding: 16px 18px;
        margin: 12px 0;
        backdrop-filter: blur(12px);
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
        background: linear-gradient(135deg, rgba(245,158,11,0.06), rgba(244,63,94,0.03));
        border: 1px solid rgba(245, 158, 11, 0.15);
        border-radius: var(--radius-md);
        padding: 18px;
        margin-top: 16px;
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .setup-warning-icon { font-size: 24px; }
    .setup-warning-text {
        color: #fbbf24;
        font-size: 14px;
        font-weight: 700;
    }

    /* ==========================================
       STEP PANELS — Wizard Flow
       ========================================== */
    .step-panel {
        background: var(--bg-card);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: var(--radius-lg);
        padding: 20px 22px;
        margin: 14px 0;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(16px);
    }
    .step-panel::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 3px; height: 100%;
        background: var(--gradient-neon);
    }
    .step-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 14px;
    }
    .step-number {
        width: 30px; height: 30px;
        border-radius: 50%;
        background: var(--gradient-main);
        color: white;
        font-size: 13px;
        font-weight: 900;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(99,102,241,0.25);
    }
    .step-title {
        color: var(--text-primary);
        font-size: 15px;
        font-weight: 700;
    }
    .step-subtitle {
        color: var(--text-secondary);
        font-size: 12px;
        margin-left: auto;
    }

    /* --- Settings Panel --- */
    .settings-panel {
        background: rgba(10, 15, 30, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: var(--radius-md);
        padding: 16px 18px;
        margin: 8px 0;
    }
    .settings-panel-title {
        color: var(--text-secondary);
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 10px;
    }

    /* --- Selection Preview --- */
    .selection-preview {
        background: rgba(99, 102, 241, 0.05);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: var(--radius-sm);
        padding: 12px 16px;
        margin-top: 8px;
    }
    .selection-preview .sel-label {
        color: #a5b4fc;
        font-size: 11px;
        font-weight: 700;
    }
    .selection-preview .sel-desc {
        color: var(--text-secondary);
        font-size: 12px;
        margin-top: 3px;
    }

    /* --- Result Actions --- */
    .result-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
    }

    /* --- Style Cards --- */
    .style-card {
        background: var(--bg-card);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: var(--radius-md);
        padding: 14px;
        margin: 6px 0;
        cursor: pointer;
        transition: var(--transition-smooth);
    }
    .style-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        background: rgba(99, 102, 241, 0.05);
        transform: translateY(-2px);
    }
    .style-card.active {
        border-color: var(--accent-primary);
        background: rgba(99, 102, 241, 0.08);
        box-shadow: 0 0 24px rgba(99, 102, 241, 0.1);
    }

    /* ==========================================
       METRICS - Override default
       ========================================== */
    [data-testid="stMetricValue"] { color: var(--text-primary) !important; }
    [data-testid="stMetricLabel"] { color: var(--text-secondary) !important; }

    /* ==========================================
       LOGIN PAGE — Premium Glass
       ========================================== */
    .login-container {
        max-width: 380px;
        margin: 60px auto 0;
        padding: 36px 28px;
        background: var(--bg-card);
        backdrop-filter: blur(30px) saturate(150%);
        -webkit-backdrop-filter: blur(30px) saturate(150%);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: var(--radius-xl);
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: var(--shadow-elevated);
    }
    .login-container::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--gradient-neon);
    }
    .login-container::after {
        content: '';
        position: absolute;
        top: -100px; right: -100px;
        width: 250px; height: 250px;
        background: radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 60%);
        border-radius: 50%;
        animation: floatOrb 8s ease-in-out infinite;
    }
    .login-logo {
        font-size: 64px;
        display: block;
        margin-bottom: 14px;
        filter: drop-shadow(0 4px 20px rgba(99,102,241,0.5));
        animation: logoFloat 4s ease-in-out infinite;
        position: relative;
        z-index: 1;
    }
    .login-title {
        font-size: 24px;
        font-weight: 900;
        color: var(--text-primary);
        margin-bottom: 6px;
        letter-spacing: -0.03em;
        position: relative;
        z-index: 1;
    }
    .login-subtitle {
        color: var(--text-secondary);
        font-size: 13px;
        margin-bottom: 28px;
        position: relative;
        z-index: 1;
    }

    /* ==========================================
       ALERTS
       ========================================== */
    .stAlert { border-radius: var(--radius-md) !important; }

    /* ==========================================
       SCROLLBAR — Theme-matched
       ========================================== */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(99, 102, 241, 0.15);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(99, 102, 241, 0.3);
    }

    /* Global touch polish */
    * { -webkit-tap-highlight-color: transparent; }

    /* ==========================================
       RESPONSIVE — Tablet
       ========================================== */
    @media (min-width: 640px) {
        .block-container { padding: 1rem 2rem 2rem 2rem !important; }
        .hero-title { font-size: 38px; }
        .hero-section { padding: 44px 24px 36px; }
        .stat-number { font-size: 32px; }
        .main-header h1 { font-size: 30px; }
    }

    /* Desktop */
    @media (min-width: 1024px) {
        .block-container { padding: 1rem 3rem 2rem 3rem !important; }
        .hero-title { font-size: 44px; }
        .main-header h1 { font-size: 34px; }
    }

    /* ==========================================
       MOBILE — Premium App Feel
       ========================================== */
    @media (max-width: 639px) {
        html, body, [data-testid="stAppViewContainer"] {
            scroll-behavior: smooth;
            -webkit-overflow-scrolling: touch;
        }

        section[data-testid="stSidebar"] {
            z-index: 99998 !important;
            box-shadow: 4px 0 50px rgba(0, 0, 0, 0.7) !important;
            border-right: 1px solid rgba(99,102,241,0.1) !important;
            min-width: 260px !important;
            width: 75vw !important;
            max-width: 320px !important;
        }
        section[data-testid="stSidebar"] .stButton > button {
            min-height: 52px !important;
            font-size: 16px !important;
            padding: 12px 16px !important;
            border-radius: 14px !important;
            margin-bottom: 6px !important;
        }

        button[data-testid="stSidebarCollapsedControl"] {
            z-index: 99997 !important;
            background: rgba(10, 15, 30, 0.9) !important;
            backdrop-filter: blur(24px) !important;
            -webkit-backdrop-filter: blur(24px) !important;
            border: 1px solid rgba(99,102,241,0.15) !important;
            border-radius: 14px !important;
            width: 48px !important;
            height: 48px !important;
            box-shadow: 0 4px 24px rgba(0,0,0,0.4), 0 0 0 1px rgba(99,102,241,0.08) !important;
            transition: var(--transition-smooth);
        }
        button[data-testid="stSidebarCollapsedControl"]:active {
            transform: scale(0.9) !important;
            background: rgba(99,102,241,0.15) !important;
        }

        .block-container { padding: 0.5rem 1rem 1.5rem 1rem !important; }

        .stButton > button {
            width: 100%;
            min-height: 48px;
            margin-bottom: 4px;
            font-size: 14px !important;
        }

        .main-header { padding: 4px 0 12px 0; }
        .main-header h1 { font-size: 22px; }

        .hero-section {
            padding: 28px 16px 24px;
            margin: -4px -4px 16px -4px;
            border-radius: 0 0 24px 24px;
        }
        .hero-logo { font-size: 48px; }
        .hero-title { font-size: 26px; }
        .hero-subtitle { font-size: 11px; letter-spacing: 0.15em; }

        [data-testid="column"] { padding: 0 3px !important; }

        .stTabs [data-baseweb="tab-list"] { border-radius: 14px; padding: 3px; }
        .stTabs [data-baseweb="tab"] {
            font-size: 12px; padding: 10px 12px;
            border-radius: 12px; min-height: 42px;
        }

        .stat-box { padding: 16px 10px; border-radius: 16px; }
        .stat-number { font-size: 26px; }
        .stat-label { font-size: 10px; }

        .action-card {
            padding: 20px 12px 16px; min-height: 110px; border-radius: 18px;
        }
        .action-card:active { transform: scale(0.97); transition-duration: 0.1s; }
        .action-icon { font-size: 32px; margin-bottom: 8px; }
        .action-title { font-size: 13px; }
        .action-desc { font-size: 11px; }

        .tweet-card {
            padding: 16px; margin: 8px 0; border-radius: 16px;
        }
        .tweet-card:active { background: rgba(15, 22, 45, 0.9); }
        .tweet-metrics { gap: 12px; font-size: 12px; }

        .generated-tweet { padding: 18px; font-size: 15px; line-height: 1.65; border-radius: 16px; }

        .activity-item { padding: 14px; border-radius: 14px; }

        .stTextInput input, .stTextArea textarea {
            font-size: 16px !important;
            border-radius: 14px !important;
            min-height: 48px;
        }
        .stSelectbox > div > div { min-height: 48px !important; }

        .info-banner { border-radius: 16px; padding: 16px; }
        .setup-warning { border-radius: 16px; }

        .element-container { margin-bottom: 4px; }

        .streamlit-expanderHeader {
            font-size: 14px; padding: 14px 16px; border-radius: 14px;
        }

        .step-panel { padding: 14px 16px; margin: 8px 0; }
        .step-number { width: 26px; height: 26px; font-size: 11px; }
        .step-title { font-size: 14px; }
        .settings-panel { padding: 12px; }

        .login-container { margin: 30px auto 0; border-radius: 24px; }
    }

    /* Small phones */
    @media (max-width: 380px) {
        .block-container { padding: 0.5rem 0.5rem 90px 0.5rem !important; }
        .hero-title { font-size: 22px; }
        .hero-section { padding: 22px 12px 18px; }
        .stTabs [data-baseweb="tab"] { font-size: 11px; padding: 8px 6px; }
        .stat-number { font-size: 22px; }
    }

    </style>
    """, unsafe_allow_html=True)


def render_step_header(number: int, title: str, subtitle: str = ""):
    """Render a numbered step header inside a step panel."""
    sub_html = f'<span class="step-subtitle">{subtitle}</span>' if subtitle else ''
    st.markdown(f"""
    <div class="step-header">
        <span class="step-number">{number}</span>
        <span class="step-title">{title}</span>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def render_research_engine_toggle(key_suffix: str = "") -> str:
    """Render research engine toggle (Standard vs Grok).
    Returns "standard" or "grok"."""
    from modules.grok_client import has_grok_key

    if not has_grok_key():
        return "standard"

    engine = st.radio(
        "Arastirma Motoru",
        options=["standard", "grok"],
        format_func=lambda x: "Standart (DuckDuckGo)" if x == "standard"
                              else "Grok AI (X + Web)",
        index=0,
        key=f"research_engine_{key_suffix}",
        horizontal=True,
        help="Grok: X verilerine dogrudan erisim, gercek zamanli arama. Standart: DuckDuckGo ucretsiz arama."
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
            "AI Otonom Arastirma",
            value=False,
            key=f"use_agentic_{key_suffix}",
            help="AI modeli kendi basina DuckDuckGo'da gezinerek arastirma yapar.",
        )

    with col_ag2:
        if _has_grok:
            use_grok_agentic = st.checkbox(
                "Grok Otonom Arastirma",
                value=False,
                key=f"use_grok_agentic_{key_suffix}",
                help="Grok modeli X'te ve web'de kendi basina gezinerek arastirma yapar. "
                     "X verilerine dogrudan erisim avantaji.",
            )
        else:
            use_grok_agentic = False

    # Mutual exclusive: if both selected, last one wins
    if use_standard_agentic and use_grok_agentic:
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
        <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.15);
                    border-radius:12px; padding:10px 14px; margin:4px 0;">
            <div style="color:#a5b4fc; font-size:11px; font-weight:bold;">Grok Kullanim</div>
            <div style="color:#f1f5f9; font-size:13px;">${cost:.3f} | {calls} cagri</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Sifirla", key="grok_cost_reset", type="secondary"):
            from modules.grok_client import reset_grok_cost
            reset_grok_cost()
            st.rerun()


def render_sidebar_nav(current_page: str = ""):
    """Render sidebar navigation."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 12px 0 16px;">
            <span style="font-size: 32px; filter: drop-shadow(0 4px 12px rgba(99,102,241,0.4));">🤖</span>
            <div style="font-size: 17px; font-weight: 900; color: #f1f5f9; margin-top: 6px;
                        letter-spacing: -0.03em;
                        background: linear-gradient(135deg, #f1f5f9, #a5b4fc);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;">X AI Otomasyon</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        pages = [
            ("Ana Sayfa", "streamlit_app.py", "home"),
            ("Tara", "pages/1_🔍_Tara.py", "tara"),
            ("Yaz", "pages/2_✍️_Yaz.py", "yaz"),
            ("Icerik", "pages/6_💡_İçerik.py", "icerik"),
            ("Analiz", "pages/4_📊_Analiz.py", "analiz"),
            ("Ayarlar", "pages/3_⚙️_Ayarlar.py", "ayarlar"),
            ("Takvim", "pages/7_📅_Takvim.py", "takvim"),
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
            st.success("Twitter API", icon="🐦")
        else:
            st.warning("Twitter API eksik", icon="⚠️")

        if has_ai:
            st.success("AI API", icon="🧠")
        else:
            st.warning("AI API eksik", icon="⚠️")

        has_grok = bool(get_secret("xai_api_key", ""))
        if has_grok:
            st.success("Grok API", icon="🧠")
            render_grok_cost_indicator()



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
        rel_text = "Yuksek"
    elif topic.relevance_score >= 30:
        rel_class = "relevance-medium"
        rel_text = "Orta"
    else:
        rel_class = "relevance-low"
        rel_text = "Dusuk"

    # Content summary
    content_summary = getattr(topic, 'content_summary', '') or ''
    summary_html = ""
    if content_summary:
        summary_html = f"""
        <div style="background:rgba(99, 102, 241, 0.05); border-left:3px solid #6366f1; padding:6px 10px;
                    margin:8px 0; border-radius:0 8px 8px 0;">
            <span style="color:#a5b4fc; font-size:11px; font-weight:600;">Icerik:</span>
            <span style="color:#94a3b8; font-size:12px; margin-left:4px;">{content_summary}</span>
        </div>"""

    # Follower count display
    followers = getattr(topic, 'author_followers_count', 0) or 0
    followers_html = ""
    if followers > 0:
        followers_html = f'<span style="color:#64748b; font-size:11px; margin-left:6px;">| {_format_number(followers)}</span>'

    # Total engagement
    total_eng = topic.like_count + topic.retweet_count + topic.reply_count
    total_eng_html = f'<span style="color:#fbbf24; font-size:12px; font-weight:600;">{_format_number(total_eng)}</span>'

    # Media indicator
    media_urls = getattr(topic, 'media_urls', []) or []
    media_html = ""
    if media_urls:
        media_count = len(media_urls)
        media_html = f'<span style="color:#10b981; font-size:11px; margin-left:6px;">{media_count} medya</span>'

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
        <div class="tweet-text">{topic.text[:500]}{'...' if len(topic.text) > 500 else ''}</div>
        <div class="tweet-metrics">
            <span>❤️ {_format_number(topic.like_count)}</span>
            <span>🔁 {_format_number(topic.retweet_count)}</span>
            <span>💬 {_format_number(topic.reply_count)}</span>
            <span>{total_eng_html}</span>
            <span class="tweet-time">{time_and_date}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if show_select:
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(f"Bu konuyu sec", key=f"{key_prefix}select_{topic.tweet_id}",
                         use_container_width=True, type="primary"):
                st.session_state.selected_topic = {
                    "text": topic.text,
                    "url": f"https://x.com/{topic.author_username}/status/{topic.tweet_id}",
                    "author": topic.author_username,
                    "id": topic.tweet_id,
                    "media_urls": media_urls,
                }
                st.session_state.write_mode = "normal"
                st.switch_page("pages/2_✍️_Yaz.py")


def render_generated_tweet(text: str):
    """Render a generated tweet preview"""
    char_count = len(text)
    st.markdown(f"""
    <div class="generated-tweet">
        {text}
    </div>
    <div style="text-align:right; color:#475569; font-size:13px; margin-top:4px;">
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
    """Render media search results as a visual grid with download links."""
    if not media_result or not media_result.has_results:
        st.info("Bu konu icin gorsel bulunamadi.")
        return

    # --- Images ---
    if media_result.images:
        st.markdown(f"""
        <div style="color:#a5b4fc; font-weight:bold; font-size:14px; margin:12px 0 8px 0;">
            Onerilen Gorseller ({len(media_result.images)})
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(min(len(media_result.images), 4))
        for i, img in enumerate(media_result.images):
            with cols[i % len(cols)]:
                try:
                    st.image(img.thumbnail_url or img.url, use_container_width=True)
                except Exception:
                    st.markdown(f"""
                    <div style="background:var(--bg-card); border:1px dashed rgba(255,255,255,0.1);
                                border-radius:8px; padding:20px; text-align:center; color:#64748b;">
                        Gorsel yuklenemedi
                    </div>
                    """, unsafe_allow_html=True)

                source_label = f"@{img.source_author}" if img.source_author else img.source
                st.caption(f"{source_label}")

                if img.url:
                    st.markdown(
                        f'<a href="{img.url}" target="_blank" style="color:#6366f1; font-size:12px; '
                        f'text-decoration:none; font-weight:600;">Ac &rarr;</a>',
                        unsafe_allow_html=True
                    )

    # --- Videos ---
    if media_result.videos:
        st.markdown(f"""
        <div style="color:#22d3ee; font-weight:bold; font-size:14px; margin:16px 0 8px 0;">
            Onerilen Videolar ({len(media_result.videos)})
        </div>
        """, unsafe_allow_html=True)

        for vid in media_result.videos:
            source_label = f"@{vid.source_author}" if vid.source_author else vid.source
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                <div style="background:var(--bg-card); border:1px solid rgba(255,255,255,0.04);
                            border-radius:12px; padding:12px 14px;">
                    <span style="color:#22d3ee; font-weight:bold;">Video</span>
                    <span style="color:#94a3b8; margin-left:8px;">{source_label}</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if vid.url:
                    st.markdown(
                        f'<a href="{vid.url}" target="_blank" style="color:#22d3ee; font-size:13px; '
                        f'text-decoration:none; font-weight:600;">Izle &rarr;</a>',
                        unsafe_allow_html=True
                    )


def render_media_source_selector(key_suffix: str = "") -> str:
    """Render a selector for media search source."""
    options = {
        "x": "Sadece X",
        "all": "X + Web (Onerilen)",
        "web": "Sadece Web",
    }
    selected = st.selectbox(
        "Gorsel Kaynagi",
        options=list(options.keys()),
        format_func=lambda x: options[x],
        index=1,
        key=f"media_source_{key_suffix}",
    )
    return selected


def render_image_analysis(analysis_text: str, image_url: str = ""):
    """Render the result of AI image analysis."""
    if not analysis_text:
        return

    st.markdown(f"""
    <div style="background:rgba(99,102,241,0.05); border:1px solid rgba(99,102,241,0.12);
                border-radius:14px; padding:16px; margin:8px 0;">
        <div style="color:#a5b4fc; font-weight:bold; font-size:13px; margin-bottom:8px;">
            Gorsel Analizi
        </div>
        <div style="color:#e2e8f0; font-size:13px; line-height:1.65;">
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
        <div class="login-subtitle">Twitter/X AI Icerik Otomasyon Paneli</div>
    </div>
    """, unsafe_allow_html=True)

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Sifre", type="password", key="login_password",
                                 label_visibility="collapsed", placeholder="Sifrenizi girin...")

        if st.button("Giris Yap", type="primary", use_container_width=True):
            correct_password = get_secret("app_password", "admin123")
            if password == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Yanlis sifre!")

    return False
