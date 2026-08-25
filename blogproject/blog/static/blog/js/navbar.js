/**
 * Modern SaaS Navigation Profile Menu Component Handler
 */
document.addEventListener('DOMContentLoaded', () => {
    const profileToggle = document.getElementById('userProfileDropdown');
    
    if (profileToggle) {
        // Universal keyboard ESC close event fallback handling block
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                const openMenu = document.querySelector('.modern-nav-dropdown.show');
                if (openMenu) {
                    profileToggle.click(); // Programmatically shuts focus dropdown
                }
            }
        });
    }
});