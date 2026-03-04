"""
📅 Posting Takvimi — Günlük Paylaşım Planı & Log
X algoritmasını optimize eden zamanlama stratejisi
"""
import streamlit as st
import datetime
from modules.ui_components import inject_custom_css, check_password, render_sidebar_nav
from modules.style_manager import (
    load_posting_log, log_scheduled_post,
    load_daily_checklist, save_daily_checklist,
    load_post_history,
)

# Page config
st.set_page_config(page_title="Posting Takvimi", page_icon="📅", layout="wide", initial_sidebar_state="auto")
inject_custom_css()
if not check_password():
    st.stop()
render_sidebar_nav(current_page="takvim")

# --- Constants ---
WEEKDAY_SLOTS = [
    {"time": "09:00", "label": "Sabah", "icon": "☀️", "type": "Değer / Eğitim / Meme",
     "desc": "İlk post'un reach'i tüm gün en yüksek kalır. Grok ranking ilk 60dk'yı ağır tartar."},
    {"time": "13:00", "label": "Öğle", "icon": "🍽️", "type": "Soru / Poll",
     "desc": "Türk lunch + global overlap (13-17 arası Türk kaynaklarında zirve)."},
    {"time": "17:00", "label": "İş Çıkışı", "icon": "🚶", "type": "Opinion (kısa & punchy)",
     "desc": "Commute saati, telefon elde. Reply oranı +%40."},
    {"time": "21:00", "label": "Akşam", "icon": "🌙", "type": "Conversation Starter / Video",
     "desc": "En yüksek 'unregretted user-seconds'. Uzun scroll, bookmark, video izleme."},
]

WEEKEND_SLOTS = [
    {"time": "10:00", "label": "Sabah", "icon": "☀️", "type": "Değer / Eğitim / Meme",
     "desc": "Hafta sonu insanlar geç uyanıyor, 1 saat kaydırıldı."},
    {"time": "13:30", "label": "Öğle", "icon": "🍽️", "type": "Soru / Poll",
     "desc": "Brunch sonrası scroll zamanı."},
    {"time": "17:30", "label": "Akşamüstü", "icon": "🌅", "type": "Opinion (kısa & punchy)",
     "desc": "Hafta sonu akşamüstü daha rahat engagement."},
    {"time": "21:30", "label": "Akşam", "icon": "🌙", "type": "Conversation Starter / Video",
     "desc": "Hafta sonu akşam en uzun scroll süreleri."},
]

ALGORITHM_CHECKLIST = [
    {"key": "native_media", "label": "Her posta native medya koy (foto/GIF/video/poll)", "impact": "+%50-90 reach"},
    {"key": "self_reply", "label": "Attıktan sonra kendi postuna soruyla reply at", "impact": "Phoenix ranking boost"},
    {"key": "early_engage", "label": "İlk 5-10 yorumu 30dk içinde cevapla", "impact": "Erken engagement sinyali"},
    {"key": "no_external_link", "label": "External link varsa 1. reply'e koy, ana postta olmasın", "impact": "Link cezası önleme"},
    {"key": "diversify", "label": "Post türlerini çeşitlendir (aynı türden ceza gelir)", "impact": "Diversity bonus"},
    {"key": "check_analytics", "label": "X Analytics: Impressions & Profile visits kontrol", "impact": "Zamanlama optimizasyonu"},
]

POST_TYPES = ["Değer / Eğitim", "Meme / Eğlence", "Soru / Poll", "Opinion (kısa)", "Conversation Starter", "Video / Görsel", "Thread", "Quote Tweet"]


def get_today_slots() -> list[dict]:
    """Get posting slots for today (weekday vs weekend)"""
    today = datetime.datetime.now()
    if today.weekday() >= 5:  # Saturday=5, Sunday=6
        return WEEKEND_SLOTS
    return WEEKDAY_SLOTS


def get_slot_datetime(slot_time: str) -> datetime.datetime:
    """Convert slot time string to today's datetime"""
    now = datetime.datetime.now()
    hour, minute = map(int, slot_time.split(":"))
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def get_next_slot(slots: list[dict]) -> tuple[dict | None, datetime.timedelta | None]:
    """Find the next upcoming slot and time remaining"""
    now = datetime.datetime.now()
    for slot in slots:
        slot_dt = get_slot_datetime(slot["time"])
        if slot_dt > now:
            return slot, slot_dt - now
    return None, None


