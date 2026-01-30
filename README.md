# Twitter/X Growth Automation Tool

Twitter/X hesabınızı büyütmek için tam otomatik içerik oluşturma ve paylaşım aracı.

## Özellikler

- **Trend Analizi**: Twitter'daki güncel trendleri otomatik takip eder
- **AI İçerik Oluşturma**: OpenAI GPT veya Anthropic Claude ile tweet oluşturur
- **Görsel Bulma**: Unsplash/Pexels'tan konuya uygun görsel bulur
- **Akıllı Zamanlama**: Twitter algoritmasına göre optimal saatlerde paylaşım
- **Thread Oluşturma**: Uzun konular için otomatik thread oluşturma
- **Dashboard**: Streamlit ile görsel kontrol paneli

## Twitter Algoritması Optimizasyonu

Bu araç, Twitter'ın açık kaynak algoritmasına göre optimize edilmiştir:

| Etkileşim | Ağırlık |
|-----------|---------|
| Reply | 13.5x |
| Profil Tıklama | 12x |
| Retweet | 1x |
| Like | 0.5x |

**Kaynak**: [github.com/twitter/the-algorithm](https://github.com/twitter/the-algorithm)

### İpuçları
- İlk 30 dakika kritik - erken etkileşim önemli
- Görsel içerik 3 kat daha fazla etkileşim alır
- 1-3 hashtag optimal
- Günde 2-5 tweet ideal

## Kurulum

### 1. Gereksinimleri yükleyin

```bash
pip install -r requirements.txt
```

### 2. API anahtarlarını ayarlayın

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyerek API anahtarlarınızı girin:

- **Twitter API**: [developer.twitter.com](https://developer.twitter.com/) (Basic veya Pro tier gerekli)
- **OpenAI API**: [platform.openai.com](https://platform.openai.com/)
- **Anthropic API**: [console.anthropic.com](https://console.anthropic.com/)
- **Unsplash API**: [unsplash.com/developers](https://unsplash.com/developers)
- **Pexels API**: [pexels.com/api](https://www.pexels.com/api/)

### 3. Uygulamayı başlatın

```bash
streamlit run streamlit_app.py
```

## Kullanım

### Web Dashboard

Dashboard 5 sekmeden oluşur:

1. **Tweet Oluştur**: Yeni içerik oluşturma
   - Manuel konu girişi
   - Trending'den seçim
   - Otomatik görsel ekleme
   - Thread oluşturma

2. **Zamanlanmış**: Bekleyen tweetleri görüntüleme/iptal etme

3. **Trendler**: Güncel trendleri analiz etme

4. **Analiz**: Hesap istatistikleri

5. **Ayarlar**: Konfigürasyon

### CLI Kullanımı

```python
from src.automation_engine import engine

# Otomatik tweet oluştur ve zamanla
result = engine.auto_generate_and_schedule(
    topic="Yapay Zeka",  # Opsiyonel
    use_trending=True,    # Trending'den konu seç
    include_image=True,   # Görsel ekle
    auto_post=False       # Zamanla (True = hemen gönder)
)

# Günlük içerik planı oluştur
results = engine.generate_daily_content(num_tweets=5)

# Thread oluştur
result = engine.create_thread(
    topic="Python Programlama",
    num_tweets=4
)

# Otomasyonu başlat
engine.start_automation()
```

## Proje Yapısı

```
twitter-growth/
├── config/
│   └── settings.py          # Tüm yapılandırmalar
├── src/
│   ├── api/
│   │   └── twitter_client.py # Twitter API entegrasyonu
│   ├── content/
│   │   ├── ai_writer.py      # AI içerik oluşturma
│   │   └── image_finder.py   # Görsel arama
│   ├── scheduler/
│   │   └── scheduler.py      # Zamanlama sistemi
│   └── automation_engine.py  # Ana otomasyon motoru
├── data/
│   └── images/               # İndirilen görseller
├── logs/                     # Log dosyaları
├── streamlit_app.py          # Web dashboard
├── requirements.txt
├── .env.example
└── README.md
```

## Yapılandırma

`config/settings.py` dosyasından tüm ayarları özelleştirebilirsiniz:

```python
# Günlük tweet limiti
max_tweets_per_day: int = 5

# Optimal paylaşım saatleri (Türkiye)
optimal_posting_hours_turkey: List[int] = [8, 12, 13, 17, 19, 21]

# Hashtag ayarları
max_hashtags: int = 3

# Gece paylaşımı
enable_night_posting: bool = False
```

## Güvenlik Notları

- API anahtarlarınızı asla paylaşmayın
- `.env` dosyasını `.gitignore`'a ekleyin
- Twitter API kullanım limitlerini aşmamaya dikkat edin
- Spam yapmaktan kaçının - kaliteli içerik üretin

## Lisans

MIT License

## Kaynaklar

- [Twitter Algorithm (GitHub)](https://github.com/twitter/the-algorithm)
- [Twitter API v2 Documentation](https://developer.twitter.com/en/docs/twitter-api)
- [Tweepy Documentation](https://docs.tweepy.org/)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic API](https://docs.anthropic.com/)
