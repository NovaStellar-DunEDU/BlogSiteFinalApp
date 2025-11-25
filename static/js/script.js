document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('fileInput');
    const previewContainer = document.getElementById('previewContainer');

    if (fileInput && previewContainer) {
        fileInput.addEventListener('change', function (event) {
        previewContainer.innerHTML = '';
        const files = event.target.files;

        for (const file of files) {
            if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function (e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.style.maxWidth = '150px';
                img.style.margin = '10px';
                previewContainer.appendChild(img);
            };
            reader.readAsDataURL(file);
        }
    }
    });
}
});
