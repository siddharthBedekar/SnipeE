#image processing imports
from collections import deque
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time
import math 

#server imports
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit

def set_res(cap, x,y):
    cap.set(cv.CV_CAP_PROP_FRAME_WIDTH, int(x))
    cap.set(cv.CV_CAP_PROP_FRAME_HEIGHT, int(y))
    return str(cap.get(cv.CV_CAP_PROP_FRAME_WIDTH)),str(cap.get(cv.CV_CAP_PROP_FRAME_HEIGHT))
	
def set_res(cap2, x2,y2):
    cap2.set(cv.CV_CAP_PROP_FRAME_WIDTH, int(x2))
    cap2.set(cv.CV_CAP_PROP_FRAME_HEIGHT, int(y2))
    return str(cap2.get(cv.CV_CAP_PROP_FRAME_WIDTH)),str(cap2.get(cv.CV_CAP_PROP_FRAME_HEIGHT))

print("Starting Server...")

msg ='x1y1'
msg2 = 'x2y2'

def runServer():
	socketio.run(app, host='0.0.0.0')

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def hello(name=None):
    return render_template('game.html')

@socketio.on('message')
def handle_message(data):
    print('received message: ' + str(data))
    emit('updatePuck', msg)


def puckThis(data):
    emit('updatePuck', str(data))

if __name__ == '__main__':
    # socketio.run(app)
    threading.Thread(target=runServer).start() #start on main thread


print("...Server started")
print("-----------------------------")
print("Starting image detection code...")


px = 0
py = 0

px2 = 0
py2 = 0

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=64, help="max buffer size")
args = vars(ap.parse_args())

# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points




# yellow ticket - noubar              
#   greenLower = (16, 98, 53)
#   greenUpper = (63,255,255)   # detects yellow ticket great, if no ticket gets green great              


# green patch  - noubar # not working  
#   strikerLower = (40,78,47)    
#   strikerUpper = (169,162,149)   #good green decector, sorta figity 


# yellow paper          # green paper     # brown paper   # dark blue paper
# min=(98,155,172)      # (134,153,107)   # (91,98,148)    # (120,40,30)
# max=(164,195,208)     # (167,193,171)   # (146,157,188)   # (255,130,140)


# mask works on yellow ticket - object1 -    PINK CENTER
greenLower =  (16, 98, 53)
greenUpper =  (63,255,255)   


# mask considering all above masks  # for object 2
strikerLower = (40,78,47)    
strikerUpper = (169,162,149)   #good green decector, sorta figity 




pts = deque(maxlen=args["buffer"])
pts2 = deque(maxlen=args["buffer"]) 

# if a video path was not supplied, grab the reference
# to the webcam
if not args.get("video", False):
	vs = VideoStream(src=0, resolution=(1920,1024)).start()
# otherwise, grab a reference to the video file
else:
	vs = cv2.VideoCapture(args["video"])
# allow the camera or video file to warm up
time.sleep(2.0)

# keep looping
while True:
	# grab the current frame
	frame = vs.read()
	# handle the frame from VideoCapture or VideoStream
	frame = frame[1] if args.get("video", False) else frame
	# if we are viewing a video and we did not grab a frame,
	# then we have reached the end of the video
	if frame is None:
		break
		
	# resize the frame, blur it, and convert it to the HSV color space
	#frame = imutils.resize(frame, width=1000)                               #this was commented before, we uncommented when we mounted *NOUBAR

	##################################################### - perspective transofrmation
	bound1 = np.float32([[2,36],[636,28],[0,400],[638,377]])
	bound2 = np.float32([[0,0],[636,0],[0,400],[636,400]])
	M = cv2.getPerspectiveTransform(bound1,bound2)                         # commented out when mounted *NOUBAR 
	
	frame = cv2.warpPerspective(frame,M,(640,480))                         # commented out when mounted *NOUBAR 
    
	blurred = cv2.GaussianBlur(frame, (11, 11), 0)
	
	hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	
	#mask1 = puck (green)
	mask = cv2.inRange(hsv, greenLower, greenUpper)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)
	
	#mask2 = striker ( x )                          # noubar
	mask2 = cv2.inRange(hsv, strikerLower, strikerUpper)
	mask2 = cv2.erode(mask2, None, iterations=2)
	mask2 = cv2.dilate(mask2, None, iterations=2)

	
	
	
	
	
	########### COMPUTING CONTURE 1 ################ - 1 (red frame / pink centre)
	
	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	center = None
	
	# only proceed if at least one contour was found
	if len(cnts) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

		#debug
		#print(abs(x-px))
		if (abs(x-px) > 10 or abs(y-py) > 10):
			px = x
			print("( x1:", round(x),", y1:", round(y),")")
			msg=str(round(x))+","+str(round(y))
			#puckThis(msg)
			socketio.emit('updatePuck', msg)


		# only proceed if the radius meets a minimum size
		if radius > 20:
			# draw the circle and centroid on the frame,
			# then update the list of tracked points
			cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
			cv2.circle(frame, center, 5, (0, 0, 255), -1)
	# update the points queue
	pts.appendleft(center)


	# loop over the set of tracked points
	for i in range(1, len(pts)):
		# if either of the tracked points are None, ignore
		# them
		if pts[i - 1] is None or pts[i] is None:
			continue
		# otherwise, compute the thickness of the line and
		# draw the connecting lines
		thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
		cv2.line(frame, pts[i - 1], pts[i], (255, 0, 255), thickness)   # change color of centre dot (now= pink)
	# show the frame to our screen
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF
	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break
		
		
		
		
	############### COMPUTING CONTURE 2 ################ - 2
	
	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	cnts2 = cv2.findContours(mask2.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cnts2 = imutils.grab_contours(cnts2)
	center2 = None
	
	# only proceed if at least one contour was found
	if len(cnts2) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		c2 = max(cnts2, key=cv2.contourArea)
		((x2, y2), radius2) = cv2.minEnclosingCircle(c2)
		M = cv2.moments(c2)
		center2 = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

		#debug
		#print(abs(x2-px2))
		if (abs(x2-px2) > 10 or abs(y2-py2) > 10):
			px2 = x2
			#truncate(x2,2)
			#truncate(y2,2)
			print("( x2:",round(x2),", y2:",round(y2),")")
			msg=str(round(x2))+","+str(round(y2))
			#puckThis(msg)
			socketio.emit('updatePuck2', msg2)


		# only proceed if the radius meets a minimum size
		if radius2 > 20:
			# draw the circle and centroid on the frame,
			# then update the list of tracked points
			cv2.circle(frame, (int(x2), int(y2)), int(radius2), (0, 255, 255), 2)
			cv2.circle(frame, center2, 5, (0, 0, 255), -1)
	# update the points queue
	pts2.appendleft(center2)


	# loop over the set of tracked points
	for i in range(1, len(pts2)):
		# if either of the tracked points are None, ignore
		# them
		if pts2[i - 1] is None or pts2[i] is None:
			continue
		# otherwise, compute the thickness of the line and
		# draw the connecting lines
		thickness2 = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
		cv2.line(frame, pts2[i - 1], pts2[i], (0, 0, 255), thickness2)  
	# show the frame to our screen
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF
	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break
		
		
		
		
	###################  END OF 2  #######################
		
		
		
		
		
		
# if we are not using a video file, stop the camera video stream
if not args.get("video", False):
	vs.stop()
# otherwise, release the camera
else:
	vs.release()
# close all windows
cv2.destroyAllWindows()
