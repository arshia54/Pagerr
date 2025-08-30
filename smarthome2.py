from operator import imul
import sys
sys.path.append("C:\Program Files\Webots\lib\controller\python")
from controller import Robot,DistanceSensor
from controller import Motor
from controller import PositionSensor
from termcolor import colored
from datetime import timedelta
from termcolor import cprint
import time
import math
from datetime import datetime
import numpy as np
import struct
from random import *



Compass =  0
PositionX = 0
PositionY = 0
FrontLeft = 0
FrontRight = 0
RightFront = 0
RightBack = 0
BackLeft = 0
BackRight = 0
LeftBack = 0
LeftFront = 0
zaman = 0
Battery = 0
state = ""
velesh_kon = 0
chargepathcounter = 0
chargecondition = False
boro_be_otagh = 0
boro_be_otagh = False
Front = 0 
ForntLeft = 0
Back = 0
BackLeft = 0
Back = 0
BackRight = 0
Right =  0
FrontRight = 0
re = 0
le = 0
abcd = 0
konj = 0



Matrix = [[0 for x in range(100)] for y in range(100)]
zavievaisadan = 180
vaccume_state = "FOLLOWPATH"
jabejaflag = 0
countervaisadan = 0


#---------------------------------------------------------------------------------------------------------------# 
#INIT
robot = Robot() # Create robot object
timeStep = int(robot.getBasicTimeStep()) 
maxSpeed = 6.28

wheel_left = robot.getDevice("wheel1 motor")
wheel_left.setPosition(float('inf'))

wheel_right = robot.getDevice("wheel2 motor") 
wheel_right.setPosition(float('inf'))

distanceSensor1 = robot.getDevice("D1")
distanceSensor1.enable(timeStep) 

distanceSensor2 = robot.getDevice("D2")
distanceSensor2.enable(timeStep) 

distanceSensor3 = robot.getDevice("D3")
distanceSensor3.enable(timeStep) 

distanceSensor4 = robot.getDevice("D4")
distanceSensor4.enable(timeStep) 

distanceSensor5 = robot.getDevice("D5")
distanceSensor5.enable(timeStep) 

distanceSensor6 = robot.getDevice("D6")
distanceSensor6.enable(timeStep) 

distanceSensor7 = robot.getDevice("D7")
distanceSensor7.enable(timeStep) 

distanceSensor8 = robot.getDevice("D8")
distanceSensor8.enable(timeStep) 

iuSensor = robot.getDevice("inertial_unit") 
iuSensor.enable(timeStep)

gpsSensor = robot.getDevice("gps") 
gpsSensor.enable(timeStep)

receiver = robot.getDevice("receiver")
receiver.setChannel(1)
receiver.enable(timeStep)

leftEncoderSensor = wheel_left.getPositionSensor()
rightEncoderSensor = wheel_right.getPositionSensor()
leftEncoderSensor.enable(timeStep)
rightEncoderSensor.enable(timeStep)


# TEAM NAME
emitter = robot.getDevice("emitter")
emitter.setChannel(1)
emitter.send('KONTASH'.encode('utf-8'))
#---------------------------------------------------------------------------------------------------------------#



#FUNCTIONS
def rad2deg(rad):
    return (rad/3.14)*180



def vastazavie(x):
    global countervaisadan



    if x+0.5>=comp>=x-0.5 :

        countervaisadan = 0
        return True
    else:
        x_comp = x-comp

        # # print("zavie vaisadan: " , x)
        # # print("comp: " , comp)
        if x_comp < 0:
            # # print("omadam in to")
            x_comp = x_comp + 360          
            # # print("x-comp: " , x_comp)  
        if x_comp > 180:
            # # print("charkhesh samt rast")
            move(-5,5) #charkhesh samt rast
        if x_comp <= 180:
            # # print("x-comp: " , x_comp)
            # # print("charkhesh samt chap")
            move(5,-5) #charkhesh samt chap



def sharj():
    global shoroo, shoroox, shorooy
    shoroox = gpsDevice.getValues()[0]
    shorooy = gpsDevice.getValues()[2]
    shoroo = 1



def jolo():
    if FrontRight <= 14 or FrontLeft <= 14:
        return False

    else:
        return True

def check():
    global Gpsx, Gpsy, counter, mapsended , zavievaisadan , countervaisadan,comp,jabejaflag,vaccume_state
    
    

    if jolo()==False and countervaisadan == 0:
        # # print("raftam to check")
        zavievaisadan = comp + randint(180 - 100 , 180 + 100)
        if zavievaisadan >= 360 :
            zavievaisadan =  zavievaisadan - 360
        countervaisadan = 1
    





