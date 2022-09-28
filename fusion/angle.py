import tkinter as tk
from PIL import ImageTk, Image
import cv2
import numpy as np
import re
from math import sqrt, sin, cos, asin, acos, atan, pi
from typing import List, Tuple
import serial


# Capture from camera
cap = cv2.VideoCapture(0)

ser = serial.Serial('/dev/ttyACM0')


def send(a):
    ser.write(bytearray(a)) # 80:160 - corner:side, 120:170 - claw open:closed
    ser.flush()


# [version, count, pins0, delay0, pins1, delay1, ...]
# send([17, 250, 13, 90, 4, 30, 8, 35, 1, 0])
# pins: 8 - up/down, 4 - fwd/bkwd, 2 - rot, 1 - claw

servos = [110, 160, 140, 100]  # claw, rot, fwd, up


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


label_width = 13

root = tk.Tk()
# app.grid()
# Create a frame
app = tk.Frame(root, bg="white")
# Create a label in the frame
image_label = tk.Label(app)
image_label.pack(side=tk.TOP)
app.pack(side=tk.TOP,
         fill=tk.X,
         padx=5,
         pady=5)
# lmain.grid()


def create_entry_row(label):
    row = tk.Frame(root)
    lab = tk.Label(row, width=label_width, text=f"{label}: ", anchor='w')
    ent = tk.Entry(row)
    row.pack(side=tk.TOP,
             fill=tk.X,
             padx=5,
             pady=5)
    lab.pack(side=tk.LEFT)
    ent.pack(side=tk.LEFT,
             expand=tk.YES,
             fill=tk.X)
    return ent


# Create a time interval
time_entry = create_entry_row('Time Interval')
time_entry.insert(0, '25')
# Create a threshold input
threshold_entry = create_entry_row('Threshold')
threshold_entry.insert(0, '40')
# Contours
contours_entry = create_entry_row('Contours')
contours_entry.insert(0, '0')
# Fusion
fusion_entry = create_entry_row('Fusion')
fusion_entry.insert(0, '0')
# Angle
angle_entry = create_entry_row('Angles')
# angle_entry.insert(0, '90')
# Tracker
# tracker = cv2.TrackerKCF_create()
# tracker = cv2.TrackerMIL_create()
tracker = cv2.TrackerCSRT_create()


def track():
    _, frame = cap.read()
    initBB = cv2.selectROI("Frame", frame, fromCenter=False, showCrosshair=False)
    tracker.init(frame, initBB)


track()
b = tk.Button(root, text='Detect', command=(lambda: track()))
b.pack(side=tk.LEFT, padx=5, pady=5)
b2 = tk.Button(root, text='Send',
               command=(lambda e=angle_entry: send_servos(e)))
b2.pack(side=tk.LEFT, padx=5, pady=5)


# Kalman filter
kalman = cv2.KalmanFilter(2, 1, 0)
kalman.transitionMatrix = np.array([[1., 1.], [0., 1.]])
kalman.measurementMatrix = 1. * np.ones((1, 2))
kalman.processNoiseCov = 1e-5 * np.eye(2)
kalman.measurementNoiseCov = 1e-1 * np.ones((1, 1))
kalman.errorCovPost = 1. * np.ones((2, 2))
kalman.statePost = np.zeros((2, 1))


