from flask import Flask, send_from_directory, jsonify, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    return send_from_directory('.', 'index_premium.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory('.', 'index_premium.html')

@app.route('/chat')
def chat():
    return jsonify({"message": "Chat wird geladen..."})

@app.route('/api/coaching', methods=['POST'])
def coaching_api():
    data = request.get_json()
    return jsonify({"response": "Coaching-Antwort wird verarbeitet..."})

@app.route('/admin')
def admin():
    return jsonify({"status": "Admin-Bereich aktiv"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
