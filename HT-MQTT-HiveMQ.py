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

"""
 You must setup the broker to be used on the Shelly Device Webpage.
 Change the broker address, prefix, username, password, and TLS No Validation.
 HiveMQ provides a free broker to host your MQTT data.
 This file is already set up for HiveMQ.
 https://www.hivemq.com/products/mqtt-cloud-broker/
"""

"""
 The H&T only comes online every so often.
 The values only update after it transmits a Full Status Notification. (Threshold met or 2 hours)
 You can hook up an external power supply to increase the transmit frequency to 5 min.
 Values will be empty until an update has been triggered.
 You can manually trigger an update by single pressing the reset button.
"""


# For the terminal display.
# 🠉   reading is increasing from last update
# 🠋   reading is decreasing from last update
# 🠈🠊 reading is the same as last update


# IP address, username and password of the HiveMQ broker that holds the MQTT values
ip       = '23423hkj45hkj567hk6j7787kjh8hkj345.s1.eu.hivemq.cloud'  # <------ Change This to your HiveMQ url
username = "SomeBrokerUserName"                                     # <------ Change This to your HiveMQ username
password = "SomePassWord8456"                                       # <------ Change This to your HiveMQ password
tls_version_value = 2 # see the connect to broker part below if needed (client.tls_set(tls_version=2))
#======================================
# Number of H&T's you have (3 or less)
Qty = 1                                                     # <------ Change This
#======================================
# MQTT H&T Topic Prefix on the broker as in H&T-Computer-Room/events/rpc (Just the prefix part H&T-Computer-Room)
# You set these prefixes in the H&T MQTT settings web page.
HT1Prefix = "H&T-Bedroom"                             # <------ Change This
HT2Prefix = "H&T-Living-Room"                               # <------ Change This if you have more than 1. Otherwise leave as is
HT3Prefix = "H&T-Garage"                                    # <------ Change This if you have more than 2. Otherwise leave as is
#======================================
# H&T Location / Call them anything you want
HT1Location = "BedRoom1"                                    # <------ Change This
HT2Location = "Living Room"                                 # <------ Change This if you have more than 1. Otherwise leave as is
HT3Location = "Garage"                                      # <------ Change This if you have more than 2. Otherwise leave as is
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
HT1TempOLD     = None
HT1HumidOLD    = None
HT2TempOLD     = None
HT2HumidOLD    = None
HT3TempOLD     = None
HT3HumidOLD    = None

print("\033[H\033[J") # Clear screen
print('\033[?25l', end="") # Hide Blinking Cursor
clear = "\033[K\033[1K" # Eliminates screen flashing / blink during refresh
                        # It clear's to end of line and moves to begining of line then prints the new line

