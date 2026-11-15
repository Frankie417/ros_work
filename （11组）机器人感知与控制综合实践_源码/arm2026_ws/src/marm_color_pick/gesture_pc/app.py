#!/usr/bin/env python3
"""Windows webcam UI, disarmed by default; optional local ROS image preview."""
import argparse
import json
from pathlib import Path
import time
import uuid
from urllib.request import Request, urlopen
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from gesture_gate import GestureGate, COLORS
from recognizer import create, classify, draw
from frame_sender import FrameSender

HERE = Path(__file__).resolve().parent
ZH = {'red': '红', 'yellow': '黄', 'blue': '蓝', 'green': '绿'}


def request(connection, path, data=None):
    headers = {'X-Arm-Gesture-Token': connection['token']}
    if data is not None:
        headers['Content-Type'] = 'application/json'
    req = Request(connection['url']+path,
                  data=None if data is None else json.dumps(data).encode('utf-8'), headers=headers)
    with urlopen(req, timeout=1.5) as response:
        return json.loads(response.read())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--model', default=str(HERE/'models/gesture_recognizer.task'))
    parser.add_argument('--connection', default=r'\\wsl.localhost\Ubuntu-20.04\home\cubertzk\.ros\arm2026_gesture_bridge.json')
    parser.add_argument('--probe-seconds', type=float, default=0, help='Recognition only; auto-exit; cannot arm')
    parser.add_argument('--report', help='Metadata only; never saves webcam frames')
    parser.add_argument('--telemetry', help='Optional live metadata file; no frames or credentials')
    parser.add_argument('--publish-images', action='store_true', help='Send preview images only to the local ROS bridge')
    args = parser.parse_args()
    connection = None
    if Path(args.connection).is_file():
        connection = json.loads(Path(args.connection).read_text())
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 20)
    gate = GestureGate()
    camera, model = None, None
    enabled, remote, network_error = False, {}, '未连接；可先测试手势'
    last_poll, last_frame, last_telemetry = -10., time.monotonic(), -10.
    timestamp, start = -1, time.monotonic()
    last_action = '尚未发送指令'
    report = dict(frames=0, labels={}, hand_frames=0, commands_sent=0, images_saved=False, frames_uploaded=False)
    sender, last_upload = None, -10.
    try:
        model = create(args.model)
        if args.publish_images:
            if not connection or not connection['url'].startswith('http://127.0.0.1:'):
                raise ValueError('Image preview requires a localhost connection file')
            sender = FrameSender(connection)
        camera = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
        if not camera.isOpened():
            raise RuntimeError('摄像头无法打开，请关闭占用程序并检查Windows相机权限')
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cv2.namedWindow('Arm2026 gesture control', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Arm2026 gesture control', 960, 1035)
        cv2.moveWindow('Arm2026 gesture control', 100, 80)
        while True:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError('摄像头取帧失败；不再发送指令')
            now = time.monotonic()
            if now-last_frame > .35:
                gate.reset()
            last_frame = now
            frame = cv2.flip(frame, 1)
            if sender and now-last_upload >= .5:
                sender.offer(frame)
                last_upload = now
            timestamp = max(timestamp+1, int(now*1000))
            diagnostics = {}
            label, hands = classify(frame, model, timestamp, diagnostics)
            report['frames'] += 1
            report['labels'][label] = report['labels'].get(label, 0)+1
            report['hand_frames'] += int(bool(hands))
            if connection and now-last_poll > .4:
                try:
                    remote = request(connection, '/status')
                    if remote.get('session') != connection.get('session'):
                        raise RuntimeError('桥接已重启，请重新打开本程序')
                    network_error = ''
                except Exception as error:
                    remote, network_error, enabled = {}, '连接失败：'+str(error), False
                    gate.reset()
                last_poll = time.monotonic()
            ready = enabled and remote.get('ready', False) and not network_error and not args.probe_seconds
            color = gate.feed(label, now, ready=ready)
            if color:
                try:
                    receipt = request(connection, '/command', dict(color=color, request_id=str(uuid.uuid4()),
                                                                   session=connection['session']))
                    if not receipt.get('accepted'):
                        raise RuntimeError('未收到接受确认')
                    report['commands_sent'] += 1
                    last_action = '已发送：'+ZH[color]+'色方块；等待动作结束'
                    # Never permit another trigger until a fresh status says the job ended.
                    remote['ready'] = False
                    last_poll = -10.
                except Exception as error:
                    enabled = False
                    gate.reset()
                    last_action = '发送失败或结果不明，请核对RViz后再启用：'+str(error)
            display = draw(frame, hands)
            panel = np.full((280, display.shape[1], 3), 35, np.uint8)
            image = Image.fromarray(cv2.cvtColor(panel, cv2.COLOR_BGR2RGB))
            pen = ImageDraw.Draw(image)
            selected = ZH.get(COLORS.get(gate.selected), '无')
            label_zh = {'none': '未识别数字或OK', 'blocked': '多手已拦截'}.get(label, label)
            gate_description = gate.state if enabled else '仅预览识别，按S启用控制'
            if enabled and gate.selected:
                gate_description += '（剩余%d秒）' % max(0, int(gate.deadline-now)+1)
            if enabled and gate.state in ('等待数字1～4', '请做OK确认'):
                gate_description += ' %d%%' % round(gate.progress*100)
            hand_status = ('检测到%d只手；每手21个点位及编号' % len(hands)) if hands else '未检测到手：手掌正对镜头，完整露出手指'
            if gate.selected and 'ring_ratio' in diagnostics:
                hand_status = 'OK指尖距 %.2f/0.42；另三指%s' % (diagnostics['ring_ratio'],
                               '已伸直' if diagnostics['ok_three_fingers'] else '请伸直')
            lines = ['实时帧%d  识别：%s  候选：%s' % (report['frames'], label_zh, selected),
                     hand_status,
                     gate_description+'；数字→放松→OK',
                     ('已启用虚拟抓取' if enabled else '只识别、不控制（按S启用）')+'；仅限RViz',
                     last_action,
                     network_error or '机械臂：'+str(remote.get('robot', {}).get('state', '等待状态')),
                     'S启用 / 空格暂停输入 / R复位场景 / ESC退出']
            for i, text in enumerate(lines):
                pen.text((8, 4+i*29), text[:44], font=font, fill=(240, 240, 240))
            tiles = [('1', '红色', (235, 55, 55)), ('2', '黄色', (240, 210, 35)),
                     ('3', '蓝色', (65, 135, 245)), ('4', '绿色', (55, 210, 90))]
            for i, (number, name, rgb) in enumerate(tiles):
                x = 8+i*158
                highlight = gate.selected == number or label == number
                pen.rounded_rectangle((x, 213, x+148, 273), radius=7,
                                      fill=rgb if highlight else (45, 45, 45), outline=rgb,
                                      width=5 if highlight else 2)
                pen.text((x+12, 229), number+' → '+name, font=font,
                         fill=(15, 15, 15) if highlight else rgb)
            if args.telemetry and now-last_telemetry >= 1:
                metadata = dict(frame=report['frames'], label=label, hand_count=len(hands),
                                landmark_count=[len(h) for h in hands], enabled=enabled,
                                candidate=gate.selected, gate_state=gate.state,
                                label_counts=report['labels'], hand_frames=report['hand_frames'],
                                commands_sent=report['commands_sent'], images_saved=False,
                                confirmation_progress=gate.progress, diagnostics=diagnostics)
                Path(args.telemetry).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
                last_telemetry = now
            panel = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
            cv2.imshow('Arm2026 gesture control', np.vstack([display, panel]))
            key = cv2.waitKey(1) & 255
            if key in (27, ord('q')) or cv2.getWindowProperty('Arm2026 gesture control', cv2.WND_PROP_VISIBLE) < 1:
                break
            if key == ord('s') and not args.probe_seconds:
                if remote.get('ready') and not network_error:
                    enabled = True
                    gate.reset()
                    last_action = '已启用；请先放松手或移出画面'
                else:
                    last_action = '无法启用：先启动WSL手势场景并等待空闲'
            if key == 32:
                enabled = False
                gate.reset()
                last_action = '已暂停手势输入；不会中断正在执行的虚拟动作'
            if key == ord('r') and connection and not args.probe_seconds:
                enabled = False
                gate.reset()
                try:
                    request(connection, '/reset', {})
                    last_action = '虚拟场景复位；完成后按S重新启用'
                except Exception as error:
                    last_action = '复位未确认：'+str(error)
            if args.probe_seconds and time.monotonic()-start >= args.probe_seconds:
                break
        report['result'] = 'PASS'
    except Exception as error:
        report['result'], report['error'] = 'FAIL', str(error)
        raise
    finally:
        if sender:
            sender.close()
            report['frames_uploaded'] = sender.sent > 0
            report['local_preview_frames'] = sender.sent
            report['preview_error'] = sender.error
        if camera is not None:
            camera.release()
        if model is not None:
            model.close()
        cv2.destroyAllWindows()
        report['duration_s'] = round(time.monotonic()-start, 3)
        if args.report:
            Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
