// Show the full image when an image is clicked
function showFullImage(imageData, title) {
    // Hide the preview list
    document.getElementById('image-preview-list').style.display = 'none';

    // Show the full image container
    const fullImageContainer = document.getElementById('full-image-container');
    fullImageContainer.style.display = 'block';

    // Update the full image and title
    const fullImage = document.getElementById('full-image');
    fullImage.src = 'data:image/png;base64,' + imageData;

    const fullImageTitle = document.getElementById('full-image-title');
    fullImageTitle.textContent = title;

    // Reset zoom scale
    scale = 1;
    fullImage.style.transform = `scale(${scale})`;
}

// Hide the full image and return to the preview list
function hideFullImage() {
    // Hide the full image container
    document.getElementById('full-image-container').style.display = 'none';

    // Show the preview list
    document.getElementById('image-preview-list').style.display = 'block';
}

// Zoom functionality with scroll wheel
let scale = 1;
document.addEventListener('DOMContentLoaded', () => {
    const fullImage = document.getElementById('full-image');

    fullImage.addEventListener('wheel', function (event) {
        event.preventDefault();

        // Adjust scale based on scroll direction
        scale += event.deltaY * -0.01;

        // Limit the scale
        scale = Math.min(Math.max(1, scale), 10);

        // Apply the scale transform
        fullImage.style.transform = `scale(${scale})`;
    });
});
