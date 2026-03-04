"""
Zamanlanmis AI Gundem Tarayici
Windows Gorev Zamanlayici ile her X saatte bir calisir.
Sonuclari kaydeder ve Telegram'a bildirim gonderir.

Kullanim:
    python scheduled_scanner.py              # Tek seferlik tara
    python scheduled_scanner.py --loop 60    # Her 60 dakikada tara (surekli)
"""
import sys
import os
import json
import time
import argparse
import datetime
from pathlib import Path

# Proje kokunu Python path'e ekle
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# .env veya secrets dosyasindaki degerleri yukle
SECRETS_PATH = PROJECT_DIR / ".streamlit" / "secrets.toml"
RESULTS_DIR = PROJECT_DIR / "data" / "scan_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_secrets() -> dict:
    """secrets.toml dosyasini oku ve dict olarak dondur."""
    secrets = {}
    if not SECRETS_PATH.exists():
        print(f"HATA: {SECRETS_PATH} bulunamadi!")
        return secrets

    with open(SECRETS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                secrets[key] = value
    return secrets


def run_scan(secrets: dict, time_range_hours: int = 24,
             max_results: int = 20) -> list:
    """Tarama yap ve sonuclari dondur."""
    from modules.twikit_client import TwikitSearchClient
    from modules.twitter_scanner import TwitterScanner, DEFAULT_AI_ACCOUNTS
    from modules.style_manager import load_monitored_accounts

    twikit_username = secrets.get("twikit_username", "")
    twikit_password = secrets.get("twikit_password", "")
    twikit_email = secrets.get("twikit_email", "")
    bearer_token = secrets.get("twitter_bearer_token", "")

    scanner = TwitterScanner(
        bearer_token=bearer_token,
        twikit_username=twikit_username,
        twikit_password=twikit_password,
        twikit_email=twikit_email,
    )

    if not scanner.use_twikit and not scanner.client:
        print("HATA: Ne Twikit ne de Twitter API baglantisi kuruldu!")
        if scanner.twikit_error:
            print(f"  Twikit hatasi: {scanner.twikit_error}")
        return []

    method = "Twikit" if scanner.use_twikit else "Twitter API"
    print(f"  Tarama yontemi: {method}")

    # Ozel hesaplari yukle
    try:
        custom_accounts = load_monitored_accounts()
    except Exception:
        custom_accounts = []

    # Tara
    topics = scanner.scan_ai_topics(
        time_range_hours=time_range_hours,
        max_results_per_query=max_results,
        custom_accounts=custom_accounts,
    )

    # Hatalari goster
    if scanner.search_errors:
        unique = list(dict.fromkeys(scanner.search_errors))[:5]
        for err in unique:
            print(f"  Uyari: {err}")

    return topics


def save_results(topics: list, tag: str = "auto"):
    """Sonuclari JSON dosyasina kaydet."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scan_{tag}_{timestamp}.json"
    filepath = RESULTS_DIR / filename

    data = []
    for t in topics:
        data.append({
            "id": t.id,
            "text": t.text,
            "author_username": t.author_username,
            "author_name": t.author_name,
            "category": t.category,
            "like_count": t.like_count,
            "retweet_count": t.retweet_count,
            "reply_count": t.reply_count,
            "relevance_score": t.relevance_score,
            "url": t.url,
            "created_at": str(t.created_at),
        })

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  Sonuclar kaydedildi: {filepath}")

    # Eski dosyalari temizle (son 50 tane tut)
    old_files = sorted(RESULTS_DIR.glob("scan_*.json"))[:-50]
    for old in old_files:
        try:
            old.unlink()
        except Exception:
            pass


def send_telegram(secrets: dict, topics: list) -> bool:
    """Telegram bildirimi gonder."""
    bot_token = secrets.get("telegram_bot_token", "")
    chat_id = secrets.get("telegram_chat_id", "")

    if not bot_token or not chat_id:
        print("  Telegram yapilandirilmamis (telegram_bot_token/telegram_chat_id)")
        return False

    from modules.telegram_notifier import TelegramNotifier
    notifier = TelegramNotifier(bot_token, chat_id)

    if notifier.send_scan_results(topics, max_items=10):
        print(f"  Telegram bildirimi gonderildi ({len(topics)} konu)")
        return True
    else:
        print("  Telegram bildirim gonderilemedi!")
        return False


def main():
    parser = argparse.ArgumentParser(description="AI Gundem Zamanli Tarayici")
    parser.add_argument("--loop", type=int, default=0,
                        help="Dakika cinsinden tekrar suresi (0 = tek seferlik)")
    parser.add_argument("--hours", type=int, default=24,
                        help="Kac saatlik gecmisi tara (varsayilan: 24)")
    parser.add_argument("--max", type=int, default=20,
                        help="Sorgu basina maks sonuc (varsayilan: 20)")
    parser.add_argument("--no-telegram", action="store_true",
                        help="Telegram bildirimi gonderme")
    args = parser.parse_args()

    print("=" * 50)
    print("AI Gundem Zamanli Tarayici")
    print("=" * 50)

    secrets = load_secrets()
    if not secrets:
        print("HATA: Secrets yuklenemedi!")
        sys.exit(1)

    def do_scan():
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] Tarama basliyor...")

        try:
            topics = run_scan(secrets, args.hours, args.max)
            print(f"  {len(topics)} konu bulundu")

            if topics:
                save_results(topics)

                if not args.no_telegram:
                    send_telegram(secrets, topics)
            else:
                print("  Sonuc bulunamadi")

        except Exception as e:
            print(f"  HATA: {e}")

    if args.loop > 0:
        print(f"Surekli mod: Her {args.loop} dakikada bir taranacak")
        print("Durdurmak icin Ctrl+C basin\n")

        while True:
            do_scan()
            next_time = datetime.datetime.now() + datetime.timedelta(minutes=args.loop)
            print(f"\n  Sonraki tarama: {next_time.strftime('%H:%M:%S')}")
            print(f"  Bekleniyor ({args.loop} dakika)...")
            try:
                time.sleep(args.loop * 60)
            except KeyboardInterrupt:
                print("\nDurduruldu.")
                break
    else:
        do_scan()


if __name__ == "__main__":
    main()
