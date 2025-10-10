# routes/search_routes.py

import os
import json
from flask import Blueprint, request, jsonify
from services.file_reader import search_file_content
import logging

search_bp = Blueprint('search', __name__)
logger = logging.getLogger("search_routes")

UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@search_bp.route("/search_upload", methods=["POST"])
def search_upload():
    try:
        query = request.form.get("q", "").strip()
        if not query:
            return jsonify({"status": "error", "message": "Missing 'q' parameter."}), 400

        uploaded_files = request.files.getlist("files")
        if not uploaded_files:
            return jsonify({"status": "error", "message": "No files uploaded."}), 400

        file_paths_json = request.form.get("paths", "{}")
        file_paths = json.loads(file_paths_json)
        
        all_matches = []
        total_count = 0
        
        for file in uploaded_files:
            file_name = file.filename
            file_path = file_paths.get(file_name, file_name)
            
            # Reset file pointer to the beginning before processing
            file.seek(0)
            
            item = {
                'file_obj': file,
                'file_name': file_name,
                'file_path': file_path,
            }
            
            result, status_code = search_file_content(item, query, UPLOAD_FOLDER)
            
            if status_code == 200:
                all_matches.extend(result['matches'])
                total_count += result['count']
            else:
                # If a file fails to process, log it but continue with other files
                logger.error(f"Failed to process file {file_name}: {result['message']}")
        
        return jsonify({"status": "ok", "matches": all_matches, "count": total_count}), 200

    except Exception as e:
        logger.exception("An error occurred during file upload search.")
        return jsonify({"status": "error", "message": "An internal server error occurred."}), 500