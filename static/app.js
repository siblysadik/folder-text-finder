// static/app.js (FINAL CODE with Service Worker Registration)

// 🌟 PWA: Service Worker Registration যুক্ত করা হলো 🌟
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // service worker ফাইলটি static/sw.js এ আছে
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
            })
            .catch(error => {
                console.log('ServiceWorker registration failed: ', error);
            });
    });
}
// 🌟 PWA কোড শেষ 🌟


document.addEventListener('DOMContentLoaded', () => {
    const $ = s => document.querySelector(s);
    const $$ = s => document.querySelectorAll(s);

    const pickDirBtn = $('#pickDirBtn');
    const useFallbackBtn = $('#useFallbackBtn');
    const addFolderBtn = $('#addFolderBtn');
    const fallbackInput = $('#fallbackInput');
    const folderListContainer = $('#folderListContainer');
    const queryInput = $('#query');
    const searchBtn = $('#searchBtn');
    const tbody = $('#tbody');
    const statusEl = $('#status');
    // একক basePathInputGroup লুকানোর জন্য এটি অ্যাক্সেস করা হলো
    const singleBasePathInputGroup = $('#basePathInputGroup');

    // Key data structures
    let selectedFolderHandles = [];
    let pickedFiles = new Map();
    let pickedFilePaths = new Map(); // file.name -> root_folder/subfolder/file_name (relative path)
    let currentQuery = '';

    // 🚀 মূল ডেটা স্ট্রাকচার: প্রতিটি ফোল্ডারের জন্য Absolute Path সংরক্ষণ করার জন্য Map
    let folderBasePaths = new Map(); // folder_name (root_dir) -> absolute_path

    // Constants
    const MAX_FILE_SIZE = 64 * 1024 * 1024; // 64 MB ফাইল সাইজ লিমিট
    const DRIVE_PATTERN = /^[A-Za-z]:[\\\/]?$/;

    const supportedExtensions = new Set([
        '.pdf', '.docx', '.doc', '.py', '.js', '.java', '.class', '.cpp', '.cc',
        '.cxx', '.hpp', '.hxx', '.cs', '.ts', '.tsx', '.go', '.c', '.h', '.php',
        '.phtml', '.sql', '.rs', '.rb', '.swift', '.kt', '.kts', '.r', '.R',
        '.pl', '.pm', '.dart', '.scala', '.sc', '.vb', '.asm', '.s', '.html',
        '.htm', '.css', '.m', '.mat', '.sh', '.bash', '.cls', '.cbl', '.cob',
        '.fs', '.fsi', '.fsx', '.ps1', '.plsql', '.scm', '.ss', '.tsql', '.cr',
        '.pro', '.pl', '.vhd', '.vhdl', '.d', '.abap', '.txt', '.md', '.log',
        '.json', '.xml', '.yml', '.yaml', '.toml',
        // 🌟 নতুন যোগ: Excel ও CSV
        '.xlsx', '.xls', '.csv'
    ]);

    // 🌟 নতুন কনস্ট্যান্ট: যে ফাইলগুলো টেক্সট ভিউয়ার দিয়ে দেখা হবে
    const TEXT_VIEW_EXTENSIONS = new Set([
        '.docx', '.doc', '.xlsx', '.xls', '.csv'
    ]);

    // ------------------- UI and Selection Logic -------------------

    // একক Root Folder Path ইনপুট বক্সটি লুকিয়ে রাখছি
    if (singleBasePathInputGroup) {
        singleBasePathInputGroup.style.display = 'none';
        if (singleBasePathInputGroup.nextElementSibling && singleBasePathInputGroup.nextElementSibling.tagName === 'HR') {
             singleBasePathInputGroup.nextElementSibling.style.display = 'none';
        }
    }


    if ('showDirectoryPicker' in window) {
        pickDirBtn.style.display = 'inline-block';
        useFallbackBtn.style.display = 'inline-block';
        addFolderBtn.style.display = 'inline-block';

        pickDirBtn.addEventListener('click', async () => {
            pickedFiles.clear();
            pickedFilePaths.clear();
            selectedFolderHandles = [];
            folderListContainer.innerHTML = '';
            folderBasePaths.clear(); // Map পরিষ্কার করা হলো
            await handleFolderSelection();
        });

        addFolderBtn.addEventListener('click', async () => {
            await handleFolderSelection();
        });

        async function handleFolderSelection() {
            try {
                const dirHandle = await window.showDirectoryPicker();
                await addFolderToSelection(dirHandle);

            } catch (e) {
                if (e.name !== 'AbortError') {
                    console.error("Folder selection error:", e);
                    statusEl.textContent = 'Folder selection failed. Check console for details.';
                } else {
                    statusEl.textContent = 'Folder selection canceled.';
                }
            }
        }

    } else {
        // Fallback Mode
        pickDirBtn.style.display = 'none';
        useFallbackBtn.style.display = 'inline-block';
        addFolderBtn.style.display = 'none';

        useFallbackBtn.addEventListener('click', () => {
            fallbackInput.click();
        });

        fallbackInput.addEventListener('change', (e) => {
            if (e.target.files.length === 0) return;

            pickedFiles.clear();
            pickedFilePaths.clear();
            selectedFolderHandles = [];
            folderListContainer.innerHTML = '';
            folderBasePaths.clear();

            const { files, paths } = collectFilesFromFileList(e.target.files);

            files.forEach((file, name) => pickedFiles.set(name, file));
            paths.forEach((path, name) => pickedFilePaths.set(name, path));

            const inferredPath = pickedFilePaths.values().next().value || 'Selected Files';
            // ফোল্ডারের নাম বের করা
            const folderName = inferredPath.includes('/') ? inferredPath.split('/')[0] : inferredPath;

            selectedFolderHandles.push({ name: folderName, isFallback: true });
            reRenderFolderList();
            updateOverallStatus();

            // ফলব্যাক মোডে ম্যানুয়াল পাথ ইনপুট দরকার, তাই প্রথম বারের জন্য আমরা ইনপুটকে ফোকাস করব
            setTimeout(() => {
                const pathInput = document.querySelector(`input[data-folder-name="${folderName}"]`);
                if (pathInput) {
                    pathInput.focus();
                    statusEl.textContent = `Ready. Please enter the Absolute Path for the selected files.`;
                }
            }, 50);
        });
    }

    // Function to handle the selected directory
    async function addFolderToSelection(dirHandle) {
        const folderName = dirHandle.name;

        if (DRIVE_PATTERN.test(folderName)) {
            alert("Error: Selecting a drive root (e.g., C:, D:) is not supported. Please select one or more specific folders inside the drive.");
            return;
        }

        for (const existingHandle of selectedFolderHandles) {
            if (!existingHandle.isFallback && await existingHandle.isSameEntry(dirHandle)) {
                alert(`Error: Folder "${folderName}" has already been selected.`);
                return;
            }
        }

        statusEl.textContent = `Processing folder "${folderName}"...`;

        const { files, paths } = await collectFilesRecursively(dirHandle, folderName);

        files.forEach((file, name) => pickedFiles.set(name, file));
        paths.forEach((path, name) => pickedFilePaths.set(name, path));

        selectedFolderHandles.push(dirHandle);

        reRenderFolderList();
        updateOverallStatus();

        // ফোল্ডার যুক্ত হওয়ার পর নতুন ইনপুট ফিল্ডটি ফোকাস করা হলো
        setTimeout(() => {
            const pathInput = document.querySelector(`input[data-folder-name="${folderName}"]`);
            if (pathInput) {
                pathInput.focus();
                statusEl.textContent = `Ready. Please enter the Absolute Path for the folder: ${folderName}.`;
            }
        }, 50);
    }

    // Renders the list of all currently selected folders
    function reRenderFolderList() {
        folderListContainer.innerHTML = '';
        selectedFolderHandles.forEach((handle, index) => {
            const pathName = handle.isFallback ? handle.name : handle.name;

            let fileCount = 0;
            pickedFilePaths.forEach(path => {
                if (path.startsWith(pathName)) {
                    fileCount++;
                }
            });

            const div = document.createElement('div');
            div.className = 'selected-folder-item';
            div.dataset.folderPath = pathName;
            div.dataset.index = index;

            const currentBasePath = folderBasePaths.get(pathName) || '';
            const pathPlaceholder = (navigator.platform.includes('Win')) ? `C:\\Path\\To\\${pathName}` : `/home/user/${pathName}`;

            // HTML স্ট্রাকচার
            div.innerHTML = `
                <div class="folder-header">
                    <span class="folder-path-display">📁 ${pathName}</span>
                    <span class="file-count-display">(${fileCount} files)</span>
                    <button class="remove-folder-btn" title="Remove Folder">✕</button>
                </div>
                <div class="folder-basepath-input-group">
                    <label>${index + 1}. Enter Root Folder's ABSOLUTE Path:</label>
                    <input type="text"
                            class="basePathInput"
                            data-folder-name="${pathName}"
                            placeholder="${pathPlaceholder}"
                            value="${currentBasePath}">
                </div>
            `;

            const removeBtn = div.querySelector('.remove-folder-btn');
            removeBtn.addEventListener('click', () => removeFolderFromSelection(div, handle));

            // ইনপুট বক্সে কোনো পরিবর্তন হলে Map এ সেভ করা হচ্ছে
            const pathInput = div.querySelector('.basePathInput');
            pathInput.addEventListener('change', (e) => {
                // স্লাশ ঠিক করা হলো এবং Map এ সেভ করা হলো
                const newPath = e.target.value.trim().replace(/[\/\\]+$/, '').replace(/\\/g, '/');
                folderBasePaths.set(pathName, newPath);
            });

            folderListContainer.appendChild(div);
        });
    }


    // Function to remove a folder from the selection
    async function removeFolderFromSelection(el, handleToRemove) {

        const folderNameToRemove = el.dataset.folderPath;

        selectedFolderHandles = selectedFolderHandles.filter(h => h !== handleToRemove);
        folderBasePaths.delete(folderNameToRemove); // Map থেকে পাথ মুছে ফেলা হলো

        pickedFiles.clear();
        pickedFilePaths.clear();

        statusEl.textContent = 'Re-collecting files from remaining folders...';

        // ফাইল ও পাথ পুনরায় সংগ্রহ করা
        for (const handle of selectedFolderHandles) {
            if (handle.isFallback) {
                // Fallback Mode Handling
                const fileList = Array.from(fallbackInput.files);
                const { files, paths } = collectFilesFromFileList(fileList);
                files.forEach((file, name) => pickedFiles.set(name, file));
                paths.forEach((p, name) => pickedFilePaths.set(name, p));
                break;
            }
            const { files, paths } = await collectFilesRecursively(handle, handle.name);
            files.forEach((file, name) => pickedFiles.set(name, file));
            paths.forEach((p, name) => pickedFilePaths.set(name, p));
        }

        reRenderFolderList();
        updateOverallStatus();
    }

    // Updates the main status text
    function updateOverallStatus() {
        const totalFiles = pickedFiles.size;
        const totalFolders = selectedFolderHandles.length;
        if (totalFolders === 0) {
            statusEl.textContent = 'Ready. Select a folder to begin.';
            addFolderBtn.style.display = 'none';
            return;
        }
        statusEl.textContent = `Ready. ${totalFiles} file(s) across ${totalFolders} folder(s) ready for search.`;
        if ('showDirectoryPicker' in window) {
            addFolderBtn.style.display = 'inline-block';
        }
    }

    // ------------------- Search Logic -------------------

    if (searchBtn) {
        searchBtn.addEventListener('click', async () => {
            const query = queryInput.value.trim();

            if (!query) {
                alert('Please enter a search term.');
                return;
            }
            if (pickedFiles.size === 0) {
                alert('No files selected. Please select one or more folders first.');
                return;
            }

            // পাথ চেকিং: প্রতিটি ফোল্ডারের জন্য পাথ দেওয়া হয়েছে কিনা তা পরীক্ষা করুন
            let missingPath = false;
            for (const handle of selectedFolderHandles) {
                const folderName = handle.name;
                const basePath = folderBasePaths.get(folderName);
                if (!basePath || basePath.length < 3) {
                    alert(`Error: Please enter the Absolute Path for the folder: ${folderName}.`);
                    document.querySelector(`input[data-folder-name="${folderName}"]`).focus();
                    missingPath = true;
                    return;
                }
            }
            if (missingPath) return;

            statusEl.textContent = 'Uploading and searching...';
            tbody.innerHTML = '';
            currentQuery = query;

            const formData = new FormData();
            formData.append('q', query);
            formData.append('paths', JSON.stringify(Object.fromEntries(pickedFilePaths)));

            for (const [name, file] of pickedFiles) {
                formData.append('files', file, name);
            }

            try {
                const response = await fetch('/search_upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();

                if (data.status === 'ok') {
                    statusEl.textContent = `Found ${data.count} match(es) in ${selectedFolderHandles.length} folder(s).`;
                    displayResults(data.matches);
                } else {
                    statusEl.textContent = `Error: ${data.message}`;
                }
            } catch (error) {
                console.error('Search failed:', error);
                statusEl.textContent = `Search failed: ${error.message}. Try searching a smaller number of files.`;
            }
        });
    }

    // ------------------- Helper Functions (File Collection) -------------------

    async function collectFilesRecursively(dirHandle, parentPath = '') {
        const outFiles = new Map();
        const outPaths = new Map();

        for await (const entry of dirHandle.values()) {
            const path = `${parentPath}/${entry.name}`;

            if (entry.kind === 'file') {
                const fileExtension = entry.name.toLowerCase().substring(entry.name.lastIndexOf('.'));

                if (supportedExtensions.has(fileExtension) && !entry.name.startsWith('~$')) {
                    try {
                        const file = await entry.getFile();
                        if (file.size <= MAX_FILE_SIZE) {
                            outFiles.set(file.name, file);
                            outPaths.set(file.name, path);
                        }
                    } catch (e) {
                        console.warn(`Skipping file ${path}: Could not read file content.`);
                    }
                }
            } else if (entry.kind === 'directory') {
                const subDirResults = await collectFilesRecursively(entry, path);
                subDirResults.files.forEach((file, name) => outFiles.set(name, file));
                subDirResults.paths.forEach((p, name) => outPaths.set(name, p));
            }
        }
        return { files: outFiles, paths: outPaths };
    }

    function collectFilesFromFileList(fileList) {
        const outFiles = new Map();
        const outPaths = new Map();

        for (const file of fileList) {
            const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
            if (supportedExtensions.has(fileExtension) && !file.name.startsWith('~$') && file.size <= MAX_FILE_SIZE) {
                outFiles.set(file.name, file);
                outPaths.set(file.name, file.webkitRelativePath || file.name);
            }
        }
        return { files: outFiles, paths: outPaths };
    }


    // ------------------- Results Display Logic -------------------

    async function getFileId(fileToOpen, originalPath, match) {
        const formData = new FormData();
        formData.append('file', fileToOpen, match.file);

        // originalPath: root_folder/subfolder/file.ext (আপেক্ষিক পাথ)
        const pathSegments = originalPath.split(/[\/\\]/);
        const rootFolder = pathSegments[0]; // যেমন: 'Milton Data'

        const currentBasePhysicalPath = folderBasePaths.get(rootFolder);

        if (!currentBasePhysicalPath) {
            console.error(`Base Physical Path is missing for folder: ${rootFolder}.`);
            return null;
        }

        let absolutePath = currentBasePhysicalPath;

        // আপেক্ষিক পাথ থেকে রুট ফোল্ডারের নাম বাদ দেওয়া হলো
        let relativePath = originalPath;
        if (relativePath.startsWith(rootFolder)) {
            // root_folder সহ স্লাশটি বাদ দেওয়া হলো
            relativePath = relativePath.substring(rootFolder.length).replace(/^[\/\\]+/, '');
        }

        // সম্পূর্ণ পাথ তৈরি করা হলো: BasePath/subfolder/file.ext
        if (relativePath) {
             // BasePath/relativePath যুক্ত করা হলো এবং স্লাশ ঠিক করা হলো
             absolutePath = `${currentBasePhysicalPath}/${relativePath}`.replace(/\/\/+/g, '/');
        }

        // সার্ভারে পাঠানোর জন্য সকল স্লাশ ফরওয়ার্ড স্লাশ (/) এ পরিবর্তন করা হলো
        formData.append('original_path', absolutePath.replace(/\\/g, '/'));

        try {
            const response = await fetch('/upload_for_view', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.status === 'ok') {
                return data.file_id;
            } else {
                return null;
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            return null;
        }
    }


    function displayResults(matches) {
        tbody.innerHTML = '';
        matches.forEach(match => {
            const tr = document.createElement('tr');

            const pathTd = document.createElement('td');
            pathTd.textContent = match.path;
            pathTd.setAttribute('data-label', 'File Path'); 
            tr.appendChild(pathTd);

            const pageLineTd = document.createElement('td');
            let content = `Page: ${match.page}`;
            if (match.line) {
                content = `Line: ${match.line}`;
            }
            pageLineTd.innerHTML = content;
            pageLineTd.setAttribute('data-label', 'Page/Line'); 
            tr.appendChild(pageLineTd);

            const previewTd = document.createElement('td');
            previewTd.innerHTML = match.preview;
            previewTd.setAttribute('data-label', 'Preview (highlighted)'); 
            tr.appendChild(previewTd);

            const openTd = document.createElement('td');
            // 🚀 ফিক্স: বাটন দুটি পাশাপাশি দেখানোর জন্য Flexbox ব্যবহার করা হলো
            openTd.style.display = 'flex'; 
            openTd.style.gap = '10px'; // বাটন দুটির মাঝে সামান্য ফাঁকা স্থান
            openTd.setAttribute('data-label', 'Open Actions'); 

            // 1. Open File Button (Updated logic for all text-based files)
            const openFileBtn = document.createElement('button');
            openFileBtn.textContent = 'Open File';
            openFileBtn.onclick = async () => {
                const fileToOpen = pickedFiles.get(match.file);
                const originalPath = pickedFilePaths.get(match.file);

                if (!fileToOpen || !originalPath) {
                    alert('File not found in the selected files.');
                    return;
                }

                const fileId = await getFileId(fileToOpen, originalPath, match);

                if (fileId) {
                    const fileExtension = match.file.toLowerCase().substring(match.file.lastIndexOf('.'));

                    if (fileExtension === '.pdf') {
                        let viewerUrl = `/get_file/${fileId}`;
                        if (match.page && match.page !== "N/A") {
                            viewerUrl += `#page=${match.page}`;
                        }
                        window.open(viewerUrl, '_blank');
                    } else if (TEXT_VIEW_EXTENSIONS.has(fileExtension)) {
                        // 🌟 .docx, .doc, .xlsx, .xls, .csv কে টেক্সট ভিউয়ার রুটে পাঠানো হলো
                        const viewerUrl = `/view_text/${fileId}?q=${encodeURIComponent(currentQuery)}`;
                        window.open(viewerUrl, '_blank');
                    }
                    else {
                        // অন্যান্য সকল ফাইল (কোড/প্লেইন টেক্সট) এর জন্য বিদ্যমান /view_code/ রুটটি ব্যবহার করা হলো
                        const viewerUrl = `/view_code/${fileId}?q=${encodeURIComponent(currentQuery)}`;
                        window.open(viewerUrl, '_blank');
                    }
                } else {
                    alert('Failed to prepare file for viewing.');
                }
            };
            openTd.appendChild(openFileBtn);

            // 2. Open Folder Button (Updated logic)
            const openFolderBtn = document.createElement('button');
            openFolderBtn.textContent = 'Open Folder';
            // openFolderBtn.style.marginLeft = '10px'; 

            openFolderBtn.onclick = async () => {
                const fileToOpen = pickedFiles.get(match.file);
                const originalPath = pickedFilePaths.get(match.file);

                if (!fileToOpen || !originalPath) {
                    alert('File not found in the selected files.');
                    return;
                }

                const pathSegments = originalPath.split(/[\/\\]/);
                const rootFolder = pathSegments[0];

                // প্রতি ফোল্ডারের পাথ চেক করা হলো
                if (!folderBasePaths.get(rootFolder)) {
                    alert(`Error: Please enter the Absolute Path for the folder: ${rootFolder}.`);
                    document.querySelector(`input[data-folder-name="${rootFolder}"]`).focus();
                    return;
                }

                // প্রথমে ফাইল আপলোড করে file_id পেতে হবে
                const fileId = await getFileId(fileToOpen, originalPath, match);

                if (fileId) {
                    // এখন open_folder API কল করা হচ্ছে
                    const folderResponse = await fetch(`/open_folder/${fileId}`, {
                        method: 'POST'
                    });
                    const folderData = await folderResponse.json();

                    if (folderData.status === 'ok') {
                        console.log(`Open Folder success: ${folderData.message}`);
                    } else {
                        alert(`Failed to open folder on server: ${folderData.message}`);
                    }
                } else {
                    alert('Failed to prepare file for opening folder.');
                }
            };
            openTd.appendChild(openFolderBtn);

            tr.appendChild(openTd);
            tbody.appendChild(tr);
        });
    }

    // Initial status update
    updateOverallStatus();
});