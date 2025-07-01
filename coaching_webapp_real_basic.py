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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

@app.route("/")
def home():
    return '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>🧠 Intelligentes Ruhestandscoaching</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; margin: 0; color: white; text-align: center; padding: 50px; }
        .phases { background: white; color: #333; padding: 30px; border-radius: 20px; margin: 20px auto; max-width: 800px; }
        .phase { background: #007bff; color: white; padding: 15px; margin: 10px; border-radius: 10px; }
        .progress-circle { width: 80px; height: 80px; border-radius: 50%; background: #28a745; color: white; display: flex; align-items: center; justify-content: center; margin: 20px auto; font-weight: bold; }
        .btn { background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 10px; display: inline-block; }
    </style>
</head>
<body>
    <h1>🧠 Intelligentes Ruhestandscoaching</h1>
    <p>Mit automatischem Phase-Tracking und Fortschrittsanzeige</p>
    
    <div class="phases">
        <h3>📊 Ihr Coaching-Fortschritt</h3>
        <div class="progress-circle">0%</div>
        
        <h3>📋 Coaching-Phasen</h3>
        <div class="phase">Phase 1: Standortbestimmung</div>
        <div class="phase">Phase 2: Emotionale Vertiefung</div>
        <div class="phase">Phase 3: Systemanalyse</div>
        <div class="phase">Phase 4: Zukunftsgestaltung</div>
        <div class="phase">Phase 5: Integration</div>
        
        <h3>🚀 Intelligente Features</h3>
        <ul style="text-align: left; max-width: 400px; margin: 0 auto;">
            <li>✅ Automatisches Phase-Tracking</li>
            <li>✅ Echtzeit-Fortschrittsanzeige</li>
            <li>✅ Intelligente Phasenübergänge</li>
        </ul>
    </div>
    
    <a href="/coaching" class="btn">🚀 Intelligentes Coaching starten</a>
    <a href="/dashboard" class="btn">📊 Coach Dashboard</a>
</body>
</html>'''

@app.route("/coaching")
def coaching():
    return '''<h1>🎯 Intelligentes Coaching</h1>
    <p>Hier kommt das intelligente Chat-System hin!</p>
    <a href="/">← Zurück</a>'''

@app.route("/dashboard")
def dashboard():
    return '''<h1>📊 Coach Dashboard</h1>
    <p>Hier kommt die Session-Übersicht hin!</p>
    <a href="/">← Zurück</a>'''

if __name__ == "__main__":
    print("🧠 Intelligentes Ruhestandscoaching läuft auf: http://localhost:8080")
    print(f"🔑 OpenAI verbunden: {os.getenv('OPENAI_API_KEY')[:20]}...")
    print(f"🤖 Assistant: {ASSISTANT_ID}")
    app.run(port=8080, debug=True)
