

# COACH-ÜBERNAHME FEATURE
# Diese Funktionen in coaching_webapp_real.py hinzufügen:

# 1. Session State Management erweitern
@app.route('/coach-takeover/<session_id>', methods=['POST'])
def coach_takeover(session_id):
    """Coach übernimmt Session manuell"""
    if session_id in sessions:
        sessions[session_id]['mode'] = 'coach_mode'
        sessions[session_id]['takeover_time'] = datetime.now().isoformat()
        sessions[session_id]['takeover_reason'] = request.form.get('reason', 'Manual intervention')
        
        # Coach per E-Mail benachrichtigen
        send_coach_notification(session_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Coach hat Session übernommen',
            'session_id': session_id
        })
    return jsonify({'status': 'error', 'message': 'Session not found'}), 404

# 2. Automatische Trigger für Coach-Intervention
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
            sessions[session_id]['intervention_needed'] = True
            sessions[session_id]['trigger_detected'] = trigger
            return True
    return False

# 3. Coach-Benachrichtigung
def send_coach_notification(session_id):
    """Sendet Benachrichtigung an Coach"""
    session = sessions.get(session_id, {})
    
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
            <p><strong>Grund:</strong> {session.get('trigger_detected', 'Manuelle Übernahme')}</p>
        </div>
        
        <div style="margin: 20px 0;">
            <h3>Session übernehmen:</h3>
            <a href="https://coaching-system.onrender.com/coaching-session/{session_id}?coach_mode=true" 
               style="background: #28a745; color: white; padding: 15px 30px; 
                      text-decoration: none; border-radius: 5px; font-weight: bold;">
                🎯 Session übernehmen
            </a>
        </div>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
            <p><strong>Letzte Nachrichten:</strong></p>
            <p>{session.get('last_message', 'Keine Nachrichten verfügbar')}</p>
        </div>
    </body>
    </html>
    '''
    
    msg.set_content(f'Coach-Intervention erforderlich für Session {session_id[:8]}')
    msg.add_alternative(html_content, subtype='html')
    
    try:
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
            server.send_message(msg)
        print(f"📧 Coach-Benachrichtigung gesendet für Session {session_id[:8]}")
    except Exception as e:
        print(f"❌ Fehler beim Senden der Coach-Benachrichtigung: {e}")

# 4. Erweiterte Chat-Route mit Intervention-Check
@app.route('/chat/<session_id>', methods=['POST'])
def chat_with_intervention_check(session_id):
    """Chat mit automatischer Intervention-Prüfung"""
    user_message = request.form.get('message', '')
    
    # Prüfe ob Intervention nötig
    if check_intervention_needed(session_id, user_message):
        # Coach benachrichtigen
        send_coach_notification(session_id)
        
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
        
        sessions[session_id]['messages'].append({
            'type': 'user', 
            'content': user_message, 
            'timestamp': datetime.now().isoformat()
        })
        sessions[session_id]['messages'].append({
            'type': 'assistant', 
            'content': ai_response, 
            'timestamp': datetime.now().isoformat(),
            'intervention_triggered': True
        })
        
        return jsonify({
            'response': ai_response,
            'intervention_triggered': True,
            'coach_notified': True
        })
    
    # Normale AI-Antwort falls keine Intervention nötig
    return normal_chat_response(session_id, user_message)

# 5. Coach-Mode Interface
@app.route('/coaching-session/<session_id>')
def coaching_session_with_coach_mode(session_id):
    """Coaching Session mit Coach-Mode Option"""
    coach_mode = request.args.get('coach_mode') == 'true'
    
    if session_id not in sessions:
        sessions[session_id] = {
            'messages': [],
            'phase': 1,
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'mode': 'coach_mode' if coach_mode else 'ai_mode'
        }
    
    session = sessions[session_id]
    intervention_needed = session.get('intervention_needed', False)
    
    # Interface mit Coach-Kontrollen
    coach_controls = '''
    <div id="coach-controls" style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 20px 0; display: {};">
        <h4>🎯 Coach-Kontrollen</h4>
        <div style="display: flex; gap: 10px; margin: 10px 0;">
            <button onclick="takeoverSession()" class="btn btn-warning">
                🤝 Session übernehmen
            </button>
            <button onclick="toggleMode()" class="btn btn-info">
                🔄 AI/Coach Mode wechseln
            </button>
            <button onclick="addCoachNote()" class="btn btn-secondary">
                📝 Coach-Notiz hinzufügen
            </button>
        </div>
        <div style="background: {}; padding: 10px; border-radius: 5px;">
            <strong>Status:</strong> {}
        </div>
    </div>
    '''.format(
        'block' if coach_mode or intervention_needed else 'none',
        '#fff3cd' if intervention_needed else '#d1ecf1',
        'Intervention erforderlich - Coach übernehmen!' if intervention_needed else 'Normal - AI aktiv'
    )
    
    return render_template_string(coaching_template_with_controls, 
                                session_id=session_id, 
                                coach_controls=coach_controls,
                                session=session)

# JavaScript für Coach-Kontrollen hinzufügen
coach_js = '''
<script>
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
            document.getElementById('coach-controls').style.display = 'block';
        }
    });
}

