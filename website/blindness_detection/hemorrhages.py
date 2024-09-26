def get_hemorrhages(image):
    import numpy as np
    import cv2
    import os

    image = np.array(image)
    gray  = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    b,g,r = cv2.split(image)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_enhanced = clahe.apply(g)

    # Pipeline 1 - ksize 81
    img_medf = cv2.medianBlur(img_enhanced,81)
    img_sub = cv2.subtract(img_medf,img_enhanced)
    img_subf = cv2.blur(img_sub,(5,5))
    ret, img_darkf = cv2.threshold(img_subf, 10, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2,2))
    img_darkl = cv2.morphologyEx(img_darkf,cv2.MORPH_OPEN,kernel)

    # Pipeline 2 - ksize 131
    img_medf1 = cv2.medianBlur(img_enhanced,131)
    img_sub1 = cv2.subtract(img_medf1,img_enhanced)
    img_subf1 = cv2.blur(img_sub1,(5,5))
    ret, img_darkf1 = cv2.threshold(img_subf1, 10, 255, cv2.THRESH_BINARY)
    img_darkl1 = cv2.morphologyEx(img_darkf1,cv2.MORPH_OPEN,kernel)

    # Bitwise Operations
    img_both = cv2.bitwise_or(img_darkl,img_darkl1)

    return img_both