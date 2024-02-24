#!/usr/bin/env python3
"""
The following modules need to be installed:
    pandas
    numpy
    matplotlib
as in:
pip install pandas numpy matplotlib
"""

"""
This is a companion tool for the HT-MQTT.py script that displays (on the terminal) and stores data (in a csv file) from Shelly H&T G3 sensors.
This tool only displays (in a chart) your already stored data (in a csv file) from the HT-MQTT.py script.

Mostly ChatGPT generated Code. I have never used numpy, pandas or matplotlib. :-)
"""


import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.dates import DateFormatter
from tkinter import Tk, simpledialog

# Check if both CSV filename and Sensor Location are provided as command-line arguments
if len(sys.argv) != 3:
    print("Usage: ./script.py <csv_filename> <sensor_location>")
    print("\nThe sensor location is the name you gave for HT1Location, HT2Location, HT3Location ")
    print("\nOnly use one location at a time")
    print("\nExample: ./HT-Chart.py HT-sensor-log.csv \"Living Room\"")
    sys.exit(1)

# Extract command-line arguments
csv_filename = sys.argv[1]
sensor_location = sys.argv[2]

# Load your CSV data
df = pd.read_csv(csv_filename, parse_dates=['Timestamp'], date_format='%Y-%m-%d %H:%M:%S')
#df = pd.read_csv(csv_filename, parse_dates=['Timestamp'])
df.set_index('Timestamp', inplace=True)

# Filter the data based on the specified Sensor Location
df_filtered = df[df['Sensor Location'] == sensor_location]

# Get unique sensor types in the specified Sensor Location
sensor_types = df_filtered['Sensor Type'].unique()

# Specify individual colors for each sensor type
individual_colors = ['red', 'blue', 'green', 'orangered']

# Set the desired initial window size (width, height) in inches
initial_figsize = (10, 7)  # Adjust the values based on your preference

# Create a Tkinter window for date selection
root = Tk()
root.withdraw()  # Hide the main Tkinter window

# Date picker dialog
selected_date_str = simpledialog.askstring("Date Selection", "Enter Date (YYYY-MM-DD):\nLeave blank for all days")
try:
    selected_date = pd.to_datetime(selected_date_str).date()
except (TypeError, ValueError) as e:
    print(f"Error parsing date: {e}")
    selected_date = None



# Check if the entered date is valid
if pd.isnull(selected_date):
    print("Invalid date format or empty. Showing all days.")
    selected_date = pd.Timestamp(df.index.min())

# Create the main plot window
fig_main, ax_main = plt.subplots(figsize=initial_figsize)

# Fine-tune the layout of the subplot to adjust the inside plot area
fig_main.subplots_adjust(left=0.055, right=1, bottom=0.2, top=0.95)

# Background color for the window area
fig_main.set_facecolor('darkgray')

# Background color for the plot area
ax_main.set_facecolor('#353434')

# Get the existing toolbar instance
toolbar = fig_main.canvas.manager.toolbar

# Activate the pan button
toolbar.pan()

# Plot each sensor type with a specified color
lines = []
for i, sensor_type in enumerate(sensor_types):
    df_filtered_temp = df_filtered[df_filtered['Sensor Type'] == sensor_type]
    x = df_filtered_temp.index.values
    y = df_filtered_temp['Sensor Value'].values
    line, = ax_main.plot(x, y, marker='o', label=f'{sensor_location} - {sensor_type}', color=individual_colors[i])
    lines.append(line)

# Format the timestamp on the x-axis
date_form = DateFormatter("%Y-%m-%d %H:%M:%S")
ax_main.xaxis.set_major_formatter(date_form)

# Increase the bottom margin to accommodate the angled timestamps
plt.subplots_adjust(bottom=0.2)

