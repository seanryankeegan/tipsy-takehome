# Tipsy: Autonomous Drink Carrier

[Tipsy](https://docs.viam.com/tutorials/projects/tipsy/) is an autonomous drink carrier designed vy Viam to navigate a party environment, interact with guests, and deliver drinks. This project is a submission for a take-home assignment, where I took the initial code for Tipsy and made significant improvements. The improved code enhances the functionality, readability, and maintainability of the original codebase.

## Project Overview

The goal of Tipsy is to create an autonomous drink carrier with the following capabilities:

1. **Person Detection and Navigation**: Tipsy utilizes a camera and a machine learning model to detect people at a party. It intelligently navigates towards individuals to provide them with drinks.

2. **Obstacle Avoidance**: Tipsy incorporates ultrasonic sensors to detect obstacles in its path. It employs a control loop to avoid collisions by adjusting its movement and stopping when an obstacle is detected.

3. **Pause Near People**: Tipsy pauses near people to allow them to select and grab their drinks. This feature enhances guest interaction and convenience.

4. **Dynamic Movement**: To prevent Tipsy from getting stuck next to the same person, the code includes randomized movements. Tipsy explores the party space without tracking individual people or remembering its previous paths.

5. **Tipping Prevention**: The code checks Tipsy's orientation to prevent tipping over. If Tipsy is at risk of tipping, it stops its movement to ensure safety.

6. **Configurable Number of Ultrasonic Sensors**: The code allows for easy configuration of the number of ultrasonic sensors. By adjusting a configuration variable, Tipsy can utilize different sensor setups.


## Project Structure

The Tipsy project repository contains the following files:

- `tipsy.py`: The main Python script that implements the functionality of Tipsy. This script includes the control loop, person detection, obstacle avoidance, tipping prevention, and other necessary functions.

- `README.md`: This README file providing an overview of the project, setup instructions, and usage guidelines.

## Note

This code should not be considered production-ready, as it has not been tested on any hardware. It is solely an attempt to improve the original Tipsy code provided as part of a job interview submission. **Please do not fork this repository and attempt to use the code as is.**

Contributions to this Tipsy project repository are not currently accepted, as this project is specifically tailored for a job interview submission. For more information about the Tipsy project from Viam, see their [official tutorial](https://docs.viam.com/tutorials/projects/tipsy/).

## Contact

For any questions regarding this Tipsy project, please contact me at seanryankeegan@gmail.com.
