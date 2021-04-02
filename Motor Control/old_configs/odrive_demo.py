#!/usr/bin/env python3
"""
Example usage of the ODrive python library to monitor and control ODrive devices
"""

from __future__ import print_function

import odrive
from odrive.enums import *
import time
import math

# Find a connected ODrive (this will block until you connect one)
print("finding an odrive...")
my_drive = odrive.find_any()

# Find an ODrive that is connected on the serial port /dev/ttyUSB0
#my_drive = odrive.find_any("serial:/dev/ttyUSB0")

# Calibrate motor and wait for it to finish
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
#my_drive.axis0.controller.config.input_mode = INPUT_MODE_POS_FILTER
time.sleep(0.1)

my_drive.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
time.sleep(0.1)
#my_drive.axis1.controller.config.input_mode = INPUT_MODE_POS_FILTER
time.sleep(0.1)



# # To read a value, simply read the property
# print("Bus voltage is " + str(my_drive.vbus_voltage) + "V")

# # Or to change a value, just assign to the property
# my_drive.axis0.controller.input_pos = 3.14

# print("Position setpoint is " + str(my_drive.axis0.controller.pos_setpoint))

# # And this is how function calls are done:
# for i in [1,2,3,4]:
#     print('voltage on GPIO{} is {} Volt'.format(i, my_drive.get_adc_voltage(i)))

# A sine wave to test
t0 = time.monotonic()

#start_liveplotter(lambda:[my_drive.axis0.encoder.pos_estimate, my_drive.axis0.controller.pos_setpoint])

while True:
   # setpoint = 10000.0 * math.sin((time.monotonic() - t0)*2)
    set_inp = input("Enter Setpoint: \n")
    setpoint =  float(set_inp)
    print("goto " + str(int(setpoint)))
    my_drive.axis1.controller.input_pos = setpoint
    my_drive.axis0.controller.input_pos = setpoint + 0.25
    time.sleep(1)

