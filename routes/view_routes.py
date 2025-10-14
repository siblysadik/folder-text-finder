# routes/view_routes.py (আপডেট করা)

from flask import Blueprint, request, jsonify, render_template, send_file, Response, redirect, url_for
from globals import FILE_STORAGE_DICT, FILE_STORAGE_LOCK
# 💡 file_reader থেকে দুটি ফাংশন ইম্পোর্ট করা হলো
from services.file_reader import get_file_text_content, open_folder_in_os
from pathlib import Path
import logging
import uuid
import threading
import mimetypes
import io # send_file এর জন্য io import করা হলো

view_bp = Blueprint('view', __name__)
logger = logging.getLogger("view_routes")

# ----------------- UPLOAD/STORAGE ROUTE (No change needed here) -----------------

@view_bp.route("/upload_for_view", methods=["POST"])
def upload_for_view():
    """
    Receives an uploaded file and its original path, stores it in memory, 
    and returns a unique file_id.
    """
    try:
        if 'file' not in request.files:
            # 500 error এর পরিবর্তে 400 JSON response নিশ্চিত করা হলো
            return jsonify({"status": "error", "message": "No file part in the request."}), 400
        
        uploaded_file = request.files['file']
        # 'original_path' এখন absolute path হিসেবে আসবে
        original_path = request.form.get('original_path')

        if not uploaded_file.filename:
            return jsonify({"status": "error", "message": "No selected file."}), 400
        
        file_id = str(uuid.uuid4())
        file_content_bytes = uploaded_file.read()
        
        # 🌟 থ্রেড-সেফ সেভিং
        with FILE_STORAGE_LOCK:
            FILE_STORAGE_DICT[file_id] = {
                'data': file_content_bytes,
                'filename': uploaded_file.filename,
                'original_path': original_path, # অ্যাবসোলিউট পাথ সেভ করা হলো
                'timestamp': threading.local(), 
                'size': len(file_content_bytes)
            }
        
        logger.info(f"File uploaded and stored: ID={file_id}, Name={uploaded_file.filename}, Size={len(file_content_bytes)} bytes")
        
        return jsonify({"status": "ok", "file_id": file_id}), 200

    except Exception as e:
        logger.exception("Error during file upload for viewing.")
        # 500 internal server error এর জন্যও JSON response নিশ্চিত করা হলো
        return jsonify({"status": "error", "message": f"An internal server error occurred: {e}"}), 500

# ----------------- VIEWER ROUTES (No change needed here) -----------------

@view_bp.route("/view_code/<file_id>")
def view_code(file_id):
    """
    Viewer for code/generic text files. Preloads content in HTML.
    """
    query = request.args.get('q', '').strip()
    
    with FILE_STORAGE_LOCK:
        file_info = FILE_STORAGE_DICT.get(file_id)

    if not file_info:
        return "File not found or session expired.", 404

    try:
        # বাইনারি ডেটা সরাসরি কন্টেন্টে ডিকোড করা হলো (ছোট ফাইলের জন্য)
        file_content_bytes = file_info['data']
        preloaded_content = file_content_bytes.decode('utf-8', errors='replace')
        
        return render_template(
            "code_viewer.html",
            file_id=file_id,
            filename=file_info['filename'],
            query=query,
            preloaded_content=preloaded_content
        )
    except Exception as e:
        logger.error(f"Error reading file content for view_code/{file_id}: {e}")
        return f"Error reading file content: {e}", 500


@view_bp.route("/view_text/<file_id>")
def view_text(file_id):
    """
    Special viewer for large text files (DOCX/XLSX/CSV). Loads content via JS.
    """
    query = request.args.get('q', '').strip()
    
    with FILE_STORAGE_LOCK:
        file_info = FILE_STORAGE_DICT.get(file_id)

    if not file_info:
        return "File not found or session expired.", 404

    # কন্টেন্ট লোড না করার জন্য None পাঠানো হলো। JS পরে /get_file/ কল করবে।
    return render_template(
        "code_viewer.html", 
        file_id=file_id,
        filename=file_info['filename'],
        query=query,
        preloaded_content=None 
    )


# ----------------- FILE RETRIEVAL ROUTE (FIXED FOR PDF VIEWING) -----------------

