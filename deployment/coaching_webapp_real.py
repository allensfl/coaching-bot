#!/usr/bin/env python3
import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import uuid, time, re
from datetime import datetime
import smtplib
import imaplib
import email
from email.message import EmailMessage
import threading

load_dotenv()
app = Flask(__name__)
sessions = {}

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# E-Mail-Konfiguration
EMAIL_CONFIG = {
    'address': os.getenv('DELTA_EMAIL', 'bot@allenspach-coaching.ch'),
    'password': os.getenv('DELTA_PASSWORD'),
    'smtp_server': 'mail.cyon.ch',
    'smtp_port': 587,
    'imap_server': 'mail.cyon.ch', 
    'imap_port': 993
}

# Intelligente Phase-Definitionen
PHASE_KEYWORDS = {
    1: ['lernstil', 'ausgangssituation', 'herzenswunsch', 'standort'],
    2: ['gefühle', 'emotionen', 'schlüsselaffekt', 'bildarbeit'], 
    3: ['inneres team', 'teufelskreislauf', 'muster', 'systemanalyse'],
    4: ['erfolgsimagination', 'vision', 'schritte', 'zukunft'],
    5: ['erfolge', 'integration', 'learnings', 'abschluss']
}

def create_session():
    sid = str(uuid.uuid4())[:8]
    thread = client.beta.threads.create()
    sessions[sid] = {
        'id': sid,
        'thread_id': thread.id,
        'current_phase': 1,
        'phase_progress': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        'total_progress': 0,
        'messages': [],
        'created': datetime.now()
    }
    return sid

def analyze_progress(message, response, session):
    """Intelligente Fortschrittsanalyse"""
    current_phase = session['current_phase']
    text = (message + " " + response).lower()
    
    # Keywords für aktuelle Phase zählen
    keywords = PHASE_KEYWORDS[current_phase]
    matches = sum(1 for keyword in keywords if keyword in text)
    
    # Progress berechnen (25% pro Keyword)
    new_progress = min(matches * 25, 100)
    session['phase_progress'][current_phase] = max(
        session['phase_progress'][current_phase], 
        new_progress
    )
    
    # Automatischer Phasenwechsel bei 75%+ und nächste Phase hat Aktivität
    if (session['phase_progress'][current_phase] >= 75 and 
        current_phase < 5 and
        any(kw in text for kw in PHASE_KEYWORDS.get(current_phase + 1, []))):
        session['current_phase'] = current_phase + 1
        session['phase_progress'][current_phase + 1] = 15  # Start der neuen Phase
    
    # Gesamtfortschritt berechnen
    total = sum(session['phase_progress'].values()) / 5
    session['total_progress'] = min(total, 100)
    
    return {
        'current_phase': session['current_phase'],
        'total_progress': session['total_progress'],
        'phase_progress': session['phase_progress'],
        'phase_changed': current_phase != session['current_phase']
    }

def get_ai_response(thread_id, message, session):
    """OpenAI Response mit Phase-Kontext"""
    try:
        phase_context = f"""
Du bist ein Ruhestandscoach. Aktuelle Phase: {session['current_phase']}/5
Führe systematisch durch das 8-Aufträge-System. Verwende Du-Form und Guillemets « ».
Beginne mit Lernstil-Abfrage bei neuen Sessions.
        """
        
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user", 
            content=f"KONTEXT: {phase_context}\n\nUSER: {message}"
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        
        while run.status in ['queued', 'in_progress']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for msg in messages.data:
            if msg.role == 'assistant':
                return msg.content[0].text.value
                
        return "Entschuldigung, ich konnte keine Antwort generieren."
    except Exception as e:
        return f"Fehler: {str(e)}"

def send_coaching_email(to_email, subject, message, session_link=None):
    """Sendet professionelle Coaching-E-Mail"""
    try:
        msg = EmailMessage()
        msg['From'] = EMAIL_CONFIG['address']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Professionelle HTML-E-Mail
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white;">
                <h1>🎯 Allenspach Coaching</h1>
                <p>Intelligentes Ruhestandscoaching</p>
            </div>
            
            <div style="padding: 30px; background: white;">
                <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin: 20px 0;">
                    {message.replace(chr(10), '<br>')}
                </div>
                
                {f'''
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{session_link}" 
                       style="background: #28a745; color: white; padding: 15px 30px; 
                              text-decoration: none; border-radius: 25px; font-weight: bold; 
                              box-shadow: 0 4px 15px rgba(40,167,69,0.3);">
                        🚀 Intelligentes Coaching starten
                    </a>
                </div>
                ''' if session_link else ''}
                
                <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h4>🧠 Ihr intelligenter AI-Coach bietet:</h4>
                    <ul>
                        <li>✅ Automatisches Phase-Tracking</li>
                        <li>✅ Personalisierte Coaching-Anpassung</li>
                        <li>✅ Strukturiertes 8-Aufträge-System</li>
                        <li>✅ Echtzeit-Fortschrittsanzeige</li>
                    </ul>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px;">
                <p>Diese E-Mail wurde automatisch vom intelligenten Coaching-System generiert.</p>
                <p>Bei Fragen antworten Sie einfach auf diese E-Mail.</p>
                <p>🌐 <a href="https://coaching.allenspach-coaching.ch">coaching.allenspach-coaching.ch</a></p>
            </div>
        </body>
        </html>
        """
        
        # Plain text Fallback
        msg.set_content(f"""
Hallo,

{message}

{f'Ihr Coaching-Link: {session_link}' if session_link else ''}

Mit freundlichen Grüßen
Ihr intelligenter AI-Coach

