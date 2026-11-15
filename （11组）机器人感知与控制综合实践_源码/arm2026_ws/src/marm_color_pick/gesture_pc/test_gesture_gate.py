"""Synthetic event tests; not a claim of live human recognition accuracy."""
from gesture_gate import GestureGate, COLORS


def run():
    now = 0.
    results = []
    gate = GestureGate()

    def frames(label, duration, ready=True):
        nonlocal now
        outputs = []
        for _ in range(round(duration/.05)):
            now += .05
            output = gate.feed(label, now, ready)
            if output:
                outputs.append(output)
        return outputs

    assert not frames('none', .5)
    assert not frames('OK', 1.)  # OK alone never triggers.
    for number, color in COLORS.items():
        assert not frames(number, .9)
        assert not frames('OK', .9)  # Must relax between number and OK.
        assert not frames('none', .5)
        assert frames('OK', .9) == [color]
        assert not frames('OK', 2.)  # Held OK cannot repeat.
        results.append(color)
        frames('none', .5)
    assert not frames('1', .2)  # Brief flash is rejected.
    frames('none', .4)
    assert gate.selected is None
    frames('1', .9)
    frames('none', 9.)
    assert not frames('OK', .9)  # Expired selection cannot confirm.
    frames('none', .5)
    frames('2', 1., ready=False)
    frames('OK', 1., ready=False)
    assert gate.selected is None
    frames('none', .5)
    assert not frames('blocked', 2.)  # Multiple hands cannot trigger.
    gate.reset()
    frames('none', .5)
    frames('1', .9)
    frames('none', .6)
    assert not frames('OK', .3)
    assert not frames('none', .1)  # Brief dropout must not dispatch by itself.
    assert frames('OK', .4) == ['red']
    assert not frames('OK', 1.)
    print('PASS: four colours; OK alone, no-relax, repeat, flash, expiry, busy and multi-hand rejection')
    return results


if __name__ == '__main__':
    run()
