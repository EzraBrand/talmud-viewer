from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('basic.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "message": "Talmud Viewer API is running"})
