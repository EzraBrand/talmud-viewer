from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Basic data
tractates = ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Shekalim", "Yoma", "Sukkah", "Beitzah",
    "Rosh Hashanah", "Taanit", "Megillah", "Moed Katan", "Chagigah", "Yevamot", "Ketubot",
    "Nedarim", "Nazir", "Sotah", "Gittin", "Kiddushin", "Bava Kamma", "Bava Metzia",
    "Bava Batra", "Sanhedrin", "Makkot", "Shevuot", "Avodah Zarah", "Horayot"]

# Generate pages
pages = [f"{daf}{suffix}" for daf in range(2, 21) for suffix in ['a', 'b']]

@app.route('/')
def home():
    return render_template('basic.html', tractates=tractates, pages=pages)

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "message": "Talmud Viewer API is running"})

# Mock API endpoint with more realistic data
@app.route('/api/fetch', methods=['POST'])
def fetch():
    data = request.json
    
    # Create mock response based on request
    if data.get('input_method') == 'dropdown':
        tractate = data.get('tractate', 'Unknown')
        page = data.get('page', 'Unknown')
        section = data.get('section', 'All')
        
        # Generate different mock responses based on inputs
        mock_data = {
            "status": "success",
            "mock": True,
            "reference": f"{tractate} {page}:{section if section else 'All'}",
            "hebrew": "שלום זהו טקסט עברי לדוגמה. בקרוב יהיה כאן את הטקסט האמיתי מהתלמוד.",
            "text": f"This is mock text for {tractate} {page}, section {section if section else 'All'}. " +
                   "In the next step, we'll integrate with the real Sefaria API to retrieve actual Talmud text. " +
                   "This sample text demonstrates that the form, API, and UI flow is working correctly."
        }
    else:  # URL method
        url = data.get('url', '')
        mock_data = {
            "status": "success",
            "mock": True,
            "reference": "URL Reference",
            "url": url,
            "hebrew": "שלום זהו טקסט עברי לדוגמה. בקרוב יהיה כאן את הטקסט האמיתי מהתלמוד.",
            "text": f"This is mock text for URL: {url}. " +
                   "In the next step, we'll parse this URL and use the Sefaria API to retrieve the actual text."
        }
    
    return jsonify(mock_data)
