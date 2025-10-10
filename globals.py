# globals.py

# কেন্দ্রীয় ফাইল স্টোরেজ। এটি routes/view_routes.py এ ব্যবহৃত TEMP_FILE_STORAGE এর স্থান নেবে।
# এটি file_id -> {'data': bytes, 'filename': str, 'original_path': str} সংরক্ষণ করবে।
TEMP_FILE_STORAGE = {}