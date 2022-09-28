import time
import serial
ser = serial.Serial('/dev/ttyACM0')

def send(a):
    ser.write(bytearray(a)) # 80:160 - corner:side, 120:170 - claw open:closed
    ser.flush()

# [version, count, pins0, delay0, pins1, delay1, ...]
# send([17, 250, 13, 90, 4, 30, 8, 35, 1, 0])
for a in range(2):
    print(f'{a + 1} of 3')
    # send([17, 200, 15, 130, 13, 40, 2, 0,   17, 100, 1, 140, 1, 0,   17, 100, 1, 145, 1, 0,   17, 100, 1, 150, 1, 0,   17, 100, 1, 155, 1, 0])
    send([17, 200, 15, 120, 13, 40, 2, 0,   17, 100, 1, 155, 1, 0])
    time.sleep(12)
ser.close()
exit(0)
