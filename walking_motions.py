#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

"""Example: Move To - Small example to make Nao Move To an Objective"""

import qi
import argparse
import sys
import math
import almath


def main(session):
    """
    Move To: Small example to make Nao Move To an Objective.
    """
    # Get the services ALMotion & ALRobotPosture.

    motion_service = session.service("ALMotion")
    posture_service = session.service("ALRobotPosture")
    
    # Wake up robot
    if not motion_service.robotIsWakeUp():
        motion_service.wakeUp()
        posture_service.goToPosture("StandInit", 0.5)
   
    motion_service.setMoveArmsEnabled(True, True)
    motion_service.setMotionConfig([["ENABLE_FOOT_CONTACT_PROTECTION", True]])
        
    
    # Send robot to Stand Init
    

    #####################
    ## Enable arms control by move algorithm
    #####################
    
    #~ motion_service.setMoveArmsEnabled(False, False)

    #####################
    ## FOOT CONTACT PROTECTION
    #####################
    #~ motion_service.setMotionConfig([["ENABLE_FOOT_CONTACT_PROTECTION",False]])
   

    #####################
    ## get robot position before move
    #####################
    initRobotPosition = almath.Pose2D(motion_service.getRobotPosition(False))
    if motion_type == 'TurnL':
        motion_service.waitUntilMoveIsFinished()
        X = 0
        Y = 0
        Theta = math.pi/2.0
        motion_service.moveTo(X, Y, Theta, _async=True)
    # wait is useful because with _async moveTo is not blocking function
        
    elif motion_type == 'WalkS':
        motion_service.waitUntilMoveIsFinished()
        X = 0.75
        Y = 0
        Theta = 0
        motion_service.moveTo(X, Y, Theta, _async=True)
    
    elif motion_type == 'TurnR':
        motion_service.waitUntilMoveIsFinished()
        X = 0
        Y = 0
        Theta = math.pi/-2.0
        motion_service.moveTo(X, Y, Theta, _async=True)


   # if motion_final:
    #    motion_service.rest()
    #else:
     #   posture_service.goToPosture("Stand", 1)

    motion_service.waitUntilMoveIsFinished()

    # Go to rest position
    #motion_service.rest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")
    parser.add_argument("--motion", type=str,default="straight",
                        help="Motion that you want to play")
    parser.add_argument("--final", type=bool,default=False,
                        help="Whether you want the robot to rest after this motion")


    

    args = parser.parse_args()
    motion_type = args.motion
    motion_final = args.final
    print(motion_type)
    session = qi.Session()
    try:
        session.connect("tcp://" + args.ip + ":" + str(args.port))
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) +".\n"
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    main(session)
