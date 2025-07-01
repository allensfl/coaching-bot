#!/usr/bin/env python3
import os
import sys
from coaching_webapp_real import app, start_email_monitor

# Production-Konfiguration
if os.environ.get('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False

if __name__ == '__main__':
    print("🌐 PRODUCTION: Coaching System startet...")
    print("📧 E-Mail Monitor wird gestartet...")
    
    # E-Mail Monitor starten
    start_email_monitor()
    
    # Produktionsserver
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=False
    )
