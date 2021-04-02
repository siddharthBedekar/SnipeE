import cv2
import numpy as np
import imutils
from collections import deque


#Server imports
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
import time

#odrive imports
import pygame
import sys
import odrive
from odrive.enums import *
import time
import math

# SERVER ---------------------------------------------------------------------------------------------------------------

#globals for server
pingT = 0
pinged = False

#read data globals
desiredX = 0
desiredY = 0

#socket init and event handlers
app = Flask(__name__)
socketio = SocketIO(app, logger=False, engineio_logger=False)

@socketio.on('message')
def handle_message(data):
    print('received message: ' + str(data))

# @socketio.on('stop')  #stop server from client side
# def stopServer():

@socketio.on('customPong')
def getLatency(data):
    global pingT
    global pinged
    if pinged:
        lat = str(time.time() - pingT)
        print("Latency = " + lat  + " sec")
    pinged = False

@socketio.on("desiredStrikerLocation")
def rxDesiredCoords(data):
    temp = data.split(',')
    desiredX = float(temp[0])
    desiredY = float(temp[1])
    print("DesiredX= ", desiredX)
    print("DesiredY= ", desiredY)


#functions for server
def pingTest():
    print("Performing latency test...")
    global pingT
    global pinged
    pinged = True
    pingT = time.time()
    socketio.emit("customPing","1"*(128+1))	#approximate size of a float,float emit

def runServer():
    socketio.run(app, host='0.0.0.0')

# MOTOR CONTROL --------------------------------------------------------------------------------------------------------
def runMotorControl():
    x = 247
    x_old = 247
    y=132
    y_old = 132
    print("finding an odrive...")
    my_drive = odrive.find_any()

    if my_drive.axis0.motor.is_calibrated != True:
        print("starting calibration for axis 0...")
        my_drive.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
        while my_drive.axis0.current_state != AXIS_STATE_IDLE:
            time.sleep(0.1)

    if my_drive.axis1.motor.is_calibrated != True:
        print("starting calibration for axis 1...")
        my_drive.axis1.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
        while my_drive.axis1.current_state != AXIS_STATE_IDLE:
            time.sleep(0.1)
    # PID closed loop control
    my_drive.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
    time.sleep(0.1)
    my_drive.axis0.controller.config.input_mode = INPUT_MODE_POS_FILTER
    time.sleep(0.1)

    my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
    time.sleep(0.1)
    my_drive.axis1.controller.config.input_mode = INPUT_MODE_POS_FILTER
    time.sleep(0.1)

    del_x = x - x_old
    del_y = y - y_old

    print("Delta X:"+str(del_x)+" Delta Y:"+str(del_y))
    my_drive.axis1.controller.input_pos = -(del_x + del_y)
    my_drive.axis0.controller.input_pos = -(del_x - del_y)

# for live video
frameWidth = 640
frameHeight = 480
cap = cv2.VideoCapture(0)
cap.set(3, frameWidth)
cap.set(4, frameHeight)
# live video


# set up array that hold 4 sets of coordinates
circles = np.zeros((4,2), int)
counter = 0

stage2 = 0  # transition to stage 2
pts1 = 0
pts2 = 0   # store xy of perspective transform
h_min = [ [0], [0], [0] ]
h_max = [ [0], [0], [0] ]
s_min = [ [0], [0], [0] ]
s_max = [ [0], [0], [0] ]
v_min = [ [0], [0], [0] ]
v_max = [ [0], [0], [0] ]   # hold hsv values

yuv_count = 0    # index for h_min[ [], [], [] ]

switch1 = 'Good? \n->1'

argsBuffer = 64  # for args["buffer"] we copied from old code

HSV_number = 1   # counter for HSV window function

onetime = 1  # for preset window

##################################### - HSV trackbar window
# # create window
# cv2.namedWindow("HSV")
# cv2.resizeWindow("HSV", 710, 350)
# # add 6 trackbars
# cv2.createTrackbar("HUE min", "HSV", 0, 179, empty)
# cv2.createTrackbar("HUE max", "HSV", 179, 179, empty)
# cv2.createTrackbar("SAT min", "HSV", 0, 255, empty)
# cv2.createTrackbar("SAT max", "HSV", 255, 255, empty)
# cv2.createTrackbar("VALUE min", "HSV", 0, 255, empty)
# cv2.createTrackbar("VALUE max", "HSV", 255, 255, empty)
# # add exit condition
# switch1 = 'Good? \n->1'
# cv2.createTrackbar(switch1, "HSV", 0, 1, empty)
# #####################################

