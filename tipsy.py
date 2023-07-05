import asyncio
import os
import time
import random 

from enum import Enum
from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.sensor import Sensor
from viam.components.base import Base
from viam.services.vision import VisionClient

robot_secret = os.getenv('ROBOT_SECRET') or ''
robot_address = os.getenv('ROBOT_ADDRESS') or ''
base_name = os.getenv('ROBOT_BASE') or 'tipsy-base'
camera_name = os.getenv('ROBOT_CAMERA') or 'cam'
pause_interval = os.getenv('PAUSE_INTERVAL') or 3
num_sensors = os.getenv('NUM_SENSORS') or 2
min_sensor_distance = os.getenv('MIN_SENSOR_DISTANCE') or 0.4  # minimum distance that the robot will allow before stopping to avoid an obstacle.
human_confidence_threshold = os.getenv('HUMAN_CONFIDENCE_THRESHOLD') or 0.7
default_move_distance = os.getenv('DEFAULT_MOVE_DISTANCE') or 800


# The use of enums for RobotStates improves code readability and reduces the chance of errors related to state management.
class RobotStates(str, Enum):
    stopped = "stopped"
    straight = "straight"
    spinning = "spinning"
    
base_state = RobotStates.stopped
iterations_stopped = 0

async def connect():
    creds = Credentials(
        type='robot-location-secret',
        payload=robot_secret)
    opts = RobotClient.Options(
        refresh_interval=0,
        dial_options=DialOptions(credentials=creds)
    )
    return await RobotClient.at_address(robot_address, opts)

async def obstacle_detect(sensor):
    """
    Takes in a sensor and returns the distance to the nearest object
    
    We gracefully handle the uncommon situation where readings does not
    return a distance.
    """
    reading = (await sensor.get_readings())
    # If distance isn't present, we assume a nearby object and halt the
    # robot until distance is present and we can safely move again
    dist = reading.get("distance", 0)
    return dist 


async def obstacle_detect_loop(sensors, base, min_distance_threshold = min_sensor_distance):
    """
    Get distance readings from each sensor and checks
    to see if an object is "too close". If too close, stop moving.
    
    Args:
        sensors (List[Sensor]): List of ultrasonic sensors.
        base (Base): Robot base.
        min_distance (float): Minimum distance to sensor for an obstacle
            to be considered detected.
    """
    while(True):
        sensor_distances = [await obstacle_detect(sensor) for sensor in sensors]
        min_dist = min(sensor_distances)
        if min_dist < min_distance_threshold:
            if base_state == RobotStates.straight:
                await base.stop()
                print("obstacle in front, Tipsy stopping")
        await asyncio.sleep(.01)

async def person_detect(detector, base, sensors):
    """
    This function first checks to see if the `VisionClient` has detected a person. If
    it has, the function moves the robot towards the person. If it has not, the function
    spins the robot in a random direction.

    Args:
        detector (VisionClient): VisionClient object.
        base (Base): Robot base.
        sensors (list): List of ultrasonic sensors.
    """
    while(True):
        # look for person
        found = False
        global base_state
        global iterations_stopped
        # The variable `iterations_stopped` tracks the number of seconds the robot has been
        # stopped at a person. If this variable gets up to 3, that means the robot has been 
        # at one person for 3 seconds, so we want the robot to go find a new person and assume 
        # that the person has gotten what it's needed from Tipsy.
        
        print("will detect")
        detections = await detector.get_detections_from_camera(camera_name)
        for d in detections:
            if d.confidence > human_confidence_threshold:
                print(d.class_name, d.confidence)
                if (d.class_name == "Person"):
                    found = True
                    break  # Save time, don't need to check other detections
        if found and iterations_stopped < 3:
            print("I see a person")
            # first manually call obstacle_detect - don't even start moving if someone in the way
            readings = [await obstacle_detect(sensor) for sensor in sensors] 
            min_obst_dist = min(readings)
            max_obst_dist = max(readings)

            if max_obst_dist > min_sensor_distance:
                iterations_stopped = 0
                # If an obstacle is closer than our default move distance
                # we want to avoid moving straight into a potential collision
                # so we move at most the distance to the closest obstacle
                move_distance = min(min_obst_dist - 1, default_move_distance)
                print("will move straight")
                base_state = RobotStates.straight
                await base.move_straight(distance=move_distance, velocity=250)
                base_state = RobotStates.stopped
            else:
                iterations_stopped += 1
        else:
            iterations_stopped = 0
            print("I will turn and look for a person")
            base_state = RobotStates.spinning
            # Randomly spin instead
            await base.spin(random.randint(45, 180), 45) # (angle, velocity)
            base_state = RobotStates.stopped

        await asyncio.sleep(pause_interval)
        
async def tip_detect(detector, base, imu_sensor):
    """
    Checks the orientation of the robot and stops it if it is tipping over.

    Args:
        detector (VisionClient): VisionClient object.
        base (Base): Robot base.
        imu_sensor (Sensor): IMU sensor.
    """
    global base_state

    while(True):
        # Not currently using acceleration or magnetometer, but could be used
        # if that's a more effective way to determine tipping over.
        # acceleration = await imu_sensor.get_acceleration()
        # magnetometer = await imu_sensor.get_magnetometer()
        orientation = await imu_sensor.get_orientation()

        degrees_tipping_threshold = 30
        if orientation > degrees_tipping_threshold:
            # The robot is tipping over!
            await base.stop()
            base_state = RobotStates.stopped
            print("The robot is tipping over!")

        await asyncio.sleep(0.1)

async def main():
    robot = await connect()
    base = Base.from_robot(robot, base_name)
    sensors = []
    # Use global config variable to set num sensors
    for s in range(num_sensors):
        curr_sensor = Sensor.from_robot(robot, "ultrasonic" + str(s+1))
        sensors.append(curr_sensor)
     
    # Initialize camera detector ML model for people detection    
    detector = VisionClient.from_robot(robot, "myPeopleDetector")

    # IMU sensor for getting acceleration, magnetometer, and orientation
    imu_sensor = Sensor.from_robot(robot, "imu")
    
    # Create a background task that checks the orientation of the robot and stops it if it is tipping over.
    tipping_task = asyncio.create_task(tip_detect(detector, base, imu_sensor))

    # Ultrasonic distance sensors for object detection/avoidance
    # Create a background task that looks for obstacles and stops the base if it's moving
    obstacle_task = asyncio.create_task(obstacle_detect_loop(sensors, base))
    
    # Use camera ML model to detect if we see a person
    # Create a background task that looks for a person and moves towards them, or turns and keeps looking
    person_task = asyncio.create_task(person_detect(detector, base, sensors))
    
    results= await asyncio.gather(obstacle_task, person_task, tipping_task, return_exceptions=True)
    print(results)

    await robot.close()

if __name__ == '__main__':
    asyncio.run(main())