Allenspach Coaching
coaching.allenspach-coaching.ch
        """)
        
        # HTML-Version hinzufügen
        msg.add_alternative(html_content, subtype='html')
        
        # E-Mail senden
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
            server.send_message(msg)
            
        print(f"📧 E-Mail gesendet an: {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ E-Mail Fehler: {e}")
        return False

def check_email_inbox():
    """Überwacht E-Mail-Posteingang und antwortet automatisch"""
    try:
        with imaplib.IMAP4_SSL(EMAIL_CONFIG['imap_server'], EMAIL_CONFIG['imap_port']) as mail:
            mail.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
            mail.select('INBOX')
            
            # Ungelesene E-Mails suchen
            status, messages = mail.search(None, 'UNSEEN')
            
            if messages[0]:
                for msg_id in messages[0].split():
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            sender_email = msg['From']
                            subject = msg['Subject'] or "Coaching Anfrage"
                            
                            # E-Mail Inhalt extrahieren
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        payload = part.get_payload(decode=True)
                                        if payload:
                                            body = payload.decode('utf-8', errors='ignore')
                            else:
                                payload = msg.get_payload(decode=True)
                                if payload:
                                    body = payload.decode('utf-8', errors='ignore')
                            
                            if body.strip():
                                # Neue Coaching-Session erstellen
                                session_id = create_session()
                                
                                # AI-Response generieren
                                session = sessions[session_id]
                                ai_response = get_ai_response(session['thread_id'], body, session)
                                
                                # Session-Link erstellen
                                session_link = f"http://localhost:8080/coaching-session/{session_id}"
                                
                                # Professionelle E-Mail-Antwort
                                email_response = f"""
Herzlich willkommen zum intelligenten Ruhestandscoaching!

Vielen Dank für Ihre Nachricht. Ich habe Ihre Anfrage gelesen und eine erste Antwort für Sie vorbereitet:

{ai_response}

