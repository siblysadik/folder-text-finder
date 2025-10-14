# server.py

from flask import Flask, send_from_directory
from routes.search_routes import search_bp
from routes.open_routes import open_bp
from routes.view_routes import view_bp
import logging
from werkzeug import formparser
from werkzeug.wrappers import Request
import os
import shutil
import time
# 🚀 globals.py ফাইলটি ইম্পোর্ট করা হলো
from globals import TEMP_FILE_STORAGE, FILE_CLEANUP_HOURS 

# অতিরিক্ত মেমরি ব্যবহারের জন্য: formparser-এর ফাইল বাফারের সীমা বৃদ্ধি 
# 10 MB পর্যন্ত ছোট ফাইলগুলি মেমরিতে বাফার হবে
formparser.DEFAULT_MAX_SIZE = 512 * 1024 * 1024
formparser.PART_MAX_SIZE = 512 * 1024 * 1024

# ফর্ম ডেটার মেটাডেটা (যেমন ফাইলের নাম ও পাথ) বাফার আকার বৃদ্ধি।
Request.max_form_parts = 0 
formparser.DEFAULT_MAX_FORM_MEMORY_SIZE = 10 * 1024 * 1024 # 10 MB

# কনফিগারেশন: মোট আপলোড সাইজ 64 GB রাখা হলো
MAX_CONTENT_LENGTH = 64 * 1024 * 1024 * 1024

app = Flask(__name__, static_folder="static", static_url_path="")
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# 🌟 সার্ভার শুরুর আগে টেম্প ফোল্ডার পরিষ্কার করা
def cleanup_temp_files():
    """নির্দিষ্ট সময়ের চেয়ে পুরনো টেম্প ফাইলগুলি ডিলিট করে।"""
    now = time.time()
    cutoff = now - (FILE_CLEANUP_HOURS * 3600) # 1 ঘণ্টা আগে
    
    # 🌟 নিশ্চিত করুন যে ফোল্ডারটি আছে
    if not TEMP_FILE_STORAGE.exists():
        TEMP_FILE_STORAGE.mkdir(parents=True, exist_ok=True)
        return

    # 🌟 ফোল্ডারের ভেতরে ফাইল ডিলিট করা
    for item in TEMP_FILE_STORAGE.iterdir():
        try:
            # os.stat() ব্যবহার করে শেষ পরিবর্তনের সময় পাওয়া যায়
            if os.stat(item).st_mtime < cutoff:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    os.remove(item)
                logging.info(f"Cleaned up old file/dir: {item}")
        except Exception as e:
            logging.error(f"Error cleaning up {item}: {e}")

# Register blueprints
app.register_blueprint(search_bp)
app.register_blueprint(open_bp)
app.register_blueprint(view_bp)

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# 🌟 ডেপ্লয়মেন্টের সময় cleanup ফাংশনটি চালানো উচিত
cleanup_temp_files()

if __name__ == "__main__":
    app.run(port=5055, debug=False)