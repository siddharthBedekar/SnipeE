import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
img = cv.imread('raw.png')
rows,cols,ch = img.shape
pts1 = np.float32([[2,36],[636,28],[0,400],[638,377]])
pts2 = np.float32([[0,0],[636,0],[0,400],[636,400]])
M = cv.getPerspectiveTransform(pts1,pts2)
dst = cv.warpPerspective(img,M,(636,400))
plt.subplot(121),plt.imshow(img),plt.title('Input')
plt.subplot(122),plt.imshow(dst),plt.title('Output')
plt.show()