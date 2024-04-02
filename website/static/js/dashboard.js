// // Gradcam Transparency
// const gradcamTransparencyElement = document.querySelector("#gradcam_transparency");
// let gradcam_transparency = gradcamTransparencyElement.value;
// gradcamTransparencyElement.oninput = (e) => {
//     gradcam_transparency = e.target.value;
//     document.getElementById("gradcam_image").style.opacity = gradcam_transparency;
// };

// // Canvas Transparency
// const canvasTransparencyElement = document.querySelector("#canvas_transparency");
// let canvas_transparency = canvasTransparencyElement.value;
// canvasTransparencyElement.oninput = (e) => {
//     canvas_transparency = e.target.value;
//     document.getElementById("canvas_image").style.opacity = canvas_transparency;
// };

$(document).ready(function() {
    // Loop over each image container
    $('.image-container').each(function() {
        // Get the submission id from the data attribute
        var submissionId = $(this).data('submission-id');

        // Get the unique ids
        var gradcamImageId = "gradcam_image_" + submissionId;
        var canvasImageId = "canvas_image_" + submissionId;
        var gradcamTransparencyId = "gradcam_transparency_" + submissionId;
        var canvasTransparencyId = "canvas_transparency_" + submissionId;

        // Select the elements
        var gradcamImage = $("#" + gradcamImageId);
        var canvasImage = $("#" + canvasImageId);
        var gradcamTransparency = $("#" + gradcamTransparencyId);
        var canvasTransparency = $("#" + canvasTransparencyId);

        // Gradcam Transparency
        gradcamTransparency.on('input change', function() {
            gradcamImage.css('opacity', $(this).val());
        });

        // Canvas Transparency
        canvasTransparency.on('input change', function() {
            canvasImage.css('opacity', $(this).val());
        });
    });
});