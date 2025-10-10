import os
import fitz
import re
import logging
import io

logger = logging.getLogger("pdf_reader")

def get_pdf_content(file_obj):
    full_text = ""
    try:
        doc = fitz.open(stream=io.BytesIO(file_obj.read()), filetype="pdf")
        for page in doc:
            full_text += page.get_text()
        doc.close()
    except Exception as e:
        logger.error(f"Error reading PDF content: {e}")
    return full_text
    
def search_pdf_content(file_obj, file_path, query):
    try:
        query_parts = query.strip().split()
        escaped_query_parts = [re.escape(part) for part in query_parts]
        regex_pattern_str = r'\s+'.join(escaped_query_parts)
        matcher = re.compile(regex_pattern_str, re.IGNORECASE)

    except re.error as e:
        logger.error(f"Invalid regex pattern: {e}")
        return {"status": "error", "message": f"Invalid regex pattern: {e}"}, 400

    results = []
    
    try:
        doc = fitz.open(stream=io.BytesIO(file_obj.read()), filetype="pdf")

        for pno in range(len(doc)):
            page = doc[pno]
            blocks = page.get_text("blocks")
            
            found_in_blocks = False
            for block_num, block in enumerate(blocks, start=1):
                block_text = block[4]
                
                for m in matcher.finditer(block_text):
                    start_index = max(0, m.start() - 50)
                    end_index = min(len(block_text), m.end() + 50)
                    
                    highlighted_preview = (
                        block_text[start_index:m.start()] +
                        f"**{block_text[m.start():m.end()]}**" +
                        block_text[m.end():end_index]
                    )
                    highlighted_preview = re.sub(r'\s+', ' ', highlighted_preview).strip()

                    results.append({
                        "file": os.path.basename(file_path),
                        "path": file_path,
                        "page": pno + 1,
                        "line": block_num,
                        "preview": highlighted_preview
                    })
                    found_in_blocks = True
            
            if not found_in_blocks:
                full_page_text = page.get_text("text") or ""
                for m in matcher.finditer(full_page_text):
                    start_index = max(0, m.start() - 50)
                    end_index = min(len(full_page_text), m.end() + 50)
                    
                    highlighted_preview = (
                        full_page_text[start_index:m.start()] +
                        f"**{full_page_text[m.start():m.end()]}**" +
                        full_page_text[m.end():end_index]
                    )
                    highlighted_preview = re.sub(r'\s+', ' ', highlighted_preview).strip()

                    results.append({
                        "file": os.path.basename(file_path),
                        "path": file_path,
                        "page": pno + 1,
                        "line": None,
                        "preview": highlighted_preview
                    })

        doc.close()
    except fitz.FileDataError as e:
        logger.warning(f"Could not open/process {os.path.basename(file_path)}: {e}")
    except Exception as e:
        logger.exception(f"An error occurred while processing {os.path.basename(file_path)}: {e}")
        
    return {"status": "ok", "matches": results, "count": len(results)}, 200