def readSensorsPrimary():
    global Compass,Front,ForntLeft,Left,BackLeft,Back,BackRight,Right,FrontRight
    global US_Front,US_Left,US_Right
    Compass =  (rad2deg(iuSensor.getRollPitchYaw()[2]) + 360 )% 360

    Front = int(distanceSensor1.getValue() * 10 * 32)
    ForntLeft = int(distanceSensor2.getValue() * 10  * 32)
    Left = int(distanceSensor3.getValue() * 10 * 32)
    BackLeft = int(distanceSensor4.getValue()* 10 * 32)
    Back = int(distanceSensor5.getValue()* 10 * 32)
    BackRight = int(distanceSensor6.getValue()* 10 * 32)
    Right = int(distanceSensor7.getValue() * 10  * 32)
    FrontRight = int(distanceSensor8.getValue() * 10 * 32)
    US_Front = Front
    US_Left = FrontLeft
    US_Right = FrontRight




def debugPrimary():
    global Compass,Front,ForntLeft,Back,BackLeft,Back,BackRight,Right,FrontRight


def readSensors():
    global Compass,PositionX,PositionY,FrontLeft,FrontRight,RightFront,RightBack,BackLeft,BackRight,LeftBack,LeftFront,le,re, Battery
    Compass =  (rad2deg(iuSensor.getRollPitchYaw()[2]) + 360 )% 360
    PositionX = gpsSensor.getValues()[0] * 100
    PositionY = gpsSensor.getValues()[2] * 100
    FrontLeft = int(distanceSensor1.getValue() * 10 * 32)
    FrontRight = int(distanceSensor8.getValue() * 10 * 32)
    RightFront = int(distanceSensor7.getValue() * 10 * 32)
    RightBack = int(distanceSensor6.getValue()* 10 * 32)
    BackLeft = int(distanceSensor3.getValue()* 10 * 32)
    BackRight = int(distanceSensor5.getValue()* 10  * 32)
    LeftBack = int(distanceSensor4.getValue() *10 * 32)
    LeftFront = int(distanceSensor2.getValue()*10 * 32)
    le = leftEncoderSensor.getValue() 
    re = rightEncoderSensor.getValue()

    if receiver.getQueueLength() > 0:
        received_data = receiver.getString()
        if len(received_data) > 0:
            Battery = float(received_data) 
        receiver.nextPacket()


def debug():
    global Compass, PositionX, PositionY, FrontLeft, FrontRight, RightFront, RightBack, BackLeft, BackRight, LeftBack, LeftFront, Battery

    print()
    cprint("---------------------------------------", "cyan", )
    cprint("------------------ Debug --------------", "cyan", )
    cprint("---------------------------------------", "cyan", )
    print()
    cprint("---------------- Battery -------------", "yellow", )
    cprint(Battery, "yellow", )
    print()
    cprint("---------------- Distance -------------", "yellow", )
    cprint("            FrontLeft: " + str(FrontLeft) + " , FrontRight: " + str(FrontRight), "yellow")
    cprint("LeftFront: " + str(LeftFront) + "                            RightFront: " + str(RightFront), "yellow")
    cprint("LeftBack:  " + str(LeftBack) + "                             RightBack:  " + str(RightBack), "yellow")
    cprint("            BackLeft: " + str(BackLeft) + " ,  BackRight:  " + str(BackRight), "yellow")
    cprint("-----------------  GPS  ---------------", "cyan")
    cprint("X: " + str("%.2f " % PositionX) + "           Y: " + str("%.2f " % PositionY), "blue")
    cprint("----------------- Compass -------------", "yellow")
    cprint("Compass: " + str("%.0f " % Compass), "yellow")
    cprint("------------------ Time ---------------", "yellow")
    cprint("Time: " + str(robot.getTime()), "yellow")
timeon = robot.getTime()

def move (left,right,dur=0):
    global zaman
    wheel_right.setVelocity(right * maxSpeed/10)
    wheel_left.setVelocity(left * maxSpeed/10)
    zaman = dur




def eslah(alpha):
    if alpha > 360:
        alpha = alpha - 360
    if alpha < 0 :
        alpha = alpha + 360
    return alpha

def dist(x1,y1,x2,y2):
    return math.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))

