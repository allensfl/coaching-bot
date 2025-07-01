#!/usr/bin/env python3
import os
import smtplib
import imaplib
from dotenv import load_dotenv

load_dotenv()

EMAIL_CONFIG = {
    'address': os.getenv('DELTA_EMAIL'),
    'password': os.getenv('DELTA_PASSWORD'),
    'smtp_server': 'smtp.cyon.ch',
    'smtp_port': 587,
    'imap_server': 'imap.cyon.ch',
    'imap_port': 993
}

print("🧪 E-Mail Verbindungstest...")
print(f"📧 E-Mail: {EMAIL_CONFIG['address']}")

# SMTP Test
try:
    print("📤 SMTP Test...")
    with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
        server.starttls()
        server.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
        print("✅ SMTP Verbindung erfolgreich!")
except Exception as e:
    print(f"❌ SMTP Fehler: {e}")

# IMAP Test  
try:
    print("📥 IMAP Test...")
    with imaplib.IMAP4_SSL(EMAIL_CONFIG['imap_server'], EMAIL_CONFIG['imap_port']) as mail:
        mail.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
        print("✅ IMAP Verbindung erfolgreich!")
except Exception as e:
    print(f"❌ IMAP Fehler: {e}")
