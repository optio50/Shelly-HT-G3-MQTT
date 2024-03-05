#!/usr/bin/env python3
import sys
from tkinter import Toplevel, StringVar, ttk
import pandas as pd
#import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.dates import DateFormatter
from tkcalendar import Calendar

# Check if CSV filename is provided as a command-line argument
if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <csv_filename>")
    sys.exit(1)

# Extract command-line argument
csv_filename = sys.argv[1]

# Load your CSV data
try:
    df = pd.read_csv(
        csv_filename, parse_dates=["Timestamp"], date_format="%Y-%m-%d %H:%M:%S"
    )
    df.set_index("Timestamp", inplace=True)
except Exception as e:
    print(f"Error loading CSV file: {e}")
    sys.exit(1)

current_location = df["Sensor Location"].unique()[0]

# Get unique sensor locations
sensor_locations = df["Sensor Location"].unique()

# Set the desired initial window size (width, height) in inches
initial_figsize = (10, 7)  # Adjust the values based on your preference

# Create the main plot window
fig_main, ax_main = plt.subplots(figsize=initial_figsize)

# Fine-tune the layout of the subplot to adjust the inside plot area
fig_main.subplots_adjust(left=0.055, right=1, bottom=0.2, top=0.95)

# Background color for the window area
fig_main.set_facecolor("darkgray")

# Background color for the plot area
ax_main.set_facecolor("#353434")

# Plot each sensor type with a specified color
lines = []
sensor_types = df["Sensor Type"].unique()
individual_colors = ["red", "blue", "green", "orangered"]
for i, sensor_type in enumerate(sensor_types):
    df_filtered_temp = df[df["Sensor Type"] == sensor_type]
    x = df_filtered_temp.index.values
    y = df_filtered_temp["Sensor Value"].values
    (line,) = ax_main.plot(
        x, y, marker="o", label=f"{sensor_type}", color=individual_colors[i]
    )
    lines.append(line)

# Format the timestamp on the x-axis
date_form = DateFormatter("%Y-%m-%d %H:%M")
ax_main.xaxis.set_major_formatter(date_form)

# Increase the bottom margin to accommodate the angled timestamps
plt.subplots_adjust(bottom=0.2)

# Initialize selected_date as a list to allow modification within the set_date function
selected_date = [df.index.min()]

# Function to update the main plot based on the selected date
def update_date():
    ax_main.set_xlim(
        selected_date[0], selected_date[0] + pd.Timedelta(days=1)
    )  # Adjust the duration as needed
    fig_main.canvas.draw_idle()

# Function to reset zoom on "Home" button press
def reset_zoom_all_days(event):
    ax_main.relim()
    ax_main.autoscale_view()
    ax_main.set_xlim(df.index.min(), df.index.max())  # Set limits to include all days
    fig_main.canvas.draw_idle()

# Add annotation
annot = ax_main.annotate(
    "",
    xy=(0, 0),
    xytext=(20, 20),
    textcoords="offset points",
    bbox=dict(boxstyle="round", fc="w"),
)

# Function to open calendar dialog
def pick_date(event=None):  # Default event=None allows calling it without an event
    top = Toplevel()
    top.title("Date Selection")
    cal = Calendar(top, selectmode="day")
    cal.pack(padx=10, pady=10)

    # Function to set the selected date
    def set_date():
        selected_date[0] = pd.to_datetime(cal.get_date(), errors="coerce").date()
        update_date()
        top.destroy()

    ok_button = ttk.Button(top, text="OK", command=set_date)
    ok_button.pack(pady=10)

    # Function to update annotation on mouse hover
    def update_annot(event):
        if event.inaxes == ax_main:
            visible_lines = [line for line in lines if line.contains(event)[0]]
            if visible_lines:
                line = visible_lines[0]
                x, y = line.get_data()
                ind = line.contains(event)[1]["ind"][0]
                timestamp_str = pd.to_datetime(str(x[ind])).strftime("%Y-%m-%d %H:%M:%S")
                text = f"Date: {timestamp_str}\nValue: {y[ind]:.2f}"
                annot.xy = (x[ind], y[ind])
                annot.set_text(text)
                annot.set_visible(True)
                fig_main.canvas.draw_idle()
            else:
                annot.set_visible(False)
                fig_main.canvas.draw_idle()

    # Function to handle mouse motion
    def hover(event):
        update_annot(event)

    # Connect the hover function to the motion_notify_event
    fig_main.canvas.mpl_connect("motion_notify_event", hover)

    # Block execution until the calendar window is closed
    top.attributes('-topmost', True)
    top.grab_set()
    top.wait_window()

