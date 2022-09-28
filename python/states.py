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

servos = [150, 160, 140, 120] # claw, rot, fwd, up

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

def pack_servos(servos=servos, delay=20):
    sd = sorted([t for t in zip(range(len(servos)), servos)], key=lambda t: t[1])
    return pin_delays(sd, [17, delay, 15])


def pwm(states: List[Tuple[int, List[int]]]) -> None:
    instr = []
    for state in states:
        delay, servos = state
        instr += pack_servos(servos, delay)
    print(f'sending {len(instr)} bytes')
    send(instr)

c0 = 80
r0 = 160
r1 = 175

servos = [c0, r1, 120, 120] # claw, rot, fwd, up


f0 = 140
f1 = 190
u1 = 110
c1 = 155
r2 = 120
f2 = 110
u2 = 80

pwm([(200, servos)])
time.sleep(3)

states = []
states += [(100, [c0, r1, f1, u1])]
states += [(250, [c1, r1, f1, u1])]
states += [(250, [c1, r1, 90, 90])]
states += [(200, [c1, r2, f2, u2])]
states += [(120, [c0, r2, f2, u2])]
pwm(states)
time.sleep(25)

ser.close()
