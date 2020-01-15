import cv2
import numpy as np
import imutils
import math


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

    lines = cv2.HoughLinesP(edges, 1, np.pi/180.0, 100, minLineLength=100, maxLineGap=10)
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        if abs(angle) < 30:
            angles.append(angle)
        if len(angles) > 5:
            break
    median = np.median(angles)
    return median

def get_contours_angle(gray_img, min_w = 100, min_h= 200, w_blur=1):
    blur = gray_img.copy()
    if w_blur == 17:
        blur = cv2.GaussianBlur(gray_img, (3, 3), 0)
    elif w_blur != 1:
        blur = cv2.GaussianBlur(gray_img, (w_blur, w_blur), 0)

    (thresh, img_bin) = cv2.threshold(blur, 128, 255,cv2.THRESH_BINARY)
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
    if w_blur == 17:
        verticle_lines_img = cv2.dilate(img_temp1, verticle_kernel, iterations=3)
    else:
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
    (thresh, img_final_bin) = cv2.threshold(img_final_bin, 128,255, cv2.THRESH_BINARY )

    # Find contours for image, which will detect all the boxes
    cnts = cv2.findContours(img_final_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    # Sort all the contours by top to bottom.
    (contours, boundingBoxes) = sort_contours(cnts, method="top-to-bottom")
    idx = 0
    angle = 0

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if (w > min_w and h > min_h):
            idx += 1
            if idx==2:
                new_img = gray_img[y:y+h, x:x+w]
                angle = detect_angle(new_img)
                break
    return contours, angle

def scale_ratio(gray_img, scale_ratio=0.03):
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

    if len(lst_location) < total_bboxs and w_blur < 17:
        return get_all_cell(gray, num_col=num_col, min_cell_w=min_cell_w, min_cell_h=min_cell_h, img_path=img_path, total_bboxs=total_bboxs, w_blur=w_blur+2)
    elif len(lst_location) > total_bboxs and min_cell_h < 80:
        return get_all_cell(gray, num_col=num_col, min_cell_w=min_cell_w+2, min_cell_h=min_cell_h+2, img_path=img_path, total_bboxs=total_bboxs, w_blur=w_blur)
    if len(lst_location) == total_bboxs:
        return lst_location
    else:
        return lst_location
    
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
    _bboxs = []
    
    for c in cnts:
        area = cv2.contourArea(c)
        if area > 10000:
            x,y,w,h = cv2.boundingRect(c)
            _distance = x*x + y*y
            _bboxs.append([x,y,w,h])
            _area = w*h
            if max_area < _area:
                max_area = _area
            if _distance < min_distance and 0.65<w/h<1.35:
                min_distance = _distance
    for bbox in _bboxs:
        x,y,w,h = bbox
        if max_area == w*h:
            bboxs['table'] = [x,y,w,h].copy()
            _bboxs.remove([x,y,w,h])
        elif min_distance == x*x + y*y and 0.65<w/h<1.35 and x < 600 and y < 600:
            if y-int(0.05*h) > 0 and x-int(0.05*w) > 0:
                bboxs['stamp'] = [x - int(0.05*w), y-int(0.05*h), int(1.1*w), int(1.1*h)].copy()
            else:
                bboxs['stamp'] = [x,y,w,h].copy()
            _bboxs.remove([x,y,w,h])

    for bbox in _bboxs:
        x,y,w,h = bbox
        if 'title' in bboxs:
            bboxs['spam'] = [x,y,w,h].copy()
        else:
            bboxs['title'] = [x,y,w,h].copy()
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
        gray_img = rotate_image(gray_img, angle)
    return gray_img, get_bbox(gray_img)

def check_tile_outside(dilate_test, bboxs_test):
    dilate_test_cp = dilate_test.copy()
    dilate_test_cp = cv2.GaussianBlur(dilate_test_cp, (3,3), 0)
    (thresh, dilate_test_cp) = cv2.threshold(dilate_test_cp, 128, 255,cv2.THRESH_BINARY)
    dilate_test_cp = 255 - dilate_test_cp
    # Kiem tra phan ngoai dau va bang
    for item in bboxs_test:
        x,y,w,h = bboxs_test[item]
        if x < 0:
            x = 0
        if y < 0:
            y = 0
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
            if tiles.sum()/(tiles.shape[0]*tiles.shape[1])> 2.0:
                return False, "Gạch ở ngoài bảng"
    return True, ""


def check_horizontally(img):
    img_new = img.copy()
    h, w = img_new.shape
    img_new = img_new[0:h, int(0.05*w):int((1-0.05)*w)]
    img_new = 255 - img_new
    num_point = 0
    for i in range(img_new.shape[0]):
        if img_new[i].sum()/img_new.shape[1] > 0.5:
            num_point += 1
    if num_point == h:
        return False
    return True

def get_pixcel_crop(img_bin_test):
    top_left = 0
    for i in range(10):
        if img_bin_test[i][0:5].sum() >= 255:
            top_left = i+1
    bottom_left = 0
    for i in range(img_bin_test.shape[0]-1,img_bin_test.shape[0]-11, -1):
        if img_bin_test[i][0:5].sum() >= 255:
            bottom_left = img_bin_test.shape[0] - i
    top_right = 0
    for i in range(10):
        if img_bin_test[i][-6:-1].sum() >= 255:
            top_right = i+1
    bottom_right = 0
    for i in range(img_bin_test.shape[0]-1,img_bin_test.shape[0]-11, -1):
        if img_bin_test[i][-6:-1].sum() >= 255:
            bottom_right = img_bin_test.shape[0] - i
    return max([top_left, bottom_left, top_right, bottom_right, 2])

def get_segment(img_crop, thresh=254):
    status = 0
    segment = 0
    segments = []
    max_sum = 0
    for i in range(img_crop.shape[1]):
        value_sum = img_crop[: , i].sum()
        if value_sum > thresh:
            if status == 0:
                segments.append({'status' : status, 'segment':segment, 'sum': max_sum})
                status = 1
                segment = 0
            if max_sum < value_sum:
                max_sum = value_sum
            segment += 1
        else:
            if status == 1:
                segments.append({'status' : status, 'segment':segment, 'sum': max_sum})
                max_sum = 0
                status = 0
                segment = 0
            segment += 1
    segments.append({'status' : status, 'segment':segment, 'sum': max_sum})
    return segments

def validate_pre_cell(img, check_num=False):
    h, w = img.shape
    img_bin_test = 255 - img

    thresh = 254
    if not check_num:
        pixel_crop = get_pixcel_crop(img_bin_test)
        img_crop = img_bin_test[pixel_crop:h-pixel_crop*2, pixel_crop:w-pixel_crop*2]
        step = 6
        segment_one = 0
        segments = get_segment(img_crop, thresh = thresh)
        for i in range(len(segments)):
            if segments[i]['segment'] > 30 and segments[i]['sum'] <= 2550 \
            and segments[i]['status'] == 1 and segments[i+1]['segment'] > 8 and segments[i-1]['segment'] > 8:
                return 'small', None
            if i != 0 and i!= len(segments)-1:
                if (segments[i]['segment'] > segments[0]['segment'] \
                    or segments[i]['segment'] > segments[-1]['segment']) \
                and segments[i]['status'] == 0 and segments[i]['segment'] > 30 \
                and segments[i+1]['segment'] > 8 and segments[i-1]['segment'] > 8:
                    return 'alone', None
            if segments[i]['status'] == 1:
                segment_one += 1
            # check theo chieu doc thi xoa bot lop dau va cuoi
            
        img_crop_horizontal = img_bin_test[pixel_crop:h-pixel_crop*2, 0:w-pixel_crop*2]
        cnt = 0

        for i in range(0, step):
            if img_crop[: , i].sum()> thresh:
                cnt += 1
            if img_crop_horizontal[: , i].sum()> thresh:
                cnt += 1


        if cnt == step*2:
            return 'left', segment_one
        cnt = 0
        
        img_crop_horizontal = img_bin_test[pixel_crop:h-pixel_crop*2, pixel_crop*2:w]
        for i in range(img_crop.shape[1]-1, img_crop.shape[1]-step-1, -1):
            if img_crop[: , i].sum()> thresh:
                cnt += 1
            if img_crop_horizontal[: , i-pixel_crop].sum()> thresh:
                    cnt += 1

        if cnt == step*2:
            return 'right', segment_one
        img_crop_vertical = img_bin_test[0:h-pixel_crop*2, pixel_crop:w-pixel_crop*2]
        
        cnt = 0
        for i in range(0, step):
            if img_crop[i].sum()> thresh:
                cnt += 1
            if img_crop_vertical[i].sum()> thresh:
                    cnt += 1

        if cnt == step*2:
            return 'top', segment_one
        
        cnt = 0
        img_crop_vertical = img_bin_test[pixel_crop*2:h, pixel_crop:w-pixel_crop*2]
        for i in range(img_crop.shape[0]-1, img_crop.shape[0]-step-1, -1):
            if img_crop[i].sum()> thresh:
                cnt += 1
            if img_crop_vertical[i-pixel_crop].sum()> thresh:
                cnt += 1

        if cnt == step*2:
            return 'bottom', segment_one
        # check gach khong hop le
        return '', segment_one
    else:
        step = 4
        pixel_crop = 0
        if img_bin_test.shape[0] < 58 or img_bin_test.shape[0] < 58:
            return 'size', None
        img_crop = img_bin_test[pixel_crop:h-pixel_crop*2, pixel_crop:w-pixel_crop*2]
        # check theo chieu ngang

        img_crop_horizontal = img_bin_test[pixel_crop:h-pixel_crop*2, 0:w-pixel_crop*2]
        cnt = 0
        for i in range(0, step):
            if img_crop[: , i].sum()> thresh:
                cnt += 1
            if img_crop_horizontal[: , i].sum()> thresh:
                cnt += 1

        if cnt == step*2:
            return 'left', None
        cnt = 0
        img_crop_horizontal = img_bin_test[pixel_crop:h-pixel_crop*2, pixel_crop*2:w]
        for i in range(img_crop.shape[1]-1, img_crop.shape[1]-step-1, -1):
            if img_crop[: , i].sum()> thresh:
                cnt += 1
            if img_crop_horizontal[: , i-pixel_crop].sum()> thresh:
                    cnt += 1

        if cnt == step*2:
            return 'right', None
        
        # check theo chieu doc thi xoa bot lop dau va cuoi
        img_crop_vertical = img_bin_test[0:h-pixel_crop*2, pixel_crop:w-pixel_crop*2]
        cnt = 0
        for i in range(0, step):
            if img_crop[i].sum()> thresh:
                cnt += 1
            if img_crop_vertical[i].sum()> thresh:
                    cnt += 1

        if cnt == step*2:
            return 'top', None
        cnt = 0
        img_crop_vertical = img_bin_test[pixel_crop*2:h, pixel_crop:w-pixel_crop*2]
        for i in range(img_crop.shape[0]-1, img_crop.shape[0]-step-1, -1):
            if img_crop[i].sum()> thresh:
                cnt += 1
            if img_crop_vertical[i-pixel_crop].sum()> thresh:
                cnt += 1

        if cnt == step*2:
            return 'bottom', None
    return '', None

def validate_small(img, right=True):
    h, w = img.shape
    img_bin_test = 255 - img
    pixel_crop = 2

    thresh = 254            
    img_crop_horizontal = img_bin_test[pixel_crop:h-pixel_crop*2, 0:w-pixel_crop*2]
    status = True
    if right:
        for i in range(h):
            if img_crop_horizontal[: , i].sum()< thresh:
                status = False
                break
            if img_crop_horizontal[: , i].sum()< 2550:
                break
    else:
        for i in range(h-1,0,-1):
            if img_crop_horizontal[: , i].sum()< thresh:
                status = False
                break
            if img_crop_horizontal[: , i].sum()< 2550:
                break
    return not status
    
def validation_full(list_people, path_test='', num_person=10, size_blur = (0,0)):
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
    if 'stamp' not in bboxs_test:
        return False, "Thiếu dấu góc trái" 
    lst_location_cell_test = get_all_cell(gray_test, num_col = num_col, min_cell_w= 50, min_cell_h = 50, total_bboxs=total_bboxs)

    bboxs_test['table'] = lst_location_cell_test[1]
    if len(lst_location_cell_test) != total_bboxs:
        return False, "Ảnh bị mờ hoặc phiếu bầu cử không hợp lệ"
    status, message = check_tile_outside(gray_test, bboxs_test)
    if status == False: 
        return status, message
    
    # test
    if size_blur != (0, 0):
        blur_test = cv2.GaussianBlur(gray_test, size_blur, 0)
        (_, img_bin_test) = cv2.threshold(blur_test, 170, 255,cv2.THRESH_BINARY)
    else:
        (_, img_bin_test) = cv2.threshold(gray_test, 170, 255,cv2.THRESH_BINARY)

    results = []
    step = 2
    # check gach ko hop le
    for i in range(num_col + step + 1, len(lst_location_cell_test), step):
        stt = int((i - num_col)/step)
        # check stt 
        x_test, y_test, w_test, h_test = lst_location_cell_test[i-1]
        message, _ = validate_pre_cell(img_bin_test[y_test:y_test+h_test, x_test:x_test+w_test], check_num=True)
        if message != '':
            return False, "Gạch không hợp lệ ô STT %s"%(stt) 
        # top
        x_test, y_test, w_test, h_test = lst_location_cell_test[i]
        message, segments = validate_pre_cell(img_bin_test[y_test:y_test+h_test, x_test:x_test+w_test])
        if message == 'right':
            x_test_new = x_test + w_test -10
            w_test_new = 40
            if not validate_small(img_bin_test[y_test:y_test+h_test, x_test_new:x_test_new+w_test_new]):
                return False, "Gạch không hợp lệ ô STT %s"%(stt) 
        if message == 'left':
            x_test_new = x_test + w_test -10
            w_test_new = 40
            if not validate_small(img_bin_test[y_test:y_test+h_test, x_test_new:x_test_new+w_test_new], right=False):
                return False, "Gạch không hợp lệ ô STT %s"%(stt) 
        if message == 'top' or message == 'bottom':
            return False, "Gạch không hợp lệ ô STT %s"%(stt) 
        # alone small
        if message == 'small' or message == 'alone':
            return False, "Gạch không hợp lệ ô STT %s"%(stt) 
        if stt > num_person:
            break
        if 2*len(list_people[stt].split()) >= segments:
            results.append({'vote': 0, 'order_number': stt})
        else:
            results.append({'vote': 1, 'order_number': stt})
    return True, results