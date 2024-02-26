#!/usr/bin/env python3
import sys
import os
import csv
from datetime import datetime
import time
from time import strftime
from time import gmtime
from time import sleep
import json

# MQTT
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as mqttpublish

# The H&T only comes online every so often.
# The values only update after it transmits a Full Status Notification. (Threshold met or 2 hours)
# You can hook up an external power supply to increase the transmit frequency to 5 min.
# Values will be empty until an update has been triggered.
# You can manually trigger an update by single pressing the reset button.

# 🠉   reading is increasing from last update
# 🠋   reading is decreasing from last update
# 🠈🠊 reading is the same as last update


# IP of the broker that holds the MQTT values
ip   = '192.168.20.167'          # <------ Change This
port = 1883
#======================================
# Number of H&T's you have (5 or less)
Qty = 5                         # <------ Change This
#======================================
# MQTT H&T Topic Prefix on the broker as in H&T-Computer-Room/events/rpc (Just the prefix part H&T-Computer-Room)
# You set these prefixes in the H&T MQTT settings web page.
HT1Prefix = "H&T-Computer-Room" # <------ Change This
HT2Prefix = "H&T-Living-Room"   # <------ Change This if you have more than 1. Otherwise leave as is
HT3Prefix = "H&T-Garage"        # <------ Change This if you have more than 2. Otherwise leave as is
HT4Prefix = "H&T-BedRoom"       # <------ Change This if you have more than 3. Otherwise leave as is
HT5Prefix = "H&T-Kitchen"       # <------ Change This if you have more than 4. Otherwise leave as is
HT6Prefix = "H&T-CrawlSpace"    # <------ Change This if you have more than 5. Otherwise leave as is
#======================================
# H&T Location / Call them anything you want
HT1Location = "Computer Room"   # <------ Change This
HT2Location = "Living Room"     # <------ Change This if you have more than 1. Otherwise leave as is
HT3Location = "Garage"          # <------ Change This if you have more than 2. Otherwise leave as is
HT4Location = "BedRoom 1"       # <------ Change This if you have more than 3. Otherwise leave as is
HT5Location = "Kitchen"         # <------ Change This if you have more than 4. Otherwise leave as is
HT6Location = "CrawlSpace"      # <------ Change This if you have more than 4. Otherwise leave as is
#======================================
# H&T initial Values. This is what will be displayed for the values until an update is received.
# You can manually trigger an update by single pressing the reset button.
HT1Time        = "Waiting For Update"
HT1Temp        = "* "
HT1Humid       = "* "
HT1BattV       = "* "
HT1BattPercent = "* "
HT1TempDir     = ""
HT1HumidDir    = ""
#======================================
HT2Time        = "Waiting For Update"
HT2Temp        = "* "
HT2Humid       = "* "
HT2BattV       = "* "
HT2BattPercent = "* "
HT2TempDir     = ""
HT2HumidDir    = ""
#======================================
HT3Time        = "Waiting For Update"
HT3Temp        = "* "
HT3Humid       = "* "
HT3BattV       = "* "
HT3BattPercent = "* "
HT3TempDir     = ""
HT3HumidDir    = ""
#======================================
HT4Time        = "Waiting For Update"
HT4Temp        = "* "
HT4Humid       = "* "
HT4BattV       = "* "
HT4BattPercent = "* "
HT4TempDir     = ""
HT4HumidDir    = ""
#======================================
HT5Time        = "Waiting For Update"
HT5Temp        = "* "
HT5Humid       = "* "
HT5BattV       = "* "
HT5BattPercent = "* "
HT5TempDir     = ""
HT5HumidDir    = ""
#======================================
HT6Time        = "Waiting For Update"
HT6Temp        = "* "
HT6Humid       = "* "
HT6BattV       = "* "
HT6BattPercent = "* "
HT6TempDir     = ""
HT6HumidDir    = ""
#======================================
HT1TempOLD     = None
HT1HumidOLD    = None
HT2TempOLD     = None
HT2HumidOLD    = None
HT3TempOLD     = None
HT3HumidOLD    = None
HT4TempOLD     = None
HT4HumidOLD    = None
HT5TempOLD     = None
HT5HumidOLD    = None
HT6TempOLD     = None
HT6HumidOLD    = None


