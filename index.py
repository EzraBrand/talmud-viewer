from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Hello from Talmud Viewer"})

# Required for Vercel
app.debug = False
