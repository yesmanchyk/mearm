from typing import List, Tuple
import time
from math import sin, cos, pi
import serial
ser = serial.Serial('/dev/ttyACM0')

def send(a):
    ser.write(bytearray(a)) # 80:160 - corner:side, 120:170 - claw open:closed
    ser.flush()

# [version, count, pins0, delay0, pins1, delay1, ...]
# send([17, 250, 13, 90, 4, 30, 8, 35, 1, 0])
# pins: 8 - up/down, 4 - fwd/bkwd, 2 - rot, 1 - claw

servos = [160, 160, 120, 160] # claw, rot, fwd, up

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

def pwm(ss, delay=50, instr=[]):
    sd = sorted([t for t in zip(range(len(ss)), ss)], key=lambda t: t[1])
    packet = pin_delays(sd, [17, delay, 15])
    instr += packet
    return instr

def countdown(n, q):
    for i in range(n):
        time.sleep(q)
        print(n - i - 1, end=' ', flush=True)

n = 60
for a in range(n):
    print(f'{a + 1} of {n}')
    x = 0.0
    r = 0.1
    whole = []
    while x < 4 * pi:
        servos[1] = 140 + int(sin(x) * 30)
        servos[2] = 140 + int(cos(x) * 10)
        servos[3] = 120 + int(cos(x) * 40)
        print(x, cos(x), servos)
        instr = pwm(servos, 25, [])
        whole += instr
        x += r * pi
        servos[1] = 140 + int(sin(x) * 30)
        servos[2] = 140 + int(cos(x) * 10)
        servos[3] = 120 + int(cos(x) * 40)
        print(x, cos(x), servos)
        instr = pwm(servos, 25, instr)
        whole += instr
        x += r * pi
        print(instr)
        send(instr)
        time.sleep(1.5)
    print(len(whole), whole)
    print(f'end of {a + 1} of {n}')
    # s = job(0 if a % 2 == 0 else 40)
    # send(s)
    # send([17, 200, 15, 120, 13, 40, 2, 0,   17, 150, 1, 160, 1, 0,   17, 150, 15, 80, 6, 60, 8, 20, 1, 0,   17, 50, 1, 120, 1, 0])
    # countdown(10, 12)
ser.close()
exit(0)
