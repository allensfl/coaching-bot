from flask import Flask, send_from_directory
import os

app = Flask(__name__)

@app.route("/")
def home():
    return send_from_directory(".", "index_premium.html")

@app.route("/premium")
def premium_dashboard():
    return send_from_directory(".", "index_premium.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
