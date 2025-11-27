#!/usr/bin/env python3
"""
Script zum Entfernen von Emojis aus Logger-Nachrichten in Scraper-Dateien
Ersetzt Emojis am Anfang von Logger-Nachrichten durch nichts, ohne Whitespace zu erzeugen
"""

import re
from pathlib import Path

# Emoji-Pattern (Unicode ranges für gängige Emojis)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # Symbols & Pictographs
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F680-\U0001F6FF"  # Transport & Map
    "\U0001F1E0-\U0001F1FF"  # Flags
    "\U00002600-\U000027BF"  # Misc symbols (includes ⏳)
    "\U0000231A-\U0000231B"  # Watches
    "\U000024C2-\U0001F251"  # Enclosed characters
    "\U00002300-\U000023FF"  # Misc Technical (zusätzlich)
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols
    "]+", 
    flags=re.UNICODE
)

def remove_emojis_from_logger(content: str) -> str:
    """
    Entfernt Emojis aus logger-Aufrufen
    
    Beispiel:
        logger.info("✅ Browser initialisiert")
        -> logger.info("Browser initialisiert")
    """
    # Einfachere Lösung: Zeilenweise bearbeiten
    lines = content.split('\n')
    result_lines = []
    
    for line in lines:
        # Prüfe ob Zeile einen logger-Aufruf enthält
        if 'logger.' in line and ('logger.info' in line or 'logger.warning' in line or 
                                   'logger.error' in line or 'logger.debug' in line):
            # Bewahre die Einrückung
            indent = len(line) - len(line.lstrip())
            indent_str = line[:indent]
            
            # Entferne ALLE Emojis aus dem Rest der Zeile
            line_content = line[indent:]
            original = line_content
            cleaned = EMOJI_PATTERN.sub('', line_content)
            
            # Wenn Emojis entfernt wurden, bereinige überflüssige Leerzeichen
            if cleaned != original:
                # Entferne doppelte Leerzeichen die durch Emoji-Entfernung entstanden sind
                cleaned = re.sub(r'  +', ' ', cleaned)
                # Entferne Leerzeichen direkt nach öffnendem Quote
                cleaned = re.sub(r'(["\'])\s+', r'\1', cleaned)
            
            # Füge Einrückung wieder hinzu
            line = indent_str + cleaned
        
        result_lines.append(line)
    
    return '\n'.join(result_lines)

def find_string_end(text: str, start: int) -> int:
    """Findet das Ende eines Python-Strings mit Escape-Handling"""
    quote_char = text[start]
    i = start + 1
    
    while i < len(text):
        if text[i] == '\\':
            i += 2  # Skip escaped character
            continue
        if text[i] == quote_char:
            return i + 1
        i += 1
    
    return -1

def process_file(filepath: Path) -> tuple[bool, int]:
    """
    Bearbeitet eine Datei und entfernt Emojis
    
    Returns:
        (changed, emoji_count): Ob die Datei geändert wurde und wie viele Emojis entfernt wurden
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        original_content = content
        
        # Zähle Emojis vor der Entfernung
        emoji_count = len(EMOJI_PATTERN.findall(content))
        
        # Entferne Emojis
        new_content = remove_emojis_from_logger(content)
        
        if new_content != original_content:
            filepath.write_text(new_content, encoding='utf-8')
            return True, emoji_count
        
        return False, 0
        
    except Exception as e:
        print(f"❌ Fehler bei {filepath}: {e}")
        return False, 0

def main():
    """Hauptfunktion"""
    # Finde alle Scraper-Dateien
    scraper_files = [
        Path('src/webscraping/scraper_enbw_strom.py'),
        Path('src/webscraping/scraper_enbw.py'),
        Path('src/webscraping/scraper_tibber.py'),
        Path('src/webscraping/scraper_tado.py'),
    ]
    
    total_changed = 0
    total_emojis = 0
    
    print("🔧 Starte Emoji-Entfernung aus Scraper-Dateien...\n")
    
    for filepath in scraper_files:
        if not filepath.exists():
            print(f"⚠️  Überspringe (nicht gefunden): {filepath}")
            continue
            
        changed, emoji_count = process_file(filepath)
        
        if changed:
            total_changed += 1
            total_emojis += emoji_count
            print(f"✓  Bearbeitet: {filepath.name} ({emoji_count} Emojis entfernt)")
        else:
            print(f"○  Unverändert: {filepath.name}")
    
    print(f"\n{'='*60}")
    print(f"Zusammenfassung:")
    print(f"  Dateien bearbeitet: {total_changed}")
    print(f"  Emojis entfernt: {total_emojis}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
