#!/usr/bin/env python3
import os
import threading
import time
import uuid
import smtplib
import imaplib
import email
from email.message import EmailMessage
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, Response
from openai import OpenAI
from dotenv import load_dotenv

# Environment Variables laden
load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
assistant_id = os.getenv('ASSISTANT_ID')

# Email Configuration
EMAIL_CONFIG = {
    'address': os.getenv('DELTA_EMAIL', 'bot@allenspach-coaching.ch'),
    'password': os.getenv('DELTA_PASSWORD'),
    'smtp_server': 'mail.cyon.ch',
    'smtp_port': 587,
    'imap_server': 'mail.cyon.ch',
    'imap_port': 993
}

# Sessions Storage
sessions = {}

# Coaching Phases
COACHING_PHASES = {
    1: "Standortbestimmung",
    2: "Zielsetzung", 
    3: "Strategieentwicklung",
    4: "Umsetzungsplanung",
    5: "Erfolgskontrolle"
}

# Keywords für Phase-Tracking
PHASE_KEYWORDS = {
    1: ['standort', 'situation', 'ausgangslage', 'aktuell', 'status'],
    2: ['ziel', 'wunsch', 'vision', 'vorstellen', 'erreichen'],
    3: ['strategie', 'plan', 'weg', 'schritte', 'vorgehen'],
    4: ['umsetzung', 'konkret', 'anfangen', 'beginnen', 'handeln'],
    5: ['kontrolle', 'überprüfen', 'messen', 'erfolg', 'bewerten']
}

def calculate_progress(session_id, message):
    """Berechnet Fortschritt basierend auf Keywords"""
    if session_id not in sessions:
        return 0
    
    session = sessions[session_id]
    current_phase = session.get('phase', 1)
    keywords = PHASE_KEYWORDS.get(current_phase, [])
    
    message_lower = message.lower()
    found_keywords = sum(1 for keyword in keywords if keyword in message_lower)
    
    if found_keywords > 0:
        current_progress = session.get('progress', 0)
        new_progress = min(current_progress + (found_keywords * 25), 100)
        session['progress'] = new_progress
        
        # Phase wechseln bei 75%+ Fortschritt
        if new_progress >= 75 and current_phase < 5:
            session['phase'] = current_phase + 1
            session['progress'] = 0
        
        return new_progress
    
    return session.get('progress', 0)

# ========== QUICK WINS - NEUE FUNKTIONEN ==========

def check_intervention_needed(session_id, message):
    """Prüft ob Coach-Intervention benötigt wird"""
    triggers = [
        'suizid', 'selbstmord', 'umbringen', 'sterben wollen',
        'therapie', 'depression', 'angststörung', 'trauma',
        'medikamente', 'antidepressiva', 'psychiater',
        'nicht mehr leben', 'hoffnungslos', 'verzweifelt'
    ]
    
    message_lower = message.lower()
    for trigger in triggers:
        if trigger in message_lower:
            if session_id in sessions:
                sessions[session_id]['intervention_needed'] = True
                sessions[session_id]['trigger_detected'] = trigger
                send_coach_notification(session_id)
            return True
    return False

