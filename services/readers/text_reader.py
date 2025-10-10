# services/readers/text_reader.py

import logging
import io
import re

logger = logging.getLogger("text_reader")

def get_text_content(file_obj):
    full_text = ""
    try:
        file_obj.seek(0)
        content_bytes = file_obj.read()
        
        # 1. BOM Removal (Important for UTF-8 files with BOM)
        if content_bytes.startswith(b'\xef\xbb\xbf'):
            content_bytes = content_bytes[3:]
            
        # 2. Try decoding with fallbacks
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                full_text = content_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
    except Exception as e:
        logger.error(f"Error reading text file content: {e}")
        return ""
    
    # 3. Standardize Line Endings (CRLF to LF)
    # This is the most crucial step for correct and consistent counting across OS types.
    # Replace all \r\n and \r with a single \n.
    full_text = full_text.replace('\r\n', '\n').replace('\r', '\n') 
    
    return full_text

def search_text_content(full_text, file_name, file_path, query):
    results = []
    
    escaped_query = re.escape(query)
    pattern = re.compile(escaped_query, re.IGNORECASE | re.DOTALL)
    
    # Text split into lines (lines list contains non-empty and empty lines)
    lines = full_text.splitlines(keepends=False)
    
    for match in pattern.finditer(full_text):
        start_index = match.start()
        
        # 1. Find the exact line number of the match
        # Count the number of newline characters ('\n') before the start_index
        line_number = full_text.count('\n', 0, start_index) + 1
        
        # 2. Extract the complete line text
        if 1 <= line_number <= len(lines):
            line_text = lines[line_number - 1]
        else:
            # Fallback
            line_text = match.group()

        # 3. Highlight the preview text on the server-side
        highlighted_preview = re.sub(
            re.escape(match.group()), 
            f"<mark>{match.group()}</mark>", 
            line_text, 
            count=1, 
            flags=re.IGNORECASE | re.DOTALL
        )
        
        results.append({
            "file": file_name,
            "path": file_path,
            "page": "N/A",
            "line": line_number,
            "preview": highlighted_preview
        })
    
    return {"status": "ok", "matches": results, "count": len(results)}, 200