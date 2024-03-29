#!/usr/bin/env python2
import rospy
import actionlib
import irob_assignment_1.msg
from irob_assignment_1.srv import GetSetpoint, GetSetpointRequest, GetSetpointResponse
from geometry_msgs.msg import Twist
from nav_msgs.msg import Path
import tf2_ros
import tf2_geometry_msgs
from math import atan2, hypot
from std_msgs.msg import String
import geometry_msgs.msg
import math

# Use to transform between frames
tf_buffer = None
listener = None

# The exploration simple action client
goal_client = None
# The collision avoidance service client
control_client = None
# The velocity command publisher
pub = None

# The robots frame
robot_frame_id = "base_link"

# Max linear velocity (m/s)
max_linear_velocity = 0.5
# Max angular velocity (rad/s)
max_angular_velocity = 1.0
GetSetpointRequest

def move(path):
    global control_client, robot_frame_id, pub,tf_buffer
  #We use global keyword to read and write a global variable inside a function.
  #use of global keyword outside a function has no effect

    rate = rospy.Rate(10.0)
    # the Rate instance will attempt to keep the loop at 10hz by accounting for the time used by any operations during the loop.
    while path.poses:
        # Call service client with path
        res = control_client(path)
        setpoint = res.setpoint
        new_path = res.new_path
        
        # Transform Setpoint from service client
        try:
                transform = tf_buffer.lookup_transform(robot_frame_id,setpoint.header.frame_id,rospy.Time())
                transformed_setpoint = tf2_geometry_msgs.do_transform_point(setpoint, transform)
                # print(transformed_setpoint)
        except(tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException):
                rate.sleep()
                continue
          #ROSInterruptException if the sleep is interrupted by shutdown.


        # Create Twist message from the transformed Setpoint
        mess_twist = Twist()
        angle_v = atan2(transformed_setpoint.point.y,transformed_setpoint.point.x)
        mess_twist.angular.z =  min(angle_v,max_angular_velocity)
        mess_twist.linear.x = min(transformed_setpoint.point.x,max_linear_velocity)
        # if angle_v>=max_angular_velocity-0.1:
        #         angle_v = 0
        
        # Publish Twist
        pub.publish(mess_twist)
        rate.sleep()

        # Call service client again if the returned path is not empty and do stuff again

        # Send 0 control Twist to stop robot
        # mess_twist = 0
        # pub.publish(mess_twist)
        # # Get new path from action server
        path = new_path
    
    mess_twist.angular.z = 0
    mess_twist.linear.x = 0
    pub.publish(mess_twist)
    

def get_path():
    global goal_client
    while True:
                # Get path from action server
                goal_client.wait_for_server()
                #sending  goals before the action server comes up would be  useless, this line wait until we are connected to the action server.

                goal = irob_assignment_1.msg.GetNextGoalAction()
                #create a goal to send to the action server.
    
                goal_client.send_goal(goal)
                #send the goal to the action server.
                goal_client.wait_for_result()
                #waits for the server to finish performing the action
    
                # Call move with path from action server
                move(goal_client.get_result().path)



if __name__ == "__main__":
    # Init node
    rospy.init_node('controller')

    # Init publisher
    pub = rospy.Publisher('cmd_vel',Twist,queue_size=10)

    #declares that your node is publishing to the "cmd_vel" topic using the message type Twist to make the robot move.  queue_size limits the amount of the queued messages.

    # Init simple action client
    goal_client = actionlib.SimpleActionClient('get_next_goal',irob_assignment_1.msg.GetNextGoalAction)

    #the action name descibes the  namespce containing these topics, and the action specification message describes wthat messages should be passed along there topics.

    # Init service client
    control_client = rospy.ServiceProxy('get_setpoint',GetSetpoint)
    
    tf_buffer = tf2_ros.Buffer()
    listener = tf2_ros.TransformListener(tf_buffer)

    #we create a tf_2ros.TransformLinsterner object, once the listener is created, it starts receving tf2 transformations over the wire, and buffers them for 10 seconds.

    # Call get path
    get_path()

    # Spin
    rospy.spin()