def log_sensor_data(sensor_name, sensor_type, sensor_value, timestamp):
    with open('HT-sensor-log-HiveMQ.csv', 'a', newline='') as csvfile:
        fieldnames = ['Timestamp', 'Sensor Location', 'Sensor Type', 'Sensor Value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Check if the file is empty and write header if needed
        if csvfile.tell() == 0:
            writer.writeheader()

        writer.writerow({'Timestamp': timestamp, 'Sensor Location': sensor_name, 'Sensor Type': sensor_type,  'Sensor Value': sensor_value})

#===================================
# Begin MQTT Section
# The topics you want to subscripbe to
def on_connect(client, userdata, flags, rc):
    print(f"\033[38;5;130mConnected to Broker {ip} with result code {str(rc)}\033[0m")

    topics = [
              (HT1Prefix+"/events/rpc",0),
              (HT2Prefix+"/events/rpc",0),
              (HT3Prefix+"/events/rpc",0)
              ]

    client.subscribe(topics)
    print("\033[38;5;127mWaiting For Shelly MQTT Broker Messages\n\033[0m")


def on_disconnect(client, userdata,rc):
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

    if rc != 0:
        Disconnect = datetime.now()
        Disconnect_dt_string = Disconnect.strftime("%a %d %b %Y     %r")
        print(f"\033[38;5;196mUnexpected Disconnect \033[0m{Disconnect_dt_string}")
        print(f"Disconnect Code {str(rc)} {RC[rc]}" )
        print(f"\033[38;5;196mTrying to Reconnect....\033[0m")

        if rc in range(1, 17):
            try:
                client.reconnect()
            except ConnectionRefusedError:
                print(f"Connection Refused Error...Retrying")

            except TimeoutError:
                print(f"Connection Timeout Error...Retrying")

        else:
            print(f"\033[38;5;196mUnexpected Disconnect reason unknown \033[0m")
            print(f"Disconnect Code {str(rc)}")
    else:
        client.loop_stop()
        print(f"\033[38;5;148mStopping MQTT Loop")
        print(f"Disconnect Result Code {str(rc)}\033[0m\n")
        print('\033[?25h', end="") # Restore Blinking Cursor
        quit()


#===================================
# Read the topics as they come in and assign them to variables
def on_message(client, userdata, msg):
    global HT1Time, HT1Temp, HT1Humid, HT1BattV, HT1BattPercent, \
           HT2Time, HT2Temp, HT2Humid, HT2BattV, HT2BattPercent, \
           HT3Time, HT3Temp, HT3Humid, HT3BattV, HT3BattPercent, \
           HT1TempDir, HT1TempOLD, HT1HumidDir, HT1HumidOLD, \
           HT2TempDir, HT2TempOLD, HT2HumidDir, HT2HumidOLD, \
           HT3TempDir, HT3TempOLD, HT3HumidDir, HT3HumidOLD

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
                    HT1TempDir = "🠉"
                    HT1TempOLD = HT1Temp
                elif HT1Temp < HT1TempOLD:
                    HT1TempDir = "🠋"
                    HT1TempOLD = HT1Temp
                else:
                    HT1TempDir = "🠈🠊"
                    HT1TempOLD = HT1Temp
            if isinstance(HT1HumidOLD, float):
                if HT1Humid > HT1HumidOLD:
                    HT1HumidDir = "🠉"
                    HT1HumidOLD = HT1Humid
                elif HT1Humid < HT1HumidOLD:
                    HT1HumidDir = "🠋"
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
                    HT2TempDir = "🠉"
                    HT2TempOLD = HT2Temp
                elif HT2Temp < HT2TempOLD:
                    HT2TempDir = "🠋"
                    HT2TempOLD = HT2Temp
                else:
                    HT2TempDir = "🠈🠊"
                    HT2TempOLD = HT2Temp
            if isinstance(HT2HumidOLD, float):
                if HT2Humid > HT2HumidOLD:
                    HT2HumidDir = "🠉"
                    HT2HumidOLD = HT2Humid
                elif HT2Humid < HT2HumidOLD:
                    HT2HumidDir = "🠋"
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
                    HT3TempDir = "🠉"
                    HT3TempOLD = HT3Temp
                elif HT3Temp < HT3TempOLD:
                    HT3TempDir = "🠋"
                    HT3TempOLD = HT3Temp
                else:
                    HT3TempDir = "🠈🠊"
                    HT3TempOLD = HT3Temp
            if isinstance(HT3HumidOLD, float):
                if HT3Humid > HT3HumidOLD:
                    HT3HumidDir = "🠉"
                    HT3HumidOLD = HT3Humid
                elif HT3Humid < HT3HumidOLD:
                    HT3HumidDir = "🠋"
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


#===================================
# Create a mqtt client instance
client = mqtt.Client()

# Assign callback functions
client.on_connect    = on_connect
client.on_message    = on_message
client.on_disconnect = on_disconnect

# Connect to the broker
print(f"\n\033[38;5;28mTrying to Connect To Broker {ip}")
try:
    # enable TLS
    client.tls_set(tls_version=tls_version_value)
    # set username and password
    client.username_pw_set(username, password)
    client.connect(ip, 8883, 60)
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

        time.sleep(15) # Wait seconds then see if a new reading has been received

    except KeyboardInterrupt:
        print("\033[K\033[1K") # Erase the line (removes the printed ^C)
        print(f"\n\033[38;5;148mExiting App\033[0m")
        print('\033[?25h', end="") # Restore Blinking Cursor
        client.disconnect() # Disconnect from the broker and print the disconnect message
        time.sleep(1) # small time for the disconnect to run
        quit()
