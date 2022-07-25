#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

"""Example: Walk - Small example to make Nao walk"""
from naoqi import ALProxy
import qi
import argparse
import sys
import motion
import time
import almath

def motion_joint_angles(motion_name):
    if motion_name == "LArmFront":
        Larm_deg_list = [-60, 0, 0, 0]
        Rarm_deg_list = False
    elif motion_name == "RArmFront":
        Larm_deg_list = False
        Rarm_deg_list = [-60, 0, 0, 0]  
    elif motion_name == "ArmsFront":
        Larm_deg_list = [-60, 0, 0, 0]              
        Rarm_deg_list = [-60, 0, 0, 0] 
    elif motion_name == "LArmSide":
        Larm_deg_list = [0, 76, 0, 0]              
        Rarm_deg_list = False
    elif motion_name == "RArmSide":
        Larm_deg_list = False              
        Rarm_deg_list = [0, -75, 0, 0] 
    elif motion_name == "ArmsSide":
        Larm_deg_list = [0, 75, 0, 0]              
        Rarm_deg_list = [0, -75, 0, 0] 
    return Larm_deg_list, Rarm_deg_list


def userArmArticular(motion_service):
    LArm_angles = motion_joint_angles(motion_name)[0]
    RArm_angles = motion_joint_angles(motion_name)[1]
    # Arms motion from user have always the priority than walk arms motion
    LJointNames = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll"]
    RJointNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll"]
    pFractionMaxSpeed = 0.6
    if LArm_angles:
        Arm1 = LArm_angles
        Arm1 = [ x * motion.TO_RAD for x in Arm1]
        motion_service.angleInterpolationWithSpeed(LJointNames, Arm1, pFractionMaxSpeed)

    if RArm_angles:
        Arm2 = RArm_angles
        Arm2 = [ x * motion.TO_RAD for x in Arm2]   
        motion_service.angleInterpolationWithSpeed(RJointNames, Arm2, pFractionMaxSpeed)


def main(session):
    """
    Walk - Small example to make Nao walk
    This example is only compatible with NAO
    """
    # Get the services ALMotion & ALRobotPosture.

    motion_service = session.service("ALMotion")
    posture_service = session.service("ALRobotPosture")

    # Wake up robot
    if not motion_service.robotIsWakeUp():
        motion_service.wakeUp()
        posture_service.goToPosture("StandInit", 0.5)
  

    # Send robot to Stand

    #####################
    ## Enable arms control by Motion algorithm
    #####################
    motion_service.setMoveArmsEnabled(True, True)
    # motion_service.setMoveArmsEnabled(False, False)

   # userArmArticular(motion_service)
    #time.sleep(1.0)
    userArmArticular(motion_service)



    # Go to rest position
    if motion_final:
        motion_service.rest()
    else:
        posture_service.goToPosture("Stand", 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")
    parser.add_argument("--motion", type=str,default="left_arm_side",
                        help="Motion that you want to play in format (which_arm_direction)")
    parser.add_argument("--final", type=bool,default=False,
                        help="Whether you want the robot to rest after this motion")


    args = parser.parse_args()
    session = qi.Session()
    motion_name = args.motion
    motion_final = args.final
    try:
        session.connect("tcp://" + args.ip + ":" + str(args.port))
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) +".\n"
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    main(session)
