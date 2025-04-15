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
    "divine inspiration": "Holy Spirit",
    "Divine Spirit": "Holy Spirit",
    "the Lord": "YHWH",
    "leper": "metzora",
    "leprosy": "tzara'at",
    "phylacteries": "tefillin",
    "gentile": "non-Jew",
    "ignoramus": "am ha'aretz",
    "maidservant": "female slave",
    "barrel": "jug",
    "the Holy One, Blessed be He": "God",
    "son of R'": "ben"
}

def remove_nikud(text):
    """Remove Hebrew vowel points from text"""
    nikud_pattern = re.compile(r'[\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]')
    return nikud_pattern.sub('', text)

def split_into_sentences(text):
    """Split text into sentences while preserving HTML"""
    if not text:
        return []

    # Temporarily replace HTML tags and special cases
    tag_counter = 0
    tag_map = {}

    def replace_tag(match):
        nonlocal tag_counter
        placeholder = f"__TAG_{tag_counter}__"
        tag_map[placeholder] = match.group(0)
        tag_counter += 1
        return placeholder

    text = re.sub(r'<[^>]+>', replace_tag, text)

    # Handle abbreviations
    for case in ["e.g.", "i.e.", "etc.", "vs.", "Mr.", "Mrs.", "Dr.", "Prof."]:
        text = text.replace(case, case.replace(".", "@@"))

    # Split by sentence endings
    sentences = []
    for s in re.split(r'(?<=[.!?])\s+', text):
        if not s.strip():
            continue

        # Ensure sentence ends with punctuation
        if not s.rstrip()[-1] in '.!?':
            s = s.rstrip() + "."

        # Restore placeholders
        s = s.replace("@@", ".")
        for placeholder, tag in tag_map.items():
            s = s.replace(placeholder, tag)

        sentences.append(s.strip())

    return sentences

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
        
        section = {"hebrew": [], "english": []}
        
        # Hebrew text - split into sentences
        if current_he:
            current_he = remove_nikud(current_he)
            section["hebrew"] = split_into_sentences(current_he)
        
        # English text - split into sentences and apply term replacements
        if current_en:
            sentences = split_into_sentences(current_en)
            processed_sentences = []
            
            for sentence in sentences:
                for original, replacement in term_replacements.items():
                    pattern = r'\b' + re.escape(original) + r'\b'
                    sentence = re.sub(pattern, replacement, sentence, flags=re.IGNORECASE)
                processed_sentences.append(sentence)
                
            section["english"] = processed_sentences
        
        result["sections"].append(section)
    
    return result
