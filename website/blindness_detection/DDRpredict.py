from PIL import Image, ImageOps
import numpy as np
import cv2
import torch
from torchvision.transforms import v2
import torch.nn as nn
from torchvision import models
from torchvision.transforms.functional import to_pil_image
import torchcam
from torch.nn.parameter import Parameter
import torch.nn.functional as F
import matplotlib.pyplot as plt
import os
from pathlib import Path

def get_cropped_image(image):
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

def preprocess_image(cropped_image, size=(224, 224)):
    
    # Resize the cropped image to the desired size
    cropped = cropped_image.resize(size, Image.Resampling.LANCZOS)

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

def gem(x, p=3, eps=1e-6):
    return F.avg_pool2d(x.clamp(min=eps).pow(p), (x.size(-2), x.size(-1))).pow(1./p)
class GeM(nn.Module):
    def __init__(self, p=3, eps=1e-6):
        super(GeM,self).__init__()
        self.p = Parameter(torch.ones(1)*p)
        self.eps = eps
    def forward(self, x):
        return gem(x, p=self.p, eps=self.eps)       
    def __repr__(self):
        return self.__class__.__name__ + '(' + 'p=' + '{:.4f}'.format(self.p.data.tolist()[0]) + ', ' + 'eps=' + str(self.eps) + ')'


def get_predicted_label_and_gradcam(image, last_conv_layer='layer4'):
    """ Get the predicted label and GradCAM image for the input image and model for the last_conv_layer"""
    
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    
    # Load the model and set the last layer to have 5 output classes
    model = models.resnet50(weights='ResNet50_Weights.DEFAULT')
    num_classes = 5 # Number of predicted classes
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model.avgpool = GeM()

    default_model_path = Path(__file__).with_name('DDRresnet50_best_acc final.pth')
    model_path = Path(os.environ.get('DR_MODEL_PATH', default_model_path))
    if not model_path.is_file():
        raise FileNotFoundError(
            f'Model checkpoint not found at {model_path}. '
            'Set DR_MODEL_PATH to the ResNet-50 checkpoint location.'
        )
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

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

    cam_extractor = torchcam.methods.GradCAM(model, last_conv_layer)
    out = model(test_image_tensor.unsqueeze(0)) 
    predicted_class = out.cpu().detach().numpy().argmax(axis=1)[0]
    cams = cam_extractor([predicted_class], out)

    mask = cams[0].squeeze(0)
    mask_range = {'min': mask.min().cpu(), 'max': mask.max().cpu()}
    custom_cmap = plt.cm.colors.ListedColormap(['#218AE5', '#FFFFFF', '#FF1D62'])

    gradcam_image = torchcam.utils.overlay_mask(to_pil_image(original_image_tensor), to_pil_image(mask, mode='F'), alpha=0.0)

    return cropped_image, predicted_class, gradcam_image, mask_range