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

#for storing preset
from ast import literal_eval as make_tuple


# SERVER ---------------------------------------------------------------------------------------------------------------

#globals for server

pingT = 0
pinged = False



#Tracking Center vals
#Puck
x1 = 0
y1 = 0
#Robot
x2 = 0
y2 = 0
#human 
x3 = 0
y3 = 0

first_run=True


#Input Bound
rect_bound=[[48, 45],[192, 430]]


#read data globals
desiredX= rect_bound[0][0]+(rect_bound[1][0]-rect_bound[0][0])/2
desiredY= rect_bound[0][1]+(rect_bound[1][1]-rect_bound[0][1])/2

#(imgOutput, (65, 25), (142 + 65, 25 + 435), (0, 0, 255), 1)

#modes highest priority first
wasd=False
ai=False


#loadOdrive
loadO = True
o_limit_lower=[]
o_limit_x=12
o_limit_y=7
o_error=[0,0]

#calibration flag
CALIBRATING = False

#socket init and event handlers -------------------------------------------------------------------
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
    global desiredY
    global desiredX
    temp = data.split(',')
    desiredX = float(temp[0])
    desiredY = float(temp[1])


#odrive plotter

def liveplot():
    from odrive.utils import start_liveplotter
    start_liveplotter(lambda: [
    my_drive.axis0.encoder.vel_estimate,
    my_drive.axis0.encoder.pos_estimate,
    my_drive.axis1.encoder.vel_estimate,
    my_drive.axis1.encoder.pos_estimate
    ])




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
def pt_to_line(p1,v,p3):
    t=sum((p3-p1)*v)/sum((v**2))
    intercept=(p1+v*t-p3)
    return [intercept,t]

# MOTOR CONTROL --------------------------------------------------------------------------------------------------------
# def runMotorControl():
#
#     print("finding an odrive...")
#     my_drive = odrive.find_any()
#
#     if my_drive.axis0.motor.is_calibrated != True:
#         print("starting calibration for axis 0...")
#         my_drive.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
#         while my_drive.axis0.current_state != AXIS_STATE_IDLE:
#             time.sleep(0.1)
#
#     if my_drive.axis1.motor.is_calibrated != True:
#         print("starting calibration for axis 1...")
#         my_drive.axis1.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
#         while my_drive.axis1.current_state != AXIS_STATE_IDLE:
#             time.sleep(0.1)
#
#     # PID closed loop control
#     my_drive.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
#     time.sleep(0.1)
#     my_drive.axis0.controller.config.input_mode = INPUT_MODE_POS_FILTER
#     time.sleep(0.1)
#
#     my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
#     time.sleep(0.1)
#     my_drive.axis1.controller.config.input_mode = INPUT_MODE_POS_FILTER
#     time.sleep(0.1)
#
#     while True:
#         del_x = int(desiredY) - 0.8888889
#         del_x = del_x*(11.5/896.52)-5.75
#         del_y = int(desiredX) - 65.39738
#         del_y = del_y*(6.5/506.73)-3.25  #FLIPPED? OK?
#         del_a = (del_x + del_y)
#         del_b = (del_x - del_y)
#         print(del_a,del_b)
#         if (del_a - del_b < 6.5) and (del_a + del_b < 11.5) and (del_a + del_b > -11.5) and (del_a - del_b > -6.5):
#            print()
#             #print("Delta X:"+str(del_x)+" Delta Y:"+str(del_y))
#             #print("Delta A:" + str(del_a) + " Delta B:" + str(del_b))
#             #my_drive.axis1.controller.input_pos = del_a
#             #my_drive.axis0.controller.input_pos = del_b

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

# to draw boundry box
counter22 = 0
circles22 = np.zeros((2,2), int)


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

argsBuffer = 8  # for args["buffer"] we copied from old code

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

def mousePoints22(event, x, y, flags, params):
    global counter22
    if event == cv2.EVENT_LBUTTONDOWN:
        circles22[counter22] = x,y
        counter22 = counter22 + 1
        print(circles22)


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
# del_x = -(del_x * (11.6/ (rect_bound[1][1]-rect_bound[0][1])) - 5.75)
#         del_y = int(desiredX) - rect_bound[0][0]
#         del_y = del_y * (o_limit_y / (rect_bound[1][0]-rect_bound[0][0])) - 3.25  # FLIPPED? OK?