@view_bp.route("/get_file/<file_id>")
def get_file(file_id):
    """
    Serves the file content.
    - For DOCX/XLSX/CSV/DOC, returns the plain text content.
    - For PDF, returns the file data without attachment header to open in browser.
    - For others, returns the file data as attachment for download.
    """
    with FILE_STORAGE_LOCK:
        file_info = FILE_STORAGE_DICT.get(file_id)

    if not file_info:
        return "File not found or session expired.", 404

    filename = file_info['filename']
    file_content_bytes = file_info['data']
    file_extension = Path(filename).suffix.lower()

    # 🌟 PDF ফাইল ব্রাউজারে খোলার জন্য বিশেষ হ্যান্ডলিং
    if file_extension == '.pdf':
        # io.BytesIO ব্যবহার করে বাইট ডেটাকে ফাইল স্ট্রিম হিসেবে send_file এ পাঠানো
        return send_file(
            io.BytesIO(file_content_bytes),
            mimetype='application/pdf',
            as_attachment=False, # <--- attachment বন্ধ করা হলো
            download_name=filename 
        )

    # 🌟 Excel/CSV/DOCX/DOC এর জন্য প্লেইন টেক্সট কন্টেন্ট জেনারেট করা হলো
    TEXT_GENERATION_EXTENSIONS = {'.docx', '.doc', '.xlsx', '.xls', '.csv'}
    
    if file_extension in TEXT_GENERATION_EXTENSIONS:
        try:
            # services/file_reader.py থেকে টেক্সট কন্টেন্ট জেনারেট করা হলো
            full_text = get_file_text_content(file_id, FILE_STORAGE_DICT)
            
            if full_text is None:
                return "Failed to extract text content.", 500
            
            # Text/Plain MIME type সেট করা হলো
            response = Response(full_text, mimetype='text/plain; charset=utf-8')
            
            # ফ্রন্টএন্ডে ফাইলের নাম পাঠানোর জন্য Content-Disposition হেডার যোগ করা হলো
            encoded_filename = filename.encode('utf-8').decode('latin-1', 'ignore')
            response.headers['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8''{filename}'

            return response
            
        except Exception as e:
            logger.error(f"Error processing text for /get_file/{file_id}: {e}")
            return f"Error processing file content: {e}", 500

    # 🌟 অন্যান্য ফাইল (যেমন Code/TXT) এর জন্য বাইনারি ফাইল ডেটা রিটার্ন করা হলো
    
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = 'application/octet-stream'

    
    return Response(
        file_content_bytes,
        mimetype=mime_type,
        headers={
            # এই ফাইলগুলো (যা পিডিএফ বা টেক্সট জেনারেটেড নয়) বাই ডিফল্ট ডাউনলোড হবে
            "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{filename}" 
        }
    )

# ----------------- FOLDER OPEN ROUTE (No change needed here) -----------------

@view_bp.route("/open_folder/<file_id>", methods=["POST"])
def open_folder(file_id):
    """
    Opens the original folder location of the file using the saved absolute path.
    """
    with FILE_STORAGE_LOCK:
        file_info = FILE_STORAGE_DICT.get(file_id)

    if not file_info:
        # File ID না পাওয়া গেলে JSON response নিশ্চিত করা হলো
        return jsonify({"status": "error", "message": "File ID not found or session expired."}), 404

    original_path = file_info.get('original_path')
    
    if not original_path:
        return jsonify({"status": "error", "message": "Original path not recorded for this file."}), 400

    try:
        # services/file_reader.py এর ফাংশন ব্যবহার করে ফোল্ডার ওপেন করা হলো
        success = open_folder_in_os(original_path)
        
        if success:
            logger.info(f"Successfully sent command to open folder for path: {original_path}")
            return jsonify({"status": "ok", "message": "Folder open command executed successfully."}), 200
        else:
            logger.error(f"Failed to execute folder open command for path: {original_path}")
            return jsonify({"status": "error", "message": "Failed to open folder on the server. (This only works in a local environment)"}), 500

    except Exception as e:
        logger.exception("Error executing open folder command.")
        return jsonify({"status": "error", "message": f"An internal error occurred while opening the folder: {e}"}), 500