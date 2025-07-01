from coaching_webapp_real import app, start_email_monitor
import os

if __name__ == '__main__':
    print("🚀 Railway Coaching System startet...")
    start_email_monitor()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
