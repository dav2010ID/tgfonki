"""
Text formatting module for handling song lyrics.
"""
import re
from typing import Dict, Optional, Set, Tuple, Any, List


# Regular expression for chord detection
CHORD_REGEX = re.compile(
    r'^[A-H][b#]?('
    r'2|5|6|7|9|11|13|\+[2-9]|\+1[1-3]|6/9|7[-#]5|7[-#]9|7\+[35]|7\+9|7b[59]|'
    r'7sus[24]|sus4|add[2469]|aug|dim|dim7|m/maj7|m[67]|m7b5|m(9|11|13)|'
    r'maj[79]?|maj1[1-3]|mb5|m|sus[24]?|m7add11|add11|b5|-5|4'
    r')*(/[A-H][b#]*)*$', re.I
)

# Special symbols that might appear in chord lines
CHORD_SYMBOLS: Set[str] = {'|', '/', '(', ')', '-', 'x2', 'x3', 'x4', 'x5', 'x6', 'NC'}

# Labels for song sections in different languages
SECTION_LABELS: Set[str] = {
    *[f"{i}|" for i in range(10)],
    *[f"{i}:" for i in range(10)],
    *map(str.lower, [
        'Вступление:', 'Интро:', 'Куплет:', 'Припев:', 'Переход:', 'Реп:',
        'Мост:', 'Мостик:', 'Вставка:', 'Речитатив:', 'Бридж:', 'Инструментал:',
        'Проигрыш:', 'Запев:', 'Концовка:', 'Окончание:', 'В конце:', 'Кода:', 'Тэг:',
        'Intro:', 'Verse:', 'Chorus:', 'Pre chorus:', 'Pre-chorus:', 'Bridge:',
        'Instrumental:', 'Ending:', 'Outro:', 'Interlude:', 'Rap:', 'Spontaneous:',
        'Refrain:', 'Tag:', 'Coda:', 'Vamp:', 'Channel:', 'Breakdown:', 'Hook:',
        'Вступ:', 'Приспів:', 'Брідж:', 'Заспів:', 'Міст:', 'Програш:',
        'Перехід:', 'Інтро:', 'Повтор:', 'Кінець:', 'Тег:'
    ])
}


def trim(s: Any) -> str:
    """Trim whitespace from a string if it is a string."""
    return s.strip() if isinstance(s, str) else ''


def is_non_empty(s: Any) -> bool:
    """Check if a value is a non-empty string."""
    return isinstance(s, str) and bool(s.strip())


def clean_html_entities(s: Any) -> str:
    """Remove HTML entities from a string."""
    return re.sub(r'&[\w#]+;', '', s) if is_non_empty(s) else ''


def is_chord_line(line: str) -> bool:
    """
    Determine if a line contains only chord notations.
    
    Args:
        line: A single line of text
        
    Returns:
        True if the line contains only chord notations, False otherwise
    """
    if not is_non_empty(line):
        return False
    tokens = trim(line).split()
    return all(CHORD_REGEX.match(t) or any(sym in t for sym in CHORD_SYMBOLS) for t in tokens)


def is_section_label(line: str) -> bool:
    """
    Check if a line is a section label (like 'Chorus:', 'Verse:', etc.)
    
    Args:
        line: A single line of text
        
    Returns:
        True if the line is a section label, False otherwise
    """
    line = trim(line).lower()
    return any(line.startswith(label.rstrip(':|')) for label in SECTION_LABELS)


def is_numbered_section(line: str) -> Optional[Dict[str, str]]:
    """
    Check if a line is a numbered section (like '1 куплет', '2 verse', etc.)
    
    Args:
        line: A single line of text
        
    Returns:
        Dictionary with 'number' and 'type' keys if it's a numbered section, None otherwise
    """
    match = re.match(r'^(\d+)\s*(куплет|бридж|verse|bridge)', line.strip(), re.I)
    return {'number': match[1], 'type': match[2].capitalize()} if match else None


def format_lines(text: str) -> str:
    """
    Format text by handling special markers and spacing.
    
    Args:
        text: Multiline text to format
        
    Returns:
        Formatted text
    """
    if not is_non_empty(text):
        return ''
    lines = text.split('\n')
    result: List[str] = []
    found_header = False

    for line in lines:
        line = trim(line)
        if line.startswith('##('):
            if found_header and result and result[-1] != '':
                result.append('')
            found_header = True
        if line != '//':
            result.append(line)
    return trim('\n'.join(result))


def format_song(raw_text: str) -> str:
    """
    Format song lyrics by removing chord lines and standardizing section labels.
    
    Args:
        raw_text: Raw song lyrics text
        
    Returns:
        Formatted song lyrics
    """
    if not is_non_empty(raw_text):
        return ''
    text = clean_html_entities(raw_text)
    output: List[str] = []

    for line in text.split('\n'):
        line = trim(line)
        if not line or is_chord_line(line):
            continue
        if section := is_numbered_section(line):
            output.append(f"{section['type']} {section['number']}:")
        elif is_section_label(line):
            output.append(re.sub(r'[:|]$', '', line) + ':')
        else:
            output.append(line)

    return format_lines('\n'.join(output))