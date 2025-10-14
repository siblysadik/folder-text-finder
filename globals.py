# globals.py

import os
import tempfile
from pathlib import Path

# 🌟 Render/Cloud-এর জন্য /tmp ফোল্ডার ব্যবহার করা হলো 🌟
# TEMP_FILE_STORAGE: /tmp/temp_uploads
# ক্লাউড এনভায়রনমেন্টে আমরা অস্থায়ীভাবে ডেটা সংরক্ষণের জন্য /tmp ব্যবহার করি
TEMP_DIR = Path(tempfile.gettempdir())
TEMP_FILE_STORAGE = TEMP_DIR / "temp_uploads"
TEMP_FILE_STORAGE.mkdir(parents=True, exist_ok=True) # ফোল্ডারটি নিশ্চিতভাবে তৈরি করা হলো

# ফাইলটি আপলোড করার পর কতক্ষণ রাখা হবে (ঘণ্টা)
FILE_CLEANUP_HOURS = 1