Für ein vollständiges, interaktives Coaching-Erlebnis mit automatischem Phase-Tracking und Echtzeit-Fortschrittsanzeige nutzen Sie bitte den Link unten. Dort führe ich Sie strukturiert durch unser bewährtes 8-Aufträge-System.
                                """
                                
                                # E-Mail senden
                                response_subject = f"Re: {subject} - Ihr intelligenter Coaching-Assistent"
                                send_coaching_email(sender_email, response_subject, email_response, session_link)
                                
                                # Session-Info speichern
                                session['email'] = sender_email
                                session['initial_message'] = body
                                
                                print(f"🎯 Neue Coaching-Session erstellt: {session_id} für {sender_email}")
                            
                            # Als gelesen markieren
                            mail.store(msg_id, '+FLAGS', '\\Seen')
                        
    except Exception as e:
        print(f"📧 E-Mail Check Fehler: {e}")

def start_email_monitor():
    """Startet E-Mail-Überwachung im Hintergrund"""
    def monitor():
        print("📧 E-Mail Monitor gestartet...")
        while True:
            try:
                if EMAIL_CONFIG['password']:
                    check_email_inbox()
                    time.sleep(60)  # Alle 60 Sekunden prüfen
                else:
                    print("⚠️ E-Mail-Password nicht gesetzt - Monitor wartet...")
                    time.sleep(300)  # 5 Minuten warten
            except Exception as e:
                print(f"📧 Monitor Fehler: {e}")
                time.sleep(120)  # 2 Minuten bei Fehler
    
    thread = threading.Thread(target=monitor)
    thread.daemon = True
    thread.start()

@app.route("/")
def home():
    return '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>🧠 Intelligentes Ruhestandscoaching</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; margin: 0; color: white; text-align: center; padding: 50px; }
        .cockpit { background: white; color: #333; padding: 40px; border-radius: 20px; margin: 20px auto; max-width: 900px; box-shadow: 0 20px 40px rgba(0,0,0,0.2); }
        .progress-section { display: flex; align-items: center; justify-content: center; gap: 30px; margin: 30px 0; }
        .progress-circle { 
            width: 100px; height: 100px; border-radius: 50%; 
            background: conic-gradient(#28a745 0deg, #28a745 0deg, #e9ecef 0deg, #e9ecef 360deg);
            display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem;
        }
        .phases-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 30px 0; }
        .phase { 
            padding: 20px; border-radius: 12px; position: relative; transition: all 0.3s ease;
            cursor: pointer; border: 2px solid transparent;
        }
        .phase.pending { background: #6c757d; color: white; }
        .phase.active { background: #007bff; color: white; transform: scale(1.05); border-color: #ffc107; }
        .phase.completed { background: #28a745; color: white; }
        .phase-progress { 
            position: absolute; bottom: 0; left: 0; height: 4px; 
            background: rgba(255,255,255,0.3); border-radius: 0 0 12px 12px; 
            transition: width 0.5s ease;
        }
        .btn { background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 15px; display: inline-block; font-weight: bold; transition: all 0.3s ease; }
        .btn:hover { background: #218838; transform: translateY(-2px); }
        .features { background: #f8f9fa; padding: 20px; border-radius: 15px; margin: 20px 0; }
        .email-info { background: #e8f5e8; padding: 20px; border-radius: 15px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>🧠 Intelligentes Ruhestandscoaching</h1>
    <p>Mit automatischem Phase-Tracking und E-Mail-Integration</p>
    
    <div class="cockpit">
        <div class="progress-section">
            <div>
                <h3>📊 Gesamtfortschritt</h3>
                <div class="progress-circle" id="progressCircle">0%</div>
            </div>
            <div>
                <h3>📍 Aktuelle Phase</h3>
                <div style="font-size: 1.5rem; font-weight: bold; color: #007bff;">Phase 1 von 5</div>
                <small>Standortbestimmung</small>
            </div>
        </div>
        
        <h3>📋 Coaching-Phasen</h3>
        <div class="phases-grid">
            <div class="phase active" id="phase1">
                <strong>Phase 1: Standortbestimmung</strong>
                <p>Lernstil & Ausgangssituation</p>
                <div class="phase-progress" style="width: 0%;"></div>
            </div>
            <div class="phase pending" id="phase2">
                <strong>Phase 2: Emotionale Vertiefung</strong>
                <p>Gefühle & Schlüsselaffekt</p>
                <div class="phase-progress" style="width: 0%;"></div>
            </div>
            <div class="phase pending" id="phase3">
                <strong>Phase 3: Systemanalyse</strong>
                <p>Muster & Teufelskreislauf</p>
                <div class="phase-progress" style="width: 0%;"></div>
            </div>
            <div class="phase pending" id="phase4">
                <strong>Phase 4: Zukunftsgestaltung</strong>
                <p>Vision & konkrete Schritte</p>
                <div class="phase-progress" style="width: 0%;"></div>
            </div>
            <div class="phase pending" id="phase5">
                <strong>Phase 5: Integration</strong>
                <p>Erfolge & Learnings</p>
                <div class="phase-progress" style="width: 0%;"></div>
            </div>
        </div>
        
        <div class="email-info">
            <h4>📧 E-Mail-Integration aktiv</h4>
            <p><strong>bot@allenspach-coaching.ch</strong> - Automatische AI-Antworten</p>
            <small>Senden Sie eine E-Mail und erhalten Sie sofort eine intelligente Antwort mit Link zu Ihrer persönlichen Coaching-Session!</small>
        </div>
        
        <div class="features">
            <h4>🚀 Intelligente Features</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; text-align: left;">
                <div>✅ Automatisches Phase-Tracking</div>
                <div>✅ Echtzeit-Fortschrittsanzeige</div>
                <div>✅ Intelligente Phasenübergänge</div>
                <div>✅ E-Mail-Integration</div>
            </div>
        </div>
        
        <a href="/coaching" class="btn">🚀 Intelligentes Coaching starten</a>
        <a href="/dashboard" class="btn">📊 Coach Dashboard</a>
        <a href="/test-email" class="btn">📧 E-Mail System testen</a>
    </div>
</body>
</html>'''

@app.route("/coaching")
def coaching():
    session_id = create_session()
    return f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Intelligentes Ruhestandscoaching Chat</title>
    <style>
        body {{ font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; margin: 0; }}
        .chat-container {{ max-width: 1000px; margin: 0 auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.2); }}
        .chat-header {{ background: #28a745; color: white; padding: 25px; text-align: center; }}
        .progress-bar {{ background: #20c997; padding: 15px; color: white; display: flex; justify-content: space-between; align-items: center; }}
        .progress-track {{ flex: 1; height: 8px; background: rgba(255,255,255,0.3); border-radius: 4px; margin: 0 20px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: white; border-radius: 4px; transition: width 0.5s ease; width: 0%; }}
        .messages {{ height: 500px; overflow-y: auto; padding: 25px; background: #fafafa; }}
        .message {{ margin: 20px 0; display: flex; gap: 15px; }}
        .message.user {{ flex-direction: row-reverse; }}
        .message-content {{ max-width: 75%; padding: 15px 20px; border-radius: 18px; line-height: 1.5; }}
        .message.assistant .message-content {{ background: white; border: 1px solid #e9ecef; }}
        .message.user .message-content {{ background: #007bff; color: white; }}
        .input-area {{ display: flex; padding: 25px; gap: 15px; }}
        .message-input {{ flex: 1; padding: 15px; border: 2px solid #e9ecef; border-radius: 25px; font-size: 16px; }}
        .send-btn {{ background: #28a745; color: white; border: none; padding: 15px 25px; border-radius: 25px; cursor: pointer; font-weight: bold; }}
        .phase-alert {{ background: linear-gradient(45deg, #28a745, #20c997); color: white; padding: 15px; margin: 10px 0; border-radius: 10px; text-align: center; animation: slideIn 0.5s ease; }}
        @keyframes slideIn {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h2>🧠 Intelligentes Ruhestandscoaching</h2>
            <small>Session: {session_id} | AI-gesteuertes Phase-Tracking aktiv</small><br>
            <a href="/" style="color: white; text-decoration: none;">← Zurück zum Dashboard</a>
        </div>
        
        <div class="progress-bar">
            <div id="currentPhase">📍 Phase 1: Standortbestimmung</div>
            <div class="progress-track">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div id="overallProgress">0% abgeschlossen</div>
        </div>
        
        <div class="messages" id="messages">
            <div class="message assistant">
                <div class="message-content">
                    🎯 Herzlich willkommen zum intelligenten Ruhestandscoaching!

Ich bin Ihr AI-Coach und erkenne automatisch Ihren Fortschritt durch unser 8-Aufträge-System. 

📍 Wir beginnen mit Phase 1: Standortbestimmung

Bevor wir starten - wie lernen Sie am liebsten?
- 👁️ Visuell (Bilder, Diagramme)
- 👂 Auditiv (Gespräche, Erklärungen) 
- ✋ Kinästhetisch (Übungen, Ausprobieren)

Antworten Sie einfach mit "visuell", "auditiv" oder "kinästhetisch"!
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="messageInput" class="message-input" placeholder="Ihre Nachricht..." />
            <button onclick="sendMessage()" class="send-btn" id="sendBtn">🚀 Senden</button>
        </div>
    </div>

    <script>
        const sessionId = '{session_id}';
        
        function addMessage(sender, content) {{
            const container = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'message ' + sender;
            div.innerHTML = '<div class="message-content">' + content + '</div>';
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }}
        
        function showPhaseTransition(newPhase) {{
            const phaseNames = ['', 'Standortbestimmung', 'Emotionale Vertiefung', 'Systemanalyse', 'Zukunftsgestaltung', 'Integration'];
            const container = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'phase-alert';
            div.innerHTML = `🎉 Phase ${{newPhase}}: ${{phaseNames[newPhase]}} erreicht!`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }}
        
        function updateProgress(data) {{
            if (!data) return;
            
            const phaseNames = ['', 'Standortbestimmung', 'Emotionale Vertiefung', 'Systemanalyse', 'Zukunftsgestaltung', 'Integration'];
            
            document.getElementById('currentPhase').textContent = 
                `📍 Phase ${{data.current_phase}}: ${{phaseNames[data.current_phase]}}`;
            
            document.getElementById('progressFill').style.width = data.total_progress + '%';
            document.getElementById('overallProgress').textContent = 
                Math.round(data.total_progress) + '% abgeschlossen';
            
            if (data.phase_changed) {{
                showPhaseTransition(data.current_phase);
            }}
        }}
        
        function sendMessage() {{
            const input = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage('user', message);
            input.value = '';
            
            sendBtn.disabled = true;
            sendBtn.textContent = '⏳ AI analysiert...';
            addMessage('assistant', '<em style="color: #666;">🧠 Intelligenter Coach analysiert Ihren Fortschritt...</em>');
            
            fetch('/api/intelligent-chat', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{session_id: sessionId, message: message}})
            }})
            .then(r => r.json())
            .then(data => {{
                const messages = document.getElementById('messages');
                messages.removeChild(messages.lastChild);
                
                addMessage('assistant', data.response);
                updateProgress(data.progress);
                
                sendBtn.disabled = false;
                sendBtn.textContent = '🚀 Senden';
            }});
        }}
        
        document.getElementById('messageInput').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') sendMessage();
        }});
    </script>
</body>
</html>'''

@app.route('/api/intelligent-chat', methods=['POST'])
def intelligent_chat():
    data = request.json
    sid = data['session_id']
    message = data['message']
    
    session = sessions.get(sid)
    if not session:
        return jsonify({'error': 'Session nicht gefunden'}), 404
    
    # AI Response generieren
    ai_response = get_ai_response(session['thread_id'], message, session)
    
    # Intelligente Fortschrittsanalyse
    progress_data = analyze_progress(message, ai_response, session)
    
    # Messages speichern
    session['messages'].extend([
        {'sender': 'user', 'message': message, 'timestamp': datetime.now().isoformat()},
        {'sender': 'assistant', 'message': ai_response, 'timestamp': datetime.now().isoformat()}
    ])
    
    return jsonify({
        'response': ai_response,
        'progress': progress_data
    })

@app.route("/coaching-session/<session_id>")
def email_coaching_session(session_id):
    """Spezielle Route für E-Mail-Sessions"""
    session = sessions.get(session_id)
    if not session:
        return '''<h1>❌ Session nicht gefunden</h1>
        <p>Diese Coaching-Session ist nicht mehr verfügbar.</p>
        <a href="/coaching">Neue Session starten</a>'''
    
    return f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>E-Mail Coaching Session</title>
    <style>
        body {{ font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .welcome {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 20px; text-align: center; }}
        .btn {{ background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 10px; display: inline-block; }}
    </style>
</head>
<body>
    <div class="welcome">
        <h1>🎯 Willkommen zurück!</h1>
        <p>Ihre Coaching-Session ist bereit. Sie wurden automatisch von unserem E-Mail-System weitergeleitet.</p>
        
        <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3>📧 E-Mail-Adresse:</h3>
            <p>{session.get('email', 'Unbekannt')}</p>
            
            <h3>💬 Ihre ursprüngliche Nachricht:</h3>
            <p style="font-style: italic;">"{session.get('initial_message', 'Keine Nachricht')[:100]}..."</p>
        </div>
        
        <a href="/coaching" class="btn">🚀 Zum intelligenten Coaching-Chat</a>
        <a href="/" class="btn">🏠 Zum Dashboard</a>
    </div>
</body>
</html>'''

@app.route("/dashboard")
def dashboard():
    return f'''<!DOCTYPE html>
<html>
<head><title>Coach Dashboard</title></head>
<body style="font-family: Arial; padding: 40px; background: #f8f9fa;">
    <div style="max-width: 1000px; margin: 0 auto;">
        <h1>📊 Coach Dashboard</h1>
        <p>Aktive Sessions: {len(sessions)}</p>
        
        <div style="background: #e8f5e8; padding: 20px; border-radius: 15px; margin: 20px 0;">
            <h3>📧 E-Mail-Integration Status</h3>
            <p><strong>E-Mail:</strong> {EMAIL_CONFIG['address']}</p>
            <p><strong>Status:</strong> {'✅ Aktiv' if EMAIL_CONFIG['password'] else '❌ Passwort fehlt'}</p>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">
            {chr(10).join([f'''
            <div style="background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <h4>Session {s['id']}</h4>
                <p>Phase: {s['current_phase']}/5</p>
                <p>Fortschritt: {s['total_progress']:.1f}%</p>
                {f"<p>E-Mail: {s.get('email', 'Keine E-Mail')}</p>" if s.get('email') else ''}
                <div style="width: 100%; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                    <div style="width: {s['total_progress']}%; height: 100%; background: #28a745; border-radius: 4px;"></div>
                </div>
            </div>
            ''' for s in sessions.values()])}
        </div>
        
        <a href="/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">← Zurück</a>
    </div>
</body>
</html>'''

@app.route("/test-email")
def test_email():
    """Test-Route für E-Mail-Funktionalität"""
    return f'''<!DOCTYPE html>
<html>
<head><title>E-Mail System Test</title></head>
<body style="font-family: Arial; padding: 40px;">
    <h1>📧 E-Mail System Test</h1>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h3>📋 Konfiguration:</h3>
        <p><strong>E-Mail:</strong> {EMAIL_CONFIG['address']}</p>
        <p><strong>SMTP Server:</strong> {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}</p>
        <p><strong>IMAP Server:</strong> {EMAIL_CONFIG['imap_server']}:{EMAIL_CONFIG['imap_port']}</p>
        <p><strong>Password gesetzt:</strong> {'✅ Ja' if EMAIL_CONFIG['password'] else '❌ Nein'}</p>
    </div>
    
    <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h3>🧪 So testen Sie:</h3>
        <ol>
            <li>Senden Sie eine E-Mail an: <strong>{EMAIL_CONFIG['address']}</strong></li>
            <li>Das System antwortet automatisch mit AI-Response</li>
            <li>Sie erhalten einen Link zu Ihrer persönlichen Coaching-Session</li>
            <li>Über den Link gelangen Sie zum intelligenten Chat</li>
        </ol>
    </div>
    
    <div style="background: #fff3cd; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h4>⚠️ Wichtige Hinweise:</h4>
        <ul>
            <li>E-Mail-Monitor läuft alle 60 Sekunden</li>
            <li>Nur ungelesene E-Mails werden verarbeitet</li>
            <li>Pro E-Mail wird eine neue Coaching-Session erstellt</li>
            <li>Links sind nur solange gültig wie der Server läuft</li>
        </ul>
    </div>
    
    <a href="/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">← Zurück zum Dashboard</a>
</body>
</html>'''

if __name__ == "__main__":
    print("🧠 INTELLIGENTES Ruhestandscoaching System mit E-Mail-Integration!")
    print(f"🔑 OpenAI verbunden: {os.getenv('OPENAI_API_KEY')[:20]}...")
    print(f"🤖 Assistant: {ASSISTANT_ID}")
    print(f"📧 E-Mail: {EMAIL_CONFIG['address']}")
    print("🎯 Intelligente Features aktiv:")
    print("  ✅ Automatisches Phase-Tracking")
    print("  ✅ Echtzeit-Fortschrittsanzeige") 
    print("  ✅ Intelligente Phasenübergänge")
    print("  ✅ E-Mail-Integration")
    print("🌐 http://localhost:8080")
    
    # E-Mail Monitor starten
    start_email_monitor()
    
    app.run(port=8080, debug=True)
#!/usr/bin/env python3
import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import uuid, time, re
from datetime import datetime

load_dotenv()
app = Flask(__name__)
sessions = {}

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Intelligente Phase-Definitionen
PHASE_KEYWORDS = {
    1: ['lernstil', 'ausgangssituation', 'herzenswunsch', 'standort'],
    2: ['gefühle', 'emotionen', 'schlüsselaffekt', 'bildarbeit'], 
    3: ['inneres team', 'teufelskreislauf', 'muster', 'systemanalyse'],
    4: ['erfolgsimagination', 'vision', 'schritte', 'zukunft'],
    5: ['erfolge', 'integration', 'learnings', 'abschluss']
}

def create_session():
    sid = str(uuid.uuid4())[:8]
    thread = client.beta.threads.create()
    sessions[sid] = {
        'id': sid,
        'thread_id': thread.id,
        'current_phase': 1,
        'phase_progress': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        'total_progress': 0,
        'messages': [],
        'created': datetime.now()
    }
    return sid

def analyze_progress(message, response, session):
    """Intelligente Fortschrittsanalyse"""
    current_phase = session['current_phase']
    text = (message + " " + response).lower()
    
    # Keywords für aktuelle Phase zählen
    keywords = PHASE_KEYWORDS[current_phase]
    matches = sum(1 for keyword in keywords if keyword in text)
    
    # Progress berechnen (25% pro Keyword)
    new_progress = min(matches * 25, 100)
    session['phase_progress'][current_phase] = max(
        session['phase_progress'][current_phase], 
        new_progress
    )
    
    # Automatischer Phasenwechsel bei 75%+ und nächste Phase hat Aktivität
    if (session['phase_progress'][current_phase] >= 75 and 
        current_phase < 5 and
        any(kw in text for kw in PHASE_KEYWORDS.get(current_phase + 1, []))):
        session['current_phase'] = current_phase + 1
        session['phase_progress'][current_phase + 1] = 15  # Start der neuen Phase
    
    # Gesamtfortschritt berechnen
    total = sum(session['phase_progress'].values()) / 5
    session['total_progress'] = min(total, 100)
    
    return {
        'current_phase': session['current_phase'],
        'total_progress': session['total_progress'],
        'phase_progress': session['phase_progress'],
        'phase_changed': current_phase != session['current_phase']
    }

def get_ai_response(thread_id, message, session):
    """OpenAI Response mit Phase-Kontext"""
    try:
        phase_context = f"""
