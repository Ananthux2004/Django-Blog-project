document.addEventListener("DOMContentLoaded", function() {
    // Dynamic Placeholder Injection Engine
    document.querySelectorAll('.auth-form-group input').forEach(input => {
        const name = input.name.toLowerCase();
        const id = input.id.toLowerCase();
        
        if (name.includes('email')) {
            input.placeholder = 'Email';
        } else if (name.includes('username')) {
            input.placeholder = 'Email'; 
        } else if (name.includes('password')) {
            // Evaluates string checks to separate primary password inputs from confirmation rows
            if (name.includes('confirm') || name.includes('2') || id.includes('confirm')) {
                input.placeholder = 'Confirm password';
            } else if (name.includes('create') || id.includes('create')) {
                input.placeholder = 'Create password';
            } else if (name.includes('new') || id.includes('new')) {
                input.placeholder = 'New password';
            } else {
                input.placeholder = 'Password';
            }
        }
    });
});

// 2D Vector Password Visibility Engine
function togglePasswordVisibility(fieldId, buttonElement) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    
    const isPassword = field.type === "password";
    field.type = isPassword ? "text" : "password";
    
    const eyeOpen = buttonElement.querySelector('.eye-open');
    const eyeClosed = buttonElement.querySelector('.eye-closed');
    
    if (isPassword) {
        eyeOpen.classList.add('d-none');
        eyeClosed.classList.remove('d-none');
    } else {
        eyeOpen.classList.remove('d-none');
        eyeClosed.classList.add('d-none');
    }
}