from typing import List, Tuple
import time
import tkinter as tk
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


def pwm(delay=20):
    instr = []
    sd = sorted([t for t in zip(range(len(servos)), servos)], key=lambda t: t[1])
    packet = pin_delays(sd, [17, delay, 15])
    instr += packet
    print(instr)
    send(instr)

fields = ('Closed', 'Rotation', 'Forward', 'Up')

def send_servos(entries):
    global servos
    servos = [int(entries[field].get()) % 256 for field in fields]
    print(servos)
    pwm(50)

delta = 5

def change(entry, how):
    value = int(entry.get())
    entry.delete(0, tk.END)
    entry.insert(0, how(value))

def decrease(entry):
    change(entry, lambda value: value - delta)

def increase(entry):
    change(entry, lambda value: value + delta)

def create_form(root, fields):
    global servos
    entries = {}
    for i, field in enumerate(fields):
        print(field, servos[i])
        row = tk.Frame(root)
        lab = tk.Label(row, width=22, text=field+": ", anchor='w')
        ent = tk.Entry(row)
        ent.insert(0, f'{servos[i]}')
        dec = tk.Button(row, text=' - ', command=(lambda e=ent: decrease(e)))
        inc = tk.Button(row, text=' + ', command=(lambda e=ent: increase(e)))
        row.pack(side=tk.TOP,
                 fill=tk.X,
                 padx=5,
                 pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.LEFT,
                 expand=tk.YES,
                 fill=tk.X)
        inc.pack(side=tk.RIGHT)
        dec.pack(side=tk.RIGHT)
        entries[field] = ent
    return entries

def run_tk():
    root = tk.Tk()
    ents = create_form(root, fields)
    b2 = tk.Button(root, text='Send',
           command=(lambda e=ents: send_servos(e)))
    b2.pack(side=tk.LEFT, padx=5, pady=5)
    b3 = tk.Button(root, text='Quit', command=root.quit)
    b3.pack(side=tk.LEFT, padx=5, pady=5)
    root.mainloop()

def console():
    n = 100
    delta = 10
    for a in range(n):
        l = input()
        if l == 'q':
            break
    # lines = ['', '-', '--0+']
    # for a, l in enumerate(lines):
        for i, c in enumerate(l):
            if len(servos) <= i:
                break
            if c == '-':
                servos[i] -= delta
            elif c == '0':
                pass
            else:
                servos[i] += delta
        print(f'{a + 1} of {n}: ', servos)
        pwm(100)
        # time.sleep(5)

if __name__ == '__main__':
    run_tk()
    ser.close()
