import cv2 as cv
import numpy as np
import os

# Resizing function, extract_hardexudates() will revert back to original size
def imgResize(img):
    h = img.shape[0]
    w = img.shape[1]
    perc = 500 / w
    w1 = 500
    h1 = int(h * perc)
    img_rs = cv.resize(img, (w1, h1))
    return img_rs, h, w

def kmeansclust(img, k, attempts, max_iter, acc, use='OD'):
    if use == 'OD':
        img_rsp = img.reshape((-1, 1))
    else:
        img_rsp = img.reshape((-1, 3))

    img_rsp = img_rsp.astype('float32')
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, max_iter, acc)
    _, labels, centers = cv.kmeans(img_rsp, k, None, criteria, attempts, cv.KMEANS_RANDOM_CENTERS)
    centers = centers.astype('uint8')

    labels = labels.flatten()
    seg_img = centers[labels.flatten()]
    seg_img = seg_img.reshape(img.shape)
    return seg_img

# Get contours
def getContours1(img, img_main, cnt_area):
    mask1 = np.ones(img.shape, dtype="uint8") * 0
    cnts0, hier0 = cv.findContours(img.copy(), cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
    for i in cnts0:
        if cv.contourArea(i) <= cnt_area:
            cv.drawContours(mask1, [i], -1, 255, -1)
    mask1 = cv.bitwise_and(img_main, img_main, mask=mask1)
    return mask1

# Masking optical disk but first have to retrieve its location
def extract_opticdisk(image):
    img_rs, h, w = imgResize(image)
    img_grey = cv.cvtColor(img_rs, cv.COLOR_BGR2GRAY)
    img_k = kmeansclust(img_grey, 7, 10, 400, 0.99)
    template = np.ones((95, 95), dtype="uint8") * 0
    template = cv.circle(template, (47, 47), 46, 255, -1)
    temp = template

    # TEMPLATE MATCHING
    metd = cv.TM_CCOEFF_NORMED
    temp_mat = cv.matchTemplate(img_k, temp, metd)

    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(temp_mat)
    x = max_loc[0] + 45
    y = max_loc[1] + 45

    temp_mat = img_grey.copy()
    img_mark = cv.circle(temp_mat, (x, y), 40, 0, -1)

    return img_mark

# Extraction, returns segmented BW image of the hard exudates
def get_hardexudates(image):
    image = np.array(image)
    img_mark = extract_opticdisk(image)
    img, h, w = imgResize(image)

    _, img_gc, _ = cv.split(img)
    
    # Apply CLAHE to enhance contrast
    clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_gc = clahe.apply(img_gc)

    # K-means clustering
    clus_seg = kmeansclust(img, 18, 15, 20, 0.39, use='EX')
    clus_seg = cv.cvtColor(clus_seg, cv.COLOR_BGR2GRAY)
    unique, counts = np.unique(clus_seg, return_counts=True)
    _, kthm = cv.threshold(clus_seg, np.max(unique) - 20, 255, cv.THRESH_BINARY)  # Adjusted threshold

    # Edge detection and morphological operations
    edges = cv.Canny(img_gc, 1, 5)
    img_cnt = cv.dilate(edges, cv.getStructuringElement(cv.MORPH_ELLIPSE, (2, 2)))
    img_clean = getContours1(img_cnt, img_gc, 2)  # Adjusted contour area
    img_clean = cv.erode(img_clean, cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)), iterations=1)
    img_clean = cv.dilate(img_clean, cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5)), iterations=1)  # Reduced iterations
    max_intsy = np.max(img_clean.flatten())
    img_clean[img_clean >= max_intsy] = 255
    img_clean[img_clean < max_intsy] = 0

    _, img_clean = cv.threshold(img_clean, 150, 255, cv.THRESH_BINARY)  # Adjusted threshold
    img_final = cv.bitwise_or(kthm, img_clean)

    img_final[img_mark == 0] = 0

    # Create a circular mask to remove the border of the fundus image
    mask = np.zeros((img_final.shape[0], img_final.shape[1]), dtype=np.uint8)
    cv.circle(mask, (img_final.shape[1] // 2, img_final.shape[0] // 2), min(img_final.shape[0] // 2, img_final.shape[1] // 2), 255, -1)
    img_final = cv.bitwise_and(img_final, mask)

    img_final = cv.resize(img_final, (w, h))

    return img_final