Du bist ein Ruhestandscoach. Aktuelle Phase: {session['current_phase']}/5
Führe systematisch durch das 8-Aufträge-System. Verwende Du-Form und Guillemets « ».
Beginne mit Lernstil-Abfrage bei neuen Sessions.
        """
        
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user", 
            content=f"KONTEXT: {phase_context}\n\nUSER: {message}"
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        
        while run.status in ['queued', 'in_progress']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for msg in messages.data:
            if msg.role == 'assistant':
                return msg.content[0].text.value
                
        return "Entschuldigung, ich konnte keine Antwort generieren."
    except Exception as e:
        return f"Fehler: {str(e)}"

@app.route("/")
def home():
    return '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>🧠 Intelligentes Ruhestandscoaching</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; margin: 0; color: white; text-align: center; padding: 50px; }
        .cockpit { background: white; color: #333; padding: 40px; border-radius: 20px; margin: 20px auto; max-width: 900px; box-shadow: 0 20px 40px rgba(0,0,0,0.2); }
        .progress-section { display: flex; align-items: center; justify-content: center; gap: 30px; margin: 30px 0; }
        .progress-circle { 
            width: 100px; height: 100px; border-radius: 50%; 
            background: conic-gradient(#28a745 0deg, #28a745 0deg, #e9ecef 0deg, #e9ecef 360deg);
            display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem;
        }
        .phases-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 30px 0; }
        .phase { 
            padding: 20px; border-radius: 12px; position: relative; transition: all 0.3s ease;
            cursor: pointer; border: 2px solid transparent;
        }
        .phase.pending { background: #6c757d; color: white; }
        .phase.active { background: #007bff; color: white; transform: scale(1.05); border-color: #ffc107; }
        .phase.completed { background: #28a745; color: white; }
        .phase-progress { 
            position: absolute; bottom: 0; left: 0; height: 4px; 
            background: rgba(255,255,255,0.3); border-radius: 0 0 12px 12px; 
            transition: width 0.5s ease;
        }
        .btn { background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 15px; display: inline-block; font-weight: bold; transition: all 0.3s ease; }
        .btn:hover { background: #218838; transform: translateY(-2px); }
        .features { background: #f8f9fa; padding: 20px; border-radius: 15px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>🧠 Intelligentes Ruhestandscoaching</h1>
    <p>Mit automatischem Phase-Tracking und Echtzeit-Fortschrittsanzeige</p>
    
    <div class="cockpit">
        <div class="progress-section">
            <div>
                <h3>📊 Gesamtfortschritt</h3>
                <div class="progress-circle" id="progressCircle">0%</div>
            </div>
            <div>
                <h3>📍 Aktuelle Phase</h3>
                <div style="font-size: 1.5rem; font-weight: bold; color: #007bff;">Phase 1 von 5</div>
                <small>Standortbestimmung</small>
            </div>
        </div>
        
        <h3>📋 Coaching-Phasen</h3>
        <div class="phases-grid">
            <div class="phase active" id="phase1">
                <strong>Phase 1: Standortbestimmung</strong>
                <p>Lernstil & Ausgangssituation</p>
                <div class="phase-progress" style="width: 0%;"></div>
            </div>
            <div class="phase pending" id="phase2">
                <strong>Phase 2: Emotionale Vertiefung</strong>
                <p>Gefühle & Schlüsselaffekt</p>
                <div class="phase-progress" style="width: 0%;"></div>
            </div>
            <div class="phase pending" id="phase3">
                <strong>Phase 3: Systemanalyse</strong>
                <p>Muster & Teufelskreislauf</p>
                <div class="phase-progress" style="width: 0%;"></div>
            </div>
            <div class="phase pending" id="phase4">
                <strong>Phase 4: Zukunftsgestaltung</strong>
                <p>Vision & konkrete Schritte</p>
                <div class="phase-progress" style="width: 0%;"></div>
            </div>
            <div class="phase pending" id="phase5">
                <strong>Phase 5: Integration</strong>
                <p>Erfolge & Learnings</p>
                <div class="phase-progress" style="width: 0%;"></div>
            </div>
        </div>
        
        <div class="features">
            <h4>🚀 Intelligente Features</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; text-align: left;">
                <div>✅ Automatisches Phase-Tracking</div>
                <div>✅ Echtzeit-Fortschrittsanzeige</div>
                <div>✅ Intelligente Phasenübergänge</div>
                <div>✅ Personalisierte Anpassung</div>
            </div>
        </div>
        
        <a href="/coaching" class="btn">🚀 Intelligentes Coaching starten</a>
        <a href="/dashboard" class="btn">📊 Coach Dashboard</a>
    </div>
</body>
</html>'''

@app.route("/coaching")
def coaching():
    session_id = create_session()
    return f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Intelligentes Ruhestandscoaching Chat</title>
    <style>
        body {{ font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; margin: 0; }}
        .chat-container {{ max-width: 1000px; margin: 0 auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.2); }}
        .chat-header {{ background: #28a745; color: white; padding: 25px; text-align: center; }}
        .progress-bar {{ background: #20c997; padding: 15px; color: white; display: flex; justify-content: space-between; align-items: center; }}
        .progress-track {{ flex: 1; height: 8px; background: rgba(255,255,255,0.3); border-radius: 4px; margin: 0 20px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: white; border-radius: 4px; transition: width 0.5s ease; width: 0%; }}
        .messages {{ height: 500px; overflow-y: auto; padding: 25px; background: #fafafa; }}
        .message {{ margin: 20px 0; display: flex; gap: 15px; }}
        .message.user {{ flex-direction: row-reverse; }}
        .message-content {{ max-width: 75%; padding: 15px 20px; border-radius: 18px; line-height: 1.5; }}
        .message.assistant .message-content {{ background: white; border: 1px solid #e9ecef; }}
        .message.user .message-content {{ background: #007bff; color: white; }}
        .input-area {{ display: flex; padding: 25px; gap: 15px; }}
        .message-input {{ flex: 1; padding: 15px; border: 2px solid #e9ecef; border-radius: 25px; font-size: 16px; }}
        .send-btn {{ background: #28a745; color: white; border: none; padding: 15px 25px; border-radius: 25px; cursor: pointer; font-weight: bold; }}
        .phase-alert {{ background: linear-gradient(45deg, #28a745, #20c997); color: white; padding: 15px; margin: 10px 0; border-radius: 10px; text-align: center; animation: slideIn 0.5s ease; }}
        @keyframes slideIn {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h2>🧠 Intelligentes Ruhestandscoaching</h2>
            <small>Session: {session_id} | AI-gesteuertes Phase-Tracking aktiv</small><br>
            <a href="/" style="color: white; text-decoration: none;">← Zurück zum Dashboard</a>
        </div>
        
        <div class="progress-bar">
            <div id="currentPhase">📍 Phase 1: Standortbestimmung</div>
            <div class="progress-track">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div id="overallProgress">0% abgeschlossen</div>
        </div>
        
        <div class="messages" id="messages">
            <div class="message assistant">
                <div class="message-content">
                    🎯 Herzlich willkommen zum intelligenten Ruhestandscoaching!

Ich bin Ihr AI-Coach und erkenne automatisch Ihren Fortschritt durch unser 8-Aufträge-System. 

📍 Wir beginnen mit Phase 1: Standortbestimmung

Bevor wir starten - wie lernen Sie am liebsten?
- 👁️ Visuell (Bilder, Diagramme)
- 👂 Auditiv (Gespräche, Erklärungen) 
- ✋ Kinästhetisch (Übungen, Ausprobieren)

Antworten Sie einfach mit "visuell", "auditiv" oder "kinästhetisch"!
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="messageInput" class="message-input" placeholder="Ihre Nachricht..." />
            <button onclick="sendMessage()" class="send-btn" id="sendBtn">🚀 Senden</button>
        </div>
    </div>

    <script>
        const sessionId = '{session_id}';
        
        function addMessage(sender, content) {{
            const container = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'message ' + sender;
            div.innerHTML = '<div class="message-content">' + content + '</div>';
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }}
        
        function showPhaseTransition(newPhase) {{
            const phaseNames = ['', 'Standortbestimmung', 'Emotionale Vertiefung', 'Systemanalyse', 'Zukunftsgestaltung', 'Integration'];
            const container = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'phase-alert';
            div.innerHTML = `🎉 Phase ${{newPhase}}: ${{phaseNames[newPhase]}} erreicht!`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }}
        
        function updateProgress(data) {{
            if (!data) return;
            
            const phaseNames = ['', 'Standortbestimmung', 'Emotionale Vertiefung', 'Systemanalyse', 'Zukunftsgestaltung', 'Integration'];
            
            document.getElementById('currentPhase').textContent = 
                `📍 Phase ${{data.current_phase}}: ${{phaseNames[data.current_phase]}}`;
            
            document.getElementById('progressFill').style.width = data.total_progress + '%';
            document.getElementById('overallProgress').textContent = 
                Math.round(data.total_progress) + '% abgeschlossen';
            
            if (data.phase_changed) {{
                showPhaseTransition(data.current_phase);
            }}
        }}
        
        function sendMessage() {{
            const input = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage('user', message);
            input.value = '';
            
            sendBtn.disabled = true;
            sendBtn.textContent = '⏳ AI analysiert...';
            addMessage('assistant', '<em style="color: #666;">🧠 Intelligenter Coach analysiert Ihren Fortschritt...</em>');
            
            fetch('/api/intelligent-chat', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{session_id: sessionId, message: message}})
            }})
            .then(r => r.json())
            .then(data => {{
                const messages = document.getElementById('messages');
                messages.removeChild(messages.lastChild);
                
                addMessage('assistant', data.response);
                updateProgress(data.progress);
                
                sendBtn.disabled = false;
                sendBtn.textContent = '🚀 Senden';
            }});
        }}
        
        document.getElementById('messageInput').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') sendMessage();
        }});
    </script>
</body>
</html>'''

@app.route('/api/intelligent-chat', methods=['POST'])
def intelligent_chat():
    data = request.json
    sid = data['session_id']
    message = data['message']
    
    session = sessions.get(sid)
    if not session:
        return jsonify({'error': 'Session nicht gefunden'}), 404
    
    # AI Response generieren
    ai_response = get_ai_response(session['thread_id'], message, session)
    
    # Intelligente Fortschrittsanalyse
    progress_data = analyze_progress(message, ai_response, session)
    
    # Messages speichern
    session['messages'].extend([
        {'sender': 'user', 'message': message, 'timestamp': datetime.now().isoformat()},
        {'sender': 'assistant', 'message': ai_response, 'timestamp': datetime.now().isoformat()}
    ])
    
    return jsonify({
        'response': ai_response,
        'progress': progress_data
    })

@app.route("/dashboard")
def dashboard():
    return f'''<!DOCTYPE html>
<html>
<head><title>Coach Dashboard</title></head>
<body style="font-family: Arial; padding: 40px; background: #f8f9fa;">
    <div style="max-width: 1000px; margin: 0 auto;">
        <h1>📊 Coach Dashboard</h1>
        <p>Aktive Sessions: {len(sessions)}</p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">
            {chr(10).join([f'''
            <div style="background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <h4>Session {s['id']}</h4>
                <p>Phase: {s['current_phase']}/5</p>
                <p>Fortschritt: {s['total_progress']:.1f}%</p>
                <div style="width: 100%; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                    <div style="width: {s['total_progress']}%; height: 100%; background: #28a745; border-radius: 4px;"></div>
                </div>
            </div>
            ''' for s in sessions.values()])}
        </div>
        
        <a href="/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">← Zurück</a>
    </div>
</body>
</html>'''

if __name__ == "__main__":
    print("🧠 INTELLIGENTES Ruhestandscoaching System!")
    print(f"🔑 OpenAI verbunden: {os.getenv('OPENAI_API_KEY')[:20]}...")
    print(f"🤖 Assistant: {ASSISTANT_ID}")
    print("🎯 Intelligente Features aktiv:")
    print("  ✅ Automatisches Phase-Tracking")
    print("  ✅ Echtzeit-Fortschrittsanzeige") 
    print("  ✅ Intelligente Phasenübergänge")
    print("🌐 http://localhost:8080")
    start_email_monitor()
    app.run(port=8080, debug=True)

# E-Mail Integration hinzufügen
import smtplib
import imaplib
import email
from email.message import EmailMessage
import threading
import time

# E-Mail-Konfiguration (aus Ihren Credentials)
EMAIL_CONFIG = {
    'address': os.getenv('DELTA_EMAIL', 'bot@allenspach-coaching.ch'),
    'password': os.getenv('DELTA_PASSWORD'),
    'smtp_server': 'mail.cyon.ch',
    'smtp_port': 587,
    'imap_server': 'mail.cyon.ch', 
    'imap_port': 993
}

def send_coaching_email(to_email, subject, message, session_link=None):
    """Sendet professionelle Coaching-E-Mail"""
    try:
        msg = EmailMessage()
        msg['From'] = EMAIL_CONFIG['address']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Professionelle HTML-E-Mail
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white;">
                <h1>🎯 Allenspach Coaching</h1>
                <p>Intelligentes Ruhestandscoaching</p>
            </div>
            
            <div style="padding: 30px; background: white;">
                <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin: 20px 0;">
                    {message.replace(chr(10), '<br>')}
                </div>
                
                {f'''
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{session_link}" 
                       style="background: #28a745; color: white; padding: 15px 30px; 
                              text-decoration: none; border-radius: 25px; font-weight: bold; 
                              box-shadow: 0 4px 15px rgba(40,167,69,0.3);">
                        🚀 Intelligentes Coaching starten
                    </a>
                </div>
                ''' if session_link else ''}
                
                <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h4>🧠 Ihr intelligenter AI-Coach bietet:</h4>
                    <ul>
                        <li>✅ Automatisches Phase-Tracking</li>
                        <li>✅ Personalisierte Coaching-Anpassung</li>
                        <li>✅ Strukturiertes 8-Aufträge-System</li>
                        <li>✅ Echtzeit-Fortschrittsanzeige</li>
                    </ul>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px;">
                <p>Diese E-Mail wurde automatisch vom intelligenten Coaching-System generiert.</p>
                <p>Bei Fragen antworten Sie einfach auf diese E-Mail.</p>
                <p>🌐 <a href="https://coaching.allenspach-coaching.ch">coaching.allenspach-coaching.ch</a></p>
            </div>
        </body>
        </html>
        """
        
        # Plain text Fallback
        msg.set_content(f"""
Hallo,

{message}

{f'Ihr Coaching-Link: {session_link}' if session_link else ''}

Mit freundlichen Grüßen
Ihr intelligenter AI-Coach

Allenspach Coaching
coaching.allenspach-coaching.ch
        """)
        
        # HTML-Version hinzufügen
        msg.add_alternative(html_content, subtype='html')
        
        # E-Mail senden
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
            server.send_message(msg)
            
        print(f"📧 E-Mail gesendet an: {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ E-Mail Fehler: {e}")
        return False

