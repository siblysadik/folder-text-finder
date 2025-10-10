# routes/open_routes.py

from flask import Blueprint, request, jsonify, send_file
import logging
import secrets 
import io 
import os
# 🚀 globals থেকে কেন্দ্রীয় TEMP_FILE_STORAGE ইম্পোর্ট করা হলো
from globals import TEMP_FILE_STORAGE
# 🚀 file_reader থেকে নতুন ফাংশন Import করা হলো
from services.file_reader import get_original_folder_path, open_folder_in_os 

open_bp = Blueprint("open", __name__)
logger = logging.getLogger("open_routes")

# ⚠️ দ্রষ্টব্য: এখানে স্থানীয় TEMP_FILE_STORAGE = {} সরিয়ে দেওয়া হয়েছে, 
# কারণ আমরা globals.py থেকে কেন্দ্রীয় স্টোরেজ ব্যবহার করছি।

# -------- Open in Browser (PDF Viewer functionality) --------
@open_bp.route("/open_browser", methods=["GET"])
def open_browser():
    file_id = request.args.get("file_id")
    # ⚠️ এখন কেন্দ্রীয় TEMP_FILE_STORAGE ব্যবহার করা হলো
    file_info = TEMP_FILE_STORAGE.get(file_id) 
    
    if not file_info:
        return jsonify({"status": "error", "message": "File not found or has expired."}), 404

    # We use io.BytesIO to treat the byte data as a file
    file_stream = io.BytesIO(file_info['data'])
    
    return send_file(
        file_stream,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=file_info['filename']
    )
    
@open_bp.route("/store_file_temp", methods=["POST"])
def store_file_temp():
    # এই রুটটি /upload_for_view দ্বারা প্রতিস্থাপিত হওয়া উচিত, তবে এটি কেন্দ্রীয় স্টোরেজ ব্যবহার করছে।
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        return jsonify({"status": "error", "message": "No file uploaded."}), 400
    
    try:
        file_content_bytes = uploaded_file.read()
        file_id = secrets.token_hex(16)
        
        # ⚠️ এখন কেন্দ্রীয় TEMP_FILE_STORAGE ব্যবহার করা হলো
        TEMP_FILE_STORAGE[file_id] = { 
            'data': file_content_bytes,
            'filename': uploaded_file.filename
            # 'original_path' এখানে প্রয়োজন নেই
        }
        
        uploaded_file.seek(0) 
        
        return jsonify({"status": "ok", "file_id": file_id})
    except Exception as e:
        logger.exception("Failed to store file temp.")
        return jsonify({"status": "error", "message": str(e)}), 500

# ------------------ 🚀 New Route for Open Folder ------------------
@open_bp.route("/open_folder/<file_id>", methods=["POST"])
def open_folder(file_id):
    
    # TEMP_FILE_STORAGE থেকে আসল ফোল্ডার পাথ বের করা
    folder_path = get_original_folder_path(file_id, TEMP_FILE_STORAGE)
    
    if not folder_path:
        return jsonify({"status": "error", "message": "Original folder path not found for this file. Please open the file once first."}), 404
        
    # ওপেন করার ফাংশন কল করা
    if open_folder_in_os(folder_path):
        return jsonify({"status": "ok", "message": f"Opening folder: {folder_path}"})
    else:
        return jsonify({"status": "error", "message": "Failed to execute OS command to open the folder. Check server logs."}), 500