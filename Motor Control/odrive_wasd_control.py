
import pygame
import sys
import odrive
from odrive.enums import *
import time
import math




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


my_drive.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
time.sleep(0.1)
my_drive.axis0.controller.config.input_mode = INPUT_MODE_POS_FILTER
time.sleep(0.1)

my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
time.sleep(0.1)
my_drive.axis1.controller.config.input_mode = INPUT_MODE_POS_FILTER
time.sleep(0.1)
 
pygame.init() 
  
res_x = 400
res_y = 320

win = pygame.display.set_mode((res_x, res_y)) 
  

pygame.display.set_caption("Snipe-E") 
  
# object current co-ordinates  
x = res_x/2
y = res_y/2

# dimensions of the object  
radius = 5

# velocity / speed of movement 
vel = 1

# Indicates pygame is running 
run = True
font = pygame.font.Font('freesansbold.ttf', 16) 


#Safe Operation region
xlim = 55
ylim = 27

#stopping consitions
x_stop = res_x/2-(xlim/2)
y_stop = res_y/2-(ylim/2)

x_gui = x
y_gui = y

x_old = x
y_old = y

#ODrive Scaling
O_scale = 0.25
# infinite loop  
while run: 
    # creates time delay of 30ms  
    pygame.time.delay(30) 
         
    for event in pygame.event.get(): 
          
        if event.type == pygame.QUIT: 
            run = False

    keys = pygame.key.get_pressed() 
      
    if keys[pygame.K_ESCAPE]:        
        pygame.quit()
        sys.exit()
    if keys[pygame.K_a] and x_gui>x_stop+radius:
    	x_gui -= vel
    	x -= (vel*O_scale)
    	# print("X vals: " + str(x_gui)+","+str(x))
    if keys[pygame.K_d] and x_gui<x_stop+xlim-radius: 
    	x_gui += vel
    	x += (vel*O_scale)
    if keys[pygame.K_w] and y_gui>y_stop+radius:
    	y_gui -= vel
    	y -= (vel*O_scale)
    if keys[pygame.K_s] and y_gui<y_stop+ylim-radius: 
    	y_gui += vel
    	y += (vel*O_scale)


    win.fill((0, 0, 0)) 
      
    pygame.draw.circle(win, (255, 0, 0), (x_gui, y_gui),radius) 

    text = font.render(str(x_gui)+","+str(y_gui), True, (0,0,255))
   
    pygame.draw.rect(win,(0,255,0),(res_x/2-(xlim/2),res_y/2-(ylim/2),xlim,ylim),1)

    # for the coordinates display
    textRect = text.get_rect()
    textRect.center = (res_x - 50, res_y-25)
    win.blit(text,textRect)
    
    pygame.display.update() 


    #---------------Odrive Commands-------------

    del_x = x - x_old
    del_y = y - y_old

    print("Delta X:"+str(x)+" Delta Y:"+str(y))
    my_drive.axis1.controller.input_pos = -(del_x + del_y)
    my_drive.axis0.controller.input_pos = -(del_x - del_y)


  
  
pygame.quit() 







