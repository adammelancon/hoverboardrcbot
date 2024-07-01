import time
from machine import Pin, PWM
from ibus import IBus

# Initialize iBus on UART1
ibus_in = IBus(1)

# Setup PWM and DIR on GPIO for wheel controllers
pwm_left_wheel_pin = 15
dir_left_wheel_pin = 17
pwm_right_wheel_pin = 14
dir_right_wheel_pin = 16

pwm_left_wheel = PWM(Pin(pwm_left_wheel_pin))
dir_left_wheel = Pin(dir_left_wheel_pin, Pin.OUT)
pwm_right_wheel = PWM(Pin(pwm_right_wheel_pin))
dir_right_wheel = Pin(dir_right_wheel_pin, Pin.OUT)

pwm_left_wheel.freq(50)  # Frequency set to 50 Hz (standard for motor controllers)
pwm_right_wheel.freq(50)  # Frequency set to 50 Hz (standard for motor controllers)

# Define the neutral range and threshold for throttle and steering
NEUTRAL_RANGE = 10  # Adjust this value as needed for your joystick dead zone
THROTTLE_THRESHOLD = 5  # Minimum value to activate motor
STEERING_THRESHOLD = 5  # Minimum value to activate turning

# Function to map normalized throttle value to PWM duty cycle with speed limit
def map_to_pwm(value, speed_limit):
    # Normalize from -100 to 100 range to 0 to 65535 range with speed limit
    pwm_value = int((abs(value) * 65535 * speed_limit) / 10000)
    return pwm_value

while True:
    # Read data from iBus
    res = ibus_in.read()
    
    # If new valid data is received
    if res[0] == 1:
        # Get the normalized values for channel 2 (throttle), channel 1 (steering), and channel 6 (speed limit)
        throttle_value = IBus.normalize(res[2])
        steering_value = IBus.normalize(res[1])
        speed_limit = IBus.normalize(res[6], type="dial")  # Channel 6 as speed limit
        
        # Determine PWM duty cycles for each wheel based on throttle, steering, and speed limit
        left_wheel_duty = 0
        right_wheel_duty = 0
        
        if throttle_value > THROTTLE_THRESHOLD:
            # Moving forward
            base_duty = map_to_pwm(throttle_value, speed_limit)
            if steering_value > STEERING_THRESHOLD:
                # Moving forward and turning right: left wheel moves forward faster
                left_wheel_duty = base_duty
                right_wheel_duty = base_duty * (1 - steering_value / 100)
                dir_left_wheel.value(1)  # Forward direction
                dir_right_wheel.value(0)  # Reverse direction
            elif steering_value < -STEERING_THRESHOLD:
                # Moving forward and turning left: right wheel moves forward faster
                left_wheel_duty = base_duty * (1 + steering_value / 100)
                right_wheel_duty = base_duty
                dir_left_wheel.value(1)  # Forward direction
                dir_right_wheel.value(0)  # Reverse direction
            else:
                # Moving forward, both wheels spin equally
                left_wheel_duty = base_duty
                right_wheel_duty = base_duty
                dir_left_wheel.value(1)  # Forward direction
                dir_right_wheel.value(0)  # Reverse direction
        elif throttle_value < -THROTTLE_THRESHOLD:
            # Moving backward
            base_duty = map_to_pwm(-throttle_value, speed_limit)
            if steering_value > STEERING_THRESHOLD:
                # Moving backward and turning right: left wheel moves backward faster
                left_wheel_duty = base_duty
                right_wheel_duty = base_duty * (1 - steering_value / 100)
                dir_left_wheel.value(0)  # Reverse direction
                dir_right_wheel.value(1)  # Forward direction
            elif steering_value < -STEERING_THRESHOLD:
                # Moving backward and turning left: right wheel moves backward faster
                left_wheel_duty = base_duty * (1 + steering_value / 100)
                right_wheel_duty = base_duty
                dir_left_wheel.value(0)  # Reverse direction
                dir_right_wheel.value(1)  # Forward direction
            else:
                # Moving backward, both wheels spin equally
                left_wheel_duty = base_duty
                right_wheel_duty = base_duty
                dir_left_wheel.value(0)  # Reverse direction
                dir_right_wheel.value(1)  # Forward direction
        else:
            # Neutral throttle
            if steering_value > STEERING_THRESHOLD:
                # Turning right: left wheel moves forward, right wheel stops
                left_wheel_duty = map_to_pwm(steering_value, speed_limit)
                right_wheel_duty = 0
                dir_left_wheel.value(1)  # Forward direction
                dir_right_wheel.value(0)  # Reverse direction
            elif steering_value < -STEERING_THRESHOLD:
                # Turning left: right wheel moves forward, left wheel stops
                right_wheel_duty = map_to_pwm(-steering_value, speed_limit)
                left_wheel_duty = 0
                dir_left_wheel.value(1)  # Stop left wheel
                dir_right_wheel.value(0)  # Reverse direction
            else:
                # No steering input, cut off both motors
                left_wheel_duty = 0
                right_wheel_duty = 0
                dir_left_wheel.value(0)
                dir_right_wheel.value(1)
        
        # Apply PWM duty cycles to the wheels
        pwm_left_wheel.duty_u16(int(left_wheel_duty))
        pwm_right_wheel.duty_u16(int(right_wheel_duty))
        
        # Print the status and normalized channel values for debugging
#         print("Status {} CH 1 {} Ch 2 {} Ch 3 {} Ch 4 {} Ch 5 {} Ch 6 {}".format(
#             res[0],    # Status
#             steering_value,           # Channel 1 (Steering)
#             throttle_value,           # Channel 2 (Throttle)
#             IBus.normalize(res[3]),   # Channel 3
#             IBus.normalize(res[4]),   # Channel 4
#             IBus.normalize(res[5], type="dial"),  # Channel 5 (dial)
#             speed_limit               # Channel 6 (Speed Limit)
#         ))

    # Short delay to avoid rapid changes
    time.sleep(0.02)
