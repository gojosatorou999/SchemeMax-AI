import json
import os
from flask import session, current_app

def load_translations(lang):
    """Load translation JSON from disk."""
    path = os.path.join(current_app.root_path, 'translations', f'{lang}.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def t(key, default=None):
    """
    Template helper to translate a key.
    Reads current language from session.
    """
    lang = session.get('lang', 'en')
    
    # Try current language
    translations = load_translations(lang)
    if key in translations:
        return translations[key]
        
    # Fallback to English
    if lang != 'en':
        en_translations = load_translations('en')
        if key in en_translations:
            return en_translations[key]
            
    return default or key
