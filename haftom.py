from djitellopy import tello
import cv2
import numpy as np
import time
import logging
import at

#---------------- ID OF TAGS ---------------- 

tag_ID = [0,1,2,3] 

#---------------- SETUP ---------------- 

robot = tello.Tello()
robot.LOGGER.setLevel(logging.ERROR)
robot.connect()

robot.streamon()
robot_frame = robot.get_frame_read(with_queue=False)

robot.takeoff()

time.sleep(3)


state = 'SEARCH'
tag_now = 0
time_to_see = time.time()
search_height = 'Down'

#---------------- MAIN WHILE ---------------- 

while True:
    frame = cv2.resize(cv2.cvtColor(robot_frame.frame , cv2.COLOR_RGB2BGR), (960,720))
    tags = at.get_tags()
    copy_frame = frame.copy()
    height = robot.get_height()

    #---------------- ---------------- ---------------- 
#i am one of the greatest 

    mistake_x = 0
    mistake_y = 0
    mistake_distance = 0
    mistake_yaw = 0
    
    velocity_x = 0
    velocity_y = 0
    velocity_distance = 0
    velocity_yaw = 0

    #---------------- GOTO TAG ---------------- 

    if state == 'TAG':
        seen = False

        for tag in tags:
            if tag[0] == tag_ID[tag_now]:

                #left and right
                mistake_x = tag[1]

                if mistake_x > 10:
                    velocity_x = 20

                elif mistake_x < -10:
                    velocity_x = -20

                else:
                    velocity_x = 0

                #up and down
                mistake_y = 0 - tag[2]

                if mistake_y > 10:
                    velocity_y = 30

                elif mistake_y < -10:
                    velocity_y = -30

                else:
                    velocity_y = 0

                #forward and backward
                mistake_distance = tag[3] - 50
           
                if mistake_distance > 15:
                    velocity_distance = 30

                elif mistake_distance < -15:
                    velocity_distance = -30

                else:
                    velocity_distance = 0

                #yaw : charkhesh
                mistake_yaw = tag[4]

                if mistake_yaw > 10:
                    velocity_yaw = 20

                elif mistake_yaw < -10:
                    velocity_yaw = -20

                else:
                    velocity_yaw = 0

                robot.send_rc_control(int(velocity_x),int(velocity_distance),int(velocity_y),int(velocity_yaw))

                time_to_see = time.time()
                seen = True # saw the tag
                break


        if seen == False:
            robot.send_rc_control(0,0,0,0)
            if (time.time() - time_to_see) > 4.0:                
                state = 'SEARCH'
                print('SEARCHING ON FIRE')
                
        else:
    
            if velocity_x == 0 and velocity_y == 0 and velocity_distance == 0 and velocity_yaw == 0:
                robot.send_rc_control(0,0,0,0)
                print('GO TO TAG')

                #Move Up
                while True:
                    time_to_UP = time.time()
                    robot.move_up(45)
                    if time.time() - time_to_UP > 1.0:
                        break

                #Move Forward
                while True:
                    time_Goto = time.time()
                    robot.move_forward(120)
                    if time.time() - time_Goto > 1.0:
                        break

                
                

                

                #//////////////////////////////////////////////////////
                #//////////////////////////////////////////////////////
                #/////////////////////////////////////////////////////

            
                #////////////////////////////////////////////////////
                #///////////////////////////////////////////////////
                #//////////////////////////////////////////////////

                tag_now = tag_now + 1
                if tag_now >= len(tag_ID):
                    #State landing (Save H)
                    #robot.move_forward(250)
                    #robot.move_left(110)

                    robot.land()
                    break
            
        
    #---------------- SEARCH MODE ----------------
    

    elif state == 'SEARCH':
        seen = False
    #     robot.send_rc_control(0,0,35,0)

    # if seen == False:
    #     robot.send_rc_control(0,0,-35,0)



        for tag in tags:
            if tag[0] == tag_ID[tag_now]:
                seen = True
                break

        if seen == True:
            robot.send_rc_control(0,0,0,0)
            time_to_see = time.time()
            state = 'TAG'

            print("TAG FOUND")

        else:
            if height > 123:
                search_height = 'Down'

            elif height < 50:
                search_height = 'Up'

            if search_height == 'Up':
                robot.send_rc_control(0, 0, 45, -30)
                print("Up")
            else : 
                robot.send_rc_control(0, 0, -45, -30)
                print("Down")
            


    #---------------- SHOW IMAGE ---------------- 

    battery = robot.get_battery()
    
    if abs(battery) < 40:
        robot.land()
        robot.end()

    print("Battery : ", battery)
    print()
    print("Battery : ", battery)
    print()

    cv2.imshow('OUT', copy_frame)
    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    
robot.streamoff()
robot.land()
robot.end()


























