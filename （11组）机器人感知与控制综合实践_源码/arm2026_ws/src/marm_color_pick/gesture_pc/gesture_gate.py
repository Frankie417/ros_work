"""Debounced number -> neutral -> OK handshake; independent of camera/ROS."""
COLORS = {'1': 'red', '2': 'yellow', '3': 'blue', '4': 'green'}


class GestureGate:
    def __init__(self):
        self.reset()

    def reset(self):
        self.state, self.selected = '先放松手势', None
        self.label, self.since, self.deadline = None, 0., 0.
        self.last_seen, self.progress = 0., 0.

    def feed(self, label, now, ready=True):
        raw_label = label
        # At webcam rates a single missed detection should not reset a held
        # gesture. A different recognised gesture or multiple hands still reset
        # it immediately. Never dispatch on a missing/unknown frame.
        if label == 'none' and self.label in tuple(COLORS)+('OK',) and now-self.last_seen <= .12:
            label = self.label
        elif label != 'none':
            self.last_seen = now
        if label != self.label:
            self.label, self.since = label, now
        held = now-self.since
        self.progress = 0.
        if not ready:
            self.selected, self.state = None, '机械臂忙碌或未连接'
            self.label, self.since = None, now
            return None
        if self.state == '机械臂忙碌或未连接':
            self.state = '先放松手势'
        if self.selected and now > self.deadline:
            self.selected, self.state = None, '先放松手势'
        if self.state in ('先放松手势', '已发送，请放松'):
            if label == 'none' and held+1e-8 >= .35:
                self.state = '等待数字1～4'
        elif self.state == '等待数字1～4':
            self.progress = min(1., held/.65) if label in COLORS else 0.
            if label in COLORS and raw_label == label and held+1e-8 >= .65:
                self.selected, self.deadline = label, now+8.
                self.state = '已选择，请先放松'
        elif self.state == '已选择，请先放松':
            if label == 'none' and held+1e-8 >= .30:
                self.state = '请做OK确认'
        elif self.state == '请做OK确认':
            self.progress = min(1., held/.55) if label == 'OK' else 0.
            if label == 'OK' and raw_label == 'OK' and held+1e-8 >= .55:
                color = COLORS[self.selected]
                self.selected, self.state = None, '已发送，请放松'
                return color
        return None
