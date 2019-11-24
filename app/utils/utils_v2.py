import cv2
import numpy as np
from matplotlib import pyplot as plt
import json
import os
import imutils
from scipy import ndimage, misc

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
 
    # return the list of sorted contours and bounding boxes
    return (cnts, boundingBoxes)


def unit_vector(vector):
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)) * 180/np.pi 

def detect_angle(gray):
    # Apply edge detection method on the image 
    edges = cv2.Canny(gray,50,150,apertureSize = 3) 

    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 300, maxLineGap=250)
    angle = 0
    k=0
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = angle_between((10, 0), (x2 - x1, y2-y1))
        if (angle > 0 and angle <30) or (angle <0 and angle > -30):
            k+=1
        if k > 5:
            break
    return (angle)

def get_contours_angle(gray_img, min_w = 100, min_h= 200):

    (thresh, img_bin) = cv2.threshold(gray_img, 128, 255,cv2.THRESH_BINARY| cv2.THRESH_OTSU)
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
    # cv2.imwrite("a.png", img_temp2)
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

def get_bbox(gray):
    blur = cv2.GaussianBlur(gray, (9,9), 0)
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,30)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
    dilate = cv2.dilate(thresh, kernel, iterations=4)

    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    min_distance = float('Inf')
    max_area = 0
    bboxs = {}
    dilates = {}
    for c in cnts:
        area = cv2.contourArea(c)
        if area > 10000:
            x,y,w,h = cv2.boundingRect(c)
            distance = x*x + y*y
            # lấy phần diện tích lớn nhất
            if max_area < area:
                max_area = area
                bboxs['table'] = [x,y,w,h]
                temp = dilate.copy()
                dilates['table'] = temp[y:y+h, x:x+w]
            # kiểm tra xem có dạng hình vuông hay ko
            elif distance < min_distance and 0.95<w/h<1.05:
                min_distance = distance
                bboxs['stamp'] = [x,y,w,h]
                temp = dilate.copy()
                temp[y:y+h, x:x+w] = 0
                dilates['stamp'] = temp[0:y+h, :]
            elif 'title' in bboxs:
                bboxs['spam'] = [x,y,w,h]
            else:
                bboxs['title'] = [x,y,w,h]
    return bboxs, dilates, thresh

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

def get_all_cell(gray, num_col = 4, min_cell_w= 20, min_cell_h = 20):

    # Thresholding the image
    gray_img = gray.copy()
    h, w = gray_img.shape
    # img_name =  (("img_path".split("/")[-1]).split("."))[0]
    # output_dir = "output/%s"%img_name
    # os.makedirs(output_dir, exist_ok=True)
    # contours, angle = get_contours_angle(gray_img, min_w = 0.3*w)
    # if angle >0 and angle <30:
    #     gray_img = rotate_image(gray_img, -angle)
    contours, _ = get_contours_angle(gray_img)
    idx = 0
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
                        idx += 1
                        # new_img = gray_img[y:y+h, x:x+w]
                        # cv2.imwrite("%s/%s"%(output_dir, str(idx) + '.png'), new_img)
                    first = False
                    lst_box = []
            elif (len(lst_box) == num_col) or (id == (len(contours) - 1)):
                boundingBoxes = sorted(lst_box, key=lambda b: b[0], reverse = False)
                for id, box in enumerate(boundingBoxes):
                    x, y, w, h = box 
                    if (w > min_cell_w and h > min_cell_h):
                        lst_location.append([x, y, w, h])
                        idx += 1
                        # new_img = gray_img[y+int(0.05*h):y+int(0.95*h), x + int(0.05*w):x+int(0.95*w)]
                        # cv2.imwrite("%s/%s"%(output_dir, str(idx) + '.png'), new_img)
                lst_box = []
    x, y, w, h = lst_location[1]
    new_img = gray_img[y:y+h, x:x+w]
    return lst_location, new_img

def validate(img_origin, img_test, in_table=True):
    ratio = img_test.sum()/img_origin.sum()
    if 0.99 < ratio < 1.01:
        return True
    if 0.95 < ratio < 1.05 and in_table:
        return True
    return False

def rotate_image_by_table(gray_img):
    bboxs_test, _, _ = get_bbox(gray_img)
    # xoay ảnh dựa theo bảng và title
    ## lấy phần bảng và title
    bbox_tb_and_tt = bboxs_test['table']
    table_and_title_img = gray_img[bbox_tb_and_tt[1]:bbox_tb_and_tt[1] + bbox_tb_and_tt[3], bbox_tb_and_tt[0]:bbox_tb_and_tt[0]+bbox_tb_and_tt[2]]
    ### lấy góc
    _, angle = get_contours_angle(table_and_title_img)
    ## xoay ảnh
    if angle >0 and angle <30:
        gray_img = rotate_image(gray_img, -angle)
    return gray_img

