#!/usr/bin/python

import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
import signal
import getopt
import sys
import datetime
import os
import time
from time import sleep # Import the sleep function from the time module

slackHook = "https://hooks.slack.com/services/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"

def nowStr():
    return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")

def nowH():
    return datetime.datetime.now().strftime("%H")

def log(message):
    slack(nowStr() + message)

def slack(message):
    #log(message)
    print message
    os.popen("slack.sh '" + message + "'");

def forceExit(sig = False, frame = False):
    log("exiting.")
    off()
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, forceExit)
signal.signal(signal.SIGTERM, forceExit)
signal.pause

GPIO.setwarnings(True) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering

oPin = [23, 21, 19, 15, 13, 11]
iPin = [26, 24, 22, 12, 10, 8]

oSensor = 3
oPump = 5

GPIO.setup(oSensor, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(oPump, GPIO.OUT, initial=GPIO.LOW)

for x in oPin:
    GPIO.setup(x, GPIO.OUT, initial=GPIO.LOW)
    
for x in iPin:
    GPIO.setup(x, GPIO.IN)
    
def off():
    for x in oPin:
        GPIO.output(x, GPIO.LOW)
    GPIO.output(oPump, GPIO.LOW)
    GPIO.output(oSensor, GPIO.LOW)

def isDry(index, upseconds = 0.1):
    off()
    GPIO.output(oSensor, GPIO.HIGH)
    GPIO.output(oPin[index], GPIO.HIGH)
    sleep(upseconds)
    ret = GPIO.input(iPin[index])
    if (ret == 1):
        sleep(upseconds)
        ret = GPIO.input(iPin[index])
    off()
    log("sensor " + str(index) + " = " + str(ret))
    return ret

def startPump(index, upseconds = 3):
    off()
    GPIO.output(oSensor, GPIO.LOW)
    GPIO.output(oPump, GPIO.HIGH)
    GPIO.output(oPin[index], GPIO.HIGH)
    log("Started pump " + str(index) + " (`" + str(upseconds) + "sec`)")
    sleep(upseconds)
    log("Stopped pump " + str(index))
    off()

def sensorTest(upseconds = 0.1):
    for i in range(len(oPin)):
      oneSensorTest(i, upseconds)
    
def oneSensorTest(index, upseconds = 0.1):
    ret = isDry(index, upseconds)

def pumpTest(delay = 0.5, upseconds = 0.5):
    for i in range(5):
        log("Checking pump " + str(i))
        startPump(i, upseconds)
        sleep(delay)
  
def pi_temp():
    temp = os.popen("vcgencmd measure_temp").readline().strip()
    return temp.replace("temp=","").replace("'C","")

def check_temperature():
    piTemp = float(pi_temp())
    if (piTemp > 60.0):
        log("WARNING: temperature too high. `piTemp=" + str(piTemp) + "`")
    else:
        log("piTemp = " + str(piTemp))

def auto():
    onTime = 0
    sleepSeconds = 6
    resetInterval = 6 * 3600
    maxRelay = 15

    relay = [0, 0, 0, 0]
    pTime = [0, 0, 0, 0]
    upTime = [3, 3, 3, 3]

    while onTime < 3600: # =1hour
        check_temperature()

        log("onTime = " + str(onTime) + "sec")

        for i in range(0, 4):
            h = int(nowH())
            if (4 >= h) or (h >= 23):
                log("Quiet period")
                break;

            if isDry(i):
                relay[i] += 1
                log("relay " + str(i) + " = " + str(relay[i]))

                #reset after ca. 6-hours of "dry-period"
                if ((relay[i] - maxRelay) * sleepSeconds) > resetInterval:
                    print("Reseting relay " + str(i) + " (was " + str(relay[i]) + ")")
                    relay[i] = 1

                if relay[i] == maxRelay + 1:
                    log("WARNING: relay too high. `relay " + str(i) + " = " + str(relay[i]) + "`")
                elif relay[i] < maxRelay:
                    pTime[i] += upTime[i]
                    log("pTime " + str(i) + " = " + str(pTime[i]))
                    startPump(i, upTime[i])
                    onTime += upTime[i]

            else:
                relay[i] = 0
          
        log("Going to sleep " + str(sleepSeconds) + "sec")
        sleep(sleepSeconds)   
      
def main(argv):

    try:
        opts, args = getopt.getopt(argv,"ap:sx",["ifile=","ofile="])
    except getopt.GetoptError:
        print('invalid arguments')
        forceExit()

    for opt, arg in opts:
        log("`Starting " + opt + "`")
        if opt in ("-a", "--auto"):
            auto()
        elif opt in ("-p", "--pumptest"):
            startPump(arg, 60)
        elif opt in ("-s", "--sensortest"):
            sensorTest(upseconds = 0.1)
        elif opt in ("-x", "--off"):
            off()
    forceExit()

main(sys.argv[1:])

#os.system("shutdown") # schedule system shutdown (requires root)