#baraye move robot
def tan2alpha(x,y):
    global Compass
    comp = Compass
    alpha = math.atan2( x-gpsx, y-gpsy)
    alpha = rad2deg(alpha)
    alpha = alpha - 180


    alpha = eslah(alpha)


    deg = alpha
    mindeg = deg-3
    maxdeg = deg+3


    mindeg = eslah(mindeg)
    maxdeg = eslah(maxdeg)



    if dist(x,y,gpsx,gpsy) < 1:#...........................................................................................................................................................

        return True


    if mindeg < maxdeg:
        if mindeg<comp and comp < maxdeg:
            move(10,10)
        else:
            if (eslah(deg-comp)<180):
                if(eslah(deg-comp)<3):
                    move(10,0)
                elif(eslah(deg-comp)<10):
                    move(3,-3)
                else:
                    move(10,-10)
            else:
                if (eslah(deg-comp)>357):
                    move(0,10)
                elif (eslah(deg-comp)>350):
                    move(-3,3)
                else:
                    move(-10,10)


    if mindeg > maxdeg:
        if mindeg < comp or maxdeg > comp:
            move(10,10)
        else:
            if (eslah(deg-comp)<180):
                if(eslah(deg-comp)<1):
                    move(10,0)
                elif(eslah(deg-comp)<10):
                    move(3,-3)
                else:
                    move(10,-10)
            else:
                if (eslah(deg-comp)>359):
                    move(0,10)
                elif (eslah(deg-comp)>350):
                    move(-3,3)
                else:
                    move(-10,10)
    return False
#---------------------halat adi
def standard():
    global zaman, state
    if(zaman > 0):
            zaman = zaman - 1

            
    elif(state == "turn"):
        if (randint(0,1) == 0):
            move(10,-10,25)
        else:
            move(-10,10,25)
        state = ""

    elif(FrontLeft < 30 and FrontRight  < 30):
        move(-10,-10,25)
        konj = 1
        if konj == 1:
            move(-10, 10, 15)
            konj = 0
        state = "turn"
        
    elif(FrontLeft < 30):
        move(-10,10,15)

    elif(FrontRight < 30):
        move(10,-10,15)
    else:
        if (50>Battery):
            move(10,9,0)
        elif (50<Battery):
            move(9,10,0)
#-----------------------------------dar halat noghte raftan
# def standard():
#     global zaman, state
#     if(zaman > 0):
#             zaman = zaman - 1

            
#     elif(state == "turn"):
#         if (randint(0,1) == 0):
#             move(10,-10,25)
#         else:
#             move(-10,10,25)            
#         state = ""

#     elif(FrontLeft < 35 and FrontRight  < 35):
#         move(-10,-10,25)
#         konj = 1
#         if konj == 1:
#             move(-10, 10, 15)
#             konj = 0
#         state = "turn"
        
#     elif(FrontLeft < 35):
#         move(-10,10,15)

#     elif(FrontRight < 35):
#         move(10,-10,15)
#     else:
#         if (50>gametime):
#             move(10,9,0)
#         elif (50<gametime):
#             move(9,10,0)

#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#-----------------------------------------#mahal sharj#---------------------------------------------------------------------

roomlist = [(-74, 19, -36, 83, 1), (-72, -90, -13, 16, 2), (-11, -89, 26, -9, 3), (-12, -10, 25, 16, 4), (-25, 20, 25, 84, 5), (-35, 19, -25, 86, 6)]
room1path = [(-89,77),(-77,114),(-16,114),(-15,15),(-98,15)]
room2path = [(-15,76),(-16,9),(-98,15)]
room3path = [(-15,79),(-14,31),(-20,-18),(-69,-56),(-96,-97)]
room4path = [(43,64),(2,40),(-14,39),(-17,0),(-20,-40),(-43,-67),(-86,-83),(-96,-95)]
room5path = [(69,12),(-8,10),(-38,-31),(-68,-63),(-97,-96)]
room6path = [(103,-51),(77,-79),(43,-109),(33,-114),(12,-111),(-37,-108),(-96,-96)]

#-----------------------------------------------------------------------------------------------------------

helperpath1 = [[]]

#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------#
#MAINWHILE
shoroo = 0
starttime = 0
gametime = 0
pathcounter = 0
timetodest = 0
TIMETEL = 1000
last_vaccum_state = ""
VELTIME = 100
girvelkontime = VELTIME

def sharj():
    global starttime 
    starttime = robot.getTime()
while robot.step(timeStep) != -1:
    print(vaccume_state)


    debug()

    if shoroo == 0 :
        shoroo = 1
        sharj()
    gametime = robot.getTime() - starttime 
    readSensors()


#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#-----------------------------------------#che moghe beram sharj??????#---------------------------------------------------------------------
    # debug()
    if Battery < 19:    ######## if(19 < battery < 20 and timeon > 351),gametime < 450

        chargecondition = True

    else: 
        chargecondition = False
#--------------------------------------------------------------------------------------------------------------#


