from flask import Flask, render_template, jsonify
import cv2
import numpy as np
import pickle
import threading
# from flask_ngrok import run_with_ngrok 


app = Flask(__name__)
# run_with_ngrok(app)
# Initialize the lock for threading
lock = threading.Lock()

# Load parking space positions from the pickle file
with open('parkveu-final123-main\CarParkPos', 'rb') as pickle_file:
    posList = pickle.load(pickle_file)

width, height = 107, 48
sv = []  # Initialize the sv list
img = None  # Initialize the image variable

def process_frames():
    global sv, img

    cap = cv2.VideoCapture("parkveu-final123-main\carPark.mp4")

    while True:
        _, img = cap.read()
        imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
        imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
        imgMedium = cv2.medianBlur(imgThreshold, 5)
        kernel = np.ones((3, 3), np.uint8)
        img_dilate = cv2.dilate(imgMedium, kernel, iterations=1)

        # Reset video frame to start when it reaches the end
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        with lock:
            sv = check_parking_space(img_dilate)

# Create a thread for processing frames
frame_thread = threading.Thread(target=process_frames)
frame_thread.daemon = True
frame_thread.start()

def check_parking_space(img_pro):
    spaceCounter = 0
    space = 0
    sc = []

    for pos in posList:
        x, y = pos
        img_crop = img_pro[y:y+height, x:x+width]

        count = cv2.countNonZero(img_crop)

        if count < 900:
            status = 'free'
            color = (0, 255, 0)
            thickness = 5
            spaceCounter += 1
            space += 1
            sc.append({'slot': spaceCounter, 'status': status})
            cv2.putText(img, f'S:{spaceCounter}', (x, y + height - 3), cv2.FONT_HERSHEY_SIMPLEX, 1, color, thickness)
        else:
            status = 'occupied'
            color = (0, 0, 255)
            thickness = 2
            spaceCounter += 1
            sc.append({'slot': spaceCounter, 'status': status})
            cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)

        cv2.putText(img, f'Free:{space}/{len(posList)}', (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 200, 0), 5)

    return sc

@app.route('/')
def index():
    global sv, img

    with lock:
        sc = sv  # Get the current sv list

    return render_template('NAVBAR1.html', sv=sc, img=img)

@app.route('/get_sv')
def get_sv():
    global sv

    with lock:
        return jsonify(sv)
app.run()



