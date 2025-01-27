#!/usr/bin/env python

import rospy
#from modbus_ascii_ros.msg import Pwm
from hg_ros_pololu.msg import Pwm
from geometry_msgs.msg import Twist
from geometry_msgs.msg import TwistWithCovarianceStamped
from sensor_msgs.msg import Joy
from numpy  import *
import LookUpPWM as lup
"""
t = [t0, t1, t2, t3, t4, t5, t6, t7]
F = [Fx, Fy, Fz, Mx, My, Mz]
"""

pwm_publisher = 0
d = 0 #d = direction of each thruster
r = 0 #r = distance from origin to each thruster
T = 0 #T = matrix map thruster forces to robot force
M = 0 #M = matrix map robot force to thruster forces

class thrust_mapper:
    def __init__(self):
	rospy.init_node('thrust_mapper')
	self.pwm_publisher = rospy.Publisher('/pwm', Pwm, queue_size=10)
	#self.joyOdom_publisher = rospy.Publisher('/Joy_Odom', TwistWithCovarianceStamped, queue_size=10)
	#self.joy_odom = TwistWithCovarianceStamped()
	#self.joy_odom.header.frame_id = "base_link"

	#self.joy_odom.twist.covariance[0] = 0.25
	#self.joy_odom.twist.covariance[7] = 0.25
	#self.joy_odom.twist.covariance[14] = 0.25

	#rospy.Subscriber("/zeabus/cmd_vel", Twist, self.joy_callback)
    	rospy.Subscriber("/zeabus/cmd_vel", Twist, self.joy_callback)
	#rospy.Subscriber("/joy", Joy, self.checkJoy)

	#self.odom_x = 0
	#self.joyEn = False
	#d = direction of each thruster  [0,2,5,6 reverse direction]
	print '============d============='
	# self.d = array([[math.cos(math.radians(40)), math.sin(math.radians(40)), 0],
	# 				[0,0,1],
	# 				[-math.cos(math.radians(40)), math.sin(math.radians(40)), 0],
	# 				[0, 0, 1],
	# 				[-math.cos(math.radians(40)), -math.sin(math.radians(40)), 0],
	# 				[0, 0, 1],
	# 				[math.cos(math.radians(40)), -math.sin(math.radians(40)), 0],
	# 				[0, 0, 1]])
	# self.d = array([[0, 0, 1],
	# 				[0,0,1],
	# 				[0, 0, 1],
	# 				[0, 0, 1],
	# 				[math.cos(math.radians(40)), math.sin(math.radians(40)), 0],
	# 				[math.cos(math.radians(40)), -math.sin(math.radians(40)), 0],
	# 				[-math.cos(math.radians(40)), -math.sin(math.radians(40)), 0],
	# 				[-math.cos(math.radians(40)), math.sin(math.radians(40)), 0]])

	#tul
	#self.d = array([[0, 0, 0],
	#				[0, 0, 0],
	#				[0, 0, 0],
	#				[0, 0, 0],
	#				[math.cos(math.radians(40)), math.sin(math.radians(40)), 0],
	#				[math.cos(math.radians(40)), -math.sin(math.radians(40)), 0],
	#				[-math.cos(math.radians(40)), -math.sin(math.radians(40)), 0],
	#				[-math.cos(math.radians(40)), math.sin(math.radians(40)), 0]])	

	#ek
	self.d = array([[0, 0, 1],
			[0, 0, -1],
			[0, 0, 1],
			[0, 0, 1],
			[-math.cos(math.radians(40)), math.sin(math.radians(40)), 0],
			[math.cos(math.radians(40)), math.sin(math.radians(40)), 0],
			[-math.cos(math.radians(40)), -math.sin(math.radians(40)), 0],
			[math.cos(math.radians(40)), -math.sin(math.radians(40)), 0]])	

