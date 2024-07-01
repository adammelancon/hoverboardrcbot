from machine import UART, Pin
import time

# Configure UART1 for iBUS communication (115200 baud rate, 8 data bits, no parity bit, 1 stop bit)
uart = UART(1, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(8), rx=Pin(9))

# Function to read iBUS data
def read_ibus():
    if uart.any() >= 32:
        data = uart.read(32)
        print("Raw data:", data)  # Debugging: Print raw data
        if len(data) == 32:
            channels = []
            for i in range(14):
                channel = data[2 + i*2] | (data[3 + i*2] << 8)
                channels.append(channel)
            checksum = sum(data[:-2]) & 0xFFFF
            received_checksum = data[30] | (data[31] << 8)
            if checksum == received_checksum:
                return channels
            else:
                print("Checksum mismatch: calculated", checksum, "received", received_checksum)
        else:
            print("Data length mismatch")
    return None

# Main loop to read iBUS data and print channel values
while True:
    channels = read_ibus()
    if channels:
        print("Channel values:", channels)
    else:
        print("No valid iBUS data detected")
    time.sleep(0.1)  # Short delay to allow for other processing
