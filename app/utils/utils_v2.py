import cv2
import numpy as np
import imutils
import math
from .model import build_model
import tensorflow as tf

def load_model():
    global model
    model = build_model()
    model.load_weights('model_weight.h5')
    global graph
    graph = tf.get_default_graph()

img_width = 500
img_height = 50

step = 2


def rotate_image(mat, angle):

    height, width = mat.shape[:2] # image shape has 3 dimensions
    image_center = (width/2, height/2) # getRotationMatrix2D needs coordinates in reverse order (width, height) compared to shape

    rotation_mat = cv2.getRotationMatrix2D(image_center, angle, 1.)

    # rotation calculates the cos and sin, taking absolutes of those.
    abs_cos = abs(rotation_mat[0,0]) 
    abs_sin = abs(rotation_mat[0,1])

    # find the new width and height bounds
    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)

    # subtract old image center (bringing image back to origo) and adding the new image center coordinates
    rotation_mat[0, 2] += bound_w/2 - image_center[0]
    rotation_mat[1, 2] += bound_h/2 - image_center[1]

    # rotate image with the new bounds and translated rotation matrix
    rotated_mat = cv2.warpAffine(mat, rotation_mat, (bound_w, bound_h), borderValue=(255,255,255))
    return rotated_mat

def sort_contours(cnts, method="left-to-right"):
    # initialize the reverse flag and sort index
    reverse = False
    i = 0
 
    # handle if we need to sort in reverse
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True
 
    # handle if we are sorting against the y-coordinate rather than
    # the x-coordinate of the bounding box
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1
    # construct the list of bounding boxes and sort them from top to
    # bottom
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]

    (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),
        key=lambda b: b[i][1], reverse=reverse))
 
    return (cnts, boundingBoxes)

def detect_angle(gray):
    # Apply edge detection method on the image 
    edges = cv2.Canny(gray,100, 100,apertureSize = 3) 

    lines = cv2.HoughLinesP(edges, 1, np.pi/180.0, 100, minLineLength=100, maxLineGap=30)
    angles = []
    
    for line in lines:
        x1, y1, x2, y2 = line[0]
        cv2.line(gray, (x1, y1), (x2, y2), (255, 0, 0), 3)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        angles.append(angle)
    median_angle = np.median(angles)

    return (median_angle)

