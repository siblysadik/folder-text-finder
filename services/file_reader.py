# services/file_reader.py (Updated for Excel/CSV)

import os
import logging
import subprocess 
import io
from .readers.pdf_reader import search_pdf_content
from .readers.docx_reader import get_docx_content 
from .readers.doc_reader import get_doc_content
from .readers.text_reader import get_text_content, search_text_content
# 🚀 নতুন ইম্পোর্ট
from .readers.excel_reader import get_excel_content, get_csv_content 

logger = logging.getLogger("file_reader_service")

# 🚀 TEXT_EXTENSIONS এর সাথে নতুন Excel/CSV এক্সটেনশন যোগ করা হলো
TEXT_EXTENSIONS = {
    '.py', '.js', '.java', '.class', '.cpp', '.cc', '.cxx', '.hpp', '.hxx',
    '.cs', '.ts', '.tsx', '.go', '.c', '.h', '.php', '.phtml', '.sql', '.rs',
    '.rb', '.swift', '.kt', '.kts', '.r', '.R', '.pl', '.pm', '.dart', '.scala',
    '.sc', '.vb', '.asm', '.s', '.html', '.htm', '.css', '.m', '.mat', '.sh',
    '.bash', '.cls', '.cbl', '.cob', '.fs', '.fsi', '.fsx', '.ps1', '.plsql',
    '.scm', '.ss', '.tsql', '.cr', '.pro', '.pl', '.vhd', '.vhdl', '.d', '.abap',
    '.txt', '.md', '.log', '.json', '.xml', '.yml', '.yaml', '.toml',
    # 🚀 নতুন সংযোজন
    '.xlsx', '.xls', '.csv' 
}

EXCEL_EXTENSIONS = {'.xlsx', '.xls'}
CSV_EXTENSION = {'.csv'}

# ------------------ New Function for Text Content Retrieval ------------------
def get_file_text_content(file_id, file_storage):
    """
    Retrieves the plain text content of a file (.docx, .doc, .xlsx, .xls, .csv, or other text file) 
    from the temporary storage.
    """
    file_info = file_storage.get(file_id)
    if not file_info:
        return None
    
    file_content_bytes = file_info['data']
    file_filename = file_info['filename']
    file_extension = os.path.splitext(file_filename)[1].lower()
    
    temp_uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'temp_uploads')

    file_obj = io.BytesIO(file_content_bytes)
    
    if file_extension == '.docx':
        return get_docx_content(file_obj)
    
    elif file_extension == '.doc':
        return get_doc_content(file_obj, file_filename, temp_uploads_dir)
    
    # 🚀 Excel ফাইল হ্যান্ডলিং
    elif file_extension in EXCEL_EXTENSIONS:
        return get_excel_content(file_obj, file_filename)
        
    # 🚀 CSV ফাইল হ্যান্ডলিং
    elif file_extension in CSV_EXTENSION:
        return get_csv_content(file_obj)
    
    elif file_extension in TEXT_EXTENSIONS:
        # অন্যান্য টেক্সট ফাইলগুলোর জন্য (যেমন .py, .txt ইত্যাদি)
        return get_text_content(file_obj)
    
    else:
        logger.warning(f"Attempted to view unsupported file type {file_extension} as plain text.")
        return None

# ------------------ Open Folder Functions (আগের মতোই রাখা হলো) ------------------
def get_original_folder_path(file_id, file_storage):
    file_info = file_storage.get(file_id)
    if file_info and 'original_path' in file_info:
        return os.path.dirname(file_info['original_path'])
    return None

def open_folder_in_os(folder_path):
    try:
        if os.path.isfile(folder_path):
            folder_path = os.path.dirname(folder_path)

        if not folder_path or folder_path.strip() == os.path.curdir:
             logger.error(f"Cannot open folder: Path is ambiguous or empty: {folder_path}")
             return False
             
        if os.name == 'nt':
            folder_path_win = folder_path.replace('/', '\\')
            subprocess.Popen(['explorer', folder_path_win]) 
            
        elif os.uname().sysname == 'Darwin': # macOS
            subprocess.Popen(['open', folder_path])
        else: # Linux (and others)
            subprocess.Popen(['xdg-open', folder_path])
            
        return True
    except Exception as e:
        logger.error(f"Failed to open folder '{folder_path}' in OS: {e}")
        return False
# ------------------------------------------------------------------

def search_file_content(file_item, query, temp_uploads_dir):
    file_obj = file_item['file_obj']
    file_name = file_item['file_name']
    file_path = file_item['file_path']
    file_extension = os.path.splitext(file_name)[1].lower()

    if file_extension == '.pdf':
        return search_pdf_content(file_obj, file_path, query)

    elif file_extension == '.docx':
        full_text = get_docx_content(file_obj)
        if not full_text:
            return {"status": "error", "message": f"Could not read content from {file_name}"}, 500
        return search_text_content(full_text, file_name, file_path, query)

    elif file_extension == '.doc':
        full_text = get_doc_content(file_obj, file_name, temp_uploads_dir)
        if not full_text:
            return {"status": "error", "message": f"Could not read content from {file_name}"}, 500
        return search_text_content(full_text, file_name, file_path, query)
        
    # 🚀 Excel ফাইল হ্যান্ডলিং
    elif file_extension in EXCEL_EXTENSIONS:
        full_text = get_excel_content(file_obj, file_name)
        if not full_text:
            return {"status": "error", "message": f"Could not read content from {file_name}. Check if required libraries (openpyxl/xlrd) are installed."}, 500
        # Excel/CSV-এর জন্য text_reader-এর সার্চ ফাংশন ব্যবহার করা হলো
        return search_text_content(full_text, file_name, file_path, query)

    # 🚀 CSV ফাইল হ্যান্ডলিং
    elif file_extension in CSV_EXTENSION:
        full_text = get_csv_content(file_obj)
        if not full_text:
            return {"status": "error", "message": f"Could not read content from {file_name}. Check if required libraries (pandas) are installed."}, 500
        return search_text_content(full_text, file_name, file_path, query)

    elif file_extension in TEXT_EXTENSIONS:
        full_text = get_text_content(file_obj)
        if not full_text:
            return {"status": "error", "message": f"Could not read content from {file_name}"}, 500
        return search_text_content(full_text, file_name, file_path, query)

    else:
        return {"status": "error", "message": f"Unsupported file type: {file_extension}"}, 400