# Function to update annotation on mouse hover
def update_annot(event):
    visible_lines = [line for line in lines if line.contains(event)[0]]
    if visible_lines:
        line = visible_lines[0]
        x, y = line.get_data()
        ind = line.contains(event)[1]["ind"][0]
        timestamp_str = pd.to_datetime(str(x[ind])).strftime("%Y-%m-%d %H:%M:%S")
        text = f"({timestamp_str}, {y[ind]:.2f})"
        annot.xy = (x[ind], y[ind])
        annot.set_text(text)
        annot.set_visible(True)
        fig_main.canvas.draw_idle()
    else:
        annot.set_visible(False)
        fig_main.canvas.draw_idle()

# Function to handle mouse motion
def hover(event):
    if event.inaxes == ax_main:
        update_annot(event)

# Connect the hover function to the motion_notify_event
fig_main.canvas.mpl_connect("motion_notify_event", hover)

# Add annotation
annot = ax_main.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points", bbox=dict(boxstyle="round", fc="w"))

# Set labels and title
ax_main.set_xlabel('Timestamp')
ax_main.set_ylabel('Sensor Value')
ax_main.set_title(f'{sensor_location} Sensor Data')

# Set window title using manager.set_window_title
fig_main.canvas.manager.set_window_title(f'HT-Sensor - {sensor_location} Data')

# Rotate x-axis labels for better alignment
ax_main.tick_params(axis='x', rotation=45)  # Remove ha='right'

# Increase the bottom margin to accommodate the rotated timestamps
plt.subplots_adjust(bottom=0.25)  # Adjust the value as needed

# Adjust the alignment of x-axis tick labels
for label in ax_main.get_xticklabels():
    label.set_horizontalalignment('right')

# Add legend
leg = ax_main.legend()
leg.set_draggable(True)

# Function to update the main plot based on the selected date
def update_date(selected_date):
    ax_main.set_xlim(selected_date, selected_date + pd.Timedelta(days=1))  # Adjust the duration as needed
    fig_main.canvas.draw_idle()

# Function to handle mouse double-click event for date selection
def on_date_picker_click(event):
    if event.dblclick:
        selected_date_str = simpledialog.askstring("Date Selection", "Enter Date (YYYY-MM-DD):")
        if selected_date_str:
            selected_date = pd.to_datetime(selected_date_str, errors='coerce').date()
            update_date(selected_date)

# Connect the on_date_picker_click function to the button_press_event
fig_main.canvas.mpl_connect("button_press_event", on_date_picker_click)

# Function to reset zoom on "Home" button press
# Function to reset zoom to include all days
def reset_zoom_all_days(event):
    ax_main.relim()
    ax_main.autoscale_view()
    ax_main.set_xlim(df.index.min(), df.index.max())  # Set limits to include all days
    fig_main.canvas.draw_idle()

# Function to handle the date picker button click
def on_date_picker_button_click(event):
    selected_date_str = simpledialog.askstring("Date Selection", "Enter Date (YYYY-MM-DD):")
    if selected_date_str:
        selected_date = pd.to_datetime(selected_date_str, errors='coerce').date()
        update_date(selected_date)

# Create a custom home button with hover color
home_ax = plt.axes([0.87, 0.01, 0.12, 0.04])  # Adjust the position and size as needed
home_button = Button(home_ax, 'Show All Days', color='#353434', hovercolor='green')  # Specify the normal and hover color

# Create a custom date picker button with hover color
date_picker_ax = plt.axes([0.75, 0.01, 0.12, 0.04])  # Adjust the position and size as needed
date_picker_button = Button(date_picker_ax, 'Pick Date', color='#353434', hovercolor='blue')  # Specify the normal and hover color

# Connect the custom date picker button to the on_date_picker_button_click function
date_picker_button.on_clicked(on_date_picker_button_click)

# Connect the custom home button to the reset_zoom_all_days function
home_button.on_clicked(reset_zoom_all_days)

# Update the main plot with the selected date
update_date(selected_date)

# Show the plot using plt.show() to launch the interactive window
plt.show(block=True)
