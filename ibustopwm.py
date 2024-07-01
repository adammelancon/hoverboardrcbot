import time
from machine import Pin, PWM
from ibus import IBus

# Initialize iBus on UART1
ibus_in = IBus(1)

# Setup PWM on GPIO 15 for forward direction
pwm_forward_pin = 15
pwm_forward = PWM(Pin(pwm_forward_pin))
pwm_forward.freq(50)  # Frequency set to 50 Hz (standard for motor controllers)

# Setup PWM on GPIO 14 for reverse direction
pwm_reverse_pin = 14
pwm_reverse = PWM(Pin(pwm_reverse_pin))
pwm_reverse.freq(50)  # Frequency set to 50 Hz (standard for motor controllers)

# Define the neutral range and threshold for throttle
NEUTRAL_RANGE = 10  # Adjust this value as needed for your joystick dead zone
THROTTLE_THRESHOLD = 10  # Minimum value to activate motor

# Function to map normalized throttle value to PWM duty cycle
def map_to_pwm(value):
    # Normalize from -100 to 100 range to 0 to 65535 range
    pwm_value = int((abs(value) * 65535) / 100)
    return pwm_value

while True:
    # Read data from iBus
    res = ibus_in.read()
    
    # If new valid data is received
    if res[0] == 1:
        # Get the normalized value for channel 2 (throttle)
        throttle_value = IBus.normalize(res[2])
        
        # Check if throttle is within the neutral range
        if -NEUTRAL_RANGE <= throttle_value <= NEUTRAL_RANGE:
            # Set both PWM duty cycles to zero to cut off the motor
            pwm_forward.duty_u16(0)
            pwm_reverse.duty_u16(0)
        elif throttle_value > THROTTLE_THRESHOLD:
            # Forward direction
            pwm_duty = map_to_pwm(throttle_value)
            pwm_forward.duty_u16(pwm_duty)
            pwm_reverse.duty_u16(0)
        elif throttle_value < -THROTTLE_THRESHOLD:
            # Reverse direction
            pwm_duty = map_to_pwm(throttle_value)
            pwm_forward.duty_u16(0)
            pwm_reverse.duty_u16(pwm_duty)
        
        # Print the status and normalized channel values for debugging
        print("Status {} CH 1 {} Ch 2 {} Ch 3 {} Ch 4 {} Ch 5 {} Ch 6 {}".format(
            res[0],    # Status
            IBus.normalize(res[1]),           # Channel 1
            throttle_value,                   # Channel 2 (Throttle)
            IBus.normalize(res[3]),           # Channel 3
            IBus.normalize(res[4]),           # Channel 4
            IBus.normalize(res[5], type="dial"),  # Channel 5 (dial)
            IBus.normalize(res[6], type="dial")   # Channel 6 (dial)
        ), end="")
        
        print("")  # Print a newline
    
    # Short delay to avoid overwhelming the CPU
    time.sleep(0.05)
