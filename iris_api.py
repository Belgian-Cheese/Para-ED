from flask import Flask, jsonify
import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import threading

app = Flask(__name__)

# Initialize Mediapipe modules
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Iris and eye landmarks
LEFT_EYE_LANDMARKS = [33, 133, 159, 145, 160]  # Key points for left eye
RIGHT_EYE_LANDMARKS = [362, 263, 386, 374, 387]  # Key points for right eye
IRIS_LEFT_LANDMARKS = [469, 470, 471, 472]  # Landmarks for left iris
IRIS_RIGHT_LANDMARKS = [474, 475, 476, 477]  # Landmarks for right iris
NOSE_LANDMARK = 1  # Landmark for nose tip
# Map for tracking directions
DIRECTIONS = {"center": 0, "left": 1, "right": 2, "up": 3, "down": 4}

STABLE_DURATION_CLICK = 5.0
SENSITIVITY_HORIZONTAL = 0.1  # Sensitivity for horizontal movements
SENSITIVITY_VERTICAL = 0.15  # Sensitivity for vertical movements
BLINK_THRESHOLD = 0.2
BLINK_DURATION = 0.2
CLOSE_EYE_DURATION_DISABLE = 2.0  # For disabling tracking
CLOSE_EYE_DURATION_BACK = 5.0 # For enabling/disabling scrolling and navigation
CLOSE_EYE_DURATION_CLICK = 3.0

# Global variables for tracking state
tracking_enabled = False
last_movement = DIRECTIONS["center"]
tracking_thread = None
stable_start_time = None
last_iris_position = None
click_triggered = False
eye_close_start = None

def calculate_position_ratio(iris_landmarks, eye_landmarks):
    """
    Calculate the relative position of the iris within the eye boundary.
    """
    # Eye boundaries
    left = np.array(eye_landmarks[0])  # Leftmost point
    right = np.array(eye_landmarks[1])  # Rightmost point
    top = np.array(eye_landmarks[2])  # Topmost point
    bottom = np.array(eye_landmarks[3])  # Bottommost point

    # Compute the center of the iris
    iris_center = np.mean(iris_landmarks, axis=0)

    # Normalize iris position
    horizontal_ratio = (iris_center[0] - left[0]) / (right[0] - left[0])
    vertical_ratio = (iris_center[1] - top[1]) / (bottom[1] - top[1])

    return float(horizontal_ratio), float(vertical_ratio)

def detect_movement(horizontal_ratio, vertical_ratio):
    """
    Detect the movement direction based on iris position ratios with adjusted sensitivity.
    """
    if horizontal_ratio < 0.5 - SENSITIVITY_HORIZONTAL:
        return DIRECTIONS["left"]
    elif horizontal_ratio > 0.5 + SENSITIVITY_HORIZONTAL:
        return DIRECTIONS["right"]
    elif vertical_ratio < 0.5 - SENSITIVITY_VERTICAL:
        return DIRECTIONS["up"]
    elif vertical_ratio > 0.5 + SENSITIVITY_VERTICAL:
        return DIRECTIONS["down"]
    else:
        return DIRECTIONS["center"]

def perform_action_based_on_movement(movement):
    """
    Perform scrolling based on detected eye movement (no cursor movement).
    """
    if movement == DIRECTIONS["down"]:
        pyautogui.scroll(-100)  # Scroll down
    elif movement == DIRECTIONS["up"]:
        pyautogui.scroll(100)  # Scroll up

def detect_blink_or_close(eye_landmarks):
    """
    Detect blink or closed eye based on the eye aspect ratio.
    """
    top = np.array(eye_landmarks[2])  # Topmost point
    bottom = np.array(eye_landmarks[3])  # Bottommost point
    left = np.array(eye_landmarks[0])  # Leftmost point
    right = np.array(eye_landmarks[1])  # Rightmost point

    vertical_distance = np.linalg.norm(top - bottom)
    horizontal_distance = np.linalg.norm(left - right)

    return vertical_distance / horizontal_distance

