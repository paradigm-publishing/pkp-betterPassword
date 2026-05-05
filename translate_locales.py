import os
import polib
import time
import re
from deep_translator import GoogleTranslator

base_dir = '/usr/local/var/www/ojs-3.4.0-unpublish_issue/plugins/generic/betterPassword/locale'
en_po_path = os.path.join(base_dir, 'en', 'locale.po')

if not os.path.exists(en_po_path):
    print(f"Error: {en_po_path} not found.")
    exit(1)

def safe_translate(translator, text):
    if translator is None:
        return text

    vars = re.findall(r'\{\$[a-zA-Z0-9_]+\}', text)
    placeholder_text = text
    for i, var in enumerate(vars):
        placeholder_text = placeholder_text.replace(var, f"__VAR{i}__")
        
    try:
        translation = translator.translate(placeholder_text)
    except Exception as e:
        print(f"Translation API error: {e}")
        return text
    
    if not translation:
        return text
        
    for i, var in enumerate(vars):
        translation = re.sub(r'__\s*VAR' + str(i) + r'\s*__', var, translation, flags=re.IGNORECASE)
        
    return translation

en_po = polib.pofile(en_po_path)
en_dict = {entry.msgid: entry.msgstr for entry in en_po}

for locale_dir in os.listdir(base_dir):
    locale_path = os.path.join(base_dir, locale_dir)
    if not os.path.isdir(locale_path) or locale_dir == 'en':
        continue
    
    po_path = os.path.join(locale_path, 'locale.po')
    
    if os.path.exists(po_path):
        try:
            po = polib.pofile(po_path)
        except Exception as e:
            print(f"Error loading {po_path}: {e}. Recreating from English.")
            po = polib.pofile(en_po_path)
            for entry in po:
                entry.msgstr = ""
    else:
        po = polib.pofile(en_po_path)
        for entry in po:
            entry.msgstr = ""
            
    lang_code = locale_dir.split('_')[0]
    
    lang_mapping = {
        'ckb': 'ku',
        'nb': 'no',
        'sr': 'sr',
        'zh_CN': 'zh-CN',
        'zh_TW': 'zh-TW',
    }
    
    target_lang = lang_mapping.get(lang_code, lang_code)
    print(f"Processing {locale_dir} ({target_lang})...")
    
    modified = False
    
    valid_entries = []
    for entry in po:
        if entry.msgid in en_dict:
            valid_entries.append(entry)
            
    existing_ids = [e.msgid for e in valid_entries]
    for en_entry in en_po:
        if en_entry.msgid not in existing_ids:
            new_entry = polib.POEntry(
                msgid=en_entry.msgid,
                msgstr='',
                occurrences=en_entry.occurrences
            )
            valid_entries.append(new_entry)
            
    po.clear()
    for e in valid_entries:
        po.append(e)

    try:
        translator = GoogleTranslator(source='en', target=target_lang)
    except Exception as e:
        print(f"Could not initialize translator for {target_lang}: {e}")
        translator = None

    for entry in po:
        if not entry.msgstr or entry.msgstr == entry.msgid or entry.msgstr == en_dict.get(entry.msgid):
            try:
                translation = safe_translate(translator, en_dict[entry.msgid])
                if translation and translation != entry.msgid:
                    entry.msgstr = translation
                    modified = True
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error translating '{entry.msgid}' to {target_lang}: {e}")
                
    if modified:
        po.save(po_path)
        print(f"Saved {po_path}")
    else:
        print(f"No changes for {locale_dir}")