# Function to load chart data based on selected location
def load_chart_data(ax, sensor_location):
    df_filtered = df[df["Sensor Location"] == sensor_location]

    # Clear existing plots
    for line in lines:
        line.remove()

    lines.clear()

    # Plot each sensor type with a specified color
    for i, sensor_type in enumerate(sensor_types):
        df_filtered_temp = df_filtered[df_filtered["Sensor Type"] == sensor_type]
        x = df_filtered_temp.index.values
        y = df_filtered_temp["Sensor Value"].values
        (line,) = ax.plot(
            x,
            y,
            marker="o",
            label=f"{sensor_location} - {sensor_type}",
            color=individual_colors[i],
        )
        lines.append(line)

    # Update labels and title
    ax.set_title(f"{sensor_location} Sensor Data")

    # Redraw the legend
    leg = ax.legend()
    leg.set_draggable(True)

    # Update the plot
    fig_main.canvas.draw_idle()

# Function to handle "Select Location" button click
def select_location(event):
    # Open a dialog to pick a new location
    new_location = pick_location()
    if new_location is not None:
        # Load chart data for the new location
        load_chart_data(ax_main, new_location)

"""
# Function to handle "Show All Days" button click
def reset_zoom_all_days(event):
    ax_main.relim()
    ax_main.autoscale_view()
    ax_main.set_xlim(df.index.min(), df.index.max())  # Set limits to include all days
    fig_main.canvas.draw_idle()
"""

# Function to open a dialog for location selection
def pick_location():
    top = Toplevel()
    top.title("Select Location")
    label = ttk.Label(top, text="Choose a location:")
    label.pack(padx=10, pady=10)
    location_var = StringVar()

    # Use a Combobox to display unique values of "Sensor Location"
    location_combobox = ttk.Combobox(
        top, textvariable=location_var, values=tuple(sensor_locations), width=40, state="readonly"
    )
    location_combobox.pack(padx=10, pady=10)
    location_combobox.set(current_location)

    # Function to set the selected location
    def set_location():
        top.destroy()
        # Load chart data for the new location
        load_chart_data(ax_main, location_var.get())

    ok_button = ttk.Button(top, text="OK", command=set_location)
    ok_button.pack(pady=10)

    # Block execution until the location window is closed
    top.attributes('-topmost', True)
    top.grab_set()
    top.wait_window()

# Connect the custom "Select Location" button to the select_location function
select_location_ax = plt.axes([0.4, 0.01, 0.15, 0.04])
select_location_button = Button(select_location_ax,
                                "Select Location", color="#353434", hovercolor="blue")
select_location_button.on_clicked(select_location)
# Connect the custom "Show All Days" button to the reset_zoom_all_days function
home_ax = plt.axes([0.6, 0.01, 0.2, 0.04])
home_button = Button(home_ax, "Show All Days", color="#353434", hovercolor="green")
home_button.on_clicked(reset_zoom_all_days)

# Connect the custom "Select Date" button to the pick_date function
pick_date_ax = plt.axes([0.2, 0.01, 0.15, 0.04])
pick_date_button = Button(pick_date_ax, "Select Date", color="#353434", hovercolor="red")
pick_date_button.on_clicked(pick_date)

# Initialize the chart with the initial location
load_chart_data(ax_main, sensor_locations[0])

# Angle the bottom x-axis labels for better readability
for tick in ax_main.get_xticklabels():
    tick.set_rotation(25)
    tick.set_ha('right')


# Simulate "Select Date" button click before showing the main window
pick_date()

# Show the plot using plt.show() to launch the interactive window
plt.show()
