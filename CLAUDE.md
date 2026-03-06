# CLAUDE.md -- Proje Kurallari ve Sistem Bellegi

## Gelistirme Sureci

1. **Herhangi bir kod yazmadan once yaklasimini acikla ve onay bekle.** Dogrudan implementasyona gecme, once plani sun.
2. **Once aciklayici sorular sor.** Belirsiz veya eksik noktalari netlestirmeden kodlamaya baslama.
3. **Kod yazmayi bitirdikten sonra, olasi edge case'leri listele ve bunlari kapsayacak test senaryolari oner.**
4. **Bir gorev 3'ten fazla dosyada degisiklik gerektiriyorsa, dur ve once daha kucuk gorevlere bol.** Her alt gorevi ayri ayri onayla.
5. **Bir hata oldugunda, oncelikle hatayi yeniden olusturacak bir test yaz, ardindan test basarili olana kadar hatayi duzelt.**
6. **Her duzeltme yaptiginda, neyi yanlis yaptigini dusun ve ayni hatayi bir daha asla yapmamak icin bir plan gelistir.**
7. **Bu dosyayi her onemli degisiklikten sonra guncelle.** Yeni kararlar, mimari degisiklikler, bilinen sorunlar buraya yazilmali.

---

## Sistem Mimarisi

### Proje Nedir?
X (Twitter) AI Otomasyon Dashboard -- AI gelismelerini tarayip, arastirip, dogal tweet ureten uygulama.

**Mimari: Next.js (frontend) + FastAPI (backend) + Streamlit (eski, hala mevcut)**

Proje Streamlit'ten Next.js + FastAPI mimarisine tasinmistir. Eski Streamlit dosyalari hala repoda mevcut.

### Dosya Yapisi
```
# === YENI MIMARI (Next.js + FastAPI) ===

backend/
  main.py                     -> FastAPI app, CORS, middleware, router'lar
  config.py                   -> Backend konfigurasyonu
  api/
    auth.py                   -> JWT auth, login/register, auth middleware
    dashboard.py              -> Ana sayfa API'leri
    scanner.py                -> Konu tarama API'leri
    generator.py              -> Tweet uretme API'leri
    publish.py                -> Tweet paylasma API'leri
    settings.py               -> Ayarlar API'leri
    analytics.py              -> Hesap analiz API'leri
    calendar.py               -> Takvim API'leri
    drafts.py                 -> Taslak (draft) yonetim API'leri
    helpers.py                -> Ortak yardimci fonksiyonlar
  modules/
    _compat.py                -> Uyumluluk katmani (Streamlit -> FastAPI gecisi)
    content_generator.py      -> ContentGenerator (Claude/OpenAI/MiniMax)
    twitter_scanner.py        -> TwitterScanner sinifi
    tweet_analyzer.py         -> Hesap tweet analizi, stil DNA
    tweet_publisher.py        -> Tweet/thread/quote tweet paylasma
    twikit_client.py          -> Ucretsiz Twitter arama (cookie)
    grok_client.py            -> Grok xAI API
    deep_research.py          -> DDG arama + makale cekme
    style_manager.py          -> JSON dosya yoneticisi
    media_finder.py           -> Gorsel/video arama
    tweet_pool.py             -> Tweet havuzu
    telegram_notifier.py      -> Telegram bildirim

frontend/
  src/
    app/
      page.tsx                -> Ana sayfa (dashboard)
      layout.tsx              -> Root layout
      globals.css             -> Global stiller
      login/                  -> Giris sayfasi
      tara/                   -> Konu tarama sayfasi
      yaz/                    -> Tweet yazma sayfasi
      analiz/                 -> Hesap analiz sayfasi
      ayarlar/                -> Ayarlar sayfasi
      icerik/                 -> Uzun icerik uretimi
      takvim/                 -> Posting takvimi
      taslaklarim/            -> Taslak yonetimi
    components/
      AppShell.tsx            -> Ana layout wrapper (sidebar + content)
      Sidebar.tsx             -> Sol menu
      ActionCard.tsx          -> Aksiyon karti bileşeni
      ScheduleCard.tsx        -> Takvim karti bilesen
      StatBox.tsx             -> Istatistik kutusu
    lib/
      api.ts                  -> Backend API client (fetch wrapper)
      auth.tsx                -> Auth context, JWT yonetimi

# === ESKI MIMARI (Streamlit - hala mevcut) ===

streamlit_app.py              -> Ana sayfa (dashboard, istatistikler)
scheduled_scanner.py          -> Arka plan zamanli tarayici
pages/
  1_Tara.py                   -> AI konu tarama
  2_Yaz.py                    -> Tweet uretme ve paylasma
  3_Ayarlar.py                -> API anahtarlari ve ayarlar
  4_Analiz.py                 -> Hesap analizi
  6_Icerik.py                 -> Uzun icerik uretimi
  7_Takvim.py                 -> Gunluk posting takvimi
modules/
  (ayni backend/modules ile, Streamlit uyumluluk)

# === DIGER ===
ai_news_twitter_bot/          -> Bagimsiz haber botu (config, fetcher, writer, poster)
generate_cookies.py           -> Twitter cookie uretici
```

