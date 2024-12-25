document.addEventListener('DOMContentLoaded', () => {
    const fullImageContainer = document.getElementById('full-image-container');
    const fullImage = document.getElementById('full-image');
});

// Function to display the full image
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

    // Adjust the grid overlay after the image is loaded
    fullImage.onload = adjustGridOverlay;
}

// Function to hide the full image view
function hideFullImage() {
    const fullImageContainer = document.getElementById('full-image-container');
    const fullImage = document.getElementById('full-image');
    const imagePreviewList = document.getElementById('image-preview-list'); // Get the item list
    const svgOverlay = document.getElementById('grid-overlay');

    // Hide the container and reset the image
    fullImageContainer.style.display = 'none';
    fullImage.src = '';

    // Show the item list
    imagePreviewList.classList.remove('hidden');
    svgOverlay.innerHTML = '';
}

// Function to dynamically adjust the grid overlay
function adjustGridOverlay() {
    const fullImage = document.getElementById('full-image');
    const svgOverlay = document.getElementById('grid-overlay');

    const imageWidth = fullImage.clientWidth;
    const imageHeight = fullImage.clientHeight;

    // Update the SVG viewBox to match the image dimensions
    svgOverlay.setAttribute('viewBox', `0 0 ${imageWidth} ${imageHeight}`);
    svgOverlay.style.width = `${imageWidth}px`;
    svgOverlay.style.height = `${imageHeight}px`;
}

// Call adjustGridOverlay whenever the window resizes
window.addEventListener('resize', () => {
    const fullImageContainer = document.getElementById('full-image-container');
    const fullImage = document.getElementById('full-image');
    const svgOverlay = document.getElementById('grid-overlay');

    // Only adjust the grid if the full image container is visible
    if (fullImageContainer && fullImageContainer.style.display === 'flex' && svgOverlay) {
        adjustGridOverlay();
    }
});


// Function to create and show the grid overlay
function showGrid() {
    const fullImage = document.getElementById('full-image');
    const fullImageTitle = document.getElementById('full-image-title').textContent;

    // Get the hidden grids data
    const gridsElement = document.getElementById(`'${fullImageTitle}'`);
    if (!gridsElement) {
        console.error('Grid data not found for the current image.');
        return;
    }

    const gridsList = JSON.parse(gridsElement.textContent);
    const svgOverlay = document.getElementById('grid-overlay');

    // Clear existing SVG grid
    svgOverlay.innerHTML = '';

    const scaleX = svgOverlay.clientWidth / fullImage.naturalWidth;
    const scaleY = svgOverlay.clientHeight / fullImage.naturalHeight;

    // Iterate through each grid JSON in the list
    gridsList.forEach(grids => {
        // Add horizontal segments
        grids.horizontal_segments.forEach(segment => {
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", segment.x_start * scaleX);
            line.setAttribute("y1", segment.y_start * scaleY);
            line.setAttribute("x2", segment.x_end * scaleX);
            line.setAttribute("y2", segment.y_end * scaleY);
            line.setAttribute("stroke", "blue");
            line.setAttribute("stroke-width", "2");
            line.setAttribute("class", "grid-line");
            line.dataset.info = `${segment.id}`;

            // Add click event listener
            line.addEventListener('click', (event) => {
                console.log(`Clicked on horizontal segment: ${event.target.dataset.info}`);
            });

            svgOverlay.appendChild(line);
        });

        // Add vertical segments
        grids.vertical_segments.forEach(segment => {
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", segment.x_start * scaleX);
            line.setAttribute("y1", segment.y_start * scaleY);
            line.setAttribute("x2", segment.x_end * scaleX);
            line.setAttribute("y2", segment.y_end * scaleY);
            line.setAttribute("stroke", "green");
            line.setAttribute("stroke-width", "2");
            line.setAttribute("class", "grid-line");
            line.dataset.info = `${segment.id}`;

            // Add click event listener
            line.addEventListener('click', (event) => {
                console.log(`Clicked on vertical segment: ${event.target.dataset.info}`);
            });

            svgOverlay.appendChild(line);
        });
    });


    // Ensure the SVG overlay is visible
    svgOverlay.style.display = 'block';
}
