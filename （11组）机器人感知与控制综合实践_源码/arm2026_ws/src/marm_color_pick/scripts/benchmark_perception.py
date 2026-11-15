#!/usr/bin/env python3
"""Repeatable synthetic perturbation benchmark; never a physical-camera accuracy claim."""
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2
import numpy as np
import yaml
from pick_core import Camera, COLORS, transform
from perception_core import Detector, decode_bgr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).read_text())
    camera = Camera(config['camera'])
    rng = np.random.RandomState(20261113)
    results, latencies = [], []
    for name in ['normal', 'dim', 'noise', 'holes', 'blur']:
        old_hits, new_hits, errors = 0, 0, []
        for trial in range(12):
            blocks = {c: np.array([.29+rng.uniform(-.006, .006), y+rng.uniform(-.008, .008), .074])
                      for c, y in zip(COLORS, config['rows'])}
            rotations = {c: transform(rpy=(0, 0, rng.uniform(-.7, .7)))[:3, :3] for c in COLORS}
            image = camera.render(blocks, config['cube_size'], rotations)
            if name == 'dim':
                image = (image.astype(float)*.27).astype(np.uint8)
            elif name == 'noise':
                image = np.clip(image.astype(float)+rng.normal(0, 14, image.shape), 0, 255).astype(np.uint8)
            elif name == 'holes':
                for _ in range(500):
                    u, v = rng.randint(camera.w), rng.randint(camera.h)
                    cv2.circle(image, (u, v), 1, (65, 65, 65), -1)
            elif name == 'blur':
                image = cv2.GaussianBlur(image, (7, 7), 1.8)
            baseline, _ = camera.detect(image)
            old_hits += sum(c in baseline and np.linalg.norm(np.array(baseline[c])-blocks[c][:2]) < .002 for c in COLORS)
            detector = Detector(config['camera'])
            for _ in range(3):
                start = time.perf_counter()
                found, _ = detector.detect(image)
                latencies.append((time.perf_counter()-start)*1000)
            for c in COLORS:
                if c in found['stable']:
                    error = float(np.linalg.norm(np.array(found['stable'][c])-blocks[c][:2]))
                    errors.append(error)
                    new_hits += int(error < .002)
            if trial == 0:
                cv2.imwrite(str(Path(args.output).parent/('benchmark_'+name+'.png')), image)
        results.append(dict(condition=name, frames=12, expected_targets=48,
                            baseline_hits_under_2mm=int(old_hits), improved_hits_under_2mm=int(new_hits),
                            max_detected_error_m=max(errors) if errors else None))
    detector = Detector(config['camera'])
    blank = np.full((camera.h, camera.w, 3), 65, np.uint8)
    assert not detector.detect(blank)[0]['stable']
    image = camera.render({'red': np.array([.29, -.12, .074])}, .028)
    for _ in range(3):
        found, _ = detector.detect(image)
    assert 'red' in found['stable']
    assert not detector.detect(blank)[0]['stable'], 'Missing target must invalidate immediately'
    for y in [-.12, .04]:
        u, v = camera.pixel(.29, y)
        cv2.rectangle(blank, (u-15, v-15), (u+15, v+15), (0, 0, 230), -1)
    for _ in range(3):
        found, _ = detector.detect(blank)
    assert found['ambiguous'] == ['red'] and not found['stable']
    detector = Detector(config['camera'])
    assert not detector.detect(image)[0]['stable']
    assert not detector.detect(image)[0]['stable']
    assert 'red' in detector.detect(image)[0]['stable']
    padded = np.array([[1, 2, 3, 4, 5, 6, 99, 99]], np.uint8)
    assert decode_bgr(padded.tobytes(), 1, 2, 8, 'rgb8').tolist() == [[[3, 2, 1], [6, 5, 4]]]
    for bad in [(b'', 1, 2, 8, 'rgb8'), (b'1234', 1, 1, 4, 'bad')]:
        try:
            decode_bgr(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError('Bad image accepted')
    record = dict(seed=20261113, scope='synthetic image perturbations, not real-camera/physical grasp accuracy',
                  results=results, mean_ms=float(np.mean(latencies)), p95_ms=float(np.percentile(latencies, 95)),
                  checks=dict(blank=True, missing_target=True, same_color_ambiguity=True,
                              consecutive_frames=True, padded_rgb=True, malformed_images=True))
    Path(args.output).write_text(json.dumps(record, ensure_ascii=False, indent=2))
    assert all(r['improved_hits_under_2mm'] >= r['baseline_hits_under_2mm'] for r in results)
    assert sum(r['improved_hits_under_2mm'] for r in results) > sum(r['baseline_hits_under_2mm'] for r in results)
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
