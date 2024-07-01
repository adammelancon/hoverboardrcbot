from machine import Pin, time_pulse_us
import time

# Define the pin for channel 3 (Pin 9)
channel_pin = Pin(9, Pin.IN)

# Built-in LED pin on the Pico W
led_pin = Pin("LED", Pin.OUT)

# Function to read PWM pulse width with timeout
def read_pulse_width(pin, timeout=1000000):
    start = time.ticks_us()
    while pin.value() == 0:
        if time.ticks_diff(time.ticks_us(), start) > timeout:
            return -1  # Timeout, return -1 to indicate failure
    start = time.ticks_us()
    while pin.value() == 1:
        if time.ticks_diff(time.ticks_us(), start) > timeout:
            return -1  # Timeout, return -1 to indicate failure
    pulse_width = time.ticks_diff(time.ticks_us(), start)
    return pulse_width

# Function to set LED brightness using software PWM
def set_led_brightness(duty_cycle):
    period = 0.02  # Total period in seconds (50 Hz)
    on_time = duty_cycle / 65535 * period
    off_time = period - on_time
    if on_time > 0:
        led_pin.on()
        time.sleep(on_time)
    if off_time > 0:
        led_pin.off()
        time.sleep(off_time)

# Main loop to read PWM and control the LED brightness
while True:
    pulse_width = read_pulse_width(channel_pin)
    if pulse_width > 0:
        # Map pulse width to duty cycle (assuming pulse width range is 1000 to 2000 microseconds)
        duty_cycle = int((pulse_width - 1000) * 65535 / 1000)
        duty_cycle = max(0, min(65535, duty_cycle))  # Clamp duty cycle to 0-65535
        set_led_brightness(duty_cycle)
        print("Channel 3 PWM value:", pulse_width, "Duty cycle:", duty_cycle)
    else:
        led_pin.off()  # Turn off LED if no valid pulse width is detected
    time.sleep(0.00001)  # Short delay to allow for other processing
