import tkinter as tk
from tkinter import messagebox
from djitellopy import tello
import cv2
import numpy as np
import time
import logging
from simple_pid import PID
import math

# Tag and search configuration
tag_list = []
tag_ID = [1, 2, 3, 4, 5]
TAG_SIZE_CM = 17
GRID_SIZE = 100
SPIRAL_RADIUS = 50
FRAME_SIZE = [960, 720]
PATH = []
FOCAL_LENGTH = 500
SEARCH_ALTITUDE = 70  

# PID setup with dynamic tuning
pid_x = PID(0.4, 0.0, 0.2, setpoint=0)
pid_y = PID(0.4, 0.0, 0.2, setpoint=0)
pid_distance = PID(0.5, 0.0, 0.3, setpoint=50)
pid_yaw = PID(0.5, 0.0, 0.2, setpoint=0)

pid_x.output_limits = (-25, 25)
pid_y.output_limits = (-25, 25)
pid_distance.output_limits = (-20, 20)
pid_yaw.output_limits = (-20, 20)

# Initialize Tello
robot = tello.Tello()
robot.LOGGER.setLevel(logging.ERROR)
robot.connect()
robot.streamon()
robot_frame = robot.get_frame_read(with_queue=False)
robot.takeoff()

# Variables for state and search control
state = 'SEARCH'
tag_now = 0
time_to_see = time.time()
search_mode = 'GRID'
search_direction = 1
current_position_x = 0
current_position_y = 0

# Trigonometric and helper functions
def calculate_cos(angle):
    return math.cos(math.radians(angle))

def calculate_sin(angle):
    return math.sin(math.radians(angle))

def calculate_tan(angle):
    return math.tan(math.radians(angle))

def calculate_distance(tag_size_px, known_tag_size_cm=TAG_SIZE_CM):
    return (known_tag_size_cm * FOCAL_LENGTH) / tag_size_px

# Function to calculate the angle to the second tag
def calculate_angle_to_tag(current_x, current_y, target_x, target_y):
    delta_x = target_x - current_x
    delta_y = target_y - current_y
    angle = math.degrees(math.atan2(delta_y, delta_x))  # Angle in degrees
    return angle

# Tkinter GUI setup
root = tk.Tk()
root.title("TELLO CONTROLLING PAD")

# GUI Widgets for Real-time Feedback and Controls
status_label = tk.Label(root, text="Status: Idle", font=("Helvetica", 12))
status_label.grid(row=0, column=0, columnspan=2)

battery_label = tk.Label(root, text="Battery: Updating...", font=("Helvetica", 12))
battery_label.grid(row=1, column=0, columnspan=2)

height_label = tk.Label(root, text="Height: 0 cm", font=("Helvetica", 12))
height_label.grid(row=2, column=0, columnspan=2)

# PID Adjustment sliders
def update_pid_constants():
    pid_x.tunings = (x_kp.get(), x_ki.get(), x_kd.get())
    pid_y.tunings = (y_kp.get(), y_ki.get(), y_kd.get())
    pid_distance.tunings = (distance_kp.get(), distance_ki.get(), distance_kd.get())
    pid_yaw.tunings = (yaw_kp.get(), yaw_ki.get(), yaw_kd.get())

tk.Label(root, text="PID Tuning").grid(row=3, column=0, columnspan=2)
x_kp, x_ki, x_kd = tk.DoubleVar(value=0.4), tk.DoubleVar(value=0.0), tk.DoubleVar(value=0.2)
y_kp, y_ki, y_kd = tk.DoubleVar(value=0.4), tk.DoubleVar(value=0.0), tk.DoubleVar(value=0.2)
distance_kp, distance_ki, distance_kd = tk.DoubleVar(value=0.5), tk.DoubleVar(value=0.0), tk.DoubleVar(value=0.3)
yaw_kp, yaw_ki, yaw_kd = tk.DoubleVar(value=0.5), tk.DoubleVar(value=0.0), tk.DoubleVar(value=0.2)

