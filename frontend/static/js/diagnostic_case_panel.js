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
    const gridButton = document.getElementById('grid-button');

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
    gridButton.textContent = 'Show Grid'
}

// Function to hide the full image view
function hideFullImage() {
    const fullImageContainer = document.getElementById('full-image-container');
    const fullImage = document.getElementById('full-image');
    const imagePreviewList = document.getElementById('image-preview-list'); // Get the item list
    const svgOverlay = document.getElementById('grid-overlay');
    const gridButton = document.getElementById('grid-button');

    // Hide the container and reset the image
    fullImageContainer.style.display = 'none';
    fullImage.src = '';

    // Show the item list
    imagePreviewList.classList.remove('hidden');
    svgOverlay.innerHTML = '';
    gridButton.textContent = 'Show Grid'
}

// Function to dynamically adjust the grid overlay
function adjustGridOverlay() {
    const fullImage = document.getElementById('full-image');
    const svgOverlay = document.getElementById('grid-overlay');
    const boxsvgOverlay = document.getElementById('box-overlay');

    const imageWidth = fullImage.clientWidth;
    const imageHeight = fullImage.clientHeight;

    // Update the SVG viewBox to match the image dimensions
    svgOverlay.setAttribute('viewBox', `0 0 ${imageWidth} ${imageHeight}`);
    svgOverlay.style.width = `${imageWidth}px`;
    svgOverlay.style.height = `${imageHeight}px`;

    boxsvgOverlay.setAttribute('viewBox', `0 0 ${imageWidth} ${imageHeight}`);
    boxsvgOverlay.style.width = `${imageWidth}px`;
    boxsvgOverlay.style.height = `${imageHeight}px`;
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
    const gridButton = document.getElementById('grid-button');
    const svgOverlay = document.getElementById('grid-overlay');

    if(gridButton.textContent != "Show Grid"){
        svgOverlay.innerHTML = '';
        gridButton.textContent = 'Show Grid'
        return;
    }
    // Get the hidden grids data
    const gridsElement = document.getElementById(`'${fullImageTitle}'`);
    if (!gridsElement) {
        console.error('Grid data not found for the current image.');
        return;
    }

    const gridsList = JSON.parse(gridsElement.textContent);

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
    gridButton.textContent = 'Hide Grid'
}

// Function to create and show the grid overlay
function showBoxes() {
    const fullImage = document.getElementById('full-image');
    const fullImageTitle = document.getElementById('full-image-title').textContent;
    const boxButton = document.getElementById('box-button');
    const svgOverlay = document.getElementById('box-overlay');

    if (boxButton.textContent !== "Show Tissue Boxes") {
        svgOverlay.innerHTML = '';
        boxButton.textContent = 'Show Tissue Boxes';
        return;
    }

    // Get the hidden grids data
    const gridsElement = document.getElementById(`'${fullImageTitle}'`);
    if (!gridsElement) {
        console.error('Grid data not found for the current image.');
        return;
    }

    const gridsList = JSON.parse(gridsElement.textContent);

    // Clear existing SVG grid
    svgOverlay.innerHTML = '';

    const scaleX = svgOverlay.clientWidth / fullImage.naturalWidth;
    const scaleY = svgOverlay.clientHeight / fullImage.naturalHeight;

    // Iterate through each grid JSON in the list
    gridsList.forEach(grids => {
        const boundingBox = grids.metadata.bounding_box; // Assuming bounding_box is an array [x1, y1, x2, y2]
        if (!boundingBox || boundingBox.length !== 4) {
            console.error('Invalid bounding box data:', boundingBox);
            return;
        }

        // Calculate attributes for the rectangle
        const [x1, y1, x2, y2] = boundingBox;
        const x = Math.min(x1, x2) * scaleX; // Top-left X
        const y = Math.min(y1, y2) * scaleY; // Top-left Y
        const width = Math.abs(x2 - x1) * scaleX; // Width
        const height = Math.abs(y2 - y1) * scaleY; // Height

        // Create an SVG rectangle
        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", width);
        rect.setAttribute("height", height);
        rect.setAttribute("fill", "none"); // Transparent fill
        rect.setAttribute("stroke", "red"); // Border color
        rect.setAttribute("stroke-width", "2");
        rect.setAttribute("class", "bounding-box");

        // Append the rectangle to the SVG overlay
        svgOverlay.appendChild(rect);
    });

    // Ensure the SVG overlay is visible
    svgOverlay.style.display = 'block';
    boxButton.textContent = 'Hide Tissue Boxes';
}