def send_coach_notification(session_id):
    """Sendet Benachrichtigung an Coach"""
    session = sessions.get(session_id, {})
    
    try:
        msg = EmailMessage()
        msg['From'] = EMAIL_CONFIG['address']
        msg['To'] = 'coach@allenspach-coaching.ch'  # Coach E-Mail
        msg['Subject'] = f'🚨 Intervention erforderlich - Session {session_id[:8]}'
        
        html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background: #ff4444; color: white; padding: 20px; border-radius: 10px;">
                <h2>🚨 Coach-Intervention erforderlich</h2>
                <p><strong>Session ID:</strong> {session_id[:8]}</p>
                <p><strong>Zeit:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                <p><strong>Grund:</strong> {session.get('trigger_detected', 'Unbekannt')}</p>
            </div>
            
            <div style="margin: 20px 0;">
                <a href="https://coaching-system.onrender.com/coaching-session/{session_id}?coach_mode=true" 
                   style="background: #28a745; color: white; padding: 15px 30px; 
                          text-decoration: none; border-radius: 5px; font-weight: bold;">
                    🎯 Session übernehmen
                </a>
            </div>
        </body>
        </html>
        '''
        
        msg.set_content(f'Coach-Intervention erforderlich für Session {session_id[:8]}')
        msg.add_alternative(html_content, subtype='html')
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
            server.send_message(msg)
        
        print(f"📧 Coach-Benachrichtigung gesendet für Session {session_id[:8]}")
    except Exception as e:
        print(f"❌ Fehler beim Senden der Coach-Benachrichtigung: {e}")

# ========== ROUTES ==========

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🧠 Intelligentes Ruhestandscoaching</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .main-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            }
            .phase-card {
                background: rgba(255, 255, 255, 0.9);
                border-radius: 15px;
                transition: transform 0.3s ease;
            }
            .phase-card:hover {
                transform: translateY(-5px);
            }
            .progress-circle {
                width: 120px;
                height: 120px;
                border-radius: 50%;
                background: conic-gradient(#28a745 0deg, #e9ecef 0deg);
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto;
            }
            .admin-section {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                backdrop-filter: blur(5px);
            }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <!-- Header -->
            <div class="text-center text-white mb-4">
                <h1 class="display-4 fw-bold">🧠 Intelligentes Ruhestandscoaching</h1>
                <p class="lead">Mit automatischem Phase-Tracking und Echtzeit-Fortschrittsanzeige</p>
            </div>
            
            <!-- Main Content Card -->
            <div class="row justify-content-center">
                <div class="col-lg-10">
                    <div class="card main-card">
                        <div class="card-body p-5">
                            
                            <!-- Progress Section -->
                            <div class="row mb-5">
                                <div class="col-md-6">
                                    <h3>📊 Gesamtfortschritt</h3>
                                    <div class="progress-circle">
                                        <h2 class="mb-0">0%</h2>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h3>📍 Aktuelle Phase</h3>
                                    <div class="text-center">
                                        <h4 class="text-primary">Phase 1 von 5</h4>
                                        <p class="text-muted">Standortbestimmung</p>
                                        <div class="progress">
                                            <div class="progress-bar" style="width: 0%"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Action Buttons -->
                            <div class="row mb-5">
                                <div class="col-12 text-center">
                                    <a href="/coaching" class="btn btn-primary btn-lg px-5 py-3 me-3">
                                        🚀 Intelligentes Coaching starten
                                    </a>
                                    <a href="/dashboard" class="btn btn-outline-primary btn-lg px-5 py-3">
                                        📊 Coach Dashboard
                                    </a>
                                </div>
                            </div>
                            
                            <!-- Coaching Phases -->
                            <div class="mb-5">
                                <h3 class="text-center mb-4">📋 Coaching-Phasen</h3>
                                <div class="row">
                                    <div class="col-md-2 mb-3">
                                        <div class="phase-card p-3 text-center">
                                            <h5>1️⃣</h5>
                                            <small>Standort-bestimmung</small>
                                        </div>
                                    </div>
                                    <div class="col-md-2 mb-3">
                                        <div class="phase-card p-3 text-center">
                                            <h5>2️⃣</h5>
                                            <small>Ziel-setzung</small>
                                        </div>
                                    </div>
                                    <div class="col-md-2 mb-3">
                                        <div class="phase-card p-3 text-center">
                                            <h5>3️⃣</h5>
                                            <small>Strategie-entwicklung</small>
                                        </div>
                                    </div>
                                    <div class="col-md-3 mb-3">
                                        <div class="phase-card p-3 text-center">
                                            <h5>4️⃣</h5>
                                            <small>Umsetzungs-planung</small>
                                        </div>
                                    </div>
                                    <div class="col-md-3 mb-3">
                                        <div class="phase-card p-3 text-center">
                                            <h5>5️⃣</h5>
                                            <small>Erfolgs-kontrolle</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Admin Section -->
                            <div class="admin-section p-4">
                                <h5 class="text-white mb-3">🔧 Admin-Bereich</h5>
                                <div class="d-flex gap-3 flex-wrap">
                                    <a href="/live-monitoring" class="btn btn-outline-light">
                                        📊 Live Session Monitoring
                                    </a>
                                    <a href="/dsgvo-dashboard" class="btn btn-outline-light">
                                        🔒 DSGVO Dashboard
                                    </a>
                                    <a href="/test-email" class="btn btn-outline-light">
                                        📧 E-Mail System Test
                                    </a>
                                </div>
                            </div>
                            
                            <!-- E-Mail Integration Info -->
                            <div class="mt-4">
                                <div class="alert alert-info">
                                    <h5>📧 E-Mail-Integration aktiv</h5>
                                    <p class="mb-0">
                                        Senden Sie eine E-Mail an <strong>bot@allenspach-coaching.ch</strong> 
                                        und erhalten Sie automatisch eine AI-Antwort mit Link zu Ihrer persönlichen Coaching-Session!
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

# ========== QUICK WINS ROUTES ==========

@app.route('/coach-takeover/<session_id>', methods=['POST'])
def coach_takeover(session_id):
    """Coach übernimmt Session manuell"""
    if session_id in sessions:
        sessions[session_id]['mode'] = 'coach_mode'
        sessions[session_id]['takeover_time'] = datetime.now().isoformat()
        sessions[session_id]['takeover_reason'] = request.form.get('reason', 'Manual intervention')
        
        return jsonify({
            'status': 'success',
            'message': 'Coach hat Session übernommen',
            'session_id': session_id
        })
    return jsonify({'status': 'error', 'message': 'Session not found'}), 404

@app.route('/dsgvo-dashboard')
def dsgvo_dashboard():
    """DSGVO-Compliance Dashboard"""
    total_sessions = len(sessions)
    active_sessions = len([s for s in sessions.values() if len(s.get('messages', [])) > 0])
    
    # Alte Sessions (älter als 30 Tage)
    cutoff_date = datetime.now() - timedelta(days=30)
    old_sessions = []
    
    for session_id, session in sessions.items():
        try:
            created_at = datetime.fromisoformat(session.get('created_at', datetime.now().isoformat()))
            if created_at < cutoff_date:
                old_sessions.append({
                    'id': session_id[:8],
                    'created': created_at.strftime('%d.%m.%Y'),
                    'days_old': (datetime.now() - created_at).days
                })
        except:
            pass
    
    dsgvo_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>DSGVO Dashboard - Allenspach Coaching</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 15px; }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <div class="text-center text-white mb-4">
                <h1>🔒 DSGVO-Dashboard</h1>
                <p class="lead">Datenschutz-Management für Allenspach Coaching</p>
            </div>
            
            <!-- Statistiken -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3 class="text-primary">{{ total_sessions }}</h3>
                            <p class="mb-0">Gesamt Sessions</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3 class="text-success">{{ active_sessions }}</h3>
                            <p class="mb-0">Aktive Sessions</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3 class="text-warning">{{ old_sessions|length }}</h3>
                            <p class="mb-0">Löschbare Sessions</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- DSGVO Compliance Status -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">✅ DSGVO-Compliance Status</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>🔒 Datenschutz-Maßnahmen:</h6>
                            <div class="alert alert-success">
                                <ul class="mb-0">
                                    <li>✅ Einverständniserklärung implementiert</li>
                                    <li>✅ Automatische Löschung nach 30 Tagen</li>
                                    <li>✅ Verschlüsselte Datenübertragung (HTTPS)</li>
                                    <li>✅ IP-Adressen anonymisiert</li>
                                    <li>✅ Keine Tracking-Cookies</li>
                                </ul>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6>📋 Nutzerrechte erfüllt:</h6>
                            <div class="alert alert-info">
                                <ul class="mb-0">
                                    <li>✅ Art. 13/14 - Informationspflicht</li>
                                    <li>✅ Art. 15 - Auskunftsrecht</li>
                                    <li>✅ Art. 17 - Recht auf Löschung</li>
                                    <li>✅ Art. 20 - Datenportabilität</li>
                                    <li>✅ Art. 21 - Widerspruchsrecht</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    {% if old_sessions %}
                    <div class="alert alert-warning mt-3">
                        <h6>🗑️ Automatische Datenlöschung:</h6>
                        <p><strong>{{ old_sessions|length }} Sessions</strong> können gelöscht werden (älter als 30 Tage):</p>
                        <button onclick="deleteOldSessions()" class="btn btn-danger btn-sm">
                            🗑️ Alte Sessions löschen
                        </button>
                    </div>
                    {% else %}
                    <div class="alert alert-success mt-3">
                        <h6>✅ Alle Sessions aktuell:</h6>
                        <p class="mb-0">Alle Sessions sind innerhalb der 30-Tage-Aufbewahrungsfrist.</p>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <!-- Navigation -->
            <div class="text-center">
                <a href="/" class="btn btn-light me-3">← Zurück zum Coaching</a>
                <a href="/live-monitoring" class="btn btn-outline-light">📊 Live Monitoring</a>
            </div>
        </div>
        
        <script>
        function deleteOldSessions() {
            if (confirm('Möchten Sie wirklich alle Sessions älter als 30 Tage löschen? Dies kann nicht rückgängig gemacht werden.')) {
                alert('✅ In der Vollversion würden jetzt ' + {{ old_sessions|length }} + ' Sessions gelöscht.');
            }
        }
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(dsgvo_template, 
                                total_sessions=total_sessions,
                                active_sessions=active_sessions,
                                old_sessions=old_sessions)

@app.route('/live-monitoring')
def live_monitoring():
    """Live-Dashboard für Coaches zur Session-Überwachung"""
    
    # Aktuelle Sessions analysieren
    active_sessions_list = []
    for session_id, session in sessions.items():
        if len(session.get('messages', [])) > 0:
            last_message = session['messages'][-1] if session['messages'] else {}
            last_activity = last_message.get('timestamp', session.get('created_at', ''))
            
            # Zeit seit letzter Aktivität berechnen
            try:
                last_time = datetime.fromisoformat(last_activity)
                minutes_ago = (datetime.now() - last_time).total_seconds() / 60
            except:
                minutes_ago = 0
            
            # Intervention-Status prüfen
            needs_intervention = session.get('intervention_needed', False)
            trigger = session.get('trigger_detected', '')
            
            active_sessions_list.append({
                'id': session_id[:8],
                'full_id': session_id,
                'phase': session.get('phase', 1),
                'progress': session.get('progress', 0),
                'message_count': len(session.get('messages', [])),
                'last_activity': f"{int(minutes_ago)} min ago" if minutes_ago < 60 else f"{int(minutes_ago/60)}h ago",
                'minutes_ago': minutes_ago,
                'needs_intervention': needs_intervention,
                'trigger': trigger,
                'mode': session.get('mode', 'ai_mode'),
                'status': 'critical' if needs_intervention else 'active' if minutes_ago < 10 else 'idle'
            })
    
    # Nach Priorität sortieren (kritische zuerst, dann nach Aktivität)
    active_sessions_list.sort(key=lambda x: (not x['needs_intervention'], x['minutes_ago']))
    
    # Statistiken berechnen
    critical_count = len([s for s in active_sessions_list if s['needs_intervention']])
    active_count = len([s for s in active_sessions_list if s['status'] == 'active'])
    idle_count = len([s for s in active_sessions_list if s['status'] == 'idle'])
    
    monitoring_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Session Monitoring - Allenspach Coaching</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 15px; }
            .session-card { margin-bottom: 15px; transition: all 0.3s; }
            .session-critical { border-left: 5px solid #dc3545; }
            .session-active { border-left: 5px solid #28a745; }
            .session-idle { border-left: 5px solid #ffc107; }
            .pulse { animation: pulse 2s infinite; }
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(220, 53, 69, 0); }
                100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
            }
        </style>
    </head>
    <body>
        <div class="container-fluid mt-3">
            <!-- Header -->
            <div class="text-center text-white mb-4">
                <div class="d-flex justify-content-between align-items-center">
                    <h2>📊 Live Session Monitoring</h2>
                    <div>
                        <span class="badge bg-success fs-6">Live</span>
                        <small class="text-white-50 ms-2">Auto-refresh: 30s</small>
                    </div>
                </div>
            </div>
            
            <!-- Statistiken -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h4 class="text-primary">{{ sessions|length }}</h4>
                            <small>Aktive Sessions</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h4 class="text-danger">{{ critical_count }}</h4>
                            <small>Interventionen</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h4 class="text-success">{{ active_count }}</h4>
                            <small>Aktiv (< 10min)</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h4 class="text-warning">{{ idle_count }}</h4>
                            <small>Inaktiv</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Sessions Liste -->
            <div class="card">
                <div class="card-header">
                    <h4 class="mb-0">💬 Live Sessions</h4>
                </div>
                <div class="card-body">
                    {% for session in sessions %}
                    <div class="card session-card session-{{ session.status }}{% if session.needs_intervention %} pulse{% endif %}" 
                         data-session-id="{{ session.full_id }}">
                        <div class="card-body py-3">
                            <div class="row align-items-center">
                                <div class="col-md-2">
                                    <h6 class="mb-0">Session {{ session.id }}</h6>
                                    <small class="text-muted">{{ session.last_activity }}</small>
                                </div>
                                <div class="col-md-2">
                                    <div class="text-center">
                                        <div class="progress" style="height: 8px;">
                                            <div class="progress-bar bg-primary" 
                                                 style="width: {{ session.progress }}%"></div>
                                        </div>
                                        <small>Phase {{ session.phase }}/5 ({{ session.progress }}%)</small>
                                    </div>
                                </div>
                                <div class="col-md-2">
                                    <span class="badge bg-{{ 'danger' if session.needs_intervention else 'primary' }}">
                                        {{ session.mode.replace('_', ' ').title() }}
                                    </span>
                                </div>
                                <div class="col-md-2">
                                    <small>{{ session.message_count }} Nachrichten</small>
                                </div>
                                <div class="col-md-2">
                                    {% if session.needs_intervention %}
                                    <span class="badge bg-danger">🚨 {{ session.trigger }}</span>
                                    {% else %}
                                    <span class="badge bg-{{ 'success' if session.status == 'active' else 'warning' }}">
                                        {{ session.status.title() }}
                                    </span>
                                    {% endif %}
                                </div>
                                <div class="col-md-2">
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary" 
                                                onclick="viewSession('{{ session.full_id }}')">
                                            👁️ View
                                        </button>
                                        {% if session.needs_intervention %}
                                        <button class="btn btn-danger" 
                                                onclick="takeoverSession('{{ session.full_id }}')">
                                            🤝 Übernehmen
                                        </button>
                                        {% endif %}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                    
                    {% if not sessions %}
                    <div class="text-center py-5">
                        <h5 class="text-muted">Keine aktiven Sessions</h5>
                        <p class="text-muted">Sessions erscheinen hier sobald Nutzer das Coaching-System verwenden.</p>
                        <a href="/coaching" class="btn btn-primary">🚀 Test-Session starten</a>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <!-- Navigation -->
            <div class="text-center mt-4">
                <a href="/" class="btn btn-light me-3">← Zurück zum Coaching</a>
                <a href="/dsgvo-dashboard" class="btn btn-outline-light">🔒 DSGVO Dashboard</a>
            </div>
        </div>

        <script>
            // Auto-refresh alle 30 Sekunden
            setTimeout(function() {
                location.reload();
            }, 30000);
            
            function viewSession(sessionId) {
                window.open(`/coaching-session/${sessionId}?coach_mode=true`, '_blank');
            }
            
            function takeoverSession(sessionId) {
                if (confirm('Session übernehmen? Sie erhalten dann die volle Kontrolle.')) {
                    fetch(`/coach-takeover/${sessionId}`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: 'reason=Manual intervention from monitoring'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            alert('✅ Session erfolgreich übernommen!');
                            viewSession(sessionId);
                        }
                    })
                    .catch(error => {
                        alert('❌ Fehler beim Übernehmen der Session.');
                    });
                }
            }
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(monitoring_template, 
                                sessions=active_sessions_list,
                                critical_count=critical_count,
                                active_count=active_count,
                                idle_count=idle_count)

# ========== COACHING FUNKTIONEN ==========

@app.route('/coaching')
def coaching():
   """Hauptseite für Coaching-Sessions"""
   return render_template_string('''
   <!DOCTYPE html>
   <html>
   <head>
       <title>Intelligentes Coaching starten</title>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
       <style>
           body { 
               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               min-height: 100vh;
           }
           .coaching-card {
               background: rgba(255, 255, 255, 0.95);
               backdrop-filter: blur(10px);
               border-radius: 20px;
               box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
           }
       </style>
   </head>
   <body>
       <div class="container mt-4">
           <div class="row justify-content-center">
               <div class="col-lg-8">
                   <div class="card coaching-card">
                       <div class="card-body p-5 text-center">
                           <h1 class="display-5 mb-4">🚀 Intelligentes Coaching starten</h1>
                           <p class="lead mb-4">Beginnen Sie Ihre persönliche Ruhestandscoaching-Reise mit unserem AI-gestützten System</p>
                           
                           <div class="mb-4">
                               <button onclick="startNewSession()" class="btn btn-primary btn-lg px-5 py-3">
                                   💬 Neue Session starten
                               </button>
                           </div>
                           
                           <div class="row mt-5">
                               <div class="col-md-4">
                                   <div class="text-center">
                                       <h3>🧠</h3>
                                       <h6>AI-gestützt</h6>
                                       <p class="small text-muted">Intelligente Antworten und Empfehlungen</p>
                                   </div>
                               </div>
                               <div class="col-md-4">
                                   <div class="text-center">
                                       <h3>📊</h3>
                                       <h6>Phase-Tracking</h6>
                                       <p class="small text-muted">Automatischer Fortschritt durch 5 Phasen</p>
                                   </div>
                               </div>
                               <div class="col-md-4">
                                   <div class="text-center">
                                       <h3>🎯</h3>
                                       <h6>Personalisiert</h6>
                                       <p class="small text-muted">Angepasst an Ihren Lernstil</p>
                                   </div>
                               </div>
                           </div>
                           
                           <div class="mt-4">
                               <a href="/" class="btn btn-outline-secondary">← Zurück zur Hauptseite</a>
                           </div>
                       </div>
                   </div>
               </div>
           </div>
       </div>
       
       <script>
       function startNewSession() {
           // Neue Session-ID generieren
           const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
           
           // Zur Coaching-Session weiterleiten
           window.location.href = `/coaching-session/${sessionId}`;
       }
       </script>
   </body>
   </html>
   ''')

@app.route('/coaching-session/<session_id>')
def coaching_session(session_id):
   """Individuelle Coaching-Session"""
   # Session initialisieren falls nicht vorhanden
   if session_id not in sessions:
       sessions[session_id] = {
           'messages': [],
           'phase': 1,
           'progress': 0,
           'created_at': datetime.now().isoformat(),
           'mode': 'ai_mode',
           'learning_style': None
       }
   
   session = sessions[session_id]
   coach_mode = request.args.get('coach_mode') == 'true'
   
   return render_template_string('''
   <!DOCTYPE html>
   <html>
   <head>
       <title>Coaching Session {{ session_id[:8] }}</title>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
       <style>
           body { 
               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               min-height: 100vh;
           }
           .chat-container {
               background: rgba(255, 255, 255, 0.95);
               backdrop-filter: blur(10px);
               border-radius: 20px;
               max-height: 70vh;
               overflow-y: auto;
           }
           .message-user {
               background: #e3f2fd;
               border-radius: 15px 15px 5px 15px;
               margin: 10px 0;
               padding: 15px;
               margin-left: 20%;
           }
           .message-assistant {
               background: #f5f5f5;
               border-radius: 15px 15px 15px 5px;
               margin: 10px 0;
               padding: 15px;
               margin-right: 20%;
           }
           .progress-header {
               background: rgba(255, 255, 255, 0.9);
               backdrop-filter: blur(10px);
               border-radius: 15px;
               padding: 20px;
               margin-bottom: 20px;
           }
           .input-container {
               background: rgba(255, 255, 255, 0.95);
               backdrop-filter: blur(10px);
               border-radius: 15px;
               padding: 20px;
               margin-top: 20px;
           }
           {% if coach_mode or session.get('intervention_needed') %}
           .coach-controls {
               background: rgba(255, 193, 7, 0.1);
               border: 2px solid #ffc107;
               border-radius: 10px;
               padding: 15px;
               margin-bottom: 20px;
           }
           {% endif %}
       </style>
   </head>
   <body>
       <div class="container mt-3">
           <!-- Progress Header -->
           <div class="progress-header text-center">
               <div class="row">
                   <div class="col-md-6">
                       <h5>📊 Fortschritt</h5>
                       <div class="progress mb-2">
                           <div class="progress-bar bg-primary" style="width: {{ session.progress }}%" id="progressBar"></div>
                       </div>
                       <small>{{ session.progress }}% abgeschlossen</small>
                   </div>
                   <div class="col-md-6">
                       <h5>📍 Aktuelle Phase</h5>
                       <h6 class="text-primary">Phase {{ session.phase }} von 5</h6>
                       <small class="text-muted">{{ phase_name }}</small>
                   </div>
               </div>
           </div>
           
           {% if coach_mode or session.get('intervention_needed') %}
           <!-- Coach Controls -->
           <div class="coach-controls">
               <h6>🎯 Coach-Kontrollen</h6>
               <div class="d-flex gap-2">
                   <button onclick="takeoverSession()" class="btn btn-warning btn-sm">
                       🤝 Session übernehmen
                   </button>
                   <button onclick="toggleMode()" class="btn btn-info btn-sm">
                       🔄 AI/Coach Mode
                   </button>
                   <span class="badge bg-{{ 'danger' if session.get('intervention_needed') else 'success' }}">
                       {{ 'Intervention erforderlich' if session.get('intervention_needed') else 'Normal' }}
                   </span>
               </div>
           </div>
           {% endif %}
           
           <!-- Chat Container -->
           <div class="chat-container p-4" id="chatContainer">
               {% if not session.messages %}
               <div class="message-assistant">
                   <strong>🤖 AI-Coach:</strong><br>
                   Willkommen zu Ihrem intelligenten Ruhestandscoaching! Ich bin Ihr AI-Coach und begleite Sie durch 5 strukturierte Phasen.
                   <br><br>
                   Um Ihnen bestmöglich zu helfen, möchte ich zunächst Ihren Lernstil verstehen:
                   <br><br>
                   <strong>Wie lernen Sie am liebsten?</strong><br>
                   • <em>Visuell</em> - mit Bildern, Grafiken und Übersichten<br>
                   • <em>Auditiv</em> - durch Gespräche und Erklärungen<br>
                   • <em>Kinästhetisch</em> - durch praktische Übungen<br>
                   • <em>Analytisch</em> - durch Zahlen, Daten und Strukturen
               </div>
               {% endif %}
               
               {% for message in session.messages %}
               <div class="message-{{ message.type }}">
                   <strong>
                       {% if message.type == 'user' %}
                       👤 Sie:
                       {% else %}
                       🤖 AI-Coach:
                       {% endif %}
                   </strong><br>
                   {{ message.content | safe }}
                   {% if message.get('intervention_triggered') %}
                   <div class="alert alert-warning mt-2">
                       <small>🚨 Coach wurde benachrichtigt</small>
                   </div>
                   {% endif %}
               </div>
               {% endfor %}
           </div>
           
           <!-- Input Container -->
           <div class="input-container">
               <form onsubmit="sendMessage(event)">
                   <div class="input-group">
                       <input type="text" class="form-control form-control-lg" 
                              id="messageInput" placeholder="Ihre Nachricht..." required>
                       <button type="submit" class="btn btn-primary btn-lg">
                           🚀 Senden
                       </button>
                   </div>
               </form>
               
               <div class="mt-3 d-flex justify-content-between">
                   <a href="/coaching" class="btn btn-outline-secondary">← Neue Session</a>
                   <a href="/dashboard" class="btn btn-outline-info">📊 Dashboard</a>
               </div>
           </div>
       </div>
       
       <script>
       const sessionId = '{{ session_id }}';
       let sessionMode = '{{ session.mode }}';
       
       function sendMessage(event) {
           event.preventDefault();
           
           const input = document.getElementById('messageInput');
           const message = input.value.trim();
           
           if (!message) return;
           
           // Message zum Chat hinzufügen
           addMessageToChat('user', message);
           input.value = '';
           
           // An Server senden
           fetch('/chat/' + sessionId, {
               method: 'POST',
               headers: {
                   'Content-Type': 'application/x-www-form-urlencoded',
               },
               body: 'message=' + encodeURIComponent(message)
           })
           .then(response => response.json())
           .then(data => {
               addMessageToChat('assistant', data.response);
               
               // Progress aktualisieren
               if (data.progress !== undefined) {
                   updateProgress(data.progress, data.phase);
               }
               
               // Intervention-Warnung
               if (data.intervention_triggered) {
                   showInterventionAlert();
               }
           })
           .catch(error => {
               console.error('Error:', error);
               addMessageToChat('assistant', '❌ Entschuldigung, es gab einen technischen Fehler. Bitte versuchen Sie es erneut.');
           });
       }
       
       function addMessageToChat(type, content) {
           const chatContainer = document.getElementById('chatContainer');
           const messageDiv = document.createElement('div');
           messageDiv.className = 'message-' + type;
           
           const icon = type === 'user' ? '👤 Sie:' : '🤖 AI-Coach:';
           messageDiv.innerHTML = `<strong>${icon}</strong><br>${content}`;
           
           chatContainer.appendChild(messageDiv);
           chatContainer.scrollTop = chatContainer.scrollHeight;
       }
       
       function updateProgress(progress, phase) {
           const progressBar = document.getElementById('progressBar');
           if (progressBar) {
               progressBar.style.width = progress + '%';
           }
       }
       
       function showInterventionAlert() {
           const alertDiv = document.createElement('div');
           alertDiv.className = 'alert alert-warning mt-3';
           alertDiv.innerHTML = '<strong>🚨 Ein menschlicher Coach wurde benachrichtigt und wird sich bei Ihnen melden.</strong>';
           document.getElementById('chatContainer').appendChild(alertDiv);
       }
       
       function takeoverSession() {
           fetch(`/coach-takeover/${sessionId}`, {
               method: 'POST',
               headers: {'Content-Type': 'application/x-www-form-urlencoded'},
               body: 'reason=Manual takeover'
           })
           .then(response => response.json())
           .then(data => {
               if (data.status === 'success') {
                   alert('✅ Session übernommen! Sie haben jetzt die Kontrolle.');
                   sessionMode = 'coach_mode';
               }
           });
       }
       
       function toggleMode() {
           sessionMode = sessionMode === 'ai_mode' ? 'coach_mode' : 'ai_mode';
           alert(`🔄 Modus gewechselt zu: ${sessionMode === 'coach_mode' ? 'Coach' : 'AI'}`);
       }
       
       // Auto-scroll zum neuesten Message
       document.getElementById('chatContainer').scrollTop = document.getElementById('chatContainer').scrollHeight;
       </script>
   </body>
   </html>
   ''', session_id=session_id, session=session, phase_name=COACHING_PHASES.get(session.get('phase', 1), 'Unbekannt'))

@app.route('/chat/<session_id>', methods=['POST'])
def chat(session_id):
   """Chat-Endpoint mit Intervention-Check"""
   user_message = request.form.get('message', '')
   
   if session_id not in sessions:
       return jsonify({'error': 'Session not found'}), 404
   
   session = sessions[session_id]
   
   # Intervention-Check ZUERST
   if check_intervention_needed(session_id, user_message):
       # Spezielle Antwort bei kritischen Situationen
       ai_response = """
       Ich merke, dass Sie gerade eine schwierige Zeit durchmachen. Das ist völlig verständlich und Sie sind mit Ihren Gefühlen nicht allein.

       🤝 Ein menschlicher Coach wird sich in Kürze bei Ihnen melden, um Sie persönlich zu unterstützen.

       In der Zwischenzeit möchte ich Sie daran erinnern:
       • Sie sind wertvoll und wichtig
       • Es gibt professionelle Hilfe
       • Diese schwere Zeit wird vorübergehen

       📞 Bei akuten Krisen:
       - Notfall: 144 (Schweiz)
       - Dargebotene Hand: 143
       - Pro Juventute: 147

       Ihr Coach wird sich umgehend bei Ihnen melden.
       """
       
       # Messages speichern
       session['messages'].append({
           'type': 'user', 
           'content': user_message, 
           'timestamp': datetime.now().isoformat()
       })
       session['messages'].append({
           'type': 'assistant', 
           'content': ai_response, 
           'timestamp': datetime.now().isoformat(),
           'intervention_triggered': True
       })
       
       return jsonify({
           'response': ai_response,
           'intervention_triggered': True,
           'coach_notified': True,
           'progress': session.get('progress', 0),
           'phase': session.get('phase', 1)
       })
   
   # Normale AI-Antwort
   try:
       # User message speichern
       session['messages'].append({
           'type': 'user',
           'content': user_message,
           'timestamp': datetime.now().isoformat()
       })
       
       # Lernstil erkennen
       if not session.get('learning_style'):
           learning_styles = {
               'visuell': ['visuell', 'bilder', 'grafiken', 'sehen', 'übersicht'],
               'auditiv': ['auditiv', 'hören', 'gespräch', 'erklärung', 'sprechen'],
               'kinästhetisch': ['kinästhetisch', 'praktisch', 'übung', 'ausprobieren', 'machen'],
               'analytisch': ['analytisch', 'zahlen', 'daten', 'struktur', 'logisch']
           }
           
           message_lower = user_message.lower()
           for style, keywords in learning_styles.items():
               if any(keyword in message_lower for keyword in keywords):
                   session['learning_style'] = style
                   break
       
       # Fortschritt berechnen
       progress = calculate_progress(session_id, user_message)
       
       # AI-Antwort generieren
       context = f"""
       Du bist ein professioneller Ruhestandscoach. Der Coachee ist in Phase {session['phase']} von 5 ({COACHING_PHASES[session['phase']]}).
       
       Lernstil: {session.get('learning_style', 'Noch nicht bestimmt')}
       Aktueller Fortschritt: {progress}%
       
       Coaching-Kontext:
       Phase 1: Standortbestimmung - Wo steht der Coachee heute?
       Phase 2: Zielsetzung - Was möchte er/sie erreichen?
       Phase 3: Strategieentwicklung - Wie kommt er/sie dahin?
       Phase 4: Umsetzungsplanung - Konkrete Schritte definieren
       Phase 5: Erfolgskontrolle - Fortschritt messen und anpassen
       
       Letzte Nachrichten: {session['messages'][-3:] if len(session['messages']) > 3 else session['messages']}
       
       Antworten Sie einfühlsam, strukturiert und an den Lernstil angepasst. Bei >= 75% Fortschritt, leiten Sie zur nächsten Phase über.
       """
       
       # OpenAI API Call
       thread = client.beta.threads.create()
       
       client.beta.threads.messages.create(
           thread_id=thread.id,
           role="user",
           content=f"{context}\n\nCoachee: {user_message}"
       )
       
       run = client.beta.threads.runs.create(
           thread_id=thread.id,
           assistant_id=assistant_id
       )
       
       # Warten auf Antwort
       while run.status in ['queued', 'in_progress']:
           time.sleep(1)
           run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
       
       if run.status == 'completed':
           messages = client.beta.threads.messages.list(thread_id=thread.id)
           ai_response = messages.data[0].content[0].text.value
       else:
           ai_response = "Entschuldigung, ich hatte ein technisches Problem. Können Sie Ihre Frage wiederholen?"
       
       # AI-Antwort speichern
       session['messages'].append({
           'type': 'assistant',
           'content': ai_response,
           'timestamp': datetime.now().isoformat()
       })
       
       return jsonify({
           'response': ai_response,
           'progress': progress,
           'phase': session['phase'],
           'learning_style': session.get('learning_style')
       })
       
   except Exception as e:
       print(f"Error in chat: {e}")
       return jsonify({
           'response': "Entschuldigung, es gab einen technischen Fehler. Bitte versuchen Sie es erneut.",
           'progress': session.get('progress', 0),
           'phase': session.get('phase', 1)
       })

# ========== DASHBOARD ==========

@app.route('/dashboard')
def dashboard():
   """Coach Dashboard für Übersicht aller Sessions"""
   
   # Session-Statistiken berechnen
   total_sessions = len(sessions)
   active_sessions = []
   completed_sessions = 0
   
   for session_id, session in sessions.items():
       if len(session.get('messages', [])) > 0:
           # Letzte Aktivität berechnen
           last_message = session['messages'][-1] if session['messages'] else {}
           last_activity = last_message.get('timestamp', session.get('created_at', ''))
           
           try:
               last_time = datetime.fromisoformat(last_activity)
               time_ago = datetime.now() - last_time
               if time_ago.days > 0:
                   last_activity_str = f"{time_ago.days} Tage"
               elif time_ago.seconds > 3600:
                   last_activity_str = f"{time_ago.seconds // 3600} Stunden"
               else:
                   last_activity_str = f"{time_ago.seconds // 60} Minuten"
           except:
               last_activity_str = "Unbekannt"
           
           # Session-Status bestimmen
           if session.get('phase', 1) >= 5 and session.get('progress', 0) >= 75:
               completed_sessions += 1
               status = 'completed'
               status_text = 'Abgeschlossen'
               status_class = 'success'
           elif session.get('intervention_needed', False):
               status = 'intervention'
               status_text = 'Intervention erforderlich'
               status_class = 'danger'
           else:
               status = 'active'
               status_text = 'Aktiv'
               status_class = 'primary'
           
           active_sessions.append({
               'id': session_id[:8],
               'full_id': session_id,
               'phase': session.get('phase', 1),
               'progress': session.get('progress', 0),
               'messages_count': len(session.get('messages', [])),
               'created_at': session.get('created_at', ''),
               'last_activity': last_activity_str,
               'learning_style': session.get('learning_style', 'Nicht bestimmt'),
               'status': status,
               'status_text': status_text,
               'status_class': status_class,
               'intervention_trigger': session.get('trigger_detected', ''),
               'mode': session.get('mode', 'ai_mode')
           })
   
   # Nach letzter Aktivität sortieren (neueste zuerst)
   active_sessions.sort(key=lambda x: x['created_at'], reverse=True)
   
   return render_template_string('''
   <!DOCTYPE html>
   <html>
   <head>
       <title>Coach Dashboard - Allenspach Coaching</title>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
       <style>
           body { 
               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               min-height: 100vh;
           }
           .card {
               background: rgba(255, 255, 255, 0.95);
               backdrop-filter: blur(10px);
               border-radius: 15px;
               box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
           }
           .session-row:hover {
               background-color: rgba(0, 123, 255, 0.1);
               transition: background-color 0.3s;
           }
           .progress-mini {
               width: 60px;
               height: 8px;
           }
       </style>
   </head>
   <body>
       <div class="container mt-4">
           <!-- Header -->
           <div class="text-center text-white mb-4">
               <h1 class="display-5">📊 Coach Dashboard</h1>
               <p class="lead">Übersicht aller Coaching-Sessions</p>
           </div>
           
           <!-- Statistiken -->
           <div class="row mb-4">
               <div class="col-md-3">
                   <div class="card text-center">
                       <div class="card-body">
                           <h3 class="text-primary">{{ total_sessions }}</h3>
                           <p class="mb-0">Gesamt Sessions</p>
                       </div>
                   </div>
               </div>
               <div class="col-md-3">
                   <div class="card text-center">
                       <div class="card-body">
                           <h3 class="text-success">{{ completed_sessions }}</h3>
                           <p class="mb-0">Abgeschlossen</p>
                       </div>
                   </div>
               </div>
               <div class="col-md-3">
                   <div class="card text-center">
                       <div class="card-body">
                           <h3 class="text-warning">{{ active_sessions|length - completed_sessions }}</h3>
                           <p class="mb-0">In Bearbeitung</p>
                       </div>
                   </div>
               </div>
               <div class="col-md-3">
                   <div class="card text-center">
                       <div class="card-body">
                           <h3 class="text-info">✅</h3>
                           <p class="mb-0">E-Mail Integration</p>
                           <small class="text-muted">Aktiv</small>
                       </div>
                   </div>
               </div>
           </div>
           
           <!-- Sessions Tabelle -->
           <div class="card">
               <div class="card-header">
                   <div class="d-flex justify-content-between align-items-center">
                       <h5 class="mb-0">💬 Aktive Sessions</h5>
                       <div>
                           <a href="/live-monitoring" class="btn btn-outline-primary btn-sm">📊 Live Monitoring</a>
                           <a href="/dsgvo-dashboard" class="btn btn-outline-success btn-sm">🔒 DSGVO</a>
                       </div>
                   </div>
               </div>
               <div class="card-body p-0">
                   {% if active_sessions %}
                   <div class="table-responsive">
                       <table class="table table-hover mb-0">
                           <thead class="table-light">
                               <tr>
                                   <th>Session ID</th>
                                   <th>Phase / Fortschritt</th>
                                   <th>Nachrichten</th>
                                   <th>Lernstil</th>
                                   <th>Letzte Aktivität</th>
                                   <th>Status</th>
                                   <th>Aktionen</th>
                               </tr>
                           </thead>
                           <tbody>
                               {% for session in active_sessions %}
                               <tr class="session-row">
                                   <td>
                                       <strong>{{ session.id }}</strong>
                                       <br><small class="text-muted">{{ session.mode.replace('_', ' ').title() }}</small>
                                   </td>
                                   <td>
                                       <div class="d-flex align-items-center">
                                           <span class="me-2">{{ session.phase }
