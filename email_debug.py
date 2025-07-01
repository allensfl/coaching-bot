import imaplib
import os
from dotenv import load_dotenv
import time

load_dotenv()

EMAIL_CONFIG = {
    'address': os.getenv('DELTA_EMAIL'),
    'password': os.getenv('DELTA_PASSWORD'),
    'imap_server': 'mail.cyon.ch',
    'imap_port': 993
}

print(f"🔍 Debugging E-Mail Monitor für: {EMAIL_CONFIG['address']}")

try:
    with imaplib.IMAP4_SSL(EMAIL_CONFIG['imap_server'], EMAIL_CONFIG['imap_port']) as mail:
        print("✅ IMAP Verbindung hergestellt")
        
        mail.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
        print("✅ Login erfolgreich")
        
        mail.select('INBOX')
        print("✅ INBOX ausgewählt")
        
        # Alle E-Mails
        status, all_messages = mail.search(None, 'ALL')
        total = len(all_messages[0].split()) if all_messages[0] else 0
        print(f"📧 Gesamt E-Mails im Postfach: {total}")
        
        # Ungelesene E-Mails
        status, unread = mail.search(None, 'UNSEEN')
        unread_count = len(unread[0].split()) if unread[0] else 0
        print(f"📬 Ungelesene E-Mails: {unread_count}")
        
        # Letzte 5 E-Mails anzeigen
        if all_messages[0]:
            recent_ids = all_messages[0].split()[-5:]
            print(f"\n📋 Letzte 5 E-Mails:")
            for msg_id in recent_ids:
                status, msg_data = mail.fetch(msg_id, '(ENVELOPE)')
                print(f"  ID: {msg_id.decode()}")
                print(f"  Status: {status}")

except Exception as e:
    print(f"❌ Fehler: {e}")
