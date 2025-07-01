import os
from decouple import config

class ProductionConfig:
    # OpenAI
    OPENAI_API_KEY = config('OPENAI_API_KEY')
    ASSISTANT_ID = config('ASSISTANT_ID')
    
    # E-Mail (Cyon)
    DELTA_EMAIL = config('DELTA_EMAIL', default='bot@allenspach-coaching.ch')
    DELTA_PASSWORD = config('DELTA_PASSWORD')
    
    # Flask
    SECRET_KEY = config('SECRET_KEY', default='coaching-production-2025')
    DEBUG = False
    
    # Server
    HOST = '0.0.0.0'
    PORT = int(config('PORT', default=5000))
    
    # E-Mail Settings
    EMAIL_CONFIG = {
        'address': DELTA_EMAIL,
        'password': DELTA_PASSWORD,
        'smtp_server': 'mail.cyon.ch',
        'smtp_port': 587,
        'imap_server': 'mail.cyon.ch',
        'imap_port': 993
    }