disconnect_flag = ''

print("\033[H\033[J") # Clear screen
print('\033[?25l', end="") # Hide Blinking Cursor
clear = "\033[K\033[1K" # Eliminates screen flashing / blink during refresh
                        # It clear's to end of line and moves to begining of line then prints the new line

def log_sensor_data(sensor_name, sensor_type, sensor_value, timestamp):
    with open('HT-sensor-log.csv', 'a', newline='') as csvfile:
        fieldnames = ['Timestamp', 'Sensor Location', 'Sensor Type', 'Sensor Value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Check if the file is empty and write header if needed
        if csvfile.tell() == 0:
            writer.writeheader()

        writer.writerow({'Timestamp': timestamp, 'Sensor Location': sensor_name, 'Sensor Type': sensor_type,  'Sensor Value': sensor_value})

#===================================
# Begin MQTT Section
# The topics you want to subscripbe to
def on_connect(client, userdata, flags, reason_code, properties):
    global disconnect_flag
    if disconnect_flag == 1:
        print("\033[H\033[J") # Clear screen
        disconnect_flag = 0
    else:
        print(f"\033[38;5;130mConnected to Broker {ip} with result code {str(reason_code )}\033[0m")

    topics = [
              (HT1Prefix+"/events/rpc",0),
              (HT2Prefix+"/events/rpc",0),
              (HT3Prefix+"/events/rpc",0),
              (HT4Prefix+"/events/rpc",0),
              (HT5Prefix+"/events/rpc",0),
              (HT6Prefix+"/events/rpc",0)
              ]

    client.subscribe(topics)
    print("\033[38;5;127mWaiting For Shelly MQTT Broker Messages\n\033[0m")


def on_disconnect(client, userdata, flags, reason_code, properties):
    global disconnect_flag
    RC = {1: "Out of memory",
          2: "A network protocol error occurred when communicating with the broker.",
          3: "Invalid function arguments provided.",
          4: "The client is not currently connected.",
          5: "Connection Refused",
          6: "Connection Not Found",
          7: "Connection Lost",
          8: "A TLS error occurred.",
          9: "Payload too large.",
          10: "This feature is not supported.",
          11: "Authorisation failed.",
          12: "Access denied by ACL.",
          13: "Unknown error.",
          14: "Error defined by errno.",
          15: "Message queue full.",
          16: "Connection Lost for Unknown Reason"
         }

    if reason_code != 0:
        Disconnect = datetime.now()
        Disconnect_dt_string = Disconnect.strftime("%a %d %b %Y     %r")
        print(f"\033[38;5;196mUnexpected Disconnect \033[0m{Disconnect_dt_string}")
        print(f"Disconnect Code {str(reason_code )} {RC[reason_code ]}" )
        print(f"\033[38;5;196mTrying to Reconnect....\033[0m")

        if reason_code in range(1, 17):
            try:
                client.reconnect()
                disconnect_flag = 1
            except ConnectionRefusedError:
                print(f"Connection Refused Error...Retrying")

            except TimeoutError:
                print(f"Connection Timeout Error...Retrying")

        else:
            print(f"\033[38;5;196mUnexpected Disconnect reason unknown \033[0m")
            print(f"Disconnect Code {str(reason_code )}")
    else:
        client.loop_stop()
        print(f"\033[38;5;148mStopping MQTT Loop")
        print(f"Disconnect Result Code {str(reason_code )}\033[0m\n")
        print('\033[?25h', end="") # Restore Blinking Cursor
        quit()


#===================================
# Read the topics as they come in and assign them to variables
def on_message(client, userdata, msg):
    global HT1Time, HT1Temp, HT1Humid, HT1BattV, HT1BattPercent, \
           HT2Time, HT2Temp, HT2Humid, HT2BattV, HT2BattPercent, \
           HT3Time, HT3Temp, HT3Humid, HT3BattV, HT3BattPercent, \
           HT4Time, HT4Temp, HT4Humid, HT4BattV, HT4BattPercent, \
           HT5Time, HT5Temp, HT5Humid, HT5BattV, HT5BattPercent, \
           HT6Time, HT6Temp, HT6Humid, HT6BattV, HT6BattPercent, \
           HT1TempDir, HT1TempOLD, HT1HumidDir, HT1HumidOLD, \
           HT2TempDir, HT2TempOLD, HT2HumidDir, HT2HumidOLD, \
           HT3TempDir, HT3TempOLD, HT3HumidDir, HT3HumidOLD, \
           HT4TempDir, HT4TempOLD, HT4HumidDir, HT4HumidOLD, \
           HT5TempDir, HT5TempOLD, HT5HumidDir, HT5HumidOLD, \
           HT6TempDir, HT6TempOLD, HT6HumidDir, HT6HumidOLD

    if msg.topic == HT1Prefix+"/events/rpc":
        HT1FullStatus = json.loads(msg.payload)['method']
        if HT1FullStatus == "NotifyFullStatus":
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            # Datetime object containing date and time
            HT1Time = datetime.now()
            HT1Time = HT1Time.strftime("%a %d %b %Y     %r")
            HT1Temp = json.loads(msg.payload)['params']['temperature:0']['tF']
            HT1Humid = json.loads(msg.payload)['params']['humidity:0']['rh']
            HT1BattV = json.loads(msg.payload)['params']['devicepower:0']['battery']['V']
            HT1BattPercent = json.loads(msg.payload)['params']['devicepower:0']['battery']['percent']
            if HT1TempOLD is None or HT1HumidOLD is None:
                HT1TempOLD = HT1Temp
                HT1HumidOLD = HT1Humid
            if isinstance(HT1TempOLD, float):
                if HT1Temp > HT1TempOLD:
                    HT1TempDir = f"{'🠉': <4}{'From': <8} {HT1TempOLD}"
                    HT1TempOLD = HT1Temp
                elif HT1Temp < HT1TempOLD:
                    HT1TempDir = f"{'🠋': <4}{'From': <8} {HT1TempOLD}"
                    HT1TempOLD = HT1Temp
                else:
                    HT1TempDir = "🠈🠊"
                    HT1TempOLD = HT1Temp
            if isinstance(HT1HumidOLD, float):
                if HT1Humid > HT1HumidOLD:
                    HT1HumidDir = f"{'🠉': <4}{'From': <8} {HT1HumidOLD}"
                    HT1HumidOLD = HT1Humid
                elif HT1Humid < HT1HumidOLD:
                    HT1HumidDir = f"{'🠋': <4}{'From': <8} {HT1HumidOLD}"
                    HT1HumidOLD = HT1Humid
                else:
                    HT1HumidDir = "🠈🠊"
                    HT1HumidOLD = HT1Humid
            log_sensor_data(HT1Location, "Temperature", HT1Temp, timestamp)
            time.sleep(.2)
            log_sensor_data(HT1Location, "Humidity", HT1Humid, timestamp)
            time.sleep(.2)
            log_sensor_data(HT1Location, "BatteryVolts", HT1BattV, timestamp)
            time.sleep(.2)
            log_sensor_data(HT1Location, "BatteryPercent", HT1BattPercent, timestamp)


    if msg.topic == HT2Prefix+"/events/rpc":
        HT2FullStatus = json.loads(msg.payload)['method']
        if HT2FullStatus == "NotifyFullStatus":
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            # Datetime object containing date and time
            HT2Time = datetime.now()
            HT2Time = HT2Time.strftime("%a %d %b %Y     %r")
            HT2Temp = json.loads(msg.payload)['params']['temperature:0']['tF']
            HT2Humid = json.loads(msg.payload)['params']['humidity:0']['rh']
            HT2BattV = json.loads(msg.payload)['params']['devicepower:0']['battery']['V']
            HT2BattPercent = json.loads(msg.payload)['params']['devicepower:0']['battery']['percent']
            if HT2TempOLD is None or HT2HumidOLD is None:
                HT2TempOLD = HT2Temp
                HT2HumidOLD = HT2Humid
            if isinstance(HT2TempOLD, float):
                if HT2Temp > HT2TempOLD:
                    HT2TempDir = f"{'🠉': <4}{'From': <8} {HT2TempOLD}"
                    HT2TempOLD = HT2Temp
                elif HT2Temp < HT2TempOLD:
                    HT2TempDir = f"{'🠋': <4}{'From': <8} {HT2TempOLD}"
                    HT2TempOLD = HT2Temp
                else:
                    HT2TempDir = "🠈🠊"
                    HT2TempOLD = HT2Temp
            if isinstance(HT2HumidOLD, float):
                if HT2Humid > HT2HumidOLD:
                    HT2HumidDir = f"{'🠉': <4}{'From': <8} {HT2HumidOLD}"
                    HT2HumidOLD = HT2Humid
                elif HT2Humid < HT2HumidOLD:
                    HT2HumidDir = f"{'🠋': <4}{'From': <8} {HT2HumidOLD}"
                    HT2HumidOLD = HT2Humid
                else:
                    HT2HumidDir = "🠈🠊"
                    HT2HumidOLD = HT2Humid
            log_sensor_data(HT2Location, "Temperature", HT2Temp, timestamp)
            time.sleep(.2)
            log_sensor_data(HT2Location, "Humidity", HT2Humid, timestamp)
            time.sleep(.2)
            log_sensor_data(HT2Location, "BatteryVolts", HT2BattV, timestamp)
            time.sleep(.2)
            log_sensor_data(HT2Location, "BatteryPercent", HT2BattPercent, timestamp)

    if msg.topic == HT3Prefix+"/events/rpc":
        HT3FullStatus = json.loads(msg.payload)['method']
        if HT3FullStatus == "NotifyFullStatus":
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            # Datetime object containing date and time
            HT3Time = datetime.now()
            HT3Time = HT3Time.strftime("%a %d %b %Y     %r")
            HT3Temp = json.loads(msg.payload)['params']['temperature:0']['tF']
            HT3Humid = json.loads(msg.payload)['params']['humidity:0']['rh']
            HT3BattV = json.loads(msg.payload)['params']['devicepower:0']['battery']['V']
            HT3BattPercent = json.loads(msg.payload)['params']['devicepower:0']['battery']['percent']
            if HT3TempOLD is None or HT3HumidOLD is None:
                HT3TempOLD = HT3Temp
                HT3HumidOLD = HT3Humid
            if isinstance(HT3TempOLD, float):
                if HT3Temp > HT3TempOLD:
                    HT3TempDir = f"{'🠉': <4}{'From': <8} {HT3TempOLD}"
                    HT3TempOLD = HT3Temp
                elif HT3Temp < HT3TempOLD:
                    HT3TempDir = f"{'🠋': <4}{'From': <8} {HT3TempOLD}"
                    HT3TempOLD = HT3Temp
                else:
                    HT3TempDir = "🠈🠊"
                    HT3TempOLD = HT3Temp
            if isinstance(HT3HumidOLD, float):
                if HT3Humid > HT3HumidOLD:
                    HT3HumidDir = f"{'🠉': <4}{'From': <8} {HT3HumidOLD}"
                    HT3HumidOLD = HT3Humid
                elif HT3Humid < HT3HumidOLD:
                    HT3HumidDir = f"{'🠋': <4}{'From': <8} {HT3HumidOLD}"
                    HT3HumidOLD = HT3Humid
                else:
                    HT3HumidDir = "🠈🠊"
                    HT3HumidOLD = HT3Humid
            log_sensor_data(HT3Location, "Temperature", HT3Temp, timestamp)
            time.sleep(.2)
            log_sensor_data(HT3Location, "Humidity", HT3Humid, timestamp)
            time.sleep(.2)
            log_sensor_data(HT3Location, "BatteryVolts", HT3BattV, timestamp)
            time.sleep(.2)
            log_sensor_data(HT3Location, "BatteryPercent", HT3BattPercent, timestamp)
    
    
    if msg.topic == HT4Prefix+"/events/rpc":
        HT4FullStatus = json.loads(msg.payload)['method']
        if HT4FullStatus == "NotifyFullStatus":
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            # Datetime object containing date and time
            HT4Time = datetime.now()
            HT4Time = HT4Time.strftime("%a %d %b %Y     %r")
            HT4Temp = json.loads(msg.payload)['params']['temperature:0']['tF']
            HT4Humid = json.loads(msg.payload)['params']['humidity:0']['rh']
            HT4BattV = json.loads(msg.payload)['params']['devicepower:0']['battery']['V']
            HT4BattPercent = json.loads(msg.payload)['params']['devicepower:0']['battery']['percent']
            if HT4TempOLD is None or HT4HumidOLD is None:
                HT4TempOLD = HT4Temp
                HT4HumidOLD = HT4Humid
            if isinstance(HT4TempOLD, float):
                if HT4Temp > HT4TempOLD:
                    HT4TempDir = f"{'🠉': <4}{'From': <8} {HT4TempOLD}"
                    HT4TempOLD = HT4Temp
                elif HT4Temp < HT4TempOLD:
                    HT4TempDir = f"{'🠋': <4}{'From': <8} {HT4TempOLD}"
                    HT4TempOLD = HT4Temp
                else:
                    HT4TempDir = "🠈🠊"
                    HT4TempOLD = HT4Temp
            if isinstance(HT4HumidOLD, float):
                if HT4Humid > HT4HumidOLD:
                    HT4HumidDir = f"{'🠉': <4}{'From': <8} {HT4HumidOLD}"
                    HT4HumidOLD = HT4Humid
                elif HT4Humid < HT4HumidOLD:
                    HT4HumidDir = f"{'🠋': <4}{'From': <8} {HT4HumidOLD}"
                    HT4HumidOLD = HT4Humid
                else:
                    HT4HumidDir = "🠈🠊"
                    HT4HumidOLD = HT4Humid
            log_sensor_data(HT4Location, "Temperature", HT4Temp, timestamp)
            time.sleep(.2)
            log_sensor_data(HT4Location, "Humidity", HT4Humid, timestamp)
            time.sleep(.2)
            log_sensor_data(HT4Location, "BatteryVolts", HT4BattV, timestamp)
            time.sleep(.2)
            log_sensor_data(HT4Location, "BatteryPercent", HT4BattPercent, timestamp)
    
    
    if msg.topic == HT5Prefix+"/events/rpc":
        HT5FullStatus = json.loads(msg.payload)['method']
        if HT5FullStatus == "NotifyFullStatus":
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            # Datetime object containing date and time
            HT5Time = datetime.now()
            HT5Time = HT5Time.strftime("%a %d %b %Y     %r")
            HT5Temp = json.loads(msg.payload)['params']['temperature:0']['tF']
            HT5Humid = json.loads(msg.payload)['params']['humidity:0']['rh']
            HT5BattV = json.loads(msg.payload)['params']['devicepower:0']['battery']['V']
            HT5BattPercent = json.loads(msg.payload)['params']['devicepower:0']['battery']['percent']
            if HT5TempOLD is None or HT5HumidOLD is None:
                HT5TempOLD = HT5Temp
                HT5HumidOLD = HT5Humid
            if isinstance(HT5TempOLD, float):
                if HT5Temp > HT5TempOLD:
                    HT5TempDir = f"{'🠉': <4}{'From': <8} {HT5TempOLD}"
                    HT5TempOLD = HT5Temp
                elif HT5Temp < HT5TempOLD:
                    HT5TempDir = f"{'🠋': <4}{'From': <8} {HT5TempOLD}"
                    HT5TempOLD = HT5Temp
                else:
                    HT5TempDir = "🠈🠊"
                    HT5TempOLD = HT5Temp
            if isinstance(HT5HumidOLD, float):
                if HT5Humid > HT5HumidOLD:
                    HT5HumidDir = f"{'🠉': <4}{'From': <8} {HT5HumidOLD}"
                    HT5HumidOLD = HT5Humid
                elif HT5Humid < HT5HumidOLD:
                    HT5HumidDir = f"{'🠋': <4}{'From': <8} {HT5HumidOLD}"
                    HT5HumidOLD = HT5Humid
                else:
                    HT5HumidDir = "🠈🠊"
                    HT5HumidOLD = HT5Humid
            log_sensor_data(HT5Location, "Temperature", HT5Temp, timestamp)
            time.sleep(.2)
            log_sensor_data(HT5Location, "Humidity", HT5Humid, timestamp)
            time.sleep(.2)
            log_sensor_data(HT5Location, "BatteryVolts", HT5BattV, timestamp)
            time.sleep(.2)
            log_sensor_data(HT5Location, "BatteryPercent", HT5BattPercent, timestamp)
    
    
    if msg.topic == HT6Prefix+"/events/rpc":
        HT6FullStatus = json.loads(msg.payload)['method']
        if HT6FullStatus == "NotifyFullStatus":
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            # Datetime object containing date and time
            HT6Time = datetime.now()
            HT6Time = HT6Time.strftime("%a %d %b %Y     %r")
            HT6Temp = json.loads(msg.payload)['params']['temperature:0']['tF']
            HT6Humid = json.loads(msg.payload)['params']['humidity:0']['rh']
            HT6BattV = json.loads(msg.payload)['params']['devicepower:0']['battery']['V']
            HT6BattPercent = json.loads(msg.payload)['params']['devicepower:0']['battery']['percent']
            if HT6TempOLD is None or HT6HumidOLD is None:
                HT6TempOLD = HT6Temp
                HT6HumidOLD = HT6Humid
            if isinstance(HT6TempOLD, float):
                if HT6Temp > HT6TempOLD:
                    HT6TempDir = f"{'🠉': <4}{'From': <8} {HT6TempOLD}"
                    HT6TempOLD = HT6Temp
                elif HT6Temp < HT6TempOLD:
                    HT6TempDir = f"{'🠋': <4}{'From': <8} {HT6TempOLD}"
                    HT6TempOLD = HT6Temp
                else:
                    HT6TempDir = "🠈🠊"
                    HT6TempOLD = HT6Temp
            if isinstance(HT6HumidOLD, float):
                if HT6Humid > HT6HumidOLD:
                    HT6HumidDir = f"{'🠉': <4}{'From': <8} {HT6HumidOLD}"
                    HT6HumidOLD = HT6Humid
                elif HT6Humid < HT6HumidOLD:
                    HT6HumidDir = f"{'🠋': <4}{'From': <8} {HT6HumidOLD}"
                    HT6HumidOLD = HT6Humid
                else:
                    HT6HumidDir = "🠈🠊"
                    HT6HumidOLD = HT6Humid
            log_sensor_data(HT6Location, "Temperature", HT6Temp, timestamp)
            time.sleep(.2)
            log_sensor_data(HT6Location, "Humidity", HT6Humid, timestamp)
            time.sleep(.2)
            log_sensor_data(HT6Location, "BatteryVolts", HT6BattV, timestamp)
            time.sleep(.2)
            log_sensor_data(HT6Location, "BatteryPercent", HT6BattPercent, timestamp)
    
    

#===================================
# Create a mqtt client instance
#client = mqtt.Client(callback_api_version=mqtt.CALLBACK_VERSION_2)
#client = mqtt.Client.__init__(callback_api_version=mqtt.CALLBACK_VERSION_)
#client = mqtt.Client.__init__(mqtt.CallbackAPIVersion.VERSION1)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) 


# Assign callback functions
client.on_connect    = on_connect
client.on_message    = on_message
client.on_disconnect = on_disconnect

# Connect to the broker
print(f"\n\033[38;5;28mTrying to Connect To Broker {ip}")
try:
    client.connect(ip, port, 60)
except TimeoutError:
    print(f"\033[48;5;196m\033[38;5;16mUnable to Connect To Broker {ip}\033[0m")
    print('\033[?25h', end="") # Restore Blinking Cursor
    quit()

# Start the non blocking background loop
client.loop_start()
time.sleep(2)

while True:
    # Do some other stuff while waiting for updates
    try:
        # Print the updates as they come in
        print("\033[0;0f") # move to col 0 row 0 to start the printing at the same spot everytime
                           # instead of having the text scoll up the screen just reuse the same spot on the screen
                           # the "clear" in the following lines erases the line and reprints wih new values from the begining of the line
        print(f"\033[0m{clear}{HT1Time}")
        print(f"{clear}\033[38;5;214m{HT1Location + ' Temperature': <30} {HT1Temp}° F  {HT1TempDir}")
        print(f"{clear}{HT1Location + ' Humidity': <30} {HT1Humid}%    {HT1HumidDir}")
        print(f"{clear}{HT1Location + ' Battery Voltage': <30} {HT1BattV}V")
        print(f"{clear}{HT1Location + ' Battery Percent': <30} {HT1BattPercent}%\033[0m")
        print(f"\033[0m{clear}")
        print("=" * 70, "\n")


        if Qty > 1:
            print(f"\033[0m{clear}{HT2Time}")
            print(f"{clear}\033[38;5;201m{HT2Location + ' Temperature': <30} {HT2Temp}° F  {HT2TempDir}")
            print(f"{clear}{HT2Location + ' Humidity': <30} {HT2Humid}%    {HT2HumidDir}")
            print(f"{clear}{HT2Location + ' Battery Voltage': <30} {HT2BattV}V")
            print(f"{clear}{HT2Location + ' Battery Percent': <30} {HT2BattPercent}%\033[0m")
            print(f"\033[0m{clear}")
            print("=" * 70, "\n")

        if Qty > 2:
            print(f"\033[0m{clear}{HT3Time}")
            print(f"{clear}\033[38;5;27m{HT3Location + ' Temperature': <30} {HT3Temp}° F  {HT3TempDir}")
            print(f"{clear}{HT3Location + ' Humidity': <30} {HT3Humid}%    {HT3HumidDir}")
            print(f"{clear}{HT3Location + ' Battery Voltage': <30} {HT3BattV}V")
            print(f"{clear}{HT3Location + ' Battery Percent': <30} {HT3BattPercent}%\033[0m")
            print(f"\033[0m{clear}")
            print("=" * 70, "\n")
            
        if Qty > 3:
            print(f"\033[0m{clear}{HT4Time}")
            print(f"{clear}\033[38;5;51m{HT4Location + ' Temperature': <30} {HT4Temp}° F  {HT4TempDir}")
            print(f"{clear}{HT4Location + ' Humidity': <30} {HT4Humid}%    {HT4HumidDir}")
            print(f"{clear}{HT4Location + ' Battery Voltage': <30} {HT4BattV}V")
            print(f"{clear}{HT4Location + ' Battery Percent': <30} {HT4BattPercent}%\033[0m")
            print(f"\033[0m{clear}")
            print("=" * 70, "\n")
            
        if Qty > 4:
            print(f"\033[0m{clear}{HT5Time}")
            print(f"{clear}\033[38;5;226m{HT5Location + ' Temperature': <30} {HT5Temp}° F  {HT5TempDir}")
            print(f"{clear}{HT5Location + ' Humidity': <30} {HT5Humid}%    {HT5HumidDir}")
            print(f"{clear}{HT5Location + ' Battery Voltage': <30} {HT5BattV}V")
            print(f"{clear}{HT5Location + ' Battery Percent': <30} {HT5BattPercent}%\033[0m")
            print(f"\033[0m{clear}")
            print("=" * 70, "\n")
            
        if Qty > 5:
            print(f"\033[0m{clear}{HT6Time}")
            print(f"{clear}\033[38;5;129m{HT6Location + ' Temperature': <30} {HT6Temp}° F  {HT6TempDir}")
            print(f"{clear}{HT6Location + ' Humidity': <30} {HT6Humid}%    {HT6HumidDir}")
            print(f"{clear}{HT6Location + ' Battery Voltage': <30} {HT6BattV}V")
            print(f"{clear}{HT6Location + ' Battery Percent': <30} {HT6BattPercent}%\033[0m")
            print(f"\033[0m{clear}")
            print("=" * 70, "\n")

        time.sleep(15) # Wait seconds then see if a new reading has been received

    except KeyboardInterrupt:
        print("\033[K\033[1K") # Erase the line (removes the printed ^C)
        print(f"\n\033[38;5;148mExiting App\033[0m")
        print('\033[?25h', end="") # Restore Blinking Cursor
        client.disconnect() # Disconnect from the broker and print the disconnect message
        time.sleep(1) # small time for the disconnect to run
        quit()
