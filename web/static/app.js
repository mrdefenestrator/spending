function updateActiveTab() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('[role="tab"]').forEach(tab => {
        const isActive = tab.getAttribute('href') === currentPath;
        tab.classList.toggle('border-blue-500', isActive);
        tab.classList.toggle('text-blue-600', isActive);
        tab.classList.toggle('border-transparent', !isActive);
        tab.classList.toggle('text-gray-500', !isActive);
    });
}

document.addEventListener('htmx:afterSettle', updateActiveTab);
document.addEventListener('htmx:pushedIntoHistory', updateActiveTab);

function detectAccount(file) {
    const formData = new FormData();
    formData.append('files', file);
    fetch('/import/detect-account', { method: 'POST', body: formData })
        .then(r => {
            if (!r.ok) throw new Error(`detect-account failed: ${r.status}`);
            return r.text();
        })
        .then(html => {
            const panel = document.getElementById('account-panel');
            if (panel) {
                panel.outerHTML = html;
                htmx.process(document.body);
            }
        })
        .catch(err => {
            console.error('Account detection failed, continuing without pre-fill:', err);
        });
}

function initDropzone() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('border-blue-400', 'bg-blue-50');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('border-blue-400', 'bg-blue-50');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-blue-400', 'bg-blue-50');
        fileInput.files = e.dataTransfer.files;
        updateFileList();
        if (fileInput.files.length > 0) {
            detectAccount(fileInput.files[0]);
        }
    });

    fileInput.addEventListener('change', function () {
        updateFileList();
        if (fileInput.files.length > 0) {
            detectAccount(fileInput.files[0]);
        }
    });

    function updateFileList() {
        const files = fileInput.files;
        if (files.length === 0) {
            fileList.innerHTML = '';
            return;
        }
        const names = Array.from(files).map(f => f.name).join(', ');
        fileList.textContent = `Selected: ${names}`;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    initDropzone();

    // Select all checkbox
    document.addEventListener('change', function (e) {
        if (e.target.id === 'select-all') {
            const checkboxes = document.querySelectorAll('input[name="txn_ids"]');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
        }
    });
});

// Re-init after HTMX swaps content (DOMContentLoaded only fires once)
document.addEventListener('htmx:afterSettle', initDropzone);
