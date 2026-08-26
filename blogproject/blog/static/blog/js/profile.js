/**
 * Profile Edit Page Client-Side Functionality
 * Handles live image file preview.
 */

document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('profile-picture-input');
    const avatarPreview = document.getElementById('avatar-preview');

    if (fileInput && avatarPreview) {
        fileInput.addEventListener('change', function (event) {
            const file = event.target.files[0];
            if (file) {
                if (!file.type.startsWith('image/')) {
                    alert('Please select a valid image file.');
                    fileInput.value = '';
                    return;
                }

                const reader = new FileReader();
                reader.onload = function (e) {
                    avatarPreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }
});