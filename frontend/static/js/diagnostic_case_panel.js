document.addEventListener('DOMContentLoaded', () => {
    const fullImageContainer = document.getElementById('full-image-container');
    const fullImage = document.getElementById('full-image');
});

function showFullImage(imageData, imageFilename) {
    const fullImageContainer = document.getElementById('full-image-container');
    const fullImage = document.getElementById('full-image');
    const fullImageTitle = document.getElementById('full-image-title');
    const imagePreviewList = document.getElementById('image-preview-list'); // Get the item list

    // Set the image source and title
    fullImage.src = `data:image/png;base64,${imageData}`;
    fullImageTitle.textContent = imageFilename;

    // Show the full image container
    fullImageContainer.style.display = 'flex';

    // Hide the item list
    imagePreviewList.classList.add('hidden');

    // Reset transformations for the new image
    fullImage.style.transform = 'scale(1)';
    fullImage.style.transformOrigin = 'center center';

}

function hideFullImage() {
    const fullImageContainer = document.getElementById('full-image-container');
    const fullImage = document.getElementById('full-image');
    const imagePreviewList = document.getElementById('image-preview-list'); // Get the item list

    // Hide the container and reset the image
    fullImageContainer.style.display = 'none';
    fullImage.src = '';

    // Show the item list
    imagePreviewList.classList.remove('hidden');
}

function showGrid() {
    const fullImage = document.getElementById('full-image');
    const canvas = document.getElementById('grid-canvas');
    const fullImageTitle = document.getElementById('full-image-title').textContent;

    // Get the hidden grids data
    const gridsElement = document.getElementById(`'${fullImageTitle}'`);
    if (!gridsElement) {
        console.error('Grid data not found for the current image.');
        return;
    }

    const grids = JSON.parse(gridsElement.textContent);
    //console.log(grids)
    for(const grid of grids){
        console.log(grid)
    }
}