#perlican
#     d = array([[0, -1, 0],
#                [0, 0, 1],
#                [1, 0, 0],
#                [0, 0, 1],
#                [0, 1, 0],
#                [0, 0, 1],
#                [1, 0, 0],
#                [0, 0, -1]])
	print self.d

	# r = distance from origin to each thruster
	print '\n============r============='
	# self.r = array([[ 0.45728,-0.19104, 0.03993],
	# 	   			[ 0.23594,-0.20304, 0.05816],
	# 				[-0.45728,-0.19104, 0.03993],
	# 	   			[-0.23594,-0.20304, 0.05816],
	# 				[-0.45728, 0.19104, 0.03993],
	# 	   			[-0.23594, 0.20304, 0.05816],
	# 	   			[ 0.45728, 0.19104, 0.03993],
	# 	   			[ 0.23594, 0.20304, 0.05816]])
	#self.r = array([[ 0.45728,-0.19104, 0.03993],
	# 	   			[-0.45728,-0.19104, 0.03993],
	# 				[-0.45728, 0.19104, 0.03993],
	# 				[ 0.45728, 0.19104, 0.03993],
	# 				[ 0.23594,-0.20304, 0.05816],
	# 	   			[-0.23594,-0.20304, 0.05816],
	#	   			[-0.23594, 0.20304, 0.05816],
	# 	   			[ 0.23594, 0.20304, 0.05816]])

#	self.r = array([[ 0.23594,-0.20304, 0.05816],
 #                      	 [-0.23594,-0.20304, 0.05816],
  #                     	 [-0.23594, 0.20304, 0.05816],
   #                    	 [ 0.23594, 0.20304, 0.05816],
#			 [ 0.45728,-0.19104, 0.03993],
#		   	 [-0.45728,-0.19104, 0.03993],
#			 [-0.45728, 0.19104, 0.03993],
#			 [ 0.45728, 0.19104, 0.03993]])
	#ek
	self.r = array([[ 0.225,  0.2,   0.03],
                       	[ 0.225, -0.2,   0.03],
			[-0.225,  0.2,   0.03],  
                       	[-0.225, -0.2,   0.03],
			[ 0.375,  0.26, -0.04],
		   	[ 0.375, -0.26, -0.04],
			[-0.375,  0.26, -0.04],
			[-0.375, -0.26, -0.04]])