def get_dilate(gray):
    blur = cv2.GaussianBlur(gray, (9,9), 0)
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,30)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
    dilate = cv2.dilate(thresh, kernel, iterations=4)
    return dilate

def check_stamp(dilates_test, bboxs_test):
    # Kiem tra con dau
    if 'stamp' not in dilates_test:
        return False, "Thiếu dấu"
    ## kiểm tra xem có bị gạch vào phần ngoài dấu hay không
    ## phần dấu bắt buộc phải dưới phần tiêu đề, bảng trên góc 5x5cm
    if  'spam' in bboxs_test or len(bboxs_test) != 3:
        return False, "Gạch ở ngoài bảng spam"
    if dilates_test['stamp'].sum()/len(dilates_test['stamp']) > 0.01:
        return False, "Gạch ở trên phần con dấu"
    return True, ""
    
def check_tile_outside(dilate_test, bboxs_test):
    dilate_test_cp = dilate_test.copy()
    # Kiem tra phan ngoai dau va bang
    for item in bboxs_test:
        x,y,w,h = bboxs_test[item]
        dilate_test_cp[y:y+h, x:x+w] = 0
    if dilate_test_cp.sum()/(dilate_test_cp.shape[0])> 5:
        return False, "Gạch ở ngoài bảng"
    return True, ""

def get_ratio(img_origin, img_test):
    img_origin = 255 - img_origin
    img_test = 255 - img_test
    img_test = cv2.resize(img_test,(img_origin.shape[1],img_origin.shape[0]))
    return img_test.sum()/img_origin.sum()

#     return ((img_origin.sum()/(img_origin.shape[0]*img_origin.shape[1]))
#                    /(img_test.sum()/(img_test.shape[0]*img_test.shape[1])))

def get_w_max(gray):
    blur = cv2.GaussianBlur(gray, (9,9), 0)
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,30)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
    dilate = cv2.dilate(thresh, kernel, iterations=4)

    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    ROI_number = 0
    bboxs = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area > 10:
            x,y,w,h = cv2.boundingRect(c)
            bboxs.append([int(x*0.98),int(y*0.98),int(w*1.05),int(h*1.05)])
            
    return bboxs

def validate_cell(gray_origin, gray_file, i=0):
    gray_file = scale_ratio(gray_file, scale_ratio=0.05)
    bboxs = get_w_max(gray_file)
    gray_file_cp = (255 - gray_file).copy()
    for bbox in bboxs:
        x,y,w,h = bbox
        gray_file_cp[y:y+h, x:x+w] = 0

    ratio = gray_file_cp.sum()/(gray_file_cp.shape[0]*gray_file_cp.shape[1])
    if ratio > 1.1:
#         f = plt.figure()
#         f.add_subplot(1,2, 1)
#         plt.imshow(gray_file, 'gray')
#         f.add_subplot(1,2, 2)
#         plt.imshow(gray_file_cp, 'gray')
#         plt.show(block=True)
#         plt.show()
        return False
    return True

# w_test, gray_file = get_w_max(gray_file)
#     f = plt.figure()
#     f.add_subplot(1,2, 1)
#     plt.imshow(gray_file, 'gray')
#     f.add_subplot(1,2, 2)
#     plt.imshow(gray_origin, 'gray')
#     plt.show(block=True)
#     plt.show()
#     print(w_origin, w_test)
# #     img_test = cv2.resize(img_test,(img_origin.shape[1],img_origin.shape[0]))
# #     cv2.imwrite("%s/%s"%('output_dilate', str(i) + 'img_test.png'), img_test)
# #     cv2.imwrite("%s/%s"%('output_dilate', str(i) + 'img_origin.png'), img_origin)
# #     ratio = ((img_origin.sum()/(img_origin.shape[0]*img_origin.shape[1]))
# #                    /(img_test.sum()/(img_test.shape[0]*img_test.shape[1])))
#     ratio = w_origin/w_test
#     if abs(1 - ratio) <= 0.15:
#         return True
#     print(ratio)
#     return False


def validation_full(path_origin='', path_test='', num_col = 4):
    gray_test = read_to_gray(path_test)
    gray_test = rotate_image_by_table(gray_test)
    (_, gray_test) = cv2.threshold(gray_test, 128, 255,cv2.THRESH_BINARY| cv2.THRESH_OTSU)
    
#     contours, angle = get_contours_angle(gray_img)
    bboxs_test, dilates_test, dilate_test = get_bbox(gray_test)
    


    # Phát hiện gạch title
    # lấy title và tất cả các cell trong table