### API Endpointleri
```
POST /api/auth/login          -> JWT token al
GET  /api/health              -> Saglik kontrolu
GET  /api/dashboard/...       -> Dashboard verileri
POST /api/scanner/scan        -> Konu tarama baslat
POST /api/generator/generate  -> Tweet uret
POST /api/publish/tweet       -> Tweet paylas
GET  /api/settings/...        -> Ayarlar oku/yaz
GET  /api/analytics/...       -> Analiz verileri
GET  /api/calendar/...        -> Takvim verileri
GET  /api/drafts/...          -> Taslak CRUD
```

### Moduller Arasi Bagimliliklar
```
Frontend (Next.js) -> Backend (FastAPI) via REST API (/api/*)
Backend API routes -> backend/modules/* (is mantigi)
backend/modules/_compat.py -> Streamlit session_state yerine gecen adaptorler

Eski bagimliliklar (Streamlit):
Pages -> ui_components (CSS, auth, sidebar)
Pages -> content_generator, twitter_scanner, deep_research, vb.
```

### AI Provider Siralamasi
MiniMax (oncelikli) -> Anthropic Claude -> OpenAI GPT. `get_ai_client()` bu sirayla kontrol eder.

### Engagement Score Agirliklari (X Algorithm)
- RT = 20x, Reply = 13.5x, Like = 1x, Bookmark = 10x
- `twitter_scanner.py:AITopic.engagement_score` -> tarama siralamasi
- `tweet_analyzer.py:calculate_engagement_score()` -> detayli analiz
- `calculate_relevance()` divisor = 1000

### Arama Motoru: DuckDuckGo
- `deep_research.py` paralel arama (ThreadPoolExecutor, 4 worker)
- Rate limit korumasi: 0.3s delay, 0.15s stagger
- Fallback zinciri: `day -> week -> month -> all-time`

### Arama Motoru: Grok (xAI)
- `grok_client.py` xAI Responses API
- Server-side tools: `x_search`, `web_search` (ucretsiz)
- Model: `grok-4-1-fast`

---

## Onemli Kararlar ve Nedenler

| Tarih | Karar | Neden |
|-------|-------|-------|
| 2026-03-05 | Next.js + FastAPI mimarisine gecis | Streamlit production icin yetersiz, modern SPA + API mimarisi |
| 2026-03-05 | JWT auth sistemi | Backend/frontend ayrimi icin token bazli auth |
| 2026-03-05 | Taslak (draft) sistemi | Tweet'leri kaydetme, duzenleme, sonra paylasma |
| 2026-03-05 | sniffio cvar wrapper | httpcore background loop'ta async library algilayamiyor |
| 2026-03-05 | Transport hatalari re-auth tetiklemiyor | weak reference/async library hatalari auth degil transport sorunu |
| 2026-03-04 | Auto-update varsayilan KAPALI | Her oturumda git pull + pip install app lock riski |
| 2026-03-04 | DuckDuckGo paralel arama | 9 sirali arama ~15sn -> paralel ~4sn |
| 2026-03-04 | Engagement weights X algorithm ile uyumlu | Scanner ve Analyzer farkli agirlik kullaniyordu |
| 2026-03-04 | Gorsel arama: varsayilan X, opsiyonel Web | X gorselleri daha alakali |
| 2026-03-04 | Vision: MiniMax -> Claude/OpenAI fallback | MiniMax vision desteklemiyor |