#---------------------------------------------------------------------------------------------------------------#

    comp = Compass
    gpsy = (PositionY)
    gpsx = (PositionX)

    if(vaccume_state == "GOBACK"):
        print ("go back counter ->", chargepathcounter,"/",len(chargepath) )
        print ("velesh_kon", velesh_kon )
        timetodest = timetodest + 1
        # # # print ("timetodest = ",timetodest)
         
        if(chargepathcounter == len(chargepath) - 1 and(FrontLeft < 30 or FrontRight<30)):
            velesh_kon = 100
        if (chargepathcounter == len(chargepath) - 1 and velesh_kon > 0):
            standard()
            velesh_kon = velesh_kon-1
        else:
            if chargepathcounter == len(chargepath):
                vaccume_state = "FOLLOWPATH"
                chargepathcounter = 0
                timetodest = 0
            elif timetodest > TIMETEL:
                # # # print("---------------TEL-------------------------chargepathcounter: "*5,chargepathcounter)
                chargepathcounter += 1
                timetodest = 0
    
            
            elif tan2alpha(chargepath[chargepathcounter][0],chargepath[chargepathcounter][1]):
                # # print("chargepathcounter: ",chargepathcounter)
                chargepathcounter += 1
                timetodest = 0



    if(vaccume_state == "GO_TO_CHARGER"):
        print ("go charge counter ->", chargepathcounter )
        print ("velesh_kon", velesh_kon )
        timetodest = timetodest + 1
        # # # print ("timetodest = ",timetodest)
        if(chargepathcounter == 0 and(FrontLeft < 30 or FrontRight<30)):
            velesh_kon = 100
        if (chargepathcounter == 0 and velesh_kon > 0):
            standard()
            velesh_kon = velesh_kon-1
        else:
            if chargepathcounter == len(chargepath):
                vaccume_state = "GOBACK"
                chargepath.reverse()
                print("reversed ->",chargepath)
                chargepathcounter = 0
                timetodest = 0
            elif timetodest > TIMETEL:
                # # # print("---------------TEL-------------------------chargepathcounter: "*5,chargepathcounter)
                chargepathcounter += 1
                timetodest = 0
    
            
            elif tan2alpha(chargepath[chargepathcounter][0],chargepath[chargepathcounter][1]):
                # # print("chargepathcounter: ",chargepathcounter)
                chargepathcounter += 1
                timetodest = 0
    elif(vaccume_state=="CHARGE_SELECT_PATH"):
        for x1,y1,x2,y2,n in roomlist:
            if(x1<gpsx<x2 and y1<gpsy<y2 ):
                shomare_otagh = n

#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#-----------------------------------------#sharj#---------------------------------------------------------------------

            
        if shomare_otagh == 1:
            chargepath = room1path

        elif shomare_otagh == 2:
            chargepath = room2path

        elif shomare_otagh == 3:
            chargepath = room3path

        elif shomare_otagh == 4:
            chargepath = room4path

        elif shomare_otagh == 5:
            chargepath = room5path 

        elif shomare_otagh == 6:
            chargepath = room6path
        
        # elif shomare_otagh == 7:
        #     chargepath = room7path
        

#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------

        # # print("room selected ->",shomare_otagh)
        vaccume_state = "GO_TO_CHARGER"   

        
    elif vaccume_state=="FOLLOWPATH":
        print (gpsx,gpsy," -> ",helperpath1[pathcounter][0],helperpath1[pathcounter][1],"[",pathcounter,"]")
        timetodest = timetodest + 1
        # # # print ("timetodest = ",timetodest)
        if chargecondition:
            vaccume_state = "CHARGE_SELECT_PATH"

        elif pathcounter == len(helperpath1):
            vaccume_state = "RANDOM"
            pathcounter = 0
            timetodest = 0
        elif timetodest > TIMETEL: #or dist(normalpath[pathcounter][0],normalpath[pathcounter][1],gpsx,gpsy) < 2 :
            # # # print("---------------TEL-------------------------pathcounter: "*5,pathcounter)
            pathcounter += 1
            timetodest = 0
        
        elif tan2alpha(helperpath1[pathcounter][0],helperpath1[pathcounter][1]):
            # # print("pathcounter: ",pathcounter)
            pathcounter += 1
            timetodest = 0
        
    elif vaccume_state=="ALPHA":
 
        
        if(FrontLeft < 30 or FrontRight<30):
            velesh_kon = 100
        if velesh_kon > 0:
            standard()
            velesh_kon = velesh_kon - 1
        else:
            tan2alpha(100,100)
        
            

    elif vaccume_state=="RANDOM":
        standard()
        
        if chargecondition:
            vaccume_state = "CHARGE_SELECT_PATH"
        






      


