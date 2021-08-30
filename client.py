"""
Ryan Wahler

must enable camera in raspberry pi configuration first

"""

import RPi.GPIO as GPIO
from picamera import PiCamera
from time import sleep, time
import requests
import json
from datetime import datetime, timedelta

# setup variables and address to use for data transfer in send_function
addr = 'http://10.0.0.182:5000'
url = addr + '/api/upload'

# setup GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# setup output for LEDs
GPIO.setup(18, GPIO.OUT)  # white led
GPIO.setup(17, GPIO.OUT)  # blue led
GPIO.setup(23, GPIO.OUT)  # red led
W = 18
B = 17
R = 23

# setup camera and adjust focus/light

print("Setting up camera")
camera = PiCamera()
camera.start_preview()

# turn on white LED and set all leds to low
GPIO.output(R, GPIO.LOW)
GPIO.output(W, GPIO.LOW)
GPIO.output(B, GPIO.LOW)
GPIO.output(W, GPIO.HIGH)
sleep(2)

# turn off white LED
GPIO.output(W, GPIO.LOW)

# setup output for distance sensors
TRIG = 6
ECHO = 5
TRIG2 = 21
ECHO2 = 20
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(TRIG2, GPIO.OUT)
GPIO.setup(ECHO2, GPIO.IN)

# setup variables to calculate base distance on program start
base_dist1 = -1
base_dist2 = -1

# setup global vars for recording time upon car passing
time_pass1 = 0
time_pass2 = 0

# provide a constant for conversion to mph
constant = 0.3977274


# function to return distance given each of the two distance sensors
def get_distance(TRIG, ECHO):
    # sensor 1 setup, get baseline value
    # print("distance measurement in progress")
    GPIO.output(TRIG, False)
    # print("waiting for sensor to settle")
    sleep(0.2)  # waiting for sensor to settle
    GPIO.output(TRIG, True)
    sleep(0.00001)
    GPIO.output(TRIG, False)
    while GPIO.input(ECHO) == 0:
        pulse_start = time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time()
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150

    return (round(distance, 2))


def send_function(mph="no val specified"):
    t = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    t2 = str(t).replace('/', '').replace(' ', '').replace(':', '')

    payload = {'mph': str(round(mph, 2)) + ' mph',
               'timestamp': t,
               'name': 'image' + t2 + '.jpg'}

    # addr = 'http://localhost:5000'
    my_img = {'image': open('image.jpg', 'rb')}
    r = requests.post(url, files=my_img, data=payload, timeout=7)
    return (r.json())


# getting base distances
base_dist1 = get_distance(TRIG, ECHO)
print("base dist 1:", base_dist1, "cm")
base_dist2 = get_distance(TRIG2, ECHO2)
print("base dist 2:", base_dist2, "cm")

# LED time controllers
LEDwhitetime = 0
LEDbluetime = 0
LEDredtime = 0

while 1:
    distance = get_distance(TRIG, ECHO)

    if distance < base_dist1 / 2:
        print("Sensor 1 distance change @", distance, "cm")
        # object passed in front

        # turn on blue LED
        GPIO.output(B, GPIO.HIGH)

        time_pass1 = datetime.now()
        print(distance, "cm 1")
        flag1 = 1

        duration = timedelta(seconds=5)
        sleep(0.035)  # sleep for a small amount of time to limit error
        # loop for second sensor
        while True:
            timemark = datetime.now()
            distance2 = get_distance(TRIG2, ECHO2)
            if timemark - duration > time_pass1:
                # took too long to take photo
                # if time >= 5 seconds, car is going <= 0.0795452mph
                print("no pass happened")

                # turn off blue LED
                GPIO.output(B, GPIO.LOW)

                # flash red led
                for i in range(2):
                    GPIO.output(R, GPIO.HIGH)
                    sleep(0.2)
                    GPIO.output(R, GPIO.LOW)
                    sleep(0.2)

                break
            elif distance2 < base_dist2 / 2:
                # second sensor has been detected
                print("Sensor 2 distance change @", distance, "cm")

                # turn off blue LED
                GPIO.output(B, GPIO.LOW)

                # get speed
                time_diff = float((timemark - time_pass1).total_seconds())
                # print("mph:",time_diff*constant)
                mph = (7 / time_diff) * 0.056818
                mph = 35 / (time_diff * 88)
                # print("time diff: ",time_diff,"mph:",mph)
                print("time diff:", time_diff, "--- mph:", 35 / (time_diff * 88))

                # turn on white led
                GPIO.output(W, GPIO.HIGH)

                if mph > 1:
                    for i in range(6):
                        GPIO.output(B, GPIO.HIGH);
                        sleep(0.15)
                        GPIO.output(B, GPIO.LOW);
                        GPIO.output(R, GPIO.HIGH)
                        sleep(0.15)
                        GPIO.output(R, GPIO.LOW)
                else:
                    # sleep (wait for care to pass in front of camera)
                    sleep(2)

                # take photo and save to cwd
                camera.capture('image.jpg')

                # turn off white led
                GPIO.output(W, GPIO.LOW)

                # send to server
                # turn on blue LED
                try:
                    resp = send_function(mph=mph)
                    if resp['msg'] == 'success':
                        print("Successful data upload")
                        for i in range(3):
                            GPIO.output(B, GPIO.HIGH)
                            sleep(0.15)
                            GPIO.output(B, GPIO.LOW)
                            sleep(0.15)
                except:
                    print("Error: Unsuccessful data upload")
                    for i in range(6):
                        GPIO.output(R, GPIO.HIGH)
                        sleep(0.2)
                        GPIO.output(R, GPIO.LOW)
                        sleep(0.2)

                # sleep for a bit so that movement near sensor #1 doesnt cause new car incident
                sleep(3)

                break