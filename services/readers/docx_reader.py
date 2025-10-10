import logging
import io
from docx import Document

logger = logging.getLogger("docx_reader")

def get_docx_content(file_obj):
    full_text = ""
    try:
        # docx.Document requires a file path or a seekable file-like object.
        # We use BytesIO to make the in-memory file object seekable.
        doc = Document(io.BytesIO(file_obj.read()))
        for para in doc.paragraphs:
            full_text += para.text + "\n"
    except Exception as e:
        logger.error(f"Error reading DOCX content: {e}")
    return full_text