def create_Odrive_map(spos,opos):
    global rect_bound
    global o_limit_x
    global o_limit_y
    px=spos[0]-rect_bound[0][0]#distx from top left of bound
    py=spos[1]-rect_bound[0][1]#disty from top left of bound
    err_y=opos[1]-(px* (o_limit_y / (rect_bound[1][0]-rect_bound[0][0]))- o_limit_y/2)
    err_x=opos[0]+(py* (o_limit_x/ (rect_bound[1][1]-rect_bound[0][1]))-o_limit_x/2)#table cord converted to odrive cart
    return([err_x,err_y])
    



####TEMP TESTING NO threading on MOTOR
if (loadO):
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
    if(my_drive.axis0.encoder.error==0 and my_drive.axis1.encoder.error==0 ):
        print("calabration successful")
    else:
        print("error: ",my_drive.axis0.encoder.error," ",my_drive.axis1.encoder.error )

    # PID closed loop control
    my_drive.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
    time.sleep(0.1)
    my_drive.axis0.controller.config.input_mode = INPUT_MODE_TRAP_TRAJ #INPUT_MODE_POS_FILTER
    time.sleep(0.1)

    my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
    time.sleep(0.1)
    my_drive.axis1.controller.config.input_mode = INPUT_MODE_TRAP_TRAJ #INPUT_MODE_POS_FILTER
    time.sleep(0.1)
    liveplot()
    #start_liveplotter(lambda: [((my_drive.axis0.encoder.vel_estimate),(my_drive.axis0.motor.current_control.Iq_setpoint * my_drive.axis0.motor.config.torque_constant))])

if CALIBRATING:
    print("Calibrating Object Detection...")
    fwriteStr = ""
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
            pts2 = np.float32([ [0,0], [width,0], [0,height], [width,height] ])
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
                onetime = 2

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



            # stage transition
            if done1 == 1 and HSV_number<6:
                cv2.destroyWindow("HSV")
                HSV_number = HSV_number + 1   # set HSV_number = 3
                yuv_count = yuv_count + 1
                done1 = 0

            # exit condition
            if done1 == 1 and HSV_number ==6:
                tmpList = circles.tolist()

                fwriteStr += str(tmpList[0][0]) + "," + str(tmpList[0][1]) + "," +\
                             str(tmpList[1][0]) + "," + str(tmpList[1][1]) + "," +\
                             str(tmpList[2][0]) + "," + str(tmpList[2][1]) + "," +\
                             str(tmpList[3][0]) + "," + str(tmpList[3][1]) + ","

                fwriteStr += str(h_min[0]) + "," + str(h_max[0]) + ","
                fwriteStr += str(s_min[0]) + "," + str(s_max[0]) + ","
                fwriteStr += str(v_min[0]) + "," + str(v_max[0]) + ","

                fwriteStr += str(h_min[1]) + "," + str(h_max[1]) + ","
                fwriteStr += str(s_min[1]) + "," + str(s_max[1]) + "," 
                fwriteStr += str(v_min[1]) + "," + str(v_max[1]) + ","

                fwriteStr += str(h_min[2]) + "," + str(h_max[2]) + ","
                fwriteStr += str(s_min[2]) + "," + str(s_max[2]) + "," 
                fwriteStr += str(v_min[2]) + "," + str(v_max[2])

                fo = open("preset.csv", "w")
                fo.write(fwriteStr)
                fo.close()
				
                cv2.destroyAllWindows()
                break;


        # both below must have same name "og"
        if stage2 != 1:
            cv2.imshow("og", img)
            cv2.setMouseCallback("og", mousePoints)

        cv2.waitKey(1)
    
