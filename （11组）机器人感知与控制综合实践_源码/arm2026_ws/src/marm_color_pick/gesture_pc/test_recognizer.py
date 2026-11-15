"""Synthetic landmarks and drawing tests; not human recognition accuracy."""
from types import SimpleNamespace as S
from unittest.mock import patch
import numpy as np
import cv2
from recognizer import classify, draw


def hand(number):
    points = [S(x=.45, y=.85, z=0.) for _ in range(21)]
    for index, x in enumerate([.25, .40, .55, .70]):
        base = 5+4*index
        extended = index < number
        for offset, y in enumerate([.65, .50 if extended else .53, .40 if extended else .58, .30 if extended else .64]):
            points[base+offset] = S(x=x, y=y, z=0.)
    points[4] = S(x=.50, y=.64, z=0.)
    return points


def run():
    image = np.zeros((480, 640, 3), np.uint8)

    def recognize(hands):
        class Model:
            def recognize_for_video(self, *_):
                return S(hand_landmarks=hands, gestures=[])
        return classify(image, Model(), 1)[0]

    for number in range(1, 5):
        assert recognize([hand(number)]) == str(number)
    ok = hand(4)
    folded = hand(0)
    ok[5:9] = folded[5:9]
    ok[4] = S(x=ok[8].x, y=ok[8].y, z=0.)
    assert recognize([ok]) == 'OK'
    # Near-touching fingertips at 0.35 palm widths were rejected by the old .32 cutoff.
    ok[4] = S(x=ok[8].x+.35*.45, y=ok[8].y, z=0.)
    assert recognize([ok]) == 'OK'
    ok[4] = S(x=ok[8].x+.55*.45, y=ok[8].y, z=0.)
    assert recognize([ok]) != 'OK'
    assert recognize([]) == 'none'
    assert recognize([hand(1), hand(2)]) == 'blocked'
    with patch.object(cv2, 'circle', wraps=cv2.circle) as circles:
        with patch.object(cv2, 'putText', wraps=cv2.putText) as texts:
            picture = draw(image, [hand(4)])
            assert circles.call_count == 42  # Dark outline + coloured centre, for 21 joints.
            assert texts.call_count == 42  # Outlined IDs 0..20.
            assert set(str(i) for i in range(21)) == {call.args[1] for call in texts.call_args_list}
            assert np.any(picture != image)
    assert np.array_equal(draw(image, []), image)
    print('PASS: synthetic 1/2/3/4/OK; no-hand/multi-hand; 21 joint dots and IDs; five finger colours')


if __name__ == '__main__':
    run()
