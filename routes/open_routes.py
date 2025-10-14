# routes/open_routes.py (আপডেট করা)

from flask import Blueprint, request, jsonify, send_file
import logging
import secrets 
import io 
import os
# 🚀 globals থেকে কেন্দ্রীয় FILE_STORAGE_DICT এবং Lock ইম্পোর্ট করা হলো
from globals import FILE_STORAGE_DICT, FILE_STORAGE_LOCK
# 🚀 file_reader থেকে নতুন ফাংশন Import করা হলো
from services.file_reader import get_original_folder_path, open_folder_in_os 

open_bp = Blueprint("open", __name__)
logger = logging.getLogger("open_routes")


# -------- Open in Browser (PDF Viewer functionality) --------
@open_bp.route("/open_browser", methods=["GET"])
def open_browser():
    file_id = request.args.get("file_id")
    
    with FILE_STORAGE_LOCK:
        # ⚠️ এখন কেন্দ্রীয় FILE_STORAGE_DICT ব্যবহার করা হলো
        file_info = FILE_STORAGE_DICT.get(file_id) 
    
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
        # এখানে secrets ব্যবহার না করে uuid ব্যবহার করা নিরাপদ (view_routes.py এর মতো)
        # কিন্তু সামঞ্জস্যের জন্য আপাতত secrets রাখা হলো।
        file_id = secrets.token_hex(16)
        
        with FILE_STORAGE_LOCK:
            # ⚠️ এখন কেন্দ্রীয় FILE_STORAGE_DICT ব্যবহার করা হলো
            FILE_STORAGE_DICT[file_id] = { 
                'data': file_content_bytes,
                'filename': uploaded_file.filename
                # 'original_path' এখানে প্রয়োজন নেই (যদিও view_routes এ যোগ করা হয়েছে)
            }
        
        uploaded_file.seek(0) 
        
        return jsonify({"status": "ok", "file_id": file_id})
    except Exception as e:
        logger.exception("Failed to store file temp.")
        return jsonify({"status": "error", "message": str(e)}), 500

# ------------------ 🚀 New Route for Open Folder ------------------
@open_bp.route("/open_folder/<file_id>", methods=["POST"])
def open_folder(file_id):
    
    with FILE_STORAGE_LOCK:
        # FILE_STORAGE_DICT থেকে আসল ফোল্ডার পাথ বের করা
        # get_original_folder_path ফাংশনটি globals.py থেকে dict-টি আর্গুমেন্ট হিসেবে নেয়।
        folder_path = get_original_folder_path(file_id, FILE_STORAGE_DICT)
    
    if not folder_path:
        return jsonify({"status": "error", "message": "Original folder path not found for this file. Please open the file once first."}), 404
        
    # ওপেন করার ফাংশন কল করা
    if open_folder_in_os(folder_path):
        return jsonify({"status": "ok", "message": f"Opening folder: {folder_path}"})
    else:
        # Note: open_folder_in_os শুধুমাত্র Local/Desktop পরিবেশে কাজ করবে। Render/Cloud-এ ব্যর্থ হবে।
        return jsonify({"status": "error", "message": "Failed to execute OS command to open the folder. (This functionality is only supported in a local environment). Check server logs."}), 500