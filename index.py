from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Basic data for now
tractates = ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Shekalim", "Yoma", "Sukkah", "Beitzah",
    "Rosh Hashanah", "Taanit", "Megillah", "Moed Katan", "Chagigah", "Yevamot", "Ketubot",
    "Nedarim", "Nazir", "Sotah", "Gittin", "Kiddushin", "Bava Kamma", "Bava Metzia",
    "Bava Batra", "Sanhedrin", "Makkot", "Shevuot", "Avodah Zarah", "Horayot"]

# Generate pages: 2a, 2b, 3a, 3b, etc.
pages = [f"{daf}{suffix}" for daf in range(2, 21) for suffix in ['a', 'b']]

@app.route('/')
def home():
    return render_template('basic.html', tractates=tractates, pages=pages)

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "message": "Talmud Viewer API is running"})

# Simple mock API endpoint - no actual Sefaria integration yet
@app.route('/api/fetch', methods=['POST'])
def fetch_mock():
    data = request.json
    
    # Just return mock data for now
    return jsonify({
        "status": "success",
        "mock": True,
        "request_data": data,
        "text": "This is mock text for testing. The real Sefaria API integration will be added in the next step."
    })
