def get_cropped_image(image):
    import numpy as np
    from PIL import Image
    import cv2
    # Convert the image to a numpy array and then to grayscale
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Apply a binary threshold to get a binary image
    _, binary = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

   # Check if contours list is not empty
    if contours:
        # Find the largest contour which should be the fundus
        largest_contour = max(contours, key=cv2.contourArea)

        # Get the bounding rectangle for the largest contour
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Crop the image to the bounding rectangle
        cropped = image.crop((x, y, x+w, y+h))
    else:
        print(f"No contours found in image")
        cropped = image 

        cropped = Image.fromarray(cropped)

    return cropped

def preprocess_image(image, size=(224, 224)):
    import numpy as np
    from PIL import Image
    import cv2
    
    # Resize the cropped image to the desired size
    cropped = image.resize(size, Image.Resampling.LANCZOS)

    # # Color normalization
    # mean = np.mean(cropped, axis=(0, 1))
    # image_normalized = cropped - mean

    # Illumination correction and contrast enhancement using CLAHE
    image_lab = cv2.cvtColor(np.uint8(cropped), cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(image_lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l)
    image_clahe = cv2.merge((l_clahe, a, b))
    image_clahe_rgb = cv2.cvtColor(image_clahe, cv2.COLOR_LAB2RGB)


    # Convert the image to uint8 before applying Gaussian blur
    image_clahe_rgb_uint8 = (image_clahe_rgb * 255).astype(np.uint8)

    # Apply Gaussian blur
    image_denoised = cv2.GaussianBlur(image_clahe_rgb_uint8, (5, 5), 0.5)

    image_denoised = Image.fromarray(image_denoised)
    return image_denoised


def get_predicted_label_and_gradcam(image, last_conv_layer='layer4'):
    """ Get the predicted label and GradCAM image for the input image and model for the last_conv_layer"""
    import numpy as np
    from PIL import Image, ImageOps
    import cv2
    import torch
    from torch.utils.data import Dataset, DataLoader
    from torchvision.transforms import v2
    import torch.nn as nn
    from torchvision import models
    from torchvision.transforms.functional import to_pil_image
    import torchcam
    import matplotlib.pyplot as plt
    
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    
    # Load the model and set the last layer to have 5 output classes
    model = models.resnet50(weights='ResNet50_Weights.DEFAULT')
    num_classes = 5 # Number of predicted classes
    model.fc = nn.Sequential(
        nn.Linear(model.fc.in_features, num_classes),
        nn.Sigmoid()
    )
    model.load_state_dict(torch.load('website/blindness_detection/DDRresnet50.pth', map_location=device))


    preprocess = v2.Compose([
    v2.Resize((224, 224)),
    v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)]),
    v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    original_image_preprocess = v2.Compose([
        v2.Resize((224, 224)),
        v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True)]),
    ])

    image = image.convert("RGB")
    cropped_image = get_cropped_image(image)
    preprocessed_image = preprocess_image(cropped_image)
    test_image_tensor = preprocess(preprocessed_image)
    original_image_tensor = original_image_preprocess(preprocessed_image)

    test_image_tensor = test_image_tensor.to(device)
    original_image_tensor = original_image_tensor.to(device)

    model.to(device)
    model.eval()

    cam_extractor = torchcam.methods.GradCAM(model, last_conv_layer)
    out = model(test_image_tensor.unsqueeze(0)) 
    predicted_class = int(np.round(out.cpu().detach().numpy()).astype(int).sum() - 1)
    cams = cam_extractor(predicted_class, out)

    mask = cams[0].squeeze(0)
    mask_range = {'min': mask.min().cpu(), 'max': mask.max().cpu()}
    custom_cmap = plt.cm.colors.ListedColormap(['#218AE5', '#ACD3F5', '#FFFFFF', '#FFA5C0', '#FF1D62'])

    gradcam_image = torchcam.utils.overlay_mask(to_pil_image(original_image_tensor), to_pil_image(mask, mode='F'), alpha=0.0, colormap=custom_cmap)
    # print(mask.max(), mask.min())
    return cropped_image, predicted_class, gradcam_image, mask_range