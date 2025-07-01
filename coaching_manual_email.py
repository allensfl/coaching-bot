from dotenv import load_dotenv
import imaplib
import email
from email.message import EmailMessage
import smtplib
import os

load_dotenv()

EMAIL_CONFIG = {
    'address': os.getenv('DELTA_EMAIL'),
    'password': os.getenv('DELTA_PASSWORD'),
    'smtp_server': 'mail.cyon.ch',
    'smtp_port': 587,
    'imap_server': 'mail.cyon.ch',
    'imap_port': 993
}

print('🎯 Verarbeite E-Mail...')

with imaplib.IMAP4_SSL('mail.cyon.ch', 993) as mail:
    mail.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
    mail.select('INBOX')
    
    status, messages = mail.search(None, 'UNSEEN')
    if messages[0]:
        msg_id = messages[0].split()[0]
        print(f'📧 Verarbeite E-Mail ID: {msg_id.decode()}')
        
        # Einfache Test-Antwort senden
        response_msg = EmailMessage()
        response_msg['From'] = EMAIL_CONFIG['address']
        response_msg['To'] = 'flavien@bluewin.ch'
        response_msg['Subject'] = 'Coaching-System Test - Automatische Antwort'
        response_msg.set_content('🎯 Erfolg! Ihr E-Mail wurde automatisch verarbeitet!')
        
        with smtplib.SMTP('mail.cyon.ch', 587) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
            server.send_message(response_msg)
        
        print('✅ Test-Antwort gesendet!')
        mail.store(msg_id, '+FLAGS', '\\Seen')
    else:
        print('📭 Keine ungelesenen E-Mails')
