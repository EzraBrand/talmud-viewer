import os
from flask import Flask, render_template, request, jsonify
from utils import (
    parse_sefaria_url, fetch_text, fetch_text_range, 
    process_text_for_display
)

app = Flask(__name__)

# Setup data
tractates = ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Shekalim", "Yoma", "Sukkah", "Beitzah",
    "Rosh Hashanah", "Taanit", "Megillah", "Moed Katan", "Chagigah", "Yevamot", "Ketubot",
    "Nedarim", "Nazir", "Sotah", "Gittin", "Kiddushin", "Bava Kamma", "Bava Metzia",
    "Bava Batra", "Sanhedrin", "Makkot", "Shevuot", "Avodah Zarah", "Horayot",
    "Zevachim", "Menachot", "Chullin", "Bekhorot", "Arakhin", "Temurah", "Keritot",
    "Meilah", "Kinnim", "Tamid", "Middot", "Niddah"]

# Generate pages: 2a, 2b, 3a, 3b, etc.
pages = [f"{daf}{suffix}" for daf in range(2, 181) for suffix in ['a', 'b']]

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html', tractates=tractates, pages=pages)

@app.route('/fetch', methods=['POST'])
def fetch():
    """API endpoint to fetch Talmud text"""
    data = request.json
    input_method = data.get('input_method')
    
    if input_method == 'dropdown':
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
            
        if parsed['type'] == 'single':
            text_data = fetch_text(parsed['tractate'], parsed['page'], parsed['section'])
        else:
            text_data = fetch_text_range(parsed['start'], parsed['end'])
    
    # Process the text for display
    if 'error' in text_data:
        return jsonify(text_data)
        
    html_data = process_text_for_display(text_data)
    return jsonify(html_data)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
