# globals.py (সংশোধিত)

import os
import tempfile
from pathlib import Path
import threading

# 🌟 ইন-মেমরি স্টোরেজ ডিকশনারি (ফাইল ডেটা এবং মেটাডেটা রাখার জন্য) 🌟
# এটি একটি সাধারণ Python ডিকশনারি।
FILE_STORAGE_DICT = {}

# 🌟 লক তৈরি করা হলো থ্রেড-সেফটির জন্য (একাধিক রিকোয়েস্ট একই সময়ে অ্যাক্সেস করতে পারে) 🌟
FILE_STORAGE_LOCK = threading.Lock()

# 🚀 অন-ডিস্ক টেম্পোরারি ফাইল স্টোরেজ পাথের জন্য (যদি ভবিষ্যতে লাগে) 🚀
# ক্লাউড এনভায়রনমেন্টে (Render) /tmp ফোল্ডার ব্যবহার করা হলো
TEMP_ROOT_DIR = Path(tempfile.gettempdir())

# টেম্পোরারি আপলোড ডিরেক্টরি
# বর্তমানে আমরা ইন-মেমরি স্টোরেজ ব্যবহার করছি, কিন্তু এই পাথটি রাখছি
# যদি ভবিষ্যতে ফাইল সাইজ বড় হয় এবং ডিস্কে সেভ করার প্রয়োজন হয়।
TEMP_DIR_PATH = TEMP_ROOT_DIR / "temp_finder_uploads"

# ফাইলটি আপলোড করার পর কতক্ষণ রাখা হবে (ঘণ্টা)
FILE_CLEANUP_HOURS = 1 

# নিশ্চিত করা হলো যে অন-ডিস্ক ডিরেক্টরি তৈরি আছে
try:
    TEMP_DIR_PATH.mkdir(parents=True, exist_ok=True)
except Exception as e:
    # লগিং বা এরর হ্যান্ডলিং যোগ করা যেতে পারে
    print(f"Error ensuring TEMP_DIR_PATH exists: {e}")