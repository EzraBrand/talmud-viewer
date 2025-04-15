from flask import Flask, render_template, jsonify, request
from utils import parse_sefaria_url, fetch_text, process_text_for_display
import json

app = Flask(__name__)

# Basic data
tractates = ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Shekalim", "Yoma", "Sukkah", "Beitzah",
    "Rosh Hashanah", "Taanit", "Megillah", "Moed Katan", "Chagigah", "Yevamot", "Ketubot",
    "Nedarim", "Nazir", "Sotah", "Gittin", "Kiddushin", "Bava Kamma", "Bava Metzia",
    "Bava Batra", "Sanhedrin", "Makkot", "Shevuot", "Avodah Zarah", "Horayot"]

# Generate pages
pages = [f"{daf}{suffix}" for daf in range(2, 41) for suffix in ['a', 'b']]

@app.route('/')
def home():
    return render_template('basic.html', tractates=tractates, pages=pages)

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "message": "Talmud Viewer API is running"})

# Real API endpoint
@app.route('/api/fetch', methods=['POST'])
def fetch():
    data = request.json
    
    try:
        if data.get('input_method') == 'dropdown':
            # Fetch by tractate, page, section
            tractate = data.get('tractate')
            page = data.get('page')
            section = data.get('section')
            
            if section and section.isdigit():
                section = int(section)
            else:
                section = None
                
            text_data = fetch_text(tractate, page, section)
            
        else:
            # Fetch by Sefaria URL
            url = data.get('url')
            if not url:
                return jsonify({"error": "Please enter a valid Sefaria URL"})
                
            parsed = parse_sefaria_url(url)
            if 'error' in parsed:
                return jsonify({"error": parsed['error']})
                
            text_data = fetch_text(parsed['tractate'], parsed['page'], parsed['section'])
        
        # Process the text for display
        if 'error' in text_data:
            return jsonify(text_data)
            
        result = process_text_for_display(text_data)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"})