def get_contours_angle(gray_img, min_w = 100, min_h= 200, w_blur=1):
    blur = gray_img.copy()
    if w_blur != 1:
        blur = cv2.GaussianBlur(gray_img, (w_blur, w_blur), 0)

    (thresh, img_bin) = cv2.threshold(blur, 128, 255,cv2.THRESH_BINARY| cv2.THRESH_OTSU)
    # Invert the image
    img_bin = 255-img_bin

    # Defining a kernel length
    kernel_length = np.array(gray_img).shape[1]//50

    # A verticle kernel of (1 X kernel_length), which will detect all the verticle lines from the image.
    verticle_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))
    # A horizontal kernel of (kernel_length X 1), which will help to detect all the horizontal line from the image.
    hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))
    # A kernel of (3 X 3) ones.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    # Morphological operation to detect vertical lines from an image
    img_temp1 = cv2.erode(img_bin, verticle_kernel, iterations=2)
    verticle_lines_img = cv2.dilate(img_temp1, verticle_kernel, iterations=2)
    # Morphological operation to detect horizontal lines from an image
    img_temp2 = cv2.erode(img_bin, hori_kernel, iterations=1)
    horizontal_lines_img = cv2.dilate(img_temp2, hori_kernel, iterations=1)
    # Weighting parameters, this will decide the quantity of an image to be added to make a new image.
    alpha = 0.5
    beta = 1.0 - alpha
    # This function helps to add two image with specific weight parameter to get a third image as summation of two image.
    img_final_bin = cv2.addWeighted(verticle_lines_img, alpha, horizontal_lines_img, beta, 0.0)
    img_final_bin = cv2.erode(~img_final_bin, kernel, iterations=2)
    (thresh, img_final_bin) = cv2.threshold(img_final_bin, 128,255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Find contours for image, which will detect all the boxes
    cnts = cv2.findContours(img_final_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    # Sort all the contours by top to bottom.
    (contours, boundingBoxes) = sort_contours(cnts, method="top-to-bottom")
    idx = 0
    angle = 0

    for c in contours:
        # Returns the location and width,height for every contour
        x, y, w, h = cv2.boundingRect(c)
        if (w > min_w and h > min_h):
            idx += 1
            if idx==2:
                new_img = gray_img[y:y+h, x:x+w]
                angle = detect_angle(new_img)
                break
    return contours, angle

def scale_ratio(gray_img, scale_ratio=0.01):
    h, w = gray_img.shape
    gray_img = gray_img[int(scale_ratio*h):int((1-scale_ratio)*h), int(scale_ratio*w):int((1-scale_ratio)*w)]
    return gray_img

# đọc ảnh và chuyển sang gray
def read_to_gray(path_file):
    img = cv2.imread(path_file)
    if len(img.shape) == 2:  
        gray_img = img
    elif len(img.shape) == 3:
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return scale_ratio(gray_img)

def get_all_cell(gray, num_col = 4, min_cell_w= 20, min_cell_h = 20, img_path='', total_bboxs=0, w_blur=1):

    # Thresholding the image
    gray_img = gray.copy()
    h, w = gray_img.shape
    contours, _ = get_contours_angle(gray_img, w_blur=w_blur)
    lst_box = []
    first = True
    lst_location = []
    for id, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)
        if (w > min_cell_w and h > min_cell_h):
            lst_box.append([x, y, w, h])
            if len(lst_box)==2 and first:
                for box in lst_box:
                    x, y, w, h = box
                    if (w > min_cell_w and h > min_cell_h):
                        lst_location.append([x, y, w, h]) 
                    first = False
                    lst_box = []
            elif (len(lst_box) == num_col) or (id == (len(contours) - 1)):
                boundingBoxes = sorted(lst_box, key=lambda b: b[0], reverse = False)
                for id, box in enumerate(boundingBoxes):
                    x, y, w, h = box 
                    if (w > min_cell_w and h > min_cell_h):
                        lst_location.append([x + int(0.05*w), y+int(0.05*h), int(0.95*w), int(0.95*h)])
                lst_box = []

    if len(lst_location) < total_bboxs and w_blur < 15:
        return get_all_cell(gray, num_col=num_col, min_cell_w=min_cell_w, min_cell_h=min_cell_h, img_path=img_path, total_bboxs=total_bboxs, w_blur=w_blur+2)
    elif len(lst_location) > total_bboxs and min_cell_h < 35:
        return get_all_cell(gray, num_col=num_col, min_cell_w=min_cell_w+2, min_cell_h=min_cell_h+2, img_path=img_path, total_bboxs=total_bboxs, w_blur=w_blur)
    if len(lst_location) == total_bboxs:
        return lst_location, ""
    else:
        return lst_location, "Ảnh không đúng template hoặc quá mờ"
    
def get_bbox(gray):
    blur = cv2.GaussianBlur(gray, (9,9), 0)
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,15)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
    dilate = cv2.dilate(thresh, kernel, iterations=4)
    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    min_distance = float('Inf')
    max_area = 0
    bboxs = {}
    for c in cnts:
        area = cv2.contourArea(c)
        if area > 10000:
            x,y,w,h = cv2.boundingRect(c)
            distance = x*x + y*y
            # lấy phần diện tích lớn nhất
            if max_area < area:
                max_area = area
                bboxs['table'] = [x,y,w,h]
            # kiểm tra xem có dạng hình vuông hay ko
            if distance < min_distance and 0.85<w/h<1.15:
                min_distance = distance
                bboxs['stamp'] = [x - int(0.05*w), y-int(0.05*h), int(1.1*w), int(1.1*h)]

            elif 'title' in bboxs and len(bboxs) > 3:
                bboxs['spam'] = [x,y,w,h]
            else:
                bboxs['title'] = [x,y,w,h]
    return bboxs

def rotate_image_by_table(gray_img):
    bboxs_test = get_bbox(gray_img)
    # xoay ảnh dựa theo bảng và title
    ## lấy phần bảng và title
    bbox_tb_and_tt = bboxs_test['table']
    table = gray_img[bbox_tb_and_tt[1]:bbox_tb_and_tt[1] + bbox_tb_and_tt[3], bbox_tb_and_tt[0]:bbox_tb_and_tt[0]+bbox_tb_and_tt[2]].copy()
    ### lấy góc
    _, angle = get_contours_angle(table)
    ## xoay ảnh
    if angle != 0:
        gray_img = rotate_image(gray_img, -angle)
    return gray_img, get_bbox(gray_img)

