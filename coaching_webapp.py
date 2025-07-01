#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'coaching-secret'
sessions = {}

def create_coaching_session(email):
    session_id = str(uuid.uuid4())[:8]
    sessions[session_id] = {
        'id': session_id,
        'coachee_email': email,
        'created': datetime.now(),
        'messages': []
    }
    return session_id

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/test')
def test():
    return '<h1>🎉 System funktioniert!</h1><p><a href="/">Zum Cockpit</a></p>'

if __name__ == '__main__':
    print("🚀 Coaching Cockpit läuft auf: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