class Model:
    '''
    todo:
        - select points
        - calc angle
        - move arm forward
        - predict points positions
        - detect contours
        - match with points on circle closest to the predicted one
        - use object tracking as another source of truth    or
        - fuse tracked objects with contours using Kalman filter
    '''

    def __init__(self):
        self.base = None
        self.radius = None
        self.top = None
        self.selections = []
        self.contours = []
        _, frame = cap.read()
        self.frame = frame
        # fusion
        self.state = 0.1 * np.ones((2, 1))
        self.state[0, 0] = 90.0  # angle
        angle_entry.insert(0, self.state[0, 0])
        self.state[1, 0] = 1.0  # 0.0   # velocity
        self.prev_angle = self.state[0, 0]
        self.detected_angle = self.prev_angle
        self.predicted_angle = self.prev_angle

    def select_contour(self, x, y):
        for contour in self.contours:
            if cv2.pointPolygonTest(contour, (x, y), True) >= 0:
                rect = cv2.boundingRect(contour)
                x, y, w, h = rect
                scale = 4
                tracker.init(frame, (x - w * scale, y - h * scale, w + w * scale, h + h * scale))

    def calc_base(self):
        if self.selections[1][1] > self.selections[0][1]:
            top, mid = self.selections[0], self.selections[1]
        else:
            top, mid = self.selections[1], self.selections[0]
        dx = mid[0] - top[0]
        dy = mid[1] - top[1]
        base_x = top[0] + int(dx * 80.0 / 45.0)
        base_y = top[1] + int(dy * 80.0 / 45.0)
        self.base = (base_x, base_y)
        dx, dy = base_x - top[0], base_y - top[1]
        self.radius = sqrt(dx * dx + dy * dy)

    def detect_angle(self, box):
        x, y, w, h = box
        for contour in self.contours:
            cr = cv2.boundingRect(contour)
            cx, cy, cw, ch = cr
            if x <= cx and y <= cy and x + w >= cx + cw and y + h >= cy + ch:
                mx, my = cx + cw / 2, cy + ch / 2
                self.top = (int(mx), int(my))
                dx, dy = mx - self.base[0], my - self.base[1]
                cosine = dx / self.radius
                # print((mx, my), dx, self.radius)
                self.detected_angle = acos(cosine if cosine < 1.0 else 1.0) * 180 / pi
                return self.detected_angle
        return self.detected_angle

    def fuse_angle(self, angle):
        # print('state =', self.state)
        # v = angle - self.prev_angle
        v = self.predicted_angle - self.prev_angle
        # print('velocity = ', v)
        kalman.transitionMatrix[0, 1] = v
        # self.state[1, 0] = v
        # self.prev_angle = angle
        self.prev_angle = self.predicted_angle
        prediction = kalman.predict()
        # print('prediction =', prediction)
        predict_angle = prediction[0, 0]
        measurement = np.ones((1, 1)) * angle  # kalman.measurementNoiseCov * np.random.randn(1, 1)
        # print('angle =', measurement)
        # measurement = np.dot(kalman.measurementMatrix, self.state) + measurement
        measurement_angle = measurement[0, 0]
        # print('measurement =', measurement)
        kalman.correct(measurement)
        process_noise = sqrt(kalman.processNoiseCov[0, 0]) * np.random.randn(2, 1)
        self.state = np.dot(kalman.transitionMatrix, self.state) + process_noise
        # print('state =', self.state)
        state_angle = self.state[0, 0]
        return state_angle, predict_angle, measurement_angle


model = Model()


def image_click(e):
    print(e.x, e.y)
    if len(model.selections) < 2:
        model.selections += [(e.x, e.y)]
    else:
        model.select_contour(e.x, e.y)
    if len(model.selections) == 2 and model.base is None:
        model.calc_base()


image_label.bind("<Button-1>", image_click)


def send_servos(entry):
    vs = entry.get().split()
    v = vs[0]
    g = re.match('[0-9]+', v)
    a = int(g.group(0)) if g else 45.0
    servos[2] = 210 - int(100.0 * a / 90.0)
    model.predicted_angle = a
    if len(vs) > 1:
        g = re.match('[0-9]+', vs[1])
        servos[0] = int(g.group(0)) if g else 110
    print(servos)
    pwm(50)


def detect_contours(value, frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ret, cv2image = cv2.threshold(gray, value, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(cv2image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    self_contours = []
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        if len(approx) > 8 and 9 < area < 90 and 0.75 < float(w) / float(h) < 1.25:
            self_contours += [contour]
            # print((w, h), float(w) / float(h))
    # print()
    return self_contours


# function for video streaming
def video_stream():
    _, frame = cap.read()
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    s = threshold_entry.get()
    g = re.match('[0-9]+', s)
    if g:
        # print(g, g.group(0))
        value = int(g.group(0)) % 256
        model.frame = frame
        model.contours = detect_contours(value, frame)
        drawable_contours = model.contours
        if len(contours_entry.get()) > 0 and len(drawable_contours) > 0:
            cv2image = frame
            cv2.drawContours(cv2image, drawable_contours, -1, (255, 255, 0), 1)
            contours_entry.delete(0, tk.END)
            contours_entry.insert(0, f'{len(drawable_contours)}')

        (success, box) = tracker.update(frame)
        # print(box)
        x, y, w, h = box
        cv2.rectangle(cv2image, (x, y), (x + w, y + h), (0, 255, 0), 3)
        if model.base is not None:
            angle = model.detect_angle(box)
            fusion = model.fuse_angle(angle)
            cv2.circle(cv2image, model.base, 5, (0, 255, 0), 3)
            # angle_entry.delete(0, tk.END)
            # angle_entry.insert(0, f'{angle}')
            fusion_entry.delete(0, tk.END)
            fusion_entry.insert(0, f'{fusion}')
            if model.top is not None:
                cv2.line(cv2image, model.base, model.top, (0, 255, 0), 1)
            rad = model.state[0, 0] * pi / 180
            dx = int(model.base[0] + cos(rad) * model.radius)
            dy = int(model.base[1] - sin(rad) * model.radius)
            cv2.line(cv2image, model.base, (dx, dy), (0, 255, 255), 1)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    image_label.imgtk = imgtk
    image_label.configure(image=imgtk)
    # schedule the next frame
    t = time_entry.get()
    g = re.match('[0-9]+', t)
    dt = int(g.group(0)) if g else 25
    image_label.after(dt, video_stream)


video_stream()
root.mainloop()
