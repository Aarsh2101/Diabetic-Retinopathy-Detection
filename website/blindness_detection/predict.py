def get_predicted_label_and_gradcam(image, last_conv_layer='layer4'):
    """ Get the predicted label and GradCAM image for the input image and model for the last_conv_layer"""
    import numpy as np
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
    model.load_state_dict(torch.load('/path/to/local/file Detection/ResNet50.pth', map_location=device))


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
    test_image_tensor = preprocess(image)
    original_image_tensor = original_image_preprocess(image)

    test_image_tensor = test_image_tensor.to(device)
    original_image_tensor = original_image_tensor.to(device)

    model.to(device)
    model.eval()

    cam_extractor = torchcam.methods.GradCAM(model, last_conv_layer)
    out = model(test_image_tensor.unsqueeze(0)) 
    predicted_class = int(np.round(out.cpu().detach().numpy()).astype(int).sum() - 1)
    cams = cam_extractor(predicted_class, out)

    mask = cams[0].squeeze(0)

    custom_cmap = plt.cm.colors.ListedColormap(['#218AE5', '#ACD3F5', '#FFFFFF', '#FFA5C0', '#FF1D62'])
    
    gradcam_image = torchcam.utils.overlay_mask(to_pil_image(original_image_tensor), to_pil_image(mask, mode='F'), alpha=0.0, colormap=custom_cmap)

    return predicted_class, gradcam_image