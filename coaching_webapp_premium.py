from flask import Flask, render_template_string, request, jsonify, send_from_directory
import os

app = Flask(__name__)

@app.route('/premium')
def premium_dashboard():
    return send_from_directory('.', 'index_premium.html')

@app.route('/')
def home():
    return send_from_directory('.', 'index_premium.html')

@app.route('/chat')
def chat():
    return render_template_string("""
    <!DOCTYPE html>
    <html><head><title>Chat</title></head>
    <body><h1>Chat funktioniert!</h1></body></html>
    """)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
