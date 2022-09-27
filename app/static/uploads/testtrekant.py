import cv2
import numpy as np

image = np.ones((300, 300, 3), np.uint8) * 255

pt1 = (150, 100)
pt2 = (100, 200)
pt3 = (200, 200)

cv2.circle(image, pt1, 2, (0,0,255), -1)
cv2.circle(image, pt2, 2, (0,0,255), -1)
cv2.circle(image, pt3, 2, (0,0,255), -1)

triangle_cnt = np.array( [pt1, pt2, pt3] )

cv2.drawContours(image, [triangle_cnt], 0, (0,255,0), -1)

cv2.imshow("image", image)
cv2.waitKey()