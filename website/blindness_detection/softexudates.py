def get_softexudates(image):
    import cv2
    import numpy as np
    
    image = np.array(image)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    
    contrast_enhanced_image = clahe.apply(gray_image)
    
    blurred_image = cv2.GaussianBlur(contrast_enhanced_image, (9, 9), 0)
    
    _, binary_image = cv2.threshold(blurred_image, 103.5, 255, cv2.THRESH_BINARY)
    
    mask = np.ones(binary_image.shape[:2], dtype="uint8") * 255


    contours, _ = cv2.findContours(binary_image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 140 or area > 20000:
            cv2.drawContours(mask, [cnt], -1, 0, -1)
    final_image = cv2.bitwise_and(binary_image, binary_image, mask=mask)
    return final_image