"""Pixel-based multi-object HSV detection and consecutive-frame validation."""
import cv2
import numpy as np
from pick_core import COLORS, Camera


def decode_bgr(data, height, width, step, encoding):
    channels = {'bgr8': 3, 'rgb8': 3, 'mono8': 1}.get(encoding)
    if not channels or height <= 0 or width <= 0 or step < width*channels:
        raise ValueError('Unsupported image encoding or dimensions')
    raw = np.frombuffer(data, np.uint8)
    if len(raw) != height*step:
        raise ValueError('Image length does not match height * step')
    image = raw.reshape(height, step)[:, :width*channels].reshape(height, width, channels)
    if encoding == 'rgb8':
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    if encoding == 'mono8':
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image.copy()


class Detector:
    def __init__(self, camera, stable_frames=3, max_shift=.008, source_x=.29, source_half_width=.03):
        self.camera = Camera(camera)
        self.required, self.shift = stable_frames, max_shift
        self.source_x, self.half_width = source_x, source_half_width
        self.previous, self.counts = {}, {}

    def detect(self, image):
        if image.shape != (self.camera.h, self.camera.w, 3):
            raise ValueError('Resolution differs from calibrated virtual camera')
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        debug, objects = image.copy(), []
        ranges = {'red': [(0, 10), (170, 179)], 'yellow': [(20, 35)],
                  'blue': [(95, 130)], 'green': [(40, 85)]}
        for color, intervals in ranges.items():
            mask = np.zeros(hsv.shape[:2], np.uint8)
            for low, high in intervals:
                mask |= cv2.inRange(hsv, (low, 75, 35), (high, 255, 255))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                if area < 80 or not .55 < w/float(h) < 1.8 or area/(w*h) < .40:
                    continue
                moments = cv2.moments(contour)
                uv = [moments['m10']/moments['m00'], moments['m01']/moments['m00']]
                point = self.camera.world(*uv)
                eligible = abs(point[0]-self.source_x) <= self.half_width
                objects.append(dict(color=color, pixel=uv, xy=point, area_px=area, eligible=eligible))
                cv2.rectangle(debug, (x, y), (x+w, y+h), (255, 255, 255), 2)
                cv2.putText(debug, color, (x, max(18, y-6)), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 2)
        stable, ambiguous = {}, []
        current = {}
        for color in COLORS:
            candidates = [o for o in objects if o['color'] == color and o['eligible']]
            if len(candidates) != 1:
                if len(candidates) > 1:
                    ambiguous.append(color)
                self.counts[color] = 0
                continue
            point = candidates[0]['xy']
            current[color] = point
            close = color in self.previous and np.linalg.norm(np.array(point)-self.previous[color]) <= self.shift
            self.counts[color] = self.counts.get(color, 0)+1 if close else 1
            if self.counts[color] >= self.required:
                stable[color] = point
        self.previous = current
        return dict(objects=objects, stable=stable, ambiguous=ambiguous), debug
