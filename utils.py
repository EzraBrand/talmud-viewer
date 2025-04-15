import re
import urllib.parse
import requests

# Define term replacements for the English text
term_replacements = {
    "Gemara": "Talmud",
    "Rabbi": "R'",
    "The Sages taught": "A baraita states",
    "Divine Voice": "bat kol",
    "Divine Presence": "Shekhina",
    "phylacteries": "tefillin",
    "gentile": "non-Jew"
}

def remove_nikud(text):
    """Remove Hebrew vowel points from text"""
    nikud_pattern = re.compile(r'[\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]')
    return nikud_pattern.sub('', text)

def parse_sefaria_url(url):
    """Parse a Sefaria URL to extract reference information"""
    tractates = ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Shekalim", "Yoma", "Sukkah", "Beitzah",
        "Rosh Hashanah", "Taanit", "Megillah", "Moed Katan", "Chagigah", "Yevamot", "Ketubot",
        "Nedarim", "Nazir", "Sotah", "Gittin", "Kiddushin", "Bava Kamma", "Bava Metzia",
        "Bava Batra", "Sanhedrin", "Makkot", "Shevuot", "Avodah Zarah", "Horayot"]
        
    url = url.split('?')[0]  # Remove query params
    parts = url.split('/')
    
    # Extract reference part
    reference = next((part for part in parts if any(t in part for t in tractates)
                    or re.search(r'[A-Za-z]+\.\d+[ab]', part)), None)
    
    if not reference:
        return {'error': 'Invalid URL format'}
    
    # Simple reference (e.g., "Tractate.44a.2")
    match = re.match(r'([^\.]+)\.([^\.]+)(?:\.([^\.]+))?', reference)
    if not match:
        return {'error': 'Invalid reference format'}
    
    return {
        'type': 'single',
        'tractate': match.group(1),
        'page': match.group(2),
        'section': int(match.group(3)) if match.group(3) else None
    }

def fetch_text(tractate, page, section=None):
    """Fetch text from Sefaria API with section filtering"""
    base_url = "https://www.sefaria.org/api/texts/"
    reference = f"{tractate}.{page}"
    
    try:
        # Try direct reference first
        response = requests.get(f"{base_url}{urllib.parse.quote(reference)}")
        
        # Fall back to Bavli prefix if needed
        if response.status_code != 200:
            response = requests.get(f"{base_url}{urllib.parse.quote('Bavli ' + reference)}")
            if response.status_code != 200:
                return {"error": f"Failed to fetch text"}
        
        data = response.json()
        
        # Filter to requested section if specified
        if section is not None:
            section_idx = section - 1
            if isinstance(data.get('text', []), list) and section_idx < len(data['text']):
                filtered_data = {
                    'text': [data['text'][section_idx]],
                    'he': [data.get('he', [])[section_idx]] if 'he' in data and section_idx < len(data['he']) else [''],
                    'span': f"{tractate} {page}:{section}"
                }
                return filtered_data
        
        # Return all sections
        filtered_data = {
            'text': data.get('text', [])[:20] if isinstance(data.get('text', []), list) else [],
            'he': data.get('he', [])[:20] if 'he' in data and isinstance(data['he'], list) else [],
            'span': f"{tractate} {page}"
        }
        return filtered_data
        
    except Exception as e:
        return {"error": str(e)}

def process_text_for_display(data):
    """Process text data for display in web app"""
    if "error" in data:
        return data
    
    if not data or not isinstance(data, dict):
        return {"error": "Invalid data format"}
    
    result = {
        "span": data.get("span", ""),
        "sections": []
    }
    
    # Prepare text data
    he_text = data.get("he", [])
    en_text = data.get("text", [])
    
    # Ensure list format
    if not isinstance(he_text, list): he_text = [he_text]
    if not isinstance(en_text, list): en_text = [en_text]
    
    # Process each section
    for i in range(min(len(he_text), len(en_text))):
        current_he = he_text[i]
        current_en = en_text[i]
        
        # Skip empty sections
        if not current_he and not current_en:
            continue
        
        section = {"hebrew": "", "english": ""}
        
        # Hebrew text
        if current_he:
            current_he = remove_nikud(current_he)
            section["hebrew"] = current_he
        
        # English text
        if current_en:
            # Apply term replacements
            for original, replacement in term_replacements.items():
                pattern = r'\b' + re.escape(original) + r'\b'
                current_en = re.sub(pattern, replacement, current_en, flags=re.IGNORECASE)
            
            section["english"] = current_en
        
        result["sections"].append(section)
    
    return result