def check_tile_outside(dilate_test, bboxs_test):
    dilate_test_cp = dilate_test.copy()
    dilate_test_cp = cv2.GaussianBlur(dilate_test_cp, (3,3), 0)
    (thresh, dilate_test_cp) = cv2.threshold(dilate_test_cp, 128, 255,cv2.THRESH_BINARY| cv2.THRESH_OTSU)
    dilate_test_cp = 255 - dilate_test_cp
    # Kiem tra phan ngoai dau va bang
    for item in bboxs_test:
        x,y,w,h = bboxs_test[item]
        dilate_test_cp[y:y+h, x:x+w] = 0
        
    imgheight=dilate_test_cp.shape[0]
    imgwidth=dilate_test_cp.shape[1]

    y1 = 0
    M = imgheight//16
    N = imgwidth//16

    for y in range(0,imgheight,M):
        for x in range(0, imgwidth, N):
            y1 = y + M
            x1 = x + N
            tiles = dilate_test_cp[y:y+M,x:x+N]
            if tiles.sum()/(tiles.shape[0]*tiles.shape[1])> 3.5:
                return False, "Gạch ở ngoài bảng"
    return True, ""

def get_ratio(img_origin, img_test):    
    img_origin = 255 - img_origin
    img_test = 255 - img_test
    img_test = cv2.resize(img_test,(img_origin.shape[1],img_origin.shape[0]))
    return img_test.sum()/img_origin.sum()

def validation_full(path_origin='', path_test='', num_person=10):
    if num_person <= 20:
        num_col = 2
    else:
        num_col=4
    if num_person % 2 == 1 and num_col == 4:
        total_bboxs = (num_person+1) * 2 + num_col + 2
    else:
        total_bboxs = num_person * 2 + num_col + 2
    gray_test = read_to_gray(path_test)
    gray_test, bboxs_test = rotate_image_by_table(gray_test)
    
    if 'spam' in bboxs_test:
        return False, "Gạch ở ngoài spam"
    if 'stamp' not in bboxs_test:
        return False, "Thiếu dấu"
    
    lst_location_cell_test, message = get_all_cell(gray_test, num_col = num_col, min_cell_w= 24, min_cell_h = 24, total_bboxs=total_bboxs)
    if message != "":
        return False, message
    
    bboxs_test['table'] = lst_location_cell_test[1]
    status, message = check_tile_outside(gray_test, bboxs_test)
    if status == False: 
        return status, message
    
    title_test = gray_test[bboxs_test['title'][1]:bboxs_test['title'][1] + bboxs_test['title'][3], 
                                 bboxs_test['title'][0]:bboxs_test['title'][0]+bboxs_test['title'][2]].copy()
    
    # tạm để test
    gray_origin = read_to_gray(path_origin)

    bboxs_origin = get_bbox(gray_origin)
    lst_location_cell_origin, _ = get_all_cell(gray_origin, num_col = num_col, min_cell_w= 24, min_cell_h = 24, total_bboxs=total_bboxs)
    title_origin = gray_origin[bboxs_origin['title'][1]:bboxs_origin['title'][1] + bboxs_origin['title'][3], 
                                 bboxs_origin['title'][0]:bboxs_origin['title'][0]+bboxs_origin['title'][2]].copy()

    # Check phần title
    ratio_title = get_ratio(title_origin, title_test)
    if abs(1 - ratio_title)>= 0.4:
        return False, "Gạch ở phần title"
    
    blur = cv2.GaussianBlur(gray_test, (9,9), 0)
    (_, img_bin) = cv2.threshold(blur, 128, 255,cv2.THRESH_BINARY| cv2.THRESH_OTSU)
    results = []
    for i in range(num_col + step + 1, len(lst_location_cell_test), step):
        stt = int((i - num_col)/step)
        if stt > num_person:
            break
        x, y, w, h = lst_location_cell_test[i]
        cell = cv2.resize(img_bin[y:y+h, x:x+w], (img_width,img_height), interpolation=cv2.INTER_CUBIC).reshape(img_width,img_height,1)
        with graph.as_default():
            pred = model.predict(np.array([cell/255.]))[0]
            max_pred = np.argmax(pred)
            if max_pred == 3 and max(pred) > 0.75:
                return False, "Gạch không hợp lệ ô STT %s"%(stt) 
            if max_pred == 1 or max_pred == 2:
                results.append({'vote': 0, 'order_number': stt})
            if max_pred == 0:
                results.append({'vote': 1, 'order_number': stt})
    return True, results