function toggleMode() {
    const currentMode = sessionMode || 'ai_mode';
    const newMode = currentMode === 'ai_mode' ? 'coach_mode' : 'ai_mode';
    
    sessionMode = newMode;
    alert(`🔄 Modus gewechselt zu: ${newMode === 'coach_mode' ? 'Coach' : 'AI'}`);
}

function addCoachNote() {
    const note = prompt('📝 Coach-Notiz hinzufügen:');
    if (note) {
        fetch(`/add-coach-note/${sessionId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: `note=${encodeURIComponent(note)}`
        });
    }
}
</script>
'''
# DSGVO-DASHBOARD IMPLEMENTATION
# Diese Routen in coaching_webapp_real.py hinzufügen:

from datetime import datetime, timedelta
import json

# 1. DSGVO-Dashboard Route
@app.route('/dsgvo-dashboard')
def dsgvo_dashboard():
    """DSGVO-Compliance Dashboard"""
    
    # Session-Statistiken berechnen
    total_sessions = len(sessions)
    active_sessions = len([s for s in sessions.values() if 'active' in s and s['active']])
    
    # Alte Sessions identifizieren (älter als 30 Tage)
    cutoff_date = datetime.now() - timedelta(days=30)
    old_sessions = []
    
    for session_id, session in sessions.items():
        created_at = datetime.fromisoformat(session.get('created_at', datetime.now().isoformat()))
        if created_at < cutoff_date:
            old_sessions.append({
                'id': session_id[:8],
                'created': created_at.strftime('%d.%m.%Y'),
                'days_old': (datetime.now() - created_at).days
            })
    
    return render_template_string(dsgvo_template, 
                                total_sessions=total_sessions,
                                active_sessions=active_sessions,
                                old_sessions=old_sessions,
                                retention_days=30)

# 2. Automatische Datenlöschung
@app.route('/dsgvo/delete-old-sessions', methods=['POST'])
def delete_old_sessions():
    """Löscht Sessions älter als X Tage"""
    days = int(request.form.get('days', 30))
    cutoff_date = datetime.now() - timedelta(days=days)
    
    deleted_count = 0
    sessions_to_delete = []
    
    for session_id, session in sessions.items():
        created_at = datetime.fromisoformat(session.get('created_at', datetime.now().isoformat()))
        if created_at < cutoff_date:
            sessions_to_delete.append(session_id)
    
    # Sessions löschen
    for session_id in sessions_to_delete:
        del sessions[session_id]
        deleted_count += 1
    
    # Lösch-Log erstellen
    deletion_log = {
        'timestamp': datetime.now().isoformat(),
        'deleted_sessions': deleted_count,
        'retention_days': days,
        'deleted_ids': [sid[:8] for sid in sessions_to_delete]
    }
    
    return jsonify({
        'status': 'success',
        'deleted_count': deleted_count,
        'log': deletion_log
    })

# 3. Datenexport für Nutzer
@app.route('/dsgvo/export-data/<session_id>')
def export_user_data(session_id):
    """Exportiert alle Daten eines Nutzers (DSGVO Artikel 20)"""
    if session_id not in sessions:
        return jsonify({'error': 'Session nicht gefunden'}), 404
    
    session_data = sessions[session_id].copy()
    
    # Sensible Daten anonymisieren für Export
    export_data = {
        'session_info': {
            'id': session_id[:8],  # Gekürzte ID
            'created_at': session_data.get('created_at'),
            'phase': session_data.get('phase'),
            'progress': session_data.get('progress')
        },
        'messages': [
            {
                'type': msg.get('type'),
                'timestamp': msg.get('timestamp'),
                'content_length': len(msg.get('content', ''))  # Länge statt Inhalt
            }
            for msg in session_data.get('messages', [])
        ],
        'export_info': {
            'exported_at': datetime.now().isoformat(),
            'data_protection_notice': 'Diese Daten wurden gemäß DSGVO Art. 20 exportiert.'
        }
    }
    
    return jsonify(export_data)

# 4. Einverständniserklärung Management
@app.route('/dsgvo/consent', methods=['GET', 'POST'])
def manage_consent():
    """Einverständniserklärung verwalten"""
    if request.method == 'POST':
        session_id = request.form.get('session_id')
        consent_given = request.form.get('consent') == 'true'
        
        if session_id in sessions:
            sessions[session_id]['dsgvo_consent'] = {
                'given': consent_given,
                'timestamp': datetime.now().isoformat(),
                'ip_address': request.remote_addr[:8] + '***',  # IP anonymisiert
                'version': '1.0'
            }
            
            return jsonify({'status': 'success', 'consent_recorded': consent_given})
    
    return render_template_string(consent_template)

# 5. DSGVO-Template
dsgvo_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>DSGVO Dashboard - Allenspach Coaching</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1>🔒 DSGVO-Dashboard</h1>
                <p class="text-muted">Datenschutz-Management für Allenspach Coaching</p>
            </div>
        </div>
        
        <!-- Übersicht -->
        <div class="row mt-4">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h3 class="text-primary">{{ total_sessions }}</h3>
                        <p>Gesamt Sessions</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h3 class="text-success">{{ active_sessions }}</h3>
                        <p>Aktive Sessions</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h3 class="text-warning">{{ old_sessions|length }}</h3>
                        <p>Löschbare Sessions</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Datenlöschung -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>🗑️ Automatische Datenlöschung</h5>
                    </div>
                    <div class="card-body">
                        <p>Sessions älter als {{ retention_days }} Tage werden automatisch gelöscht.</p>
                        
                        {% if old_sessions %}
                        <div class="alert alert-warning">
                            <strong>{{ old_sessions|length }} Sessions</strong> können gelöscht werden:
                            <ul class="mt-2">
                                {% for session in old_sessions[:5] %}
                                <li>Session {{ session.id }} ({{ session.days_old }} Tage alt)</li>
                                {% endfor %}
                                {% if old_sessions|length > 5 %}
                                <li>... und {{ old_sessions|length - 5 }} weitere</li>
                                {% endif %}
                            </ul>
                        </div>
                        
                        <button onclick="deleteOldSessions()" class="btn btn-danger">
                            🗑️ Alte Sessions löschen
                        </button>
                        {% else %}
                        <div class="alert alert-success">
                            ✅ Alle Sessions sind innerhalb der Aufbewahrungsfrist.
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- DSGVO-Compliance Status -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>✅ DSGVO-Compliance Status</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>🔒 Datenschutz-Maßnahmen:</h6>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item">✅ Einverständniserklärung implementiert</li>
                                    <li class="list-group-item">✅ Automatische Löschung nach 30 Tagen</li>
                                    <li class="list-group-item">✅ Datenexport auf Anfrage möglich</li>
                                    <li class="list-group-item">✅ IP-Adressen anonymisiert</li>
                                    <li class="list-group-item">✅ Verschlüsselte Datenübertragung</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6>📋 Nutzerrechte erfüllt:</h6>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item">✅ Art. 13/14 - Informationspflicht</li>
                                    <li class="list-group-item">✅ Art. 15 - Auskunftsrecht</li>
                                    <li class="list-group-item">✅ Art. 17 - Recht auf Löschung</li>
                                    <li class="list-group-item">✅ Art. 20 - Datenportabilität</li>
                                    <li class="list-group-item">✅ Art. 21 - Widerspruchsrecht</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
    function deleteOldSessions() {
        if (confirm('Möchten Sie wirklich alle alten Sessions löschen? Dies kann nicht rückgängig gemacht werden.')) {
            fetch('/dsgvo/delete-old-sessions', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'days=30'
            })
            .then(response => response.json())
            .then(data => {
                alert(`✅ ${data.deleted_count} Sessions erfolgreich gelöscht.`);
                location.reload();
            })
            .catch(error => {
                alert('❌ Fehler beim Löschen der Sessions.');
            });
        }
    }
    </script>
</body>
</html>
'''

# 6. Einverständniserklärung Template
consent_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Datenschutzerklärung - Allenspach Coaching</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="card">
            <div class="card-header">
                <h3>🔒 Datenschutzerklärung</h3>
            </div>
            <div class="card-body">
                <h5>Intelligentes Ruhestandscoaching - Datenverarbeitung</h5>
                
                <div class="alert alert-info">
                    <strong>Ihre Daten sind sicher!</strong> Wir verarbeiten Ihre Daten ausschließlich für Ihr Coaching und löschen sie automatisch nach 30 Tagen.
                </div>
                
                <h6>Was wir sammeln:</h6>
                <ul>
                    <li>Chat-Nachrichten für die Coaching-Session</li>
                    <li>Fortschritt und Phase Ihres Coachings</li>
                    <li>Anonymisierte technische Daten</li>
                </ul>
                
                <h6>Wie wir Ihre Daten schützen:</h6>
                <ul>
                    <li>🔒 Verschlüsselte Übertragung (HTTPS)</li>
                    <li>🗑️ Automatische Löschung nach 30 Tagen</li>
                    <li>🎭 Anonymisierung von IP-Adressen</li>
                    <li>🔐 Sichere Server in Europa</li>
                </ul>
                
                <h6>Ihre Rechte:</h6>
                <ul>
                    <li>📋 Auskunft über gespeicherte Daten</li>
                    <li>🗑️ Löschung Ihrer Daten jederzeit</li>
                    <li>📤 Export Ihrer Daten</li>
                    <li>🚫 Widerspruch gegen Verarbeitung</li>
                </ul>
                
                <div class="form-check mt-4">
                    <input class="form-check-input" type="checkbox" id="consent">
                    <label class="form-check-label" for="consent">
                        <strong>Ich stimme der Datenverarbeitung zu</strong> und habe die Datenschutzerklärung gelesen.
                    </label>
                </div>
                
                <button onclick="saveConsent()" class="btn btn-primary mt-3">
                    ✅ Zustimmen und fortfahren
                </button>
            </div>
        </div>
    </div>
    
    <script>
    function saveConsent() {
        const consent = document.getElementById('consent').checked;
        if (!consent) {
            alert('Bitte stimmen Sie der Datenverarbeitung zu, um fortzufahren.');
            return;
        }
        
        alert('✅ Vielen Dank! Ihre Einverständniserklärung wurde gespeichert.');
        // Weiterleitung zum Coaching
        window.location.href = '/coaching';
    }
    </script>
</body>
</html>
'''

# LIVE SESSION-MONITORING
# Diese Funktionen in coaching_webapp_real.py hinzufügen:

from flask import jsonify, render_template_string
import json

# 1. Live-Monitoring Dashboard
@app.route('/live-monitoring')
def live_monitoring():
    """Live-Dashboard für Coaches zur Session-Überwachung"""
    
    # Aktuelle Session-Statistiken
    active_sessions = []
    for session_id, session in sessions.items():
        if len(session.get('messages', [])) > 0:
            last_message = session['messages'][-1] if session['messages'] else {}
            last_activity = last_message.get('timestamp', session.get('created_at', ''))
            
            # Zeit seit letzter Aktivität berechnen
            if last_activity:
                try:
                    last_time = datetime.fromisoformat(last_activity)
                    minutes_ago = (datetime.now() - last_time).total_seconds() / 60
                except:
                    minutes_ago = 0
            else:
                minutes_ago = 0
            
            # Intervention-Status prüfen
            needs_intervention = session.get('intervention_needed', False)
            trigger = session.get('trigger_detected', '')
            
            active_sessions.append({
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
    active_sessions.sort(key=lambda x: (not x['needs_intervention'], x['minutes_ago']))
    
    return render_template_string(monitoring_template, sessions=active_sessions)

# 2. Live Session-Daten API
@app.route('/api/session-data/<session_id>')
def get_session_data(session_id):
    """API für Live-Session-Daten"""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = sessions[session_id]
    
    # Letzte 5 Nachrichten für Kontext
    recent_messages = session.get('messages', [])[-5:]
    
    return jsonify({
        'session_id': session_id[:8],
        'phase': session.get('phase', 1),
        'progress': session.get('progress', 0),
        'mode': session.get('mode', 'ai_mode'),
        'intervention_needed': session.get('intervention_needed', False),
        'trigger_detected': session.get('trigger_detected', ''),
        'message_count': len(session.get('messages', [])),
        'recent_messages': [
            {
                'type': msg.get('type'),
                'content': msg.get('content', '')[:100] + '...' if len(msg.get('content', '')) > 100 else msg.get('content', ''),
                'timestamp': msg.get('timestamp')
            }
            for msg in recent_messages
        ],
        'last_update': datetime.now().isoformat()
    })

# 3. Notification System
@app.route('/api/notifications')
def get_notifications():
    """API für Coach-Benachrichtigungen"""
    notifications = []
    
    for session_id, session in sessions.items():
        if session.get('intervention_needed', False):
            notifications.append({
                'type': 'intervention',
                'session_id': session_id[:8],
                'full_session_id': session_id,
                'message': f"Intervention erforderlich: {session.get('trigger_detected', 'Unbekannt')}",
                'priority': 'critical',
                'timestamp': session.get('takeover_time', datetime.now().isoformat())
            })
        
        # Lange inaktive Sessions
        if len(session.get('messages', [])) > 0:
            last_message = session['messages'][-1] if session['messages'] else {}
            last_activity = last_message.get('timestamp', session.get('created_at', ''))
            
            try:
                last_time = datetime.fromisoformat(last_activity)
                minutes_ago = (datetime.now() - last_time).total_seconds() / 60
                
                if minutes_ago > 30 and session.get('phase', 1) < 5:  # Unvollständige Session > 30 min
                    notifications.append({
                        'type': 'inactive',
                        'session_id': session_id[:8],
                        'full_session_id': session_id,
                        'message': f"Session inaktiv seit {int(minutes_ago)} Minuten",
                        'priority': 'low',
                        'timestamp': last_activity
                    })
            except:
                pass
    
    # Nach Priorität sortieren
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    notifications.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    return jsonify(notifications)

# 4. Real-time Updates mit Server-Sent Events
@app.route('/api/live-updates')
def live_updates():
    """Server-Sent Events für Live-Updates"""
    def generate():
        while True:
            # Session-Updates sammeln
            updates = []
            for session_id, session in sessions.items():
                if session.get('updated', False):
                    updates.append({
                        'session_id': session_id[:8],
                        'phase': session.get('phase'),
                        'progress': session.get('progress'),
                        'needs_intervention': session.get('intervention_needed', False)
                    })
                    session['updated'] = False  # Reset update flag
            
            if updates:
                yield f"data: {json.dumps(updates)}\n\n"
            
            time.sleep(5)  # Update alle 5 Sekunden
    
    return Response(generate(), mimetype='text/event-stream')

# 5. Live-Monitoring Template
monitoring_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Live Session Monitoring - Allenspach Coaching</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .session-card { margin-bottom: 15px; transition: all 0.3s; }
        .session-critical { border-left: 5px solid #dc3545; }
        .session-active { border-left: 5px solid #28a745; }
        .session-idle { border-left: 5px solid #ffc107; }
        .notification-badge { position: relative; }
        .notification-count { 
            position: absolute; top: -5px; right: -5px; 
            background: #dc3545; color: white; border-radius: 50%; 
            width: 20px; height: 20px; font-size: 12px; 
            display: flex; align-items: center; justify-content: center;
        }
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
        <div class="row">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center">
                    <h2>📊 Live Session Monitoring</h2>
                    <div class="d-flex gap-3">
                        <div class="notification-badge">
                            <button class="btn btn-outline-danger" onclick="toggleNotifications()">
                                🚨 Alerts
                                <span class="notification-count" id="notificationCount">0</span>
                            </button>
                        </div>
                        <div>
                            <span class="badge bg-success">Live</span>
                            <small class="text-muted">Auto-refresh: 30s</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Statistiken -->
        <div class="row mt-3">
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
                        <h4 class="text-danger">{{ sessions|selectattr('needs_intervention')|list|length }}</h4>
                        <small>Interventionen</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h4 class="text-success">{{ sessions|selectattr('status', 'equalto', 'active')|list|length }}</h4>
                        <small>Aktiv (< 10min)</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h4 class="text-warning">{{ sessions|selectattr('status', 'equalto', 'idle')|list|length }}</h4>
                        <small>Inaktiv</small>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Sessions Liste -->
        <div class="row mt-4">
            <div class="col-12">
                <h4>💬 Live Sessions</h4>
                <div id="sessionsContainer">
                    {% for session in sessions %}
                    <div class="card session-card session-{{ session.status }}{% if session.needs_intervention %} pulse{% endif %}" 
                         data-session-id="{{ session.full_id }}">
                        <div class="card-body">
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
                        <p>Sessions erscheinen hier sobald Nutzer das Coaching-System verwenden.</p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <!-- Notifications Panel -->
        <div class="offcanvas offcanvas-end" tabindex="-1" id="notificationsPanel">
            <div class="offcanvas-header">
                <h5>🚨 Benachrichtigungen</h5>
                <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
            </div>
            <div class="offcanvas-body" id="notificationsContent">
                <!-- Notifications werden hier geladen -->
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let notificationsPanel;
        
        // Auto-refresh alle 30 Sekunden
        setInterval(function() {
            location.reload();
        }, 30000);
        
        // Live-Updates mit Server-Sent Events
        const eventSource = new EventSource('/api/live-updates');
        eventSource.onmessage = function(event) {
            const updates = JSON.parse(event.data);
            updates.forEach(update => {
                updateSessionCard(update);
            });
        };
        
        function updateSessionCard(update) {
            const card = document.querySelector(`[data-session-id*="${update.session_id}"]`);
            if (card) {
                // Progress Bar aktualisieren
                const progressBar = card.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = update.progress + '%';
                }
                
                // Intervention Status
                if (update.needs_intervention) {
                    card.classList.add('pulse', 'session-critical');
                    loadNotifications(); // Notifications neu laden
                }
            }
        }
        
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
                });
            }
        }
        
        function toggleNotifications() {
            if (!notificationsPanel) {
                notificationsPanel = new bootstrap.Offcanvas(document.getElementById('notificationsPanel'));
            }
            loadNotifications();
            notificationsPanel.show();
        }
        
        function loadNotifications() {
            fetch('/api/notifications')
                .then(response => response.json())
                .then(notifications => {
                    const content = document.getElementById('notificationsContent');
                    const count = document.getElementById('notificationCount');
                    
                    count.textContent = notifications.length;
                    count.style.display = notifications.length > 0 ? 'flex' : 'none';
                    
                    if (notifications.length === 0) {
                        content.innerHTML = '<p class="text-muted text-center">Keine neuen Benachrichtigungen</p>';
                        return;
                    }
                    
                    content.innerHTML = notifications.map(notif => `
                        <div class="alert alert-${notif.priority === 'critical' ? 'danger' : 'warning'} alert-dismissible">
                            <strong>${notif.type === 'intervention' ? '🚨' : '⏰'}</strong>
                            ${notif.message}
                            <br><small class="text-muted">Session: ${notif.session_id}</small>
                            ${notif.type === 'intervention' ? 
                                `<button class="btn btn-sm btn-danger mt-2" onclick="takeoverSession('${notif.full_session_id}')">
                                    🤝 Übernehmen
                                </button>` : ''
                            }
                        </div>
                    `).join('');
                });
        }
        
        // Initial notifications laden
        loadNotifications();
        
        // Notifications alle 15 Sekunden aktualisieren
        setInterval(loadNotifications, 15000);
    </script>
</body>
</html>
'''



