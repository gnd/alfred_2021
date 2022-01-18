#!/usr/bin/python3

import math
import argparse
from time import sleep 
import RPi.GPIO as GPIO
from osc4py3.as_eventloop import *
from osc4py3 import oscmethod as osm

# set mode to BCM 
GPIO.setmode(GPIO.BOARD)

# define solenoid 01 - solenoid 12 pins
sol_01 = 37
sol_02 = 35
sol_03 = 33
sol_04 = 31
sol_05 = 29
sol_06 = 23
sol_07 = 21
sol_08 = 19
sol_09 = 15
sol_10 = 13
sol_11 = 11
sol_12 = 7

# set pins as output
GPIO.setup(sol_01, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sol_02, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sol_03, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sol_04, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sol_05, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sol_06, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sol_07, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sol_08, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sol_09, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sol_10, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sol_11, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sol_12, GPIO.OUT, initial=GPIO.LOW)

# simple cycle function
def cycle_pin(pin, high_time):
    print("PIN ON: {}".format(pin))
    GPIO.output(pin, GPIO.HIGH)
    sleep(high_time)
    print("PIN OFF: {}".format(pin))
    GPIO.output(pin, GPIO.LOW)

def translate_notes(pin):
    out = sol_01
    pin = int(pin)

    if (pin == 1):
        out = sol_01
    if (pin == 2):
        out = sol_02
    if (pin == 3):
        out = sol_03
    if (pin == 4):
        out = sol_04
    if (pin == 5):
        out = sol_05
    if (pin == 6):
        out = sol_06
    if (pin == 7):
        out = sol_07
    if (pin == 8):
        out = sol_08
    if (pin == 9):
        out = sol_09
    if (pin == 10):
        out = sol_10
    if (pin == 11):
        out = sol_11
    if (pin == 12):
        out = sol_12

    return out
    
def noteon(pin):
    pin = translate_notes(pin)
    print("PIN ON: {}".format(pin))
    GPIO.output(pin, GPIO.HIGH)

def noteoff(pin):
    pin = translate_notes(pin)
    print("PIN OFF: {}".format(pin))
    GPIO.output(pin, GPIO.LOW)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="192.168.0.192", help="The ip to listen on")
    parser.add_argument("--port", type=int, default=6666, help="The port to listen on")
    args = parser.parse_args()
  
    osc_startup()

    # Make server channels to receive packets.
    osc_udp_server(args.ip, args.port, "rpi")

    # Associate Python functions with message address patterns, using default
    # argument scheme OSCARG_DATAUNPACK.
    osc_method("/note/on", noteon)
    osc_method("/note/off", noteoff)
    
    # self test
    cycle_pin(sol_01, 0.5)
    cycle_pin(sol_02, 0.5)
    cycle_pin(sol_03, 0.5)
    cycle_pin(sol_04, 0.5)
    cycle_pin(sol_05, 0.5)
    cycle_pin(sol_06, 0.5)
    cycle_pin(sol_07, 0.5)
    cycle_pin(sol_08, 0.5)
    cycle_pin(sol_09, 0.5)
    cycle_pin(sol_10, 0.5)
    cycle_pin(sol_11, 0.5)
    cycle_pin(sol_12, 0.5)

    # Periodically call osc4py3 processing method in your event loop.
    finished = False
    cycle = True
    while not finished:
        osc_process()
        if cycle:
            cycle_pin(sol_01, 0.5)
            cycle_pin(sol_02, 0.5)
            cycle_pin(sol_03, 0.5)
            cycle_pin(sol_04, 0.5)
            cycle_pin(sol_05, 0.5)
            cycle_pin(sol_06, 0.5)
            cycle_pin(sol_07, 0.5)
            cycle_pin(sol_08, 0.5)
            cycle_pin(sol_09, 0.5)
            cycle_pin(sol_10, 0.5)
            cycle_pin(sol_11, 0.5)
            cycle_pin(sol_12, 0.5)
        
    # Properly close the system
    osc_terminate()