def check_email_inbox():
    """Überwacht E-Mail-Posteingang und antwortet automatisch"""
    try:
        with imaplib.IMAP4_SSL(EMAIL_CONFIG['imap_server'], EMAIL_CONFIG['imap_port']) as mail:
            mail.login(EMAIL_CONFIG['address'], EMAIL_CONFIG['password'])
            mail.select('INBOX')
            
            # Ungelesene E-Mails suchen
            status, messages = mail.search(None, 'UNSEEN')
            
            if messages[0]:
                for msg_id in messages[0].split():
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            sender_email = msg['From']
                            subject = msg['Subject'] or "Coaching Anfrage"
                            
                            # E-Mail Inhalt extrahieren
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        payload = part.get_payload(decode=True)
                                        if payload:
                                            body = payload.decode('utf-8', errors='ignore')
                            else:
                                payload = msg.get_payload(decode=True)
                                if payload:
                                    body = payload.decode('utf-8', errors='ignore')
                            
                            if body.strip():
                                # Neue Coaching-Session erstellen
                                session_id = create_session()
                                
                                # AI-Response generieren
                                session = sessions[session_id]
                                ai_response = get_ai_response(session['thread_id'], body, session)
                                
                                # Session-Link erstellen
                                session_link = f"http://localhost:8080/coaching-session/{session_id}"
                                
                                # Professionelle E-Mail-Antwort
                                email_response = f"""
Herzlich willkommen zum intelligenten Ruhestandscoaching!

Vielen Dank für Ihre Nachricht. Ich habe Ihre Anfrage gelesen und eine erste Antwort für Sie vorbereitet:

{ai_response}

Für ein vollständiges, interaktives Coaching-Erlebnis mit automatischem Phase-Tracking und Echtzeit-Fortschrittsanzeige nutzen Sie bitte den Link unten. Dort führe ich Sie strukturiert durch unser bewährtes 8-Aufträge-System.
                                """
                                
                                # E-Mail senden
                                response_subject = f"Re: {subject} - Ihr intelligenter Coaching-Assistent"
                                send_coaching_email(sender_email, response_subject, email_response, session_link)
                                
                                # Session-Info speichern
                                session['email'] = sender_email
                                session['initial_message'] = body
                                
                                print(f"🎯 Neue Coaching-Session erstellt: {session_id} für {sender_email}")
                            
                            # Als gelesen markieren
                            mail.store(msg_id, '+FLAGS', '\\Seen')
                        
    except Exception as e:
        print(f"📧 E-Mail Check Fehler: {e}")