else:   # no calibration - load preset from file
    print("Loading Preset Calibration...")
    _, img = cap.read()

    fo = open("preset.csv", "r")
    fread = fo.readline()
    fo.close()

    freadArr = fread.split(",")

    #load perspective transform values
    width, height = 640,480

    pts1 = np.float32([[freadArr.pop(0),freadArr.pop(0)],
                       [freadArr.pop(0), freadArr.pop(0)],
                       [freadArr.pop(0), freadArr.pop(0)],
                       [freadArr.pop(0), freadArr.pop(0)]
                       ])

    pts2 = np.float32([ [0,0], [width,0], [0,height], [width,height] ])
    matrix = cv2.getPerspectiveTransform(pts1,pts2)
    imgOutput = cv2.warpPerspective(img, matrix, (width,height))

    #load mask thresholds
    # for object 1  # puck
    h_min[0] =int(freadArr.pop(0))
    h_max[0] = int(freadArr.pop(0))
    s_min[0] =int(freadArr.pop(0))
    s_max[0] =int(freadArr.pop(0))
    v_min[0] = int(freadArr.pop(0))
    v_max[0] = int(freadArr.pop(0))
    # for object 2 # robot
    h_min[1] =int(freadArr.pop(0))
    h_max[1] =int(freadArr.pop(0))
    s_min[1] =int(freadArr.pop(0))
    s_max[1] =int(freadArr.pop(0))
    v_min[1] =int(freadArr.pop(0))
    v_max[1] =int(freadArr.pop(0))
    # for object 3 # human
    h_min[2] =int(freadArr.pop(0))
    h_max[2] =int(freadArr.pop(0))
    s_min[2] =int(freadArr.pop(0))
    s_max[2] =int(freadArr.pop(0))
    v_min[2] =int(freadArr.pop(0))
    v_max[2] =int(freadArr.pop(0))

    if (len(freadArr) > 0): # list should be empty if all values read properly
        print("Error reading preset from file")


#-----------------------------------------------------------------------------------------------------------------------#
# Main part

#start server
threading.Thread(target=runServer).start()
#start motor control
#threading.Thread(target=runMotorControl).start()

threading.Thread()

cv2.destroyAllWindows()

#ai y point
pts11 = deque([], argsBuffer)
pts22 = deque([], argsBuffer)
pts33 = deque([], argsBuffer)
aiy= deque([], 10)
while True:

    _, img = cap.read()
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


    width, height = 640, 480
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgOutput = cv2.warpPerspective(img, matrix, (width, height))
    #cv2.imshow("warp feed", imgOutput)  # display warp feed

    blurred = cv2.GaussianBlur(imgOutput, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)





    if counter22 < 2:
        #cv2.imshow("imgOutput", imgOutput)
        cv2.setMouseCallback("imgOutput", mousePoints22)
        #cv2.putText(imgOutput, "click 2 markers on table", (120, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)

    for i in range(0, 2):
        cv2.circle(imgOutput, (circles22[i][0], circles22[i][1]), 3, (50, 50, 250), cv2.FILLED)

    cv2.rectangle(imgOutput, ( circles22[0][0], circles22[0][1]) , (circles22[1][0], circles22[1][1]), (0, 0, 255), 1)

    if counter22==2:
        cv2.destroyWindow("imgOutput")





    # draw BOUND
     #cv2.rectangle(imgOutput, (65, 25), (142 + 65, 25 + 435), (0, 0, 255), 1)


    # Track Object 1 (PUCK)-------------------------------------------------------------------

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
    #cv2.imshow("Snipe-E Tracking Feed", imgOutput)
    key = cv2.waitKey(1) & 0xFF
    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break



    # Track Object 2 (ROBOT) --------------------------------------------------------  Robot

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
        # print("STARTING X:" + str(x2) + "Y:" + str(y2))
        msg2 = str(x2) + "," + str(y2)
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
    #cv2.imshow("Snipe-E Tracking Feed", imgOutput)
    key = cv2.waitKey(1) & 0xFF
    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break




    # Track Object 3 (HUMAN) --------------------------------------------------------------  Human
    
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




    # AI calculation
    puckpos = np.array([i for i in pts11 if i])
    puckpos = puckpos[~np.isnan(puckpos).any(axis=-1)]
    strikerpos = np.array([i for i in pts22 if i])
    if (ai):
        act_time = 60
        if (puckpos.shape[0] > 2 and len(strikerpos) > 0):
            avgvel = -1 * np.average(np.diff(puckpos, axis=0), axis=0)
            speed = np.sum(np.abs(avgvel)) / 2

            try:
                if (speed > 1 and avgvel[0] < -8):#moving left
                    encount_pt = strikerpos[0][0]
                    deltax = (puckpos[0][0] - encount_pt)
                    yp2c = -deltax * avgvel[1] / avgvel[0] + puckpos[0][1]
                    cv2.line(imgOutput, tuple(puckpos[0][:].astype(int)),
                             tuple((puckpos[0][:] + avgvel * 100).astype(int)), (255, 0, 0), 5)
                    if (avgvel[1] < 0 and yp2c < 0):#top
                        yImp = abs(yp2c)
                        Xr = int(puckpos[0][0] - puckpos[0][1] * avgvel[0] / avgvel[1])
                        displace = pt_to_line(np.array([Xr, 0]), avgvel * [1, -1], strikerpos[0])[0]
                        desiredX, desiredY = strikerpos[0] + displace
                        print("reflection point", Xr)


                        cv2.line(imgOutput, (Xr, 0), (int(encount_pt), int(yImp)), (255, 0, 0), 5)
                    elif (avgvel[1] > 0 and yp2c > 480):#botte,
                        yImp = 2 * 480 - yp2c
                        Xr = int(puckpos[0][0] + (480 - puckpos[0][1]) * avgvel[0] / avgvel[1])
                        displace = pt_to_line(np.array([Xr, 480]), avgvel * [1, -1], strikerpos[0])[0]
                        desiredX, desiredY = strikerpos[0] + displace
                        cv2.line(imgOutput, (Xr, 480), (int(encount_pt), int(yImp)), (255, 0, 0), 5)
                    else:# straight
                        displace = pt_to_line(puckpos[0],avgvel,strikerpos[0])[0]
                        desiredX,desiredY=strikerpos[0]+displace

                        cv2.line(imgOutput, tuple(strikerpos[0].astype(int)), tuple((strikerpos[0]+displace).astype(int)), (255, 0, 0), 5)
                        if abs(strikerpos[0][0] - desiredX )< 100 and abs(strikerpos[0][1] - desiredY) < 100 :  # aligned
                            diff=(strikerpos[0]-puckpos[0])
                            if (act_time >np.sqrt(diff.dot(diff))/np.sqrt(avgvel.dot(avgvel))):  # puck is close

                                desiredX=desiredX-avgvel[0]/abs(avgvel[0])*80
                                desiredY=desiredY-avgvel[1]/abs(avgvel[0])*80
                        cv2.circle(imgOutput, (int(desiredX), int(desiredY)), 20, (250, 150, 250), cv2.FILLED)
                else:
                    if (avgvel[0] >-0.1 and (puckpos[0][0] > rect_bound[1][0]) or (puckpos[0][0] < rect_bound[0][0]) ):# return to default position
                        desiredY=(rect_bound[1][1]-rect_bound[0][1])/2+rect_bound[0][1]#center the striker
                        desiredX = 80


                    #if ((puckpos[0][0] > rect_bound[0][0]) and (puckpos[0][0] < rect_bound[1][0]) and abs(np.sqrt(avgvel.dot(avgvel)))<2:# not moving inside the striking area
                        #if striker#striker infront
                    #     if abs(puckpos[0][1]- strikerpos[0][1])>60:
                    #         desiredY= puckpos[0][1]
                    #     elif strikerpos[0][0]>rect_bound[0][0]+20:# it is infront of the
                    #         desiredX= rect_bound[0][0]+10
                    #     else:
                    #         desiredX=strikerpos[0][0]+20
            except OverflowError:
                print("yikes")
            except ValueError:
                print("Double Yikes")
    #print(desiredX, desiredY)

