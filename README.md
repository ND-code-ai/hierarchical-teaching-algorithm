# hierarchical-teaching-algorithm 

To be able to run the code and algorithm several dependencies need to be installed:

Latest Python version: https://www.python.org/

For the naoqi package:
Python 2.7:
https://www.python.org/downloads/release/python-270/
Naoqi Python SDK (Python 2.7 only)
http://doc.aldebaran.com/2-5/dev/python/install_guide.html

SIC installation:
Carefully follow installation instructions, all dependencies are required
https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/260276225/Local+Installation#Installation

# The system currently only works with NAO robots

# To run the system on your local machine with a NAO robot do the following: 
1 - Run Docker then the robot-installer.jar and fill in the robots ip address

2 - Open (dont run!) the main_chaining_module.py file in a Python IDE of your choice (eg. VS code, Pycharm, Atom)

3 - Change the variable self.robot_ip in the class constructor to your current robots IP address

4 - Check if you motionkey file path is correct (for MacOS possibly remove the 'r' operator before the string)

5 - Run the main_chaining_module file

6 - Check all devices (camera not necessary)