#     r = array([[0.425, 0.140, -0.095+0.044],
#                [0.330, 0.150, 0.080+0.044],
#                [-0.150, 0.240, -0.060+0.044],
#                [-0.330, 0.150, 0.080+0.044],
#                [-0.425, -0.140, -0.095+0.044],
#                [-0.330, -0.150, 0.080+0.044],
#                [-0.150, -0.240, -0.060+0.044],
#                [0.330, -0.150, 0.080+0.044]])

	print self.r

	#T = matrix map thruster forces to robot force
	#T = [6 x 8]
	print '\n============T============='
	self.T_tmp = array([cross(self.r[0].T, self.d[0].T),
		   cross(self.r[1].T, self.d[1].T),
		   cross(self.r[2].T, self.d[2].T),
		   cross(self.r[3].T, self.d[3].T),
		   cross(self.r[4].T, self.d[4].T),
		   cross(self.r[5].T, self.d[5].T),
		   cross(self.r[6].T, self.d[6].T),
		   cross(self.r[7].T, self.d[7].T)])
	self.T = concatenate((self.d.T, self.T_tmp.T))
	print self.T
	#M = matrix map robot force to thruster forces
	#M = [8 x 6]
	print '\n============M============='
	self.M = linalg.pinv(self.T)
	print self.M.shape
	print self.M

	#F = robot force and moment
	#F = [6 x 1] = [Fx, Fy, Fz, Mx, My, Mz]
	#print '\n============F============='
	#F = array([[10], [0], [0], [0], [0], [0]])
	#print F

	#t = thruster force
	#t = [8 x 1] = [t0, t1, t2, t3, t4, t5, t6, t7]
	#print '\n============t============='
	#t = dot(M, F)
	#print t


	#T = matrix map thruster forces to robot force
	#T = [6 x 8]


    def bound(self,cmd):
        x = []
        limit_bound = 450
        for i in cmd:
            if i > limit_bound:
                x.append(limit_bound)
            elif i < -limit_bound:
                x.append(-limit_bound)
            else:
                x.append(i)
        return x
    def joy_callback(self , message):
	#print '** input ** '
	#print message
	pwm_command = Pwm()

	pwm_command.pwm = [1500]*8

	#compute thrust for each thruster based on joy stick command
	
	trusts_scale = [3,3,4.1,2.4,2.4,2.4]
	F = array([message.linear.x, message.linear.y, message.linear.z,
		   message.angular.x, message.angular.y, message.angular.z])
	print '======= F ========'
	print F
	print F.T
	t = dot(self.M, F.T)
	print '=================** thrust **=============='
	print t

	cmd = lup.lookup_pwm_array(t)
	print '=========== cmd ==========='
	print cmd
	
	#tmp = [i-1500 for i in cmd]
	
	#tul
	#pwm_command.pwm[0] += tmp[0]#500*t[0]; #thrust0		        4/		   \5
	#pwm_command.pwm[1] -= tmp[1]#500*t[1]; #thrust1				/		    \
	#pwm_command.pwm[2] += tmp[2]#500*t[2]; #thrust2			  0	|			| 1
	#pwm_command.pwm[3] += tmp[3]#500*t[3]; #thrust3				|			|
	#pwm_command.pwm[4] -= tmp[4]#500*t[4]; #thrust4				|			|
	#pwm_command.pwm[5] += tmp[5]#500*t[5]; #thrust5			  2	|			| 3
	#pwm_command.pwm[6] += tmp[6]#500*t[6]; #thrust6 old +				 \		   /
	#pwm_command.pwm[7] -= tmp[7]#500*t[7]; #thrust7	old -			 6\		  /7

	#ek
	#pwm_command.pwm[0] += tmp[0]#500*t[0]; #thrust0		        4/		   \5
	#pwm_command.pwm[1] -= tmp[1]#500*t[1]; #thrust1				/		    \
	#pwm_command.pwm[2] += tmp[2]#500*t[2]; #thrust2			  0	|			| 1
	#pwm_command.pwm[3] += tmp[3]#500*t[3]; #thrust3				|			|
	#pwm_command.pwm[4] -= tmp[4]#500*t[4]; #thrust4				|			|
	#pwm_command.pwm[5] -= tmp[5]#500*t[5]; #thrust5			  2	|			| 3
	#pwm_command.pwm[6] -= tmp[6]#500*t[6]; #thrust6 				 \		   /
	#pwm_command.pwm[7] -= tmp[7]#500*t[7]; #thrust7		

	#ek+control
	pwm_command.pwm[0] = cmd[0]#500*t[0]; #thrust0		       
	pwm_command.pwm[1] = cmd[1]#500*t[1]; #thrust1
	pwm_command.pwm[2] = cmd[2]#500*t[2]; #thrust2			 
	pwm_command.pwm[3] = cmd[3]#500*t[3]; #thrust3			
	pwm_command.pwm[4] = cmd[4]#500*t[4]; #thrust4			
	pwm_command.pwm[5] = cmd[5]#500*t[5]; #thrust5			  
	pwm_command.pwm[6] = cmd[6]#500*t[6]; #thrust6 			
	pwm_command.pwm[7] = cmd[7]#500*t[7]; #thrust7		


	print '\n============PWM before bound============='
	print pwm_command
	for i in range(8) :
		if pwm_command.pwm[i] > 1800 :	#at first 1800
			pwm_command.pwm[i] = 1800
		elif pwm_command.pwm[i] < 1200 :
			pwm_command.pwm[i] = 1200  #at first 1200
	
	print '\n============PWM============='
	print pwm_command
	pwm_command.header.stamp = rospy.Time.now()
	self.pwm_publisher.publish(pwm_command)

if __name__ == '__main__':
    x = thrust_mapper()
    #x.publishOdom()
    rospy.spin()

