import imaplib
import os
from dotenv import load_dotenv

load_dotenv()

try:
    with imaplib.IMAP4_SSL('mail.cyon.ch', 993) as mail:
        mail.login(os.getenv('DELTA_EMAIL'), os.getenv('DELTA_PASSWORD'))
        mail.select('INBOX')
        
        # Alle E-Mails als ungelesen markieren
        status, messages = mail.search(None, 'ALL')
        if messages[0]:
            for msg_id in messages[0].split():
                mail.store(msg_id, '-FLAGS', '\\Seen')
                print(f"📧 E-Mail {msg_id.decode()} als ungelesen markiert")
        
        print("✅ Alle E-Mails als ungelesen markiert!")
        
except Exception as e:
    print(f"❌ Fehler: {e}")
