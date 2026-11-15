#!/usr/bin/env python3
"""Offline regression tests; no ROS master required."""
import argparse
import json
import math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2
import numpy as np
import yaml
from pick_core import Arm, Camera, COLORS, transform


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--urdf', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--output')
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).read_text())
    arm = Arm(Path(args.urdf).read_text(), config['cube_size'])
    camera = Camera(config['camera'])
    z = config['table_height']+config['cube_size']/2
    source = {c: np.array([config['source_x'], y, z]) for c, y in zip(COLORS, config['rows'])}
    rotations = {c: transform(rpy=(0, 0, math.atan2(p[1], p[0])))[:3, :3] for c, p in source.items()}
    image = camera.render(source, config['cube_size'], rotations)
    detections, debug = camera.detect(image)
    assert set(detections) == set(COLORS)
    errors = {c: float(np.linalg.norm(np.array(detections[c])-source[c][:2])) for c in COLORS}
    assert max(errors.values()) < .001
    for color in COLORS:
        q = arm.ik(source[color], arm.grip)
        frame = arm.fk(q)['marm_mod_gripper_stator']
        corners = []
        for a in [-1, 1]:
            for b in [-1, 1]:
                for c in [-1, 1]:
                    world = source[color]+rotations[color] @ (np.array([a, b, c])*arm.size/2)
                    corners.append((np.linalg.inv(frame) @ np.r_[world, 1])[:3])
        corners = np.array(corners)
        assert abs(corners[:, 2].min()) < 1e-9
        assert abs(corners[:, 2].max()-arm.size) < 1e-9
    blank, _ = camera.detect(np.full_like(image, 65))
    assert not blank
    # Both sides of the red hue wrap must classify as red, not another colour.
    for hue in [0, 179]:
        hsv = np.zeros_like(image)
        hsv[100:150, 100:150] = (hue, 230, 230)
        found, _ = camera.detect(cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR))
        assert set(found) == {'red'}
    count, error_max = 0, 0.
    current = arm.home
    for color, y in zip(COLORS, config['rows']):
        pick = np.array(detections[color]+[z])
        place = np.array([config['destination_x'], y, z])
        lift = np.array([0, 0, config['lift_height']])
        for end in [pick+lift, pick, pick+lift, place+lift, place, place+lift]:
            for u in np.linspace(0, 1, 101):
                point = current*(1-u)+end*u
                q = arm.ik(point, arm.grip)
                actual, _ = arm.object_pose(q)
                error_max = max(error_max, float(np.linalg.norm(actual-point)))
                count += 1
            current = end
    for point in [[2, 0, z], [.3, 0, .7]]:
        try:
            arm.ik(point)
        except ValueError:
            pass
        else:
            raise AssertionError('Unreachable target accepted')
    record = dict(colors=list(COLORS), camera_error_m=errors, path_samples=count,
                  maximum_fk_error_m=error_max, blank_rejected=True, red_wrap_pass=True,
                  unreachable_rejected=True, cube_face_alignment_pass=True, grip_angle_rad=arm.grip,
                  scope='kinematic only; no dynamics or whole-arm collision certification')
    if args.output:
        Path(args.output).write_text(json.dumps(record, ensure_ascii=False, indent=2))
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
