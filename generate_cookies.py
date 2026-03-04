#!/usr/bin/env python3
"""
Twikit Cookie Olusturucu
========================
Bu scripti KENDI BILGISAYARINDA calistir.
Twitter'a giris yapar, cookie dosyasini olusturur.
Sonra bu dosyayi Streamlit uygulamasina yuklersin.

Kullanim:
  pip install twikit
  python generate_cookies.py

Sorarsa:
  - Kullanici adi: Twitter kullanici adin (@ olmadan)
  - Sifre: Twitter sifren
  - Email: Twitter'a kayitli email (2FA icin gerekebilir)
"""
import asyncio
import sys
import os


async def generate_cookies():
    try:
        from twikit import Client
    except ImportError:
        print("HATA: twikit kurulu degil!")
        print("Kurmak icin: pip install twikit")
        sys.exit(1)

    print("=" * 50)
    print("  Twikit Cookie Olusturucu")
    print("=" * 50)
    print()

    username = input("Twitter kullanici adi (@ olmadan): ").strip()
    password = input("Twitter sifre: ").strip()
    email = input("Twitter email (bos birakilabilir): ").strip()

    if not username or not password:
        print("HATA: Kullanici adi ve sifre gerekli!")
        sys.exit(1)

    print()
    print(f"@{username} ile giris yapiliyor...")
    print("(Bu 10-30 saniye surebilir)")
    print()

    # Turkce locale dene, basarisiz olursa en-US
    for locale in ['tr', 'en-US']:
        try:
            client = Client(locale)

            login_kwargs = {
                "auth_info_1": username,
                "auth_info_2": email or username,
                "password": password,
            }

            await client.login(**login_kwargs)

            # Cookie dosyasini kaydet
            cookie_file = "twikit_cookies.json"
            client.save_cookies(cookie_file)

            full_path = os.path.abspath(cookie_file)
            print("=" * 50)
            print("  BASARILI!")
            print("=" * 50)
            print()
            print(f"Cookie dosyasi olusturuldu: {full_path}")
            print()
            print("Simdi yapman gereken:")
            print("1. Streamlit uygulamasini ac")
            print("2. Ayarlar sayfasina git")
            print("3. Twikit bolumunde 'Cookie Dosyasi Yukle' butonuna tikla")
            print(f"4. '{cookie_file}' dosyasini sec ve yukle")
            print()
            print("Artik Twikit calisacak!")
            return

        except Exception as e:
            error_str = str(e)
            if locale == 'tr':
                print(f"Turkce locale basarisiz ({e}), en-US deneniyor...")
                continue

            print(f"HATA: Giris basarisiz!")
            print(f"Hata: {type(e).__name__}: {error_str}")
            print()

            if "403" in error_str:
                print("COZUM: Twitter bu girisi engelliyor.")
                print("1. Once twitter.com'dan tarayiciyla giris yap")
                print("2. Herhangi bir dogrulama isterse tamamla")
                print("3. Sonra bu scripti tekrar calistir")
            elif "challenge" in error_str.lower():
                print("COZUM: Twitter dogrulama istiyor.")
                print("1. twitter.com'dan giris yap")
                print("2. Dogrulamayi tamamla")
                print("3. Sonra bu scripti tekrar calistir")
            elif "2fa" in error_str.lower() or "totp" in error_str.lower():
                print("COZUM: 2FA aktif.")
                print("1. Twitter'dan 2FA'yi gecici olarak kapat")
                print("2. Bu scripti calistir")
                print("3. Cookie olusunca 2FA'yi geri ac")
            else:
                print("Kullanici adi, sifre veya email'i kontrol et.")

            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(generate_cookies())
