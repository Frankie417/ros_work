#!/usr/bin/env python3
"""Local Windows webcam probe. Metadata only; no frames saved or uploaded."""
import argparse
import json
from pathlib import Path
import platform
import time
import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--preview', type=float, default=15.)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    report = dict(platform=platform.platform(), opencv=cv2.__version__, camera_index=args.camera,
                  opened=False, frames=0, images_saved=False, frames_uploaded=False)
    capture = None
    try:
        for backend in (cv2.CAP_DSHOW, cv2.CAP_MSMF):
            capture = cv2.VideoCapture(args.camera, backend)
            if capture.isOpened():
                report['backend'] = capture.getBackendName()
                break
            capture.release()
        if not capture.isOpened():
            raise RuntimeError('Cannot open webcam. Check Windows camera permissions and other camera apps.')
        report['opened'] = True
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        start = time.monotonic()
        previous, changes = None, []
        while time.monotonic()-start < max(args.preview, 3):
            ok, frame = capture.read()
            if not ok or frame is None:
                raise RuntimeError('Camera opened but frame read failed')
            report['frames'] += 1
            report['shape'] = list(frame.shape)
            report['pixel_mean'] = round(float(np.mean(frame)), 3)
            report['pixel_std'] = round(float(np.std(frame)), 3)
            if previous is not None:
                changes.append(float(np.mean(cv2.absdiff(frame, previous))))
            previous = frame.copy()
            if args.preview > 0:
                view = cv2.flip(frame, 1)
                cv2.putText(view, 'LOCAL CAMERA TEST - no recording - ESC to close',
                            (10, 25), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 255, 0), 1)
                cv2.imshow('Arm2026 camera test', view)
                if cv2.waitKey(1) & 255 in (27, ord('q')):
                    break
        report['duration_s'] = round(time.monotonic()-start, 3)
        report['read_fps'] = round(report['frames']/report['duration_s'], 2)
        report['mean_frame_change'] = round(float(np.mean(changes)), 3) if changes else 0
        report['result'] = 'PASS' if report['frames'] >= 10 and report['pixel_std'] > 2 else 'CHECK_DARK_OR_SHORT_CAPTURE'
    except Exception as error:
        report['result'], report['error'] = 'FAIL', str(error)
    finally:
        if capture is not None:
            capture.release()
        cv2.destroyAllWindows()
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if report['result'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
