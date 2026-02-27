# Viral İçerik Sistemi - XPatla Benzeri Sistem Planı

## Analiz: @hrrcnes ve XPatla Nasıl Çalışıyor?

### XPatla'nın Temel Özellikleri (xpatla.com)
- 10.000+ viral tweet ile eğitilmiş AI
- Kullanıcının yazım stilini öğreniyor
- Quote tweet + araştırma sistemi
- Viral skor tahmini
- Thread oluşturma
- Optimal zamanlama

### Viral Tweet Yazım Metodolojisi
1. **Konu Araştırması**: Sadece "ne" değil, "neden önemli" ve "bağlam"
2. **Stil Uyumu**: Kullanıcının kendi sesinde yazma
3. **Format Seçimi**: Micro (kısa) → Thunder (1500 kar) → Mega (2000 kar)
4. **Quote Tweet**: Orijinal içeriğe değer katma, sadece paylaşmama

---

## Bizim Sistemimize Eklenecekler

### 1. QUOTE TWEET SİSTEMİ (YENİ)
```
Akış:
1. Viral tweet bul (AI haberi, model duyurusu vs.)
2. Araştırma yap:
   - Tweet ne hakkında?
   - Teknik detaylar neler?
   - Bağlam nedir?
   - Kullanıcı için neden önemli?
3. Quote tweet yaz:
   - Hook (dikkat çekici açılış)
   - Değer ekleme (kendi yorumun, analiz)
   - CTA (call to action)
```

### 2. GELİŞMİŞ ARAŞTIRMA SİSTEMİ
```
Mevcut: Basit konu özeti
Yeni:
- Teknik detayları çek (model özellikleri, benchmark vs.)
- Karşılaştırma yap (önceki versiyon vs yeni)
- Bağlam ekle (bu sektör için ne anlama geliyor?)
- Kaynak doğrulama
- İlgili tweetleri bul
```

### 3. TAKİP EDİLEN HESAPLAR YÖNETİMİ
```
Özellikler:
- Hesap listesi görüntüleme
- Yeni hesap ekleme/çıkarma
- Her hesap için:
  - Son tweetler
  - Etkileşim oranları
  - İçerik türü (duyuru/görüş/teknik)

İçerik Filtreleme:
- "hello", "gm", "good morning" gibi tweetleri atla
- Sadece değerli içerik:
  - Model duyuruları
  - Özellik güncellemeleri
  - Teknik analizler
  - Önemli görüşler
```

### 4. VİRAL SKOR TAHMİNİ
```
Faktörler:
- Hook kalitesi (0-20 puan)
- İçerik değeri (0-25 puan)
- Trend uyumu (0-15 puan)
- Uzunluk optimizasyonu (0-10 puan)
- CTA varlığı (0-10 puan)
- Zamanlama (0-10 puan)
- Görsel potansiyeli (0-10 puan)
```

### 5. İÇERİK FİLTRELEME
```python
SKIP_PATTERNS = [
    "hello", "gm", "good morning", "good night",
    "günaydın", "iyi geceler", "selam",
    "rt if", "like if", "follow me",
    # Sadece emoji olan tweetler
    # Çok kısa (<30 karakter) ve anlamsız
]

KEEP_PATTERNS = [
    "announce", "release", "launch", "new",
    "update", "feature", "model", "benchmark",
    "duyuru", "güncelleme", "yeni", "çıktı",
]
```

---

## Yeni Dosya Yapısı

```
src/content/
├── ai_content_engine.py      # Ana motor (mevcut)
├── viral_writer.py           # YENİ: Viral yazım motoru
├── research_engine.py        # YENİ: Derin araştırma
├── quote_tweet_generator.py  # YENİ: Quote tweet sistemi
├── account_manager.py        # YENİ: Hesap yönetimi
└── content_filter.py         # YENİ: İçerik filtreleme
```

---

## UI Değişiklikleri

