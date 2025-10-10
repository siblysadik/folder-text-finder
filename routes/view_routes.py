# routes/view_routes.py (পরিবর্তিত কোড)

from flask import Blueprint, request, jsonify, Response, render_template
import logging
import io
import os
import secrets
import re
from urllib.parse import quote
# 🚀 globals থেকে কেন্দ্রীয় TEMP_FILE_STORAGE ইম্পোর্ট করা হলো
from globals import TEMP_FILE_STORAGE
# 🚀 services/file_reader.py থেকে নতুন ফাংশন ইম্পোর্ট করা হলো
from services.file_reader import get_file_text_content 

view_bp = Blueprint('view', __name__)
logger = logging.getLogger("view_routes")

def get_mime_type(filename):
    extension = os.path.splitext(filename)[1].lower()
    if extension == '.pdf':
        return 'application/pdf'
    elif extension == '.docx':
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif extension == '.doc':
        return 'application/msword'
    else:
        return 'application/octet-stream'

@view_bp.route("/upload_for_view", methods=["POST"])
def upload_for_view():
    uploaded_file = request.files.get("file")
    # 🚀 ফ্রন্টএন্ড থেকে পাঠানো 'original_path' অ্যাক্সেস করা হলো
    original_path = request.form.get('original_path') 
    
    if not uploaded_file:
        return jsonify({"status": "error", "message": "No file uploaded."}), 400

    try:
        file_content_bytes = uploaded_file.read()
        file_id = secrets.token_hex(16)
        
        # 🚀 কেন্দ্রীয় স্টোরেজে 'original_path' সংরক্ষণ করা হলো
        TEMP_FILE_STORAGE[file_id] = {
            'data': file_content_bytes,
            'filename': uploaded_file.filename,
            'original_path': original_path 
        }
        
        return jsonify({"status": "ok", "file_id": file_id})
    except Exception as e:
        logger.exception("Failed to upload file for viewing.")
        return jsonify({"status": "error", "message": str(e)}), 500

@view_bp.route("/get_file/<file_id>", methods=["GET"])
def get_file(file_id):
    file_info = TEMP_FILE_STORAGE.get(file_id)
    if not file_info:
        return jsonify({"status": "error", "message": "File not found or has expired."}), 404

    file_content_bytes = file_info['data']
    file_filename = file_info['filename']
    mime_type = get_mime_type(file_filename)
    
    resp = Response(file_content_bytes, mimetype=mime_type)
    
    # Set Content-Disposition to 'attachment' for ALL non-PDF files to ensure download
    # 🛑 .docx, .doc, ও অন্যান্য ফাইলগুলি এখন /get_file/ এ ডিফল্টভাবে ডাউনলোড হবে
    if mime_type != 'application/pdf':
        resp.headers.add("Content-Disposition", f'attachment; filename*=UTF-8\'\'{quote(os.path.basename(file_filename))}')
    
    return resp

@view_bp.route("/view_code/<file_id>", methods=["GET"])
def view_code(file_id):
    file_info = TEMP_FILE_STORAGE.get(file_id)
    if not file_info:
        return "File not found.", 404
    
    query = request.args.get('q', '')
    return render_template("code_viewer.html", file_id=file_id, query=query)

# 🚀 নতুন রুট: Word ফাইল থেকে টেক্সট বের করে দেখানোর জন্য
@view_bp.route("/view_text/<file_id>", methods=["GET"])
def view_text(file_id):
    file_info = TEMP_FILE_STORAGE.get(file_id)
    if not file_info:
        return "File not found or has expired.", 404
    
    query = request.args.get('q', '')
    
    try:
        # file_reader সার্ভিস ব্যবহার করে ফাইল থেকে টেক্সট বের করা হলো
        # get_file_text_content ফাংশনটি এখন নিচে services/file_reader.py তে যোগ করা হবে
        file_text = get_file_text_content(file_id, TEMP_FILE_STORAGE)
        
        if file_text is None:
             return "Error: Could not extract text content from the file.", 500
        
        # টেক্সটটি HTML এ পাঠানোর জন্য উপযুক্ত করে এনকোড করা হলো
        return render_template(
            "code_viewer.html", 
            file_id=file_id, 
            query=query, 
            preloaded_content=file_text, 
            filename=file_info['filename']
        )
        
    except Exception as e:
        logger.exception(f"Error reading file {file_info.get('filename')} for text view.")
        return f"Error: Failed to process file for text view: {e}", 500