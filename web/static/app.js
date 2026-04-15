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

document.addEventListener('DOMContentLoaded', function() {
    // Drag and drop
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');

    if (dropzone && fileInput) {
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
        });

        fileInput.addEventListener('change', updateFileList);

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

    // Select all checkbox
    document.addEventListener('change', function(e) {
        if (e.target.id === 'select-all') {
            const checkboxes = document.querySelectorAll('input[name="txn_ids"]');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
        }
    });
});