def empty(a):
    pass


def mousePoints(event, x, y, flags, params):
    global counter
    if event == cv2.EVENT_LBUTTONDOWN:
        circles[counter] = x,y
        counter = counter + 1
        print(circles)


def make_preset_window():
    # create window
    cv2.namedWindow("Preset Menu - Slide to load presets")
    cv2.resizeWindow("Preset Menu - Slide to load presets", 600, 150)
    # add preset option
    cv2.createTrackbar("Slide >  ", "Preset Menu - Slide to load presets", 0, 1, empty)


def make_HSV_window():
    # create window
    cv2.namedWindow("HSV")
    cv2.resizeWindow("HSV", 710, 350)
    # add 6 trackbars
    cv2.createTrackbar("HUE min", "HSV", 0, 179, empty)
    cv2.createTrackbar("HUE max", "HSV", 179, 179, empty)
    cv2.createTrackbar("SAT min", "HSV", 0, 255, empty)
    cv2.createTrackbar("SAT max", "HSV", 255, 255, empty)
    cv2.createTrackbar("VALUE min", "HSV", 0, 255, empty)
    cv2.createTrackbar("VALUE max", "HSV", 255, 255, empty)
    # add exit condition
    switch1 = 'Good? \n->1'
    cv2.createTrackbar(switch1, "HSV", 0, 1, empty)





while True:

    # for live video
    _, img = cap.read()
    #cv2.imshow("video", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # place circles
    if counter != 4:
        cv2.putText(img, "click 4 corners of table", (120, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)
        cv2.putText(img, "TopLeft, TopRight, BottomLeft, BottomRight ", (90, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 0, 0), 2)

    # once 4 points selected it will create warp feed
    if counter == 4:
        width, height = 640,480
        pts1 = np.float32([ circles[0], circles[1], circles[2], circles[3] ])
        pts2 = np.float32([ [0,0], [width,0], [0,height], [width,height] ])   #
        matrix = cv2.getPerspectiveTransform(pts1,pts2)
        imgOutput = cv2.warpPerspective(img, matrix, (width,height))
        #cv2.imshow("warp feed", imgOutput)  # display warp feed
        coords1 = str(circles[0]) + str(circles[1])
        coords2 = str(circles[2]) + str(circles[3])
        stage2 = 1                                           # stage 2 = 1
        cv2.destroyWindow("og")

    # used to place circles wherever you click
    for i in range(0, 4):
        cv2.circle(img, (circles[i][0], circles[i][1]), 3, (50, 50, 250), cv2.FILLED)

    # enter stage 2
    # this stage loops through 3 times, once for each object were trakcing
    if stage2 == 1:

        if onetime==1:
            make_preset_window()
            onetime = 2;

        # make first HSV window
        if HSV_number==1 or HSV_number==3 or HSV_number==5:
            make_HSV_window()
            HSV_number = HSV_number + 1   # set HSV_number = 2

        imgHSV = cv2.cvtColor(imgOutput, cv2.COLOR_BGR2HSV)

        # pull trackbar values into variables
        h_min[yuv_count] = cv2.getTrackbarPos("HUE min", "HSV")
        h_max[yuv_count] = cv2.getTrackbarPos("HUE max", "HSV")
        s_min[yuv_count] = cv2.getTrackbarPos("SAT min", "HSV")
        s_max[yuv_count] = cv2.getTrackbarPos("SAT max", "HSV")
        v_min[yuv_count] = cv2.getTrackbarPos("VALUE min", "HSV")
        v_max[yuv_count] = cv2.getTrackbarPos("VALUE max", "HSV")

        # create mask
        lower = np.array([h_min[yuv_count], s_min[yuv_count], v_min[yuv_count]])
        upper = np.array([h_max[yuv_count], s_max[yuv_count], v_max[yuv_count]])
        mask = cv2.inRange(imgHSV, lower, upper)
        result = cv2.bitwise_and(imgOutput, imgOutput, mask=mask)

        # display msg to user
        if yuv_count == 0:
            cv2.putText(imgOutput, "1) PUCK", (130, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 78, 0), 2)
        if yuv_count == 1:
            cv2.putText(imgOutput, "2) ROBOT", (130, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 78, 0), 2)
        if yuv_count == 2:
            cv2.putText(imgOutput, "3) HUMAN", (130, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 78, 0), 2)

        mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
        cv2.putText(imgOutput, "Move taskbars until only", (130, 288), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 0, 0), 2)
        cv2.putText(imgOutput, "your object is available", (130, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 0, 0), 2)
        hstack1 = np.hstack([imgOutput, mask, result])
        cv2.imshow("Original - Mask - Result", hstack1)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        done1 = cv2.getTrackbarPos(switch1, "HSV")

        preset_done = cv2.getTrackbarPos("Slide >  ", "Preset Menu - Slide to load presets")

        if preset_done == 1:
            # for object 1  # puck
            h_min[0] = 9
            h_max[0] = 45
            s_min[0] = 55
            s_max[0] = 125
            v_min[0] = 140
            v_max[0] = 196
            # for object 2 # robot
            h_min[1] = 62
            h_max[1] =93
            s_min[1] =47
            s_max[1] =135
            v_min[1] =106
            v_max[1] =187
            # for object 3 # human
            h_min[2] =119
            h_max[2] =136
            s_min[2] =29
            s_max[2] =108
            v_min[2] =138
            v_max[2] =207

            cv2.destroyAllWindows()
            break;



            # stage transition
        if done1 == 1 and HSV_number<6:
            cv2.destroyWindow("HSV")
            HSV_number = HSV_number + 1   # set HSV_number = 3
            yuv_count = yuv_count + 1
            done1 = 0

        # exit condition
        if done1 == 1 and HSV_number ==6:
            cv2.destroyAllWindows()
            break;


    # both below must have same name "og"
    if stage2 != 1:
        cv2.imshow("og", img)
        cv2.setMouseCallback("og", mousePoints)

    cv2.waitKey(1)









