// Theme Toggle Logic
const themeToggleBtn = document.getElementById('theme-toggle');

if (themeToggleBtn) {
    // Update theme toggle icon based on current state
    updateThemeIcon();

    themeToggleBtn.addEventListener('click', () => {
        const isDarkMode = document.documentElement.classList.toggle('dark-mode');
        localStorage.setItem('dark-mode', isDarkMode);
        updateThemeIcon();
    });
}

function updateThemeIcon() {
    const icon = themeToggleBtn.querySelector('i');
    if (document.documentElement.classList.contains('dark-mode')) {
        icon.className = 'fa-solid fa-sun';
    } else {
        icon.className = 'fa-solid fa-moon';
    }
}

// Automatically dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', () => {
    const flashes = document.querySelectorAll('.flash-message');
    flashes.forEach(flash => {
        setTimeout(() => {
            // Check if still exists
            if (flash.parentElement) {
                flash.style.opacity = '0';
                flash.style.transform = 'translateY(-8px)';
                flash.style.transition = 'all 0.5s ease';
                setTimeout(() => flash.remove(), 500);
            }
        }, 5000);
    });
});