def tracking_loop():
    global tracking_enabled, last_movement, stable_start_time, last_iris_position, click_triggered, eye_close_start
    cap = cv2.VideoCapture(0)

    while tracking_enabled:
        ret, frame = cap.read()
        if not ret:
            break

        # Flip the frame for a mirror-like view
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb_frame)

        if result.multi_face_landmarks:
            for face_landmarks in result.multi_face_landmarks:
                # Extract iris, eye, and nose landmarks
                iris_left = [
                    (face_landmarks.landmark[point].x, face_landmarks.landmark[point].y)
                    for point in IRIS_LEFT_LANDMARKS
                ]
                iris_right = [
                    (face_landmarks.landmark[point].x, face_landmarks.landmark[point].y)
                    for point in IRIS_RIGHT_LANDMARKS
                ]
                left_eye = [
                    (face_landmarks.landmark[point].x, face_landmarks.landmark[point].y)
                    for point in LEFT_EYE_LANDMARKS
                ]
                right_eye = [
                    (face_landmarks.landmark[point].x, face_landmarks.landmark[point].y)
                    for point in RIGHT_EYE_LANDMARKS
                ]
                nose = (
                    face_landmarks.landmark[NOSE_LANDMARK].x,
                    face_landmarks.landmark[NOSE_LANDMARK].y
                )

                frame_height, frame_width, _ = frame.shape
                iris_left_pixel = [(x * frame_width, y * frame_height) for x, y in iris_left]
                iris_right_pixel = [(x * frame_width, y * frame_height) for x, y in iris_right]
                left_eye_pixel = [(x * frame_width, y * frame_height) for x, y in left_eye]
                right_eye_pixel = [(x * frame_width, y * frame_height) for x, y in right_eye]
                nose_pixel = (nose[0] * frame_width, nose[1] * frame_height)

                # Detect blink or closed eyes
                left_eye_ratio = detect_blink_or_close(left_eye_pixel)
                right_eye_ratio = detect_blink_or_close(right_eye_pixel)

                # Handle Eye Closure and Gestures
                if left_eye_ratio < BLINK_THRESHOLD or right_eye_ratio < BLINK_THRESHOLD:
                    if eye_close_start is None:
                        eye_close_start = time.time()

                if left_eye_ratio < BLINK_THRESHOLD and right_eye_ratio >= BLINK_THRESHOLD:
                    pyautogui.moveRel(-40, 0)  # Move cursor left
                    print("Left eye blink detected: Moving cursor left")
                elif right_eye_ratio < BLINK_THRESHOLD and left_eye_ratio >= BLINK_THRESHOLD:
                    pyautogui.moveRel(40, 0)  # Move cursor right
                    print("Right eye blink detected: Moving cursor right")

                else:
                    if eye_close_start is not None:
                        eye_close_duration = time.time() - eye_close_start

                        if eye_close_duration >= CLOSE_EYE_DURATION_CLICK and not click_triggered:
                            pyautogui.click()  # Perform click after 5 seconds of eye closure
                            print("Eye closure detected for 5 seconds: Performing click")
                            click_triggered = True  # Prevent triggering multiple clicks
                        
                        if eye_close_duration < CLOSE_EYE_DURATION_CLICK:
                            click_triggered = False  # Reset click trigger if not enough duration

                        eye_close_start = None

                if tracking_enabled:
                    horizontal_ratio_left, vertical_ratio_left = calculate_position_ratio(iris_left_pixel, left_eye_pixel)
                    horizontal_ratio_right, vertical_ratio_right = calculate_position_ratio(iris_right_pixel, right_eye_pixel)

                    movement_left = detect_movement(horizontal_ratio_left, vertical_ratio_left)
                    movement_right = detect_movement(horizontal_ratio_right, vertical_ratio_right)

                    if movement_left == DIRECTIONS["left"] or movement_right == DIRECTIONS["left"]:
                        pyautogui.scroll(25)  # Scroll up
                    elif movement_left == DIRECTIONS["right"] or movement_right == DIRECTIONS["right"]:
                        pyautogui.scroll(-25)  # Scroll down
                    
                    current_iris_position = (
                        np.mean([horizontal_ratio_left, vertical_ratio_left]) +
                        np.mean([horizontal_ratio_right, vertical_ratio_right])
                    ) / 2

                    if last_iris_position is None:
                        last_iris_position = current_iris_position

                    # Check for movement
                    if abs(current_iris_position - last_iris_position) < 0.5:  # Adjust threshold as needed
                        if stable_start_time is None:
                            stable_start_time = time.time()
                        else:
                            stable_duration = time.time() - stable_start_time
                            if stable_duration >= STABLE_DURATION_CLICK:
                                if not click_triggered:
                                    pyautogui.click()  # Perform click after 5 seconds of stability
                                    print("Iris stable for 5 seconds: Click action triggered")
                                    click_triggered = True  # Prevent multiple clicks
                                stable_start_time = None  # Reset the timer
                    else:
                        stable_start_time = None  # Reset stability timer on movement

                    last_iris_position = current_iris_position

    cap.release()

@app.route('/start', methods=['POST'])
def start_tracking():
    global tracking_enabled, tracking_thread
    if not tracking_enabled:
        tracking_enabled = True
        tracking_thread = threading.Thread(target=tracking_loop)
        tracking_thread.start()
        return jsonify({'message': 'Tracking started'}), 200
    else:
        return jsonify({'message': 'Tracking is already running'}), 400

@app.route('/stop', methods=['POST'])
def stop_tracking():
    global tracking_enabled, tracking_thread
    if tracking_enabled:
        tracking_enabled = False
        if tracking_thread and tracking_thread.is_alive():
            tracking_thread.join()  # Wait for the thread to finish
        return jsonify({'message': 'Tracking stopped'}), 200
    else:
        return jsonify({'message': 'Tracking is not running'}), 400

@app.route('/status', methods=['GET'])
def get_status():
    global tracking_enabled
    return jsonify({'tracking_enabled': tracking_enabled}), 200

if __name__ == '__main__':
    app.run(debug=True, threaded=True)