#     table_test = gray_test[bboxs_test['table'][1]:bboxs_test['table'][1] + bboxs_test['table'][3], 
#                                  bboxs_test['table'][0]:bboxs_test['table'][0]+bboxs_test['table'][2]]
#     tb_tt_dilate_test = dilate_test[bboxs_test['table'][1]:bboxs_test['table'][1] + bboxs_test['table'][3], 
#                                  bboxs_test['table'][0]:bboxs_test['table'][0]+bboxs_test['table'][2]]
    lst_location_cell_test, table_test = get_all_cell(gray_test)
    bboxs_test['table'] = lst_location_cell_test[1]
    status, message = check_stamp(dilates_test, bboxs_test)
    if status == False: 
        return status, message
    status, message = check_tile_outside(dilate_test, bboxs_test)
    if status == False: 
        return status, message
    
    title_test = gray_test[bboxs_test['title'][1]:bboxs_test['title'][1] + bboxs_test['title'][3], 
                                 bboxs_test['title'][0]:bboxs_test['title'][0]+bboxs_test['title'][2]]
    
    # tạm để test
    gray_origin = read_to_gray(path_origin)
#     gray_origin = rotate_image_by_table(gray_origin)
    (_, gray_origin) = cv2.threshold(gray_origin, 128, 255,cv2.THRESH_BINARY| cv2.THRESH_OTSU)

    bboxs_origin, _, dilate_origin = get_bbox(gray_origin)
    # table_origin = gray_origin[bboxs_origin['table'][1]:bboxs_origin['table'][1] + bboxs_origin['table'][3], 
    #                              bboxs_origin['table'][0]:bboxs_origin['table'][0]+bboxs_origin['table'][2]]
#     tb_tt_dilate_origin = dilate_origin[bboxs_origin['table'][1]:bboxs_origin['table'][1] + bboxs_origin['table'][3], 
#                                  bboxs_origin['table'][0]:bboxs_origin['table'][0]+bboxs_origin['table'][2]]
    lst_location_cell_origin, table_origin = get_all_cell(gray_origin)
    lst_location_cell_origin, table_origin = get_all_cell(table_origin)
    # cv2.imwrite('test/table_origin.png', table_origin)
    title_origin = gray_origin[bboxs_origin['title'][1]:bboxs_origin['title'][1] + bboxs_origin['title'][3], 
                                 bboxs_origin['title'][0]:bboxs_origin['title'][0]+bboxs_origin['title'][2]]

    table_test  = cv2.resize(table_test,(table_origin.shape[1],table_origin.shape[0]))
    # Check phần title
    
    ratio_title = get_ratio(title_origin, title_test)
    if abs(1 - ratio_title)>= 0.4:
        return False, "Gạch ở phần title"
    
    # check ở all cell
    step = int(num_col/2)
    results = []
    for i in range(num_col+2, len(lst_location_cell_origin), step):

        # x_origin, y_origin, w_origin, h_origin = lst_location_cell_origin[i]
        # cell_origin = table_origin[y_origin:y_origin+h_origin, x_origin:x_origin+w_origin]
        # cv2.imwrite('test/%s.png'%i, cell_origin)
#         x_test, y_test, w_test, h_test = lst_location_cell_origin[i]
#         cell_test = table_test[y_test:y_test+h_test, x_test:x_test+w_test]
#         ratio_cell = get_ratio(cell_origin, cell_test)
#         if abs(1 - ratio_cell) > 0.5:
#             results.append(["Lỗi gạch ở STT cell %s" %int((i-num_col)/step), ratio_cell, cell_origin, cell_test])

        x_origin, y_origin, w_origin, h_origin = lst_location_cell_origin[i]
        cell_origin = table_origin[y_origin:y_origin+h_origin, x_origin:x_origin+w_origin]
        x_test, y_test, w_test, h_test = lst_location_cell_origin[i]
        cell_test = table_test[y_test:y_test+h_test, x_test:x_test+w_test]
        ratio_cell = get_ratio(cell_origin, cell_test)
        stt = int((i-num_col)/step)
        status = validate_cell(cell_origin, cell_test,  stt)
        # cv2.imwrite('test/%s.png'%(i), cell_origin)
        if status == False:
            # return False, "Gạch không hợp lệ ô STT %s , tỷ lệ %s"%(stt, ratio_cell) 
            return False, "Gạch không hợp lệ ô STT %s"%(stt) 
        elif abs(1 - ratio_cell) <= 0.15:
            # results.append(["Không gạch", stt])
            results.append({'vote': 1, 'order_number': stt})
        else:# 0.2 > abs(1 - ratio_cell) > 0.07:
            # results.append(["Gạch hợp lệ", stt])
            results.append({'vote': 0, 'order_number': stt})
    return True, results

