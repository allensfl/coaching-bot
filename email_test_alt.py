#!/usr/bin/env python3
import os
import smtplib
import imaplib
from dotenv import load_dotenv

load_dotenv()

# Alternative Cyon-Einstellungen
CONFIGS = [
    {
        'name': 'Standard Cyon',
        'smtp_server': 'smtp.cyon.ch',
        'smtp_port': 587,
        'imap_server': 'imap.cyon.ch',
        'imap_port': 993
    },
    {
        'name': 'Alternative Cyon',
        'smtp_server': 'mail.cyon.ch', 
        'smtp_port': 587,
        'imap_server': 'mail.cyon.ch',
        'imap_port': 993
    },
    {
        'name': 'Cyon SSL',
        'smtp_server': 'smtp.cyon.ch',
        'smtp_port': 465,
        'imap_server': 'imap.cyon.ch', 
        'imap_port': 993
    }
]

email = os.getenv('DELTA_EMAIL')
password = os.getenv('DELTA_PASSWORD')

print(f"🧪 Testing E-Mail: {email}")
print()

for config in CONFIGS:
    print(f"📧 Testing {config['name']}...")
    
    # SMTP Test
    try:
        if config['smtp_port'] == 465:
            server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        else:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
        
        server.login(email, password)
        server.quit()
        print(f"✅ SMTP {config['name']} - Erfolgreich!")
        
    except Exception as e:
        print(f"❌ SMTP {config['name']} - Fehler: {e}")
    
    # IMAP Test
    try:
        mail = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
        mail.login(email, password)
        mail.logout()
        print(f"✅ IMAP {config['name']} - Erfolgreich!")
        
    except Exception as e:
        print(f"❌ IMAP {config['name']} - Fehler: {e}")
    
    print()
