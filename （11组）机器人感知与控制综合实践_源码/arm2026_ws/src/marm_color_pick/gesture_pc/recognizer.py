"""MediaPipe landmarks with explicit geometry rules for digits and OK.

Geometric checks are not calibrated probability scores. Only a single hand is
accepted; ambiguous poses are ignored. No camera frames leave this process.
"""
import math
from pathlib import Path
import cv2
import mediapipe as mp
import numpy as np


def create(model):
    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_buffer=Path(model).read_bytes()),
        running_mode=mp.tasks.vision.RunningMode.VIDEO, num_hands=2,
        min_hand_detection_confidence=.5, min_hand_presence_confidence=.5,
        min_tracking_confidence=.5)
    return mp.tasks.vision.GestureRecognizer.create_from_options(options)


def classify(frame, model, timestamp, diagnostics=None):
    image = mp.Image(image_format=mp.ImageFormat.SRGB,
                     data=np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    result = model.recognize_for_video(image, timestamp)
    hands = result.hand_landmarks
    if diagnostics is not None:
        diagnostics['hand_count'] = len(hands)
    if len(hands) != 1:
        return ('none' if not hands else 'blocked'), hands
    points = hands[0]
    ratio = frame.shape[1]/frame.shape[0]

    def distance(a, b):
        return math.hypot((points[a].x-points[b].x)*ratio, points[a].y-points[b].y)

    extension = [distance(tip, base)/max(distance(mid, base), 1e-6)
                 for base, mid, tip in ((5, 6, 8), (9, 10, 12), (13, 14, 16), (17, 18, 20))]
    palm = max(distance(5, 17), 1e-6)
    ring = distance(4, 8)/palm
    straight = [r >= 1.85 for r in extension]
    bent = [r <= 1.55 for r in extension]
    # A natural OK has a curled index and three raised fingers. The former .32
    # tip-distance cutoff rejected near-touching fingertips; use the week7-like
    # .42 cutoff plus explicit index curl instead of relaxing to any pinch.
    ok_fingers = all(r >= 1.65 for r in extension[1:])
    if diagnostics is not None:
        diagnostics.update(ring_ratio=round(ring, 3), ring_threshold=.42,
                           finger_extension=[round(r, 3) for r in extension],
                           ok_tip_close=ring <= .42, ok_index_curled=extension[0] <= 1.65,
                           ok_three_fingers=ok_fingers)
    if ring <= .42 and extension[0] <= 1.65 and ok_fingers:
        return 'OK', hands
    # Official classifiers help with foreshortened one/two-finger poses.
    # Three, four and OK remain explicit landmark rules, not model probabilities.
    if result.gestures and result.gestures[0] and ring > .42:
        category = result.gestures[0][0]
        if category.score >= .70 and category.category_name in ('Pointing_Up', 'Victory'):
            return {'Pointing_Up': '1', 'Victory': '2'}[category.category_name], hands
    if straight[0] and all(bent[1:]) and ring > .42:
        return '1', hands
    if all(straight[:2]) and all(bent[2:]) and ring > .42:
        return '2', hands
    if all(straight[:3]) and bent[3] and ring > .42:
        return '3', hands
    if all(straight) and distance(4, 9)/palm < 1.05 and ring > .42:
        return '4', hands
    return 'none', hands


def draw(frame, hands):
    frame = frame.copy()
    h, w = frame.shape[:2]
    lines = ((0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
             (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
             (15, 16), (13, 17), (0, 17), (17, 18), (18, 19), (19, 20))
    colors = ((255, 180, 60), (0, 230, 255), (65, 230, 65), (230, 80, 230), (30, 140, 255))
    for hand in hands:
        for a, b in lines:
            color = colors[(b-1)//4] if b > 0 else (240, 240, 240)
            cv2.line(frame, (int(hand[a].x*w), int(hand[a].y*h)),
                     (int(hand[b].x*w), int(hand[b].y*h)), color, 3, cv2.LINE_AA)
        # All 21 joints, including wrist, with readable IDs; never fabricate absent hands.
        for index, point in enumerate(hand):
            x, y = int(point.x*w), int(point.y*h)
            color = (245, 245, 245) if index == 0 else colors[(index-1)//4]
            cv2.circle(frame, (x, y), 7, (20, 20, 20), -1, cv2.LINE_AA)
            cv2.circle(frame, (x, y), 5, color, -1, cv2.LINE_AA)
            text = str(index)
            cv2.putText(frame, text, (x+7, y-7), cv2.FONT_HERSHEY_SIMPLEX, .42,
                        (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(frame, text, (x+7, y-7), cv2.FONT_HERSHEY_SIMPLEX, .42,
                        (255, 255, 255), 1, cv2.LINE_AA)
    return frame
