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

pwm_left_wheel.freq(50)
pwm_right_wheel.freq(50)

# Define the neutral range and threshold for throttle and steering
NEUTRAL_RANGE = 10
THROTTLE_THRESHOLD = 5
STEERING_THRESHOLD = 5

# Function to map normalized value to PWM duty cycle with speed limit
def map_to_pwm(value, speed_limit):
    return int((abs(value) * 65535 * speed_limit) / 10000)

# Function to apply smooth deceleration
def smooth_deceleration(current, target, deceleration_factor=0.2):
    return current - (current - target) * deceleration_factor

# Main control loop
while True:
    res = ibus_in.read()
    
    if res[0] == 1:
        throttle_value = IBus.normalize(res[2])
        steering_value = IBus.normalize(res[1])
        speed_limit = IBus.normalize(res[6], type="dial")
        
        # Apply deadzone to throttle and steering
        throttle_value = 0 if abs(throttle_value) < THROTTLE_THRESHOLD else throttle_value
        steering_value = 0 if abs(steering_value) < STEERING_THRESHOLD else steering_value
        
        # Calculate base duty cycle
        base_duty = map_to_pwm(abs(throttle_value), speed_limit)
        
        # Calculate steering intensity (0 to 1)
        steering_intensity = abs(steering_value) / 100
        
        # Calculate left and right wheel speeds
        if throttle_value != 0:
            # Moving forward or backward
            if steering_value > 0:
                # Turning right
                left_wheel_duty = base_duty
                right_wheel_duty = base_duty * (1 - steering_intensity)
            elif steering_value < 0:
                # Turning left
                left_wheel_duty = base_duty * (1 - steering_intensity)
                right_wheel_duty = base_duty
            else:
                # Straight
                left_wheel_duty = right_wheel_duty = base_duty
            
            # Set wheel directions (inverted for right wheel)
            dir_left_wheel.value(throttle_value > 0)
            dir_right_wheel.value(throttle_value < 0)
        else:
            # Neutral throttle, turning in place
            turn_speed = map_to_pwm(abs(steering_value), speed_limit * 0.5)
            if steering_value > 0:
                # Turning right
                left_wheel_duty = turn_speed
                right_wheel_duty = turn_speed
                dir_left_wheel.value(1)
                dir_right_wheel.value(1)
            elif steering_value < 0:
                # Turning left
                left_wheel_duty = turn_speed
                right_wheel_duty = turn_speed
                dir_left_wheel.value(0)
                dir_right_wheel.value(0)
            else:
                # No movement
                left_wheel_duty = right_wheel_duty = 0
        
        # Apply smooth deceleration when stopping
        current_left_duty = pwm_left_wheel.duty_u16()
        current_right_duty = pwm_right_wheel.duty_u16()
        
        if throttle_value == 0 and steering_value == 0:
            smooth_left_duty = smooth_deceleration(current_left_duty, 0)
            smooth_right_duty = smooth_deceleration(current_right_duty, 0)
        else:
            smooth_left_duty = left_wheel_duty
            smooth_right_duty = right_wheel_duty
        
        # Apply PWM duty cycles to the wheels
        pwm_left_wheel.duty_u16(int(smooth_left_duty))
        pwm_right_wheel.duty_u16(int(smooth_right_duty))

    time.sleep(0.02)