def start_email_monitor():
    """Startet E-Mail-Überwachung im Hintergrund"""
    def monitor():
        print("📧 E-Mail Monitor gestartet...")
        while True:
            try:
                if EMAIL_CONFIG['password']:
                    check_email_inbox()
                    time.sleep(60)  # Alle 60 Sekunden prüfen
                else:
                    print("⚠️ E-Mail-Password nicht gesetzt - Monitor wartet...")
                    time.sleep(300)  # 5 Minuten warten
            except Exception as e:
                print(f"📧 Monitor Fehler: {e}")
                time.sleep(120)  # 2 Minuten bei Fehler
    
    thread = threading.Thread(target=monitor)
    thread.daemon = True
    thread.start()

# E-Mail-spezifische Route
@app.route("/coaching-session/<session_id>")
def email_coaching_session(session_id):
    """Spezielle Route für E-Mail-Sessions"""
    session = sessions.get(session_id)
    if not session:
        return '''<h1>❌ Session nicht gefunden</h1>
        <p>Diese Coaching-Session ist nicht mehr verfügbar.</p>
        <a href="/coaching">Neue Session starten</a>'''
    
    return f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>E-Mail Coaching Session</title>
    <style>
        body {{ font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .welcome {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 20px; text-align: center; }}
        .btn {{ background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 10px; display: inline-block; }}
    </style>
</head>
<body>
    <div class="welcome">
        <h1>🎯 Willkommen zurück!</h1>
        <p>Ihre Coaching-Session ist bereit. Sie wurden automatisch von unserem E-Mail-System weitergeleitet.</p>
        
        <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3>📧 E-Mail-Adresse:</h3>
            <p>{session.get('email', 'Unbekannt')}</p>
            
            <h3>💬 Ihre ursprüngliche Nachricht:</h3>
            <p style="font-style: italic;">"{session.get('initial_message', 'Keine Nachricht')[:100]}..."</p>
        </div>
        
        <a href="/coaching" class="btn">🚀 Zum intelligenten Coaching-Chat</a>
        <a href="/" class="btn">🏠 Zum Dashboard</a>
    </div>
</body>
</html>'''

# E-Mail-Test Route
@app.route("/test-email")
def test_email():
    """Test-Route für E-Mail-Funktionalität"""
    return f'''<!DOCTYPE html>
<html>
<head><title>E-Mail System Test</title></head>
<body style="font-family: Arial; padding: 40px;">
    <h1>📧 E-Mail System Test</h1>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h3>📋 Konfiguration:</h3>
        <p><strong>E-Mail:</strong> {EMAIL_CONFIG['address']}</p>
        <p><strong>SMTP Server:</strong> {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}</p>
        <p><strong>IMAP Server:</strong> {EMAIL_CONFIG['imap_server']}:{EMAIL_CONFIG['imap_port']}</p>
        <p><strong>Password gesetzt:</strong> {'✅ Ja' if EMAIL_CONFIG['password'] else '❌ Nein'}</p>
    </div>
    
    <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h3>🧪 So testen Sie:</h3>
        <ol>
            <li>Senden Sie eine E-Mail an: <strong>{EMAIL_CONFIG['address']}</strong></li>
            <li>Das System antwortet automatisch mit AI-Response</li>
            <li>Sie erhalten einen Link zu Ihrer persönlichen Coaching-Session</li>
            <li>Über den Link gelangen Sie zum intelligenten Chat</li>
        </ol>
    </div>
    
    <a href="/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">← Zurück zum Dashboard</a>
</body>
</html>'''