def get_today_logs(posting_log: list[dict]) -> list[dict]:
    """Filter posting log for today only"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    return [entry for entry in posting_log if entry.get("date") == today]


def get_week_logs(posting_log: list[dict]) -> list[dict]:
    """Filter posting log for this week"""
    today = datetime.datetime.now()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_start_str = week_start.strftime("%Y-%m-%d")
    return [entry for entry in posting_log if entry.get("date", "") >= week_start_str]


def format_timedelta(td: datetime.timedelta) -> str:
    """Format timedelta to human-readable Turkish string"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours > 0:
        return f"{hours} saat {minutes} dk"
    return f"{minutes} dk"


# --- Header ---
st.markdown("""
<div class="hero-section">
    <span class="hero-logo">📅</span>
    <div class="hero-title">Posting Takvimi</div>
    <div class="hero-subtitle">Günlük 4 Post &middot; Algoritma Optimizasyonu</div>
</div>
""", unsafe_allow_html=True)

# --- Load data ---
posting_log = load_posting_log()
today_logs = get_today_logs(posting_log)
today_slots = get_today_slots()
next_slot, time_remaining = get_next_slot(today_slots)
today_str = datetime.datetime.now().strftime("%Y-%m-%d")
is_weekend = datetime.datetime.now().weekday() >= 5
checklist = load_daily_checklist()