### Keşfet Sayfası (Güncelleme)
```
┌─────────────────────────────────────────────────┐
│ AI İçerik Keşfet                                │
├─────────────────────────────────────────────────┤
│ [Zaman: 6s ▼] [Kategori: AI ▼] [Tara]          │
├─────────────────────────────────────────────────┤
│                                                 │
│ Tweet 1: @OpenAI - GPT-5 duyuruldu...          │
│ ❤️ 50K | 🔄 20K | Viral Skor: 92/100           │
│ [Quote Tweet Yaz] [Araştır] [Thread Yap]       │
│                                                 │
│ Tweet 2: @AnthropicAI - Claude 4...            │
│ ❤️ 30K | 🔄 15K | Viral Skor: 88/100           │
│ [Quote Tweet Yaz] [Araştır] [Thread Yap]       │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Quote Tweet Yazma Ekranı (YENİ)
```
┌─────────────────────────────────────────────────┐
│ Quote Tweet Oluştur                             │
├─────────────────────────────────────────────────┤
│ ORİJİNAL TWEET:                                │
│ @OpenAI: We're releasing GPT-5...              │
├─────────────────────────────────────────────────┤
│ ARAŞTIRMA SONUÇLARI:                           │
│ • GPT-5, GPT-4'ten 2x hızlı                    │
│ • Multimodal yetenekler geliştirilmiş          │
│ • Fiyat: $30/1M token                          │
│ • Rakipler: Claude 4, Gemini 2                 │
├─────────────────────────────────────────────────┤
│ YAZIM STİLİ: [Samimi ▼]                        │
│ FORMAT: [Thunder (1500 kar) ▼]                 │
├─────────────────────────────────────────────────┤
│ OLUŞTURULAN QUOTE TWEET:                       │
│ ┌───────────────────────────────────────────┐  │
│ │ ya şimdi bu büyük olay.                   │  │
│ │                                           │  │
│ │ openai gpt-5'i duyurdu ve...              │  │
│ │ • 2x daha hızlı                           │  │
│ │ • multimodal artık düzgün çalışıyor       │  │
│ │ • fiyat makul kalmış                      │  │
│ │                                           │  │
│ │ claude 4 ile karşılaştırınca...           │  │
│ │ [devamı]                                  │  │
│ └───────────────────────────────────────────┘  │
│ 📊 Viral Skor: 87/100                          │
│ 📝 1247 karakter                               │
├─────────────────────────────────────────────────┤
│ [Yeniden Yaz] [Kopyala] [Onayla]               │
└─────────────────────────────────────────────────┘
```

### Takip Edilen Hesaplar (YENİ SAYFA)
```
┌─────────────────────────────────────────────────┐
│ Takip Edilen Hesaplar                           │
├─────────────────────────────────────────────────┤
│ AI HESAPLARI:                                   │
│ ☑ @OpenAI - Resmi OpenAI hesabı               │
│ ☑ @AnthropicAI - Claude'un yaratıcısı         │
│ ☑ @GoogleAI - Google AI                        │
│ ☑ @sama - Sam Altman                           │
│ ☑ @karpathy - Andrej Karpathy                 │
│ ☐ @ylecun - Yann LeCun (devre dışı)           │
│                                                 │
│ [+ Yeni Hesap Ekle]                            │
├─────────────────────────────────────────────────┤
│ FİLTRE AYARLARI:                               │
│ ☑ Sadece duyuruları göster                     │
│ ☑ "gm/hello" tweetlerini atla                  │
│ ☑ Min. 100 like                                │
│ ☐ Sadece İngilizce                             │
└─────────────────────────────────────────────────┘
```

---

## Uygulama Öncelik Sırası

1. **Faz 1**: İçerik filtreleme + Hesap yönetimi
2. **Faz 2**: Gelişmiş araştırma sistemi
3. **Faz 3**: Quote tweet generator
4. **Faz 4**: Viral skor tahmini
5. **Faz 5**: Thread oluşturma

---

## Kaynaklar
- [XPatla](https://xpatla.com/) - @hrrcnes'in viral tweet aracı
- [ToolHunters XPatla İnceleme](https://toolshunters.com/arac/xpatla)
- [Guncelkal XPatla Analizi](https://guncelkal.com/urun/xpatla-x-twitter-viral-olma-araci)
