#!/usr/bin/env python3
import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import uuid, time
from datetime import datetime

load_dotenv()
app = Flask(__name__)
sessions = {}

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

def create_session():
    sid = str(uuid.uuid4())[:8]
    thread = client.beta.threads.create()
    sessions[sid] = {
        'id': sid,
        'thread_id': thread.id,
        'messages': [],
        'created': datetime.now()
    }
    return sid

def get_ai_response(thread_id, message):
    try:
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        
        while run.status in ['queued', 'in_progress']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        
        for msg in messages.data:
            if msg.role == 'assistant':
                return msg.content[0].text.value
        
        return "Entschuldigung, ich konnte keine Antwort generieren."
    except Exception as e:
        return f"Fehler: {str(e)}"

@app.route('/')
def home():
    return '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>🎯 Ruhestandscoaching Cockpit</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; color: white; }
        .header h1 { font-size: 3rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .cockpit-container {
            background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: grid; grid-template-columns: 300px 1fr; height: 80vh; overflow: hidden;
        }
        .sidebar { background: #f8f9fa; padding: 20px; }
        .sidebar h3 { color: #495057; margin: 20px 0 10px 0; }
        .phase { background: #007bff; color: white; padding: 10px; margin: 5px 0; border-radius: 8px; }
        .main-content { display: flex; flex-direction: column; }
        .chat-header { background: #28a745; color: white; padding: 20px; }
        .welcome-screen {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            height: 100%; text-align: center; color: #6c757d; padding: 40px;
        }
        .demo-button {
            background: #28a745; color: white; padding: 15px 30px; text-decoration: none;
            border-radius: 25px; margin: 20px; display: inline-block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Ruhestandscoaching Cockpit</h1>
            <p>Strukturiertes 8-Aufträge-System für erfüllten Ruhestand</p>
        </div>

        <div class="cockpit-container">
            <div class="sidebar">
                <h3>📋 Coaching-Phasen</h3>
                <div class="phase">Phase 1: Standortbestimmung</div>
                <div class="phase">Phase 2: Emotionale Vertiefung</div>
                <div class="phase">Phase 3: Systemanalyse</div>
                <div class="phase">Phase 4: Zukunftsgestaltung</div>
                <div class="phase">Phase 5: Integration</div>
                
                <h3>🤖 System-Info</h3>
                <div style="background: white; padding: 15px; border-radius: 10px; text-align: center;">
                    <strong>OpenAI Connected</strong>
                </div>
            </div>

            <div class="main-content">
                <div class="chat-header">
                    <h2>🎓 Professionelles Ruhestandscoaching</h2>
                    <span>✅ System Ready</span>
                </div>

                <div class="welcome-screen">
                    <h2>🚀 Ihr Ruhestandscoaching wartet!</h2>
                    <p>Erleben Sie das vollständige 8-Aufträge-System mit Ihrem echten OpenAI Assistant.</p>
                    
                    <a href="/chat" class="demo-button">💬 Ruhestandscoaching starten</a>
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
<html>
<head><title>Ruhestandscoaching Chat</title></head>
<body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
    <div style="max-width: 800px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden;">
        <div style="background: #28a745; color: white; padding: 20px; text-align: center;">
            <h2>🎯 Ruhestandscoaching Session</h2>
            <small>Session: {session_id}</small>
            <p><a href="/" style="color: white;">← Zurück zum Cockpit</a></p>
        </div>
        <div id="messages" style="height: 400px; overflow-y: auto; padding: 20px;"></div>
        <div style="padding: 20px; display: flex; gap: 10px;">
            <input type="text" id="messageInput" placeholder="Ihre Nachricht..." style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 20px;">
            <button onclick="sendMessage()" style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 20px;">Senden</button>
        </div>
    </div>
    
    <script>
        const sessionId = '{session_id}';
        
        function addMessage(sender, content) {{
            const div = document.createElement('div');
            div.style.marginBottom = '15px';
            div.style.textAlign = sender === 'user' ? 'right' : 'left';
            div.innerHTML = '<div style="display: inline-block; max-width: 70%; padding: 10px 15px; border-radius: 15px; background: ' + 
                          (sender === 'user' ? '#007bff; color: white' : '#e9ecef') + ';">' + content + '</div>';
            document.getElementById('messages').appendChild(div);
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }}
        
        function sendMessage() {{
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage('user', message);
            input.value = '';
            
            fetch('/api/send', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{session_id: sessionId, message: message}})
            }})
            .then(r => r.json())
            .then(data => addMessage('assistant', data.response));
        }}
        
        document.getElementById('messageInput').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') sendMessage();
        }});
        
        // Willkommensnachricht
        addMessage('assistant', '🎯 Herzlich willkommen zum Ruhestandscoaching! Schreiben Sie "Hallo" um zu beginnen.');
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
    
    ai_response = get_ai_response(session['thread_id'], message)
    
    session['messages'].extend([
        {'sender': 'user', 'message': message, 'timestamp': datetime.now().isoformat()},
        {'sender': 'assistant', 'message': ai_response, 'timestamp': datetime.now().isoformat()}
    ])
    
    return jsonify({'response': ai_response})

if __name__ == '__main__':
    print("🎯 Ruhestandscoaching mit 5 Phasen: http://localhost:8080")
    print(f"🔑 OpenAI verbunden: {os.getenv('OPENAI_API_KEY')[:20]}...")
    print(f"🤖 Assistant: {ASSISTANT_ID}")
    app.run(port=8080, debug=True)
