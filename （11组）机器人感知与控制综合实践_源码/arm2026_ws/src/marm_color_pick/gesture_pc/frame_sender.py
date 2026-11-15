"""Optional localhost-only preview transport with a single replaceable frame."""
import threading
from urllib.request import Request, urlopen
import cv2


class FrameSender:
    def __init__(self, connection):
        self.connection, self.frame = connection, None
        self.condition = threading.Condition()
        self.stopped, self.sent, self.error = False, 0, ''
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def offer(self, frame):
        with self.condition:
            self.frame = frame.copy()
            self.condition.notify()

    def run(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.stopped or self.frame is not None)
                if self.stopped:
                    return
                frame, self.frame = self.frame, None
            try:
                ok, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if not ok:
                    raise ValueError('JPEG encoding failed')
                req = Request(self.connection['url']+'/camera', data=jpeg.tobytes(),
                              headers={'Content-Type': 'image/jpeg',
                                       'X-Arm-Gesture-Token': self.connection['token']})
                with urlopen(req, timeout=.5) as response:
                    response.read()
                self.sent, self.error = self.sent+1, ''
            except Exception as error:
                self.error = str(error)

    def close(self):
        with self.condition:
            self.stopped = True
            self.condition.notify()
        self.thread.join(timeout=1)
