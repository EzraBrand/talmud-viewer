import re
import urllib.parse
import requests

# Define term replacements
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

# Maximum sections to fetch
MAX_SECTIONS = 100

# Generate pages: 2a, 2b, 3a, 3b, etc.
pages = [f"{daf}{suffix}" for daf in range(2, 181) for suffix in ['a', 'b']]

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
        "Bava Batra", "Sanhedrin", "Makkot", "Shevuot", "Avodah Zarah", "Horayot",
        "Zevachim", "Menachot", "Chullin", "Bekhorot", "Arakhin", "Temurah", "Keritot",
        "Meilah", "Kinnim", "Tamid", "Middot", "Niddah"]
        
    url = url.split('?')[0]  # Remove query params

    # Extract reference part
    parts = url.split('/')
    reference = next((part for part in parts if any(t in part for t in tractates)
                    or re.search(r'[A-Za-z]+\.\d+[ab]', part)), None)

    if not reference:
        return {'error': 'Invalid URL format'}

    # Check for section range on same page (e.g., "Tractate.44a.2-4")
    match = re.match(r'([^\.]+)\.(\d+[ab])\.(\d+)-(\d+)$', reference)
    if match:
        return {
            'type': 'range',
            'start': {'tractate': match.group(1), 'page': match.group(2), 'section': int(match.group(3))},
            'end': {'tractate': match.group(1), 'page': match.group(2), 'section': int(match.group(4))}
        }

    # Check for range (page-page or complex)
    if '-' in reference:
        start_ref, end_ref = reference.split('-')

        # Parse start reference
        start_match = re.match(r'([^\.]+)\.([^\.]+)(?:\.([^\.]+))?', start_ref)
        if not start_match:
            return {'error': 'Invalid reference format'}

        start_tractate = start_match.group(1)
        start_page = start_match.group(2)
        start_section = int(start_match.group(3)) if start_match.group(3) else None

        # Parse end reference
        end_match = re.match(r'(?:([A-Za-z]+)\.)?(\d+[ab])(?:\.(\d+))?', end_ref)
        if not end_match:
            return {'error': 'Invalid reference format'}

        end_tractate = end_match.group(1) or start_tractate
        end_page = end_match.group(2)
        end_section = int(end_match.group(3)) if end_match.group(3) else None

        # For same page with no end section, set a default range
        if end_page == start_page and start_section and not end_section:
            end_section = start_section + 2

        return {
            'type': 'range',
            'start': {'tractate': start_tractate, 'page': start_page, 'section': start_section},
            'end': {'tractate': end_tractate, 'page': end_page, 'section': end_section}
        }

    # Single reference
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

        # Limit to MAX_SECTIONS
        filtered_data = {
            'text': data.get('text', [])[:MAX_SECTIONS] if isinstance(data.get('text', []), list) else [],
            'he': data.get('he', [])[:MAX_SECTIONS] if 'he' in data and isinstance(data['he'], list) else [],
            'span': f"{tractate} {page}:1-{min(MAX_SECTIONS, len(data.get('text', [])))}"
        }
        return filtered_data

    except Exception as e:
        return {"error": str(e)}

def fetch_text_range(start_ref, end_ref):
    """Fetch a range of texts, either on same page or across pages"""
    # Only support ranges within same tractate
    if start_ref['tractate'] != end_ref['tractate']:
        return {"error": "Cross-tractate ranges not supported"}

    tractate = start_ref['tractate']
    start_page = start_ref['page']
    end_page = end_ref['page']
    start_section = start_ref['section']
    end_section = end_ref['section']
    sections_count = 0

    # Handle same-page range
    if start_page == end_page:
        data = fetch_text(tractate, start_page)
        if "error" in data:
            return data

        # Filter to sections in range
        if start_section and end_section:
            start_idx = start_section - 1
            end_idx = min(end_section, len(data.get('text', [])))

            filtered_data = {
                'text': data.get('text', [])[start_idx:end_idx] if start_idx < len(data.get('text', [])) else [],
                'he': data.get('he', [])[start_idx:end_idx] if 'he' in data and start_idx < len(data.get('he', [])) else [],
                'span': f"{tractate} {start_page}:{start_section}-{end_section}"
            }
            return filtered_data

        # Default to MAX_SECTIONS limit
        return data

    # Handle cross-page range
    combined_data = {
        'text': [],
        'he': [],
        'span': f"{tractate} {start_page}:{start_section or '1'}-{end_page}:{end_section or 'end'}"
    }

    # Get pages in range
    all_pages = []
    in_range = False
    for page in pages:
        if page == start_page:
            in_range = True
        if in_range:
            all_pages.append(page)
        if page == end_page:
            break

    # Process each page
    for i, page in enumerate(all_pages):
        if sections_count >= MAX_SECTIONS:
            break

        page_data = fetch_text(tractate, page)
        if "error" in page_data:
            continue

        # Apply filters based on position in range
        if i == 0 and start_section:  # First page
            start_idx = start_section - 1
            sections_to_add = min(len(page_data.get('text', [])) - start_idx, MAX_SECTIONS - sections_count)
            combined_data['text'].extend(page_data.get('text', [])[start_idx:start_idx + sections_to_add])
            combined_data['he'].extend(page_data.get('he', [])[start_idx:start_idx + sections_to_add]
                                     if 'he' in page_data else [])
            sections_count += sections_to_add

        elif i == len(all_pages) - 1 and end_section:  # Last page
            end_idx = min(end_section, MAX_SECTIONS - sections_count)
            if end_idx > 0:
                combined_data['text'].extend(page_data.get('text', [])[:end_idx])
                combined_data['he'].extend(page_data.get('he', [])[:end_idx] if 'he' in page_data else [])
                sections_count += end_idx

        else:  # Middle pages
            sections_to_add = min(len(page_data.get('text', [])), MAX_SECTIONS - sections_count)
            combined_data['text'].extend(page_data.get('text', [])[:sections_to_add])
            combined_data['he'].extend(page_data.get('he', [])[:sections_to_add] if 'he' in page_data else [])
            sections_count += sections_to_add

    # Update span with what was actually retrieved
    if combined_data['text']:
        if start_page == end_page:
            combined_data['span'] = f"{tractate} {start_page}:{start_section}-{min(end_section, start_section + sections_count - 1)}"
        else:
            if all_pages and sections_count:
                page_idx = min(sections_count // 10, len(all_pages) - 1)
                combined_data['span'] = f"{tractate} {start_page}:{start_section or '1'}-{all_pages[page_idx]}:{(sections_count % 10) or 10}"

    return combined_data

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

    # Limit to MAX_SECTIONS
    max_len = min(MAX_SECTIONS, min(len(he_text), len(en_text)))
    he_text = he_text[:max_len]
    en_text = en_text[:max_len]

    # Process each section
    for i in range(min(len(he_text), len(en_text))):
        current_he = he_text[i]
        current_en = en_text[i]

        # Skip empty sections
        if not current_he and not current_en:
            continue

        section = {"hebrew": [], "english": []}

        # Hebrew text
        if current_he:
            current_he = remove_nikud(current_he)
            section["hebrew"] = split_into_sentences(current_he)

        # English text
        if current_en:
            # Apply term replacements to each sentence
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
