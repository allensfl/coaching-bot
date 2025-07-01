
#!/usr/bin/env python3
import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import uuid, time
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
sessions = {}

# OpenAI Client mit Ihren echten Credentials
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

def create_session():
    sid = str(uuid.uuid4())[:8]
    
    # Create OpenAI thread für diesen User
    thread = client.beta.threads.create()
    
    sessions[sid] = {
        'id': sid,
        'thread_id': thread.id,
        'messages': [],
        'created': datetime.now()
    }
    return sid

def get_ai_response(thread_id, message):
    """Echte OpenAI Assistant Response"""
    try:
        # Message an Thread senden
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # Run erstellen
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        
        # Warten bis Run fertig ist
        while run.status in ['queued', 'in_progress']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        # Messages abrufen
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        
        # Neueste Assistant-Message finden
        for msg in messages.data:
            if msg.role == 'assistant':
                return msg.content[0].text.value
        
        return "Entschuldigung, ich konnte keine Antwort generieren."
        
    except Exception as e:
        return f"Fehler bei der AI-Antwort: {str(e)}"

@app.route('/')
def home():
    return '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coaching Cockpit - Allenspach Coaching</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 50px; color: white; }
        .header h1 { font-size: 3rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2rem; opacity: 0.9; }
        .cockpit-container {
            background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden; display: grid; grid-template-columns: 300px 1fr; height: 80vh;
        }
        .sidebar { background: #f8f9fa; border-right: 1px solid #e9ecef; padding: 20px; }
        .sidebar h3 { color: #495057; margin-bottom: 20px; font-size: 1.1rem; }
        .main-content { display: flex; flex-direction: column; }
        .chat-header {
            background: #007bff; color: white; padding: 20px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .status-indicator { display: flex; align-items: center; gap: 8px; }
        .status-dot {
            width: 10px; height: 10px; background: #28a745; border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
        .welcome-screen {
            display: flex; flex-direction: column; align-items: center;
            justify-content: center; height: 100%; text-align: center; color: #6c757d; padding: 40px;
        }
        .welcome-screen h2 { font-size: 2rem; margin-bottom: 20px; color: #007bff; }
        .welcome-screen p { font-size: 1.1rem; max-width: 500px; line-height: 1.6; margin-bottom: 30px; }
        .demo-button {
            background: #28a745; color: white; padding: 15px 30px; text-decoration: none;
            border-radius: 25px; font-weight: bold; display: inline-block; margin: 20px;
            transition: all 0.3s; box-shadow: 0 4px 15px rgba(40,167,69,0.3);
        }
        .demo-button:hover { background: #218838; transform: translateY(-2px); }
        .feature-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-top: 30px;
        }
        .feature-card {
            background: white; padding: 20px; border-radius: 15px; text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .feature-icon { font-size: 2rem; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Coaching Cockpit</h1>
            <p>Professionelle AI-gestützte Coaching-Plattform</p>
        </div>

        <div class="cockpit-container">
            <div class="sidebar">
                <h3>🎪 Aktive Sessions</h3>
                <div style="text-align: center; color: #6c757d; padding: 20px;">
                    📭 Keine aktiven Sessions<br>
                    <small>Warten auf E-Mail-Anfragen...</small>
                </div>
                
                <div style="margin-top: 30px;">
                    <h3>📊 Statistiken</h3>
                    <div class="feature-card">
                        <div class="feature-icon">📈</div>
                        <strong>0</strong> Sessions heute
                    </div>
                </div>
            </div>

            <div class="main-content">
                <div class="chat-header">
                    <h2>🤖 Echter OpenAI Assistant aktiv!</h2>
                    <div class="status-indicator">
                        <div class="status-dot"></div>
                        <span>OpenAI Connected</span>
                    </div>
                </div>

                <div class="welcome-screen">
                    <h2>🚀 Ihr echter AI-Coach ist bereit!</h2>
                    <p>
                        Verbunden mit Ihrem OpenAI Assistant: <strong>''' + ASSISTANT_ID + '''</strong><br>
                        Jetzt mit echten, intelligenten Coaching-Antworten!
                    </p>
                    
                    <a href="/chat" class="demo-button">💬 Echten AI-Coach testen</a>
                    
                    <div class="feature-grid">
                        <div class="feature-card">
                            <div class="feature-icon">🤖</div>
                            <h4>Echter OpenAI Assistant</h4>
                            <p>Ihr trainierter Coaching-Assistant</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🧠</div>
                            <h4>Intelligente Antworten</h4>
                            <p>Personalisierte Coaching-Gespräche</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">📧</div>
                            <h4>E-Mail Integration</h4>
                            <p>bot@allenspach-coaching.ch</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

@app.route('/chat')
def chat():
    session_id = create_session()
    return f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Echter AI-Coaching Chat</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .chat-container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.2); }}
        .chat-header {{ background: #28a745; color: white; padding: 25px; text-align: center; }}
        .messages {{ height: 500px; overflow-y: auto; padding: 25px; background: #fafafa; }}
        .message {{ margin: 20px 0; display: flex; gap: 15px; }}
        .message.user {{ flex-direction: row-reverse; }}
        .message-content {{ max-width: 70%; padding: 15px 20px; border-radius: 18px; line-height: 1.5; }}
        .message.assistant .message-content {{ background: white; border: 1px solid #e9ecef; }}
        .message.user .message-content {{ background: #007bff; color: white; }}
        .input-area {{ display: flex; padding: 25px; gap: 15px; }}
        .message-input {{ flex: 1; padding: 15px; border: 2px solid #e9ecef; border-radius: 25px; font-size: 16px; }}
        .send-btn {{ background: #28a745; color: white; border: none; padding: 15px 25px; border-radius: 25px; cursor: pointer; font-weight: bold; }}
        .send-btn:hover {{ background: #218838; }}
        .back-btn {{ background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; display: inline-block; }}
        .loading {{ text-align: center; color: #6c757d; font-style: italic; }}
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h2>🤖 Echter OpenAI Coaching Assistant</h2>
            <small>Session: {session_id} | Assistant: {ASSISTANT_ID[:15]}...</small><br>
            <a href="/" class="back-btn">← Zurück zum Cockpit</a>
        </div>
        <div class="messages" id="messages">
            <div class="message assistant">
                <div class="message-content">
                    👋 Hallo! Ich bin Ihr persönlicher AI-Coaching-Assistant. Ich freue mich, heute mit Ihnen zu arbeiten. Womit kann ich Ihnen helfen?
                </div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="messageInput" class="message-input" placeholder="Ihre Nachricht an den AI-Coach..." />
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
        
        function sendMessage() {{
            const input = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const message = input.value.trim();
            if (!message) return;
            
            // User message anzeigen
            addMessage('user', message);
            input.value = '';
            
            // Loading anzeigen
            sendBtn.disabled = true;
            sendBtn.textContent = '⏳ AI denkt...';
            addMessage('assistant', '<div class="loading">🤖 Ihr AI-Coach bereitet eine Antwort vor...</div>');
            
            // AI-Antwort abrufen
            fetch('/api/send', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{session_id: sessionId, message: message}})
            }})
            .then(r => r.json())
            .then(data => {{
                // Loading message entfernen
                const messages = document.getElementById('messages');
                messages.removeChild(messages.lastChild);
                
                // Echte AI-Antwort anzeigen
                addMessage('assistant', data.response);
                
                // Button wieder aktivieren
                sendBtn.disabled = false;
                sendBtn.textContent = '🚀 Senden';
            }})
            .catch(err => {{
                console.error('Fehler:', err);
                addMessage('assistant', '❌ Entschuldigung, es gab einen Fehler bei der Verbindung zum AI-Coach.');
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

@app.route('/api/send', methods=['POST'])
def send_message():
    data = request.json
    sid = data['session_id']
    message = data['message']
    
    session = sessions.get(sid)
    if not session:
        return jsonify({'error': 'Session nicht gefunden'}), 404
    
    # Echte OpenAI-Antwort abrufen
    ai_response = get_ai_response(session['thread_id'], message)
    
    # Messages speichern
    session['messages'].extend([
        {'sender': 'user', 'message': message, 'timestamp': datetime.now().isoformat()},
        {'sender': 'assistant', 'message': ai_response, 'timestamp': datetime.now().isoformat()}
    ])
    
    return jsonify({'response': ai_response})

if __name__ == '__main__':
    print("🤖 ECHTER OpenAI Assistant Coaching Cockpit!")
    print(f"🔑 API Key: {os.getenv('OPENAI_API_KEY')[:20]}...")
    print(f"🎯 Assistant ID: {ASSISTANT_ID}")
    print("🌐 http://localhost:8080")
    app.run(port=8080, debug=True)
