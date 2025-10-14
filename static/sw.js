// static/sw.js
const CACHE_NAME = 'folder-text-finder-v1';

// ক্যাশ করার জন্য প্রয়োজনীয় ফাইলগুলোর তালিকা। 
// যেহেতু Render/Flask-এ static ফাইলগুলো /static/ বা সরাসরি রুট থেকে অ্যাক্সেস করা হয়, 
// তাই আমরা এখানে রিলেটিভ পাথ ব্যবহার করছি।
const urlsToCache = [
    '/',
    '/static/styles.css',
    '/static/app.js',
    '/static/manifest.json',
    // আপনার আইকনগুলিও ক্যাশ করা হলো (index.html এ ব্যবহৃত পাথ অনুযায়ী)
    '/static/icons/icon.png', 
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png'
];

// ইনস্টলেশন ইভেন্ট: ক্যাশে ফাইল যোগ করা
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Cache opened.');
                // সমস্ত প্রয়োজনীয় স্ট্যাটিক ফাইল ক্যাশ করা হচ্ছে
                return cache.addAll(urlsToCache);
            })
            .catch(err => {
                console.error('Service Worker: Failed to cache resources', err);
            })
    );
});

// অ্যাক্টিভেট ইভেন্ট: পুরোনো ক্যাশে পরিষ্কার করা
self.addEventListener('activate', (event) => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        console.log('Service Worker: Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// ফেচ ইভেন্ট: ক্যাশে-ফার্স্ট স্ট্র্যাটেজি (স্ট্যাটিক অ্যাসেটের জন্য)
self.addEventListener('fetch', (event) => {
    // শুধুমাত্র GET রিকোয়েস্ট এবং নন-এপিআই রিকোয়েস্ট ক্যাশ করবে
    if (event.request.method !== 'GET' || event.request.url.includes('/api/')) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // যদি ক্যাশে থাকে, ক্যাশ থেকে ফেরত দিন
                if (response) {
                    return response;
                }
                
                // না হলে, নেটওয়ার্ক থেকে আনুন
                return fetch(event.request).catch(error => {
                    console.log('Service Worker: Fetch failed; returning fallback if available.', error);
                    // এখানে আপনি একটি অফলাইন পেজ যুক্ত করতে পারেন যদি আপনি চান
                });
            }
        )
    );
});