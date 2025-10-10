# server.py

from flask import Flask, send_from_directory
from routes.search_routes import search_bp
from routes.open_routes import open_bp
from routes.view_routes import view_bp
import logging
from werkzeug import formparser
from werkzeug.wrappers import Request
# 🚀 globals.py ফাইলটি ইম্পোর্ট করা হলো
from globals import TEMP_FILE_STORAGE

# অতিরিক্ত মেমরি ব্যবহারের জন্য: formparser-এর ফাইল বাফারের সীমা বৃদ্ধি 
# 10 MB পর্যন্ত ছোট ফাইলগুলি মেমরিতে বাফার হবে
formparser.DEFAULT_MAX_SIZE = 512 * 1024 * 1024
formparser.PART_MAX_SIZE = 512 * 1024 * 1024

# ফর্ম ডেটার মেটাডেটা (যেমন ফাইলের নাম ও পাথ) বাফার আকার বৃদ্ধি।
# ডিফল্ট 500KB. ড্রাইভ থেকে হাজার হাজার ফাইল সিলেক্ট করলে এটি অতিক্রম করে।
# এটিকে 10MB তে বাড়ানো হলো।
# Request.max_form_parts = None এর পরিবর্তে 0 ব্যবহার করা হলো, যা সীমাহীন বোঝায়।
Request.max_form_parts = 0 
formparser.DEFAULT_MAX_FORM_MEMORY_SIZE = 10 * 1024 * 1024 # 10 MB

# কনফিগারেশন: মোট আপলোড সাইজ 64 GB রাখা হলো
MAX_CONTENT_LENGTH = 64 * 1024 * 1024 * 1024

app = Flask(__name__, static_folder="static", static_url_path="")
# MAX_CONTENT_LENGTH কনফিগারেশনটি এখানে যোগ করা হলো
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Register blueprints
app.register_blueprint(search_bp)
app.register_blueprint(open_bp)
app.register_blueprint(view_bp)

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(port=5055, debug=False)