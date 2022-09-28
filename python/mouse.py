from typing import List, Tuple
import time
import serial
ser = serial.Serial('/dev/ttyACM0')

def send(a):
    ser.write(bytearray(a)) # 80:160 - corner:side, 120:170 - claw open:closed
    ser.flush()

# [version, count, pins0, delay0, pins1, delay1, ...]
# send([17, 250, 13, 90, 4, 30, 8, 35, 1, 0])
# pins: 8 - up/down, 4 - fwd/bkwd, 2 - rot, 1 - claw
def job(a, dur=20):
    s = []
    ss = [17, dur, 4, 140, 4, 0] # fwd
    s += ss
    ss = [17, dur, 2, 140 + a, 2, 0] # return
    # ss = [17, 100, 2, 160, 2, 0] # straight
    b = 60
    s += ss
    ss = [17, dur, 8, b, 8, 0] # down
    s += ss
    ss = [17, dur, 10, b, 8, 160 - b, 2, 0] # down + turn
    s += ss
    ss = [17, dur, 8, 120, 8, 0] # up
    s += ss
    return s

#servos = [157, 160, 110, 120]
servos = [157, 160, 140, 60]

def pin_delays(sd: List[Tuple[int, int]], packet: List[int]) -> List[int]:
    passed = 0
    for ps, pd in sd:
        pin = 1 << ps
        if pd == passed:
            packet[-1] |= pin
        else:
            packet += [pd - passed, pin]
        passed = pd
    packet += [0]
    return packet

instr = []

def pwm(delay=250):
    global instr
    sd = sorted([t for t in zip(range(len(servos)), servos)], key=lambda t: t[1])
    packet = pin_delays(sd, [17, delay, 15])
    instr += packet
    #print(instr)
    #send(instr)

def countdown(n, q):
    for i in range(n):
        time.sleep(q)
        print(n - i - 1, end=' ', flush=True)

n = 1
for a in range(n):
    print(f'({a + 1} of {n})')
    for d in [15, -15, -15, 15, 0]:
        servos[1] += d
        pwm()
        #time.sleep(0.75)
    print(len(instr))
    print(instr)
    # s = job(0 if a % 2 == 0 else 40)
    # send(s)
    # send([17, 200, 15, 120, 13, 40, 2, 0,   17, 150, 1, 160, 1, 0,   17, 150, 15, 80, 6, 60, 8, 20, 1, 0,   17, 50, 1, 120, 1, 0])
    # countdown(10, 1)
    send([18, len(instr)] + instr)
ser.close()
exit(0)

for a in range(0): # [240, 120, 60, 120, 240, 120]:
    for b in range(10):
        ser.write(bytearray([80 + b * 2, 100 + b * 4, 150 + a * 30, 120 + a * 40]))
        ser.flush()
        print(ser.read(), ser.read(), ser.read(), ser.read())

ser.write(bytearray([120, 120, 160, 90])) # 80:160 - corner:side, 120:170 - claw open:closed
ser.flush()
print(ser.read(), ser.read(), ser.read(), ser.read())
time.sleep(0.5)
ser.write(bytearray([120, 140, 120, 170]))
ser.flush()
time.sleep(0.5)
ser.write(bytearray([80, 140, 120, 170]))
ser.flush()
time.sleep(1)
ser.write(bytearray([80, 120, 160, 170]))
ser.flush()
ser.close()