for i, (var, label) in enumerate([(x_kp, "X KP"), (x_ki, "X KI"), (x_kd, "X KD"),
                                  (y_kp, "Y KP"), (y_ki, "Y KI"), (y_kd, "Y KD"),
                                  (distance_kp, "Dist KP"), (distance_ki, "Dist KI"), (distance_kd, "Dist KD"),
                                  (yaw_kp, "Yaw KP"), (yaw_ki, "Yaw KI"), (yaw_kd, "Yaw KD")]):
    tk.Label(root, text=label).grid(row=4 + i, column=0)
    tk.Scale(root, from_=0.0, to=2.0, resolution=0.01, variable=var, orient=tk.HORIZONTAL, command=lambda x: update_pid_constants()).grid(row=4 + i, column=1)

# Start Search Modes
def start_tag_search():
    global state
    state = 'TAG'
    status_label.config(text="Status: Searching for Tag")

def start_grid_search():
    global state, search_mode
    search_mode = 'GRID'
    state = 'SEARCH'
    status_label.config(text="Status: Grid Searching")

def start_spiral_search():
    global state, search_mode
    search_mode = 'SPIRAL'
    state = 'SEARCH'
    status_label.config(text="Status: Spiral Searching")

tk.Button(root, text="Start TAG Search", command=start_tag_search).grid(row=16, column=0)
tk.Button(root, text="Start GRID Search", command=start_grid_search).grid(row=16, column=1)
tk.Button(root, text="Start SPIRAL Search", command=start_spiral_search).grid(row=17, column=0, columnspan=2)

# Main loop for real-time control
def main_loop():
    global state, tag_now, time_to_see, current_position_x, current_position_y

    frame = cv2.resize(cv2.cvtColor(robot_frame.frame, cv2.COLOR_RGB2BGR), FRAME_SIZE)
    tags = []  # This should be updated with the detected tags in the frame
    height = robot.get_height()
    battery = robot.get_battery()

    # Update status labels
    battery_label.config(text=f"Battery: {battery}%")
    height_label.config(text=f"Height: {height} cm")

    if battery < 35:
        messagebox.showwarning("Battery Warning", "Battery is low! Landing drone.")
        print("BATTERY WARNING")
        robot.land()
        robot.streamoff()
        robot.end()
        root.destroy()
        return

    if state == 'TAG':
        seen = False
        for tag in tags:
            if tag[0] == tag_ID[tag_now]:  # Track the current tag
                # PID control for tag tracking
                velocity_x = pid_x(tag[1])
                velocity_y = pid_y(-tag[2])
                velocity_distance = pid_distance(tag[3])
                velocity_yaw = pid_yaw(tag[4])

                # Send control commands to the Tello
                robot.send_rc_control(int(velocity_x), int(velocity_distance), int(velocity_y), int(velocity_yaw))
                time_to_see = time.time()
                seen = True
                break

        if not seen:
            if time.time() - time_to_see > 4.0:
                # Once the first tag is lost, switch to the next tag
                tag_now = (tag_now + 1) % len(tag_ID)
                state = 'SEARCH'

    elif state == 'SEARCH':
        # Searching for a tag (either GRID or SPIRAL mode)
        seen = any(tag[0] == tag_ID[tag_now] for tag in tags)
        if seen:
            state = 'TAG'
            time_to_see = time.time()
        else:
            if search_mode == 'GRID':
                current_position_x += GRID_SIZE * search_direction
                if current_position_x >= 960 or current_position_x < 0:
                    current_position_x = 0
                    current_position_y += GRID_SIZE
            elif search_mode == 'SPIRAL':
                for angle in range(0, 360, 15):
                    robot.send_rc_control(
                        int(SPIRAL_RADIUS * calculate_cos(angle)),
                        int(SPIRAL_RADIUS * calculate_sin(angle)),
                        0, 20
                    )

    # If the first tag was tracked and lost, calculate the angle to the second tag
    if state == 'TAG' and tag_now == 0:  # If tracking the first tag (tag_ID[0])
        if time.time() - time_to_see > 4.0:
            # Switch to second tag and position the drone to approach it
            next_tag_position_x = 100  # Example values for the second tag's position (you need real data)
            next_tag_position_y = 200
            angle_to_second_tag = calculate_angle_to_tag(current_position_x, current_position_y, next_tag_position_x, next_tag_position_y)
            
            # Send commands to position the drone at the angle to the second tag
            robot.send_rc_control(0, 20, 0, int(angle_to_second_tag))

    cv2.imshow("FRAME", frame)
    if cv2.waitKey(1) == ord('q'):
        robot.streamoff()
        robot.land()
        root.destroy()

    root.after(100, main_loop)

# Run main loop
root.after(100, main_loop)
root.mainloop()
