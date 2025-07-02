from flask import Flask, send_from_directory, render_template_string
import os

app = Flask(__name__)

@app.route('/')
def home():
    return send_from_directory('.', 'index_premium.html')

@app.route('/dashboard')
def full_dashboard():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>🧠 Premium Dashboard</title>
        <style>
            body { font-family: 'Segoe UI'; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 20px; color: white; }
            .dashboard { display: grid; grid-template-columns: 350px 1fr 350px; gap: 30px; height: 80vh; }
            .panel { background: rgba(255,255,255,0.1); backdrop-filter: blur(20px); border-radius: 20px; padding: 30px; border: 1px solid rgba(255,255,255,0.2); }
            .progress-circle { width: 200px; height: 200px; border-radius: 50%; background: conic-gradient(from 0deg, #00d4ff 0%, #00d4ff 75%, rgba(255,255,255,0.2) 75%); display: flex; align-items: center; justify-content: center; margin: 30px auto; position: relative; }
            .progress-circle::before { content: '75%'; font-size: 3rem; font-weight: bold; position: absolute; }
            .admin-btn, .phase-btn { background: rgba(255,255,255,0.15); border: none; color: white; padding: 15px; border-radius: 15px; margin: 10px 0; cursor: pointer; width: 100%; text-align: left; }
            .phase-buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
            h2 { margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1 style="text-align: center;">🧠 Intelligentes Ruhestandscoaching</h1>
        <div class="dashboard">
            <div class="panel">
                <h2>🛠️ Admin-Bereich</h2>
                <button class="admin-btn">👥 Benutzer verwalten</button>
                <button class="admin-btn">📊 Session-Übersicht</button>
                <button class="admin-btn">📈 Berichte generieren</button>
                <button class="admin-btn">⚙️ System-Einstellungen</button>
                <button class="admin-btn">💾 Backup & Export</button>
            </div>
            <div class="panel" style="text-align: center;">
                <div class="progress-circle"></div>
                <div class="phase-buttons">
                    <button class="phase-btn">🔍 Analyse</button>
                    <button class="phase-btn">🎯 Planung</button>
                    <button class="phase-btn">🚀 Umsetzung</button>
                    <button class="phase-btn">⭐ Optimierung</button>
                </div>
                <button style="background: rgba(0,212,255,0.3); color: white; border: none; padding: 20px 40px; border-radius: 50px; margin: 20px; cursor: pointer;">🚀 Coaching starten</button>
            </div>
            <div class="panel">
                <h2>📧 E-Mail Integration</h2>
                <p><span style="color: #00ff88;">● System aktiv</span></p>
                <h3>Automatische Benachrichtigungen:</h3>
                <ul>
                    <li>• Session-Erinnerungen</li>
                    <li>• Fortschritts-Updates</li>
                    <li>• Coaching-Termine</li>
                </ul>
                <p>SMTP-Server: aktiv</p>
                <p>Letzte Synchronisation: vor 2 Min.</p>
            </div>
        </div>
        <p style="text-align: center; margin-top: 30px;">
            <a href="/" style="color: white; text-decoration: none; background: rgba(255,255,255,0.2); padding: 10px 20px; border-radius: 25px;">← Zurück zur Hauptseite</a>
        </p>
    </body>
    </html>
    """)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