# --- Top Stats ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{len(today_logs)}/4</div>
        <div class="stat-label">Bugün Paylaşılan</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    if next_slot and time_remaining:
        countdown = format_timedelta(time_remaining)
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{countdown}</div>
            <div class="stat-label">Sonraki Post: {next_slot['time']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">✅</div>
            <div class="stat-label">Bugün Tamamlandı</div>
        </div>
        """, unsafe_allow_html=True)
with col3:
    week_logs = get_week_logs(posting_log)
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{len(week_logs)}/28</div>
        <div class="stat-label">Bu Hafta</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    checklist_done = sum(1 for item in ALGORITHM_CHECKLIST if checklist.get(item["key"], False))
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{checklist_done}/{len(ALGORITHM_CHECKLIST)}</div>
        <div class="stat-label">Checklist</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- Today's Schedule ---
day_label = "Hafta Sonu" if is_weekend else "Hafta İçi"
day_name = datetime.datetime.now().strftime("%A")
day_names_tr = {"Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba",
                "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi", "Sunday": "Pazar"}
day_name_tr = day_names_tr.get(day_name, day_name)

st.markdown(f"""
<div class="section-header">
    <h3>📅 Bugünkü Plan — {day_name_tr} ({day_label})</h3>
    <span class="section-badge">3.5-4 saat arayla</span>
</div>
""", unsafe_allow_html=True)

logged_slots = {entry["slot_time"] for entry in today_logs}

for i, slot in enumerate(today_slots):
    slot_dt = get_slot_datetime(slot["time"])
    now = datetime.datetime.now()
    is_posted = slot["time"] in logged_slots
    is_current = not is_posted and slot_dt <= now and (
        i == len(today_slots) - 1 or get_slot_datetime(today_slots[i + 1]["time"]) > now
    )
    is_upcoming = not is_posted and slot_dt > now

    # Status indicator
    if is_posted:
        status_color = "#22c55e"
        status_icon = "✅"
        status_text = "Paylaşıldı"
    elif is_current:
        status_color = "#f59e0b"
        status_icon = "🔴"
        status_text = "ŞİMDİ PAYLAŞ!"
    else:
        status_color = "#64748b"
        status_icon = "⏳"
        if time_remaining and slot == next_slot:
            status_text = f"{format_timedelta(time_remaining)} kaldı"
        else:
            status_text = "Bekliyor"

    # Find the log entry for this slot if posted
    slot_log = next((entry for entry in today_logs if entry["slot_time"] == slot["time"]), None)

    st.markdown(f"""
    <div class="glass-card" style="border-left: 4px solid {status_color}; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div>
                <span style="font-size: 24px;">{slot['icon']}</span>
                <strong style="font-size: 18px; margin-left: 8px;">{slot['time']}</strong>
                <span style="color: var(--text-secondary); margin-left: 8px;">— {slot['label']}</span>
            </div>
            <div>
                <span style="color: {status_color}; font-weight: 600;">{status_icon} {status_text}</span>
            </div>
        </div>
        <div style="margin-top: 8px;">
            <span style="background: rgba(99, 102, 241, 0.2); padding: 4px 12px; border-radius: 20px; font-size: 13px; color: #a5b4fc;">
                🎯 Önerilen tür: {slot['type']}
            </span>
        </div>
        <div style="margin-top: 6px; font-size: 13px; color: var(--text-muted);">
            💡 {slot['desc']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Log form for unposted slots
    if not is_posted:
        with st.expander(f"📝 {slot['time']} — Paylaşım Kaydet", expanded=is_current):
            col_a, col_b = st.columns(2)
            with col_a:
                post_type = st.selectbox(
                    "Post Türü",
                    POST_TYPES,
                    key=f"type_{slot['time']}",
                    index=min(i, len(POST_TYPES) - 1),
                )
            with col_b:
                has_media = st.checkbox("Medya var mı?", key=f"media_{slot['time']}", value=True)
                self_reply = st.checkbox("Self-reply attın mı?", key=f"reply_{slot['time']}")

            content = st.text_area(
                "Tweet içeriği (opsiyonel — kayıt için)",
                key=f"content_{slot['time']}",
                height=80,
                placeholder="Tweet'ini buraya yapıştır veya boş bırak...",
            )
            tweet_url = st.text_input(
                "Tweet URL (opsiyonel)",
                key=f"url_{slot['time']}",
                placeholder="https://x.com/...",
            )

            if st.button(f"✅ {slot['time']} Paylaşımını Kaydet", key=f"log_{slot['time']}", type="primary", use_container_width=True):
                log_scheduled_post(
                    slot_time=slot["time"],
                    post_type=post_type,
                    content=content,
                    has_media=has_media,
                    self_reply=self_reply,
                    tweet_url=tweet_url,
                )
                st.success(f"✅ {slot['time']} slotu kaydedildi!")
                st.rerun()
    else:
        # Show logged details
        if slot_log:
            details = []
            if slot_log.get("post_type"):
                details.append(f"📌 {slot_log['post_type']}")
            if slot_log.get("has_media"):
                details.append("🖼️ Medya var")
            if slot_log.get("self_reply"):
                details.append("💬 Self-reply atıldı")
            if slot_log.get("content"):
                details.append(f"📝 {slot_log['content'][:100]}...")
            if slot_log.get("tweet_url"):
                details.append(f"[🔗 Tweet'i gör]({slot_log['tweet_url']})")
            if details:
                st.caption(" · ".join(details))

st.markdown("---")

# --- Algorithm Checklist ---
st.markdown("""
<div class="section-header">
    <h3>🚀 Günlük Algoritma Checklist</h3>
    <span class="section-badge">Her gün uygula</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="glass-card">
    <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">
        Bu maddeleri her gün uygulamak reach'ini 2-4x artırır. X Premium'san etkisi daha da fazla.
    </div>
</div>
""", unsafe_allow_html=True)

checklist_changed = False
for item in ALGORITHM_CHECKLIST:
    current_val = checklist.get(item["key"], False)
    new_val = st.checkbox(
        f"{item['label']}  —  _{item['impact']}_",
        value=current_val,
        key=f"check_{item['key']}",
    )
    if new_val != current_val:
        checklist[item["key"]] = new_val
        checklist_changed = True

if checklist_changed:
    save_daily_checklist(checklist)

st.markdown("---")

# --- Weekly Summary ---
st.markdown("""
<div class="section-header">
    <h3>📊 Haftalık Özet</h3>
</div>
""", unsafe_allow_html=True)

week_logs = get_week_logs(posting_log)
if week_logs:
    # Posts per day this week
    days_data = {}
    for entry in week_logs:
        day = entry.get("date", "")
        if day not in days_data:
            days_data[day] = {"count": 0, "types": [], "media_count": 0, "self_reply_count": 0}
        days_data[day]["count"] += 1
        if entry.get("post_type"):
            days_data[day]["types"].append(entry["post_type"])
        if entry.get("has_media"):
            days_data[day]["media_count"] += 1
        if entry.get("self_reply"):
            days_data[day]["self_reply_count"] += 1

    col1, col2, col3 = st.columns(3)
    with col1:
        total_posts = len(week_logs)
        media_posts = sum(1 for e in week_logs if e.get("has_media"))
        media_pct = int((media_posts / total_posts * 100)) if total_posts > 0 else 0
        st.metric("Toplam Post", total_posts)
        st.metric("Medya Oranı", f"%{media_pct}")
    with col2:
        reply_posts = sum(1 for e in week_logs if e.get("self_reply"))
        reply_pct = int((reply_posts / total_posts * 100)) if total_posts > 0 else 0
        st.metric("Self-Reply Oranı", f"%{reply_pct}")
        active_days = len(days_data)
        st.metric("Aktif Gün", f"{active_days}/7")
    with col3:
        # Type distribution
        all_types = [e.get("post_type", "Bilinmeyen") for e in week_logs]
        if all_types:
            from collections import Counter
            type_counts = Counter(all_types)
            most_common = type_counts.most_common(3)
            st.markdown("**En Çok Tür:**")
            for t, c in most_common:
                st.caption(f"• {t}: {c}x")

    # Day by day breakdown
    st.markdown("**Günlük Dağılım:**")
    for day in sorted(days_data.keys(), reverse=True):
        d = days_data[day]
        day_dt = datetime.datetime.strptime(day, "%Y-%m-%d")
        day_name = day_names_tr.get(day_dt.strftime("%A"), day_dt.strftime("%A"))
        icons = "🟢" * d["count"] + "⚫" * (4 - d["count"])
        st.caption(f"{day} ({day_name}): {icons}  — {d['count']}/4 post, {d['media_count']} medya, {d['self_reply_count']} reply")
else:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📅</div>
        <p>Henüz bu hafta paylaşım kaydı yok.<br>
        Yukarıdan ilk paylaşımını kaydet!</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- Post History Log ---
st.markdown("""
<div class="section-header">
    <h3>📜 Son Paylaşım Kayıtları</h3>
</div>
""", unsafe_allow_html=True)

if posting_log:
    show_count = st.slider("Gösterilecek kayıt", 5, 50, 10, key="log_count")
    for entry in posting_log[:show_count]:
        date = entry.get("date", "")
        slot = entry.get("slot_time", "")
        ptype = entry.get("post_type", "")
        content = entry.get("content", "")
        has_m = "🖼️" if entry.get("has_media") else ""
        has_r = "💬" if entry.get("self_reply") else ""
        url = entry.get("tweet_url", "")

        content_preview = f" — {content[:80]}..." if content else ""
        url_link = f" [🔗]({url})" if url else ""

        st.caption(f"**{date} {slot}** | {ptype} {has_m} {has_r}{content_preview}{url_link}")
else:
    st.caption("Henüz kayıt yok.")

# --- Strategy Tips (collapsible) ---
with st.expander("📚 Posting Stratejisi Detayları"):
    st.markdown("""
    ### Neden Bu Saatler?

    **Her post arası 3.5-4 saat** → Her biri kendi "ilk 30-60dk erken engagement"
    penceresini alır. Recency decay'e takılmaz, diversity cezası yemez.

    | Saat | Neden |
    |------|-------|
    | **09:00** (Hİ) / **10:00** (HS) | İlk post'un reach'i tüm gün en yüksek. Grok ranking ilk 60dk'yı çok ağır tartar. |
    | **13:00** (Hİ) / **13:30** (HS) | Türk lunch + global overlap. 13-17 arası Türk kaynaklarında zirve. |
    | **17:00** (Hİ) / **17:30** (HS) | İş çıkışı commute. İnsanlar telefon elinde, reply oranı +%40. |
    | **21:00** (Hİ) / **21:30** (HS) | Akşam en yüksek "unregretted user-seconds". Uzun scroll, bookmark, video. |

    ### Algoritma Takviyesi

    1. **Native medya** koy (foto/GIF/video/poll/carousel) → reach +%50-90
    2. **Self-reply**: Attıktan hemen sonra kendi postuna soruyla reply at → Phoenix ranking seni yukarı iter
    3. **Erken engagement**: İlk 5-10 yorumu 30dk içinde cevapla
    4. **Post türlerini çeşitlendir**: Algoritma aynı türden sıkılırsa cezalandırır
    5. **External link** varsa 1. reply'e koy, ana postta olmasın
    6. **X Analytics**'ten Impressions ve Profile visits'i haftalık kontrol et

    ### Post Tür Rotasyonu (Önerilen)
    - Post 1 → Değer/meme/eğitim
    - Post 2 → Soru/poll
    - Post 3 → Opinion (kısa ve punchy)
    - Post 4 → Conversation starter veya kısa video

    > **X Premium'san** bu saatlerde 2-4x daha fazla kişi görür.
    """)