# Odrive Motor Control
    #print(desiredX,desiredY)






    #
    #
    if (first_run): #or np.mean(stiker_vel)<1 and np.nanmean(strikerpos,axis=0)): addd on error if uncommented

        del_x = int(desiredY) - rect_bound[0][1]
        #lenght of rect bound
        del_x = -(del_x * (o_limit_x/ (rect_bound[1][1]-rect_bound[0][1])) - o_limit_x/2)
        del_y = int(desiredX) - rect_bound[0][0]
        del_y = del_y * (o_limit_y / (rect_bound[1][0]-rect_bound[0][0])) - o_limit_y/2  # FLIPPED? OK?
        #print("correction")
        first_run=False
        temp_e=create_Odrive_map([strikerpos[0][0],strikerpos[0][1]],[del_x,del_y])
        for i in range(2):
            o_error[i]=o_error[i]+ temp_e[i]
        #print(o_error,strikerpos,del_x,del_y)

    #
    # WASD TESTING
    if(wasd):
         if cv2.waitKey(1) == ord('a'):
            desiredY=desiredY-10
         if cv2.waitKey(1) == ord('d'):
            desiredY=desiredY+10
         if cv2.waitKey(1) == ord('s'):
             desiredX=desiredX-10
         if cv2.waitKey(1) == ord('w'):
             desiredX=desiredX+10

    #
    # =============================================================================

    #print(desiredX,desiredY)
    if desiredY<rect_bound[0][1]:
        desiredY= rect_bound[0][1]-o_error[0] * (rect_bound[1][1] - rect_bound[0][1]) / o_limit_x
    elif (desiredY>rect_bound[1][1]):
        desiredY  = rect_bound[1][1] + o_error[0] * (rect_bound[1][1] - rect_bound[0][1]) / o_limit_x
    if desiredX<rect_bound[0][0]:
        desiredX=rect_bound[0][0]- o_error[1] * (rect_bound[1][0] - rect_bound[0][0]) / o_limit_y
    elif (desiredX>rect_bound[1][0]):
        desiredX = rect_bound[1][0]+ o_error[1] * (rect_bound[1][0] - rect_bound[0][0]) / o_limit_y
    # Use rect_bound
    cv2.rectangle(imgOutput, tuple(rect_bound[0]), tuple(rect_bound[1]), (0, 0, 255), 1)
    #
    # # draw required position
    cv2.circle(imgOutput, (int(desiredX), int(desiredY)), 5, (250, 250, 250), cv2.FILLED)

    del_x = int(desiredY) - rect_bound[0][1]
    #lenght of rect bound
    del_x = -(del_x * (o_limit_x/ (rect_bound[1][1]-rect_bound[0][1]))- o_limit_x/2)+o_error[0]
    del_y = int(desiredX) - rect_bound[0][0]
    del_y = del_y * (o_limit_y / (rect_bound[1][0]-rect_bound[0][0])) -o_limit_y/2+ o_error[1]  # FLIPPED? OK?
    #
    #
    # v_pixel_limit=100000
    #
    # if (abs(desiredY-strikerpos[0][1])<v_pixel_limit):  #in range of the stiker
    #     del_x = int(desiredY) - rect_bound[0][1]
    #     # lenght of rect bound
    #     del_x = -(del_x * (o_limit_x / (rect_bound[1][1] - rect_bound[0][1])) - 5.75) + o_error[0]
    #
    # else:   # out of range interpolate using v_pixel_limit
    #     del_x = int(np.sign(desiredY-strikerpos[0][1])*v_pixel_limit+strikerpos[0][1]) - 25
    #     del_x = -(del_x * (o_limit_x / (rect_bound[1][1] - rect_bound[0][1])) - 5.75) + o_error[0]
    #
    # if (abs(desiredX - strikerpos[0][0]) < v_pixel_limit):  # in range of the stiker
    #     del_y = int(desiredX) - rect_bound[0][0]
    #     del_y = del_y * (o_limit_y / (rect_bound[1][0] - rect_bound[0][0])) - 3.25 + o_error[1]  # FLIPPED? OK?
    #
    # else:
    #     del_y = int(np.sign(desiredX-strikerpos[0][0])*v_pixel_limit+strikerpos[0][0]) - rect_bound[0][0]
    #     del_y = del_y * (o_limit_y / (rect_bound[1][0] - rect_bound[0][0])) - 3.25 + o_error[1]  # FLIPPED? OK?

    #print(desiredXY)
    # del_x = int(desiredY) - 1
    # del_x = -(del_x * (11.5 / 398) - 5.75)
    # del_y = int(desiredX) - 65
    # del_y = del_y * (6.5 / 142) - 3.25  # FLIPPED? OK?
    # del_a = (del_x + del_y)
    # del_b = (del_x - del_y)
    #
    del_a = (del_x + del_y)
    del_b = (del_x - del_y)


    if (loadO):  # only run if loadO = True
        #print("motor vals:", del_a, del_b)
        #formula delx=1/2*(dela+delb)
        if (del_a - del_b <= o_limit_y) and (del_a + del_b <= o_limit_x) and (del_a + del_b >= -o_limit_x) and (del_a - del_b >= -o_limit_y):
            # print("Delta X:"+str(del_x)+" Delta Y:"+str(del_y))
            # print("Delta A:" + str(del_a) + " Delta B:" + str(del_b))

            my_drive.axis1.controller.input_pos = del_a
            my_drive.axis0.controller.input_pos = del_b
            #print(del_x, del_y)
        else:
            #print(del_x,del_y)
            print("error")







    # show the frame to our screen
    cv2.imshow("Snipe-E Tracking Feed", imgOutput)
    #key = cv2.waitKey(1) & 0xFF
    # if the 'q' key is pressed, stop the loop
    #if key == ord("q"):
    #    break





# END OF TRACKING ---------------------------------------------------------------------------------------------------------------------

cv2.destroyAllWindows()

