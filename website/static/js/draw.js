let coord = {x:0 , y:0};  
function getPosition(event){ 
    const rect = canvas.getBoundingClientRect();
    coord.x = event.clientX - rect.left; 
    coord.y = event.clientY - rect.top; 
} 
    
const colorElement = document.getElementsByName("colorRadio");
let color;
colorElement.forEach((c) => {
    if (c.checked) color = c.value;
});

colorElement.forEach((c) => {
    c.onclick = () => {
        color = c.value;
    };
});

// Transparency
const transparencyElement = document.querySelector("#transparency");
let transparency = transparencyElement.value;
transparencyElement.oninput = (e) => {
    transparency = e.target.value;
    document.getElementById("shap_image").style.opacity = transparency;
};

function drawOnImage(image = null) {
    const canvasElement = document.getElementById("canvas");
    const context = canvasElement.getContext("2d");

    // Box size
    const boxSizeElement = document.querySelector("#blockSize");
    let gridSize = boxSizeElement.value;
    boxSizeElement.oninput = (e) => {
        gridSize = e.target.value;
    };

    // if an image is present,
    // the image passed as parameter is drawn in the canvas
    if (image) {
        const imageWidth = image.width;
        const imageHeight = image.height;

        // rescaling the canvas element
        canvasElement.width = imageWidth;
        canvasElement.height = imageHeight;
        // context.drawImage(image, 0, 0, imageWidth, imageHeight);
        context.globalAlpha = 0; // Change this value to adjust the transparency
        context.drawImage(image, 0, 0, imageWidth, imageHeight);
        context.globalAlpha = 1; // Reset the transparency to the default value
    }

    let isDrawing;

    canvasElement.onmousedown = (e) => {
        if (e.button === 0) { // Left mouse button clicked
            isDrawing = true;
            getPosition(e);
            drawGridBox(context, coord.x, coord.y, gridSize);
        }
        
        
    };

    canvasElement.onmousemove = (e) => {
        if (isDrawing && e.buttons === 1) {
            getPosition(e);
            drawGridBox(context, coord.x, coord.y, gridSize);
        }
    };

    canvasElement.onmouseup = function () {
        isDrawing = false;
    };

    canvasElement.addEventListener('contextmenu', function (e) {
        e.preventDefault(); // Prevent the default right-click menu
        getPosition(e);
        eraseGridBox(context, coord.x, coord.y, gridSize);
    });

    function drawGridBox(ctx, x, y, size) {
        const gridX = Math.floor(x / size) * size;
        const gridY = Math.floor(y / size) * size;
        ctx.fillStyle = color;
        ctx.fillRect(gridX, gridY, size, size);
    }

    function eraseGridBox(ctx, x, y, size) {
        const gridX = Math.floor(x / size) * size;
        const gridY = Math.floor(y / size) * size;
        ctx.clearRect(gridX, gridY, size, size);
    }
}

document.getElementById("getCanvasImage").addEventListener("click", function() {
    const canvasElement = document.getElementById("canvas");
    const imageDataUrl = canvasElement.toDataURL(); // Convert canvas to data URL
    fetch('/save_canvas_image', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val(),
        },
        body: JSON.stringify({imageDataUrl: imageDataUrl})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Image uploaded successfully');
        } else {
            console.error('Failed to upload image');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

$(document).ready(function() {
    let image = document.getElementById("original_image");
    if (image.complete) {
        console.log('Image already loaded');
        drawOnImage(image);
    } else {
        image.onload = () => {
            console.log('Image loaded');
            drawOnImage(image);
        };
    }
});