#-----------------------------------------------------------------------------------------------------------------------#
# Main part

#start server
threading.Thread(target=runServer).start()

#start motor control
threading.Thread(target=runMotorControl).start()

cv2.destroyAllWindows()

while True:

    _, img = cap.read()
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    pts11 = deque([], argsBuffer)
    pts22 = deque([], argsBuffer)
    pts33 = deque([], argsBuffer)

    width, height = 640, 480
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgOutput = cv2.warpPerspective(img, matrix, (width, height))
    #cv2.imshow("warp feed", imgOutput)  # display warp feed

    blurred = cv2.GaussianBlur(imgOutput, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)



    # Track Object 1 -------------------------------------------------------------------

    lowerBound1 = (h_min[0], s_min[0], v_min[0])
    upperBound1 = (h_max[0], s_max[0], v_max[0])

    mask11 = cv2.inRange(hsv, lowerBound1, upperBound1)
    mask11 = cv2.erode(mask11, None, iterations=1)
    mask11 = cv2.dilate(mask11, None, iterations=1)

    cnts1 = cv2.findContours(mask11.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts1 = imutils.grab_contours(cnts1)
    center1 = None

    if len(cnts1) > 0:
        # find the largest contour in the mask, then use it to compute the minimum enclosing circle and centroid
        c1 = max(cnts1, key=cv2.contourArea)
        ((x1, y1), radius1) = cv2.minEnclosingCircle(c1)
        M1 = cv2.moments(c1)
        center1 = (int(M1["m10"] / M1["m00"]), int(M1["m01"] / M1["m00"]))

        msg1 = str(x1) + "," + str(y1)
        print("1= ", msg1)
        socketio.emit('updatePuck', msg1)

        # only proceed if the radius meets a minimum size
        if radius1 > 10:
            # draw the circle and centroid on the frame, then update the list of tracked points
            cv2.circle(imgOutput, (int(x1), int(y1)), int(radius1), (0, 255, 255), 2)
            cv2.circle(imgOutput, center1, 5, (0, 0, 255), -1)
        # update the points queue
    pts11.appendleft(center1)

    # loop over the set of tracked points
    for i in range(1, len(pts11)):
        # if either of the tracked points are None, ignore them
        if pts11[i - 1] is None or pts11[i] is None:
            continue
        # otherwise, compute the thickness of the line and draw the connecting lines
        thickness1 = int(np.sqrt( argsBuffer / float(i + 1)) * 2.5)
        cv2.line(imgOutput, pts11[i - 1], pts11[i], (0, 0, 255), thickness1)

    # show the frame to our screen
    cv2.imshow("Snipe-E Tracking Feed", imgOutput)
    key = cv2.waitKey(1) & 0xFF
    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break



    # Track Object 2 --------------------------------------------------------  Robot

    lowerBound2 = (h_min[1], s_min[1], v_min[1])
    upperBound2 = (h_max[1], s_max[1], v_max[1])

    mask22 = cv2.inRange(hsv, lowerBound2, upperBound2)
    mask22 = cv2.erode(mask22, None, iterations=1)
    mask22 = cv2.dilate(mask22, None, iterations=1)

    cnts2 = cv2.findContours(mask22.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts2 = imutils.grab_contours(cnts2)
    center2 = None

    if len(cnts2) > 0:
        # find the largest contour in the mask, then use it to compute the minimum enclosing circle and centroid
        c2 = max(cnts2, key=cv2.contourArea)
        ((x2, y2), radius2) = cv2.minEnclosingCircle(c2)
        M2 = cv2.moments(c2)
        center2 = (int(M2["m10"] / M2["m00"]), int(M2["m01"] / M2["m00"]))

        msg2 = str(x2) + "," + str(y2)
        # print("2= ", msg2)
        socketio.emit('updateRobot', msg2)

        # only proceed if the radius meets a minimum size
        if radius2 > 10:
            # draw the circle and centroid on the frame, then update the list of tracked points
            cv2.circle(imgOutput, (int(x2), int(y2)), int(radius2), (0, 255, 255), 2)
            cv2.circle(imgOutput, center2, 5, (0, 0, 255), -1)
        # update the points queue
    pts22.appendleft(center2)

    # loop over the set of tracked points
    for i in range(1, len(pts22)):
        # if either of the tracked points are None, ignore them
        if pts22[i - 1] is None or pts22[i] is None:
            continue
        # otherwise, compute the thickness of the line and draw the connecting lines
        thickness2 = int(np.sqrt(argsBuffer / float(i + 1)) * 2.5)
        cv2.line(imgOutput, pts22[i - 1], pts22[i], (0, 0, 255), thickness2)

    # show the frame to our screen
    cv2.imshow("Snipe-E Tracking Feed", imgOutput)
    key = cv2.waitKey(1) & 0xFF
    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break




    # Track Object 3 --------------------------------------------------------------  Human

    lowerBound3 = (h_min[2], s_min[2], v_min[2])
    upperBound3 = (h_max[2], s_max[2], v_max[2])

    mask33 = cv2.inRange(hsv, lowerBound3, upperBound3)
    mask33 = cv2.erode(mask33, None, iterations=1)
    mask33 = cv2.dilate(mask33, None, iterations=1)

    cnts3 = cv2.findContours(mask33.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts3 = imutils.grab_contours(cnts3)
    center3 = None

    if len(cnts3) > 0:
        # find the largest contour in the mask, then use it to compute the minimum enclosing circle and centroid
        c3 = max(cnts3, key=cv2.contourArea)
        ((x3, y3), radius3) = cv2.minEnclosingCircle(c3)
        M3 = cv2.moments(c3)
        center3 = (int(M3["m10"] / M3["m00"]), int(M3["m01"] / M3["m00"]))

        msg3 = str(x3) + "," + str(y3)
        # print("3= ", msg3)
        socketio.emit('updateHuman', msg3)

        # only proceed if the radius meets a minimum size
        if radius3 > 10:
            # draw the circle and centroid on the frame, then update the list of tracked points
            cv2.circle(imgOutput, (int(x3), int(y3)), int(radius3), (0, 255, 255), 2)
            cv2.circle(imgOutput, center3, 5, (0, 0, 255), -1)
        # update the points queue
    pts33.appendleft(center3)

    # loop over the set of tracked points
    for i in range(1, len(pts33)):
        # if either of the tracked points are None, ignore them
        if pts33[i - 1] is None or pts33[i] is None:
            continue
        # otherwise, compute the thickness of the line and draw the connecting lines
        thickness3 = int(np.sqrt(argsBuffer / float(i + 1)) * 2.5)
        cv2.line(imgOutput, pts33[i - 1], pts33[i], (0, 0, 255), thickness3)

    # show the frame to our screen
    cv2.imshow("Snipe-E Tracking Feed", imgOutput)
    key = cv2.waitKey(1) & 0xFF
    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break





# END OF TRACKING ---------------------------------------------------------------------------------------------------------------------

cv2.destroyAllWindows()

