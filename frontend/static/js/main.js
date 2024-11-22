// Fade out flash messages
window.addEventListener('DOMContentLoaded', (event) => {
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach((flash) => {
        setTimeout(() => {
            flash.style.transition = "opacity 1s ease-out";
            flash.style.opacity = "0";
        }, 3000); // Delay before fading (3 seconds)
        setTimeout(() => {
            flash.remove(); // Remove from DOM after fade-out
        }, 4000); // Delay for fade-out duration (4 seconds total)
    });
});