---

## Bilinen Sorunlar / Teknik Borc

### Aktif Sorunlar
- [ ] **Streamlit kodlari hala mevcut**: Eski pages/ ve streamlit_app.py temizlenmedi, bakim gerektiriyor
- [ ] **Frontend sayfalari eksik olabilir**: Tum Streamlit sayfalari henuz Next.js'e tasinmamis olabilir
- [ ] **Engagement weights 3 yerde tanimi**: twitter_scanner.py, tweet_analyzer.py, content_generator.py
- [ ] **Test eksikligi**: Hicbir modulde unit test yok
- [ ] **content_generator.py** cok buyuk (~1700+ satir): bolunebilir
- [ ] **Hardcoded config**: Account listesi, API limitleri, timeout'lar ayri config'e tasinabilir

### Cozulmus Sorunlar
- [x] Next.js + FastAPI migration (2026-03-05)
- [x] Auth sistemi (JWT) (2026-03-05)
- [x] Taslak sistemi (2026-03-05)
- [x] Scanner ve Analytics API wiring (2026-03-05)
- [x] sniffio AsyncLibraryNotFoundError (2026-03-05)
- [x] Transport hata re-auth dongusu (2026-03-05)
- [x] Page 6 x_scanner import hatasi (2026-03-04)
- [x] Engagement weights tutarsizligi (2026-03-04)
- [x] DuckDuckGo paralel arama (2026-03-04)

---

## Degisiklik Gunlugu

### 2026-03-05 (Next.js + FastAPI Migration)
- **feat**: `backend/` -- FastAPI backend: main.py, tum API route'lari (auth, dashboard, scanner, generator, publish, settings, analytics, calendar, drafts)
- **feat**: `backend/modules/` -- Backend modulleri (Streamlit bagimliligini kaldirarak)
- **feat**: `backend/modules/_compat.py` -- Streamlit session_state uyumluluk katmani
- **feat**: `frontend/` -- Next.js app: tum sayfalar (tara, yaz, analiz, ayarlar, icerik, takvim, taslaklarim)
- **feat**: `frontend/src/components/` -- AppShell, Sidebar, ActionCard, ScheduleCard, StatBox
- **feat**: `frontend/src/lib/api.ts` -- Backend API client
- **feat**: `frontend/src/lib/auth.tsx` -- JWT auth context
- **feat**: `backend/api/auth.py` -- JWT login/register + auth middleware
- **feat**: `backend/api/drafts.py` -- Taslak CRUD API'leri
- **fix**: Scanner ve Analytics API'leri gercek modul metodlarina baglandi
- **fix**: Tara ve Analiz sayfalari yeni backend response formatlarina guncellendi

### 2026-03-05 (Async Transport Fix)
- **fix**: `twikit_client.py` -- sniffio AsyncLibraryNotFoundError duzeltildi
- **fix**: `twikit_client.py` -- Transport hatalari artik re-auth tetiklemiyor

### 2026-03-04 (Tweet Havuzu + Gorsel + Takvim)
- **feat**: Tweet havuzu sistemi, gorsel arama, vision destegi, posting takvimi
- **feat**: DuckDuckGo paralel arama, Grok cost reset
- **fix**: Cesitli bug fix'ler (engagement weights, import hatalari, regex, vb.)

---

## Calistirma

### Backend (FastAPI)
```bash
cd backend
uvicorn backend.main:app --reload --port 8000
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

### Eski Streamlit (deprecating)
```bash
streamlit run streamlit_app.py
```

### Windows PowerShell Notu
PowerShell'de `&&` calismaz. Komutlari ayri satirlarda calistirin:
```powershell
cd frontend
npm install
npm run dev
```
