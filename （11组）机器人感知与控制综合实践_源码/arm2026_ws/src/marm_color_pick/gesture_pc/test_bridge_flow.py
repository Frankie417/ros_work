"""Synthetic gesture-event -> authenticated Windows/WSL -> live virtual-arm test.

No webcam is opened. This is NOT a live human gesture accuracy test.
"""
import argparse
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import uuid
from gesture_gate import GestureGate, COLORS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--connection', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.connection).read_text())

    def request(path, data=None, authorized=True):
        headers = {'Content-Type': 'application/json'}
        if authorized:
            headers['X-Arm-Gesture-Token'] = config['token']
        body = None if data is None else json.dumps(data).encode('utf-8')
        with urlopen(Request(config['url']+path, data=body, headers=headers), timeout=3) as response:
            return json.loads(response.read())

    def rejected(path, data=None, authorized=True, expected=409):
        try:
            request(path, data, authorized)
        except HTTPError as error:
            assert error.code == expected, error.code
        else:
            raise AssertionError('Unsafe request accepted')

    rejected('/status', authorized=False, expected=403)
    rejected('/command', dict(color='all', request_id=str(uuid.uuid4()), session=config['session']))
    rejected('/command', dict(color='red', request_id=str(uuid.uuid4()), session='expired'))
    request('/reset', {})
    deadline = time.monotonic()+5
    while time.monotonic() < deadline:
        state = request('/status')
        if state['ready'] and not state['robot']['completed']:
            break
        time.sleep(.05)
    else:
        raise AssertionError('Reset timed out')
    results = []
    for number, color in COLORS.items():
        gate, now, events = GestureGate(), 0., []
        for label, duration in [('none', .5), (number, .9), ('none', .5), ('OK', 1.5)]:
            for _ in range(round(duration/.05)):
                now += .05
                event = gate.feed(label, now)
                if event:
                    events.append(event)
        assert events == [color]
        data = dict(color=color, request_id=str(uuid.uuid4()), session=config['session'])
        receipt = request('/command', data)
        assert receipt['accepted']
        assert request('/command', data) == receipt  # Same request never enqueues twice.
        rejected('/command', dict(color=color, request_id=str(uuid.uuid4()), session=config['session']))
        deadline = time.monotonic()+20
        raised, seen_busy = False, False
        while time.monotonic() < deadline:
            state = request('/status')
            robot = state['robot']
            assert not robot['error'], robot['error']
            seen_busy |= not state['ready']
            if robot.get('attached') == color and robot['blocks'][color][2] > .12:
                raised = True
            if color in robot['completed'] and state['ready']:
                break
            time.sleep(.05)
        else:
            raise AssertionError('Colour job timed out: '+color)
        assert raised and seen_busy
        assert sum(e['event'] == 'attach' and e['color'] == color for e in robot['events']) == 1
        results.append(dict(gesture=number, color=color, confirmed=True, lift_observed=True,
                            duplicate_suppressed=True))
        print('PASS:', number, '-> OK ->', color, flush=True)
    robot = request('/status')['robot']
    assert robot['completed'] == list(COLORS.values())
    assert len(robot['events']) == 8
    record = dict(result='PASS', scope='synthetic gesture events, live Windows-to-WSL/ROS virtual-arm execution; not human gesture accuracy',
                  colors=results, unauthorized_rejected=True, invalid_color_rejected=True,
                  stale_session_rejected=True, busy_rejected=True, events=robot['events'])
    Path(args.output).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS: authenticated bridge, four jobs, deduplication and gates')


if __name__ == '__main__':
    main()
