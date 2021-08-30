# Smart Street Camera
 Rasberry pi camera embedded device and webapp for sensor activated speed trap

# Hardware
The main components for the hardware are the two HC-SR04 ultrasonic distance sensors, LEDs, and Pi camera module. The distance sensors work by sending a trigger signal and receiving and echo signal in order to calculate a distance. The Pi camera has a specific function library to work in accordance with the raspberry pi and must be first activated through the raspberry Pi’s configuration settings. The LEDs and distance sensors are powered and connected via the GPIO ports, and the camera is connected via the Camera Module Port on the Raspberry Pi itself. More details will be discussed in the below software section as part of the hardware’s client programming. The Raspberry Pi is powered by the USB-C power connection.

# Server program
The server program is a Python Flask server using the Python SQLALCHEMY SQL bindings library. The server sets up and can be broken down into components for an index route for displaying the database instances, API route for data upload, and a delete route to allow the user to delete instances, as well as the SQL database itself. When the server receives the photo, mph, and timestamp information it appends it to the SQL database and the image is stored locally. The image and information then gets populated to an html table where the viewer can view the information as well as delete the instance.

Before running server you must run the following commands within a python console in cwd in order to create the SQL table within data.sqlite

```
from streetlight_server import db
db.create_all()
```


# Client Program

The client program interfaces the Pi’s hardware to its functionality. The client is written in python and makes use of both the GPIO, PiCamera, and requests libraries. The GPIO is used to interface with the sensors and LEDs. Upon client program start, the PiCamera initiates itself by running the start_preview() command in order to adjust for ambient light. The sensors are then sent a positive signal to the trigger port and the device waits for a positive response from echo port. The time difference in this response is converted to distance. The device will use this property to get distances proactively throughout the runtime of the program. Base distances are first recorded and used as thresholds to signal if a car passes by. From there, the program will loop and recalculate distance from sensor #1 until its threshold is hit by having a distance that is less then half of the base distance. A time stamp is then recorded, the blue LED flashes, and the program loops the second sensors distance until a threshold is broken by the same value. A second timestamp is recorded, and the device will sleep to wait for the vehicle to pass in front of the Pi camera and the white LED will flash. Another sleep operation is used in between the loops for each sensor to avoid hand or other object interference resulting in the output of a fast speed. If the vehicle moves too quickly the red and blue LEDs will flash in an alternate manner indicating to the driver to slow down. The distance between both sensors is approximately 7 inches. So, the following formula is used to convert to mph: 35/(time_diff*88), where time_diff is the time difference between the sensor timestamps. A photo is taken and then saved locally and closed in order to be handled by the API post request.


